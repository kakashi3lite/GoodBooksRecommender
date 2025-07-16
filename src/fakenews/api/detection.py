"""
False News Detection API - Main Entry Point
Integrates with the existing GoodBooksRecommender FastAPI application.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.security import HTTPBearer
from typing import Dict, Any, List
import asyncio
import time
from datetime import datetime

# Import from existing infrastructure
from src.auth.security import get_current_active_user, User, require_permissions
from src.core.cache import AsyncCacheManager
from src.core.enhanced_logging import StructuredLogger
from src.core.monitoring import MetricsCollector

# Import fake news detection components
from ..models.schemas import (
    DetectionRequest, DetectionResponse, BatchDetectionRequest, 
    BatchDetectionResponse, SystemStats, HealthCheckResponse,
    AnalysisStatus, Verdict, ValidationResult
)
from ..services.detection_service import DetectionService
from ..input.input_validator import InputValidator

# Setup
logger = StructuredLogger(__name__)
metrics = MetricsCollector()
security = HTTPBearer()

# Create router for fake news detection
fakenews_router = APIRouter(
    prefix="/fakenews",
    tags=["Fake News Detection"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        429: {"description": "Rate limit exceeded"}
    }
)


# Dependency injection
async def get_detection_service() -> DetectionService:
    """Get detection service instance."""
    return DetectionService()


async def get_input_validator() -> InputValidator:
    """Get input validator instance."""
    return InputValidator()


# Core Detection Endpoints
@fakenews_router.post("/detect", response_model=DetectionResponse)
async def detect_fake_news(
    request: DetectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    detection_service: DetectionService = Depends(get_detection_service),
    input_validator: InputValidator = Depends(get_input_validator)
):
    """
    Analyze content for potential misinformation.
    
    This endpoint performs comprehensive analysis of text, image, or media content
    to detect fake news, misinformation, or misleading content.
    
    **Analysis Depth Levels:**
    - `quick`: Basic text analysis only (~2 seconds)
    - `standard`: All modules except deep media analysis (~10 seconds)
    - `deep`: Full analysis including deep media verification (~30 seconds)
    - `comprehensive`: All modules + orchestration refinement (~60 seconds)
    
    **Required Permissions:** `fakenews:analyze`
    """
    start_time = time.time()
    
    try:
        # Validate input
        validation_result = await input_validator.validate_request(request)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input: {', '.join(validation_result.errors)}"
            )
        
        # Check for duplicate requests using content hash
        cache_key = f"detection:{validation_result.content_hash}"
        cached_result = await AsyncCacheManager().get(cache_key)
        if cached_result:
            logger.info("Returning cached detection result", 
                       content_hash=validation_result.content_hash,
                       user_id=current_user.id)
            return DetectionResponse.parse_obj(cached_result)
        
        # Start analysis
        logger.info("Starting fake news detection analysis",
                   user_id=current_user.id,
                   analysis_depth=request.analysis_depth,
                   content_type=validation_result.content_type)
        
        result = await detection_service.analyze_content(
            request=request,
            user_id=current_user.id,
            validation_result=validation_result
        )
        
        # Queue background deep analysis if needed
        if request.analysis_depth in ["deep", "comprehensive"]:
            background_tasks.add_task(
                detection_service.deep_analysis,
                result.request_id,
                request.analysis_depth
            )
        
        # Cache result
        await AsyncCacheManager().set(
            cache_key, 
            result.dict(), 
            ttl=3600  # 1 hour
        )
        
        # Update metrics
        analysis_time = time.time() - start_time
        metrics.record_detection_request(
            verdict=result.verdict,
            analysis_depth=request.analysis_depth,
            duration=analysis_time,
            user_tier=current_user.role.value
        )
        
        logger.info("Detection analysis completed",
                   request_id=result.request_id,
                   verdict=result.verdict,
                   confidence=result.confidence_score,
                   duration_ms=result.analysis_duration_ms)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Detection analysis failed",
                    error=str(e),
                    user_id=current_user.id,
                    exc_info=True)
        
        metrics.record_detection_error("analysis_failed")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again later."
        )


@fakenews_router.get("/detect/{request_id}", response_model=DetectionResponse)
async def get_detection_result(
    request_id: str,
    current_user: User = Depends(get_current_active_user),
    detection_service: DetectionService = Depends(get_detection_service)
):
    """
    Get results of a previous detection request.
    
    This endpoint allows you to retrieve the results of a detection analysis
    using the request ID returned from the initial detection request.
    
    **Required Permissions:** `fakenews:view_results`
    """
    try:
        result = await detection_service.get_result(request_id, current_user.id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Detection result not found or access denied"
            )
        
        logger.info("Retrieved detection result",
                   request_id=request_id,
                   user_id=current_user.id,
                   status=result.status)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve detection result",
                    request_id=request_id,
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve result"
        )


@fakenews_router.post("/detect/quick", response_model=DetectionResponse)
async def quick_detect(
    request: DetectionRequest,
    current_user: User = Depends(get_current_active_user),
    detection_service: DetectionService = Depends(get_detection_service)
):
    """
    Quick fake news detection with basic analysis only.
    
    This endpoint provides fast analysis using only text-based models
    for situations where speed is more important than comprehensive analysis.
    
    **Analysis Time:** ~2 seconds
    **Required Permissions:** `fakenews:analyze`
    """
    # Force quick analysis
    request.analysis_depth = "quick"
    request.require_explanation = False
    
    return await detect_fake_news(
        request=request,
        background_tasks=BackgroundTasks(),  # No background tasks for quick analysis
        current_user=current_user,
        detection_service=detection_service,
        input_validator=InputValidator()
    )


# Batch Processing Endpoints
@fakenews_router.post("/batch", response_model=BatchDetectionResponse)
async def batch_detect(
    batch_request: BatchDetectionRequest,
    current_user: User = Depends(get_current_active_user),
    detection_service: DetectionService = Depends(get_detection_service)
):
    """
    Batch analysis for multiple content items.
    
    This endpoint allows you to submit multiple items for analysis in a single request.
    Processing happens asynchronously, and you can poll for results or use webhooks.
    
    **Limits:**
    - Maximum 100 items per batch
    - Rate limits apply based on user tier
    
    **Required Permissions:** `fakenews:batch`
    """
    try:
        # Validate batch size based on user permissions
        max_batch_size = _get_max_batch_size(current_user.role)
        if len(batch_request.items) > max_batch_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size exceeds limit of {max_batch_size} items"
            )
        
        # Start batch processing
        batch_result = await detection_service.process_batch(
            batch_request=batch_request,
            user_id=current_user.id
        )
        
        logger.info("Started batch processing",
                   batch_id=batch_result.batch_id,
                   total_items=batch_result.total_items,
                   user_id=current_user.id)
        
        return batch_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Batch processing failed",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch processing failed"
        )


@fakenews_router.get("/batch/{batch_id}", response_model=BatchDetectionResponse)
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    detection_service: DetectionService = Depends(get_detection_service)
):
    """
    Get status and results of a batch processing request.
    
    **Required Permissions:** `fakenews:view_results`
    """
    try:
        batch_result = await detection_service.get_batch_result(batch_id, current_user.id)
        
        if not batch_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found or access denied"
            )
        
        return batch_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve batch status",
                    batch_id=batch_id,
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve batch status"
        )


# Validation Endpoints
@fakenews_router.post("/validate", response_model=ValidationResult)
async def validate_input(
    request: DetectionRequest,
    current_user: User = Depends(get_current_active_user),
    input_validator: InputValidator = Depends(get_input_validator)
):
    """
    Validate input before submitting for analysis.
    
    This endpoint allows you to check if your input is valid and get
    estimates for processing time before starting the actual analysis.
    
    **Required Permissions:** `fakenews:analyze`
    """
    try:
        validation_result = await input_validator.validate_request(request)
        
        logger.info("Input validation completed",
                   is_valid=validation_result.is_valid,
                   content_type=validation_result.content_type,
                   user_id=current_user.id)
        
        return validation_result
        
    except Exception as e:
        logger.error("Input validation failed",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation failed"
        )


# System Information Endpoints
@fakenews_router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(get_current_active_user),
    detection_service: DetectionService = Depends(get_detection_service)
):
    """
    Get system statistics and performance metrics.
    
    **Required Permissions:** `fakenews:view_stats`
    """
    try:
        stats = await detection_service.get_system_stats()
        
        logger.info("Retrieved system stats",
                   user_id=current_user.id)
        
        return stats
        
    except Exception as e:
        logger.error("Failed to retrieve system stats",
                    user_id=current_user.id,
                    error=str(e))
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )


@fakenews_router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    This endpoint does not require authentication and provides
    basic system health information.
    """
    try:
        # Basic health checks
        components = {}
        
        # Check database connectivity
        try:
            # Implement database ping
            components["database"] = "healthy"
        except:
            components["database"] = "unhealthy"
        
        # Check Redis connectivity
        try:
            await AsyncCacheManager().ping()
            components["redis"] = "healthy"
        except:
            components["redis"] = "unhealthy"
        
        # Check ML models
        try:
            # Implement model health check
            components["ml_models"] = "healthy"
        except:
            components["ml_models"] = "unhealthy"
        
        # Determine overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in components.values()
        ) else "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            version="1.0.0",
            components=components,
            uptime_seconds=int(time.time() - _get_start_time())
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            components={"system": "error"},
            uptime_seconds=0
        )


# Helper functions
def _get_max_batch_size(user_role) -> int:
    """Get maximum batch size based on user role."""
    batch_limits = {
        "free": 10,
        "premium": 50,
        "enterprise": 100
    }
    return batch_limits.get(user_role.value.lower(), 10)


def _get_start_time() -> float:
    """Get application start time."""
    # This would be set when the application starts
    return time.time() - 3600  # Placeholder: 1 hour ago


# Integration with main FastAPI app
def include_fakenews_router(app):
    """Include the fake news detection router in the main app."""
    app.include_router(fakenews_router)
    
    logger.info("Fake News Detection API endpoints registered")


# Example usage in main app:
"""
# In src/api/main.py, add:

from src.fakenews.api.detection import include_fakenews_router

# After creating the FastAPI app
include_fakenews_router(app)
"""

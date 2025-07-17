"""
Enhanced API Endpoints for GoodBooks Recommender

This module provides advanced API endpoints that integrate:
- Real-time analytics
- Advanced caching
- Enhanced health monitoring
- Batch processing
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

from src.core.logging import StructuredLogger
from src.analytics.real_time_analytics import (
    RealTimeAnalytics, UserInteraction, RecommendationEvent, RealTimeMetrics
)
from src.core.advanced_cache import MultiLevelCache, L1MemoryCache
from src.core.enhanced_health import HealthMonitor, SystemHealthReport
from src.core.batch_processing import (
    BatchProcessingEngine, create_recommendation_batch, create_user_analytics_batch
)

logger = StructuredLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v2", tags=["Enhanced Features"])

# Global instances (these would be initialized during app startup)
analytics_engine: Optional[RealTimeAnalytics] = None
cache_system: Optional[MultiLevelCache] = None
health_monitor: Optional[HealthMonitor] = None
batch_engine: Optional[BatchProcessingEngine] = None


# Pydantic Models

class UserInteractionRequest(BaseModel):
    """Request model for tracking user interactions."""
    user_id: str = Field(..., description="User identifier")
    event_type: str = Field(..., description="Type of interaction")
    item_id: Optional[str] = Field(None, description="Item identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchRecommendationRequest(BaseModel):
    """Request model for batch recommendations."""
    user_ids: List[int] = Field(..., description="List of user IDs")
    n_recommendations: int = Field(10, ge=1, le=50, description="Number of recommendations per user")
    recommendation_type: str = Field("hybrid", description="Type of recommendation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Job metadata")


class BatchAnalyticsRequest(BaseModel):
    """Request model for batch analytics."""
    user_ids: List[int] = Field(..., description="List of user IDs")
    analytics_type: str = Field("profile", description="Type of analytics")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Job metadata")


class CacheWarmingRequest(BaseModel):
    """Request model for cache warming."""
    user_recommendations: Optional[Dict[str, Any]] = Field(None, description="User recommendation patterns")
    popular_books: Optional[Dict[str, Any]] = Field(None, description="Popular books patterns")
    custom_patterns: Optional[Dict[str, Any]] = Field(None, description="Custom warming patterns")


# Analytics Endpoints

@router.post("/analytics/track-interaction", 
            summary="Track User Interaction",
            description="Track a user interaction event for real-time analytics")
async def track_user_interaction(
    interaction_request: UserInteractionRequest,
    background_tasks: BackgroundTasks
):
    """Track a user interaction event."""
    if not analytics_engine:
        raise HTTPException(status_code=503, detail="Analytics engine not available")
    
    try:
        interaction = UserInteraction(
            user_id=interaction_request.user_id,
            event_type=interaction_request.event_type,
            item_id=interaction_request.item_id,
            session_id=interaction_request.session_id,
            metadata=interaction_request.metadata or {}
        )
        
        # Track interaction in background
        background_tasks.add_task(analytics_engine.track_user_interaction, interaction)
        
        return {
            "status": "success",
            "message": "Interaction tracked",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to track interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to track interaction: {str(e)}")


@router.get("/analytics/real-time-metrics",
           response_model=Dict[str, Any],
           summary="Get Real-time Metrics",
           description="Get current real-time system metrics")
async def get_real_time_metrics():
    """Get real-time analytics metrics."""
    if not analytics_engine:
        raise HTTPException(status_code=503, detail="Analytics engine not available")
    
    try:
        metrics = await analytics_engine.get_real_time_metrics()
        return {
            "metrics": metrics.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/analytics/user-behavior",
           summary="Get User Behavior Analytics",
           description="Get user behavior analytics for specified time window")
async def get_user_behavior_analytics(
    time_window: int = Query(3600, description="Time window in seconds", ge=60, le=86400)
):
    """Get user behavior analytics."""
    if not analytics_engine:
        raise HTTPException(status_code=503, detail="Analytics engine not available")
    
    try:
        analytics = await analytics_engine.get_user_behavior_analytics(time_window)
        return {
            "analytics": analytics,
            "time_window_seconds": time_window,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get user behavior analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.get("/analytics/recommendation-performance",
           summary="Get Recommendation Performance",
           description="Get recommendation performance analytics")
async def get_recommendation_analytics(
    time_window: int = Query(3600, description="Time window in seconds", ge=60, le=86400)
):
    """Get recommendation performance analytics."""
    if not analytics_engine:
        raise HTTPException(status_code=503, detail="Analytics engine not available")
    
    try:
        analytics = await analytics_engine.get_recommendation_analytics(time_window)
        return {
            "analytics": analytics,
            "time_window_seconds": time_window,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendation analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# Cache Management Endpoints

@router.get("/cache/stats",
           summary="Get Cache Statistics",
           description="Get comprehensive cache statistics across all levels")
async def get_cache_stats():
    """Get cache statistics."""
    if not cache_system:
        raise HTTPException(status_code=503, detail="Cache system not available")
    
    try:
        stats = await cache_system.get_comprehensive_stats()
        return {
            "cache_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/cache/warm",
            summary="Warm Cache",
            description="Warm cache with specified patterns")
async def warm_cache(
    warming_request: CacheWarmingRequest,
    background_tasks: BackgroundTasks
):
    """Warm cache with specified patterns."""
    if not cache_system:
        raise HTTPException(status_code=503, detail="Cache system not available")
    
    try:
        warming_config = {}
        
        if warming_request.user_recommendations:
            warming_config["user_recommendations"] = warming_request.user_recommendations
        
        if warming_request.popular_books:
            warming_config["popular_books"] = warming_request.popular_books
        
        if warming_request.custom_patterns:
            warming_config.update(warming_request.custom_patterns)
        
        if not warming_config:
            raise HTTPException(status_code=400, detail="No warming patterns specified")
        
        # Start cache warming in background
        background_tasks.add_task(cache_system.warm_cache, warming_config)
        
        return {
            "status": "success",
            "message": "Cache warming started",
            "patterns": list(warming_config.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to warm cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@router.delete("/cache/clear",
              summary="Clear Cache",
              description="Clear all cache levels")
async def clear_cache():
    """Clear all cache levels."""
    if not cache_system:
        raise HTTPException(status_code=503, detail="Cache system not available")
    
    try:
        success = await cache_system.clear_all()
        
        return {
            "status": "success" if success else "failed",
            "message": "Cache cleared" if success else "Failed to clear cache",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# Health Monitoring Endpoints

@router.get("/health/comprehensive",
           summary="Comprehensive Health Check",
           description="Get comprehensive health status across all components")
async def comprehensive_health_check():
    """Get comprehensive health status."""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not available")
    
    try:
        health_report = await health_monitor.run_health_check()
        return health_report.to_dict()
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/health/summary",
           summary="Health Summary",
           description="Get quick health summary")
async def get_health_summary():
    """Get quick health summary."""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not available")
    
    try:
        summary = health_monitor.get_health_summary()
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get health summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health summary: {str(e)}")


@router.get("/health/history",
           summary="Health History",
           description="Get health check history")
async def get_health_history(
    hours: int = Query(1, description="Hours of history to retrieve", ge=1, le=24)
):
    """Get health check history."""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not available")
    
    try:
        history = health_monitor.get_health_history(hours)
        return {
            "history": history,
            "hours": hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get health history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health history: {str(e)}")


@router.get("/health/component/{component_name}",
           summary="Component Health",
           description="Get health status for specific component")
async def get_component_health(component_name: str):
    """Get health status for a specific component."""
    if not health_monitor:
        raise HTTPException(status_code=503, detail="Health monitor not available")
    
    try:
        component_health = health_monitor.get_component_health(component_name)
        
        if not component_health:
            raise HTTPException(status_code=404, detail=f"Component '{component_name}' not found")
        
        return component_health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get component health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get component health: {str(e)}")


# Batch Processing Endpoints

@router.post("/batch/recommendations",
            summary="Submit Batch Recommendation Job",
            description="Submit a batch job for generating recommendations")
async def submit_batch_recommendations(request: BatchRecommendationRequest):
    """Submit a batch recommendation job."""
    if not batch_engine:
        raise HTTPException(status_code=503, detail="Batch processing engine not available")
    
    try:
        tasks_data = create_recommendation_batch(
            user_ids=request.user_ids,
            n_recommendations=request.n_recommendations,
            recommendation_type=request.recommendation_type
        )
        
        batch_id = await batch_engine.submit_batch_job(
            job_type="recommendations",
            tasks_data=tasks_data,
            metadata=request.metadata
        )
        
        return {
            "batch_id": batch_id,
            "status": "submitted",
            "task_count": len(tasks_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit batch recommendation job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.post("/batch/analytics",
            summary="Submit Batch Analytics Job",
            description="Submit a batch job for user analytics")
async def submit_batch_analytics(request: BatchAnalyticsRequest):
    """Submit a batch analytics job."""
    if not batch_engine:
        raise HTTPException(status_code=503, detail="Batch processing engine not available")
    
    try:
        tasks_data = create_user_analytics_batch(
            user_ids=request.user_ids,
            analytics_type=request.analytics_type
        )
        
        batch_id = await batch_engine.submit_batch_job(
            job_type="user_analytics",
            tasks_data=tasks_data,
            metadata=request.metadata
        )
        
        return {
            "batch_id": batch_id,
            "status": "submitted",
            "task_count": len(tasks_data),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit batch analytics job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")


@router.get("/batch/{batch_id}/status",
           summary="Get Batch Job Status",
           description="Get the status of a batch job")
async def get_batch_job_status(batch_id: str):
    """Get batch job status."""
    if not batch_engine:
        raise HTTPException(status_code=503, detail="Batch processing engine not available")
    
    try:
        status = await batch_engine.get_job_status(batch_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Batch job '{batch_id}' not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch job status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/batch/{batch_id}/results",
           summary="Get Batch Job Results",
           description="Get the results of a completed batch job")
async def get_batch_job_results(batch_id: str):
    """Get batch job results."""
    if not batch_engine:
        raise HTTPException(status_code=503, detail="Batch processing engine not available")
    
    try:
        results = await batch_engine.get_job_results(batch_id)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Batch job '{batch_id}' not found")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch job results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}")


@router.delete("/batch/{batch_id}",
              summary="Cancel Batch Job",
              description="Cancel a running batch job")
async def cancel_batch_job(batch_id: str):
    """Cancel a batch job."""
    if not batch_engine:
        raise HTTPException(status_code=503, detail="Batch processing engine not available")
    
    try:
        success = await batch_engine.cancel_job(batch_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Batch job '{batch_id}' not found or cannot be cancelled")
        
        return {
            "status": "cancelled",
            "batch_id": batch_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel batch job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/batch/stats",
           summary="Get Batch Processing Stats",
           description="Get batch processing engine statistics")
async def get_batch_processing_stats():
    """Get batch processing engine statistics."""
    if not batch_engine:
        raise HTTPException(status_code=503, detail="Batch processing engine not available")
    
    try:
        stats = await batch_engine.get_engine_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get batch processing stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/batch/jobs",
           summary="Get Active Batch Jobs",
           description="Get summary of all active batch jobs")
async def get_active_batch_jobs():
    """Get active batch jobs summary."""
    if not batch_engine:
        raise HTTPException(status_code=503, detail="Batch processing engine not available")
    
    try:
        jobs = await batch_engine.get_active_jobs_summary()
        return {
            "active_jobs": jobs,
            "count": len(jobs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get active batch jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get active jobs: {str(e)}")


# System Overview Endpoint

@router.get("/system/overview",
           summary="System Overview",
           description="Get comprehensive system overview including all subsystems")
async def get_system_overview():
    """Get comprehensive system overview."""
    overview = {
        "timestamp": datetime.utcnow().isoformat(),
        "subsystems": {}
    }
    
    # Analytics system status
    if analytics_engine:
        try:
            metrics = await analytics_engine.get_real_time_metrics()
            overview["subsystems"]["analytics"] = {
                "status": "available",
                "metrics": metrics.dict()
            }
        except Exception as e:
            overview["subsystems"]["analytics"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        overview["subsystems"]["analytics"] = {"status": "unavailable"}
    
    # Cache system status
    if cache_system:
        try:
            stats = await cache_system.get_comprehensive_stats()
            overview["subsystems"]["cache"] = {
                "status": "available",
                "stats": stats
            }
        except Exception as e:
            overview["subsystems"]["cache"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        overview["subsystems"]["cache"] = {"status": "unavailable"}
    
    # Health monitoring status
    if health_monitor:
        try:
            summary = health_monitor.get_health_summary()
            overview["subsystems"]["health"] = {
                "status": "available",
                "summary": summary
            }
        except Exception as e:
            overview["subsystems"]["health"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        overview["subsystems"]["health"] = {"status": "unavailable"}
    
    # Batch processing status
    if batch_engine:
        try:
            stats = await batch_engine.get_engine_stats()
            overview["subsystems"]["batch_processing"] = {
                "status": "available",
                "stats": stats
            }
        except Exception as e:
            overview["subsystems"]["batch_processing"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        overview["subsystems"]["batch_processing"] = {"status": "unavailable"}
    
    return overview


# Streaming endpoint for real-time metrics
@router.get("/analytics/metrics/stream",
           summary="Stream Real-time Metrics",
           description="Stream real-time metrics as Server-Sent Events")
async def stream_real_time_metrics():
    """Stream real-time metrics."""
    if not analytics_engine:
        raise HTTPException(status_code=503, detail="Analytics engine not available")
    
    async def generate_metrics():
        """Generate metrics stream."""
        while True:
            try:
                metrics = await analytics_engine.get_real_time_metrics()
                data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": metrics.dict()
                }
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(5)  # Send metrics every 5 seconds
            except Exception as e:
                error_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                await asyncio.sleep(10)  # Wait longer on error
    
    return StreamingResponse(
        generate_metrics(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


# Initialization functions (called during app startup)

def initialize_enhanced_features(
    analytics: RealTimeAnalytics,
    cache: MultiLevelCache,
    health: HealthMonitor,
    batch: BatchProcessingEngine
):
    """Initialize enhanced features with provided instances."""
    global analytics_engine, cache_system, health_monitor, batch_engine
    
    analytics_engine = analytics
    cache_system = cache
    health_monitor = health
    batch_engine = batch
    
    logger.info("Enhanced features initialized")

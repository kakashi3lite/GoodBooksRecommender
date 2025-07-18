"""
Production-Grade GoodBooks Recommender API
Follows Bookworm AI Coding Standards for high-performance, secure, and maintainable systems.
"""

import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import uvicorn
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from opentelemetry import trace
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field, validator

# Security and Authentication modules
from src.auth.security import (
    OAuth2Manager,
    RBACManager,
    TokenData,
    User,
    UserRole,
    get_current_active_user,
    get_current_user,
    require_permissions,
    require_roles,
)
from src.config import Config
from src.core.cache import AsyncCacheManager
from src.core.enhanced_logging import (
    StructuredLogger,
    get_correlation_id,
    set_correlation_id,
)
from src.core.exceptions import (
    AuthenticationError,
    CacheError,
    GoodBooksException,
    RateLimitError,
    RecommendationError,
    ValidationError,
)
from src.core.logging import get_logger, setup_logging
from src.core.monitoring import (
    MetricsCollector,
    PerformanceMonitor,
    start_background_monitoring,
)
from src.core.session_store import RedisSessionStore, SessionStoreError, UserInteraction

# Core modules
from src.core.settings import settings
from src.core.tracing import TracingManager, get_tracer, trace_operation
from src.core.vector_store import BookVectorStore, VectorStoreError

# Business logic modules
from src.data.data_loader import DataLoader
from src.middleware.security_middleware import (
    CSPMiddleware,
    InputValidationMiddleware,
    RateLimitingMiddleware,
    SecurityHeadersMiddleware,
    SecurityMiddleware,
)
from src.models.ab_tester import ABTester
from src.models.hybrid_recommender import HybridRecommender
from src.models.model_manager import ModelManager
from src.privacy.data_privacy import (
    AnonymizationLevel,
    DataPrivacyService,
    RetentionPolicy,
)
from src.services.rag_service import RAGError, RAGExplanationService

# Configure structured logging
setup_logging()
logger = StructuredLogger(__name__)

# Initialize monitoring and tracing
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor()
tracing_manager = TracingManager(service_name="goodbooks-api")
tracer = get_tracer(__name__)


# API configuration class to handle missing API settings
class api:
    """API configuration settings namespace."""

    version = "1.0.0"
    host = "0.0.0.0"
    port = 8000
    workers = 4
    docs_url = "/docs"
    health_path = "/health"
    metrics_path = "/metrics"
    metrics_enabled = True
    log_requests = True


# Prometheus metrics
REQUEST_COUNT = Counter(
    "goodbooks_requests_total",
    "Total requests processed",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "goodbooks_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge("goodbooks_active_requests", "Currently active requests")

RECOMMENDATIONS_GENERATED = Counter(
    "goodbooks_recommendations_total",
    "Total recommendations generated",
    ["type"],  # user-based, content-based, hybrid
)

CACHE_OPERATIONS = Counter(
    "goodbooks_cache_operations_total",
    "Cache operations",
    ["operation", "result"],  # get/set, hit/miss/error
)

# Additional metrics
RECOMMENDATION_COUNT = Counter(
    "goodbooks_recommendation_requests_total", "Total recommendation requests"
)

ERROR_COUNT = Counter("goodbooks_errors_total", "Total errors by type", ["error_type"])

# Global instances
cache_manager = AsyncCacheManager()
data_loader = None
recommender = None
vector_store = None
rag_service = None
session_store = None

# Security and Authentication instances
oauth2_manager = OAuth2Manager()
rbac_manager = RBACManager()
data_privacy_service = DataPrivacyService()

# A/B Testing and Model Management support
ab_tester = None
model_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info("Starting GoodBooks Recommender API...")

    global data_loader, recommender, vector_store, rag_service, session_store, ab_tester, model_manager

    try:
        # Initialize tracing
        logger.info("Initializing distributed tracing...")
        tracing_manager.setup_tracing()
        # Initialize monitoring
        logger.info("Starting background monitoring...")
        monitoring_task = asyncio.create_task(start_background_monitoring())

        # Initialize core components
        logger.info("Initializing data loader...")
        data_loader = DataLoader()

        logger.info("Loading data...")
        with trace_operation("data_loading", {"component": "data_loader"}):
            books_df, ratings_df = await asyncio.to_thread(data_loader.load_data)

        logger.info("Initializing vector store...")
        config = Config()
        vector_store = BookVectorStore(
            books_df=books_df,
            model_name=config.get("model.sentence_transformer", "all-MiniLM-L6-v2"),
        )
        with trace_operation("vector_store_build", {"component": "vector_store"}):
            await asyncio.to_thread(vector_store.build_index)

        logger.info("Initializing session store...")
        session_store = RedisSessionStore(
            redis_url=config.get("redis.url", "redis://localhost:6379")
        )

        logger.info("Initializing model manager...")
        model_manager = ModelManager(
            model_registry_url=config.get("mlflow.registry_url"),
            s3_bucket=config.get("mlflow.s3_bucket"),
            cache_size=config.get("model_manager.cache_size", 3),
        )

        logger.info("Initializing recommender...")
        with trace_operation(
            "recommender_training", {"component": "hybrid_recommender"}
        ):
            recommender = HybridRecommender(
                books_df=books_df, ratings_df=ratings_df, vector_store=vector_store
            )
            await asyncio.to_thread(recommender.fit)

        logger.info("Initializing A/B testing framework...")
        ab_tester = ABTester(
            redis_url=config.get("redis.url", "redis://localhost:6379")
        )

        logger.info("Initializing RAG service...")
        rag_service = RAGExplanationService(
            vector_store=vector_store, books_df=books_df
        )

        # Start data privacy cleanup task (runs in background)
        logger.info("Starting data privacy cleanup task...")

        async def privacy_cleanup_task():
            """Background task to enforce data retention policies."""
            while True:
                try:
                    # Clean up expired session data, logs, and cached data
                    await data_privacy_service.cleanup_expired_data()
                    logger.info("Data privacy cleanup completed")
                except Exception as e:
                    logger.error("Data privacy cleanup failed", error=str(e))

                # Wait 24 hours before next cleanup
                await asyncio.sleep(24 * 60 * 60)

        privacy_cleanup_task_handle = asyncio.create_task(privacy_cleanup_task())

        logger.info("API startup complete!")

    except Exception as e:
        logger.error("Failed to initialize API", error=str(e), exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down GoodBooks Recommender API...")

    try:
        # Cancel monitoring task
        if "monitoring_task" in locals():
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass

        # Cancel privacy cleanup task
        if "privacy_cleanup_task_handle" in locals():
            privacy_cleanup_task_handle.cancel()
            try:
                await privacy_cleanup_task_handle
            except asyncio.CancelledError:
                pass

        if session_store:
            await session_store.close()

        if ab_tester:
            await ab_tester.close()

        if model_manager:
            await model_manager.close()

        await cache_manager.close()

        # Shutdown tracing
        tracing_manager.shutdown()

    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

    logger.info("API shutdown complete!")


# FastAPI application
app = FastAPI(
    title="GoodBooks Recommender API",
    description="Production-grade book recommendation system with TF-IDF and collaborative filtering",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Include News Expansion System routers
try:
    from src.news.api.endpoints import router as news_intelligence_router
    from src.news.api.news_expansion import router as news_expansion_router

    app.include_router(
        news_expansion_router, prefix="/api/news", tags=["News Expansion"]
    )
    app.include_router(
        news_intelligence_router, prefix="/api/news", tags=["News Intelligence"]
    )
    logger.info("✅ News Expansion System routers integrated successfully")

except ImportError as e:
    logger.warning(f"⚠️ News Expansion System not available: {e}")
except Exception as e:
    logger.error(f"❌ Failed to integrate News Expansion System: {e}")

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# Authentication utilities
async def get_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    """Extract and validate API key."""
    if settings.is_development and not api_key:
        return "development"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key is required"
        )

    # In production, validate against database or key store
    valid_keys = (
        settings.security.api_keys
        if hasattr(settings.security, "api_keys")
        else [settings.security.default_api_key]
    )
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return api_key


async def get_user_id(request: Request) -> int:
    """Extract user ID from request headers or session."""
    # Try to get user ID from header
    user_id_header = request.headers.get("X-User-ID")
    if user_id_header:
        try:
            return int(user_id_header)
        except ValueError:
            pass

    # Try to get from query params
    user_id_param = request.query_params.get("user_id")
    if user_id_param:
        try:
            return int(user_id_param)
        except ValueError:
            pass

    # Generate anonymous user ID for session
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    # Use hash of session ID as anonymous user ID
    import hashlib

    return abs(hash(session_id)) % 1000000


model_manager = None
current_experiments = {}


async def initialize_data_and_models():
    """Initialize data loading and ML models with proper error handling."""
    global data_loader, recommender, vector_store, rag_service, session_store, ab_tester, model_manager

    try:
        logger.info("Starting data and model initialization")
        start_time = time.time()

        # Initialize model manager with dynamic loading
        model_manager = ModelManager()
        model_manager.start_model_watching(check_interval=300)  # Check every 5 minutes

        # Initialize A/B tester
        config = Config()
        ab_tester = ABTester(config)

        # Register model reload callback for A/B testing
        model_manager.register_reload_callback(_on_model_reload)

        # Initialize data loader
        data_loader = DataLoader(str(settings.data_dir))

        # Load datasets using async methods
        logger.info("Loading datasets")
        books, ratings, tags, book_tags = await data_loader.load_datasets_async()

        # Merge and preprocess data using async methods
        logger.info("Processing book metadata")
        merged_books = await data_loader.merge_book_metadata_async(
            books, book_tags, tags
        )
        processed_books = await data_loader.preprocess_tags_async(merged_books)

        # Initialize and train recommender (or load existing)
        logger.info("Loading recommendation models")
        try:
            # Try to load existing model first
            recommender = model_manager.load_model()
            if recommender is None:
                # Train new model if none exists
                recommender = HybridRecommender()
                await asyncio.to_thread(recommender.fit, processed_books, ratings)
                # Save the newly trained model
                model_manager.save_model(recommender, {}, {})
        except Exception as e:
            logger.warning(f"Failed to load existing model, training new one: {str(e)}")
            recommender = HybridRecommender()
            await asyncio.to_thread(recommender.fit, processed_books, ratings)

        # Initialize vector store
        logger.info("Initializing vector store")
        vector_store = BookVectorStore(
            model_name="all-MiniLM-L6-v2",
            store_path=str(settings.models_dir / "vector_store"),
        )

        # Try to load existing vector store, otherwise build new one
        if not await vector_store.load_async():
            logger.info("Building new vector store")
            await vector_store.build_from_books_async(processed_books)
        else:
            logger.info("Loaded existing vector store")

        # Initialize RAG service
        logger.info("Initializing RAG explanation service")
        rag_service = RAGExplanationService(vector_store)

        # Initialize session store
        logger.info("Initializing session store")
        session_store = RedisSessionStore()
        try:
            await session_store.connect()
        except Exception as e:
            logger.warning(f"Session store connection failed, using fallback: {str(e)}")
            # Continue without session store in development mode

        duration = time.time() - start_time
        logger.info(f"Initialization completed in {duration:.2f} seconds")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize data and models: {str(e)}", exc_info=True)
        raise


def _on_model_reload(new_model: HybridRecommender, version_id: str) -> None:
    """Callback for when a new model is loaded."""
    global recommender
    recommender = new_model
    logger.info(f"Updated global recommender to version {version_id}")


def get_recommender_for_request(
    user_id: int, experiment_id: Optional[str] = None
) -> HybridRecommender:
    """
    Get the appropriate recommender for a request based on A/B testing.

    Args:
        user_id: User making the request
        experiment_id: Active experiment ID (if any)

    Returns:
        Recommender instance to use for this request
    """
    global ab_tester, recommender

    if not experiment_id or not ab_tester:
        return recommender

    try:
        # Route request through A/B testing
        assignment = ab_tester.route_request(experiment_id, user_id)

        if assignment == "variant" and experiment_id in ab_tester.experiments:
            experiment = ab_tester.experiments[experiment_id]
            return experiment["variant_model"]

    except Exception as e:
        logger.error(f"A/B testing routing failed: {str(e)}")

    # Default to control/main model
    return recommender


async def record_recommendation_metrics(
    user_id: int,
    recommendations: List[Dict],
    experiment_id: Optional[str] = None,
    interaction_type: str = "view",
) -> None:
    """Record metrics for A/B testing analysis."""
    if not experiment_id or not ab_tester:
        return

    try:
        # Record basic metrics
        ab_tester.record_real_time_metric(
            experiment_id=experiment_id,
            user_id=user_id,
            metric_name="recommendation_count",
            value=len(recommendations),
        )

        # Record interaction metrics (to be updated based on user actions)
        ab_tester.record_real_time_metric(
            experiment_id=experiment_id,
            user_id=user_id,
            metric_name=f"{interaction_type}_count",
            value=1.0,
        )

    except Exception as e:
        logger.error(f"Failed to record recommendation metrics: {str(e)}")


# Middleware for A/B testing
@app.middleware("http")
async def ab_testing_middleware(request: Request, call_next):
    """Middleware to handle A/B testing for recommendations."""

    # Extract experiment info from headers or query params
    experiment_id = request.headers.get("X-Experiment-ID") or request.query_params.get(
        "experiment_id"
    )

    if experiment_id:
        request.state.experiment_id = experiment_id
        logger.debug(f"Request assigned to experiment: {experiment_id}")

    response = await call_next(request)
    return response


# FastAPI application
app = FastAPI(
    title="GoodBooks Recommender API",
    description="Production-grade book recommendation system with TF-IDF and collaborative filtering",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Middleware setup - Comprehensive Security Stack
if not settings.is_testing:
    # Security headers middleware (first layer)
    app.add_middleware(SecurityHeadersMiddleware)

    # Content Security Policy middleware
    app.add_middleware(CSPMiddleware)

    # Rate limiting middleware
    app.add_middleware(RateLimitingMiddleware)

    # Input validation middleware
    app.add_middleware(InputValidationMiddleware)

    # Security middleware (comprehensive protection)
    app.add_middleware(SecurityMiddleware)

    # CORS middleware (after security layers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=(
            ["*"] if settings.is_development else settings.security.allowed_hosts
        ),
    )

    # Compression middleware (last)
    app.add_middleware(GZipMiddleware, minimum_size=1000)


# OAuth2/JWT Authentication (replaces API key authentication)
oauth2_scheme = oauth2_manager.oauth2_scheme

# Legacy API key support (deprecated)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
) -> Optional[str]:
    """Legacy API key verification - deprecated, use JWT instead."""
    logger.warning(
        "API key authentication is deprecated. Please use OAuth2/JWT tokens."
    )

    if settings.is_development and not api_key:
        return "development"

    if not api_key:
        raise AuthenticationError("API key is required")

    # In production, validate against database or key store
    if api_key != settings.security.default_api_key:
        raise AuthenticationError("Invalid API key")

    return api_key


# Request/Response models
class RecommendationRequest(BaseModel):
    """Request model for recommendations endpoint."""

    user_id: Optional[int] = Field(
        None, description="User ID for collaborative filtering"
    )
    book_title: Optional[str] = Field(
        None, description="Book title for content-based filtering"
    )
    n_recommendations: int = Field(
        default=5, ge=1, le=50, description="Number of recommendations to return"
    )
    include_explanation: bool = Field(
        False, description="Include explanation for recommendations"
    )
    cache_ttl: Optional[int] = Field(None, description="Custom cache TTL in seconds")

    @validator("user_id")
    def validate_user_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("User ID must be positive")
        return v

    @validator("book_title")
    def validate_book_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Book title cannot be empty")
        return v.strip() if v else None

    class Config:
        schema_extra = {
            "example": {
                "user_id": 123,
                "n_recommendations": 5,
                "include_explanation": True,
            }
        }


class BookRecommendation(BaseModel):
    """Individual book recommendation model."""

    book_id: Optional[int] = Field(None, description="Book ID")
    title: str = Field(..., description="Book title")
    authors: str = Field(..., description="Book authors")
    average_rating: float = Field(..., description="Average rating")
    ratings_count: Optional[int] = Field(None, description="Number of ratings")
    hybrid_score: float = Field(..., description="Recommendation score")
    explanation: Optional[str] = Field(
        None, description="Explanation for recommendation"
    )

    class Config:
        schema_extra = {
            "example": {
                "title": "The Great Gatsby",
                "authors": "F. Scott Fitzgerald",
                "average_rating": 4.2,
                "ratings_count": 2500,
                "hybrid_score": 0.85,
                "explanation": "Similar to books you've enjoyed before",
            }
        }


class RecommendationResponse(BaseModel):
    """Response model for recommendations endpoint."""

    recommendations: List[BookRecommendation] = Field(
        ..., description="List of recommendations"
    )
    total_count: int = Field(..., description="Total number of recommendations")
    processing_time_ms: float = Field(
        ..., description="Processing time in milliseconds"
    )
    cache_hit: bool = Field(..., description="Whether result was served from cache")
    explanation: Optional[Dict[str, Any]] = Field(
        None, description="Global explanation"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "recommendations": [
                    {
                        "title": "The Great Gatsby",
                        "authors": "F. Scott Fitzgerald",
                        "average_rating": 4.2,
                        "hybrid_score": 0.85,
                    }
                ],
                "total_count": 1,
                "processing_time_ms": 45.2,
                "cache_hit": False,
                "metadata": {"algorithm": "hybrid", "model_version": "2.0.0"},
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model for load balancer monitoring."""

    status: str = Field(..., description="Overall service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    instance_id: str = Field(..., description="Instance identifier")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    health_check_duration_ms: float = Field(
        ..., description="Health check duration in milliseconds"
    )
    checks: Dict[str, Dict[str, Any]] = Field(
        ..., description="Individual health checks"
    )


class ExplainRequest(BaseModel):
    """Request model for explanation endpoint."""

    book_id: int = Field(..., description="Book ID to explain recommendations for")
    recommendation_type: str = Field(
        default="hybrid",
        description="Type of recommendation to explain",
        pattern="^(content_based|collaborative|hybrid)$",
    )
    n_context_books: int = Field(
        default=5, ge=1, le=10, description="Number of similar books for context"
    )

    class Config:
        schema_extra = {
            "example": {
                "book_id": 123,
                "recommendation_type": "hybrid",
                "n_context_books": 5,
            }
        }


class ExplainResponse(BaseModel):
    """Response model for explanation endpoint."""

    explanation: Dict[str, Any] = Field(..., description="Generated explanation")
    book_info: Dict[str, Any] = Field(
        ..., description="Information about the queried book"
    )
    processing_time_ms: float = Field(
        ..., description="Processing time in milliseconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "explanation": {
                    "text": "Based on your interest in 'The Great Gatsby'...",
                    "confidence_scores": {"overall_confidence": 0.85},
                },
                "book_info": {
                    "title": "The Great Gatsby",
                    "authors": "F. Scott Fitzgerald",
                },
                "processing_time_ms": 125.3,
            }
        }


class SessionRequest(BaseModel):
    """Request model for session endpoint."""

    session_id: Optional[str] = Field(None, description="Session ID to retrieve")
    user_id: Optional[int] = Field(None, description="User ID for session creation")
    action: str = Field(
        default="get",
        description="Action to perform",
        pattern="^(get|create|update|delete)$",
    )
    ttl: Optional[int] = Field(None, description="Session TTL in seconds")

    class Config:
        schema_extra = {"example": {"action": "create", "user_id": 123, "ttl": 86400}}


class SessionResponse(BaseModel):
    """Response model for session endpoint."""

    session_id: Optional[str] = Field(None, description="Session ID")
    session_data: Optional[Dict[str, Any]] = Field(None, description="Session data")
    action_performed: str = Field(..., description="Action that was performed")
    success: bool = Field(..., description="Whether action was successful")
    processing_time_ms: float = Field(
        ..., description="Processing time in milliseconds"
    )

    class Config:
        schema_extra = {
            "example": {
                "session_id": "uuid-string",
                "session_data": {
                    "user_id": 123,
                    "preferences": {},
                    "interaction_history": [],
                },
                "action_performed": "get",
                "success": True,
                "processing_time_ms": 15.2,
            }
        }


class SearchRequest(BaseModel):
    """Request model for semantic search endpoint."""

    query: str = Field(
        ..., description="Search query string", min_length=1, max_length=500
    )
    k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
    score_threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity score threshold"
    )
    include_explanation: bool = Field(
        False, description="Include explanation for results"
    )

    class Config:
        schema_extra = {
            "example": {
                "query": "fantasy adventure books with magic",
                "k": 10,
                "score_threshold": 0.3,
                "include_explanation": True,
            }
        }


class SearchResponse(BaseModel):
    """Response model for semantic search endpoint."""

    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
    processing_time_ms: float = Field(
        ..., description="Processing time in milliseconds"
    )
    explanation: Optional[Dict[str, Any]] = Field(
        None, description="Search explanation"
    )

    class Config:
        schema_extra = {
            "example": {
                "results": [
                    {"book_id": 123, "title": "Harry Potter", "similarity_score": 0.85}
                ],
                "total_count": 1,
                "query": "fantasy adventure books",
                "processing_time_ms": 75.1,
                "explanation": {"text": "Found books matching fantasy themes..."},
            }
        }


# Enhanced middleware for request tracking, metrics, and tracing
@app.middleware("http")
async def enhanced_request_middleware(request: Request, call_next):
    """Enhanced middleware for tracking, tracing, and monitoring."""
    start_time = time.time()

    # Generate correlation ID and set it in context
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    request.state.correlation_id = correlation_id

    # Create trace span for this request
    with tracer.start_as_current_span(
        f"{request.method} {request.url.path}",
        attributes={
            "http.method": request.method,
            "http.url": str(request.url),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "correlation_id": correlation_id,
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    ) as span:
        # Track active requests
        metrics_collector.track_request_start(request.method, request.url.path)

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            metrics_collector.track_request_end(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration,
            )

            # Update span with response information
            span.set_attributes(
                {
                    "http.status_code": response.status_code,
                    "http.response_size": response.headers.get(
                        "content-length", "unknown"
                    ),
                    "duration_ms": duration * 1000,
                }
            )

            # Add response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Processing-Time"] = f"{duration:.3f}s"

            # Log request/response with structured logging
            logger.info(
                "Request completed",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration * 1000,
                user_agent=request.headers.get("user-agent"),
                ip=request.client.host if request.client else "unknown",
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record error metrics
            metrics_collector.track_request_error(
                method=request.method,
                endpoint=request.url.path,
                error_type=type(e).__name__,
            )

            # Update span with error information
            span.set_status(status=trace.Status(trace.StatusCode.ERROR, str(e)))
            span.set_attributes(
                {
                    "error": True,
                    "error.type": type(e).__name__,
                    "error.message": str(e),
                    "duration_ms": duration * 1000,
                }
            )

            logger.error(
                "Request failed",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration * 1000,
                exc_info=True,
            )

            raise
        finally:
            # Decrement active requests
            metrics_collector.track_request_end_gauge()


# Exception handlers
@app.exception_handler(GoodBooksException)
async def goodbooks_exception_handler(request: Request, exc: GoodBooksException):
    """Handle custom application exceptions."""
    logger.warning(
        f"Application error: {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "error_type": type(exc).__name__,
            "details": exc.details,
        },
    )

    status_map = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        RecommendationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        CacheError: status.HTTP_503_SERVICE_UNAVAILABLE,
    }

    return JSONResponse(
        status_code=status_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR),
        content={
            "error": {
                "type": type(exc).__name__,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "HTTPException",
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={"request_id": request_id, "error_type": type(exc).__name__},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred",
                "request_id": request_id,
            }
        },
    )


# Helper functions
async def generate_cache_key(request: RecommendationRequest) -> str:
    """Generate cache key for recommendation request."""
    key_parts = []

    if request.user_id:
        key_parts.append(f"user:{request.user_id}")
    if request.book_title:
        key_parts.append(f"book:{request.book_title}")

    key_parts.append(f"n:{request.n_recommendations}")

    key_string = "|".join(key_parts)
    return f"recommendations:{hashlib.md5(key_string.encode()).hexdigest()}"


async def get_cached_recommendations(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get recommendations from cache."""
    try:
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            CACHE_OPERATIONS.labels(operation="get", result="hit").inc()
            return cached_data
        else:
            CACHE_OPERATIONS.labels(operation="get", result="miss").inc()
            return None
    except Exception as e:
        CACHE_OPERATIONS.labels(operation="get", result="error").inc()
        logger.warning(f"Cache get failed: {str(e)}")
        return None


async def cache_recommendations(cache_key: str, data: Dict[str, Any], ttl: int):
    """Cache recommendations data."""
    try:
        await cache_manager.set(cache_key, data, ttl=ttl)
        CACHE_OPERATIONS.labels(operation="set", result="success").inc()
    except Exception as e:
        CACHE_OPERATIONS.labels(operation="set", result="error").inc()
        logger.warning(f"Cache set failed: {str(e)}")


import hashlib

# API Routes


@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "GoodBooks Recommender API",
        "version": api.version,
        "environment": settings.environment,
        "docs_url": api.docs_url,
        "status": "running",
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    Comprehensive health check endpoint for load balancer monitoring.

    Returns detailed health status of all system components including:
    - Redis cache connectivity
    - ML model availability
    - Data file availability
    - System resources
    - Instance information
    """
    start_time = time.time()
    checks = {}
    overall_status = "healthy"
    instance_id = os.getenv("INSTANCE_ID", "unknown")

    # Check cache connection
    try:
        if cache_manager.connected:
            await cache_manager.redis.ping()
            # Test a simple cache operation
            test_key = f"health_check:{int(time.time())}"
            await cache_manager.set(test_key, "ok", ttl=60)
            await cache_manager.delete(test_key)
            checks["cache"] = {
                "status": "healthy",
                "details": "Redis connection active and operational",
                "response_time_ms": round((time.time() - start_time) * 1000, 2),
            }
        else:
            checks["cache"] = {
                "status": "degraded",
                "details": "Redis not connected, using in-memory fallback",
            }
            if settings.is_production:
                overall_status = "unhealthy"
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "details": f"Redis error: {str(e)}"}
        overall_status = "unhealthy"

    # Check recommender system
    try:
        if recommender and hasattr(recommender, "is_fitted") and recommender.is_fitted:
            # Test a quick recommendation
            test_start = time.time()
            test_recs = await recommender.get_recommendations(
                user_id=1, n_recommendations=1
            )
            test_time = (time.time() - test_start) * 1000

            checks["recommender"] = {
                "status": "healthy",
                "details": "Models loaded and operational",
                "test_recommendation_time_ms": round(test_time, 2),
            }
        else:
            checks["recommender"] = {
                "status": "unhealthy",
                "details": "Models not loaded or not fitted",
            }
            overall_status = "unhealthy"
    except Exception as e:
        checks["recommender"] = {
            "status": "unhealthy",
            "details": f"Recommender error: {str(e)}",
        }
        overall_status = "unhealthy"

    # Check data availability
    try:
        if data_loader:
            data_paths = settings.data_paths
            missing_files = [
                name for name, path in data_paths.items() if not path.exists()
            ]

            if not missing_files:
                checks["data"] = {
                    "status": "healthy",
                    "details": "All data files available",
                    "files_count": len(data_paths),
                }
            else:
                checks["data"] = {
                    "status": "unhealthy",
                    "details": f"Missing files: {missing_files}",
                }
                overall_status = "unhealthy"
        else:
            checks["data"] = {
                "status": "unhealthy",
                "details": "Data loader not initialized",
            }
            overall_status = "unhealthy"
    except Exception as e:
        checks["data"] = {
            "status": "unhealthy",
            "details": f"Data check error: {str(e)}",
        }
        overall_status = "unhealthy"

    # System resource checks
    try:
        import psutil

        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent
        cpu_percent = psutil.cpu_percent(interval=0.1)

        resource_status = "healthy"
        if memory_percent > 90 or disk_percent > 90 or cpu_percent > 95:
            resource_status = "critical"
            overall_status = "unhealthy"
        elif memory_percent > 80 or disk_percent > 80 or cpu_percent > 80:
            resource_status = "warning"
            if overall_status == "healthy":
                overall_status = "degraded"

        checks["resources"] = {
            "status": resource_status,
            "memory_percent": round(memory_percent, 1),
            "disk_percent": round(disk_percent, 1),
            "cpu_percent": round(cpu_percent, 1),
        }
    except ImportError:
        # psutil not available, skip resource checks
        checks["resources"] = {
            "status": "unknown",
            "details": "Resource monitoring not available",
        }
    except Exception as e:
        checks["resources"] = {
            "status": "error",
            "details": f"Resource check error: {str(e)}",
        }

    health_check_duration = time.time() - start_time

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=api.version,
        environment=settings.environment,
        instance_id=instance_id,
        uptime_seconds=health_check_duration,
        health_check_duration_ms=round(health_check_duration * 1000, 2),
        checks=checks,
    )


@app.get(api.metrics_path, tags=["Monitoring"])
async def get_metrics():
    """Prometheus metrics endpoint."""
    if not api.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# =====================================
# AUTHENTICATION & AUTHORIZATION ENDPOINTS
# =====================================


@app.post("/auth/register", response_model=dict, tags=["Authentication"])
async def register_user(user_data: dict):
    """
    Register a new user account.
    Creates a new user with role-based access control.
    """
    try:
        user = await oauth2_manager.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            role=UserRole.USER,  # Default role
        )

        logger.info(
            "User registered successfully", user_id=user.id, username=user.username
        )

        return {
            "message": "User registered successfully",
            "user_id": user.id,
            "username": user.username,
        }

    except Exception as e:
        logger.error("User registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@app.post("/auth/login", response_model=dict, tags=["Authentication"])
async def login_user(login_data: dict):
    """
    Authenticate user and return JWT tokens.
    Returns both access and refresh tokens for secure API access.
    """
    try:
        # Authenticate user
        user = await oauth2_manager.authenticate_user(
            login_data["username"], login_data["password"]
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Generate tokens
        access_token = oauth2_manager.create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )
        refresh_token = oauth2_manager.create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )

        logger.info(
            "User logged in successfully", user_id=user.id, username=user.username
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.security.jwt.access_token_expire_minutes * 60,
            "user": {"id": user.id, "username": user.username, "role": user.role},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@app.post("/auth/refresh", response_model=dict, tags=["Authentication"])
async def refresh_token(refresh_data: dict):
    """
    Refresh access token using valid refresh token.
    Extends user session without requiring re-authentication.
    """
    try:
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token is required",
            )

        # Verify and decode refresh token
        payload = oauth2_manager.verify_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        # Get user information
        username = payload.get("sub")
        user_id = payload.get("user_id")

        # Get current user to include latest role
        user = await oauth2_manager.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Generate new access token
        access_token = oauth2_manager.create_access_token(
            data={"sub": username, "user_id": user_id, "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.security.jwt.access_token_expire_minutes * 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed"
        )


@app.post("/auth/logout", tags=["Authentication"])
async def logout_user(
    current_user: User = Depends(get_current_user), token: str = Depends(oauth2_scheme)
):
    """
    Logout user and invalidate tokens.
    Adds token to blacklist to prevent reuse.
    """
    try:
        # Add token to blacklist
        await oauth2_manager.blacklist_token(token)

        logger.info(
            "User logged out successfully",
            user_id=current_user.id,
            username=current_user.username,
        )

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


# =====================================
# RECOMMENDATION ENDPOINTS (Protected)
# =====================================


@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    user_id: int = Depends(get_user_id),
):
    """
    Get personalized book recommendations with A/B testing support.

    Requires authentication via JWT token.
    Users can only get recommendations for themselves unless they have admin role.
    """
    REQUEST_COUNT.inc()

    start_time = time.time()
    experiment_id = getattr(request, "experiment_id", None)

    # RBAC: Users can only access their own recommendations unless admin
    if request.user_id and request.user_id != current_user.id:
        if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own recommendations",
            )

    # Use authenticated user's ID if not specified
    effective_user_id = request.user_id or current_user.id

    # Anonymize user data in logs (data privacy compliance)
    anonymized_user_id = data_privacy_service.anonymize_user_id(effective_user_id)
    logger.info(
        "Recommendation request received",
        anonymized_user_id=anonymized_user_id,
        book_title=request.book_title,
        n_recommendations=request.n_recommendations,
        experiment_id=experiment_id,
    )

    try:
        # Get appropriate recommender based on A/B testing
        current_recommender = get_recommender_for_request(
            effective_user_id, experiment_id
        )

        # Check cache first (using anonymized cache key for privacy)
        cache_key = f"recommendations:{anonymized_user_id}:{request.n_recommendations}"
        if experiment_id:
            cache_key += f":{experiment_id}"

        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            CACHE_OPERATIONS.labels(operation="get", result="hit").inc()
            response.headers["X-Cache"] = "HIT"

            # Still record metrics for A/B testing (anonymized)
            if experiment_id:
                background_tasks.add_task(
                    record_recommendation_metrics,
                    anonymized_user_id,
                    cached_result.get("recommendations", []),
                    experiment_id,
                    "cache_hit",
                )

            return RecommendationResponse(**cached_result)

        CACHE_OPERATIONS.labels(operation="get", result="miss").inc()

        # Generate recommendations
        if request.user_id or not request.book_title:
            # Use effective_user_id for actual recommendation generation
            recommendations_df = current_recommender.get_user_recommendations(
                user_id=effective_user_id, n_recommendations=request.n_recommendations
            )
        elif request.book_title:
            recommendations_df = current_recommender.get_content_recommendations(
                book_title=request.book_title,
                n_recommendations=request.n_recommendations,
            )
        else:
            recommendations_df = current_recommender.get_popular_recommendations(
                n_recommendations=request.n_recommendations
            )

        # Convert to response format
        recommendations = []
        for _, row in recommendations_df.iterrows():
            recommendations.append(
                BookRecommendation(
                    book_id=int(row["book_id"]),
                    title=row["title"],
                    authors=row.get("authors", "Unknown"),
                    score=float(row.get("score", 0.0)),
                    explanation=row.get("explanation", ""),
                )
            )

        result = {
            "recommendations": recommendations,
            "total_count": len(recommendations),
            "user_id": effective_user_id,  # Return actual user ID for client
            "book_title": request.book_title,
            "explanation": f"Generated using {current_recommender.__class__.__name__}",
            "experiment_id": experiment_id,
        }

        # Cache the result (using anonymized key)
        await cache_manager.set(cache_key, result, ttl=settings.cache_ttl)
        CACHE_OPERATIONS.labels(operation="set", result="success").inc()

        # Record A/B testing metrics (using anonymized user ID)
        if experiment_id:
            background_tasks.add_task(
                record_recommendation_metrics,
                anonymized_user_id,
                recommendations,
                experiment_id,
                "recommendation_generated",
            )

        # Record general metrics
        REQUEST_DURATION.observe(time.time() - start_time)
        RECOMMENDATION_COUNT.inc()

        response.headers["X-Cache"] = "MISS"
        if experiment_id:
            response.headers["X-Experiment-ID"] = experiment_id
            assignment = (
                ab_tester.experiments.get(experiment_id, {})
                .get("assignments", {})
                .get(effective_user_id, "control")
            )
            response.headers["X-Assignment"] = assignment

        return RecommendationResponse(**result)

    except Exception as e:
        ERROR_COUNT.labels(error_type=type(e).__name__).inc()
        logger.error(f"Recommendation generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations",
        )


# =====================================
# ADMIN ENDPOINTS (RBAC Protected)
# =====================================


@app.post("/admin/experiments", response_model=Dict[str, Any])
@require_roles([UserRole.ADMIN])
async def create_experiment(
    experiment_request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new A/B test experiment.

    Requires ADMIN role for access.
    """
    try:
        experiment_id = experiment_request["experiment_id"]
        description = experiment_request["description"]
        traffic_split = experiment_request.get("traffic_split", 0.1)
        metrics = experiment_request.get(
            "metrics", ["precision", "recall", "click_through_rate"]
        )

        logger.info(
            "A/B experiment creation requested",
            admin_user=current_user.username,
            experiment_id=experiment_id,
            traffic_split=traffic_split,
        )

        # Load control and variant models
        control_model = model_manager.load_model()  # Current production model

        variant_model_version = experiment_request.get("variant_model_version")
        if variant_model_version:
            variant_model = model_manager.load_model(variant_model_version)
        else:
            # Use the latest model as variant
            variant_model = model_manager.load_model()

        # Create experiment
        ab_tester.create_experiment(
            experiment_id=experiment_id,
            control_model=control_model,
            variant_model=variant_model,
            description=description,
            metrics=metrics,
            traffic_split=traffic_split,
        )

        return {
            "status": "success",
            "experiment_id": experiment_id,
            "message": f"Experiment created with {traffic_split*100}% traffic split",
        }

    except Exception as e:
        logger.error(f"Failed to create experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create experiment: {str(e)}",
        )


@app.get("/admin/experiments/{experiment_id}/results", response_model=Dict[str, Any])
@require_roles([UserRole.ADMIN, UserRole.MODERATOR])
async def get_experiment_results(
    experiment_id: str,
    time_window_hours: int = 24,
    current_user: User = Depends(get_current_active_user),
):
    """
    Get real-time results for an A/B test experiment.

    Requires ADMIN or MODERATOR role for access.
    """
    try:
        logger.info(
            "A/B experiment results requested",
            user=current_user.username,
            experiment_id=experiment_id,
            time_window_hours=time_window_hours,
        )

        results = ab_tester.get_real_time_results(experiment_id, time_window_hours)

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found",
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get experiment results: {str(e)}",
        )


@app.post("/admin/experiments/{experiment_id}/stop")
@require_roles([UserRole.ADMIN])
async def stop_experiment(
    experiment_id: str, current_user: User = Depends(get_current_active_user)
):
    """
    Stop a running A/B test experiment.

    Requires ADMIN role for access.
    """
    try:
        logger.info(
            "A/B experiment stop requested",
            admin_user=current_user.username,
            experiment_id=experiment_id,
        )

        ab_tester.stop_experiment(experiment_id)

        return {"status": "success", "message": f"Experiment {experiment_id} stopped"}

    except Exception as e:
        logger.error(f"Failed to stop experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop experiment: {str(e)}",
        )


# Model Management Endpoints


@app.get("/admin/models/current", response_model=Dict[str, Any])
@require_roles([UserRole.ADMIN, UserRole.MODERATOR])
async def get_current_model_info(current_user: User = Depends(get_current_active_user)):
    """
    Get information about the currently deployed model.

    Requires ADMIN or MODERATOR role for access.
    """
    try:
        logger.info("Model info requested", user=current_user.username)

        health = model_manager.get_model_health()
        metadata = model_manager.get_model_metadata()

        return {"health": health, "metadata": metadata, "status": "active"}

    except Exception as e:
        logger.error(f"Failed to get current model info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}",
        )


@app.post("/admin/models/deploy")
@require_roles([UserRole.ADMIN])
async def deploy_model(
    deployment_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    Deploy a new model version.

    Requires ADMIN role for access.
    """
    try:
        model_uri = deployment_request["model_uri"]
        version = deployment_request["version"]
        metadata = deployment_request.get("metadata", {})

        logger.info(
            "Model deployment requested",
            admin_user=current_user.username,
            model_uri=model_uri,
            version=version,
        )

        # Deploy in background to avoid blocking
        background_tasks.add_task(
            model_manager.deploy_model, model_uri, version, metadata
        )

        return {
            "status": "deployment_initiated",
            "model_uri": model_uri,
            "version": version,
            "message": "Model deployment started in background",
        }

    except Exception as e:
        logger.error(f"Failed to deploy model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deploy model: {str(e)}",
        )


@app.post("/admin/models/rollback")
@require_roles([UserRole.ADMIN])
async def rollback_model(
    rollback_request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
):
    """
    Rollback to a previous model version.

    Requires ADMIN role for access.
    """
    try:
        target_version = rollback_request.get("target_version")

        logger.info(
            "Model rollback requested",
            admin_user=current_user.username,
            target_version=target_version,
        )

        success = model_manager.rollback_model(target_version)

        if success:
            return {
                "status": "success",
                "message": f"Rolled back to version {target_version or 'previous'}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rollback failed",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rollback model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback model: {str(e)}",
        )


# Vector Store Management Endpoints


@app.get("/admin/vector-store/stats", response_model=Dict[str, Any])
@require_roles([UserRole.ADMIN, UserRole.MODERATOR])
async def get_vector_store_stats(current_user: User = Depends(get_current_active_user)):
    """
    Get vector store statistics and health information.

    Requires ADMIN or MODERATOR role for access.
    """
    try:
        logger.info("Vector store stats requested", user=current_user.username)

        if hasattr(vector_store, "get_statistics"):
            stats = vector_store.get_statistics()
        else:
            stats = {
                "status": "basic_vector_store",
                "message": "Enhanced vector store statistics not available",
            }

        return stats

    except Exception as e:
        logger.error(f"Failed to get vector store stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vector store stats: {str(e)}",
        )


@app.post("/admin/vector-store/rebuild")
@require_roles([UserRole.ADMIN])
async def rebuild_vector_store(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    Trigger vector store rebuild (runs in background).

    Requires ADMIN role for access.
    """
    try:
        logger.info("Vector store rebuild requested", admin_user=current_user.username)

        async def rebuild_task():
            try:
                # Reload data
                books, ratings, tags, book_tags = (
                    await data_loader.load_datasets_async()
                )
                merged_books = await data_loader.merge_book_metadata_async(
                    books, book_tags, tags
                )
                processed_books = await data_loader.preprocess_tags_async(merged_books)

                # Rebuild vector store
                await vector_store.build_from_books_async(processed_books)
                logger.info("Vector store rebuild completed successfully")

            except Exception as e:
                logger.error(f"Vector store rebuild failed: {str(e)}")

        background_tasks.add_task(rebuild_task)

        return {
            "status": "rebuild_initiated",
            "message": "Vector store rebuild started in background",
        }

    except Exception as e:
        logger.error(f"Failed to initiate vector store rebuild: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate rebuild: {str(e)}",
        )


# =====================================
# METRICS & ANALYTICS ENDPOINTS
# =====================================


@app.post("/metrics/interaction")
async def record_interaction_metric(
    interaction_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """
    Record user interaction metrics for A/B testing analysis.

    Automatically anonymizes user data for privacy compliance.
    """
    try:
        user_id = interaction_data["user_id"]
        experiment_id = interaction_data.get("experiment_id")
        metric_name = interaction_data["metric_name"]
        value = interaction_data["value"]

        # Verify user can only record metrics for themselves (unless admin)
        if user_id != current_user.id and current_user.role not in [
            UserRole.ADMIN,
            UserRole.MODERATOR,
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only record metrics for yourself",
            )

        # Anonymize user ID for privacy compliance
        anonymized_user_id = data_privacy_service.anonymize_user_id(user_id)

        logger.info(
            "Interaction metric recorded",
            anonymized_user_id=anonymized_user_id,
            metric_name=metric_name,
            experiment_id=experiment_id,
        )

        if experiment_id and ab_tester:
            ab_tester.record_real_time_metric(
                experiment_id=experiment_id,
                user_id=anonymized_user_id,  # Use anonymized ID
                metric_name=metric_name,
                value=value,
            )

        return {"status": "success", "message": "Metric recorded"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record interaction metric: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record metric: {str(e)}",
        )


# Enhanced Health Check with A/B Testing and Model Status


@app.get("/health", response_model=Dict[str, Any])
async def enhanced_health_check():
    """Enhanced health check including ML pipeline components."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {},
    }

    try:
        # Basic API health
        health_status["components"]["api"] = {"status": "healthy"}

        # Model manager health
        if model_manager:
            model_health = model_manager.get_model_health()
            health_status["components"]["model_manager"] = model_health

        # A/B testing health
        if ab_tester:
            ab_health = {
                "status": "healthy",
                "active_experiments": len(
                    [
                        exp
                        for exp in ab_tester.experiments.values()
                        if exp.get("status") == "running"
                    ]
                ),
            }
            health_status["components"]["ab_testing"] = ab_health

        # Vector store health
        if vector_store:
            vs_health = {"status": "healthy"}
            if hasattr(vector_store, "get_statistics"):
                vs_stats = vector_store.get_statistics()
                vs_health.update(vs_stats)
            health_status["components"]["vector_store"] = vs_health

        # Cache health
        try:
            await cache_manager.get("health_check")
            health_status["components"]["cache"] = {"status": "healthy"}
        except Exception:
            health_status["components"]["cache"] = {"status": "degraded"}

        # Overall status
        component_statuses = [
            comp.get("status", "unknown")
            for comp in health_status["components"].values()
        ]

        if any(status == "error" for status in component_statuses):
            health_status["status"] = "error"
        elif any(status in ["degraded", "no_model"] for status in component_statuses):
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }

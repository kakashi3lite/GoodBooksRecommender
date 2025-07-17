"""
🚀 Optimized API Endpoints with Advanced Performance Features
Implements connection pooling, request batching, and smart caching for maximum throughput
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aioredis
import asyncpg
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, Histogram
from pydantic import BaseModel, Field, validator

from src.core.cache import AsyncCacheManager
from src.core.enhanced_logging import StructuredLogger
from src.core.exceptions import RecommendationError, ValidationError
from src.core.settings import settings
from src.models.hybrid_recommender import HybridRecommender

logger = StructuredLogger(__name__)

# Prometheus metrics for monitoring
RECOMMENDATION_REQUESTS = Counter(
    "recommendations_requests_total",
    "Total recommendation requests",
    ["user_type", "cache_hit"],
)

RECOMMENDATION_DURATION = Histogram(
    "recommendations_duration_seconds",
    "Recommendation request duration",
    ["cache_hit", "batch_size"],
)

ACTIVE_CONNECTIONS = Gauge(
    "active_database_connections", "Number of active database connections"
)


class OptimizedRecommendationRequest(BaseModel):
    """Optimized request model with validation and defaults"""

    user_id: Optional[int] = Field(
        None, gt=0, description="User ID for collaborative filtering"
    )
    book_title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Book title for content-based filtering",
    )
    n_recommendations: int = Field(
        5, ge=1, le=50, description="Number of recommendations"
    )
    include_explanations: bool = Field(
        False, description="Include recommendation explanations"
    )

    @validator("user_id", "book_title")
    def validate_inputs(cls, v, values):
        """Ensure at least one input method is provided"""
        if not v and not values.get("book_title") and not values.get("user_id"):
            raise ValueError("Either user_id or book_title must be provided")
        return v


class BatchRecommendationRequest(BaseModel):
    """Batch request for multiple users"""

    user_ids: List[int] = Field(
        ..., min_items=1, max_items=100, description="List of user IDs"
    )
    n_recommendations: int = Field(
        5, ge=1, le=50, description="Number of recommendations per user"
    )
    include_explanations: bool = Field(
        False, description="Include recommendation explanations"
    )


class RecommendationResponse(BaseModel):
    """Optimized response model"""

    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    cache_info: Dict[str, Any]


class DatabaseConnectionPool:
    """Optimized database connection pool manager"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize connection pool with optimized settings"""
        if self.pool is None:
            async with self._lock:
                if self.pool is None:  # Double-check locking
                    self.pool = await asyncpg.create_pool(
                        dsn=settings.database.url,
                        min_size=settings.database.pool_min_size,
                        max_size=settings.database.pool_max_size,
                        max_queries=50000,
                        max_inactive_connection_lifetime=300,
                        command_timeout=30,
                        server_settings={
                            "jit": "off",  # Disable JIT for faster simple queries
                            "application_name": "goodbooks_api",
                        },
                    )

                    logger.info(
                        "Database connection pool initialized",
                        min_size=settings.database.pool_min_size,
                        max_size=settings.database.pool_max_size,
                    )

    async def get_connection(self):
        """Get connection from pool with metrics"""
        if self.pool is None:
            await self.initialize()

        connection = await self.pool.acquire()
        ACTIVE_CONNECTIONS.inc()
        return connection

    async def release_connection(self, connection):
        """Release connection back to pool"""
        await self.pool.release(connection)
        ACTIVE_CONNECTIONS.dec()

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None


class SmartCache:
    """Enhanced cache with intelligent prefetching and TTL management"""

    def __init__(self, cache_manager: AsyncCacheManager):
        self.cache = cache_manager
        self.prefetch_queue = asyncio.Queue(maxsize=1000)
        self.cache_stats = {"hits": 0, "misses": 0, "prefetch_hits": 0}

    async def get_with_fallback(
        self, key: str, fallback_fn, ttl: int = 3600, prefetch: bool = True
    ) -> tuple[Any, bool]:
        """Get from cache with intelligent fallback and prefetching"""
        # Try primary cache
        cached_value = await self.cache.get(key)

        if cached_value is not None:
            self.cache_stats["hits"] += 1

            # Asynchronous prefetch refresh if TTL is near expiration
            if prefetch:
                await self._maybe_prefetch(key, fallback_fn, ttl)

            return cached_value, True

        self.cache_stats["misses"] += 1

        # Cache miss - compute value
        value = await fallback_fn()

        # Cache the result
        await self.cache.set(key, value, ttl)

        return value, False

    async def _maybe_prefetch(self, key: str, fallback_fn, ttl: int):
        """Queue prefetch operation if cache entry is aging"""
        # Check if we should prefetch (when TTL < 25% remaining)
        ttl_remaining = await self.cache.redis.ttl(key)

        if ttl_remaining > 0 and ttl_remaining < (ttl * 0.25):
            try:
                await self.prefetch_queue.put_nowait((key, fallback_fn, ttl))
            except asyncio.QueueFull:
                # Queue full, skip prefetch
                pass

    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """Optimized batch cache retrieval"""
        if not keys:
            return {}

        # Use Redis pipeline for batch operations
        async with self.cache.redis.pipeline() as pipe:
            for key in keys:
                pipe.get(key)
            results = await pipe.execute()

        # Parse results
        cache_results = {}
        for key, result in zip(keys, results):
            if result is not None:
                try:
                    cache_results[key] = (
                        json.loads(result) if isinstance(result, str) else result
                    )
                    self.cache_stats["hits"] += 1
                except (json.JSONDecodeError, TypeError):
                    self.cache_stats["misses"] += 1
            else:
                self.cache_stats["misses"] += 1

        return cache_results


class OptimizedRecommendationService:
    """High-performance recommendation service with batching and caching"""

    def __init__(self):
        self.recommender = HybridRecommender(max_workers=8)  # Increased parallelism
        self.cache_manager = None
        self.smart_cache = None
        self.db_pool = DatabaseConnectionPool()
        self.request_buffer = []
        self.buffer_lock = asyncio.Lock()
        self.batch_size = 10
        self.batch_timeout = 0.1  # 100ms batch window

    async def initialize(self):
        """Initialize service components"""
        self.cache_manager = AsyncCacheManager()
        await self.cache_manager.initialize()
        self.smart_cache = SmartCache(self.cache_manager)
        await self.db_pool.initialize()

        # Start background batch processor
        asyncio.create_task(self._batch_processor())

        logger.info("Optimized recommendation service initialized")

    async def _batch_processor(self):
        """Background task to process batched requests"""
        while True:
            try:
                # Wait for batch timeout or buffer to fill
                await asyncio.sleep(self.batch_timeout)

                async with self.buffer_lock:
                    if not self.request_buffer:
                        continue

                    batch = self.request_buffer[: self.batch_size]
                    self.request_buffer = self.request_buffer[self.batch_size :]

                # Process batch
                if batch:
                    await self._process_batch(batch)

            except Exception as e:
                logger.error("Batch processor error", error=str(e), exc_info=True)

    async def _process_batch(self, batch: List[tuple]):
        """Process a batch of recommendation requests"""
        logger.debug("Processing batch", batch_size=len(batch))

        # Group by request type for optimal processing
        user_requests = []
        book_requests = []

        for request_data, future in batch:
            if request_data.get("user_id"):
                user_requests.append((request_data, future))
            elif request_data.get("book_title"):
                book_requests.append((request_data, future))

        # Process user-based requests in batch
        if user_requests:
            await self._process_user_batch(user_requests)

        # Process book-based requests
        if book_requests:
            await self._process_book_batch(book_requests)

    async def _process_user_batch(self, user_requests: List[tuple]):
        """Process batch of user-based recommendations"""
        # Extract user IDs
        user_ids = [req[0]["user_id"] for req, _ in user_requests]

        # Check cache for all users at once
        cache_keys = [
            f"user_recs:{uid}:{req[0]['n_recommendations']}"
            for req, _ in user_requests
            for uid in [req[0]["user_id"]]
        ]

        cached_results = await self.smart_cache.batch_get(cache_keys)

        # Process cache misses
        for (request_data, future), cache_key in zip(user_requests, cache_keys):
            try:
                if cache_key in cached_results:
                    # Cache hit
                    result = cached_results[cache_key]
                    future.set_result(result)
                else:
                    # Cache miss - generate recommendations
                    recommendations = await self._generate_recommendations(request_data)

                    # Cache the result
                    await self.smart_cache.cache.set(
                        cache_key, recommendations, ttl=1800
                    )

                    future.set_result(recommendations)

            except Exception as e:
                future.set_exception(e)

    async def _process_book_batch(self, book_requests: List[tuple]):
        """Process batch of book-based recommendations"""
        for request_data, future in book_requests:
            try:
                # Book-based requests are processed individually (for now)
                cache_key = f"book_recs:{hashlib.md5(request_data['book_title'].encode()).hexdigest()}:{request_data['n_recommendations']}"

                async def generate_fn():
                    return await self._generate_recommendations(request_data)

                result, was_cached = await self.smart_cache.get_with_fallback(
                    cache_key, generate_fn, ttl=3600
                )

                future.set_result(result)

            except Exception as e:
                future.set_exception(e)

    async def _generate_recommendations(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate recommendations using the hybrid model"""
        start_time = time.perf_counter()

        try:
            # Get recommendations
            recommendations_df = self.recommender.get_recommendations(
                user_id=request_data.get("user_id"),
                book_title=request_data.get("book_title"),
                n_recommendations=request_data["n_recommendations"],
            )

            # Convert to response format
            recommendations = recommendations_df.to_dict("records")

            generation_time = (time.perf_counter() - start_time) * 1000

            return {
                "recommendations": recommendations,
                "metadata": {
                    "generation_time_ms": round(generation_time, 2),
                    "model_version": "hybrid_v2.0",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        except Exception as e:
            logger.error(
                "Recommendation generation failed", error=str(e), request=request_data
            )
            raise RecommendationError(f"Failed to generate recommendations: {str(e)}")

    async def get_recommendations_optimized(
        self, request: OptimizedRecommendationRequest
    ) -> Dict[str, Any]:
        """Get recommendations with optimal performance"""
        start_time = time.perf_counter()

        # Create future for async result
        future = asyncio.Future()
        request_data = request.dict()

        # Add to batch queue
        async with self.buffer_lock:
            self.request_buffer.append((request_data, future))

        # Wait for result
        try:
            result = await asyncio.wait_for(future, timeout=10.0)

            # Add cache information
            cache_info = {
                "cache_stats": self.smart_cache.cache_stats.copy(),
                "response_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
            }

            return {**result, "cache_info": cache_info}

        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Request timeout")

    async def get_batch_recommendations(
        self, request: BatchRecommendationRequest
    ) -> List[Dict[str, Any]]:
        """Get recommendations for multiple users efficiently"""
        start_time = time.perf_counter()

        # Create cache keys for all users
        cache_keys = [
            f"user_recs:{user_id}:{request.n_recommendations}"
            for user_id in request.user_ids
        ]

        # Batch cache lookup
        cached_results = await self.smart_cache.batch_get(cache_keys)

        # Identify cache misses
        results = []
        cache_misses = []

        for user_id, cache_key in zip(request.user_ids, cache_keys):
            if cache_key in cached_results:
                results.append(
                    {"user_id": user_id, **cached_results[cache_key], "cache_hit": True}
                )
            else:
                cache_misses.append(user_id)

        # Generate recommendations for cache misses
        if cache_misses:
            # Process in parallel with limited concurrency
            semaphore = asyncio.Semaphore(10)

            async def generate_for_user(user_id: int):
                async with semaphore:
                    try:
                        req_data = {
                            "user_id": user_id,
                            "n_recommendations": request.n_recommendations,
                        }

                        result = await self._generate_recommendations(req_data)

                        # Cache the result
                        cache_key = f"user_recs:{user_id}:{request.n_recommendations}"
                        await self.smart_cache.cache.set(cache_key, result, ttl=1800)

                        return {"user_id": user_id, **result, "cache_hit": False}

                    except Exception as e:
                        logger.error(
                            f"Failed to generate recommendations for user {user_id}",
                            error=str(e),
                        )
                        return {"user_id": user_id, "error": str(e), "cache_hit": False}

            # Execute parallel generation
            miss_results = await asyncio.gather(
                *[generate_for_user(user_id) for user_id in cache_misses],
                return_exceptions=True,
            )

            # Add to results
            for result in miss_results:
                if not isinstance(result, Exception):
                    results.append(result)

        total_time = (time.perf_counter() - start_time) * 1000

        # Sort results by user_id to maintain order
        results.sort(key=lambda x: x["user_id"])

        # Add batch metadata
        for result in results:
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["batch_total_time_ms"] = round(total_time, 2)
            result["metadata"]["batch_size"] = len(request.user_ids)

        return results


# Global service instance
recommendation_service = OptimizedRecommendationService()


async def get_recommendation_service() -> OptimizedRecommendationService:
    """Dependency injection for recommendation service"""
    if recommendation_service.cache_manager is None:
        await recommendation_service.initialize()
    return recommendation_service

"""
Advanced caching system with Redis integration.
Follows bookworm instructions for multi-level caching.
"""
import asyncio
import hashlib
import pickle
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, timedelta
import json

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from src.core.settings import settings
from src.core.logging import get_logger
from src.core.exceptions import CacheError

logger = get_logger(__name__)


class AsyncCacheManager:
    """
    Async cache manager with Redis backend.
    Implements sophisticated caching patterns with TTL, cache warming, and error handling.
    """
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.connected = False
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize Redis connection with retry logic."""
        try:
            self.redis = redis.Redis(
                host=settings.redis.host,
                port=settings.redis.port,
                password=settings.redis.password,
                db=settings.redis.db,
                decode_responses=settings.redis.decode_responses,
                socket_timeout=settings.redis.pool_timeout,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            self.connected = True
            
            logger.info(
                "Redis connection established",
                host=settings.redis.host,
                port=settings.redis.port,
                db=settings.redis.db
            )
            
        except (ConnectionError, TimeoutError) as e:
            logger.error(
                "Failed to connect to Redis",
                error=str(e),
                host=settings.redis.host,
                port=settings.redis.port
            )
            self.connected = False
            # Don't raise exception - allow graceful degradation
        except Exception as e:
            logger.error(
                "Unexpected error connecting to Redis",
                error=str(e),
                exc_info=True
            )
            self.connected = False
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("Redis connection closed")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from parameters."""
        # Create a consistent key from all parameters
        key_data = f"{prefix}"
        
        if args:
            key_data += f":{':'.join(str(arg) for arg in args)}"
        
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = ':'.join(f"{k}={v}" for k, v in sorted_kwargs)
            key_data += f":{kwargs_str}"
        
        # Hash long keys to keep them manageable
        if len(key_data) > 200:
            return f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
        
        return key_data
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.connected or not self.redis:
            return None
        
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                try:
                    # Try to deserialize as JSON first
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    # Fall back to pickle for complex objects
                    return pickle.loads(cached_data.encode('latin1'))
            return None
            
        except Exception as e:
            logger.warning(
                "Cache get operation failed",
                key=key,
                error=str(e)
            )
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.connected or not self.redis:
            return False
        
        try:
            # Try to serialize as JSON first (more efficient)
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                # Fall back to pickle for complex objects
                serialized_value = pickle.dumps(value).decode('latin1')
            
            ttl = ttl or settings.cache.ttl_default
            
            await self.redis.setex(key, ttl, serialized_value)
            
            logger.debug(
                "Cache set operation successful",
                key=key,
                ttl=ttl
            )
            return True
            
        except Exception as e:
            logger.warning(
                "Cache set operation failed",
                key=key,
                error=str(e)
            )
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.connected or not self.redis:
            return False
        
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.warning(
                "Cache delete operation failed",
                key=key,
                error=str(e)
            )
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.connected or not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(
                    "Deleted keys by pattern",
                    pattern=pattern,
                    count=deleted
                )
                return deleted
            return 0
        except Exception as e:
            logger.warning(
                "Cache pattern delete failed",
                pattern=pattern,
                error=str(e)
            )
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.connected or not self.redis:
            return False
        
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.warning(
                "Cache exists check failed",
                key=key,
                error=str(e)
            )
            return False
    
    async def get_recommendations(self, user_id: Optional[int], 
                                book_title: Optional[str],
                                n_recommendations: int) -> Optional[List[Dict]]:
        """Get cached recommendations."""
        key = self._generate_key(
            "recommendations",
            user_id=user_id,
            book_title=book_title,
            n_recs=n_recommendations
        )
        
        cached = await self.get(key)
        if cached:
            logger.debug(
                "Cache hit for recommendations",
                user_id=user_id,
                book_title=book_title,
                n_recommendations=n_recommendations
            )
        
        return cached
    
    async def cache_recommendations(self, user_id: Optional[int],
                                  book_title: Optional[str],
                                  n_recommendations: int,
                                  recommendations: List[Dict]) -> bool:
        """Cache recommendations with appropriate TTL."""
        key = self._generate_key(
            "recommendations",
            user_id=user_id,
            book_title=book_title,
            n_recs=n_recommendations
        )
        
        success = await self.set(
            key,
            recommendations,
            ttl=settings.cache.ttl_recommendations
        )
        
        if success:
            logger.debug(
                "Cached recommendations",
                user_id=user_id,
                book_title=book_title,
                n_recommendations=n_recommendations
            )
        
        return success
    
    async def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache entries for a user."""
        pattern = f"recommendations:*user_id={user_id}*"
        deleted = await self.delete_pattern(pattern)
        
        logger.info(
            "Invalidated user cache",
            user_id=user_id,
            deleted_keys=deleted
        )
        
        return deleted
    
    async def warm_cache_for_popular_users(self, user_ids: List[int]) -> None:
        """Pre-populate cache for popular users (background task)."""
        if not settings.cache.enable_cache_warming:
            return
        
        logger.info(
            "Starting cache warming",
            user_count=len(user_ids)
        )
        
        # This would typically call the recommendation service
        # Implementation depends on the recommendation service structure
        # For now, we'll just log the intent
        for user_id in user_ids:
            logger.debug(
                "Would warm cache for user",
                user_id=user_id
            )
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.connected or not self.redis:
            return {"connected": False}
        
        try:
            info = await self.redis.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }
        except Exception as e:
            logger.error(
                "Failed to get cache stats",
                error=str(e)
            )
            return {"connected": False, "error": str(e)}


# Global cache manager instance
cache_manager = AsyncCacheManager()

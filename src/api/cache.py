import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from redis import Redis, ConnectionError
from src.config import Config

logger = logging.getLogger(__name__)

class RecommendationCache:
    def __init__(self):
        self.config = Config()
        self.redis_client = self._initialize_redis()
        self.default_ttl = timedelta(hours=24)  # Cache for 24 hours by default
    
    def _initialize_redis(self) -> Optional[Redis]:
        """Initialize Redis connection with retry mechanism."""
        try:
            redis_client = Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                decode_responses=True,
                socket_timeout=5
            )
            # Test connection
            redis_client.ping()
            logger.info("Successfully connected to Redis")
            return redis_client
            
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            return None
    
    def _generate_cache_key(self, user_id: Optional[int], book_title: Optional[str], n_recommendations: int) -> str:
        """Generate a unique cache key based on request parameters."""
        components = [
            f"user_{user_id if user_id else 'none'}",
            f"book_{book_title if book_title else 'none'}",
            f"n_{n_recommendations}"
        ]
        return ":".join(components)
    
    def get_cached_recommendations(self, user_id: Optional[int], book_title: Optional[str], n_recommendations: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached recommendations if available."""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_cache_key(user_id, book_title, n_recommendations)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for key: {cache_key}")
                return json.loads(cached_data)
            
            logger.info(f"Cache miss for key: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    def cache_recommendations(self, user_id: Optional[int], book_title: Optional[str], n_recommendations: int, recommendations: Dict[str, Any], ttl: Optional[timedelta] = None) -> bool:
        """Cache recommendations with optional TTL."""
        if not self.redis_client:
            return False
            
        try:
            cache_key = self._generate_cache_key(user_id, book_title, n_recommendations)
            ttl = ttl or self.default_ttl
            
            # Add timestamp to cached data
            recommendations['cached_at'] = datetime.now().isoformat()
            
            # Store in Redis
            success = self.redis_client.setex(
                name=cache_key,
                time=int(ttl.total_seconds()),
                value=json.dumps(recommendations)
            )
            
            if success:
                logger.info(f"Successfully cached recommendations for key: {cache_key}")
            else:
                logger.warning(f"Failed to cache recommendations for key: {cache_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching recommendations: {str(e)}")
            return False
    
    def invalidate_cache(self, user_id: Optional[int] = None, book_title: Optional[str] = None) -> bool:
        """Invalidate cache entries for a specific user or book."""
        if not self.redis_client:
            return False
            
        try:
            pattern = None
            if user_id:
                pattern = f"user_{user_id}:*"
            elif book_title:
                pattern = f"*:book_{book_title}:*"
            
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache entries for pattern: {pattern}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis_client:
            return {"status": "disconnected"}
            
        try:
            info = self.redis_client.info()
            stats = {
                "status": "connected",
                "used_memory": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "total_keys": len(self.redis_client.keys("*")),
                "uptime_days": info.get('uptime_in_days')
            }
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def clear_all_cache(self) -> bool:
        """Clear all cached recommendations."""
        if not self.redis_client:
            return False
            
        try:
            self.redis_client.flushdb()
            logger.info("Cleared all cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
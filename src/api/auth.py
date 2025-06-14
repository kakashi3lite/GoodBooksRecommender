import time
import logging
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from redis import Redis
from src.config import Config

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

class RateLimiter:
    def __init__(self):
        self.config = Config()
        self.redis_client = self._initialize_redis()
        
        # Rate limiting configuration
        self.rate_limits = {
            'per_minute': 100,  # requests per minute
            'per_day': 1000     # requests per day
        }
    
    def _initialize_redis(self) -> Optional[Redis]:
        """Initialize Redis connection for rate limiting."""
        try:
            redis_client = Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_RATE_LIMIT_DB,  # Use different DB for rate limiting
                decode_responses=True,
                socket_timeout=5
            )
            redis_client.ping()
            return redis_client
        except Exception as e:
            logger.error(f"Failed to initialize Redis for rate limiting: {str(e)}")
            return None
    
    def _get_rate_limit_key(self, api_key: str, window: str) -> str:
        """Generate Redis key for rate limiting."""
        timestamp = datetime.now()
        if window == 'minute':
            time_window = timestamp.strftime('%Y-%m-%d-%H-%M')
        else:  # daily
            time_window = timestamp.strftime('%Y-%m-%d')
        return f"rate_limit:{api_key}:{window}:{time_window}"
    
    def is_rate_limited(self, api_key: str) -> bool:
        """Check if the request should be rate limited."""
        if not self.redis_client:
            return False  # If Redis is down, don't rate limit
        
        try:
            # Check minute limit
            minute_key = self._get_rate_limit_key(api_key, 'minute')
            minute_count = int(self.redis_client.get(minute_key) or 0)
            
            if minute_count >= self.rate_limits['per_minute']:
                logger.warning(f"Rate limit exceeded for API key {api_key} (per minute)")
                return True
            
            # Check daily limit
            day_key = self._get_rate_limit_key(api_key, 'day')
            day_count = int(self.redis_client.get(day_key) or 0)
            
            if day_count >= self.rate_limits['per_day']:
                logger.warning(f"Rate limit exceeded for API key {api_key} (per day)")
                return True
            
            # Increment counters
            pipeline = self.redis_client.pipeline()
            
            # Increment and set expiry for minute counter
            pipeline.incr(minute_key)
            pipeline.expire(minute_key, 60)  # Expire after 1 minute
            
            # Increment and set expiry for daily counter
            pipeline.incr(day_key)
            pipeline.expire(day_key, 86400)  # Expire after 24 hours
            
            pipeline.execute()
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return False
    
    def get_rate_limit_stats(self, api_key: str) -> Dict[str, int]:
        """Get current rate limit statistics for an API key."""
        if not self.redis_client:
            return {'per_minute': 0, 'per_day': 0}
        
        try:
            minute_key = self._get_rate_limit_key(api_key, 'minute')
            day_key = self._get_rate_limit_key(api_key, 'day')
            
            minute_count = int(self.redis_client.get(minute_key) or 0)
            day_count = int(self.redis_client.get(day_key) or 0)
            
            return {
                'per_minute': {
                    'current': minute_count,
                    'limit': self.rate_limits['per_minute'],
                    'remaining': max(0, self.rate_limits['per_minute'] - minute_count)
                },
                'per_day': {
                    'current': day_count,
                    'limit': self.rate_limits['per_day'],
                    'remaining': max(0, self.rate_limits['per_day'] - day_count)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {str(e)}")
            return {'per_minute': 0, 'per_day': 0}

class APIKeyAuth:
    def __init__(self):
        self.config = Config()
        self.rate_limiter = RateLimiter()
        
        # In a production environment, these would be stored in a secure database
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, Dict]:
        """Load API keys and their configurations."""
        # In production, load from secure storage (database, vault, etc.)
        return {
            self.config.DEFAULT_API_KEY: {
                'owner': 'default',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
        }
    
    async def verify_api_key(self, api_key: str = Security(API_KEY_HEADER)) -> str:
        """Verify API key and check rate limits."""
        if api_key not in self.api_keys:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        if not self.api_keys[api_key]['is_active']:
            raise HTTPException(
                status_code=403,
                detail="API key is inactive"
            )
        
        if self.rate_limiter.is_rate_limited(api_key):
            stats = self.rate_limiter.get_rate_limit_stats(api_key)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limits": stats
                }
            )
        
        return api_key

# Create global instances
api_key_auth = APIKeyAuth()
get_api_key = api_key_auth.verify_api_key
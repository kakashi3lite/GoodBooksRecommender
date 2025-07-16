"""
Redis-backed session memory store for maintaining user context and preferences.
Provides persistent storage of user interactions, preferences, and recommendation history.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from uuid import uuid4

try:
    import aioredis
    from aioredis import Redis
    # Try to import cluster support, fallback if not available
    try:
        from aioredis.cluster import RedisCluster
        CLUSTER_AVAILABLE = True
    except (ImportError, AttributeError):
        RedisCluster = None
        CLUSTER_AVAILABLE = False
    REDIS_AVAILABLE = True
except (ImportError, TypeError):
    # Handle import errors including Python 3.13 compatibility issues
    aioredis = None
    Redis = None
    RedisCluster = None
    REDIS_AVAILABLE = False
    CLUSTER_AVAILABLE = False

from src.core.logging import StructuredLogger
from src.core.exceptions import GoodBooksException
from src.core.settings import settings

logger = StructuredLogger(__name__)

class SessionStoreError(GoodBooksException):
    """Raised when session store operations fail"""
    pass

@dataclass
class UserSession:
    """User session data structure."""
    session_id: str
    user_id: Optional[int] = None
    created_at: datetime = None
    last_accessed: datetime = None
    preferences: Dict[str, Any] = None
    interaction_history: List[Dict[str, Any]] = None
    recommendation_history: List[Dict[str, Any]] = None
    search_history: List[Dict[str, Any]] = None
    context_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow()
        if self.preferences is None:
            self.preferences = {}
        if self.interaction_history is None:
            self.interaction_history = []
        if self.recommendation_history is None:
            self.recommendation_history = []
        if self.search_history is None:
            self.search_history = []
        if self.context_data is None:
            self.context_data = {}

@dataclass
class UserInteraction:
    """User interaction event."""
    timestamp: datetime
    interaction_type: str  # 'book_view', 'rating', 'search', 'recommendation_request'
    book_id: Optional[int] = None
    rating: Optional[float] = None
    search_query: Optional[str] = None
    recommendation_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class RedisSessionStore:
    """
    Redis-backed session store for user context management.
    Provides persistent storage with TTL support and efficient querying.
    """
    
    def __init__(
        self,        redis_url: Optional[str] = None,
        default_ttl: int = 86400,  # 24 hours
        max_history_items: int = 100
    ):
        """
        Initialize Redis session store.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default session TTL in seconds
            max_history_items: Maximum items to keep in history lists
        """
        self.redis_url = redis_url or f"redis://{settings.redis.host}:{settings.redis.port}"
        self.default_ttl = default_ttl
        self.max_history_items = max_history_items
        self.redis_client = None
          # Key prefixes for different data types        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.interaction_prefix = "interaction:"
        self.analytics_prefix = "analytics:"
    
    async def connect(self) -> None:
        """Establish Redis connection with cluster support."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory fallback for development")
            self.redis_client = None
            return
            
        try:
            # Check if cluster mode is enabled
            if settings.redis.cluster_enabled and settings.redis.cluster_nodes_list:
                await self._connect_cluster()
            else:
                await self._connect_single()
                
            # Test connection
            await self.redis_client.ping()            
            logger.info("Redis session store connected", 
                       cluster_mode=settings.redis.cluster_enabled,
                       url=self.redis_url)
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            # In development, continue with in-memory fallback
            if settings.is_development:
                logger.warning("Continuing with in-memory session store for development")
                self.redis_client = None
            else:
                raise SessionStoreError(f"Redis connection failed: {str(e)}") from e
    
    async def _connect_single(self) -> None:
        """Connect to single Redis instance."""
        self.redis_client = aioredis.from_url(
            self.redis_url,
            encoding=settings.redis.encoding,
            decode_responses=settings.redis.decode_responses,
            socket_connect_timeout=settings.redis.connection_timeout,
            socket_timeout=settings.redis.socket_timeout,
            password=settings.redis.password,
            ssl=settings.redis.ssl
        )
    
    async def _connect_cluster(self) -> None:
        """Connect to Redis cluster."""
        if not CLUSTER_AVAILABLE:
            logger.warning("Redis cluster not available, falling back to single instance")
            await self._connect_single()
            return
            
        # Create cluster connection
        startup_nodes = []
        for node in settings.redis.cluster_nodes_list:
            startup_nodes.append(aioredis.ConnectionPool(
                host=node["host"], 
                port=node["port"],
                password=settings.redis.password,
                ssl=settings.redis.ssl
            ))
        
        # For now, fall back to single connection until cluster support is more stable
        logger.info("Using single Redis connection (cluster support in development)")
        await self._connect_single()
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis session store disconnected")
    
    def _check_redis_available(self) -> bool:
        """Check if Redis is available and connected."""
        return REDIS_AVAILABLE and self.redis_client is not None
    
    async def create_session_async(
        self, 
        user_id: Optional[int] = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Create a new user session.
        
        Args:
            user_id: Optional user ID to associate with session
            ttl: Session TTL in seconds (uses default if not provided)
            
        Returns:
            Session ID string
            
        Raises:
            SessionStoreError: If session creation fails
        """
        try:
            # If Redis is not available, return a simple session ID for development
            if not self._check_redis_available():
                session_id = str(uuid4())
                logger.warning("Redis not available, returning session ID without storage", 
                             session_id=session_id)
                return session_id
            
            if not self.redis_client:
                await self.connect()
            
            session_id = str(uuid4())
            session = UserSession(session_id=session_id, user_id=user_id)
            
            # Store session data
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self._serialize_session(session)
            
            ttl = ttl or self.default_ttl
            await self.redis_client.setex(session_key, ttl, session_data)
            
            # If user_id provided, maintain user -> sessions mapping
            if user_id:
                user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                await self.redis_client.sadd(user_sessions_key, session_id)
                await self.redis_client.expire(user_sessions_key, ttl)
            
            logger.info(
                "Session created",
                session_id=session_id,
                user_id=user_id,
                ttl=ttl
            )
            
            return session_id
            
        except Exception as e:
            logger.error("Failed to create session", user_id=user_id, error=str(e))
            raise SessionStoreError(f"Session creation failed: {str(e)}") from e
    
    async def get_session_async(self, session_id: str) -> Optional[UserSession]:
        """
        Retrieve session by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            UserSession object or None if not found
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            session_key = f"{self.session_prefix}{session_id}"
            session_data = await self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            session = self._deserialize_session(session_data)
            
            # Update last accessed time
            session.last_accessed = datetime.utcnow()
            updated_data = self._serialize_session(session)
            
            # Reset TTL and update data
            await self.redis_client.setex(session_key, self.default_ttl, updated_data)
            
            return session
            
        except Exception as e:
            logger.error("Failed to retrieve session", session_id=session_id, error=str(e))
            return None
    
    async def update_session_async(
        self, 
        session_id: str, 
        **updates
    ) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session ID to update
            **updates: Fields to update in the session
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            session = await self.get_session_async(session_id)
            if not session:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            session.last_accessed = datetime.utcnow()
            
            # Save updated session
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self._serialize_session(session)
            await self.redis_client.setex(session_key, self.default_ttl, session_data)
            
            logger.info("Session updated", session_id=session_id, updates=list(updates.keys()))
            return True
            
        except Exception as e:
            logger.error("Failed to update session", session_id=session_id, error=str(e))
            return False
    
    async def add_interaction_async(
        self, 
        session_id: str, 
        interaction: UserInteraction
    ) -> bool:
        """
        Add user interaction to session history.
        
        Args:
            session_id: Session ID
            interaction: UserInteraction object
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            session = await self.get_session_async(session_id)
            if not session:
                return False
            
            # Add interaction to history
            interaction_dict = asdict(interaction)
            interaction_dict['timestamp'] = interaction.timestamp.isoformat()
            
            session.interaction_history.append(interaction_dict)
            
            # Trim history if too long
            if len(session.interaction_history) > self.max_history_items:
                session.interaction_history = session.interaction_history[-self.max_history_items:]
            
            # Update session
            return await self.update_session_async(
                session_id,
                interaction_history=session.interaction_history
            )
            
        except Exception as e:
            logger.error("Failed to add interaction", session_id=session_id, error=str(e))
            return False
    
    async def add_recommendation_history_async(
        self,
        session_id: str,
        recommendation_data: Dict[str, Any]
    ) -> bool:
        """
        Add recommendation to session history.
        
        Args:
            session_id: Session ID
            recommendation_data: Recommendation data
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            session = await self.get_session_async(session_id)
            if not session:
                return False
            
            # Add timestamp
            recommendation_data['timestamp'] = datetime.utcnow().isoformat()
            
            session.recommendation_history.append(recommendation_data)
            
            # Trim history if too long
            if len(session.recommendation_history) > self.max_history_items:
                session.recommendation_history = session.recommendation_history[-self.max_history_items:]
            
            return await self.update_session_async(
                session_id,
                recommendation_history=session.recommendation_history
            )
            
        except Exception as e:
            logger.error("Failed to add recommendation history", session_id=session_id, error=str(e))
            return False
    
    async def add_search_history_async(
        self,
        session_id: str,
        search_query: str,
        results_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add search to session history.
        
        Args:
            session_id: Session ID
            search_query: Search query string
            results_count: Number of results returned
            metadata: Optional search metadata
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            session = await self.get_session_async(session_id)
            if not session:
                return False
            
            search_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'query': search_query,
                'results_count': results_count,
                'metadata': metadata or {}
            }
            
            session.search_history.append(search_data)
            
            # Trim history if too long
            if len(session.search_history) > self.max_history_items:
                session.search_history = session.search_history[-self.max_history_items:]
            
            return await self.update_session_async(
                session_id,
                search_history=session.search_history
            )
            
        except Exception as e:
            logger.error("Failed to add search history", session_id=session_id, error=str(e))
            return False
    
    async def get_user_sessions_async(self, user_id: int) -> List[str]:
        """
        Get all session IDs for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of session IDs
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            session_ids = await self.redis_client.smembers(user_sessions_key)
            
            return list(session_ids) if session_ids else []
            
        except Exception as e:
            logger.error("Failed to get user sessions", user_id=user_id, error=str(e))
            return []
    
    async def delete_session_async(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            session_key = f"{self.session_prefix}{session_id}"
            result = await self.redis_client.delete(session_key)
            
            logger.info("Session deleted", session_id=session_id, existed=bool(result))
            return bool(result)
            
        except Exception as e:
            logger.error("Failed to delete session", session_id=session_id, error=str(e))
            return False
    
    async def cleanup_expired_sessions_async(self) -> int:
        """
        Clean up expired sessions (manual cleanup for keys without TTL).
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            # Scan for session keys
            session_keys = []
            async for key in self.redis_client.scan_iter(match=f"{self.session_prefix}*"):
                session_keys.append(key)
            
            # Check TTL and remove expired
            cleanup_count = 0
            for key in session_keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -1:  # No TTL set
                    await self.redis_client.delete(key)
                    cleanup_count += 1
                elif ttl == -2:  # Key doesn't exist
                    cleanup_count += 1
            
            logger.info("Session cleanup completed", cleaned_up=cleanup_count)
            return cleanup_count
            
        except Exception as e:
            logger.error("Session cleanup failed", error=str(e))
            return 0
    
    async def get_session_analytics_async(
        self, 
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get session analytics for the specified time range.
        
        Args:
            time_range_hours: Time range in hours to analyze
            
        Returns:
            Dictionary with analytics data
        """
        try:
            if not self.redis_client:
                await self.connect()
            
            # Get all session keys
            session_keys = []
            async for key in self.redis_client.scan_iter(match=f"{self.session_prefix}*"):
                session_keys.append(key)
            
            # Analyze sessions
            total_sessions = len(session_keys)
            active_sessions = 0
            user_sessions = 0
            anonymous_sessions = 0
            
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            for key in session_keys:
                session_data = await self.redis_client.get(key)
                if session_data:
                    try:
                        session = self._deserialize_session(session_data)
                        
                        if session.last_accessed >= cutoff_time:
                            active_sessions += 1
                        
                        if session.user_id:
                            user_sessions += 1
                        else:
                            anonymous_sessions += 1
                            
                    except Exception:
                        continue  # Skip malformed sessions
            
            analytics = {
                'timestamp': datetime.utcnow().isoformat(),
                'time_range_hours': time_range_hours,
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'user_sessions': user_sessions,
                'anonymous_sessions': anonymous_sessions,
                'activity_rate': active_sessions / total_sessions if total_sessions > 0 else 0
            }
            
            logger.info("Session analytics generated", analytics=analytics)
            return analytics
            
        except Exception as e:
            logger.error("Failed to generate session analytics", error=str(e))
            return {}
    
    def _serialize_session(self, session: UserSession) -> str:
        """Serialize session object to JSON string."""
        session_dict = asdict(session)
        
        # Convert datetime objects to ISO strings
        if session_dict['created_at']:
            session_dict['created_at'] = session.created_at.isoformat()
        if session_dict['last_accessed']:
            session_dict['last_accessed'] = session.last_accessed.isoformat()
        
        return json.dumps(session_dict)
    
    def _deserialize_session(self, session_data: str) -> UserSession:
        """Deserialize JSON string to session object."""
        session_dict = json.loads(session_data)
        
        # Convert ISO strings back to datetime objects
        if session_dict.get('created_at'):
            session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
        if session_dict.get('last_accessed'):
            session_dict['last_accessed'] = datetime.fromisoformat(session_dict['last_accessed'])
        
        return UserSession(**session_dict)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

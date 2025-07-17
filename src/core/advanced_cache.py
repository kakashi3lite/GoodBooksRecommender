"""
Advanced Multi-Level Caching System for GoodBooks Recommender

This module implements intelligent caching with:
- Multi-level cache hierarchy (L1: Memory, L2: Redis, L3: Database)
- Cache warming strategies
- Intelligent eviction policies
- Performance monitoring
- Cache analytics
"""

import asyncio
import hashlib
import json
import pickle
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from enum import Enum
import weakref

from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


class CacheLevel(Enum):
    """Cache level enumeration."""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DATABASE = "l3_database"


class EvictionPolicy(Enum):
    """Cache eviction policy options."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive based on access patterns


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int
    ttl: Optional[float] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()
    
    def _calculate_size(self) -> int:
        """Calculate approximate size of cached value."""
        try:
            if isinstance(self.value, (str, bytes)):
                return len(self.value)
            elif isinstance(self.value, (list, dict)):
                return len(str(self.value))
            else:
                return len(pickle.dumps(self.value))
        except Exception:
            return 1024  # Default size estimate
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    average_access_time: float = 0.0
    
    def update_hit_rate(self):
        """Update hit rate calculation."""
        total = self.hits + self.misses
        self.hit_rate = self.hits / total if total > 0 else 0.0


class CacheInterface(ABC):
    """Abstract cache interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        pass


class L1MemoryCache(CacheInterface):
    """
    Level 1 Memory Cache with intelligent eviction policies.
    
    Features:
    - Configurable eviction policies (LRU, LFU, TTL, Adaptive)
    - Size-based eviction
    - Access pattern analysis
    - Performance monitoring
    """
    
    def __init__(self, 
                 max_size_mb: int = 100,
                 max_entries: int = 10000,
                 eviction_policy: EvictionPolicy = EvictionPolicy.ADAPTIVE,
                 default_ttl: Optional[float] = 3600):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.eviction_policy = eviction_policy
        self.default_ttl = default_ttl
        
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []  # For LRU
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        
        # Adaptive policy state
        self._access_patterns: Dict[str, List[float]] = {}
        self._eviction_candidates: Set[str] = set()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache."""
        async with self._lock:
            start_time = time.time()
            
            if key not in self._cache:
                self._stats.misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                await self._remove_entry(key)
                self._stats.misses += 1
                return None
            
            # Update access metadata
            entry.touch()
            self._update_access_order(key)
            self._track_access_pattern(key)
            
            self._stats.hits += 1
            self._stats.update_hit_rate()
            self._stats.average_access_time = (
                self._stats.average_access_time * 0.9 + 
                (time.time() - start_time) * 0.1
            )
            
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in L1 cache."""
        async with self._lock:
            try:
                # Create new entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    access_count=1,
                    ttl=ttl or self.default_ttl
                )
                
                # Check if we need to evict
                while await self._should_evict(entry.size_bytes):
                    await self._evict_entry()
                
                # Store entry
                if key in self._cache:
                    old_entry = self._cache[key]
                    self._stats.total_size_bytes -= old_entry.size_bytes
                else:
                    self._stats.entry_count += 1
                
                self._cache[key] = entry
                self._stats.total_size_bytes += entry.size_bytes
                self._update_access_order(key)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to set cache entry: {str(e)}")
                return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from L1 cache."""
        async with self._lock:
            if key in self._cache:
                await self._remove_entry(key)
                return True
            return False
    
    async def clear(self) -> bool:
        """Clear all L1 cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._access_patterns.clear()
            self._eviction_candidates.clear()
            self._stats = CacheStats()
            return True
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in L1 cache."""
        async with self._lock:
            if key not in self._cache:
                return False
            
            entry = self._cache[key]
            if entry.is_expired():
                await self._remove_entry(key)
                return False
            
            return True
    
    def get_stats(self) -> CacheStats:
        """Get L1 cache statistics."""
        return self._stats
    
    async def warm_cache(self, key_value_pairs: List[Tuple[str, Any]]):
        """Warm cache with predefined key-value pairs."""
        for key, value in key_value_pairs:
            await self.set(key, value)
        
        logger.info(f"Warmed L1 cache with {len(key_value_pairs)} entries")
    
    async def get_cache_efficiency_report(self) -> Dict[str, Any]:
        """Get detailed cache efficiency report."""
        async with self._lock:
            # Calculate access frequency distribution
            access_counts = [entry.access_count for entry in self._cache.values()]
            avg_access_count = sum(access_counts) / len(access_counts) if access_counts else 0
            
            # Calculate age distribution
            current_time = time.time()
            ages = [current_time - entry.created_at for entry in self._cache.values()]
            avg_age = sum(ages) / len(ages) if ages else 0
            
            # Identify hot and cold entries
            hot_entries = [
                key for key, entry in self._cache.items()
                if entry.access_count > avg_access_count * 1.5
            ]
            
            cold_entries = [
                key for key, entry in self._cache.items()
                if entry.access_count < avg_access_count * 0.5
            ]
            
            return {
                "total_entries": len(self._cache),
                "total_size_mb": self._stats.total_size_bytes / (1024 * 1024),
                "hit_rate": self._stats.hit_rate,
                "average_access_count": avg_access_count,
                "average_age_seconds": avg_age,
                "hot_entries_count": len(hot_entries),
                "cold_entries_count": len(cold_entries),
                "eviction_policy": self.eviction_policy.value,
                "memory_utilization": self._stats.total_size_bytes / self.max_size_bytes
            }
    
    # Private methods
    
    async def _should_evict(self, new_entry_size: int) -> bool:
        """Check if eviction is needed."""
        return (
            len(self._cache) >= self.max_entries or
            self._stats.total_size_bytes + new_entry_size > self.max_size_bytes
        )
    
    async def _evict_entry(self):
        """Evict an entry based on the configured policy."""
        if not self._cache:
            return
        
        if self.eviction_policy == EvictionPolicy.LRU:
            key_to_evict = self._access_order[0]
        elif self.eviction_policy == EvictionPolicy.LFU:
            key_to_evict = min(self._cache.keys(), 
                             key=lambda k: self._cache[k].access_count)
        elif self.eviction_policy == EvictionPolicy.TTL:
            key_to_evict = min(self._cache.keys(), 
                             key=lambda k: self._cache[k].created_at)
        elif self.eviction_policy == EvictionPolicy.ADAPTIVE:
            key_to_evict = await self._adaptive_eviction()
        else:
            key_to_evict = next(iter(self._cache))
        
        await self._remove_entry(key_to_evict)
        self._stats.evictions += 1
    
    async def _adaptive_eviction(self) -> str:
        """Adaptive eviction based on access patterns."""
        current_time = time.time()
        scores = {}
        
        for key, entry in self._cache.items():
            # Calculate composite score based on:
            # - Recency (when last accessed)
            # - Frequency (access count)
            # - Size (larger entries less preferred)
            # - Access pattern (trending up/down)
            
            recency_score = (current_time - entry.last_accessed) / 3600  # Hours since last access
            frequency_score = 1.0 / (entry.access_count + 1)  # Inverse of access count
            size_score = entry.size_bytes / (1024 * 1024)  # Size in MB
            
            # Access pattern analysis
            pattern_score = 0.0
            if key in self._access_patterns and len(self._access_patterns[key]) > 1:
                recent_accesses = self._access_patterns[key][-5:]  # Last 5 access times
                if len(recent_accesses) >= 2:
                    # Calculate access trend (increasing = lower score = less likely to evict)
                    trend = (recent_accesses[-1] - recent_accesses[0]) / len(recent_accesses)
                    pattern_score = max(0, -trend)  # Negative trend (decreasing access) = higher score
            
            # Composite score (higher = more likely to evict)
            scores[key] = (recency_score * 0.4 + 
                          frequency_score * 0.3 + 
                          size_score * 0.2 + 
                          pattern_score * 0.1)
        
        return max(scores.keys(), key=lambda k: scores[k])
    
    async def _remove_entry(self, key: str):
        """Remove entry from cache and update metadata."""
        if key in self._cache:
            entry = self._cache[key]
            self._stats.total_size_bytes -= entry.size_bytes
            self._stats.entry_count -= 1
            del self._cache[key]
        
        if key in self._access_order:
            self._access_order.remove(key)
        
        if key in self._access_patterns:
            del self._access_patterns[key]
        
        self._eviction_candidates.discard(key)
    
    def _update_access_order(self, key: str):
        """Update access order for LRU tracking."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def _track_access_pattern(self, key: str):
        """Track access patterns for adaptive eviction."""
        current_time = time.time()
        
        if key not in self._access_patterns:
            self._access_patterns[key] = []
        
        self._access_patterns[key].append(current_time)
        
        # Keep only recent access times (last 10)
        if len(self._access_patterns[key]) > 10:
            self._access_patterns[key] = self._access_patterns[key][-10:]


class MultiLevelCache:
    """
    Multi-level cache system with L1 (Memory), L2 (Redis), and fallback to database.
    
    Features:
    - Automatic promotion/demotion between cache levels
    - Cache warming strategies
    - Performance monitoring across all levels
    - Intelligent cache key management
    """
    
    def __init__(self, 
                 l1_cache: L1MemoryCache,
                 l2_redis_client: Any = None,
                 l1_ttl: float = 300,  # 5 minutes
                 l2_ttl: float = 3600,  # 1 hour
                 promotion_threshold: int = 3):  # Promote after 3 L2 hits
        
        self.l1 = l1_cache
        self.l2_redis = l2_redis_client
        self.l1_ttl = l1_ttl
        self.l2_ttl = l2_ttl
        self.promotion_threshold = promotion_threshold
        
        # Track L2 access counts for promotion decisions
        self._l2_access_counts: Dict[str, int] = {}
        self._total_stats = CacheStats()
        
        # Cache warming state
        self._warming_tasks: Set[asyncio.Task] = set()
        self._warming_patterns: Dict[str, int] = {}  # key pattern -> frequency
    
    async def get(self, key: str, fallback_fn: Optional[callable] = None) -> Optional[Any]:
        """
        Get value from multi-level cache with optional fallback.
        
        Lookup order: L1 -> L2 -> Fallback function
        """
        start_time = time.time()
        cache_key = self._normalize_key(key)
        
        try:
            # Try L1 cache first
            value = await self.l1.get(cache_key)
            if value is not None:
                self._total_stats.hits += 1
                self._total_stats.update_hit_rate()
                logger.debug(f"Cache hit L1: {cache_key}")
                return value
            
            # Try L2 cache (Redis)
            if self.l2_redis:
                value = await self._get_from_l2(cache_key)
                if value is not None:
                    self._total_stats.hits += 1
                    self._total_stats.update_hit_rate()
                    
                    # Promote to L1 if accessed frequently
                    self._l2_access_counts[cache_key] = self._l2_access_counts.get(cache_key, 0) + 1
                    if self._l2_access_counts[cache_key] >= self.promotion_threshold:
                        await self.l1.set(cache_key, value, self.l1_ttl)
                        logger.debug(f"Promoted to L1: {cache_key}")
                    
                    logger.debug(f"Cache hit L2: {cache_key}")
                    return value
            
            # Fallback to provided function
            if fallback_fn:
                value = await self._execute_fallback(fallback_fn, key)
                if value is not None:
                    # Store in both L1 and L2
                    await self.set(cache_key, value)
                    logger.debug(f"Cached fallback result: {cache_key}")
                    return value
            
            self._total_stats.misses += 1
            self._total_stats.update_hit_rate()
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {str(e)}")
            self._total_stats.misses += 1
            self._total_stats.update_hit_rate()
            return None
        
        finally:
            duration = time.time() - start_time
            self._total_stats.average_access_time = (
                self._total_stats.average_access_time * 0.9 + 
                duration * 0.1
            )
    
    async def set(self, key: str, value: Any, l1_ttl: Optional[float] = None, 
                  l2_ttl: Optional[float] = None) -> bool:
        """Set value in multi-level cache."""
        cache_key = self._normalize_key(key)
        l1_ttl = l1_ttl or self.l1_ttl
        l2_ttl = l2_ttl or self.l2_ttl
        
        try:
            # Set in L1
            l1_success = await self.l1.set(cache_key, value, l1_ttl)
            
            # Set in L2 (Redis)
            l2_success = True
            if self.l2_redis:
                l2_success = await self._set_in_l2(cache_key, value, l2_ttl)
            
            # Track warming patterns
            self._track_warming_pattern(cache_key)
            
            return l1_success and l2_success
            
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from all cache levels."""
        cache_key = self._normalize_key(key)
        
        try:
            l1_success = await self.l1.delete(cache_key)
            
            l2_success = True
            if self.l2_redis:
                l2_success = await self._delete_from_l2(cache_key)
            
            # Clean up tracking data
            self._l2_access_counts.pop(cache_key, None)
            
            return l1_success and l2_success
            
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {str(e)}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache levels."""
        try:
            l1_success = await self.l1.clear()
            
            l2_success = True
            if self.l2_redis:
                l2_success = await self._clear_l2()
            
            # Clear tracking data
            self._l2_access_counts.clear()
            self._warming_patterns.clear()
            self._total_stats = CacheStats()
            
            return l1_success and l2_success
            
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False
    
    async def warm_cache(self, warming_config: Dict[str, Any]):
        """
        Intelligent cache warming based on configuration.
        
        warming_config:
        {
            "user_recommendations": {
                "user_ids": [1, 2, 3],
                "recommendation_types": ["hybrid", "content"],
                "priority": "high"
            },
            "popular_books": {
                "book_ids": [101, 102, 103],
                "priority": "medium"
            }
        }
        """
        try:
            warming_tasks = []
            
            for pattern, config in warming_config.items():
                task = asyncio.create_task(
                    self._warm_pattern(pattern, config)
                )
                warming_tasks.append(task)
                self._warming_tasks.add(task)
            
            # Wait for all warming tasks
            results = await asyncio.gather(*warming_tasks, return_exceptions=True)
            
            # Clean up completed tasks
            for task in warming_tasks:
                self._warming_tasks.discard(task)
            
            successful = sum(1 for r in results if not isinstance(r, Exception))
            
            logger.info(
                f"Cache warming completed: {successful}/{len(warming_tasks)} patterns successful"
            )
            
        except Exception as e:
            logger.error(f"Cache warming error: {str(e)}")
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics across all cache levels."""
        l1_stats = self.l1.get_stats()
        l1_efficiency = await self.l1.get_cache_efficiency_report()
        
        l2_stats = {"available": False}
        if self.l2_redis:
            l2_stats = await self._get_l2_stats()
        
        return {
            "overall": {
                "total_hits": self._total_stats.hits,
                "total_misses": self._total_stats.misses,
                "hit_rate": self._total_stats.hit_rate,
                "average_access_time": self._total_stats.average_access_time
            },
            "l1_memory": {
                "stats": l1_stats.__dict__,
                "efficiency": l1_efficiency
            },
            "l2_redis": l2_stats,
            "warming": {
                "active_tasks": len(self._warming_tasks),
                "patterns_tracked": len(self._warming_patterns),
                "top_patterns": sorted(
                    self._warming_patterns.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]
            },
            "promotion": {
                "l2_access_counts": len(self._l2_access_counts),
                "promotion_threshold": self.promotion_threshold
            }
        }
    
    # Private methods
    
    def _normalize_key(self, key: str) -> str:
        """Normalize cache key for consistency."""
        # Hash long keys to keep them manageable
        if len(key) > 200:
            return hashlib.md5(key.encode()).hexdigest()
        return key.replace(" ", "_").lower()
    
    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get value from L2 Redis cache."""
        try:
            data = await self.l2_redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"L2 cache get error: {str(e)}")
            return None
    
    async def _set_in_l2(self, key: str, value: Any, ttl: float) -> bool:
        """Set value in L2 Redis cache."""
        try:
            serialized = pickle.dumps(value)
            await self.l2_redis.setex(key, int(ttl), serialized)
            return True
        except Exception as e:
            logger.error(f"L2 cache set error: {str(e)}")
            return False
    
    async def _delete_from_l2(self, key: str) -> bool:
        """Delete key from L2 Redis cache."""
        try:
            await self.l2_redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"L2 cache delete error: {str(e)}")
            return False
    
    async def _clear_l2(self) -> bool:
        """Clear L2 Redis cache."""
        try:
            await self.l2_redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"L2 cache clear error: {str(e)}")
            return False
    
    async def _get_l2_stats(self) -> Dict[str, Any]:
        """Get L2 Redis cache statistics."""
        try:
            info = await self.l2_redis.info()
            return {
                "available": True,
                "memory_usage": info.get("used_memory", 0),
                "connected_clients": info.get("connected_clients", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"L2 stats error: {str(e)}")
            return {"available": False, "error": str(e)}
    
    async def _execute_fallback(self, fallback_fn: callable, key: str) -> Optional[Any]:
        """Execute fallback function safely."""
        try:
            if asyncio.iscoroutinefunction(fallback_fn):
                return await fallback_fn(key)
            else:
                return fallback_fn(key)
        except Exception as e:
            logger.error(f"Fallback function error: {str(e)}")
            return None
    
    def _track_warming_pattern(self, key: str):
        """Track patterns for intelligent cache warming."""
        # Extract pattern from key (e.g., "user_123_recommendations" -> "user_recommendations")
        pattern = self._extract_pattern(key)
        self._warming_patterns[pattern] = self._warming_patterns.get(pattern, 0) + 1
    
    def _extract_pattern(self, key: str) -> str:
        """Extract access pattern from cache key."""
        # Simple pattern extraction (can be made more sophisticated)
        parts = key.split("_")
        if len(parts) >= 2:
            return f"{parts[0]}_{parts[-1]}"
        return key
    
    async def _warm_pattern(self, pattern: str, config: Dict[str, Any]):
        """Warm cache for a specific pattern."""
        try:
            priority = config.get("priority", "medium")
            delay = {"high": 0, "medium": 0.1, "low": 0.5}.get(priority, 0.1)
            
            if pattern == "user_recommendations":
                await self._warm_user_recommendations(config, delay)
            elif pattern == "popular_books":
                await self._warm_popular_books(config, delay)
            # Add more patterns as needed
            
        except Exception as e:
            logger.error(f"Pattern warming error for {pattern}: {str(e)}")
    
    async def _warm_user_recommendations(self, config: Dict[str, Any], delay: float):
        """Warm user recommendation cache."""
        user_ids = config.get("user_ids", [])
        rec_types = config.get("recommendation_types", ["hybrid"])
        
        for user_id in user_ids:
            for rec_type in rec_types:
                key = f"user_{user_id}_recommendations_{rec_type}"
                # This would call your actual recommendation function
                # For now, we'll just set a placeholder
                await self.set(key, {"placeholder": "recommendations"})
                
                if delay > 0:
                    await asyncio.sleep(delay)
    
    async def _warm_popular_books(self, config: Dict[str, Any], delay: float):
        """Warm popular books cache."""
        book_ids = config.get("book_ids", [])
        
        for book_id in book_ids:
            key = f"book_{book_id}_details"
            # This would call your actual book details function
            await self.set(key, {"placeholder": "book_details"})
            
            if delay > 0:
                await asyncio.sleep(delay)

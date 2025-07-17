"""
Real-time Analytics System for GoodBooks Recommender

This module provides comprehensive real-time analytics including:
- User behavior tracking
- Recommendation performance metrics
- System performance monitoring
- Business intelligence metrics
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
try:
    import redis.asyncio as redis
    RedisClient = redis.Redis
except ImportError:
    import redis
    RedisClient = redis.Redis
from pydantic import BaseModel, Field

from src.core.logging import StructuredLogger
from src.core.monitoring import (
    REQUEST_COUNT, REQUEST_DURATION, RECOMMENDATIONS_GENERATED,
    MODEL_PREDICTIONS, MODEL_ACCURACY
)

logger = StructuredLogger(__name__)


@dataclass
class UserInteraction:
    """User interaction event data."""
    user_id: str
    event_type: str  # 'view', 'click', 'rating', 'search'
    item_id: Optional[str] = None
    timestamp: float = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RecommendationEvent:
    """Recommendation generation event."""
    user_id: str
    recommendation_type: str
    items_recommended: List[str]
    response_time_ms: float
    model_version: str
    timestamp: float = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context is None:
            self.context = {}


class RealTimeMetrics(BaseModel):
    """Real-time system metrics."""
    
    model_config = {"protected_namespaces": ()}
    
    # User metrics
    active_users_1min: int = 0
    active_users_5min: int = 0
    active_users_1hour: int = 0
    
    # Request metrics
    requests_per_second: float = 0.0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    
    # Recommendation metrics
    recommendations_per_minute: int = 0
    avg_recommendation_time: float = 0.0
    click_through_rate: float = 0.0
    
    # System metrics
    cache_hit_rate: float = 0.0
    model_prediction_accuracy: float = 0.0
    queue_length: int = 0
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RealTimeAnalytics:
    """
    Real-time analytics engine for tracking user behavior,
    system performance, and business metrics.
    """
    
    def __init__(self, redis_client: Any):
        self.redis = redis_client
        self.user_interactions: deque = deque(maxlen=10000)  # Last 10k interactions
        self.recommendation_events: deque = deque(maxlen=5000)  # Last 5k recommendations
        self.performance_metrics: deque = deque(maxlen=1000)  # Last 1k metric snapshots
        
        # Real-time counters
        self.active_users = set()
        self.request_times = deque(maxlen=1000)
        self.error_count = 0
        self.total_requests = 0
        
        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False
    
    async def start(self):
        """Start the analytics engine."""
        self._running = True
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._metrics_collector()),
            asyncio.create_task(self._cache_hit_rate_monitor()),
            asyncio.create_task(self._user_activity_tracker()),
            asyncio.create_task(self._performance_aggregator())
        ]
        
        logger.info("Real-time analytics engine started")
    
    async def stop(self):
        """Stop the analytics engine."""
        self._running = False
        
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        logger.info("Real-time analytics engine stopped")
    
    async def track_user_interaction(self, interaction: UserInteraction):
        """Track a user interaction event."""
        try:
            # Add to in-memory buffer
            self.user_interactions.append(interaction)
            
            # Update active users
            self.active_users.add(interaction.user_id)
            
            # Store in Redis with TTL
            redis_key = f"interaction:{interaction.user_id}:{int(interaction.timestamp)}"
            await self.redis.setex(
                redis_key,
                3600,  # 1 hour TTL
                json.dumps(asdict(interaction))
            )
            
            # Update real-time metrics
            await self._update_user_metrics()
            
            logger.debug(
                "User interaction tracked",
                user_id=interaction.user_id,
                event_type=interaction.event_type
            )
            
        except Exception as e:
            logger.error(f"Failed to track user interaction: {str(e)}")
    
    async def track_recommendation_event(self, event: RecommendationEvent):
        """Track a recommendation generation event."""
        try:
            # Add to in-memory buffer
            self.recommendation_events.append(event)
            
            # Update Prometheus metrics
            RECOMMENDATIONS_GENERATED.labels(
                recommendation_type=event.recommendation_type
            ).inc()
            
            MODEL_PREDICTIONS.labels(
                model_name="hybrid_recommender",
                model_version=event.model_version
            ).inc()
            
            # Store in Redis
            redis_key = f"recommendation:{event.user_id}:{int(event.timestamp)}"
            await self.redis.setex(
                redis_key,
                7200,  # 2 hours TTL
                json.dumps(asdict(event))
            )
            
            logger.debug(
                "Recommendation event tracked",
                user_id=event.user_id,
                type=event.recommendation_type,
                response_time=event.response_time_ms
            )
            
        except Exception as e:
            logger.error(f"Failed to track recommendation event: {str(e)}")
    
    async def track_request_metrics(self, endpoint: str, method: str, 
                                  status_code: int, response_time: float):
        """Track HTTP request metrics."""
        try:
            self.total_requests += 1
            self.request_times.append(response_time)
            
            if status_code >= 400:
                self.error_count += 1
            
            # Update Prometheus metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_time)
            
        except Exception as e:
            logger.error(f"Failed to track request metrics: {str(e)}")
    
    async def get_real_time_metrics(self) -> RealTimeMetrics:
        """Get current real-time metrics snapshot."""
        try:
            current_time = time.time()
            
            # Calculate active users for different time windows
            active_1min = await self._count_active_users(current_time - 60)
            active_5min = await self._count_active_users(current_time - 300)
            active_1hour = await self._count_active_users(current_time - 3600)
            
            # Calculate request metrics
            requests_per_second = len([
                t for t in self.request_times 
                if current_time - t < 60
            ]) / 60.0
            
            avg_response_time = (
                sum(self.request_times) / len(self.request_times)
                if self.request_times else 0.0
            )
            
            error_rate = (
                self.error_count / self.total_requests
                if self.total_requests > 0 else 0.0
            )
            
            # Calculate recommendation metrics
            recent_recommendations = [
                event for event in self.recommendation_events
                if current_time - event.timestamp < 60
            ]
            
            recommendations_per_minute = len(recent_recommendations)
            avg_recommendation_time = (
                sum(event.response_time_ms for event in recent_recommendations) /
                len(recent_recommendations)
                if recent_recommendations else 0.0
            )
            
            # Calculate CTR (simplified)
            ctr = await self._calculate_click_through_rate()
            
            # Get cache hit rate
            cache_hit_rate = await self._get_cache_hit_rate()
            
            return RealTimeMetrics(
                active_users_1min=active_1min,
                active_users_5min=active_5min,
                active_users_1hour=active_1hour,
                requests_per_second=requests_per_second,
                avg_response_time=avg_response_time,
                error_rate=error_rate,
                recommendations_per_minute=recommendations_per_minute,
                avg_recommendation_time=avg_recommendation_time,
                click_through_rate=ctr,
                cache_hit_rate=cache_hit_rate,
                model_prediction_accuracy=0.95,  # Placeholder - would come from ML monitoring
                queue_length=0  # Placeholder - would come from task queue
            )
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {str(e)}")
            return RealTimeMetrics()
    
    async def get_user_behavior_analytics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get user behavior analytics for specified time window."""
        try:
            current_time = time.time()
            recent_interactions = [
                interaction for interaction in self.user_interactions
                if current_time - interaction.timestamp < time_window
            ]
            
            # Analyze event types
            event_counts = defaultdict(int)
            user_sessions = defaultdict(set)
            
            for interaction in recent_interactions:
                event_counts[interaction.event_type] += 1
                if interaction.session_id:
                    user_sessions[interaction.user_id].add(interaction.session_id)
            
            # Calculate metrics
            unique_users = len(set(interaction.user_id for interaction in recent_interactions))
            avg_session_length = sum(len(sessions) for sessions in user_sessions.values()) / len(user_sessions) if user_sessions else 0
            
            return {
                "time_window_seconds": time_window,
                "total_interactions": len(recent_interactions),
                "unique_users": unique_users,
                "event_type_distribution": dict(event_counts),
                "average_session_length": avg_session_length,
                "most_active_users": await self._get_most_active_users(recent_interactions)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user behavior analytics: {str(e)}")
            return {}
    
    async def get_recommendation_analytics(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get recommendation performance analytics."""
        try:
            current_time = time.time()
            recent_events = [
                event for event in self.recommendation_events
                if current_time - event.timestamp < time_window
            ]
            
            if not recent_events:
                return {"message": "No recent recommendation events"}
            
            # Analyze recommendation types
            type_counts = defaultdict(int)
            type_response_times = defaultdict(list)
            
            for event in recent_events:
                type_counts[event.recommendation_type] += 1
                type_response_times[event.recommendation_type].append(event.response_time_ms)
            
            # Calculate performance metrics
            analytics = {
                "time_window_seconds": time_window,
                "total_recommendations": len(recent_events),
                "recommendation_types": dict(type_counts),
                "performance_by_type": {}
            }
            
            for rec_type, times in type_response_times.items():
                analytics["performance_by_type"][rec_type] = {
                    "count": len(times),
                    "avg_response_time": sum(times) / len(times),
                    "min_response_time": min(times),
                    "max_response_time": max(times)
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get recommendation analytics: {str(e)}")
            return {}
    
    # Private methods
    
    async def _metrics_collector(self):
        """Background task to collect and store metrics."""
        while self._running:
            try:
                metrics = await self.get_real_time_metrics()
                self.performance_metrics.append(metrics)
                
                # Store in Redis for dashboard
                await self.redis.setex(
                    "real_time_metrics",
                    300,  # 5 minutes TTL
                    metrics.json()
                )
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Metrics collector error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _cache_hit_rate_monitor(self):
        """Monitor cache hit rates."""
        while self._running:
            try:
                # This would integrate with your actual cache implementation
                # For now, we'll use a placeholder
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Cache monitor error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _user_activity_tracker(self):
        """Track user activity patterns."""
        while self._running:
            try:
                # Clean up old active users (older than 5 minutes)
                current_time = time.time()
                active_threshold = current_time - 300
                
                # This is simplified - in practice you'd check Redis for recent activity
                self.active_users = {
                    user for user in self.active_users
                    # Add logic to check if user was active recently
                }
                
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"User activity tracker error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _performance_aggregator(self):
        """Aggregate performance metrics."""
        while self._running:
            try:
                # Aggregate and store hourly metrics
                if len(self.performance_metrics) > 120:  # 1 hour of 30-second intervals
                    await self._store_hourly_aggregates()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Performance aggregator error: {str(e)}")
                await asyncio.sleep(300)
    
    async def _count_active_users(self, since_timestamp: float) -> int:
        """Count active users since specified timestamp."""
        try:
            # Query Redis for active users
            pattern = f"interaction:*"
            keys = await self.redis.keys(pattern)
            
            active_users = set()
            for key in keys:
                try:
                    data = await self.redis.get(key)
                    if data:
                        interaction = json.loads(data)
                        if interaction.get("timestamp", 0) >= since_timestamp:
                            active_users.add(interaction.get("user_id"))
                except Exception:
                    continue
            
            return len(active_users)
            
        except Exception as e:
            logger.error(f"Failed to count active users: {str(e)}")
            return 0
    
    async def _calculate_click_through_rate(self) -> float:
        """Calculate click-through rate for recommendations."""
        try:
            # This would analyze recommendation events vs click interactions
            # Simplified implementation
            recent_recommendations = len([
                event for event in self.recommendation_events
                if time.time() - event.timestamp < 3600
            ])
            
            recent_clicks = len([
                interaction for interaction in self.user_interactions
                if (interaction.event_type == "click" and 
                    time.time() - interaction.timestamp < 3600)
            ])
            
            return recent_clicks / recent_recommendations if recent_recommendations > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate CTR: {str(e)}")
            return 0.0
    
    async def _get_cache_hit_rate(self) -> float:
        """Get current cache hit rate."""
        try:
            # This would integrate with your Redis monitoring
            # For now, return a placeholder
            return 0.85
            
        except Exception as e:
            logger.error(f"Failed to get cache hit rate: {str(e)}")
            return 0.0
    
    async def _get_most_active_users(self, interactions: List[UserInteraction]) -> List[Dict[str, Any]]:
        """Get most active users from interaction list."""
        user_activity = defaultdict(int)
        
        for interaction in interactions:
            user_activity[interaction.user_id] += 1
        
        # Sort by activity count and return top 10
        sorted_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [
            {"user_id": user_id, "interaction_count": count}
            for user_id, count in sorted_users
        ]
    
    async def _store_hourly_aggregates(self):
        """Store hourly metric aggregates."""
        try:
            # Calculate hourly aggregates from recent metrics
            if not self.performance_metrics:
                return
            
            # Take metrics from last hour
            hour_metrics = list(self.performance_metrics)[-120:]  # Last 120 measurements (1 hour)
            
            aggregates = {
                "timestamp": datetime.utcnow().isoformat(),
                "avg_active_users": sum(m.active_users_1min for m in hour_metrics) / len(hour_metrics),
                "avg_requests_per_second": sum(m.requests_per_second for m in hour_metrics) / len(hour_metrics),
                "avg_response_time": sum(m.avg_response_time for m in hour_metrics) / len(hour_metrics),
                "max_error_rate": max(m.error_rate for m in hour_metrics),
                "avg_cache_hit_rate": sum(m.cache_hit_rate for m in hour_metrics) / len(hour_metrics)
            }
            
            # Store in Redis with longer TTL
            await self.redis.setex(
                f"hourly_metrics:{int(time.time() // 3600)}",
                86400,  # 24 hours TTL
                json.dumps(aggregates)
            )
            
            logger.info("Stored hourly metric aggregates")
            
        except Exception as e:
            logger.error(f"Failed to store hourly aggregates: {str(e)}")

    async def cleanup(self):
        """Cleanup analytics resources and connections."""
        try:
            # Stop background tasks
            if hasattr(self, '_background_tasks'):
                for task in self._background_tasks:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
            
            # Close Redis connection
            if self.redis:
                await self.redis.close()
            
            logger.info("Analytics cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during analytics cleanup: {str(e)}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            if hasattr(self, 'redis') and self.redis:
                # Try to close synchronously if possible
                if hasattr(self.redis, 'close'):
                    try:
                        self.redis.close()
                    except Exception:
                        pass
        except Exception:
            pass

"""
Performance Tracker - Real-time Newsletter Performance Analytics
Tracks engagement, conversion rates, and user behavior patterns.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.core.monitoring import MetricsCollector


class EngagementEvent(Enum):
    """Types of engagement events"""
    EMAIL_OPENED = "email_opened"
    LINK_CLICKED = "link_clicked"
    CONTENT_SHARED = "content_shared"
    UNSUBSCRIBED = "unsubscribed"
    RESUBSCRIBED = "resubscribed"
    FORWARDED = "forwarded"
    REPLIED = "replied"
    BOOKMARKED = "bookmarked"
    RATING_GIVEN = "rating_given"
    POLL_ANSWERED = "poll_answered"
    QUIZ_COMPLETED = "quiz_completed"
    CONTENT_GENERATED = "content_generated"


class MetricType(Enum):
    """Types of performance metrics"""
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    CONVERSION_RATE = "conversion_rate"
    BOUNCE_RATE = "bounce_rate"
    ENGAGEMENT_SCORE = "engagement_score"
    VIRALITY_COEFFICIENT = "virality_coefficient"
    RETENTION_RATE = "retention_rate"
    CHURN_RATE = "churn_rate"
    SATISFACTION_SCORE = "satisfaction_score"
    TIME_TO_ENGAGE = "time_to_engage"


@dataclass
class EngagementData:
    """Individual engagement event data"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    campaign_id: str = ""
    event_type: EngagementEvent = EngagementEvent.EMAIL_OPENED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    device_info: Dict[str, str] = field(default_factory=dict)
    location_info: Dict[str, str] = field(default_factory=dict)
    session_id: str = ""
    content_id: str = ""
    value: float = 0.0  # For conversions, time spent, etc.


@dataclass
class CampaignMetrics:
    """Campaign performance metrics"""
    campaign_id: str = ""
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    unique_opens: int = 0
    total_clicks: int = 0
    unique_clicks: int = 0
    total_conversions: int = 0
    total_unsubscribes: int = 0
    total_bounces: int = 0
    total_forwards: int = 0
    total_replies: int = 0
    
    # Calculated metrics
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0
    conversion_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    bounce_rate: float = 0.0
    engagement_score: float = 0.0
    virality_coefficient: float = 0.0
    
    # Time-based metrics
    average_time_to_open: float = 0.0
    average_time_to_click: float = 0.0
    peak_engagement_time: Optional[datetime] = None
    
    # Segmentation metrics
    segment_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    device_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    location_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserEngagementProfile:
    """Individual user engagement profile"""
    user_id: str = ""
    total_emails_received: int = 0
    total_emails_opened: int = 0
    total_links_clicked: int = 0
    total_conversions: int = 0
    engagement_score: float = 0.0
    frequency_preference: str = "weekly"  # daily, weekly, monthly
    best_send_time: Optional[datetime] = None
    preferred_content_types: List[str] = field(default_factory=list)
    device_preferences: List[str] = field(default_factory=list)
    churn_risk_score: float = 0.0
    lifetime_value: float = 0.0
    last_engagement_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class PerformanceTracker:
    """Real-time performance tracking and analytics engine"""
    
    def __init__(self, cache_manager: AsyncCacheManager, metrics_collector: MetricsCollector):
        self.cache = cache_manager
        self.metrics_collector = metrics_collector
        self.logger = StructuredLogger(__name__)
        
        # In-memory event storage for real-time processing
        self.event_queue: List[EngagementData] = []
        self.campaign_metrics: Dict[str, CampaignMetrics] = {}
        self.user_profiles: Dict[str, UserEngagementProfile] = {}
        
        # Real-time aggregates
        self.hourly_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.daily_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Performance thresholds for alerts
        self.alert_thresholds = {
            "low_open_rate": 0.15,
            "high_unsubscribe_rate": 0.05,
            "high_bounce_rate": 0.10,
            "low_engagement_score": 0.3
        }
        
        # Background processing task
        self.processing_active = False
    
    async def track_event(self, event: EngagementData) -> None:
        """Track a single engagement event"""
        try:
            # Add to event queue for real-time processing
            self.event_queue.append(event)
            
            # Update real-time metrics
            await self._update_real_time_metrics(event)
            
            # Update campaign metrics
            await self._update_campaign_metrics(event)
            
            # Update user profile
            await self._update_user_profile(event)
            
            # Cache event data
            cache_key = f"engagement_event:{event.event_id}"
            await self.cache.set(cache_key, event.__dict__, ttl=86400 * 7)  # 1 week
            
            # Send to metrics collector
            self.metrics_collector.increment_counter(
                f"newsletter_event_{event.event_type.value}",
                {"campaign_id": event.campaign_id, "user_id": event.user_id}
            )
            
            self.logger.info(
                "Engagement event tracked",
                event_id=event.event_id,
                event_type=event.event_type.value,
                campaign_id=event.campaign_id,
                user_id=event.user_id
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to track engagement event",
                event_id=event.event_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _update_real_time_metrics(self, event: EngagementData) -> None:
        """Update real-time metrics aggregates"""
        try:
            # Hourly stats
            hour_key = event.timestamp.strftime("%Y-%m-%d-%H")
            if hour_key not in self.hourly_stats:
                self.hourly_stats[hour_key] = {
                    "events": defaultdict(int),
                    "campaigns": set(),
                    "users": set(),
                    "devices": defaultdict(int),
                    "locations": defaultdict(int)
                }
            
            stats = self.hourly_stats[hour_key]
            stats["events"][event.event_type.value] += 1
            stats["campaigns"].add(event.campaign_id)
            stats["users"].add(event.user_id)
            
            if event.device_info.get("type"):
                stats["devices"][event.device_info["type"]] += 1
            if event.location_info.get("country"):
                stats["locations"][event.location_info["country"]] += 1
            
            # Daily stats
            day_key = event.timestamp.strftime("%Y-%m-%d")
            if day_key not in self.daily_stats:
                self.daily_stats[day_key] = {
                    "events": defaultdict(int),
                    "campaigns": set(),
                    "users": set(),
                    "devices": defaultdict(int),
                    "locations": defaultdict(int)
                }
            
            daily = self.daily_stats[day_key]
            daily["events"][event.event_type.value] += 1
            daily["campaigns"].add(event.campaign_id)
            daily["users"].add(event.user_id)
            
            if event.device_info.get("type"):
                daily["devices"][event.device_info["type"]] += 1
            if event.location_info.get("country"):
                daily["locations"][event.location_info["country"]] += 1
            
        except Exception as e:
            self.logger.error("Failed to update real-time metrics", error=str(e))
    
    async def _update_campaign_metrics(self, event: EngagementData) -> None:
        """Update campaign-specific metrics"""
        try:
            campaign_id = event.campaign_id
            if campaign_id not in self.campaign_metrics:
                self.campaign_metrics[campaign_id] = CampaignMetrics(campaign_id=campaign_id)
            
            metrics = self.campaign_metrics[campaign_id]
            
            # Update counts based on event type
            if event.event_type == EngagementEvent.EMAIL_OPENED:
                metrics.total_opened += 1
            elif event.event_type == EngagementEvent.LINK_CLICKED:
                metrics.total_clicks += 1
            elif event.event_type == EngagementEvent.UNSUBSCRIBED:
                metrics.total_unsubscribes += 1
            elif event.event_type == EngagementEvent.FORWARDED:
                metrics.total_forwards += 1
            elif event.event_type == EngagementEvent.REPLIED:
                metrics.total_replies += 1
            
            # Update segmentation metrics
            if event.metadata.get("segment"):
                segment = event.metadata["segment"]
                if segment not in metrics.segment_performance:
                    metrics.segment_performance[segment] = defaultdict(float)
                metrics.segment_performance[segment][event.event_type.value] += 1
            
            # Update device metrics
            if event.device_info.get("type"):
                device = event.device_info["type"]
                if device not in metrics.device_performance:
                    metrics.device_performance[device] = defaultdict(float)
                metrics.device_performance[device][event.event_type.value] += 1
            
            # Update location metrics
            if event.location_info.get("country"):
                location = event.location_info["country"]
                if location not in metrics.location_performance:
                    metrics.location_performance[location] = defaultdict(float)
                metrics.location_performance[location][event.event_type.value] += 1
            
            metrics.updated_at = datetime.utcnow()
            
            # Cache updated metrics
            cache_key = f"campaign_metrics:{campaign_id}"
            await self.cache.set(cache_key, metrics.__dict__, ttl=3600)
            
        except Exception as e:
            self.logger.error(
                "Failed to update campaign metrics",
                campaign_id=campaign_id,
                error=str(e)
            )
    
    async def _update_user_profile(self, event: EngagementData) -> None:
        """Update user engagement profile"""
        try:
            user_id = event.user_id
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = UserEngagementProfile(user_id=user_id)
            
            profile = self.user_profiles[user_id]
            
            # Update counts based on event type
            if event.event_type == EngagementEvent.EMAIL_OPENED:
                profile.total_emails_opened += 1
            elif event.event_type == EngagementEvent.LINK_CLICKED:
                profile.total_links_clicked += 1
            
            # Update engagement patterns
            profile.last_engagement_date = event.timestamp
            
            # Update device preferences
            if event.device_info.get("type"):
                device = event.device_info["type"]
                if device not in profile.device_preferences:
                    profile.device_preferences.append(device)
            
            # Update content preferences
            if event.metadata.get("content_type"):
                content_type = event.metadata["content_type"]
                if content_type not in profile.preferred_content_types:
                    profile.preferred_content_types.append(content_type)
            
            profile.updated_at = datetime.utcnow()
            
            # Cache updated profile
            cache_key = f"user_profile:{user_id}"
            await self.cache.set(cache_key, profile.__dict__, ttl=3600)
            
        except Exception as e:
            self.logger.error(
                "Failed to update user profile",
                user_id=user_id,
                error=str(e)
            )
    
    async def calculate_campaign_metrics(self, campaign_id: str) -> CampaignMetrics:
        """Calculate comprehensive campaign metrics"""
        try:
            if campaign_id not in self.campaign_metrics:
                return CampaignMetrics(campaign_id=campaign_id)
            
            metrics = self.campaign_metrics[campaign_id]
            
            # Calculate rates
            if metrics.total_sent > 0:
                metrics.delivery_rate = metrics.total_delivered / metrics.total_sent
                metrics.bounce_rate = metrics.total_bounces / metrics.total_sent
                metrics.unsubscribe_rate = metrics.total_unsubscribes / metrics.total_sent
            
            if metrics.total_delivered > 0:
                metrics.open_rate = metrics.unique_opens / metrics.total_delivered
                metrics.conversion_rate = metrics.total_conversions / metrics.total_delivered
            
            if metrics.unique_opens > 0:
                metrics.click_to_open_rate = metrics.unique_clicks / metrics.unique_opens
            
            if metrics.total_delivered > 0:
                metrics.click_rate = metrics.unique_clicks / metrics.total_delivered
            
            # Calculate engagement score (weighted combination of metrics)
            engagement_weights = {
                "open_rate": 0.3,
                "click_rate": 0.4,
                "conversion_rate": 0.2,
                "virality": 0.1
            }
            
            metrics.engagement_score = (
                metrics.open_rate * engagement_weights["open_rate"] +
                metrics.click_rate * engagement_weights["click_rate"] +
                metrics.conversion_rate * engagement_weights["conversion_rate"] +
                (metrics.total_forwards / max(metrics.total_delivered, 1)) * engagement_weights["virality"]
            )
            
            # Calculate virality coefficient
            if metrics.total_delivered > 0:
                metrics.virality_coefficient = metrics.total_forwards / metrics.total_delivered
            
            return metrics
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate campaign metrics",
                campaign_id=campaign_id,
                error=str(e)
            )
            return CampaignMetrics(campaign_id=campaign_id)
    
    async def calculate_user_engagement_score(self, user_id: str) -> float:
        """Calculate user engagement score"""
        try:
            if user_id not in self.user_profiles:
                return 0.0
            
            profile = self.user_profiles[user_id]
            
            # Base engagement rate
            if profile.total_emails_received == 0:
                return 0.0
            
            open_rate = profile.total_emails_opened / profile.total_emails_received
            click_rate = profile.total_links_clicked / max(profile.total_emails_opened, 1)
            
            # Recency boost
            recency_boost = 1.0
            if profile.last_engagement_date:
                days_since_last = (datetime.utcnow() - profile.last_engagement_date).days
                recency_boost = max(0.1, 1.0 - (days_since_last / 30))  # Decay over 30 days
            
            # Calculate weighted score
            engagement_score = (
                open_rate * 0.4 +
                click_rate * 0.6
            ) * recency_boost
            
            profile.engagement_score = engagement_score
            return engagement_score
            
        except Exception as e:
            self.logger.error(
                "Failed to calculate user engagement score",
                user_id=user_id,
                error=str(e)
            )
            return 0.0
    
    async def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        try:
            current_hour = datetime.utcnow().strftime("%Y-%m-%d-%H")
            current_day = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Get current hour stats
            hour_stats = self.hourly_stats.get(current_hour, {})
            day_stats = self.daily_stats.get(current_day, {})
            
            # Calculate real-time metrics
            total_events_today = sum(day_stats.get("events", {}).values())
            active_campaigns = len(day_stats.get("campaigns", set()))
            active_users = len(day_stats.get("users", set()))
            
            # Top performing campaigns
            campaign_scores = []
            for campaign_id, metrics in self.campaign_metrics.items():
                if metrics.updated_at.date() == datetime.utcnow().date():
                    campaign_scores.append({
                        "campaign_id": campaign_id,
                        "engagement_score": metrics.engagement_score,
                        "open_rate": metrics.open_rate,
                        "click_rate": metrics.click_rate
                    })
            
            campaign_scores.sort(key=lambda x: x["engagement_score"], reverse=True)
            
            return {
                "current_hour_stats": hour_stats,
                "today_stats": day_stats,
                "totals": {
                    "events_today": total_events_today,
                    "active_campaigns": active_campaigns,
                    "active_users": active_users
                },
                "top_campaigns": campaign_scores[:5],
                "alerts": await self._check_alerts(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Failed to get dashboard data", error=str(e))
            return {"error": "Failed to retrieve dashboard data"}
    
    async def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance alerts"""
        alerts = []
        
        try:
            for campaign_id, metrics in self.campaign_metrics.items():
                # Check if metrics were updated recently (within last hour)
                if (datetime.utcnow() - metrics.updated_at).seconds > 3600:
                    continue
                
                # Low open rate alert
                if metrics.open_rate < self.alert_thresholds["low_open_rate"]:
                    alerts.append({
                        "type": "low_open_rate",
                        "campaign_id": campaign_id,
                        "value": metrics.open_rate,
                        "threshold": self.alert_thresholds["low_open_rate"],
                        "severity": "warning"
                    })
                
                # High unsubscribe rate alert
                if metrics.unsubscribe_rate > self.alert_thresholds["high_unsubscribe_rate"]:
                    alerts.append({
                        "type": "high_unsubscribe_rate",
                        "campaign_id": campaign_id,
                        "value": metrics.unsubscribe_rate,
                        "threshold": self.alert_thresholds["high_unsubscribe_rate"],
                        "severity": "critical"
                    })
                
                # High bounce rate alert
                if metrics.bounce_rate > self.alert_thresholds["high_bounce_rate"]:
                    alerts.append({
                        "type": "high_bounce_rate",
                        "campaign_id": campaign_id,
                        "value": metrics.bounce_rate,
                        "threshold": self.alert_thresholds["high_bounce_rate"],
                        "severity": "critical"
                    })
                
                # Low engagement score alert
                if metrics.engagement_score < self.alert_thresholds["low_engagement_score"]:
                    alerts.append({
                        "type": "low_engagement_score",
                        "campaign_id": campaign_id,
                        "value": metrics.engagement_score,
                        "threshold": self.alert_thresholds["low_engagement_score"],
                        "severity": "warning"
                    })
            
        except Exception as e:
            self.logger.error("Failed to check alerts", error=str(e))
        
        return alerts
    
    async def start_background_processing(self) -> None:
        """Start background processing of events"""
        if self.processing_active:
            return
        
        self.processing_active = True
        self.logger.info("Starting background event processing")
        
        # Start processing loop
        asyncio.create_task(self._process_events_loop())
    
    async def stop_background_processing(self) -> None:
        """Stop background processing"""
        self.processing_active = False
        self.logger.info("Stopping background event processing")
    
    async def _process_events_loop(self) -> None:
        """Background event processing loop"""
        while self.processing_active:
            try:
                if self.event_queue:
                    # Process events in batches
                    batch_size = min(100, len(self.event_queue))
                    events_to_process = self.event_queue[:batch_size]
                    self.event_queue = self.event_queue[batch_size:]
                    
                    # Persist events to database/storage
                    await self._persist_events(events_to_process)
                    
                    # Clean up old data
                    await self._cleanup_old_data()
                
                # Sleep before next iteration
                await asyncio.sleep(10)  # Process every 10 seconds
                
            except Exception as e:
                self.logger.error("Error in event processing loop", error=str(e))
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _persist_events(self, events: List[EngagementData]) -> None:
        """Persist events to long-term storage"""
        try:
            # In a real implementation, this would save to a database
            # For now, we'll just cache them with longer TTL
            for event in events:
                cache_key = f"persisted_event:{event.event_id}"
                await self.cache.set(cache_key, event.__dict__, ttl=86400 * 30)  # 30 days
            
            self.logger.info(f"Persisted {len(events)} events to storage")
            
        except Exception as e:
            self.logger.error("Failed to persist events", error=str(e))
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old in-memory data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Clean up hourly stats older than 24 hours
            old_hours = [
                hour for hour in self.hourly_stats.keys()
                if datetime.strptime(hour, "%Y-%m-%d-%H") < cutoff_time
            ]
            
            for hour in old_hours:
                del self.hourly_stats[hour]
            
            if old_hours:
                self.logger.info(f"Cleaned up {len(old_hours)} old hourly stats")
            
        except Exception as e:
            self.logger.error("Failed to cleanup old data", error=str(e))

"""
Campaign Manager - Orchestrates Newsletter Campaign Lifecycle
Manages campaigns, scheduling, segmentation, and performance tracking.
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

from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.newsletter.core.personalization_engine import UserPersona, PersonalizationEngine
from src.newsletter.core.content_curator import AIContentCurator, ContentItem
from src.newsletter.core.send_time_optimizer import SendTimeOptimizer, SendTimeStrategy
from src.newsletter.templates.adaptive_templates import AdaptiveTemplateEngine, TemplateData


class CampaignType(Enum):
    """Types of newsletter campaigns"""
    REGULAR = "regular"
    WELCOME_SERIES = "welcome_series"
    ONBOARDING = "onboarding"
    RE_ENGAGEMENT = "re_engagement"
    PROMOTIONAL = "promotional"
    MILESTONE = "milestone"
    SEASONAL = "seasonal"
    PERSONALIZED = "personalized"


class CampaignStatus(Enum):
    """Campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class SegmentationType(Enum):
    """User segmentation types"""
    ALL_USERS = "all_users"
    NEW_USERS = "new_users"
    ACTIVE_USERS = "active_users"
    INACTIVE_USERS = "inactive_users"
    HIGH_ENGAGEMENT = "high_engagement"
    LOW_ENGAGEMENT = "low_engagement"
    BY_GENRE = "by_genre"
    BY_READING_VELOCITY = "by_reading_velocity"
    CUSTOM = "custom"


@dataclass
class CampaignSegment:
    """User segment definition"""
    id: str
    name: str
    type: SegmentationType
    criteria: Dict[str, Any]
    user_count: int
    description: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CampaignConfig:
    """Campaign configuration"""
    type: CampaignType
    segments: List[CampaignSegment]
    send_strategy: SendTimeStrategy
    template_style: str
    content_types: List[str]
    personalization_level: str
    a_b_testing: bool = False
    frequency_cap: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Campaign:
    """Newsletter campaign"""
    id: str
    name: str
    description: str
    type: CampaignType
    status: CampaignStatus
    config: CampaignConfig
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


@dataclass
class CampaignAnalytics:
    """Campaign performance analytics"""
    campaign_id: str
    total_sent: int
    total_delivered: int
    total_opens: int
    total_clicks: int
    total_unsubscribes: int
    open_rate: float
    click_rate: float
    unsubscribe_rate: float
    engagement_rate: float
    revenue_attributed: float = 0.0
    cost_per_engagement: float = 0.0
    segment_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    time_series_data: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


class CampaignManager:
    """
    Campaign Manager
    
    Features:
    - Campaign lifecycle management
    - User segmentation and targeting
    - Automated scheduling and sending
    - Real-time performance tracking
    - A/B testing coordination
    - Frequency capping and suppression
    """
    
    def __init__(
        self,
        cache_manager: AsyncCacheManager,
        personalization_engine: PersonalizationEngine,
        content_curator: AIContentCurator,
        send_time_optimizer: SendTimeOptimizer,
        template_engine: AdaptiveTemplateEngine
    ):
        self.cache = cache_manager
        self.personalization_engine = personalization_engine
        self.content_curator = content_curator
        self.send_time_optimizer = send_time_optimizer
        self.template_engine = template_engine
        self.logger = StructuredLogger(__name__)
        
        # Campaign storage
        self.campaigns: Dict[str, Campaign] = {}
        self.segments: Dict[str, CampaignSegment] = {}
        
        # Sending queue
        self.send_queue: List[Dict[str, Any]] = []
        self.sending_active = False
        
        # Performance tracking
        self.campaign_analytics: Dict[str, CampaignAnalytics] = {}
        
        # Frequency caps
        self.user_send_history: Dict[str, List[datetime]] = {}
    
    async def create_campaign(
        self,
        name: str,
        description: str,
        campaign_type: CampaignType,
        config: CampaignConfig,
        scheduled_at: Optional[datetime] = None
    ) -> Campaign:
        """Create a new campaign"""
        try:
            campaign_id = str(uuid.uuid4())
            
            # Calculate total recipients
            total_recipients = sum(segment.user_count for segment in config.segments)
            
            campaign = Campaign(
                id=campaign_id,
                name=name,
                description=description,
                type=campaign_type,
                status=CampaignStatus.DRAFT,
                config=config,
                scheduled_at=scheduled_at,
                total_recipients=total_recipients
            )
            
            # Store campaign
            self.campaigns[campaign_id] = campaign
            
            # Cache campaign
            await self._cache_campaign(campaign)
            
            self.logger.info(
                "Campaign created",
                campaign_id=campaign_id,
                name=name,
                type=campaign_type.value,
                total_recipients=total_recipients
            )
            
            return campaign
            
        except Exception as e:
            self.logger.error(
                "Campaign creation failed",
                name=name,
                error=str(e)
            )
            raise
    
    async def schedule_campaign(
        self,
        campaign_id: str,
        scheduled_at: datetime
    ) -> bool:
        """Schedule a campaign for sending"""
        try:
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
                raise ValueError(f"Campaign {campaign_id} cannot be scheduled (status: {campaign.status})")
            
            # Validate scheduled time
            if scheduled_at <= datetime.utcnow():
                raise ValueError("Scheduled time must be in the future")
            
            # Update campaign
            campaign.scheduled_at = scheduled_at
            campaign.status = CampaignStatus.SCHEDULED
            
            # Update cache
            await self._cache_campaign(campaign)
            
            self.logger.info(
                "Campaign scheduled",
                campaign_id=campaign_id,
                scheduled_at=scheduled_at.isoformat()
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Campaign scheduling failed",
                campaign_id=campaign_id,
                error=str(e)
            )
            return False
    
    async def send_campaign_immediately(
        self,
        campaign_id: str
    ) -> bool:
        """Send campaign immediately"""
        try:
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
                raise ValueError(f"Campaign {campaign_id} cannot be sent (status: {campaign.status})")
            
            # Start sending process
            campaign.status = CampaignStatus.SENDING
            campaign.started_at = datetime.utcnow()
            
            # Add to send queue
            await self._queue_campaign_sends(campaign)
            
            # Start sending process if not already active
            if not self.sending_active:
                asyncio.create_task(self._process_send_queue())
            
            await self._cache_campaign(campaign)
            
            self.logger.info(
                "Campaign sending started",
                campaign_id=campaign_id,
                total_recipients=campaign.total_recipients
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Campaign sending failed",
                campaign_id=campaign_id,
                error=str(e)
            )
            return False
    
    async def create_user_segment(
        self,
        name: str,
        segment_type: SegmentationType,
        criteria: Dict[str, Any],
        description: str = ""
    ) -> CampaignSegment:
        """Create a user segment"""
        try:
            segment_id = str(uuid.uuid4())
            
            # Calculate user count
            user_count = await self._calculate_segment_size(segment_type, criteria)
            
            segment = CampaignSegment(
                id=segment_id,
                name=name,
                type=segment_type,
                criteria=criteria,
                user_count=user_count,
                description=description
            )
            
            # Store segment
            self.segments[segment_id] = segment
            
            # Cache segment
            cache_key = f"campaign_segment:{segment_id}"
            await self.cache.set(
                cache_key,
                json.dumps(segment.__dict__, default=str),
                ttl=86400  # 24 hours
            )
            
            self.logger.info(
                "User segment created",
                segment_id=segment_id,
                name=name,
                type=segment_type.value,
                user_count=user_count
            )
            
            return segment
            
        except Exception as e:
            self.logger.error(
                "Segment creation failed",
                name=name,
                error=str(e)
            )
            raise
    
    async def analyze_campaign_performance(
        self,
        campaign_id: str
    ) -> CampaignAnalytics:
        """Analyze campaign performance"""
        try:
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            # Get performance data
            performance_data = await self._get_campaign_performance_data(campaign_id)
            
            # Calculate metrics
            analytics = await self._calculate_campaign_metrics(campaign, performance_data)
            
            # Store analytics
            self.campaign_analytics[campaign_id] = analytics
            
            # Cache analytics
            cache_key = f"campaign_analytics:{campaign_id}"
            await self.cache.set(
                cache_key,
                json.dumps(analytics.__dict__, default=str),
                ttl=3600  # 1 hour
            )
            
            self.logger.info(
                "Campaign analytics generated",
                campaign_id=campaign_id,
                open_rate=analytics.open_rate,
                click_rate=analytics.click_rate,
                engagement_rate=analytics.engagement_rate
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(
                "Campaign analysis failed",
                campaign_id=campaign_id,
                error=str(e)
            )
            raise
    
    async def pause_campaign(self, campaign_id: str) -> bool:
        """Pause an active campaign"""
        try:
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                return False
            
            if campaign.status == CampaignStatus.SENDING:
                campaign.status = CampaignStatus.PAUSED
                await self._cache_campaign(campaign)
                
                self.logger.info(
                    "Campaign paused",
                    campaign_id=campaign_id
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(
                "Campaign pause failed",
                campaign_id=campaign_id,
                error=str(e)
            )
            return False
    
    async def resume_campaign(self, campaign_id: str) -> bool:
        """Resume a paused campaign"""
        try:
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                return False
            
            if campaign.status == CampaignStatus.PAUSED:
                campaign.status = CampaignStatus.SENDING
                await self._cache_campaign(campaign)
                
                # Resume sending if not active
                if not self.sending_active:
                    asyncio.create_task(self._process_send_queue())
                
                self.logger.info(
                    "Campaign resumed",
                    campaign_id=campaign_id
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(
                "Campaign resume failed",
                campaign_id=campaign_id,
                error=str(e)
            )
            return False
    
    async def get_campaigns(
        self,
        status: Optional[CampaignStatus] = None,
        campaign_type: Optional[CampaignType] = None
    ) -> List[Campaign]:
        """Get campaigns with optional filters"""
        try:
            campaigns = list(self.campaigns.values())
            
            if status:
                campaigns = [c for c in campaigns if c.status == status]
            
            if campaign_type:
                campaigns = [c for c in campaigns if c.type == campaign_type]
            
            # Sort by creation time (newest first)
            campaigns.sort(key=lambda x: x.created_at, reverse=True)
            
            return campaigns
            
        except Exception as e:
            self.logger.error(
                "Get campaigns failed",
                error=str(e)
            )
            return []
    
    async def check_frequency_cap(
        self,
        user_id: str,
        max_sends_per_day: int = 2
    ) -> bool:
        """Check if user has reached frequency cap"""
        try:
            send_history = self.user_send_history.get(user_id, [])
            
            # Count sends in last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(days=1)
            recent_sends = [send_time for send_time in send_history if send_time > cutoff_time]
            
            return len(recent_sends) < max_sends_per_day
            
        except Exception as e:
            self.logger.error(
                "Frequency cap check failed",
                user_id=user_id,
                error=str(e)
            )
            return True  # Allow send if check fails
    
    # Private helper methods
    
    async def _get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID"""
        if campaign_id in self.campaigns:
            return self.campaigns[campaign_id]
        
        # Try to load from cache
        cache_key = f"campaign:{campaign_id}"
        cached_campaign = await self.cache.get(cache_key)
        if cached_campaign:
            campaign_data = json.loads(cached_campaign)
            # Reconstruct campaign object (simplified)
            return Campaign(**campaign_data)
        
        return None
    
    async def _cache_campaign(self, campaign: Campaign) -> None:
        """Cache campaign data"""
        cache_key = f"campaign:{campaign.id}"
        await self.cache.set(
            cache_key,
            json.dumps(campaign.__dict__, default=str),
            ttl=86400  # 24 hours
        )
    
    async def _calculate_segment_size(
        self,
        segment_type: SegmentationType,
        criteria: Dict[str, Any]
    ) -> int:
        """Calculate segment size based on criteria"""
        # This would query the actual user database
        # For demo, return estimated sizes
        
        segment_sizes = {
            SegmentationType.ALL_USERS: 10000,
            SegmentationType.NEW_USERS: 500,
            SegmentationType.ACTIVE_USERS: 7000,
            SegmentationType.INACTIVE_USERS: 3000,
            SegmentationType.HIGH_ENGAGEMENT: 2000,
            SegmentationType.LOW_ENGAGEMENT: 3000,
            SegmentationType.BY_GENRE: 1500,
            SegmentationType.BY_READING_VELOCITY: 1200,
            SegmentationType.CUSTOM: 800
        }
        
        return segment_sizes.get(segment_type, 1000)
    
    async def _queue_campaign_sends(self, campaign: Campaign) -> None:
        """Queue individual sends for campaign"""
        try:
            # Get users for each segment
            for segment in campaign.config.segments:
                users = await self._get_segment_users(segment)
                
                for user_persona in users:
                    # Check frequency cap
                    if not await self.check_frequency_cap(user_persona.user_id):
                        continue
                    
                    # Optimize send time
                    optimal_send_time = await self.send_time_optimizer.find_optimal_send_time(
                        user_persona, campaign.config.send_strategy
                    )
                    
                    # Add to queue
                    send_item = {
                        "campaign_id": campaign.id,
                        "user_persona": user_persona,
                        "segment_id": segment.id,
                        "send_time": optimal_send_time.send_time,
                        "template_config": None  # Will be determined later
                    }
                    
                    self.send_queue.append(send_item)
            
            self.logger.info(
                "Campaign queued for sending",
                campaign_id=campaign.id,
                queue_size=len(self.send_queue)
            )
            
        except Exception as e:
            self.logger.error(
                "Campaign queueing failed",
                campaign_id=campaign.id,
                error=str(e)
            )
    
    async def _process_send_queue(self) -> None:
        """Process the send queue"""
        self.sending_active = True
        
        try:
            while self.send_queue:
                # Get next item
                send_item = self.send_queue.pop(0)
                
                # Check if it's time to send
                if send_item["send_time"] > datetime.utcnow():
                    # Put back in queue and wait
                    self.send_queue.insert(0, send_item)
                    await asyncio.sleep(60)  # Check again in 1 minute
                    continue
                
                # Send the email
                success = await self._send_individual_email(send_item)
                
                if success:
                    # Update campaign metrics
                    campaign = await self._get_campaign(send_item["campaign_id"])
                    if campaign:
                        campaign.sent_count += 1
                        await self._cache_campaign(campaign)
                    
                    # Update user send history
                    user_id = send_item["user_persona"].user_id
                    if user_id not in self.user_send_history:
                        self.user_send_history[user_id] = []
                    self.user_send_history[user_id].append(datetime.utcnow())
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
            
        except Exception as e:
            self.logger.error(
                "Send queue processing failed",
                error=str(e)
            )
        finally:
            self.sending_active = False
    
    async def _send_individual_email(self, send_item: Dict[str, Any]) -> bool:
        """Send individual email"""
        try:
            campaign_id = send_item["campaign_id"]
            user_persona = send_item["user_persona"]
            
            campaign = await self._get_campaign(campaign_id)
            if not campaign:
                return False
            
            # Check if campaign is still active
            if campaign.status != CampaignStatus.SENDING:
                return False
            
            # Curate content for user
            content_items = await self.content_curator.curate_content(
                user_persona,
                [getattr(ContentType, ct) for ct in campaign.config.content_types],
                max_items=5
            )
            
            # Prepare template data
            template_data = TemplateData(
                user_persona=user_persona,
                content_items=content_items,
                subject_line="",  # Will be generated
                preheader_text="",  # Will be generated
                sender_name="BookWorm AI",
                sender_email="hello@bookworm.ai",
                unsubscribe_url=f"https://bookworm.ai/unsubscribe?user={user_persona.user_id}",
                preferences_url=f"https://bookworm.ai/preferences?user={user_persona.user_id}",
                branding={
                    "logo_url": "https://bookworm.ai/logo.png",
                    "brand_color": "#2563eb",
                    "company_name": "BookWorm AI"
                },
                metadata={
                    "campaign_id": campaign_id,
                    "segment_id": send_item["segment_id"]
                }
            )
            
            # Render template
            rendered_template = await self.template_engine.render_personalized_template(
                template_data
            )
            
            # Send email (integrate with email service)
            email_sent = await self._deliver_email(
                user_persona.user_id,
                rendered_template
            )
            
            if email_sent:
                self.logger.debug(
                    "Email sent successfully",
                    campaign_id=campaign_id,
                    user_id=user_persona.user_id
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(
                "Individual email send failed",
                campaign_id=send_item.get("campaign_id"),
                user_id=send_item.get("user_persona", {}).get("user_id"),
                error=str(e)
            )
            return False
    
    async def _deliver_email(
        self,
        user_id: str,
        rendered_template: Any
    ) -> bool:
        """Deliver email via email service"""
        # This would integrate with actual email service (SendGrid, AWS SES, etc.)
        # For demo, just log and return success
        
        self.logger.info(
            "Email delivered",
            user_id=user_id,
            subject=rendered_template.subject_line,
            template_version=rendered_template.template_version
        )
        
        return True
    
    async def _get_segment_users(self, segment: CampaignSegment) -> List[UserPersona]:
        """Get users for a segment"""
        # This would query the actual user database
        # For demo, generate sample personas
        
        sample_personas = []
        for i in range(min(segment.user_count, 10)):  # Limit for demo
            persona = UserPersona(
                user_id=f"user_{segment.id}_{i}",
                reading_velocity=2.0 + (i * 0.5),
                preferred_genres=["Fiction", "Science Fiction"],
                reading_times=["19:00"],
                engagement_pattern="evening",
                content_preferences={},
                attention_span="medium",
                interaction_history=[],
                behavioral_clusters=["avid_reader"],
                sentiment_profile={"positive": 0.7, "neutral": 0.2, "negative": 0.1}
            )
            sample_personas.append(persona)
        
        return sample_personas
    
    async def _get_campaign_performance_data(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get campaign performance data"""
        # This would query actual analytics database
        # For demo, generate sample data
        
        campaign = await self._get_campaign(campaign_id)
        if not campaign:
            return []
        
        sample_data = []
        for i in range(campaign.sent_count):
            sample_data.append({
                "recipient_id": f"user_{i}",
                "sent_at": datetime.utcnow() - timedelta(hours=i),
                "delivered": True,
                "opened": i % 3 == 0,  # 33% open rate
                "clicked": i % 10 == 0,  # 10% click rate
                "unsubscribed": i % 100 == 0,  # 1% unsubscribe rate
                "engagement_score": 0.3 + (i % 7) * 0.1
            })
        
        return sample_data
    
    async def _calculate_campaign_metrics(
        self,
        campaign: Campaign,
        performance_data: List[Dict[str, Any]]
    ) -> CampaignAnalytics:
        """Calculate campaign metrics"""
        if not performance_data:
            return CampaignAnalytics(
                campaign_id=campaign.id,
                total_sent=0,
                total_delivered=0,
                total_opens=0,
                total_clicks=0,
                total_unsubscribes=0,
                open_rate=0.0,
                click_rate=0.0,
                unsubscribe_rate=0.0,
                engagement_rate=0.0
            )
        
        total_sent = len(performance_data)
        total_delivered = sum(1 for d in performance_data if d.get("delivered", False))
        total_opens = sum(1 for d in performance_data if d.get("opened", False))
        total_clicks = sum(1 for d in performance_data if d.get("clicked", False))
        total_unsubscribes = sum(1 for d in performance_data if d.get("unsubscribed", False))
        
        open_rate = total_opens / total_delivered if total_delivered > 0 else 0
        click_rate = total_clicks / total_delivered if total_delivered > 0 else 0
        unsubscribe_rate = total_unsubscribes / total_delivered if total_delivered > 0 else 0
        
        # Calculate engagement rate (opens + clicks) / delivered
        total_engaged = len(set([
            d["recipient_id"] for d in performance_data 
            if d.get("opened", False) or d.get("clicked", False)
        ]))
        engagement_rate = total_engaged / total_delivered if total_delivered > 0 else 0
        
        return CampaignAnalytics(
            campaign_id=campaign.id,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_opens=total_opens,
            total_clicks=total_clicks,
            total_unsubscribes=total_unsubscribes,
            open_rate=open_rate,
            click_rate=click_rate,
            unsubscribe_rate=unsubscribe_rate,
            engagement_rate=engagement_rate
        )

"""
Newsletter API Integration - FastAPI endpoints for AI-first newsletter functionality
Integrates newsletter features with the main GoodBooks API.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import asyncio
import json

from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.core.monitoring import MetricsCollector
from src.auth.security import get_current_user, User, require_permissions
from src.newsletter.core.personalization_engine import PersonalizationEngine, UserPersona
from src.newsletter.core.content_curator import AIContentCurator, ContentItem
from src.newsletter.core.send_time_optimizer import SendTimeOptimizer
from src.newsletter.templates.adaptive_templates import AdaptiveTemplateEngine
from src.newsletter.campaigns.campaign_manager import CampaignManager, CampaignType, CampaignStatus
from src.newsletter.analytics.performance_tracker import PerformanceTracker, EngagementData, EngagementEvent
from src.newsletter.automation.workflow_engine import AIWorkflowAutomation, WorkflowDefinition, WorkflowType
from src.newsletter.engagement.interactive_engine import InteractiveEngagementEngine, InteractionContent, InteractionType
from .validation_endpoints import validation_router


# Pydantic models for API requests/responses
class UserPreferencesUpdate(BaseModel):
    """User preferences update request"""
    frequency: Optional[str] = Field(None, description="Email frequency preference")
    content_types: Optional[List[str]] = Field(None, description="Preferred content types")
    genres: Optional[List[str]] = Field(None, description="Preferred book genres")
    reading_level: Optional[str] = Field(None, description="Reading level preference")
    language: Optional[str] = Field(None, description="Language preference")
    send_time_preference: Optional[str] = Field(None, description="Preferred send time")
    interests: Optional[List[str]] = Field(None, description="User interests")


class ContentGenerationRequest(BaseModel):
    """Content generation request"""
    content_type: str = Field(..., description="Type of content to generate")
    context: Optional[Dict[str, Any]] = Field(None, description="Generation context")
    personalization_level: Optional[str] = Field("medium", description="Personalization level")
    target_audience: Optional[str] = Field(None, description="Target audience segment")
    template_style: Optional[str] = Field(None, description="Template style preference")


class CampaignCreateRequest(BaseModel):
    """Campaign creation request"""
    name: str = Field(..., description="Campaign name")
    type: str = Field(..., description="Campaign type")
    template: str = Field(..., description="Template to use")
    subject_line: str = Field(..., description="Email subject line")
    recipients: Optional[List[str]] = Field(None, description="Recipient user IDs")
    segment: Optional[str] = Field(None, description="Target segment")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled send time")
    personalize: bool = Field(True, description="Enable personalization")
    ab_test: bool = Field(False, description="Enable A/B testing")


class InteractiveContentRequest(BaseModel):
    """Interactive content creation request"""
    title: str = Field(..., description="Content title")
    description: str = Field(..., description="Content description")
    interaction_type: str = Field(..., description="Type of interaction")
    question: str = Field(..., description="Main question")
    options: List[Dict[str, Any]] = Field(..., description="Response options")
    time_limit: Optional[int] = Field(None, description="Time limit in seconds")
    points_awarded: Optional[int] = Field(10, description="Points for participation")
    ai_enhance: bool = Field(True, description="Use AI enhancement")


class InteractionResponse(BaseModel):
    """User response to interactive content"""
    content_id: str = Field(..., description="Interactive content ID")
    selected_options: Optional[List[str]] = Field(None, description="Selected option IDs")
    text_response: Optional[str] = Field(None, description="Text response")
    numeric_response: Optional[float] = Field(None, description="Numeric response")


class WorkflowCreateRequest(BaseModel):
    """Workflow creation request"""
    name: str = Field(..., description="Workflow name")
    description: str = Field(..., description="Workflow description")
    workflow_type: str = Field(..., description="Workflow type")
    triggers: List[Dict[str, Any]] = Field(..., description="Workflow triggers")
    actions: List[Dict[str, Any]] = Field(..., description="Workflow actions")
    active: bool = Field(True, description="Workflow active status")


class ChatbotMessage(BaseModel):
    """Chatbot message request"""
    message: str = Field(..., description="User message")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


# Newsletter API Router
newsletter_router = APIRouter(prefix="/newsletter", tags=["Newsletter"])
logger = StructuredLogger(__name__)


class NewsletterAPI:
    """Newsletter API integration class"""
    
    def __init__(
        self,
        cache_manager: AsyncCacheManager,
        metrics_collector: MetricsCollector
    ):
        self.cache = cache_manager
        self.metrics = metrics_collector
        self.logger = StructuredLogger(__name__)
        
        # Initialize newsletter components
        self.personalization_engine = PersonalizationEngine(cache_manager)
        self.content_curator = AIContentCurator(cache_manager)
        self.send_time_optimizer = SendTimeOptimizer(cache_manager)
        self.template_engine = AdaptiveTemplateEngine(cache_manager)
        self.campaign_manager = CampaignManager(
            cache_manager,
            self.personalization_engine,
            self.content_curator,
            self.send_time_optimizer,
            self.template_engine
        )
        self.performance_tracker = PerformanceTracker(cache_manager, metrics_collector)
        self.workflow_engine = AIWorkflowAutomation(
            cache_manager,
            self.personalization_engine,
            self.content_curator,
            self.send_time_optimizer,
            self.campaign_manager,
            self.performance_tracker
        )
        self.interactive_engine = InteractiveEngagementEngine(
            cache_manager,
            self.personalization_engine,
            self.content_curator,
            self.performance_tracker
        )
    
    async def initialize(self) -> None:
        """Initialize newsletter components"""
        try:
            await self.performance_tracker.start_background_processing()
            await self.workflow_engine.start_automation_engine()
            
            self.logger.info("Newsletter API initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize newsletter API", error=str(e))
            raise


# Global newsletter API instance
newsletter_api: Optional[NewsletterAPI] = None


async def get_newsletter_api() -> NewsletterAPI:
    """Get newsletter API instance"""
    global newsletter_api
    if newsletter_api is None:
        # This would be initialized in the main app startup
        raise HTTPException(status_code=500, detail="Newsletter API not initialized")
    return newsletter_api


# User Management Endpoints
@newsletter_router.post("/users/preferences")
async def update_user_preferences(
    preferences: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Update user newsletter preferences"""
    try:
        user_id = str(current_user.id)
        
        # Get existing profile or create new one
        user_profile = await api.personalization_engine.get_user_profile(user_id)
        if not user_profile:
            user_profile = UserPersona(user_id=user_id)
        
        # Update preferences
        if preferences.frequency:
            user_profile.frequency_preference = preferences.frequency
        if preferences.content_types:
            user_profile.content_preferences = preferences.content_types
        if preferences.genres:
            user_profile.book_genres = preferences.genres
        if preferences.reading_level:
            user_profile.reading_level = preferences.reading_level
        if preferences.language:
            user_profile.language = preferences.language
        if preferences.interests:
            user_profile.interests = preferences.interests
        
        # Save updated profile
        await api.personalization_engine.update_user_profile(user_profile)
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "profile": {
                "user_id": user_profile.user_id,
                "frequency": user_profile.frequency_preference,
                "content_types": user_profile.content_preferences,
                "reading_level": user_profile.reading_level
            }
        }
        
    except Exception as e:
        logger.error("Failed to update user preferences", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@newsletter_router.get("/users/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get user newsletter profile"""
    try:
        user_id = str(current_user.id)
        user_profile = await api.personalization_engine.get_user_profile(user_id)
        
        if not user_profile:
            return {"profile": None, "message": "Profile not found"}
        
        return {
            "profile": {
                "user_id": user_profile.user_id,
                "frequency_preference": user_profile.frequency_preference,
                "content_preferences": user_profile.content_preferences,
                "book_genres": getattr(user_profile, 'book_genres', []),
                "reading_level": user_profile.reading_level,
                "language": user_profile.language,
                "interests": user_profile.interests,
                "engagement_score": user_profile.engagement_score,
                "persona_type": user_profile.persona_type,
                "created_at": user_profile.created_at.isoformat(),
                "last_updated": user_profile.last_updated.isoformat()
            }
        }
        
    except Exception as e:
        logger.error("Failed to get user profile", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


# Content Generation Endpoints
@newsletter_router.post("/content/generate")
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Generate AI-powered newsletter content"""
    try:
        user_id = str(current_user.id)
        
        generation_params = {
            "content_type": request.content_type,
            "context": request.context or {},
            "personalization_level": request.personalization_level,
            "target_audience": request.target_audience,
            "template_style": request.template_style
        }
        
        generated_content = await api.content_curator.generate_personalized_content(
            user_id, generation_params
        )
        
        return {
            "success": True,
            "content": generated_content,
            "generation_params": generation_params,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to generate content", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate content")


@newsletter_router.get("/content/curated")
async def get_curated_content(
    content_type: str = Query(..., description="Type of content to retrieve"),
    limit: int = Query(10, description="Number of items to retrieve"),
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get curated content for user"""
    try:
        user_id = str(current_user.id)
        
        curated_content = await api.content_curator.get_curated_content_for_user(
            user_id, content_type, limit
        )
        
        return {
            "success": True,
            "content_type": content_type,
            "items": curated_content,
            "count": len(curated_content),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get curated content", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve curated content")


# Campaign Management Endpoints
@newsletter_router.post("/campaigns")
async def create_campaign(
    request: CampaignCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Create a new newsletter campaign"""
    try:
        # Validate campaign type
        try:
            campaign_type = CampaignType(request.type.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid campaign type: {request.type}")
        
        campaign_config = {
            "name": request.name,
            "type": campaign_type,
            "template": request.template,
            "subject_line": request.subject_line,
            "recipients": request.recipients or [],
            "segment": request.segment,
            "schedule_time": request.schedule_time,
            "personalize": request.personalize,
            "ab_test": request.ab_test,
            "created_by": str(current_user.id)
        }
        
        campaign_id = await api.campaign_manager.create_campaign(campaign_config)
        
        # Schedule campaign if requested
        if request.schedule_time and request.schedule_time > datetime.utcnow():
            background_tasks.add_task(
                api.campaign_manager.schedule_campaign,
                campaign_id,
                request.schedule_time
            )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": "Campaign created successfully",
            "scheduled": bool(request.schedule_time)
        }
        
    except Exception as e:
        logger.error("Failed to create campaign", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create campaign")


@newsletter_router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Send a newsletter campaign"""
    try:
        # Send campaign in background
        background_tasks.add_task(api.campaign_manager.send_campaign, campaign_id)
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": "Campaign send initiated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to send campaign", campaign_id=campaign_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to send campaign")


@newsletter_router.get("/campaigns/{campaign_id}/status")
async def get_campaign_status(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get campaign status and metrics"""
    try:
        status = await api.campaign_manager.get_campaign_status(campaign_id)
        metrics = await api.performance_tracker.calculate_campaign_metrics(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "status": status,
            "metrics": {
                "total_sent": metrics.total_sent,
                "total_delivered": metrics.total_delivered,
                "open_rate": metrics.open_rate,
                "click_rate": metrics.click_rate,
                "conversion_rate": metrics.conversion_rate,
                "engagement_score": metrics.engagement_score
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get campaign status", campaign_id=campaign_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get campaign status")


# Interactive Content Endpoints
@newsletter_router.post("/interactive/content")
async def create_interactive_content(
    request: InteractiveContentRequest,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Create interactive content (polls, quizzes, etc.)"""
    try:
        user_id = str(current_user.id)
        
        # Validate interaction type
        try:
            interaction_type = InteractionType(request.interaction_type.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid interaction type: {request.interaction_type}")
        
        content_data = {
            "title": request.title,
            "description": request.description,
            "interaction_type": interaction_type,
            "question": request.question,
            "options": [
                {
                    "text": opt.get("text", ""),
                    "value": opt.get("value"),
                    "correct": opt.get("correct", False)
                }
                for opt in request.options
            ],
            "time_limit": request.time_limit,
            "points_awarded": request.points_awarded,
            "ai_generated": request.ai_enhance
        }
        
        content_id = await api.interactive_engine.create_interactive_content(
            content_data,
            user_id if request.ai_enhance else None
        )
        
        return {
            "success": True,
            "content_id": content_id,
            "message": "Interactive content created successfully"
        }
        
    except Exception as e:
        logger.error("Failed to create interactive content", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create interactive content")


@newsletter_router.post("/interactive/respond")
async def submit_interaction_response(
    response: InteractionResponse,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Submit response to interactive content"""
    try:
        user_id = str(current_user.id)
        
        response_data = {
            "selected_options": response.selected_options or [],
            "text_response": response.text_response,
            "numeric_response": response.numeric_response,
            "response_time": 0.0,  # Would be calculated from client timing
            "device_info": {"type": "web"},  # Would come from request headers
            "location_info": {}
        }
        
        result = await api.interactive_engine.submit_response(
            user_id,
            response.content_id,
            response_data
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to submit interaction response", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to submit response")


@newsletter_router.get("/interactive/{content_id}/analytics")
async def get_interaction_analytics(
    content_id: str,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get analytics for interactive content"""
    try:
        analytics = await api.interactive_engine.get_interaction_analytics(content_id)
        return analytics
        
    except Exception as e:
        logger.error("Failed to get interaction analytics", content_id=content_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get analytics")


# Chatbot Endpoints
@newsletter_router.post("/chatbot/create")
async def create_chatbot_session(
    context: Dict[str, Any] = Body({}),
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Create AI chatbot session"""
    try:
        user_id = str(current_user.id)
        
        chatbot_id = await api.interactive_engine.create_ai_chatbot(user_id, context)
        
        return {
            "success": True,
            "chatbot_id": chatbot_id,
            "message": "Chatbot session created"
        }
        
    except Exception as e:
        logger.error("Failed to create chatbot session", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create chatbot session")


@newsletter_router.post("/chatbot/{chatbot_id}/message")
async def send_chatbot_message(
    chatbot_id: str,
    message: ChatbotMessage,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Send message to AI chatbot"""
    try:
        response = await api.interactive_engine.chat_with_bot(
            chatbot_id,
            message.message,
            message.context
        )
        
        return response
        
    except Exception as e:
        logger.error("Failed to process chatbot message", chatbot_id=chatbot_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process message")


# Workflow Automation Endpoints
@newsletter_router.post("/workflows")
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Create automated workflow"""
    try:
        # Validate workflow type
        try:
            workflow_type = WorkflowType(request.workflow_type.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid workflow type: {request.workflow_type}")
        
        workflow_def = WorkflowDefinition(
            name=request.name,
            description=request.description,
            workflow_type=workflow_type,
            triggers=request.triggers,
            actions=request.actions,
            active=request.active
        )
        
        workflow_id = await api.workflow_engine.create_workflow(workflow_def)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow created successfully"
        }
        
    except Exception as e:
        logger.error("Failed to create workflow", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create workflow")


@newsletter_router.post("/workflows/{workflow_id}/trigger")
async def trigger_workflow(
    workflow_id: str,
    context: Dict[str, Any] = Body({}),
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Manually trigger a workflow"""
    try:
        user_id = str(current_user.id)
        
        execution_id = await api.workflow_engine.trigger_workflow(
            workflow_id,
            user_id,
            {"triggered_by": "manual", **context}
        )
        
        return {
            "success": True,
            "execution_id": execution_id,
            "message": "Workflow triggered successfully"
        }
        
    except Exception as e:
        logger.error("Failed to trigger workflow", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")


@newsletter_router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get workflow status and metrics"""
    try:
        status = await api.workflow_engine.get_workflow_status(workflow_id)
        return status
        
    except Exception as e:
        logger.error("Failed to get workflow status", workflow_id=workflow_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get workflow status")


# Analytics and Reporting Endpoints
@newsletter_router.get("/analytics/dashboard")
async def get_newsletter_dashboard(
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get real-time newsletter dashboard data"""
    try:
        dashboard_data = await api.performance_tracker.get_real_time_dashboard_data()
        
        # Add user-specific data
        user_id = str(current_user.id)
        user_history = await api.interactive_engine.get_user_interaction_history(user_id)
        
        dashboard_data["user_stats"] = user_history.get("stats", {})
        
        return dashboard_data
        
    except Exception as e:
        logger.error("Failed to get newsletter dashboard", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


@newsletter_router.get("/analytics/engagement/{user_id}")
async def get_user_engagement_analytics(
    user_id: str,
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get detailed user engagement analytics"""
    try:
        # Check if user can access this data (admin or self)
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        engagement_score = await api.performance_tracker.calculate_user_engagement_score(user_id)
        interaction_history = await api.interactive_engine.get_user_interaction_history(user_id)
        
        return {
            "user_id": user_id,
            "engagement_score": engagement_score,
            "interaction_history": interaction_history,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get user engagement analytics", target_user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get engagement analytics")


# Event Tracking Endpoints
@newsletter_router.post("/events/track")
async def track_engagement_event(
    event_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Track user engagement event"""
    try:
        user_id = str(current_user.id)
        
        # Validate event type
        try:
            event_type = EngagementEvent(event_data.get("event_type"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid event type")
        
        engagement_data = EngagementData(
            user_id=user_id,
            event_type=event_type,
            metadata=event_data.get("metadata", {}),
            device_info=event_data.get("device_info", {}),
            location_info=event_data.get("location_info", {}),
            content_id=event_data.get("content_id", ""),
            value=event_data.get("value", 0.0)
        )
        
        await api.performance_tracker.track_event(engagement_data)
        
        return {
            "success": True,
            "event_id": engagement_data.event_id,
            "message": "Event tracked successfully"
        }
        
    except Exception as e:
        logger.error("Failed to track engagement event", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to track event")


# Admin Endpoints
@newsletter_router.get("/admin/stats")
async def get_admin_newsletter_stats(
    current_user: User = Depends(get_current_user),
    api: NewsletterAPI = Depends(get_newsletter_api)
):
    """Get comprehensive newsletter statistics (admin only)"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get system-wide statistics
        dashboard_data = await api.performance_tracker.get_real_time_dashboard_data()
        
        # Add additional admin metrics
        admin_stats = {
            "system_overview": dashboard_data,
            "active_campaigns": len([c for c in api.campaign_manager.campaigns.values() if c.status == CampaignStatus.ACTIVE]),
            "total_users": len(api.personalization_engine.user_profiles),
            "active_workflows": len([w for w in api.workflow_engine.workflows.values() if w.active]),
            "interactive_content_count": len(api.interactive_engine.interactive_content),
            "performance_summary": {
                "avg_open_rate": 0.0,  # Would calculate from all campaigns
                "avg_click_rate": 0.0,
                "avg_engagement_score": 0.0
            }
        }
        
        return admin_stats
        
    except Exception as e:
        logger.error("Failed to get admin newsletter stats", user_id=str(current_user.id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get admin stats")


# Include validation router
newsletter_router.include_router(validation_router, prefix="/validation")


# Initialize function to set up the newsletter API
async def initialize_newsletter_api(cache_manager: AsyncCacheManager, metrics_collector: MetricsCollector) -> NewsletterAPI:
    """Initialize the newsletter API with dependencies"""
    global newsletter_api
    
    newsletter_api = NewsletterAPI(cache_manager, metrics_collector)
    await newsletter_api.initialize()
    
    return newsletter_api

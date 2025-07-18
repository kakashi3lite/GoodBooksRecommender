"""
Interactive Engagement Engine - Multimodal User Interactions
Handles polls, quizzes, interactive content, and AI-powered conversations.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd

from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.newsletter.core.personalization_engine import PersonalizationEngine, UserPersona
from src.newsletter.core.content_curator import AIContentCurator
from src.newsletter.analytics.performance_tracker import PerformanceTracker, EngagementEvent


class InteractionType(Enum):
    """Types of interactive content"""
    POLL = "poll"
    QUIZ = "quiz"
    SURVEY = "survey"
    CHATBOT = "chatbot"
    RATING = "rating"
    FEEDBACK = "feedback"
    GAME = "game"
    CHALLENGE = "challenge"
    DISCUSSION = "discussion"
    VOTE = "vote"
    PREDICT = "predict"
    SHARE_STORY = "share_story"


class ResponseType(Enum):
    """Types of user responses"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_INPUT = "text_input"
    NUMERIC_INPUT = "numeric_input"
    RATING_SCALE = "rating_scale"
    SLIDER = "slider"
    FILE_UPLOAD = "file_upload"
    VOICE_INPUT = "voice_input"
    DRAWING = "drawing"
    EMOJI_REACTION = "emoji_reaction"


class ContentModality(Enum):
    """Content modalities for multimodal experiences"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    INTERACTIVE_WIDGET = "interactive_widget"
    AUGMENTED_REALITY = "augmented_reality"
    VIRTUAL_REALITY = "virtual_reality"
    HAPTIC_FEEDBACK = "haptic_feedback"


@dataclass
class InteractionOption:
    """Individual option for interactive content"""
    option_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    value: Any = None
    media_url: Optional[str] = None
    correct: bool = False  # For quizzes
    weight: float = 1.0  # For weighted responses
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionContent:
    """Interactive content definition"""
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    interaction_type: InteractionType = InteractionType.POLL
    response_type: ResponseType = ResponseType.SINGLE_CHOICE
    modalities: List[ContentModality] = field(default_factory=list)
    
    # Content data
    question: str = ""
    options: List[InteractionOption] = field(default_factory=list)
    media_content: Dict[str, str] = field(default_factory=dict)  # URLs by modality
    
    # Configuration
    time_limit: Optional[int] = None  # seconds
    max_responses: Optional[int] = None
    allow_anonymous: bool = True
    require_explanation: bool = False
    randomize_options: bool = False
    
    # AI enhancement
    ai_generated: bool = False
    personalization_level: str = "medium"
    adaptive_difficulty: bool = False
    
    # Gamification
    points_awarded: int = 0
    achievements: List[str] = field(default_factory=list)
    leaderboard_eligible: bool = False
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class UserResponse:
    """User response to interactive content"""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str = ""
    user_id: str = ""
    session_id: str = ""
    
    # Response data
    selected_options: List[str] = field(default_factory=list)
    text_response: Optional[str] = None
    numeric_response: Optional[float] = None
    media_response: Optional[str] = None  # URL to uploaded media
    
    # Metadata
    response_time: float = 0.0  # seconds taken to respond
    device_info: Dict[str, str] = field(default_factory=dict)
    location_info: Dict[str, str] = field(default_factory=dict)
    confidence_score: Optional[float] = None
    
    # AI analysis
    sentiment_score: Optional[float] = None
    engagement_score: Optional[float] = None
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InteractionSession:
    """Interactive session tracking"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    content_ids: List[str] = field(default_factory=list)
    responses: List[UserResponse] = field(default_factory=list)
    
    # Session metrics
    total_time: float = 0.0
    completion_rate: float = 0.0
    engagement_score: float = 0.0
    
    # Personalization
    difficulty_level: str = "medium"
    content_preferences: List[str] = field(default_factory=list)
    
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class ContentAnalytics:
    """Analytics for interactive content"""
    content_id: str = ""
    total_views: int = 0
    total_responses: int = 0
    completion_rate: float = 0.0
    average_response_time: float = 0.0
    engagement_score: float = 0.0
    
    # Response distribution
    option_distribution: Dict[str, int] = field(default_factory=dict)
    sentiment_distribution: Dict[str, float] = field(default_factory=dict)
    
    # Demographics
    age_distribution: Dict[str, int] = field(default_factory=dict)
    device_distribution: Dict[str, int] = field(default_factory=dict)
    location_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Insights
    ai_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    last_updated: datetime = field(default_factory=datetime.utcnow)


class InteractiveEngagementEngine:
    """Engine for creating and managing interactive content experiences"""
    
    def __init__(
        self,
        cache_manager: AsyncCacheManager,
        personalization_engine: PersonalizationEngine,
        content_curator: AIContentCurator,
        performance_tracker: PerformanceTracker
    ):
        self.cache = cache_manager
        self.personalization_engine = personalization_engine
        self.content_curator = content_curator
        self.performance_tracker = performance_tracker
        self.logger = StructuredLogger(__name__)
        
        # Content storage
        self.interactive_content: Dict[str, InteractionContent] = {}
        self.user_responses: Dict[str, List[UserResponse]] = {}
        self.sessions: Dict[str, InteractionSession] = {}
        self.analytics: Dict[str, ContentAnalytics] = {}
        
        # AI chatbot instances
        self.active_chatbots: Dict[str, 'AINewsletterChatbot'] = {}
        
        # Real-time interaction tracking
        self.active_interactions: Dict[str, Dict[str, Any]] = {}
        
        # Gamification
        self.user_points: Dict[str, int] = {}
        self.leaderboards: Dict[str, List[Dict[str, Any]]] = {}
        self.achievements: Dict[str, List[str]] = {}
    
    async def create_interactive_content(
        self,
        content_data: Dict[str, Any],
        personalize_for_user: Optional[str] = None
    ) -> str:
        """Create new interactive content with AI enhancement"""
        try:
            # Create base content
            content = InteractionContent(**content_data)
            
            # AI enhancement if requested
            if content.ai_generated or personalize_for_user:
                content = await self._enhance_content_with_ai(content, personalize_for_user)
            
            # Store content
            content_id = content.content_id
            self.interactive_content[content_id] = content
            
            # Initialize analytics
            self.analytics[content_id] = ContentAnalytics(content_id=content_id)
            
            # Cache content
            cache_key = f"interactive_content:{content_id}"
            await self.cache.set(cache_key, content.__dict__, ttl=86400 * 7)
            
            self.logger.info(
                "Interactive content created",
                content_id=content_id,
                interaction_type=content.interaction_type.value,
                ai_generated=content.ai_generated
            )
            
            return content_id
            
        except Exception as e:
            self.logger.error(
                "Failed to create interactive content",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _enhance_content_with_ai(
        self,
        content: InteractionContent,
        user_id: Optional[str] = None
    ) -> InteractionContent:
        """Enhance content with AI-generated elements"""
        try:
            # Get user profile for personalization
            user_profile = None
            if user_id:
                user_profile = await self.personalization_engine.get_user_profile(user_id)
            
            # Generate personalized question and options
            if content.interaction_type in [InteractionType.QUIZ, InteractionType.POLL]:
                enhanced_content = await self._generate_quiz_content(content, user_profile)
                content.question = enhanced_content.get("question", content.question)
                
                # Generate AI-enhanced options
                if enhanced_content.get("options"):
                    content.options = []
                    for i, option_text in enumerate(enhanced_content["options"]):
                        option = InteractionOption(
                            text=option_text,
                            value=i,
                            correct=enhanced_content.get("correct_answers", [False] * len(enhanced_content["options"]))[i]
                        )
                        content.options.append(option)
            
            # Generate multimodal content
            if ContentModality.IMAGE in content.modalities:
                image_prompt = await self._generate_image_prompt(content, user_profile)
                # In production, this would call an image generation API
                content.media_content["image"] = f"generated_image_{content.content_id}.jpg"
            
            if ContentModality.AUDIO in content.modalities:
                # Generate audio content description
                audio_script = await self._generate_audio_script(content, user_profile)
                content.media_content["audio"] = f"generated_audio_{content.content_id}.mp3"
                content.metadata["audio_script"] = audio_script
            
            content.ai_generated = True
            return content
            
        except Exception as e:
            self.logger.error("Failed to enhance content with AI", error=str(e))
            return content
    
    async def _generate_quiz_content(
        self,
        content: InteractionContent,
        user_profile: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Generate quiz content using AI"""
        try:
            # Create context for AI generation
            context = {
                "interaction_type": content.interaction_type.value,
                "title": content.title,
                "description": content.description,
                "personalization_level": content.personalization_level
            }
            
            if user_profile:
                context["user_preferences"] = user_profile.content_preferences
                context["reading_level"] = user_profile.reading_level
                context["interests"] = user_profile.interests
            
            # Generate content using content curator
            generation_params = {
                "content_type": "interactive_quiz",
                "context": context,
                "num_options": 4,
                "difficulty": content.metadata.get("difficulty", "medium")
            }
            
            generated = await self.content_curator.generate_personalized_content(
                user_profile.user_id if user_profile else "anonymous",
                generation_params
            )
            
            return {
                "question": generated.get("question", content.question),
                "options": generated.get("options", []),
                "correct_answers": generated.get("correct_answers", []),
                "explanation": generated.get("explanation", "")
            }
            
        except Exception as e:
            self.logger.error("Failed to generate quiz content", error=str(e))
            return {"question": content.question, "options": []}
    
    async def _generate_image_prompt(
        self,
        content: InteractionContent,
        user_profile: Optional[Any] = None
    ) -> str:
        """Generate image prompt for visual content"""
        base_prompt = f"Create an engaging visual for {content.title}: {content.description}"
        
        if user_profile and user_profile.visual_preferences:
            style_preferences = ", ".join(user_profile.visual_preferences)
            base_prompt += f" in {style_preferences} style"
        
        return base_prompt
    
    async def _generate_audio_script(
        self,
        content: InteractionContent,
        user_profile: Optional[Any] = None
    ) -> str:
        """Generate audio script for voice content"""
        script = f"Welcome to {content.title}. {content.description}"
        
        if content.question:
            script += f" Here's the question: {content.question}"
        
        if user_profile and user_profile.audio_preferences:
            # Adjust script based on audio preferences (tone, pace, etc.)
            pass
        
        return script
    
    async def submit_response(
        self,
        user_id: str,
        content_id: str,
        response_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit user response to interactive content"""
        try:
            if content_id not in self.interactive_content:
                raise ValueError("Interactive content not found")
            
            content = self.interactive_content[content_id]
            
            # Create response object
            response = UserResponse(
                content_id=content_id,
                user_id=user_id,
                session_id=session_id or str(uuid.uuid4()),
                **response_data
            )
            
            # Validate response
            validation_result = await self._validate_response(response, content)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "response_id": response.response_id
                }
            
            # AI analysis of response
            await self._analyze_response_with_ai(response, content)
            
            # Store response
            if user_id not in self.user_responses:
                self.user_responses[user_id] = []
            self.user_responses[user_id].append(response)
            
            # Update session
            if session_id:
                await self._update_session(session_id, response)
            
            # Update analytics
            await self._update_content_analytics(content_id, response)
            
            # Track engagement event
            engagement_event = EngagementEvent.POLL_ANSWERED if content.interaction_type == InteractionType.POLL else EngagementEvent.QUIZ_COMPLETED
            await self.performance_tracker.track_event(
                EngagementData(
                    user_id=user_id,
                    event_type=engagement_event,
                    metadata={
                        "content_id": content_id,
                        "interaction_type": content.interaction_type.value,
                        "response_time": response.response_time
                    }
                )
            )
            
            # Calculate gamification rewards
            rewards = await self._calculate_rewards(response, content)
            
            # Generate personalized feedback
            feedback = await self._generate_personalized_feedback(response, content)
            
            # Cache response
            cache_key = f"user_response:{response.response_id}"
            await self.cache.set(cache_key, response.__dict__, ttl=86400 * 30)
            
            self.logger.info(
                "User response submitted",
                response_id=response.response_id,
                user_id=user_id,
                content_id=content_id,
                interaction_type=content.interaction_type.value
            )
            
            return {
                "success": True,
                "response_id": response.response_id,
                "feedback": feedback,
                "rewards": rewards,
                "analytics": await self._get_response_analytics(response, content)
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to submit response",
                user_id=user_id,
                content_id=content_id,
                error=str(e),
                exc_info=True
            )
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_response(
        self,
        response: UserResponse,
        content: InteractionContent
    ) -> Dict[str, Any]:
        """Validate user response against content requirements"""
        try:
            # Check if content has expired
            if content.expires_at and datetime.utcnow() > content.expires_at:
                return {"valid": False, "error": "Content has expired"}
            
            # Check max responses limit
            if content.max_responses:
                total_responses = len([
                    r for responses in self.user_responses.values()
                    for r in responses if r.content_id == content.content_id
                ])
                if total_responses >= content.max_responses:
                    return {"valid": False, "error": "Maximum responses reached"}
            
            # Validate response format
            if content.response_type == ResponseType.SINGLE_CHOICE:
                if len(response.selected_options) != 1:
                    return {"valid": False, "error": "Single choice required"}
            
            elif content.response_type == ResponseType.MULTIPLE_CHOICE:
                if not response.selected_options:
                    return {"valid": False, "error": "At least one choice required"}
            
            elif content.response_type == ResponseType.TEXT_INPUT:
                if not response.text_response:
                    return {"valid": False, "error": "Text response required"}
            
            elif content.response_type == ResponseType.NUMERIC_INPUT:
                if response.numeric_response is None:
                    return {"valid": False, "error": "Numeric response required"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def _analyze_response_with_ai(
        self,
        response: UserResponse,
        content: InteractionContent
    ) -> None:
        """Analyze response using AI for insights"""
        try:
            # Sentiment analysis for text responses
            if response.text_response:
                # In production, this would use NLP models
                sentiment_score = await self._analyze_text_sentiment(response.text_response)
                response.sentiment_score = sentiment_score
            
            # Engagement score calculation
            base_engagement = 0.5
            
            # Time-based adjustment
            if content.time_limit and response.response_time:
                time_factor = min(1.0, content.time_limit / response.response_time)
                base_engagement += time_factor * 0.3
            
            # Response depth for text
            if response.text_response:
                word_count = len(response.text_response.split())
                depth_factor = min(1.0, word_count / 50)  # Normalize to 50 words
                base_engagement += depth_factor * 0.2
            
            response.engagement_score = min(1.0, base_engagement)
            
            # AI insights
            response.ai_insights = {
                "engagement_factors": ["response_time", "content_depth"],
                "personalization_opportunities": ["content_style", "difficulty_level"],
                "follow_up_suggestions": ["related_content", "deeper_exploration"]
            }
            
        except Exception as e:
            self.logger.error("Failed to analyze response with AI", error=str(e))
    
    async def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text response"""
        # Simplified sentiment analysis - in production use proper NLP models
        positive_words = ["good", "great", "excellent", "love", "amazing", "fantastic"]
        negative_words = ["bad", "terrible", "awful", "hate", "horrible", "worst"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.5  # Neutral
        
        return positive_count / (positive_count + negative_count)
    
    async def _update_session(self, session_id: str, response: UserResponse) -> None:
        """Update interaction session with new response"""
        try:
            if session_id not in self.sessions:
                self.sessions[session_id] = InteractionSession(
                    session_id=session_id,
                    user_id=response.user_id
                )
            
            session = self.sessions[session_id]
            session.responses.append(response)
            
            if response.content_id not in session.content_ids:
                session.content_ids.append(response.content_id)
            
            # Update session metrics
            session.total_time += response.response_time
            session.completion_rate = len(session.responses) / len(session.content_ids) if session.content_ids else 0
            
            # Calculate session engagement
            if session.responses:
                avg_engagement = sum(r.engagement_score or 0.5 for r in session.responses) / len(session.responses)
                session.engagement_score = avg_engagement
            
            # Cache session
            cache_key = f"interaction_session:{session_id}"
            await self.cache.set(cache_key, session.__dict__, ttl=86400)
            
        except Exception as e:
            self.logger.error("Failed to update session", session_id=session_id, error=str(e))
    
    async def _update_content_analytics(self, content_id: str, response: UserResponse) -> None:
        """Update content analytics with new response"""
        try:
            if content_id not in self.analytics:
                self.analytics[content_id] = ContentAnalytics(content_id=content_id)
            
            analytics = self.analytics[content_id]
            analytics.total_responses += 1
            
            # Update response time
            if response.response_time:
                total_time = analytics.average_response_time * (analytics.total_responses - 1)
                analytics.average_response_time = (total_time + response.response_time) / analytics.total_responses
            
            # Update option distribution
            for option_id in response.selected_options:
                analytics.option_distribution[option_id] = analytics.option_distribution.get(option_id, 0) + 1
            
            # Update sentiment distribution
            if response.sentiment_score is not None:
                sentiment_bucket = "positive" if response.sentiment_score > 0.6 else "negative" if response.sentiment_score < 0.4 else "neutral"
                analytics.sentiment_distribution[sentiment_bucket] = analytics.sentiment_distribution.get(sentiment_bucket, 0) + 1
            
            # Update device distribution
            if response.device_info.get("type"):
                device = response.device_info["type"]
                analytics.device_distribution[device] = analytics.device_distribution.get(device, 0) + 1
            
            analytics.last_updated = datetime.utcnow()
            
            # Cache analytics
            cache_key = f"content_analytics:{content_id}"
            await self.cache.set(cache_key, analytics.__dict__, ttl=3600)
            
        except Exception as e:
            self.logger.error("Failed to update content analytics", content_id=content_id, error=str(e))
    
    async def _calculate_rewards(
        self,
        response: UserResponse,
        content: InteractionContent
    ) -> Dict[str, Any]:
        """Calculate gamification rewards for response"""
        try:
            rewards = {
                "points": 0,
                "achievements": [],
                "badges": [],
                "leaderboard_position": None
            }
            
            # Base points for participation
            base_points = content.points_awarded or 10
            
            # Engagement bonus
            if response.engagement_score:
                engagement_bonus = int(base_points * response.engagement_score)
                rewards["points"] += engagement_bonus
            
            # Speed bonus for quick responses
            if content.time_limit and response.response_time:
                if response.response_time < content.time_limit * 0.5:
                    rewards["points"] += 5
                    rewards["badges"].append("speed_demon")
            
            # Quality bonus for detailed text responses
            if response.text_response and len(response.text_response.split()) > 20:
                rewards["points"] += 10
                rewards["badges"].append("thoughtful_responder")
            
            # Quiz correctness bonus
            if content.interaction_type == InteractionType.QUIZ:
                correct_answers = await self._check_quiz_correctness(response, content)
                if correct_answers > 0:
                    rewards["points"] += correct_answers * 5
                    if correct_answers == len(content.options):
                        rewards["achievements"].append("perfect_score")
            
            # Update user points
            user_id = response.user_id
            if user_id not in self.user_points:
                self.user_points[user_id] = 0
            self.user_points[user_id] += rewards["points"]
            
            # Update achievements
            if user_id not in self.achievements:
                self.achievements[user_id] = []
            self.achievements[user_id].extend(rewards["achievements"])
            
            return rewards
            
        except Exception as e:
            self.logger.error("Failed to calculate rewards", error=str(e))
            return {"points": 0, "achievements": [], "badges": []}
    
    async def _check_quiz_correctness(
        self,
        response: UserResponse,
        content: InteractionContent
    ) -> int:
        """Check correctness of quiz response"""
        correct_count = 0
        
        for option_id in response.selected_options:
            for option in content.options:
                if option.option_id == option_id and option.correct:
                    correct_count += 1
                    break
        
        return correct_count
    
    async def _generate_personalized_feedback(
        self,
        response: UserResponse,
        content: InteractionContent
    ) -> Dict[str, Any]:
        """Generate personalized feedback for user response"""
        try:
            feedback = {
                "message": "Thank you for your response!",
                "insights": [],
                "next_steps": [],
                "related_content": []
            }
            
            # Quiz-specific feedback
            if content.interaction_type == InteractionType.QUIZ:
                correct_answers = await self._check_quiz_correctness(response, content)
                total_questions = len([opt for opt in content.options if opt.correct])
                
                if correct_answers == total_questions:
                    feedback["message"] = "Perfect! You got all answers correct! 🎉"
                elif correct_answers > total_questions * 0.7:
                    feedback["message"] = "Great job! You did really well! 👏"
                else:
                    feedback["message"] = "Good effort! Here's some additional information to help you learn:"
                
                # Add explanations for incorrect answers
                for option in content.options:
                    if option.correct and option.option_id not in response.selected_options:
                        feedback["insights"].append(f"The correct answer was: {option.text}")
            
            # Engagement-based feedback
            if response.engagement_score and response.engagement_score > 0.8:
                feedback["insights"].append("We loved your enthusiastic participation!")
            
            # Text response feedback
            if response.text_response:
                word_count = len(response.text_response.split())
                if word_count > 30:
                    feedback["insights"].append("Thank you for your detailed thoughts!")
                
                # Sentiment-based feedback
                if response.sentiment_score:
                    if response.sentiment_score > 0.7:
                        feedback["insights"].append("We're glad you're enjoying the content!")
                    elif response.sentiment_score < 0.3:
                        feedback["insights"].append("We appreciate your honest feedback and will work to improve.")
            
            # Suggest next steps
            feedback["next_steps"] = [
                "Try our next interactive quiz",
                "Share your thoughts with the community",
                "Explore related topics"
            ]
            
            # Recommend related content
            feedback["related_content"] = [
                {"title": "Advanced Quiz on Similar Topics", "type": "quiz"},
                {"title": "Discussion: What Others Think", "type": "discussion"},
                {"title": "Deep Dive Article", "type": "article"}
            ]
            
            return feedback
            
        except Exception as e:
            self.logger.error("Failed to generate feedback", error=str(e))
            return {"message": "Thank you for participating!"}
    
    async def _get_response_analytics(
        self,
        response: UserResponse,
        content: InteractionContent
    ) -> Dict[str, Any]:
        """Get analytics for the response"""
        analytics = self.analytics.get(content.content_id)
        if not analytics:
            return {}
        
        return {
            "your_response_time": response.response_time,
            "average_response_time": analytics.average_response_time,
            "total_responses": analytics.total_responses,
            "your_engagement_score": response.engagement_score,
            "response_distribution": analytics.option_distribution
        }
    
    async def create_ai_chatbot(
        self,
        user_id: str,
        context: Dict[str, Any]
    ) -> str:
        """Create an AI chatbot instance for personalized conversations"""
        try:
            chatbot_id = str(uuid.uuid4())
            
            chatbot = AINewsletterChatbot(
                chatbot_id=chatbot_id,
                user_id=user_id,
                personalization_engine=self.personalization_engine,
                content_curator=self.content_curator,
                context=context
            )
            
            self.active_chatbots[chatbot_id] = chatbot
            await chatbot.initialize()
            
            self.logger.info(
                "AI chatbot created",
                chatbot_id=chatbot_id,
                user_id=user_id
            )
            
            return chatbot_id
            
        except Exception as e:
            self.logger.error(
                "Failed to create AI chatbot",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def chat_with_bot(
        self,
        chatbot_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message to AI chatbot and get response"""
        try:
            if chatbot_id not in self.active_chatbots:
                raise ValueError("Chatbot not found")
            
            chatbot = self.active_chatbots[chatbot_id]
            response = await chatbot.process_message(message, context)
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to process chatbot message",
                chatbot_id=chatbot_id,
                error=str(e)
            )
            return {
                "success": False,
                "error": "Failed to process message"
            }
    
    async def get_interaction_analytics(self, content_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for interactive content"""
        try:
            if content_id not in self.analytics:
                return {"error": "Content not found"}
            
            analytics = self.analytics[content_id]
            content = self.interactive_content[content_id]
            
            # Calculate advanced metrics
            engagement_rate = analytics.engagement_score if hasattr(analytics, 'engagement_score') else 0.5
            completion_rate = analytics.completion_rate if hasattr(analytics, 'completion_rate') else analytics.total_responses / max(analytics.total_views, 1)
            
            return {
                "content_info": {
                    "id": content_id,
                    "title": content.title,
                    "type": content.interaction_type.value,
                    "created_at": content.created_at.isoformat()
                },
                "metrics": {
                    "total_views": analytics.total_views,
                    "total_responses": analytics.total_responses,
                    "completion_rate": completion_rate,
                    "engagement_rate": engagement_rate,
                    "average_response_time": analytics.average_response_time
                },
                "distributions": {
                    "responses": analytics.option_distribution,
                    "sentiment": analytics.sentiment_distribution,
                    "devices": analytics.device_distribution,
                    "locations": analytics.location_distribution
                },
                "insights": analytics.ai_insights,
                "recommendations": analytics.recommendations
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to get interaction analytics",
                content_id=content_id,
                error=str(e)
            )
            return {"error": "Failed to retrieve analytics"}
    
    async def get_user_interaction_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's interaction history and stats"""
        try:
            user_responses = self.user_responses.get(user_id, [])
            user_sessions = [s for s in self.sessions.values() if s.user_id == user_id]
            
            # Calculate user stats
            total_interactions = len(user_responses)
            total_points = self.user_points.get(user_id, 0)
            user_achievements = self.achievements.get(user_id, [])
            
            # Engagement metrics
            avg_engagement = sum(r.engagement_score or 0.5 for r in user_responses) / max(total_interactions, 1)
            avg_response_time = sum(r.response_time for r in user_responses) / max(total_interactions, 1)
            
            # Interaction type breakdown
            interaction_types = {}
            for response in user_responses:
                content = self.interactive_content.get(response.content_id)
                if content:
                    interaction_type = content.interaction_type.value
                    interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1
            
            return {
                "user_id": user_id,
                "stats": {
                    "total_interactions": total_interactions,
                    "total_points": total_points,
                    "achievements": user_achievements,
                    "average_engagement": avg_engagement,
                    "average_response_time": avg_response_time
                },
                "interaction_breakdown": interaction_types,
                "recent_sessions": [
                    {
                        "session_id": s.session_id,
                        "started_at": s.started_at.isoformat(),
                        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
                        "engagement_score": s.engagement_score,
                        "total_interactions": len(s.responses)
                    }
                    for s in sorted(user_sessions, key=lambda x: x.started_at, reverse=True)[:10]
                ]
            }
            
        except Exception as e:
            self.logger.error(
                "Failed to get user interaction history",
                user_id=user_id,
                error=str(e)
            )
            return {"error": "Failed to retrieve user history"}


class AINewsletterChatbot:
    """AI-powered chatbot for personalized newsletter conversations"""
    
    def __init__(
        self,
        chatbot_id: str,
        user_id: str,
        personalization_engine: PersonalizationEngine,
        content_curator: AIContentCurator,
        context: Dict[str, Any]
    ):
        self.chatbot_id = chatbot_id
        self.user_id = user_id
        self.personalization_engine = personalization_engine
        self.content_curator = content_curator
        self.context = context
        self.logger = StructuredLogger(__name__)
        
        # Conversation state
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_profile: Optional[Any] = None
        self.current_topic: Optional[str] = None
        self.conversation_state: str = "greeting"
        
        # AI personality
        self.personality = {
            "tone": "friendly",
            "expertise_level": "adaptive",
            "response_style": "conversational",
            "humor_level": "light"
        }
    
    async def initialize(self) -> None:
        """Initialize chatbot with user profile and context"""
        try:
            self.user_profile = await self.personalization_engine.get_user_profile(self.user_id)
            
            # Adapt personality based on user preferences
            if self.user_profile:
                if hasattr(self.user_profile, 'communication_style'):
                    self.personality.update(self.user_profile.communication_style)
            
            # Send greeting message
            greeting = await self._generate_greeting()
            self.conversation_history.append({
                "role": "assistant",
                "message": greeting,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            self.logger.error("Failed to initialize chatbot", error=str(e))
    
    async def process_message(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process user message and generate AI response"""
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "message": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Analyze message intent
            intent = await self._analyze_message_intent(user_message)
            
            # Generate contextual response
            response = await self._generate_response(user_message, intent, context)
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "message": response["message"],
                "timestamp": datetime.utcnow().isoformat(),
                "intent": intent,
                "metadata": response.get("metadata", {})
            })
            
            return {
                "success": True,
                "response": response["message"],
                "intent": intent,
                "suggestions": response.get("suggestions", []),
                "actions": response.get("actions", [])
            }
            
        except Exception as e:
            self.logger.error("Failed to process chatbot message", error=str(e))
            return {
                "success": False,
                "error": "Failed to process message",
                "response": "I'm sorry, I'm having trouble understanding right now. Could you try rephrasing?"
            }
    
    async def _generate_greeting(self) -> str:
        """Generate personalized greeting message"""
        user_name = self.user_profile.first_name if self.user_profile and hasattr(self.user_profile, 'first_name') else "there"
        
        greetings = [
            f"Hi {user_name}! I'm your personal newsletter assistant. How can I help you discover amazing content today?",
            f"Hello {user_name}! Ready to explore some personalized book recommendations and discussions?",
            f"Hey {user_name}! I'm here to chat about books, answer questions, and help you find your next great read!"
        ]
        
        # Pick greeting based on time of day and user preferences
        return greetings[0]  # Simplified for now
    
    async def _analyze_message_intent(self, message: str) -> str:
        """Analyze user message intent"""
        message_lower = message.lower()
        
        # Simple intent classification - in production use NLP models
        if any(word in message_lower for word in ["recommend", "suggestion", "book", "read"]):
            return "book_recommendation"
        elif any(word in message_lower for word in ["quiz", "test", "question"]):
            return "interactive_content"
        elif any(word in message_lower for word in ["help", "how", "what", "explain"]):
            return "help_request"
        elif any(word in message_lower for word in ["opinion", "think", "feel", "review"]):
            return "opinion_sharing"
        else:
            return "general_conversation"
    
    async def _generate_response(
        self,
        user_message: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate contextual AI response"""
        try:
            response_data = {
                "message": "",
                "suggestions": [],
                "actions": [],
                "metadata": {}
            }
            
            if intent == "book_recommendation":
                response_data = await self._handle_book_recommendation(user_message)
            
            elif intent == "interactive_content":
                response_data = await self._handle_interactive_content_request(user_message)
            
            elif intent == "help_request":
                response_data = await self._handle_help_request(user_message)
            
            elif intent == "opinion_sharing":
                response_data = await self._handle_opinion_sharing(user_message)
            
            else:
                response_data = await self._handle_general_conversation(user_message)
            
            return response_data
            
        except Exception as e:
            self.logger.error("Failed to generate response", error=str(e))
            return {
                "message": "I'm not sure how to respond to that. Could you ask me something else?",
                "suggestions": ["Tell me about your reading preferences", "Ask for book recommendations"],
                "actions": []
            }
    
    async def _handle_book_recommendation(self, message: str) -> Dict[str, Any]:
        """Handle book recommendation requests"""
        # Generate personalized recommendations
        if self.user_profile:
            # Use content curator to get recommendations
            recommendations = await self.content_curator.generate_personalized_content(
                self.user_id,
                {"content_type": "book_recommendations", "context": message}
            )
        else:
            recommendations = {"books": ["A great book to start with is 'The Alchemist' by Paulo Coelho"]}
        
        response_message = "Based on your preferences, here are some books I think you'll love:\n\n"
        for book in recommendations.get("books", [])[:3]:
            response_message += f"📚 {book}\n"
        
        return {
            "message": response_message,
            "suggestions": [
                "Tell me more about the first book",
                "I want something different",
                "Why did you choose these?"
            ],
            "actions": ["view_book_details", "get_more_recommendations"]
        }
    
    async def _handle_interactive_content_request(self, message: str) -> Dict[str, Any]:
        """Handle requests for interactive content"""
        return {
            "message": "I'd love to create a fun quiz for you! What topic would you like to explore? I can create quizzes about:\n\n📖 Book genres and recommendations\n🎭 Literary characters and plots\n🌟 Author trivia\n💭 Reading habits and preferences",
            "suggestions": [
                "Create a book genre quiz",
                "Test my knowledge of classic literature",
                "Quiz me on my reading preferences"
            ],
            "actions": ["create_quiz", "browse_existing_quizzes"]
        }
    
    async def _handle_help_request(self, message: str) -> Dict[str, Any]:
        """Handle help and information requests"""
        return {
            "message": "I'm here to help! Here's what I can do for you:\n\n🎯 Get personalized book recommendations\n📊 Create interactive quizzes and polls\n💬 Discuss books and reading topics\n📈 Track your reading progress\n🎮 Play book-related games\n\nWhat would you like to try?",
            "suggestions": [
                "Get book recommendations",
                "Take a reading quiz",
                "Discuss a book I'm reading"
            ],
            "actions": ["show_features", "start_onboarding"]
        }
    
    async def _handle_opinion_sharing(self, message: str) -> Dict[str, Any]:
        """Handle opinion sharing and discussion"""
        return {
            "message": "I love hearing your thoughts! That's really interesting. What specifically made you feel that way? I find that personal reactions to books often reveal a lot about our reading preferences and can help me suggest even better matches for you.",
            "suggestions": [
                "Tell me more about what you liked",
                "Find similar books",
                "Share with other readers"
            ],
            "actions": ["analyze_preferences", "find_similar_content"]
        }
    
    async def _handle_general_conversation(self, message: str) -> Dict[str, Any]:
        """Handle general conversation"""
        return {
            "message": "That's interesting! I'm always eager to chat about books and reading. Is there anything specific about literature or reading that you'd like to explore today?",
            "suggestions": [
                "Recommend me a book",
                "Let's take a reading quiz",
                "Tell me about new releases"
            ],
            "actions": ["suggest_activities", "continue_conversation"]
        }

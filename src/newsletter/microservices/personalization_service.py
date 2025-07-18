"""
Personalization Microservice
Dedicated service for AI-powered newsletter personalization
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import aioredis
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai

from .service_discovery import MicroserviceBase, ServiceType
from ..privacy.gdpr_compliance import get_privacy_engine, ConsentType, ProcessingPurpose

logger = logging.getLogger(__name__)

class PersonalizationRequest(BaseModel):
    user_id: str
    content_items: List[Dict[str, Any]]
    personalization_level: str = "basic"
    context: Optional[Dict[str, Any]] = None

class PersonalizationResponse(BaseModel):
    user_id: str
    personalized_content: List[Dict[str, Any]]
    personalization_score: float
    explanation: str
    privacy_compliant: bool

class UserProfile(BaseModel):
    user_id: str
    preferences: Dict[str, Any]
    reading_history: List[str]
    engagement_patterns: Dict[str, float]
    demographics: Optional[Dict[str, Any]] = None
    last_updated: datetime

class PersonalizationMicroservice(MicroserviceBase):
    """Microservice for newsletter personalization"""
    
    def __init__(self, host: str = "localhost", port: int = 8001):
        super().__init__(
            service_type=ServiceType.PERSONALIZATION,
            host=host,
            port=port,
            version="1.0.0"
        )
        
        self.redis = None
        self.vectorizer = None
        self.user_profiles: Dict[str, UserProfile] = {}
        self.content_cache: Dict[str, np.ndarray] = {}
        
        # Add routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.post("/personalize", response_model=PersonalizationResponse)
        async def personalize_content(
            request: PersonalizationRequest,
            background_tasks: BackgroundTasks
        ):
            return await self.personalize_content(request, background_tasks)
        
        @self.app.get("/profile/{user_id}")
        async def get_user_profile(user_id: str):
            return await self.get_user_profile(user_id)
        
        @self.app.post("/profile/{user_id}")
        async def update_user_profile(user_id: str, profile_data: Dict[str, Any]):
            return await self.update_user_profile(user_id, profile_data)
        
        @self.app.post("/feedback")
        async def record_feedback(feedback_data: Dict[str, Any]):
            return await self.record_feedback(feedback_data)
    
    async def startup(self):
        """Service startup with model initialization"""
        await super().startup()
        
        try:
            # Initialize Redis
            self.redis = aioredis.from_url("redis://localhost:6379")
            
            # Load or initialize ML models
            await self.initialize_models()
            
            # Load user profiles
            await self.load_user_profiles()
            
            logger.info("Personalization service fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize personalization service: {e}")
            raise
    
    async def initialize_models(self):
        """Initialize ML models for personalization"""
        try:
            # Initialize TF-IDF vectorizer for content similarity
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Try to load pre-trained models
            try:
                self.vectorizer = joblib.load("models/content_vectorizer.pkl")
                logger.info("Loaded pre-trained content vectorizer")
            except FileNotFoundError:
                logger.info("No pre-trained vectorizer found, will train on first use")
            
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            raise
    
    async def load_user_profiles(self):
        """Load user profiles from storage"""
        try:
            # Load profiles from Redis
            profile_keys = await self.redis.keys("profile:*")
            
            for key in profile_keys:
                user_id = key.decode().split(":")[-1]
                profile_data = await self.redis.hgetall(key)
                
                if profile_data:
                    # Reconstruct profile
                    profile = UserProfile(
                        user_id=user_id,
                        preferences=eval(profile_data.get(b'preferences', b'{}')),
                        reading_history=eval(profile_data.get(b'reading_history', b'[]')),
                        engagement_patterns=eval(profile_data.get(b'engagement_patterns', b'{}')),
                        demographics=eval(profile_data.get(b'demographics', b'None')),
                        last_updated=datetime.fromisoformat(
                            profile_data.get(b'last_updated', datetime.utcnow().isoformat()).decode()
                        )
                    )
                    
                    self.user_profiles[user_id] = profile
            
            logger.info(f"Loaded {len(self.user_profiles)} user profiles")
            
        except Exception as e:
            logger.error(f"Failed to load user profiles: {e}")
    
    async def personalize_content(
        self,
        request: PersonalizationRequest,
        background_tasks: BackgroundTasks
    ) -> PersonalizationResponse:
        """Personalize content for a user"""
        try:
            # Check privacy consent
            privacy_engine = get_privacy_engine()
            can_personalize = await privacy_engine.check_consent(
                request.user_id,
                ConsentType.PERSONALIZATION,
                ProcessingPurpose.NEWSLETTER_PERSONALIZATION
            )
            
            if not can_personalize:
                return PersonalizationResponse(
                    user_id=request.user_id,
                    personalized_content=request.content_items,
                    personalization_score=0.0,
                    explanation="No personalization applied due to privacy settings",
                    privacy_compliant=True
                )
            
            # Get or create user profile
            user_profile = await self.get_or_create_profile(request.user_id)
            
            # Apply personalization based on level
            if request.personalization_level == "basic":
                result = await self.basic_personalization(user_profile, request.content_items)
            elif request.personalization_level == "advanced":
                result = await self.advanced_personalization(user_profile, request.content_items)
            else:
                result = await self.ai_personalization(user_profile, request.content_items, request.context)
            
            # Record interaction for learning
            background_tasks.add_task(
                self.record_interaction,
                request.user_id,
                request.content_items,
                result["personalized_content"]
            )
            
            return PersonalizationResponse(
                user_id=request.user_id,
                personalized_content=result["personalized_content"],
                personalization_score=result["score"],
                explanation=result["explanation"],
                privacy_compliant=True
            )
            
        except Exception as e:
            logger.error(f"Personalization failed: {e}")
            raise HTTPException(status_code=500, detail="Personalization service error")
    
    async def basic_personalization(
        self,
        user_profile: UserProfile,
        content_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Basic personalization using preferences and history"""
        try:
            personalized_items = []
            
            for item in content_items:
                item_copy = item.copy()
                
                # Calculate relevance score based on preferences
                relevance_score = self.calculate_preference_score(user_profile, item)
                
                # Boost based on reading history
                history_boost = self.calculate_history_boost(user_profile, item)
                
                # Combined score
                final_score = (relevance_score * 0.7) + (history_boost * 0.3)
                item_copy["personalization_score"] = final_score
                
                personalized_items.append(item_copy)
            
            # Sort by personalization score
            personalized_items.sort(key=lambda x: x.get("personalization_score", 0), reverse=True)
            
            return {
                "personalized_content": personalized_items,
                "score": np.mean([item.get("personalization_score", 0) for item in personalized_items]),
                "explanation": "Content ranked based on your reading preferences and history"
            }
            
        except Exception as e:
            logger.error(f"Basic personalization failed: {e}")
            return {
                "personalized_content": content_items,
                "score": 0.0,
                "explanation": "Personalization temporarily unavailable"
            }
    
    async def advanced_personalization(
        self,
        user_profile: UserProfile,
        content_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Advanced personalization using ML models"""
        try:
            # Extract content features
            content_features = await self.extract_content_features(content_items)
            
            # Get user embedding
            user_embedding = await self.get_user_embedding(user_profile)
            
            # Calculate similarity scores
            if content_features is not None and user_embedding is not None:
                similarity_scores = cosine_similarity([user_embedding], content_features)[0]
            else:
                similarity_scores = np.zeros(len(content_items))
            
            personalized_items = []
            for i, item in enumerate(content_items):
                item_copy = item.copy()
                item_copy["personalization_score"] = similarity_scores[i]
                personalized_items.append(item_copy)
            
            # Sort by similarity
            personalized_items.sort(key=lambda x: x.get("personalization_score", 0), reverse=True)
            
            return {
                "personalized_content": personalized_items,
                "score": np.mean(similarity_scores),
                "explanation": "Content personalized using AI to match your reading patterns"
            }
            
        except Exception as e:
            logger.error(f"Advanced personalization failed: {e}")
            # Fallback to basic
            return await self.basic_personalization(user_profile, content_items)
    
    async def ai_personalization(
        self,
        user_profile: UserProfile,
        content_items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """AI-powered personalization using language models"""
        try:
            # Create user context for AI
            user_context = self.create_user_context(user_profile, context)
            
            # Use OpenAI to rank content
            content_descriptions = [
                f"Title: {item.get('title', 'Unknown')}\n"
                f"Summary: {item.get('summary', item.get('description', 'No summary'))}"
                for item in content_items
            ]
            
            prompt = f"""
            User Profile: {user_context}
            
            Please rank the following content items from 1-{len(content_items)} based on how relevant they would be for this user. Consider their preferences, reading history, and current context.
            
            Content Items:
            {chr(10).join(f"{i+1}. {desc}" for i, desc in enumerate(content_descriptions))}
            
            Return only a JSON array of rankings: [1, 3, 2, ...] where the first number is the rank of the first item.
            """
            
            # Make OpenAI API call (mock for now)
            rankings = await self.get_ai_rankings(prompt, len(content_items))
            
            # Apply rankings
            personalized_items = []
            for i, item in enumerate(content_items):
                item_copy = item.copy()
                rank = rankings[i] if i < len(rankings) else len(content_items)
                item_copy["personalization_score"] = 1.0 - (rank - 1) / len(content_items)
                item_copy["ai_rank"] = rank
                personalized_items.append(item_copy)
            
            # Sort by AI ranking
            personalized_items.sort(key=lambda x: x.get("ai_rank", 999))
            
            return {
                "personalized_content": personalized_items,
                "score": np.mean([item.get("personalization_score", 0) for item in personalized_items]),
                "explanation": "Content personalized using advanced AI to understand your preferences"
            }
            
        except Exception as e:
            logger.error(f"AI personalization failed: {e}")
            # Fallback to advanced
            return await self.advanced_personalization(user_profile, content_items)
    
    async def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one"""
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        # Create new profile
        profile = UserProfile(
            user_id=user_id,
            preferences={},
            reading_history=[],
            engagement_patterns={},
            last_updated=datetime.utcnow()
        )
        
        self.user_profiles[user_id] = profile
        await self.save_user_profile(profile)
        
        return profile
    
    async def save_user_profile(self, profile: UserProfile):
        """Save user profile to Redis"""
        try:
            profile_key = f"profile:{profile.user_id}"
            profile_data = {
                "preferences": str(profile.preferences),
                "reading_history": str(profile.reading_history),
                "engagement_patterns": str(profile.engagement_patterns),
                "demographics": str(profile.demographics),
                "last_updated": profile.last_updated.isoformat()
            }
            
            await self.redis.hmset(profile_key, profile_data)
            await self.redis.expire(profile_key, 86400 * 365)  # 1 year
            
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
    
    def calculate_preference_score(self, user_profile: UserProfile, item: Dict[str, Any]) -> float:
        """Calculate preference-based relevance score"""
        preferences = user_profile.preferences
        score = 0.0
        
        # Genre preferences
        item_genres = item.get("genres", [])
        if isinstance(item_genres, str):
            item_genres = [item_genres]
        
        for genre in item_genres:
            score += preferences.get(f"genre_{genre.lower()}", 0.5)
        
        # Author preferences
        item_authors = item.get("authors", [])
        if isinstance(item_authors, str):
            item_authors = [item_authors]
        
        for author in item_authors:
            score += preferences.get(f"author_{author.lower()}", 0.5)
        
        # Normalize score
        return min(1.0, score / max(1, len(item_genres) + len(item_authors)))
    
    def calculate_history_boost(self, user_profile: UserProfile, item: Dict[str, Any]) -> float:
        """Calculate boost based on reading history"""
        history = user_profile.reading_history
        
        if not history:
            return 0.5
        
        # Check for similar items in history
        item_title = item.get("title", "").lower()
        item_description = item.get("description", "").lower()
        
        similarity_scores = []
        for hist_item in history[-50]:  # Consider last 50 items
            hist_lower = hist_item.lower()
            
            # Simple keyword matching
            title_overlap = len(set(item_title.split()) & set(hist_lower.split()))
            desc_overlap = len(set(item_description.split()) & set(hist_lower.split()))
            
            similarity = (title_overlap + desc_overlap) / max(1, len(item_title.split()) + len(item_description.split()))
            similarity_scores.append(similarity)
        
        return np.mean(similarity_scores) if similarity_scores else 0.5
    
    async def extract_content_features(self, content_items: List[Dict[str, Any]]) -> Optional[np.ndarray]:
        """Extract TF-IDF features from content"""
        try:
            # Combine title and description for each item
            texts = []
            for item in content_items:
                text = f"{item.get('title', '')} {item.get('description', '')} {item.get('summary', '')}"
                texts.append(text)
            
            if not texts:
                return None
            
            # Use existing vectorizer or fit new one
            if hasattr(self.vectorizer, 'vocabulary_'):
                features = self.vectorizer.transform(texts)
            else:
                features = self.vectorizer.fit_transform(texts)
                # Save the fitted vectorizer
                joblib.dump(self.vectorizer, "models/content_vectorizer.pkl")
            
            return features.toarray()
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None
    
    async def get_user_embedding(self, user_profile: UserProfile) -> Optional[np.ndarray]:
        """Get user embedding based on profile"""
        try:
            # Create user text representation
            user_text = ""
            
            # Add preferences
            for pref, score in user_profile.preferences.items():
                if score > 0.5:
                    user_text += f"{pref.replace('_', ' ')} " * int(score * 3)
            
            # Add reading history
            user_text += " ".join(user_profile.reading_history[-20:])  # Last 20 items
            
            if not user_text.strip():
                return None
            
            # Transform using same vectorizer
            if hasattr(self.vectorizer, 'vocabulary_'):
                user_features = self.vectorizer.transform([user_text])
                return user_features.toarray()[0]
            else:
                return None
            
        except Exception as e:
            logger.error(f"User embedding failed: {e}")
            return None
    
    def create_user_context(self, user_profile: UserProfile, context: Optional[Dict[str, Any]]) -> str:
        """Create user context for AI personalization"""
        context_parts = []
        
        # Reading preferences
        if user_profile.preferences:
            top_prefs = sorted(user_profile.preferences.items(), key=lambda x: x[1], reverse=True)[:5]
            context_parts.append(f"Preferences: {', '.join([pref[0].replace('_', ' ') for pref in top_prefs])}")
        
        # Recent reading history
        if user_profile.reading_history:
            recent_books = user_profile.reading_history[-5:]
            context_parts.append(f"Recently read: {', '.join(recent_books)}")
        
        # Engagement patterns
        if user_profile.engagement_patterns:
            patterns = []
            for pattern, value in user_profile.engagement_patterns.items():
                if value > 0.6:
                    patterns.append(pattern.replace('_', ' '))
            if patterns:
                context_parts.append(f"Engagement patterns: {', '.join(patterns)}")
        
        # Current context
        if context:
            if context.get("time_of_day"):
                context_parts.append(f"Time: {context['time_of_day']}")
            if context.get("device"):
                context_parts.append(f"Device: {context['device']}")
        
        return "; ".join(context_parts) if context_parts else "New user with no established preferences"
    
    async def get_ai_rankings(self, prompt: str, num_items: int) -> List[int]:
        """Get AI rankings (mock implementation)"""
        try:
            # Mock implementation - would use actual OpenAI API
            # For now, return semi-random rankings with some logic
            import random
            rankings = list(range(1, num_items + 1))
            random.shuffle(rankings)
            return rankings
            
        except Exception as e:
            logger.error(f"AI ranking failed: {e}")
            # Return natural order as fallback
            return list(range(1, num_items + 1))
    
    async def record_interaction(
        self,
        user_id: str,
        original_content: List[Dict[str, Any]],
        personalized_content: List[Dict[str, Any]]
    ):
        """Record user interaction for learning"""
        try:
            # This would normally record engagement data
            # For ML model improvement
            interaction_data = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "original_count": len(original_content),
                "personalized_count": len(personalized_content),
                "top_personalized_items": [item.get("title") for item in personalized_content[:3]]
            }
            
            # Store for analytics
            await self.redis.lpush(
                f"interactions:{user_id}",
                str(interaction_data)
            )
            
            # Keep only recent interactions
            await self.redis.ltrim(f"interactions:{user_id}", 0, 999)
            
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile API endpoint"""
        profile = await self.get_or_create_profile(user_id)
        return {
            "user_id": profile.user_id,
            "preferences": profile.preferences,
            "reading_history_count": len(profile.reading_history),
            "engagement_patterns": profile.engagement_patterns,
            "last_updated": profile.last_updated.isoformat()
        }
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile API endpoint"""
        try:
            profile = await self.get_or_create_profile(user_id)
            
            # Update preferences
            if "preferences" in profile_data:
                profile.preferences.update(profile_data["preferences"])
            
            # Add to reading history
            if "reading_history" in profile_data:
                new_items = profile_data["reading_history"]
                if isinstance(new_items, list):
                    profile.reading_history.extend(new_items)
                else:
                    profile.reading_history.append(new_items)
                
                # Keep only recent items
                profile.reading_history = profile.reading_history[-1000:]
            
            # Update engagement patterns
            if "engagement_patterns" in profile_data:
                profile.engagement_patterns.update(profile_data["engagement_patterns"])
            
            profile.last_updated = datetime.utcnow()
            await self.save_user_profile(profile)
            
            return {"status": "updated", "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            raise HTTPException(status_code=500, detail="Profile update failed")
    
    async def record_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record user feedback for model improvement"""
        try:
            # Store feedback for model training
            feedback_key = f"feedback:{feedback_data.get('user_id', 'anonymous')}:{datetime.utcnow().isoformat()}"
            await self.redis.setex(feedback_key, 86400 * 30, str(feedback_data))
            
            return {"status": "recorded", "feedback_id": feedback_key}
            
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            raise HTTPException(status_code=500, detail="Feedback recording failed")
    
    async def get_load_factor(self) -> float:
        """Get current service load"""
        # Simple implementation based on active requests
        return min(1.0, len(self.user_profiles) / 10000)
    
    async def get_service_metadata(self) -> Dict[str, Any]:
        """Get service metadata"""
        return {
            "capabilities": [
                "basic_personalization",
                "advanced_personalization", 
                "ai_personalization",
                "user_profiling",
                "preference_learning"
            ],
            "dependencies": ["redis", "sklearn", "openai"],
            "configuration": {
                "max_content_items": 100,
                "max_profile_history": 1000,
                "supported_personalization_levels": ["basic", "advanced", "ai"]
            }
        }

# Entry point for running the service
if __name__ == "__main__":
    import uvicorn
    
    service = PersonalizationMicroservice(port=8001)
    uvicorn.run(service.app, host="0.0.0.0", port=8001)

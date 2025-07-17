"""
Optimized Personalization Engine with CNN-GRU Architecture
Hybrid user modeling combining short-term behavior with explicit preferences
COT: Hybrid user modeling is essential—combine short-term behavior with explicit preferences
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# Try to import deep learning frameworks, fallback if not available
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from src.core.logging import StructuredLogger
from src.news.core.intelligence_engine import NewsArticle

logger = StructuredLogger(__name__)


class ReadingStyle(Enum):
    """User reading style preferences"""
    SKIM = "skim"           # Quick headlines and summaries
    DEEP_READ = "deep_read" # Full articles and detailed analysis
    THEMATIC_DIVE = "thematic_dive"  # Focus on specific themes


@dataclass
class UserReadingProfile:
    """Comprehensive user reading profile"""
    
    user_id: str
    reading_style: ReadingStyle
    explicit_interests: Dict[str, float]  # User-declared interests
    implicit_interests: Dict[str, float]  # Learned from behavior
    reading_time_preference: int          # Minutes per session
    
    # Behavioral patterns
    article_completion_rate: float        # How often user finishes articles
    interaction_patterns: Dict[str, float] # Click, share, save rates
    time_of_day_preferences: List[int]    # Preferred reading hours
    
    # Diversity preferences
    perspective_openness: float           # Openness to diverse viewpoints
    source_diversity_preference: float    # Preference for varied sources
    
    # Learning preferences
    complexity_tolerance: float           # Tolerance for complex content
    fact_verification_importance: float   # Importance of fact-checking
    
    # Temporal patterns
    short_term_interests: Dict[str, float]  # Recent 7 days
    medium_term_interests: Dict[str, float] # Recent 30 days
    long_term_interests: Dict[str, float]   # Historical patterns


@dataclass
class PersonalizationContext:
    """Context for personalization decision making"""
    
    current_session_time: int            # Minutes in current session
    recent_articles_read: List[str]      # Recent article IDs
    current_mood_indicators: Dict[str, float]  # Inferred mood/interests
    time_of_day: int                     # Current hour
    day_of_week: int                     # Current day (0-6)
    
    # Real-time context
    breaking_news_preference: float      # Interest in breaking news
    in_depth_analysis_mode: bool         # Currently in analysis mode
    quick_scan_mode: bool                # Currently scanning quickly


class CNNGRUPersonalizationModel:
    """
    COT: CNN-GRU hybrid model for news personalization (NP-3C-FIP style)
    
    Research Integration: Neural personalization architectures
    - CNN for content feature extraction
    - GRU for temporal sequence modeling
    - Attention mechanism for importance weighting
    - Hybrid explicit/implicit preference fusion
    """

    def __init__(self, embedding_dim: int = 128, hidden_dim: int = 64):
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.model = None
        
        if TORCH_AVAILABLE:
            self.model = self._build_cnn_gru_model()
        
        # Fallback to traditional ML if PyTorch not available
        self.fallback_weights = {
            'explicit_weight': 0.4,
            'implicit_weight': 0.3,
            'temporal_weight': 0.2,
            'context_weight': 0.1
        }

    def _build_cnn_gru_model(self):
        """Build CNN-GRU architecture for personalization"""
        if not TORCH_AVAILABLE:
            return None
            
        class NewsPersonalizationNet(nn.Module):
            def __init__(self, embedding_dim, hidden_dim):
                super().__init__()
                
                # CNN for content feature extraction
                self.content_cnn = nn.Sequential(
                    nn.Conv1d(embedding_dim, 64, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.MaxPool1d(2),
                    nn.Conv1d(64, 32, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.AdaptiveAvgPool1d(1)
                )
                
                # GRU for temporal modeling
                self.temporal_gru = nn.GRU(
                    input_size=32,
                    hidden_size=hidden_dim,
                    num_layers=2,
                    batch_first=True,
                    dropout=0.2
                )
                
                # Attention mechanism
                self.attention = nn.MultiheadAttention(
                    embed_dim=hidden_dim,
                    num_heads=4,
                    batch_first=True
                )
                
                # Preference fusion layers
                self.explicit_encoder = nn.Linear(50, hidden_dim)  # 50 interest categories
                self.implicit_encoder = nn.Linear(50, hidden_dim)
                self.context_encoder = nn.Linear(10, hidden_dim)   # 10 context features
                
                # Final prediction layers
                self.fusion_layer = nn.Linear(hidden_dim * 4, hidden_dim)
                self.output_layer = nn.Linear(hidden_dim, 1)
                self.dropout = nn.Dropout(0.3)
                
            def forward(self, content_features, temporal_sequence, explicit_prefs, 
                       implicit_prefs, context_features):
                # Content CNN processing
                content_out = self.content_cnn(content_features)
                content_out = content_out.squeeze(-1)
                
                # Temporal GRU processing
                temporal_out, _ = self.temporal_gru(temporal_sequence)
                temporal_out = temporal_out[:, -1, :]  # Last hidden state
                
                # Attention over temporal features
                attended_temporal, _ = self.attention(
                    temporal_out.unsqueeze(1), 
                    temporal_out.unsqueeze(1), 
                    temporal_out.unsqueeze(1)
                )
                attended_temporal = attended_temporal.squeeze(1)
                
                # Preference encoding
                explicit_encoded = self.explicit_encoder(explicit_prefs)
                implicit_encoded = self.implicit_encoder(implicit_prefs)
                context_encoded = self.context_encoder(context_features)
                
                # Feature fusion
                fused_features = torch.cat([
                    content_out, attended_temporal, 
                    explicit_encoded, implicit_encoded, context_encoded
                ], dim=-1)
                
                # Final prediction
                fused = self.fusion_layer(fused_features)
                fused = F.relu(fused)
                fused = self.dropout(fused)
                
                output = self.output_layer(fused)
                return torch.sigmoid(output)
        
        return NewsPersonalizationNet(self.embedding_dim, self.hidden_dim)


class OptimizedPersonalizationEngine:
    """
    COT: Advanced personalization with hybrid user modeling
    
    Features:
    - CNN-GRU neural architecture for deep personalization
    - Explicit + implicit preference fusion
    - Real-time context awareness
    - Reading style adaptation
    - Diversity optimization
    """

    def __init__(self):
        self.cnn_gru_model = CNNGRUPersonalizationModel()
        self.user_profiles = {}  # Cache for user profiles
        
        # Personalization parameters
        self.diversity_injection_rate = 0.15
        self.novelty_boost_factor = 1.2
        self.recency_decay_factor = 0.95
        self.context_adaptation_rate = 0.3
        
        # Interest categories (simplified taxonomy)
        self.interest_categories = [
            "politics", "technology", "science", "health", "business", "sports",
            "entertainment", "world_news", "local_news", "environment", "education",
            "finance", "lifestyle", "travel", "food", "culture", "opinion", "crime",
            "weather", "military", "space", "energy", "transportation", "housing",
            "employment", "social_issues", "religion", "arts", "gaming", "automotive",
            "fashion", "parenting", "pets", "gardening", "cooking", "music", "movies",
            "books", "photography", "fitness", "meditation", "investing", "startups",
            "ai_ml", "cybersecurity", "blockchain", "climate", "psychology", "history"
        ]

    async def generate_personalized_recommendations(
        self,
        user_id: str,
        candidate_articles: List[NewsArticle],
        context: PersonalizationContext,
        max_recommendations: int = 20
    ) -> List[Dict[str, Any]]:
        """
        COT: Generate personalized recommendations using hybrid model
        
        Process:
        1. Load/build user profile
        2. Extract article features
        3. Apply CNN-GRU model or fallback
        4. Inject diversity and novelty
        5. Adapt to reading style and context
        """
        try:
            # Stage 1: User Profile
            user_profile = await self._get_or_build_user_profile(user_id)
            
            # Stage 2: Feature Extraction
            article_features = await self._extract_article_features(candidate_articles)
            
            # Stage 3: Personalization Scoring
            if self.cnn_gru_model.model is not None and TORCH_AVAILABLE:
                scores = await self._score_with_neural_model(
                    user_profile, article_features, context
                )
            else:
                scores = await self._score_with_fallback_model(
                    user_profile, article_features, context
                )
            
            # Stage 4: Diversity and Novelty Injection
            enhanced_scores = await self._inject_diversity_and_novelty(
                candidate_articles, scores, user_profile
            )
            
            # Stage 5: Reading Style Adaptation
            adapted_recommendations = await self._adapt_to_reading_style(
                candidate_articles, enhanced_scores, user_profile, context
            )
            
            # Stage 6: Final Ranking and Selection
            final_recommendations = self._rank_and_select_final(
                adapted_recommendations, max_recommendations
            )

            logger.info(
                "Personalized recommendations generated",
                user_id=user_id,
                candidate_count=len(candidate_articles),
                recommendation_count=len(final_recommendations)
            )

            return final_recommendations

        except Exception as e:
            logger.error("Personalization failed", user_id=user_id, error=str(e))
            # Fallback to basic ranking
            return [
                {
                    "article": article,
                    "score": article.credibility_score,
                    "explanation": "Fallback ranking by credibility"
                }
                for article in candidate_articles[:max_recommendations]
            ]

    async def _get_or_build_user_profile(self, user_id: str) -> UserReadingProfile:
        """
        COT: Build comprehensive user profile from historical data
        Combine explicit preferences with learned behavioral patterns
        """
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            # Update with recent activity
            await self._update_profile_with_recent_activity(profile)
            return profile
        
        # Build new profile
        profile = UserReadingProfile(
            user_id=user_id,
            reading_style=ReadingStyle.SKIM,  # Default
            explicit_interests={},
            implicit_interests={},
            reading_time_preference=10,  # 10 minutes default
            article_completion_rate=0.6,
            interaction_patterns={
                "click_rate": 0.3,
                "share_rate": 0.1,
                "save_rate": 0.05,
                "comment_rate": 0.02
            },
            time_of_day_preferences=[8, 12, 18, 21],  # Morning, lunch, evening, night
            perspective_openness=0.7,
            source_diversity_preference=0.6,
            complexity_tolerance=0.5,
            fact_verification_importance=0.8,
            short_term_interests={},
            medium_term_interests={},
            long_term_interests={}
        )
        
        # Load from database or user preferences
        await self._load_user_preferences(profile)
        
        # Learn from historical behavior
        await self._learn_implicit_preferences(profile)
        
        self.user_profiles[user_id] = profile
        return profile

    async def _extract_article_features(
        self, 
        articles: List[NewsArticle]
    ) -> Dict[str, np.ndarray]:
        """
        COT: Extract features for neural model processing
        Create embeddings and structured features
        """
        features = {
            "content_embeddings": [],
            "temporal_features": [],
            "credibility_features": [],
            "topic_features": []
        }
        
        for article in articles:
            # Content embedding (simplified - would use actual embeddings)
            content_embedding = self._create_content_embedding(article)
            features["content_embeddings"].append(content_embedding)
            
            # Temporal features
            hours_since_published = (datetime.now() - article.published_at).total_seconds() / 3600
            temporal_feature = [
                hours_since_published,
                article.published_at.hour,
                article.published_at.weekday(),
                1.0 if hours_since_published <= 1 else 0.0  # Breaking news indicator
            ]
            features["temporal_features"].append(temporal_feature)
            
            # Credibility features
            credibility_feature = [
                article.credibility_score,
                1.0 if article.bias_rating == "center" else 0.0,
                article.reading_time_minutes / 10.0  # Normalized reading time
            ]
            features["credibility_features"].append(credibility_feature)
            
            # Topic features (one-hot encoding)
            topic_feature = self._create_topic_embedding(article)
            features["topic_features"].append(topic_feature)
        
        # Convert to numpy arrays
        for key in features:
            features[key] = np.array(features[key])
        
        return features

    async def _score_with_neural_model(
        self,
        user_profile: UserReadingProfile,
        article_features: Dict[str, np.ndarray],
        context: PersonalizationContext
    ) -> List[float]:
        """
        COT: Score articles using CNN-GRU neural model
        Process features through neural architecture
        """
        if not TORCH_AVAILABLE or self.cnn_gru_model.model is None:
            return await self._score_with_fallback_model(user_profile, article_features, context)
        
        try:
            model = self.cnn_gru_model.model
            model.eval()
            
            # Prepare model inputs
            batch_size = len(article_features["content_embeddings"])
            
            # Content features
            content_features = torch.FloatTensor(article_features["content_embeddings"])
            content_features = content_features.transpose(1, 2)  # For CNN
            
            # Temporal sequence (use recent temporal patterns)
            temporal_sequence = torch.FloatTensor(article_features["temporal_features"])
            temporal_sequence = temporal_sequence.unsqueeze(0).expand(batch_size, -1, -1)
            
            # User preference vectors
            explicit_prefs = self._encode_user_interests(user_profile.explicit_interests)
            implicit_prefs = self._encode_user_interests(user_profile.implicit_interests)
            
            explicit_tensor = torch.FloatTensor(explicit_prefs).expand(batch_size, -1)
            implicit_tensor = torch.FloatTensor(implicit_prefs).expand(batch_size, -1)
            
            # Context features
            context_features = self._encode_context(context)
            context_tensor = torch.FloatTensor(context_features).expand(batch_size, -1)
            
            # Forward pass
            with torch.no_grad():
                scores = model(
                    content_features,
                    temporal_sequence,
                    explicit_tensor,
                    implicit_tensor,
                    context_tensor
                )
            
            return scores.squeeze().tolist()
            
        except Exception as e:
            logger.warning("Neural model scoring failed, using fallback", error=str(e))
            return await self._score_with_fallback_model(user_profile, article_features, context)

    async def _score_with_fallback_model(
        self,
        user_profile: UserReadingProfile,
        article_features: Dict[str, np.ndarray],
        context: PersonalizationContext
    ) -> List[float]:
        """
        COT: Fallback scoring using traditional ML approaches
        Linear combination of feature scores
        """
        scores = []
        weights = self.cnn_gru_model.fallback_weights
        
        for i, topic_features in enumerate(article_features["topic_features"]):
            # Explicit interest score
            explicit_score = self._calculate_interest_alignment(
                topic_features, user_profile.explicit_interests
            )
            
            # Implicit interest score
            implicit_score = self._calculate_interest_alignment(
                topic_features, user_profile.implicit_interests
            )
            
            # Temporal score (recency and timing)
            temporal_score = self._calculate_temporal_score(
                article_features["temporal_features"][i], user_profile, context
            )
            
            # Context score
            context_score = self._calculate_context_score(
                article_features["credibility_features"][i], user_profile, context
            )
            
            # Weighted combination
            final_score = (
                explicit_score * weights['explicit_weight'] +
                implicit_score * weights['implicit_weight'] +
                temporal_score * weights['temporal_weight'] +
                context_score * weights['context_weight']
            )
            
            scores.append(final_score)
        
        return scores

    async def _inject_diversity_and_novelty(
        self,
        articles: List[NewsArticle],
        scores: List[float],
        user_profile: UserReadingProfile
    ) -> List[float]:
        """
        COT: Inject diversity and novelty to prevent echo chambers
        Boost underrepresented perspectives and novel content
        """
        enhanced_scores = scores.copy()
        
        # Diversity injection
        diversity_boost = self.diversity_injection_rate
        topic_coverage = {}
        
        for i, article in enumerate(articles):
            # Track topic coverage
            for topic in article.topics:
                if topic not in topic_coverage:
                    topic_coverage[topic] = 0
                topic_coverage[topic] += 1
        
        # Boost underrepresented topics
        for i, article in enumerate(articles):
            article_topics = set(article.topics)
            
            # Find underrepresented topics
            underrepresented = [
                topic for topic in article_topics
                if topic_coverage.get(topic, 0) <= 2
            ]
            
            if underrepresented:
                diversity_bonus = diversity_boost * len(underrepresented) / len(article_topics)
                enhanced_scores[i] += diversity_bonus
        
        # Novelty boost
        for i, article in enumerate(articles):
            # Check if content is novel (not recently seen)
            is_novel = self._is_content_novel(article, user_profile)
            if is_novel:
                enhanced_scores[i] *= self.novelty_boost_factor
        
        return enhanced_scores

    async def _adapt_to_reading_style(
        self,
        articles: List[NewsArticle],
        scores: List[float],
        user_profile: UserReadingProfile,
        context: PersonalizationContext
    ) -> List[Dict[str, Any]]:
        """
        COT: Adapt recommendations to user's reading style
        Adjust content selection and presentation based on style
        """
        adapted_recommendations = []
        
        for i, (article, score) in enumerate(zip(articles, scores)):
            recommendation = {
                "article": article,
                "base_score": score,
                "adapted_score": score,
                "explanation": "",
                "reading_style_match": 0.0
            }
            
            # Adapt based on reading style
            if user_profile.reading_style == ReadingStyle.SKIM:
                # Prefer shorter articles and summaries
                if article.reading_time_minutes <= 3:
                    recommendation["adapted_score"] *= 1.3
                    recommendation["reading_style_match"] = 0.9
                    recommendation["explanation"] = "Quick read matching your skim style"
                elif article.reading_time_minutes > 10:
                    recommendation["adapted_score"] *= 0.7
                    recommendation["reading_style_match"] = 0.3
            
            elif user_profile.reading_style == ReadingStyle.DEEP_READ:
                # Prefer longer, detailed articles
                if article.reading_time_minutes >= 8:
                    recommendation["adapted_score"] *= 1.4
                    recommendation["reading_style_match"] = 0.9
                    recommendation["explanation"] = "In-depth article for detailed reading"
                elif article.reading_time_minutes < 3:
                    recommendation["adapted_score"] *= 0.8
                    recommendation["reading_style_match"] = 0.4
            
            elif user_profile.reading_style == ReadingStyle.THEMATIC_DIVE:
                # Prefer articles that match current thematic interests
                current_themes = set(user_profile.short_term_interests.keys())
                article_themes = set(article.topics)
                
                theme_overlap = len(current_themes & article_themes)
                if theme_overlap > 0:
                    theme_boost = 1.0 + (theme_overlap * 0.3)
                    recommendation["adapted_score"] *= theme_boost
                    recommendation["reading_style_match"] = min(1.0, theme_overlap / 3.0)
                    recommendation["explanation"] = f"Matches your current focus on {', '.join(list(current_themes & article_themes)[:2])}"
            
            # Context adaptations
            if context.quick_scan_mode and article.reading_time_minutes > 5:
                recommendation["adapted_score"] *= 0.6
            elif context.in_depth_analysis_mode and article.reading_time_minutes < 5:
                recommendation["adapted_score"] *= 0.8
            
            adapted_recommendations.append(recommendation)
        
        return adapted_recommendations

    def _rank_and_select_final(
        self,
        recommendations: List[Dict[str, Any]],
        max_count: int
    ) -> List[Dict[str, Any]]:
        """
        COT: Final ranking and selection of recommendations
        Apply final sorting and ensure quality thresholds
        """
        # Sort by adapted score
        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: x["adapted_score"],
            reverse=True
        )
        
        # Apply quality filters
        quality_filtered = [
            rec for rec in sorted_recommendations
            if rec["article"].credibility_score >= 0.6  # Minimum credibility
        ]
        
        # Ensure diversity in final selection
        final_selection = []
        used_topics = set()
        
        for rec in quality_filtered:
            article_topics = set(rec["article"].topics)
            
            # Check topic diversity
            if len(final_selection) < max_count // 2:
                # First half: prioritize score
                final_selection.append(rec)
            else:
                # Second half: ensure topic diversity
                if not (article_topics & used_topics) or len(final_selection) < max_count:
                    final_selection.append(rec)
            
            used_topics.update(article_topics)
            
            if len(final_selection) >= max_count:
                break
        
        return final_selection

    def _create_content_embedding(self, article: NewsArticle) -> np.ndarray:
        """Create simple content embedding (would use actual embeddings in production)"""
        # Simplified: create embedding based on content features
        features = []
        
        # Length features
        features.append(len(article.title.split()) / 20.0)  # Normalized title length
        features.append(len(article.content.split()) / 1000.0)  # Normalized content length
        
        # Content type indicators
        features.append(1.0 if "breaking" in article.title.lower() else 0.0)
        features.append(1.0 if "analysis" in article.title.lower() else 0.0)
        features.append(1.0 if "opinion" in article.title.lower() else 0.0)
        
        # Pad to embedding dimension
        while len(features) < self.cnn_gru_model.embedding_dim:
            features.append(0.0)
        
        return np.array(features[:self.cnn_gru_model.embedding_dim])

    def _create_topic_embedding(self, article: NewsArticle) -> np.ndarray:
        """Create topic one-hot embedding"""
        embedding = np.zeros(len(self.interest_categories))
        
        for i, category in enumerate(self.interest_categories):
            if category in article.topics:
                embedding[i] = 1.0
        
        return embedding

    def _encode_user_interests(self, interests: Dict[str, float]) -> np.ndarray:
        """Encode user interests as feature vector"""
        encoding = np.zeros(len(self.interest_categories))
        
        for i, category in enumerate(self.interest_categories):
            if category in interests:
                encoding[i] = interests[category]
        
        return encoding

    def _encode_context(self, context: PersonalizationContext) -> np.ndarray:
        """Encode context as feature vector"""
        features = [
            context.current_session_time / 60.0,  # Normalized session time
            context.time_of_day / 24.0,           # Normalized hour
            context.day_of_week / 7.0,            # Normalized day
            1.0 if context.quick_scan_mode else 0.0,
            1.0 if context.in_depth_analysis_mode else 0.0,
            context.breaking_news_preference,
            len(context.recent_articles_read) / 10.0,  # Normalized recent activity
            float(context.time_of_day in [8, 12, 18, 21]),  # Peak reading time
            0.0, 0.0  # Padding
        ]
        
        return np.array(features)

    def _calculate_interest_alignment(
        self, 
        topic_features: np.ndarray, 
        user_interests: Dict[str, float]
    ) -> float:
        """Calculate alignment between article topics and user interests"""
        if not user_interests:
            return 0.5  # Neutral score
        
        interest_vector = self._encode_user_interests(user_interests)
        alignment = np.dot(topic_features, interest_vector)
        
        # Normalize by magnitude
        if np.linalg.norm(interest_vector) > 0:
            alignment /= np.linalg.norm(interest_vector)
        
        return min(1.0, max(0.0, alignment))

    def _calculate_temporal_score(
        self, 
        temporal_features: np.ndarray, 
        user_profile: UserReadingProfile,
        context: PersonalizationContext
    ) -> float:
        """Calculate temporal relevance score"""
        hours_since_published = temporal_features[0]
        article_hour = int(temporal_features[1])
        
        # Recency score (decay over time)
        recency_score = self.recency_decay_factor ** (hours_since_published / 24.0)
        
        # Time preference score
        time_pref_score = 1.0 if article_hour in user_profile.time_of_day_preferences else 0.5
        
        # Breaking news boost
        breaking_score = temporal_features[3]  # Breaking news indicator
        
        return (recency_score * 0.5 + time_pref_score * 0.3 + breaking_score * 0.2)

    def _calculate_context_score(
        self,
        credibility_features: np.ndarray,
        user_profile: UserReadingProfile,
        context: PersonalizationContext
    ) -> float:
        """Calculate context-based relevance score"""
        credibility_score = credibility_features[0]
        is_unbiased = credibility_features[1]
        reading_time = credibility_features[2]
        
        # Credibility alignment
        credibility_weight = user_profile.fact_verification_importance
        credibility_component = credibility_score * credibility_weight
        
        # Bias preference
        bias_component = is_unbiased * user_profile.source_diversity_preference
        
        # Reading time alignment
        time_alignment = 1.0
        if context.quick_scan_mode and reading_time > 0.5:  # >5 minutes
            time_alignment = 0.6
        elif context.in_depth_analysis_mode and reading_time < 0.3:  # <3 minutes
            time_alignment = 0.7
        
        return credibility_component * 0.5 + bias_component * 0.3 + time_alignment * 0.2

    def _is_content_novel(self, article: NewsArticle, user_profile: UserReadingProfile) -> bool:
        """Check if content is novel for the user"""
        # Simple novelty check based on topics
        article_topics = set(article.topics)
        recent_topics = set(user_profile.short_term_interests.keys())
        
        # Novel if has topics not recently seen
        novel_topics = article_topics - recent_topics
        return len(novel_topics) > 0

    async def _load_user_preferences(self, profile: UserReadingProfile):
        """Load explicit user preferences from database/settings"""
        # In production, this would load from user settings database
        # For now, use defaults with some example preferences
        
        profile.explicit_interests = {
            "technology": 0.8,
            "science": 0.7,
            "politics": 0.3,
            "sports": 0.2
        }
        
        profile.reading_style = ReadingStyle.DEEP_READ  # Example preference

    async def _learn_implicit_preferences(self, profile: UserReadingProfile):
        """Learn implicit preferences from user behavior"""
        # In production, this would analyze click history, reading time, etc.
        # For now, create some example implicit preferences
        
        profile.implicit_interests = {
            "ai_ml": 0.9,      # High engagement with AI content
            "startups": 0.6,   # Moderate engagement with startup news
            "climate": 0.8     # High engagement with climate content
        }

    async def _update_profile_with_recent_activity(self, profile: UserReadingProfile):
        """Update profile with recent user activity"""
        # In production, this would update based on recent clicks, reads, etc.
        # For now, simulate some updates
        
        current_time = datetime.now()
        
        # Update short-term interests (last 7 days)
        profile.short_term_interests = {
            "technology": 0.9,
            "business": 0.6,
            "health": 0.4
        }
        
        logger.debug("Updated user profile with recent activity", user_id=profile.user_id)


# Reading Style UI Integration
READING_STYLE_SELECTOR_TEMPLATE = """
<div class="reading-style-selector">
    <h4>📖 Reading Style</h4>
    <div class="style-options">
        <button class="style-option {skim_active}" data-style="skim">
            <span class="style-icon">⚡</span>
            <span class="style-name">Skim</span>
            <span class="style-desc">Quick headlines & summaries</span>
        </button>
        
        <button class="style-option {deep_active}" data-style="deep_read">
            <span class="style-icon">🔍</span>
            <span class="style-name">Deep Read</span>
            <span class="style-desc">Full articles & analysis</span>
        </button>
        
        <button class="style-option {thematic_active}" data-style="thematic_dive">
            <span class="style-icon">🎯</span>
            <span class="style-name">Thematic Dive</span>
            <span class="style-desc">Focus on specific themes</span>
        </button>
    </div>
    
    <div class="personalization-insights">
        <h5>🧠 Your Reading Patterns</h5>
        <div class="insight-item">
            <span class="insight-label">Completion Rate:</span>
            <span class="insight-value">{completion_rate:.0%}</span>
        </div>
        <div class="insight-item">
            <span class="insight-label">Avg. Session:</span>
            <span class="insight-value">{avg_session_time} min</span>
        </div>
        <div class="insight-item">
            <span class="insight-label">Diversity Score:</span>
            <span class="insight-value">{diversity_score:.0%}</span>
        </div>
    </div>
</div>
"""

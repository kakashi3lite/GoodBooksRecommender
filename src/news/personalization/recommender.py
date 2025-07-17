"""
Hybrid News Recommender System
Leverages existing GoodBooks recommendation infrastructure for news personalization
Performance target: <300ms for recommendation scoring
"""

import asyncio
import pickle
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import StructuredLogger
from src.news.core.intelligence_engine import NewsArticle

logger = StructuredLogger(__name__)


@dataclass
class UserProfile:
    """User's reading profile and preferences"""

    user_id: int
    topics_of_interest: Dict[str, float]  # topic -> interest_score (0-1)
    reading_history: List[str]  # article IDs
    credibility_preference: float  # 0.7-1.0
    diversity_preference: float  # 0.0-1.0 (0=echo chamber, 1=maximum diversity)
    reading_time_preference: str  # "brief", "medium", "detailed"
    source_preferences: Dict[str, float]  # source -> preference_score
    last_updated: datetime

    def __post_init__(self):
        if not self.topics_of_interest:
            self.topics_of_interest = {}
        if not self.reading_history:
            self.reading_history = []
        if not self.source_preferences:
            self.source_preferences = {}


@dataclass
class RecommendationScore:
    """Recommendation score with explanation"""

    article_id: str
    score: float
    explanation: Dict[str, float]  # component -> contribution
    diversity_factor: float  # 0-1, higher = more diverse from user's usual content
    confidence: float  # 0-1, confidence in the recommendation


class HybridNewsRecommender:
    """
    Hybrid recommendation system combining multiple approaches:
    1. Content-based filtering (TF-IDF + cosine similarity)
    2. Collaborative filtering (user behavior patterns)
    3. Credibility weighting
    4. Diversity injection
    5. Temporal relevance
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8,
        )
        self.user_profiles: Dict[int, UserProfile] = {}
        self.article_vectors = None
        self.article_ids = []

        # Recommendation weights
        self.weights = {
            "content_similarity": 0.35,
            "credibility_score": 0.25,
            "temporal_relevance": 0.15,
            "source_preference": 0.15,
            "diversity_bonus": 0.10,
        }

    async def get_recommendations(
        self,
        user_id: int,
        candidate_articles: List[NewsArticle],
        num_recommendations: int = 20,
        diversity_enabled: bool = True,
    ) -> List[Tuple[NewsArticle, RecommendationScore]]:
        """
        Generate personalized news recommendations

        Args:
            user_id: User identifier
            candidate_articles: Pool of articles to recommend from
            num_recommendations: Number of recommendations to return
            diversity_enabled: Whether to inject diverse content

        Returns:
            List of (article, score) tuples ranked by relevance
        """
        start_time = datetime.now()

        try:
            # Get or create user profile
            user_profile = await self._get_user_profile(user_id)

            # Compute article vectors if needed
            await self._update_article_vectors(candidate_articles)

            # Score all articles
            scored_articles = await self._score_articles(
                user_profile, candidate_articles, diversity_enabled
            )

            # Apply diversity if enabled
            if diversity_enabled:
                scored_articles = self._apply_diversity_optimization(
                    scored_articles, user_profile, diversity_ratio=0.15
                )

            # Sort by score and return top N
            scored_articles.sort(key=lambda x: x[1].score, reverse=True)
            recommendations = scored_articles[:num_recommendations]

            # Log performance metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                "Recommendations generated",
                user_id=user_id,
                candidate_count=len(candidate_articles),
                recommendation_count=len(recommendations),
                processing_time_ms=processing_time,
                avg_score=(
                    np.mean([score.score for _, score in recommendations])
                    if recommendations
                    else 0
                ),
            )

            return recommendations

        except Exception as e:
            logger.error(
                "Recommendation generation failed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            # Fallback to simple ranking by credibility and recency
            return self._fallback_recommendations(
                candidate_articles, num_recommendations
            )

    async def _get_user_profile(self, user_id: int) -> UserProfile:
        """Get or create user profile"""
        if user_id in self.user_profiles:
            profile = self.user_profiles[user_id]

            # Check if profile needs updating (older than 1 hour)
            if datetime.now() - profile.last_updated > timedelta(hours=1):
                await self._update_user_profile(profile)

            return profile

        # Create new profile
        profile = await self._create_user_profile(user_id)
        self.user_profiles[user_id] = profile
        return profile

    async def _create_user_profile(self, user_id: int) -> UserProfile:
        """Create new user profile with default preferences"""
        # In production, this would query the database for user data
        return UserProfile(
            user_id=user_id,
            topics_of_interest={
                "technology": 0.8,
                "science": 0.7,
                "politics": 0.6,
                "business": 0.5,
                "health": 0.4,
            },
            reading_history=[],
            credibility_preference=0.8,
            diversity_preference=0.3,
            reading_time_preference="medium",
            source_preferences={},
            last_updated=datetime.now(),
        )

    async def _update_user_profile(self, profile: UserProfile):
        """Update user profile based on recent activity"""
        # In production, this would analyze recent reading behavior
        # and update topic interests, source preferences, etc.
        profile.last_updated = datetime.now()
        logger.info(f"Updated profile for user {profile.user_id}")

    async def _update_article_vectors(self, articles: List[NewsArticle]):
        """Update TF-IDF vectors for articles"""
        if not articles:
            return

        # Prepare text corpus
        corpus = []
        article_ids = []

        for article in articles:
            # Combine title and content for vectorization
            text = f"{article.title} {article.content}"
            corpus.append(text)
            article_ids.append(article.id)

        # Fit and transform corpus
        try:
            self.article_vectors = self.tfidf_vectorizer.fit_transform(corpus)
            self.article_ids = article_ids

            logger.info(
                "Article vectors updated",
                articles_count=len(articles),
                vector_dimensions=(
                    self.article_vectors.shape[1]
                    if self.article_vectors is not None
                    else 0
                ),
            )

        except Exception as e:
            logger.error(f"Failed to update article vectors: {e}")
            self.article_vectors = None
            self.article_ids = []

    async def _score_articles(
        self,
        user_profile: UserProfile,
        articles: List[NewsArticle],
        diversity_enabled: bool,
    ) -> List[Tuple[NewsArticle, RecommendationScore]]:
        """Score all articles for the user"""
        scored_articles = []

        for i, article in enumerate(articles):
            try:
                score = await self._score_single_article(
                    user_profile, article, i, diversity_enabled
                )
                scored_articles.append((article, score))

            except Exception as e:
                logger.warning(f"Failed to score article {article.id}: {e}")
                # Use fallback scoring
                fallback_score = RecommendationScore(
                    article_id=article.id,
                    score=article.credibility_score * 0.5,  # Simple fallback
                    explanation={"fallback": 1.0},
                    diversity_factor=0.5,
                    confidence=0.3,
                )
                scored_articles.append((article, fallback_score))

        return scored_articles

    async def _score_single_article(
        self,
        user_profile: UserProfile,
        article: NewsArticle,
        article_index: int,
        diversity_enabled: bool,
    ) -> RecommendationScore:
        """Score a single article for the user"""

        explanation = {}

        # 1. Content similarity score
        content_score = self._compute_content_similarity(
            user_profile, article, article_index
        )
        explanation["content_similarity"] = content_score

        # 2. Credibility score (already available)
        credibility_score = article.credibility_score
        explanation["credibility_score"] = credibility_score

        # 3. Temporal relevance (newer articles get higher scores)
        temporal_score = self._compute_temporal_relevance(article)
        explanation["temporal_relevance"] = temporal_score

        # 4. Source preference score
        source_score = self._compute_source_preference(user_profile, article)
        explanation["source_preference"] = source_score

        # 5. Diversity factor
        diversity_factor = self._compute_diversity_factor(user_profile, article)

        # Compute weighted final score
        final_score = (
            self.weights["content_similarity"] * content_score
            + self.weights["credibility_score"] * credibility_score
            + self.weights["temporal_relevance"] * temporal_score
            + self.weights["source_preference"] * source_score
        )

        # Apply diversity bonus if enabled
        if diversity_enabled and diversity_factor > 0.7:
            diversity_bonus = self.weights["diversity_bonus"] * diversity_factor
            final_score += diversity_bonus
            explanation["diversity_bonus"] = diversity_bonus

        # Calculate confidence based on profile completeness
        confidence = self._calculate_confidence(user_profile, explanation)

        return RecommendationScore(
            article_id=article.id,
            score=final_score,
            explanation=explanation,
            diversity_factor=diversity_factor,
            confidence=confidence,
        )

    def _compute_content_similarity(
        self, user_profile: UserProfile, article: NewsArticle, article_index: int
    ) -> float:
        """Compute content-based similarity score"""

        # Topic-based scoring
        topic_score = 0.0
        article_text = f"{article.title} {article.content}".lower()

        for topic, interest in user_profile.topics_of_interest.items():
            if topic in article_text:
                topic_score += interest

        # Normalize topic score
        topic_score = min(topic_score, 1.0)

        # TF-IDF similarity (if vectors are available)
        tfidf_score = 0.0
        if self.article_vectors is not None and article_index < len(self.article_ids):
            # For simplicity, we'll use topic-based scoring
            # In production, this would compute cosine similarity with user's reading history
            tfidf_score = topic_score  # Placeholder

        # Combine scores
        return topic_score * 0.7 + tfidf_score * 0.3

    def _compute_temporal_relevance(self, article: NewsArticle) -> float:
        """Compute temporal relevance score (newer = higher)"""
        now = datetime.now()
        if article.published_at.tzinfo is None:
            article_time = article.published_at.replace(tzinfo=now.tzinfo)
        else:
            article_time = article.published_at

        # Articles lose relevance over time
        hours_old = (
            now.replace(tzinfo=None) - article_time.replace(tzinfo=None)
        ).total_seconds() / 3600

        if hours_old < 1:
            return 1.0  # Very recent
        elif hours_old < 6:
            return 0.9
        elif hours_old < 24:
            return 0.7
        elif hours_old < 72:
            return 0.5
        else:
            return 0.3  # Older articles

    def _compute_source_preference(
        self, user_profile: UserProfile, article: NewsArticle
    ) -> float:
        """Compute source preference score"""
        if article.source in user_profile.source_preferences:
            return user_profile.source_preferences[article.source]

        # Default score based on credibility tier (if available)
        if hasattr(article, "credibility_score"):
            return min(article.credibility_score, 0.8)  # Cap at 0.8 for unknown sources

        return 0.5  # Neutral score for unknown sources

    def _compute_diversity_factor(
        self, user_profile: UserProfile, article: NewsArticle
    ) -> float:
        """Compute how diverse this article is from user's usual reading"""

        # Simple diversity computation based on topic distribution
        article_text = f"{article.title} {article.content}".lower()

        # Check if article covers topics user doesn't usually read
        uncommon_topics = ["environment", "arts", "sports", "entertainment"]
        diversity_score = 0.0

        for topic in uncommon_topics:
            if topic in article_text and topic not in user_profile.topics_of_interest:
                diversity_score += 0.25

        return min(diversity_score, 1.0)

    def _calculate_confidence(
        self, user_profile: UserProfile, explanation: Dict[str, float]
    ) -> float:
        """Calculate confidence in the recommendation"""

        # Base confidence on profile completeness
        profile_completeness = 0.0

        if user_profile.topics_of_interest:
            profile_completeness += 0.3
        if user_profile.reading_history:
            profile_completeness += 0.3
        if user_profile.source_preferences:
            profile_completeness += 0.2

        # Add confidence from score components
        score_confidence = len(explanation) / 5.0  # Max 5 components

        return min(profile_completeness + score_confidence * 0.2, 1.0)

    def _apply_diversity_optimization(
        self,
        scored_articles: List[Tuple[NewsArticle, RecommendationScore]],
        user_profile: UserProfile,
        diversity_ratio: float = 0.15,
    ) -> List[Tuple[NewsArticle, RecommendationScore]]:
        """Apply diversity optimization to prevent echo chambers"""

        if not scored_articles or user_profile.diversity_preference < 0.1:
            return scored_articles

        num_diverse = max(1, int(len(scored_articles) * diversity_ratio))

        # Sort by diversity factor
        diverse_articles = sorted(
            scored_articles, key=lambda x: x[1].diversity_factor, reverse=True
        )[:num_diverse]

        # Boost scores of diverse articles
        for article, score in diverse_articles:
            score.score *= 1.2  # 20% boost for diverse content

        return scored_articles

    def _fallback_recommendations(
        self, articles: List[NewsArticle], num_recommendations: int
    ) -> List[Tuple[NewsArticle, RecommendationScore]]:
        """Fallback recommendations when main algorithm fails"""

        # Simple ranking by credibility and recency
        fallback_recommendations = []

        for article in articles:
            temporal_score = self._compute_temporal_relevance(article)
            combined_score = article.credibility_score * 0.7 + temporal_score * 0.3

            score = RecommendationScore(
                article_id=article.id,
                score=combined_score,
                explanation={
                    "fallback_credibility": article.credibility_score,
                    "fallback_temporal": temporal_score,
                },
                diversity_factor=0.5,
                confidence=0.4,
            )

            fallback_recommendations.append((article, score))

        # Sort and return top N
        fallback_recommendations.sort(key=lambda x: x[1].score, reverse=True)
        return fallback_recommendations[:num_recommendations]

    async def update_user_feedback(
        self,
        user_id: int,
        article_id: str,
        feedback_type: str,  # "read", "liked", "shared", "dismissed"
        reading_time_seconds: Optional[int] = None,
    ):
        """Update user profile based on feedback"""

        if user_id not in self.user_profiles:
            return

        profile = self.user_profiles[user_id]

        # Add to reading history
        if feedback_type == "read" and article_id not in profile.reading_history:
            profile.reading_history.append(article_id)

            # Keep only recent history (last 100 articles)
            if len(profile.reading_history) > 100:
                profile.reading_history = profile.reading_history[-100:]

        # Update topic interests based on positive feedback
        if feedback_type in ["liked", "shared"]:
            # In production, this would analyze article content and boost relevant topics
            logger.info(f"Positive feedback for user {user_id}, article {article_id}")

        profile.last_updated = datetime.now()

    async def get_recommendation_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get analytics on recommendation performance for user"""

        if user_id not in self.user_profiles:
            return {"error": "User profile not found"}

        profile = self.user_profiles[user_id]

        return {
            "user_id": user_id,
            "profile_age_hours": (datetime.now() - profile.last_updated).total_seconds()
            / 3600,
            "reading_history_count": len(profile.reading_history),
            "topics_of_interest": profile.topics_of_interest,
            "credibility_preference": profile.credibility_preference,
            "diversity_preference": profile.diversity_preference,
            "source_preferences_count": len(profile.source_preferences),
        }


# Test and development utilities
async def test_recommendation_system():
    """Test the recommendation system"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from src.news.core.intelligence_engine import NewsArticle

    # Create test session
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        recommender = HybridNewsRecommender(session)

        # Create sample articles
        sample_articles = [
            NewsArticle(
                id="tech_1",
                title="AI Breakthrough in Healthcare",
                content="Artificial intelligence researchers have developed a new system for medical diagnosis...",
                source="MIT Technology Review",
                url="https://example.com/ai-healthcare",
                published_at=datetime.now(),
                credibility_score=0.95,
            ),
            NewsArticle(
                id="climate_1",
                title="Climate Change Summit Results",
                content="World leaders gathered to discuss new climate policies and carbon reduction targets...",
                source="Reuters",
                url="https://example.com/climate-summit",
                published_at=datetime.now() - timedelta(hours=2),
                credibility_score=0.92,
            ),
        ]

        # Get recommendations
        recommendations = await recommender.get_recommendations(
            user_id=123, candidate_articles=sample_articles, num_recommendations=5
        )

        print(f"Generated {len(recommendations)} recommendations:")
        for article, score in recommendations:
            print(f"- {article.title[:50]}... (Score: {score.score:.3f})")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_recommendation_system())

"""
AI Content Curator - Intelligent Content Selection and Optimization
Curates and optimizes content for maximum engagement and personalization.
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, Counter

from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.models.hybrid_recommender import HybridRecommender
from src.newsletter.core.personalization_engine import ContentType, UserPersona


class ContentSource(Enum):
    """Sources of content"""
    RECOMMENDATIONS = "recommendations"
    TRENDING = "trending"
    EDITORIAL = "editorial"
    USER_GENERATED = "user_generated"
    EXTERNAL_FEEDS = "external_feeds"
    AI_GENERATED = "ai_generated"


class ContentPriority(Enum):
    """Content priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ContentItem:
    """Structured content item"""
    id: str
    type: ContentType
    source: ContentSource
    priority: ContentPriority
    title: str
    description: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    target_audience: List[str]
    estimated_read_time: int  # minutes
    quality_score: float  # 0-1
    engagement_prediction: float  # 0-1
    created_at: datetime
    expires_at: Optional[datetime] = None
    personalization_hints: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class ContentCurationConfig:
    """Configuration for content curation"""
    max_items_per_type: int = 5
    freshness_weight: float = 0.3
    quality_weight: float = 0.4
    engagement_weight: float = 0.3
    diversity_threshold: float = 0.7
    trending_boost: float = 1.2
    editorial_boost: float = 1.1
    enable_ai_generation: bool = True
    content_type_weights: Dict[ContentType, float] = field(default_factory=dict)


class AIContentCurator:
    """
    AI-Powered Content Curator
    
    Features:
    - Multi-source content aggregation
    - Intelligent content scoring and ranking
    - Diversity optimization
    - Real-time trend analysis
    - Quality assessment
    - Personalized content selection
    """
    
    def __init__(
        self,
        cache_manager: AsyncCacheManager,
        recommender: HybridRecommender,
        config: Optional[ContentCurationConfig] = None
    ):
        self.cache = cache_manager
        self.recommender = recommender
        self.config = config or ContentCurationConfig()
        self.logger = StructuredLogger(__name__)
        
        # Content pools
        self.content_pools: Dict[ContentType, List[ContentItem]] = defaultdict(list)
        self.trending_cache: Dict[str, float] = {}
        
        # Quality models (simplified for demo)
        self.quality_keywords = {
            "high_quality": ["comprehensive", "detailed", "expert", "analysis", "insights"],
            "low_quality": ["clickbait", "shocking", "you won't believe", "one weird trick"]
        }
        
    async def curate_content(
        self,
        user_persona: UserPersona,
        target_content_types: List[ContentType],
        max_items: int = 10
    ) -> List[ContentItem]:
        """Curate personalized content for user"""
        try:
            # Refresh content pools
            await self._refresh_content_pools()
            
            # Get trending topics
            trending_topics = await self._get_trending_topics()
            
            curated_items = []
            type_counts = defaultdict(int)
            
            for content_type in target_content_types:
                if type_counts[content_type] >= self.config.max_items_per_type:
                    continue
                    
                # Get candidates for this content type
                candidates = await self._get_content_candidates(
                    content_type, user_persona, trending_topics
                )
                
                # Score and rank candidates
                scored_candidates = await self._score_content_candidates(
                    candidates, user_persona, trending_topics
                )
                
                # Select top items ensuring diversity
                selected = await self._select_diverse_content(
                    scored_candidates, 
                    curated_items,
                    self.config.max_items_per_type - type_counts[content_type]
                )
                
                curated_items.extend(selected)
                type_counts[content_type] += len(selected)
                
                if len(curated_items) >= max_items:
                    break
            
            # Final ranking and optimization
            final_curation = await self._optimize_final_selection(
                curated_items, user_persona, max_items
            )
            
            self.logger.info(
                "Content curation completed",
                user_id=user_persona.user_id,
                total_items=len(final_curation),
                content_types={ct.value: type_counts[ct] for ct in target_content_types},
                avg_quality=np.mean([item.quality_score for item in final_curation]) if final_curation else 0
            )
            
            return final_curation
            
        except Exception as e:
            self.logger.error(
                "Content curation failed",
                user_id=user_persona.user_id,
                error=str(e)
            )
            return []
    
    async def generate_dynamic_content(
        self,
        content_type: ContentType,
        user_persona: UserPersona,
        context: Dict[str, Any]
    ) -> Optional[ContentItem]:
        """Generate dynamic AI content based on user context"""
        try:
            if not self.config.enable_ai_generation:
                return None
                
            # Generate content based on type
            if content_type == ContentType.PERSONALIZED_QUOTES:
                return await self._generate_personalized_quote(user_persona, context)
            elif content_type == ContentType.READING_INSIGHTS:
                return await self._generate_reading_insight(user_persona, context)
            elif content_type == ContentType.READING_CHALLENGES:
                return await self._generate_reading_challenge(user_persona, context)
            else:
                return None
                
        except Exception as e:
            self.logger.error(
                "Dynamic content generation failed",
                content_type=content_type.value,
                user_id=user_persona.user_id,
                error=str(e)
            )
            return None
    
    async def analyze_content_performance(
        self,
        content_items: List[ContentItem],
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content performance for optimization"""
        try:
            performance_metrics = {
                "total_items": len(content_items),
                "avg_quality_score": np.mean([item.quality_score for item in content_items]),
                "content_type_distribution": {},
                "source_distribution": {},
                "engagement_predictions": {},
                "quality_distribution": {}
            }
            
            # Content type analysis
            type_counts = Counter(item.type.value for item in content_items)
            performance_metrics["content_type_distribution"] = dict(type_counts)
            
            # Source analysis
            source_counts = Counter(item.source.value for item in content_items)
            performance_metrics["source_distribution"] = dict(source_counts)
            
            # Engagement analysis
            for content_type in ContentType:
                type_items = [item for item in content_items if item.type == content_type]
                if type_items:
                    avg_engagement = np.mean([item.engagement_prediction for item in type_items])
                    performance_metrics["engagement_predictions"][content_type.value] = avg_engagement
            
            # Quality distribution
            quality_ranges = {
                "high": len([item for item in content_items if item.quality_score >= 0.8]),
                "medium": len([item for item in content_items if 0.5 <= item.quality_score < 0.8]),
                "low": len([item for item in content_items if item.quality_score < 0.5])
            }
            performance_metrics["quality_distribution"] = quality_ranges
            
            self.logger.info(
                "Content performance analyzed",
                metrics=performance_metrics
            )
            
            return performance_metrics
            
        except Exception as e:
            self.logger.error(
                "Content performance analysis failed",
                error=str(e)
            )
            return {}
    
    async def update_content_weights(
        self,
        performance_data: Dict[str, Any],
        user_feedback: Dict[str, Any]
    ) -> None:
        """Update content weights based on performance and feedback"""
        try:
            # Analyze performance patterns
            high_performing_types = []
            low_performing_types = []
            
            for content_type, engagement in performance_data.get("engagement_predictions", {}).items():
                if engagement > 0.7:
                    high_performing_types.append(content_type)
                elif engagement < 0.3:
                    low_performing_types.append(content_type)
            
            # Update weights
            for content_type_str in high_performing_types:
                content_type = ContentType(content_type_str)
                current_weight = self.config.content_type_weights.get(content_type, 1.0)
                self.config.content_type_weights[content_type] = min(2.0, current_weight * 1.1)
            
            for content_type_str in low_performing_types:
                content_type = ContentType(content_type_str)
                current_weight = self.config.content_type_weights.get(content_type, 1.0)
                self.config.content_type_weights[content_type] = max(0.5, current_weight * 0.9)
            
            self.logger.info(
                "Content weights updated",
                high_performing=high_performing_types,
                low_performing=low_performing_types,
                updated_weights=self.config.content_type_weights
            )
            
        except Exception as e:
            self.logger.error(
                "Content weight update failed",
                error=str(e)
            )
    
    # Private helper methods
    
    async def _refresh_content_pools(self) -> None:
        """Refresh content from all sources"""
        try:
            # Clear expired content
            await self._clear_expired_content()
            
            # Fetch new content from each source
            await asyncio.gather(
                self._fetch_recommendation_content(),
                self._fetch_trending_content(),
                self._fetch_editorial_content(),
                self._fetch_external_content(),
                return_exceptions=True
            )
            
        except Exception as e:
            self.logger.error("Content pool refresh failed", error=str(e))
    
    async def _clear_expired_content(self) -> None:
        """Remove expired content from pools"""
        now = datetime.utcnow()
        for content_type in self.content_pools:
            self.content_pools[content_type] = [
                item for item in self.content_pools[content_type]
                if item.expires_at is None or item.expires_at > now
            ]
    
    async def _fetch_recommendation_content(self) -> None:
        """Fetch recommendation-based content"""
        try:
            # Get popular books for recommendations
            # This would integrate with the existing recommender system
            popular_books = await self._get_popular_books()
            
            for book in popular_books[:10]:  # Limit to top 10
                content_item = ContentItem(
                    id=f"rec_{book.get('book_id', 'unknown')}",
                    type=ContentType.BOOK_RECOMMENDATION,
                    source=ContentSource.RECOMMENDATIONS,
                    priority=ContentPriority.HIGH,
                    title=f"Recommended: {book.get('title', 'Unknown Title')}",
                    description=f"A highly-rated book by {book.get('authors', 'Unknown Author')}",
                    content=self._format_book_content(book),
                    metadata=book,
                    tags=book.get('genres', []),
                    target_audience=["general"],
                    estimated_read_time=2,
                    quality_score=min(1.0, book.get('average_rating', 3.0) / 5.0),
                    engagement_prediction=0.7,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=7),
                    personalization_hints={
                        "genres": book.get('genres', []),
                        "rating": book.get('average_rating', 0),
                        "popularity": book.get('ratings_count', 0)
                    }
                )
                self.content_pools[ContentType.BOOK_RECOMMENDATION].append(content_item)
                
        except Exception as e:
            self.logger.error("Failed to fetch recommendation content", error=str(e))
    
    async def _fetch_trending_content(self) -> None:
        """Fetch trending topics content"""
        try:
            trending_topics = await self._get_trending_topics()
            
            for topic in trending_topics[:5]:  # Top 5 trending
                content_item = ContentItem(
                    id=f"trend_{topic.replace(' ', '_').lower()}",
                    type=ContentType.TRENDING_TOPICS,
                    source=ContentSource.TRENDING,
                    priority=ContentPriority.HIGH,
                    title=f"Trending: {topic.title()}",
                    description=f"Discover what's trending in {topic}",
                    content=f"Join the conversation about {topic} that's capturing readers' attention worldwide.",
                    metadata={"topic": topic, "trend_score": random.uniform(0.7, 1.0)},
                    tags=[topic.lower()],
                    target_audience=["trend_followers"],
                    estimated_read_time=1,
                    quality_score=0.8,
                    engagement_prediction=0.8,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=2)
                )
                self.content_pools[ContentType.TRENDING_TOPICS].append(content_item)
                
        except Exception as e:
            self.logger.error("Failed to fetch trending content", error=str(e))
    
    async def _fetch_editorial_content(self) -> None:
        """Fetch editorial content"""
        try:
            # Generate editorial insights
            editorial_topics = [
                "The Rise of Digital Reading",
                "Author Spotlight: Contemporary Voices",
                "Book Club Recommendations",
                "Reading Habits That Changed My Life",
                "The Future of Publishing"
            ]
            
            for topic in editorial_topics:
                content_item = ContentItem(
                    id=f"editorial_{topic.replace(' ', '_').lower()}",
                    type=ContentType.READING_INSIGHTS,
                    source=ContentSource.EDITORIAL,
                    priority=ContentPriority.MEDIUM,
                    title=topic,
                    description=f"Editorial insights on {topic.lower()}",
                    content=f"Explore our thoughts and analysis on {topic.lower()}.",
                    metadata={"editorial_category": "insights"},
                    tags=["editorial", "insights"],
                    target_audience=["engaged_readers"],
                    estimated_read_time=3,
                    quality_score=0.9,
                    engagement_prediction=0.6,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=14)
                )
                self.content_pools[ContentType.READING_INSIGHTS].append(content_item)
                
        except Exception as e:
            self.logger.error("Failed to fetch editorial content", error=str(e))
    
    async def _fetch_external_content(self) -> None:
        """Fetch content from external sources"""
        try:
            # Simulate external content (would integrate with RSS feeds, APIs, etc.)
            external_sources = [
                {"title": "Community Book Discussion", "type": ContentType.COMMUNITY_HIGHLIGHTS},
                {"title": "Author Interview Highlights", "type": ContentType.AUTHOR_SPOTLIGHTS},
                {"title": "Genre Deep Dive: Mystery", "type": ContentType.GENRE_DEEP_DIVES}
            ]
            
            for source in external_sources:
                content_item = ContentItem(
                    id=f"external_{source['title'].replace(' ', '_').lower()}",
                    type=source['type'],
                    source=ContentSource.EXTERNAL_FEEDS,
                    priority=ContentPriority.MEDIUM,
                    title=source['title'],
                    description=f"External content: {source['title']}",
                    content=f"Curated content from our partners about {source['title'].lower()}.",
                    metadata={"external_source": "partner_feed"},
                    tags=["external", "curated"],
                    target_audience=["diverse_interests"],
                    estimated_read_time=2,
                    quality_score=0.7,
                    engagement_prediction=0.5,
                    created_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                self.content_pools[source['type']].append(content_item)
                
        except Exception as e:
            self.logger.error("Failed to fetch external content", error=str(e))
    
    async def _get_content_candidates(
        self,
        content_type: ContentType,
        user_persona: UserPersona,
        trending_topics: List[str]
    ) -> List[ContentItem]:
        """Get content candidates for a specific type"""
        candidates = self.content_pools.get(content_type, [])
        
        # Filter by relevance to user
        relevant_candidates = []
        for item in candidates:
            relevance_score = await self._calculate_content_relevance(item, user_persona)
            if relevance_score > 0.3:  # Minimum relevance threshold
                item.personalization_hints["relevance_score"] = relevance_score
                relevant_candidates.append(item)
        
        return relevant_candidates
    
    async def _score_content_candidates(
        self,
        candidates: List[ContentItem],
        user_persona: UserPersona,
        trending_topics: List[str]
    ) -> List[Tuple[ContentItem, float]]:
        """Score and rank content candidates"""
        scored_candidates = []
        
        for item in candidates:
            score = await self._calculate_content_score(item, user_persona, trending_topics)
            scored_candidates.append((item, score))
        
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates
    
    async def _calculate_content_score(
        self,
        item: ContentItem,
        user_persona: UserPersona,
        trending_topics: List[str]
    ) -> float:
        """Calculate comprehensive content score"""
        # Base score components
        quality_score = item.quality_score * self.config.quality_weight
        engagement_score = item.engagement_prediction * self.config.engagement_weight
        
        # Freshness score
        age_hours = (datetime.utcnow() - item.created_at).total_seconds() / 3600
        freshness_score = max(0, 1.0 - (age_hours / 168)) * self.config.freshness_weight  # 1 week decay
        
        # Trending boost
        trending_boost = 1.0
        item_text = f"{item.title} {item.description}".lower()
        if any(topic.lower() in item_text for topic in trending_topics):
            trending_boost = self.config.trending_boost
        
        # Source boost
        source_boost = 1.0
        if item.source == ContentSource.EDITORIAL:
            source_boost = self.config.editorial_boost
        
        # Content type weight
        type_weight = self.config.content_type_weights.get(item.type, 1.0)
        
        # Personal preference alignment
        preference_score = user_persona.content_preferences.get(item.type, 0.5)
        
        # Calculate final score
        base_score = quality_score + engagement_score + freshness_score
        final_score = base_score * trending_boost * source_boost * type_weight * preference_score
        
        return min(1.0, final_score)
    
    async def _calculate_content_relevance(
        self,
        item: ContentItem,
        user_persona: UserPersona
    ) -> float:
        """Calculate content relevance to user"""
        relevance_factors = []
        
        # Genre alignment for book recommendations
        if item.type == ContentType.BOOK_RECOMMENDATION:
            item_genres = set(item.tags)
            user_genres = set(user_persona.preferred_genres)
            genre_overlap = len(item_genres & user_genres) / max(1, len(user_genres))
            relevance_factors.append(genre_overlap)
        
        # Reading velocity alignment
        if item.estimated_read_time <= 2 and user_persona.reading_velocity < 1.0:
            relevance_factors.append(1.0)  # Short content for slow readers
        elif item.estimated_read_time > 5 and user_persona.reading_velocity > 3.0:
            relevance_factors.append(1.0)  # Long content for fast readers
        else:
            relevance_factors.append(0.7)
        
        # Attention span alignment
        attention_scores = {"short": 1, "medium": 3, "long": 5}
        attention_match = 1.0 - abs(
            attention_scores.get(user_persona.attention_span, 3) - item.estimated_read_time
        ) / 5.0
        relevance_factors.append(max(0, attention_match))
        
        return np.mean(relevance_factors) if relevance_factors else 0.5
    
    async def _select_diverse_content(
        self,
        scored_candidates: List[Tuple[ContentItem, float]],
        existing_items: List[ContentItem],
        max_items: int
    ) -> List[ContentItem]:
        """Select diverse content to avoid redundancy"""
        selected = []
        existing_tags = set()
        
        # Collect tags from existing items
        for item in existing_items:
            existing_tags.update(item.tags)
        
        for item, score in scored_candidates:
            if len(selected) >= max_items:
                break
                
            # Check diversity
            item_tags = set(item.tags)
            overlap = len(item_tags & existing_tags) / max(1, len(item_tags))
            
            if overlap < self.config.diversity_threshold:
                selected.append(item)
                existing_tags.update(item_tags)
        
        return selected
    
    async def _optimize_final_selection(
        self,
        items: List[ContentItem],
        user_persona: UserPersona,
        max_items: int
    ) -> List[ContentItem]:
        """Final optimization of content selection"""
        if len(items) <= max_items:
            return items
        
        # Re-score with user-specific factors
        item_scores = []
        for item in items:
            # Calculate final personalization score
            base_score = item.quality_score * 0.4 + item.engagement_prediction * 0.6
            
            # User preference boost
            preference_boost = user_persona.content_preferences.get(item.type, 0.5)
            
            # Priority boost
            priority_scores = {
                ContentPriority.CRITICAL: 1.0,
                ContentPriority.HIGH: 0.8,
                ContentPriority.MEDIUM: 0.6,
                ContentPriority.LOW: 0.4
            }
            priority_boost = priority_scores.get(item.priority, 0.6)
            
            final_score = base_score * preference_boost * priority_boost
            item_scores.append((item, final_score))
        
        # Sort and select top items
        item_scores.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in item_scores[:max_items]]
    
    async def _generate_personalized_quote(
        self,
        user_persona: UserPersona,
        context: Dict[str, Any]
    ) -> ContentItem:
        """Generate personalized reading quote"""
        # Simple quote generation (would use LLM in production)
        quotes = [
            "A reader lives a thousand lives before he dies",
            "Books are a uniquely portable magic",
            "Reading is to the mind what exercise is to the body",
            "The more that you read, the more things you will know"
        ]
        
        selected_quote = random.choice(quotes)
        
        return ContentItem(
            id=f"quote_{user_persona.user_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            type=ContentType.PERSONALIZED_QUOTES,
            source=ContentSource.AI_GENERATED,
            priority=ContentPriority.LOW,
            title="Your Daily Reading Inspiration",
            description="A personalized quote to inspire your reading journey",
            content=f'"{selected_quote}" - A message curated just for you',
            metadata={"quote": selected_quote, "personalized": True},
            tags=["inspiration", "personalized"],
            target_audience=[user_persona.user_id],
            estimated_read_time=1,
            quality_score=0.8,
            engagement_prediction=0.6,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
    
    async def _generate_reading_insight(
        self,
        user_persona: UserPersona,
        context: Dict[str, Any]
    ) -> ContentItem:
        """Generate personalized reading insight"""
        insights = [
            f"Based on your reading of {len(user_persona.preferred_genres)} genres, you have diverse literary tastes",
            f"Your reading velocity of {user_persona.reading_velocity:.1f} books per month puts you among active readers",
            f"You tend to be most engaged during {user_persona.engagement_pattern} hours"
        ]
        
        selected_insight = random.choice(insights)
        
        return ContentItem(
            id=f"insight_{user_persona.user_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            type=ContentType.READING_INSIGHTS,
            source=ContentSource.AI_GENERATED,
            priority=ContentPriority.MEDIUM,
            title="Your Reading Insights",
            description="Personalized insights about your reading habits",
            content=selected_insight,
            metadata={"insight_type": "personal_stats", "personalized": True},
            tags=["insights", "personalized", "statistics"],
            target_audience=[user_persona.user_id],
            estimated_read_time=1,
            quality_score=0.7,
            engagement_prediction=0.7,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=3)
        )
    
    async def _generate_reading_challenge(
        self,
        user_persona: UserPersona,
        context: Dict[str, Any]
    ) -> ContentItem:
        """Generate personalized reading challenge"""
        challenges = [
            f"Try reading a {random.choice(['mystery', 'sci-fi', 'romance'])} novel this week",
            f"Challenge yourself to read for {user_persona.reading_velocity * 30:.0f} minutes today",
            "Discover a new author from a different country",
            "Read a book published in the last year"
        ]
        
        selected_challenge = random.choice(challenges)
        
        return ContentItem(
            id=f"challenge_{user_persona.user_id}_{datetime.utcnow().strftime('%Y%m%d')}",
            type=ContentType.READING_CHALLENGES,
            source=ContentSource.AI_GENERATED,
            priority=ContentPriority.LOW,
            title="Your Reading Challenge",
            description="A personalized challenge to expand your reading horizons",
            content=f"Today's challenge: {selected_challenge}",
            metadata={"challenge_type": "daily", "personalized": True},
            tags=["challenge", "personalized", "growth"],
            target_audience=[user_persona.user_id],
            estimated_read_time=1,
            quality_score=0.6,
            engagement_prediction=0.5,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
    
    async def _get_popular_books(self) -> List[Dict]:
        """Get popular books for recommendations"""
        # This would integrate with the existing book database
        return [
            {
                "book_id": "1",
                "title": "The Midnight Library",
                "authors": "Matt Haig",
                "genres": ["Fiction", "Philosophy"],
                "average_rating": 4.2,
                "ratings_count": 150000
            },
            {
                "book_id": "2",
                "title": "Project Hail Mary",
                "authors": "Andy Weir",
                "genres": ["Science Fiction", "Adventure"],
                "average_rating": 4.5,
                "ratings_count": 120000
            }
        ]
    
    async def _get_trending_topics(self) -> List[str]:
        """Get current trending topics"""
        # This would integrate with trending analysis
        return ["artificial intelligence", "climate fiction", "mystery thriller", "memoir", "fantasy"]
    
    def _format_book_content(self, book: Dict) -> str:
        """Format book information for content"""
        return f"Discover '{book.get('title', 'Unknown')}' by {book.get('authors', 'Unknown Author')} - rated {book.get('average_rating', 0):.1f}/5 by {book.get('ratings_count', 0):,} readers."

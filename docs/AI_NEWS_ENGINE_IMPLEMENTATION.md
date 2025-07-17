# 🚀 **AI News Engine - Module Implementation Plan**

_From Architecture to Production Code_

## 📋 **Implementation Roadmap**

### Phase 1: Core Engine (Days 1-3)

```
┌─ NewsIntelligenceEngine ────────────────────────────────────┐
│  ├─ SourceManager                                           │
│  ├─ ContentProcessor                                        │
│  ├─ CredibilityIntegration (leverage existing 85% system)   │
│  └─ CacheManager                                            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 2: AI Processing (Days 4-6)

```
┌─ AISummarizationPipeline ───────────────────────────────────┐
│  ├─ ClaudeSonnetIntegration                                 │
│  ├─ SummaryQualityValidator                                 │
│  ├─ DiversityInjector                                       │
│  └─ BiasDetector                                            │
└─────────────────────────────────────────────────────────────┘
```

### Phase 3: Personalization (Days 7-9)

```
┌─ HybridNewsRecommender ─────────────────────────────────────┐
│  ├─ UserProfileManager                                      │
│  ├─ ContentBasedFiltering                                   │
│  ├─ CollaborativeFiltering                                  │
│  └─ DiversityOptimizer                                      │
└─────────────────────────────────────────────────────────────┘
```

### Phase 4: Frontend & UX (Days 10-12)

```
┌─ KindleDashboard ───────────────────────────────────────────┐
│  ├─ VirtualizedNewsFeed                                     │
│  ├─ IntelligentSearch                                       │
│  ├─ CredibilityVisualization                               │
│  └─ PersonalizationControls                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ **Module 1: NewsIntelligenceEngine**

### File: `src/news/core/intelligence_engine.py`

```python
"""
AI News Intelligence Engine - Core System
Integrates with existing false news detection (85% complete)
Performance target: <500ms response time
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import aiohttp
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.fakenews.detection_service import FakeNewsDetectionService
from src.core.cache import CacheManager
from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


@dataclass
class NewsArticle:
    """Enhanced news article with credibility and AI analysis"""
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    credibility_score: float = 0.0
    bias_rating: Optional[str] = None
    topics: List[str] = None
    reading_time_minutes: int = 0
    diversity_tag: Optional[str] = None  # "contrarian", "alternative_perspective"

    def __post_init__(self):
        if self.topics is None:
            self.topics = []
        # Calculate reading time (avg 200 words/minute)
        if self.reading_time_minutes == 0:
            word_count = len(self.content.split())
            self.reading_time_minutes = max(1, word_count // 200)


@dataclass
class NewsSource:
    """News source with credibility metadata"""
    id: str
    name: str
    base_url: str
    credibility_tier: int  # 1=highest (>95%), 2=high (85-95%), 3=moderate (70-85%)
    api_key: Optional[str] = None
    rss_feeds: List[str] = None
    rate_limit: int = 100  # requests per hour
    last_accessed: Optional[datetime] = None

    def __post_init__(self):
        if self.rss_feeds is None:
            self.rss_feeds = []


class NewsIntelligenceEngine:
    """
    Main orchestrator for AI news intelligence system
    Leverages existing FakeNewsDetectionService (85% complete)
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        fake_news_service: FakeNewsDetectionService,
        db_session: AsyncSession
    ):
        self.cache = cache_manager
        self.fake_news_service = fake_news_service
        self.db = db_session
        self.sources: Dict[str, NewsSource] = {}
        self.session = None

        # Performance optimization: Pre-load high-credibility sources
        self._initialize_sources()

    async def __aenter__(self):
        """Async context manager for HTTP sessions"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _initialize_sources(self):
        """Initialize high-credibility news sources"""
        # Tier 1 sources (>95% credibility)
        tier_1_sources = [
            NewsSource(
                id="reuters",
                name="Reuters",
                base_url="https://newsapi.org/v2",
                credibility_tier=1,
                rss_feeds=["https://feeds.reuters.com/reuters/topNews"]
            ),
            NewsSource(
                id="ap_news",
                name="Associated Press",
                base_url="https://newsapi.org/v2",
                credibility_tier=1,
                rss_feeds=["https://feeds.apnews.com/ap/world-news"]
            ),
            NewsSource(
                id="bbc",
                name="BBC News",
                base_url="https://newsapi.org/v2",
                credibility_tier=1,
                rss_feeds=["http://feeds.bbci.co.uk/news/rss.xml"]
            )
        ]

        # Tier 2 sources (85-95% credibility)
        tier_2_sources = [
            NewsSource(
                id="nytimes",
                name="The New York Times",
                base_url="https://api.nytimes.com/svc",
                credibility_tier=2,
                rss_feeds=["https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"]
            ),
            NewsSource(
                id="guardian",
                name="The Guardian",
                base_url="https://content.guardianapis.com",
                credibility_tier=2
            )
        ]

        for source in tier_1_sources + tier_2_sources:
            self.sources[source.id] = source

    async def get_personalized_feed(
        self,
        user_id: int,
        credibility_threshold: float = 0.8,
        diversity_enabled: bool = True,
        limit: int = 20
    ) -> List[NewsArticle]:
        """
        Get personalized news feed with credibility filtering

        Performance target: <500ms response time
        Cache strategy: 15-minute TTL for personalized feeds
        """
        cache_key = f"personalized_feed:{user_id}:{credibility_threshold}:{diversity_enabled}"

        # Check cache first (O(1) operation)
        cached_feed = await self.cache.get(cache_key)
        if cached_feed:
            logger.info("Served personalized feed from cache", user_id=user_id)
            return cached_feed

        start_time = datetime.now()

        try:
            # Parallel processing for performance
            tasks = [
                self._fetch_trending_news(limit * 2),  # Over-fetch for filtering
                self._get_user_preferences(user_id),
                self._get_user_reading_history(user_id)
            ]

            raw_articles, user_preferences, reading_history = await asyncio.gather(*tasks)

            # Apply credibility filtering using existing detection service
            credible_articles = await self._filter_by_credibility(
                raw_articles,
                credibility_threshold
            )

            # Apply personalization
            personalized_articles = await self._apply_personalization(
                credible_articles,
                user_preferences,
                reading_history,
                limit
            )

            # Inject diversity if enabled
            if diversity_enabled:
                personalized_articles = await self._inject_diversity(
                    personalized_articles,
                    user_preferences
                )

            # Cache the result
            await self.cache.set(
                cache_key,
                personalized_articles,
                ttl=900  # 15 minutes
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                "Generated personalized feed",
                user_id=user_id,
                articles_count=len(personalized_articles),
                processing_time_ms=processing_time * 1000,
                credibility_threshold=credibility_threshold
            )

            return personalized_articles[:limit]

        except Exception as e:
            logger.error(
                "Failed to generate personalized feed",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            # Fallback to trending news
            return await self._get_fallback_feed(credibility_threshold, limit)

    async def _fetch_trending_news(self, limit: int) -> List[NewsArticle]:
        """Fetch trending news from multiple high-credibility sources"""
        all_articles = []

        # Parallel source fetching
        fetch_tasks = []
        for source_id, source in self.sources.items():
            if source.credibility_tier <= 2:  # Only tier 1 and 2 sources
                fetch_tasks.append(self._fetch_from_source(source, limit // len(self.sources)))

        source_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        for i, result in enumerate(source_results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch from source", source=list(self.sources.keys())[i], error=str(result))
            else:
                all_articles.extend(result)

        # Sort by recency and credibility
        all_articles.sort(
            key=lambda x: (x.credibility_score, x.published_at),
            reverse=True
        )

        return all_articles[:limit]

    async def _fetch_from_source(self, source: NewsSource, limit: int) -> List[NewsArticle]:
        """Fetch articles from a specific news source"""
        if source.id == "reuters":
            return await self._fetch_newsapi(source, "reuters.com", limit)
        elif source.id == "ap_news":
            return await self._fetch_newsapi(source, "associated-press", limit)
        elif source.id == "bbc":
            return await self._fetch_newsapi(source, "bbc-news", limit)
        elif source.id == "nytimes":
            return await self._fetch_nytimes(source, limit)
        else:
            logger.warning(f"Unknown source type: {source.id}")
            return []

    async def _fetch_newsapi(self, source: NewsSource, source_param: str, limit: int) -> List[NewsArticle]:
        """Fetch from NewsAPI"""
        url = f"{source.base_url}/top-headlines"
        params = {
            "sources": source_param,
            "pageSize": limit,
            "apiKey": self._get_api_key("newsapi")
        }

        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                articles = []

                for article_data in data.get("articles", []):
                    if article_data.get("content") and article_data.get("content") != "[Removed]":
                        article = NewsArticle(
                            id=f"{source.id}_{hash(article_data['url'])}",
                            title=article_data["title"],
                            content=article_data["content"],
                            source=source.name,
                            url=article_data["url"],
                            published_at=datetime.fromisoformat(
                                article_data["publishedAt"].replace("Z", "+00:00")
                            ),
                            credibility_score=self._get_source_credibility(source.credibility_tier)
                        )
                        articles.append(article)

                return articles

        except Exception as e:
            logger.error(f"Failed to fetch from NewsAPI", source=source.id, error=str(e))
            return []

    async def _fetch_nytimes(self, source: NewsSource, limit: int) -> List[NewsArticle]:
        """Fetch from New York Times API"""
        url = f"{source.base_url}/search/v2/articlesearch.json"
        params = {
            "sort": "newest",
            "page": 0,
            "page_size": limit,
            "api-key": self._get_api_key("nytimes")
        }

        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                articles = []

                for doc in data.get("response", {}).get("docs", []):
                    article = NewsArticle(
                        id=f"nytimes_{doc['_id']}",
                        title=doc["headline"]["main"],
                        content=doc.get("abstract", ""),
                        source=source.name,
                        url=doc["web_url"],
                        published_at=datetime.fromisoformat(doc["pub_date"]),
                        credibility_score=self._get_source_credibility(source.credibility_tier)
                    )
                    articles.append(article)

                return articles

        except Exception as e:
            logger.error(f"Failed to fetch from NYTimes", error=str(e))
            return []

    async def _filter_by_credibility(
        self,
        articles: List[NewsArticle],
        threshold: float
    ) -> List[NewsArticle]:
        """
        Filter articles by credibility using existing FakeNewsDetectionService

        Leverages the 85% complete false news detection system
        """
        credible_articles = []

        # Batch process for performance
        batch_size = 10
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]

            # Use existing detection service
            batch_tasks = []
            for article in batch:
                task = self.fake_news_service.analyze_article(
                    title=article.title,
                    content=article.content,
                    source=article.source,
                    url=article.url
                )
                batch_tasks.append(task)

            results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for article, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.warning(f"Credibility check failed", article_id=article.id, error=str(result))
                    # Use source-based credibility as fallback
                    if article.credibility_score >= threshold:
                        credible_articles.append(article)
                else:
                    # Use detection service result
                    article.credibility_score = result.credibility_score
                    article.bias_rating = result.bias_rating

                    if article.credibility_score >= threshold:
                        credible_articles.append(article)

        logger.info(
            "Credibility filtering complete",
            original_count=len(articles),
            filtered_count=len(credible_articles),
            threshold=threshold
        )

        return credible_articles

    def _get_source_credibility(self, tier: int) -> float:
        """Convert credibility tier to numeric score"""
        tier_scores = {
            1: 0.95,  # Tier 1: >95%
            2: 0.90,  # Tier 2: 85-95%
            3: 0.75   # Tier 3: 70-85%
        }
        return tier_scores.get(tier, 0.70)

    def _get_api_key(self, service: str) -> str:
        """Get API key from environment or config"""
        import os
        keys = {
            "newsapi": os.getenv("NEWSAPI_KEY"),
            "nytimes": os.getenv("NYTIMES_API_KEY")
        }
        return keys.get(service, "")

    async def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user reading preferences"""
        # Implementation will connect to user preferences storage
        return {
            "topics": ["technology", "science", "politics"],
            "credibility_threshold": 0.8,
            "diversity_enabled": True,
            "reading_time_preference": "medium"  # short, medium, long
        }

    async def _get_user_reading_history(self, user_id: int) -> List[Dict]:
        """Get user's recent reading history for personalization"""
        # Implementation will query user activity
        return []

    async def _apply_personalization(
        self,
        articles: List[NewsArticle],
        preferences: Dict[str, Any],
        reading_history: List[Dict],
        limit: int
    ) -> List[NewsArticle]:
        """Apply ML-based personalization"""
        # Filter by topic preferences
        preferred_topics = set(preferences.get("topics", []))
        if preferred_topics:
            articles = [
                article for article in articles
                if any(topic in preferred_topics for topic in article.topics)
            ]

        # TODO: Implement collaborative filtering based on reading history
        # This will use the existing hybrid recommender patterns

        return articles[:limit]

    async def _inject_diversity(
        self,
        articles: List[NewsArticle],
        preferences: Dict[str, Any]
    ) -> List[NewsArticle]:
        """Inject diverse perspectives to prevent echo chambers"""
        diversity_ratio = 0.15  # 15% contrarian content
        num_diverse = int(len(articles) * diversity_ratio)

        if num_diverse == 0:
            return articles

        # TODO: Implement diversity injection logic
        # Mark some articles as "contrarian" or "alternative perspective"

        return articles

    async def _get_fallback_feed(self, threshold: float, limit: int) -> List[NewsArticle]:
        """Fallback feed when personalization fails"""
        return await self._fetch_trending_news(limit)


# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} completed", duration_ms=duration * 1000)
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} failed", duration_ms=duration * 1000, error=str(e))
            raise
    return wrapper
```

### Usage Example:

```python
# Initialize the news intelligence engine
async def create_news_engine():
    cache_manager = CacheManager(redis_client)
    fake_news_service = FakeNewsDetectionService(db_session)

    async with NewsIntelligenceEngine(
        cache_manager=cache_manager,
        fake_news_service=fake_news_service,
        db_session=db_session
    ) as engine:

        # Get personalized feed for user
        articles = await engine.get_personalized_feed(
            user_id=123,
            credibility_threshold=0.85,
            diversity_enabled=True,
            limit=20
        )

        return articles
```

---

## 🚀 **Next Implementation Steps**

1. **Immediate**: Create `src/news/` directory structure
2. **Day 1**: Implement `NewsIntelligenceEngine` core
3. **Day 2**: Integrate with existing `FakeNewsDetectionService`
4. **Day 3**: Add caching and performance optimization
5. **Day 4**: Begin AI summarization pipeline

This module provides the foundation for the entire AI news system, leveraging the existing 85% complete false news detection infrastructure while adding personalization and performance optimization.

"""
AI News Intelligence Engine - Core System
Integrates with existing false news detection (85% complete)
Performance target: <500ms response time
"""

import asyncio
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

# Import existing infrastructure
from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)


@dataclass
class NewsArticle:
    """Enhanced news article with credibility and AI analysis"""

    id: str
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    summary: Optional[str] = None
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
    Leverages existing infrastructure for high-performance news processing
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.sources: Dict[str, NewsSource] = {}
        self.session = None

        # Performance optimization: Pre-load high-credibility sources
        self._initialize_sources()

    async def __aenter__(self):
        """Async context manager for HTTP sessions"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=aiohttp.TCPConnector(limit=100),
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
                rss_feeds=["https://feeds.reuters.com/reuters/topNews"],
            ),
            NewsSource(
                id="ap_news",
                name="Associated Press",
                base_url="https://newsapi.org/v2",
                credibility_tier=1,
                rss_feeds=["https://feeds.apnews.com/ap/world-news"],
            ),
            NewsSource(
                id="bbc",
                name="BBC News",
                base_url="https://newsapi.org/v2",
                credibility_tier=1,
                rss_feeds=["http://feeds.bbci.co.uk/news/rss.xml"],
            ),
        ]

        # Tier 2 sources (85-95% credibility)
        tier_2_sources = [
            NewsSource(
                id="nytimes",
                name="The New York Times",
                base_url="https://api.nytimes.com/svc",
                credibility_tier=2,
                rss_feeds=["https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"],
            ),
            NewsSource(
                id="guardian",
                name="The Guardian",
                base_url="https://content.guardianapis.com",
                credibility_tier=2,
            ),
        ]

        for source in tier_1_sources + tier_2_sources:
            self.sources[source.id] = source

    async def get_personalized_feed(
        self,
        user_id: int,
        credibility_threshold: float = 0.8,
        diversity_enabled: bool = True,
        limit: int = 20,
    ) -> List[NewsArticle]:
        """
        Get personalized news feed with credibility filtering

        Performance target: <500ms response time
        """
        start_time = datetime.now()

        try:
            # Parallel processing for performance
            tasks = [
                self._fetch_trending_news(limit * 2),  # Over-fetch for filtering
                self._get_user_preferences(user_id),
                self._get_user_reading_history(user_id),
            ]

            raw_articles, user_preferences, reading_history = await asyncio.gather(
                *tasks
            )

            # Apply credibility filtering
            credible_articles = await self._filter_by_credibility(
                raw_articles, credibility_threshold
            )

            # Apply personalization
            personalized_articles = await self._apply_personalization(
                credible_articles, user_preferences, reading_history, limit
            )

            # Inject diversity if enabled
            if diversity_enabled:
                personalized_articles = await self._inject_diversity(
                    personalized_articles, user_preferences
                )

            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                "Generated personalized feed",
                user_id=user_id,
                articles_count=len(personalized_articles),
                processing_time_ms=processing_time * 1000,
                credibility_threshold=credibility_threshold,
            )

            return personalized_articles[:limit]

        except Exception as e:
            logger.error(
                "Failed to generate personalized feed",
                user_id=user_id,
                error=str(e),
                exc_info=True,
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
                fetch_tasks.append(
                    self._fetch_from_source(source, limit // len(self.sources))
                )

        source_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        for i, result in enumerate(source_results):
            if isinstance(result, Exception):
                source_name = list(self.sources.keys())[i]
                logger.warning(
                    "Failed to fetch from source", source=source_name, error=str(result)
                )
            else:
                all_articles.extend(result)

        # Sort by recency and credibility
        all_articles.sort(
            key=lambda x: (x.credibility_score, x.published_at), reverse=True
        )

        return all_articles[:limit]

    async def _fetch_from_source(
        self, source: NewsSource, limit: int
    ) -> List[NewsArticle]:
        """Fetch articles from a specific news source"""
        if source.id in ["reuters", "ap_news", "bbc"]:
            return await self._fetch_newsapi(source, limit)
        elif source.id == "nytimes":
            return await self._fetch_nytimes(source, limit)
        else:
            logger.warning(f"Unknown source type: {source.id}")
            return []

    async def _fetch_newsapi(self, source: NewsSource, limit: int) -> List[NewsArticle]:
        """Fetch from NewsAPI"""
        # Source mapping for NewsAPI
        source_mapping = {
            "reuters": "reuters",
            "ap_news": "associated-press",
            "bbc": "bbc-news",
        }

        url = f"{source.base_url}/top-headlines"
        params = {
            "sources": source_mapping.get(source.id, source.id),
            "pageSize": min(limit, 20),  # NewsAPI limit
            "apiKey": self._get_api_key("newsapi"),
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(
                        f"NewsAPI returned status {response.status}", source=source.id
                    )
                    return []

                data = await response.json()
                articles = []

                for article_data in data.get("articles", []):
                    if (
                        article_data.get("content")
                        and article_data.get("content") != "[Removed]"
                    ):
                        # Generate unique ID
                        article_id = hashlib.md5(
                            f"{source.id}_{article_data['url']}".encode()
                        ).hexdigest()

                        article = NewsArticle(
                            id=article_id,
                            title=article_data["title"],
                            content=article_data["content"],
                            source=source.name,
                            url=article_data["url"],
                            published_at=datetime.fromisoformat(
                                article_data["publishedAt"].replace("Z", "+00:00")
                            ),
                            credibility_score=self._get_source_credibility(
                                source.credibility_tier
                            ),
                        )
                        articles.append(article)

                return articles

        except Exception as e:
            logger.error("Failed to fetch from NewsAPI", source=source.id, error=str(e))
            return []

    async def _fetch_nytimes(self, source: NewsSource, limit: int) -> List[NewsArticle]:
        """Fetch from New York Times API"""
        url = f"{source.base_url}/search/v2/articlesearch.json"
        params = {
            "sort": "newest",
            "page": 0,
            "page_size": min(limit, 10),  # NYTimes API limit
            "api-key": self._get_api_key("nytimes"),
        }

        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"NYTimes API returned status {response.status}")
                    return []

                data = await response.json()
                articles = []

                for doc in data.get("response", {}).get("docs", []):
                    article = NewsArticle(
                        id=f"nytimes_{doc['_id']}",
                        title=doc["headline"]["main"],
                        content=doc.get("abstract", doc.get("lead_paragraph", "")),
                        source=source.name,
                        url=doc["web_url"],
                        published_at=datetime.fromisoformat(doc["pub_date"]),
                        credibility_score=self._get_source_credibility(
                            source.credibility_tier
                        ),
                    )
                    articles.append(article)

                return articles

        except Exception as e:
            logger.error("Failed to fetch from NYTimes", error=str(e))
            return []

    async def _filter_by_credibility(
        self, articles: List[NewsArticle], threshold: float
    ) -> List[NewsArticle]:
        """
        Filter articles by credibility threshold
        Future: Integrate with existing FakeNewsDetectionService
        """
        credible_articles = [
            article for article in articles if article.credibility_score >= threshold
        ]

        logger.info(
            "Credibility filtering complete",
            original_count=len(articles),
            filtered_count=len(credible_articles),
            threshold=threshold,
        )

        return credible_articles

    def _get_source_credibility(self, tier: int) -> float:
        """Convert credibility tier to numeric score"""
        tier_scores = {
            1: 0.95,  # Tier 1: >95%
            2: 0.90,  # Tier 2: 85-95%
            3: 0.75,  # Tier 3: 70-85%
        }
        return tier_scores.get(tier, 0.70)

    def _get_api_key(self, service: str) -> str:
        """Get API key from environment"""
        keys = {
            "newsapi": os.getenv("NEWSAPI_KEY", "demo_key"),
            "nytimes": os.getenv("NYTIMES_API_KEY", "demo_key"),
        }
        return keys.get(service, "demo_key")

    async def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user reading preferences"""
        # Default preferences for now
        return {
            "topics": ["technology", "science", "politics"],
            "credibility_threshold": 0.8,
            "diversity_enabled": True,
            "reading_time_preference": "medium",
        }

    async def _get_user_reading_history(self, user_id: int) -> List[Dict]:
        """Get user's recent reading history for personalization"""
        # Placeholder for future implementation
        return []

    async def _apply_personalization(
        self,
        articles: List[NewsArticle],
        preferences: Dict[str, Any],
        reading_history: List[Dict],
        limit: int,
    ) -> List[NewsArticle]:
        """Apply basic personalization"""
        # Simple topic filtering for now
        preferred_topics = set(preferences.get("topics", []))

        if preferred_topics:
            # Score articles based on topic relevance
            scored_articles = []
            for article in articles:
                score = 0.5  # Base score

                # Check if any preferred topics appear in title or content
                text = f"{article.title} {article.content}".lower()
                for topic in preferred_topics:
                    if topic.lower() in text:
                        score += 0.2

                scored_articles.append((score, article))

            # Sort by score and return top articles
            scored_articles.sort(key=lambda x: x[0], reverse=True)
            return [article for _, article in scored_articles[:limit]]

        return articles[:limit]

    async def _inject_diversity(
        self, articles: List[NewsArticle], preferences: Dict[str, Any]
    ) -> List[NewsArticle]:
        """Inject diverse perspectives to prevent echo chambers"""
        # Mark some articles as diverse perspectives
        diversity_ratio = 0.15  # 15% diverse content
        num_diverse = max(1, int(len(articles) * diversity_ratio))

        # Simple implementation: mark last N articles as diverse
        for i in range(max(0, len(articles) - num_diverse), len(articles)):
            articles[i].diversity_tag = "alternative_perspective"

        return articles

    async def _get_fallback_feed(
        self, threshold: float, limit: int
    ) -> List[NewsArticle]:
        """Fallback feed when personalization fails"""
        try:
            return await self._fetch_trending_news(limit)
        except Exception as e:
            logger.error("Fallback feed generation failed", error=str(e))
            return []


async def get_sample_news_feed() -> List[NewsArticle]:
    """Sample function to demonstrate news engine"""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    # Create a temporary session (in production, use existing session)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with NewsIntelligenceEngine(session) as news_engine:
            articles = await news_engine.get_personalized_feed(
                user_id=1, credibility_threshold=0.8, limit=10
            )
            return articles


if __name__ == "__main__":
    # Test the news engine
    import asyncio

    async def test_engine():
        articles = await get_sample_news_feed()
        print(f"Retrieved {len(articles)} articles")
        for article in articles[:3]:
            print(
                f"- {article.title[:60]}... (Credibility: {article.credibility_score:.2f})"
            )

    asyncio.run(test_engine())

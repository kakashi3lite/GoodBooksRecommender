"""
Content Curation Microservice
Dedicated service for AI-powered content curation and generation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import aioredis
import aiohttp
import feedparser
import asyncio
from bs4 import BeautifulSoup
import openai
from textblob import TextBlob
import re

from .service_discovery import MicroserviceBase, ServiceType
from ..privacy.gdpr_compliance import get_privacy_engine, ConsentType, ProcessingPurpose

logger = logging.getLogger(__name__)

class CurationRequest(BaseModel):
    user_id: str
    content_sources: List[str] = []
    topics: List[str] = []
    content_types: List[str] = ["article", "book", "review"]
    max_items: int = 20
    freshness_hours: int = 24
    quality_threshold: float = 0.7

class CurationResponse(BaseModel):
    user_id: str
    curated_content: List[Dict[str, Any]]
    total_sources_checked: int
    content_quality_score: float
    curation_explanation: str
    generated_at: datetime

class ContentSource(BaseModel):
    source_id: str
    name: str
    url: str
    source_type: str  # rss, api, scraping
    reliability_score: float
    last_updated: datetime
    active: bool = True

class ContentItem(BaseModel):
    item_id: str
    title: str
    description: str
    content: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    author: Optional[str] = None
    tags: List[str] = []
    quality_score: float
    sentiment_score: float
    reading_time_minutes: int
    engagement_prediction: float

class ContentCurationMicroservice(MicroserviceBase):
    """Microservice for content curation and generation"""
    
    def __init__(self, host: str = "localhost", port: int = 8002):
        super().__init__(
            service_type=ServiceType.CONTENT_CURATION,
            host=host,
            port=port,
            version="1.0.0"
        )
        
        self.redis = None
        self.session = None
        self.content_sources: Dict[str, ContentSource] = {}
        self.quality_classifier = None
        self.content_cache: Dict[str, ContentItem] = {}
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.post("/curate", response_model=CurationResponse)
        async def curate_content(
            request: CurationRequest,
            background_tasks: BackgroundTasks
        ):
            return await self.curate_content(request, background_tasks)
        
        @self.app.get("/sources")
        async def get_content_sources():
            return await self.get_content_sources()
        
        @self.app.post("/sources")
        async def add_content_source(source_data: Dict[str, Any]):
            return await self.add_content_source(source_data)
        
        @self.app.post("/generate")
        async def generate_content(generation_request: Dict[str, Any]):
            return await self.generate_content(generation_request)
        
        @self.app.get("/trending")
        async def get_trending_topics():
            return await self.get_trending_topics()
        
        @self.app.post("/quality/analyze")
        async def analyze_content_quality(content: Dict[str, Any]):
            return await self.analyze_content_quality(content)
    
    async def startup(self):
        """Service startup with content source initialization"""
        await super().startup()
        
        try:
            # Initialize Redis and HTTP session
            self.redis = aioredis.from_url("redis://localhost:6379")
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=100)
            )
            
            # Load content sources
            await self.load_content_sources()
            
            # Initialize quality classifier
            await self.initialize_quality_models()
            
            # Start content polling task
            asyncio.create_task(self.start_content_polling())
            
            logger.info("Content curation service fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize curation service: {e}")
            raise
    
    async def shutdown(self):
        """Service shutdown"""
        if self.session:
            await self.session.close()
        await super().shutdown()
    
    async def load_content_sources(self):
        """Load content sources from configuration"""
        try:
            # Default book-related content sources
            default_sources = [
                {
                    "source_id": "goodreads_blog",
                    "name": "Goodreads Blog",
                    "url": "https://www.goodreads.com/blog.rss",
                    "source_type": "rss",
                    "reliability_score": 0.9
                },
                {
                    "source_id": "book_riot",
                    "name": "Book Riot",
                    "url": "https://bookriot.com/feed/",
                    "source_type": "rss",
                    "reliability_score": 0.85
                },
                {
                    "source_id": "literary_hub",
                    "name": "Literary Hub",
                    "url": "https://lithub.com/feed/",
                    "source_type": "rss",
                    "reliability_score": 0.9
                },
                {
                    "source_id": "publishers_weekly",
                    "name": "Publishers Weekly",
                    "url": "https://www.publishersweekly.com/pw/feeds/recent/index.xml",
                    "source_type": "rss",
                    "reliability_score": 0.95
                }
            ]
            
            # Load from Redis if available
            sources_data = await self.redis.hgetall("content_sources")
            
            if sources_data:
                for source_id, data in sources_data.items():
                    source_dict = eval(data.decode())
                    source = ContentSource(**source_dict)
                    self.content_sources[source_id.decode()] = source
            else:
                # Initialize with default sources
                for source_data in default_sources:
                    source = ContentSource(
                        **source_data,
                        last_updated=datetime.utcnow()
                    )
                    self.content_sources[source.source_id] = source
                    
                    # Save to Redis
                    await self.redis.hset(
                        "content_sources",
                        source.source_id,
                        str(source_data)
                    )
            
            logger.info(f"Loaded {len(self.content_sources)} content sources")
            
        except Exception as e:
            logger.error(f"Failed to load content sources: {e}")
    
    async def initialize_quality_models(self):
        """Initialize content quality assessment models"""
        try:
            # Initialize simple quality assessment
            # In production, this would load trained ML models
            self.quality_classifier = {
                "min_word_count": 50,
                "max_word_count": 5000,
                "quality_keywords": [
                    "review", "analysis", "critique", "recommendation",
                    "author", "book", "novel", "story", "character",
                    "plot", "writing", "style", "genre", "literature"
                ],
                "spam_keywords": [
                    "click here", "buy now", "limited time", "free",
                    "amazing deal", "must read this", "you won't believe"
                ]
            }
            
            logger.info("Quality assessment models initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize quality models: {e}")
    
    async def curate_content(
        self,
        request: CurationRequest,
        background_tasks: BackgroundTasks
    ) -> CurationResponse:
        """Curate content for a user"""
        try:
            # Check privacy consent
            privacy_engine = get_privacy_engine()
            can_curate = await privacy_engine.check_consent(
                request.user_id,
                ConsentType.PERSONALIZATION,
                ProcessingPurpose.CONTENT_CURATION
            )
            
            if not can_curate:
                # Return basic, non-personalized content
                basic_content = await self.get_basic_content(request)
                return CurationResponse(
                    user_id=request.user_id,
                    curated_content=basic_content,
                    total_sources_checked=len(self.content_sources),
                    content_quality_score=0.7,
                    curation_explanation="Basic content curation without personalization",
                    generated_at=datetime.utcnow()
                )
            
            # Fetch fresh content from sources
            fresh_content = await self.fetch_fresh_content(
                request.freshness_hours,
                request.content_types
            )
            
            # Filter by topics if specified
            if request.topics:
                fresh_content = await self.filter_by_topics(fresh_content, request.topics)
            
            # Apply quality filtering
            quality_content = await self.filter_by_quality(
                fresh_content,
                request.quality_threshold
            )
            
            # Personalize based on user preferences
            personalized_content = await self.personalize_content(
                request.user_id,
                quality_content,
                request.max_items
            )
            
            # Calculate overall quality score
            quality_score = np.mean([item.quality_score for item in personalized_content]) if personalized_content else 0.0
            
            # Convert to response format
            curated_items = [self.content_item_to_dict(item) for item in personalized_content]
            
            # Record curation for analytics
            background_tasks.add_task(
                self.record_curation_analytics,
                request.user_id,
                len(fresh_content),
                len(curated_items),
                quality_score
            )
            
            return CurationResponse(
                user_id=request.user_id,
                curated_content=curated_items,
                total_sources_checked=len(self.content_sources),
                content_quality_score=quality_score,
                curation_explanation=f"Curated {len(curated_items)} high-quality items from {len(fresh_content)} candidates",
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Content curation failed: {e}")
            raise HTTPException(status_code=500, detail="Content curation service error")
    
    async def fetch_fresh_content(
        self,
        freshness_hours: int,
        content_types: List[str]
    ) -> List[ContentItem]:
        """Fetch fresh content from all sources"""
        try:
            all_content = []
            cutoff_time = datetime.utcnow() - timedelta(hours=freshness_hours)
            
            # Fetch from each active source
            for source in self.content_sources.values():
                if not source.active:
                    continue
                
                try:
                    if source.source_type == "rss":
                        content_items = await self.fetch_rss_content(source, cutoff_time)
                    elif source.source_type == "api":
                        content_items = await self.fetch_api_content(source, cutoff_time)
                    elif source.source_type == "scraping":
                        content_items = await self.fetch_scraped_content(source, cutoff_time)
                    else:
                        continue
                    
                    all_content.extend(content_items)
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch from {source.name}: {e}")
                    continue
            
            # Remove duplicates based on title similarity
            unique_content = await self.deduplicate_content(all_content)
            
            logger.info(f"Fetched {len(unique_content)} unique content items from {len(self.content_sources)} sources")
            return unique_content
            
        except Exception as e:
            logger.error(f"Failed to fetch fresh content: {e}")
            return []
    
    async def fetch_rss_content(
        self,
        source: ContentSource,
        cutoff_time: datetime
    ) -> List[ContentItem]:
        """Fetch content from RSS feed"""
        try:
            async with self.session.get(source.url) as response:
                if response.status != 200:
                    return []
                
                rss_text = await response.text()
            
            # Parse RSS feed
            feed = feedparser.parse(rss_text)
            content_items = []
            
            for entry in feed.entries:
                try:
                    # Parse published date
                    published_at = datetime.fromtimestamp(
                        feedparser._parse_date(entry.get('published', ''))
                    ) if entry.get('published') else datetime.utcnow()
                    
                    # Skip old content
                    if published_at < cutoff_time:
                        continue
                    
                    # Extract content
                    description = entry.get('summary', entry.get('description', ''))
                    content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
                    
                    # Clean HTML
                    description = self.clean_html(description)
                    content = self.clean_html(content)
                    
                    # Calculate quality score
                    quality_score = await self.calculate_quality_score(
                        entry.get('title', ''),
                        description,
                        content
                    )
                    
                    # Create content item
                    item = ContentItem(
                        item_id=f"{source.source_id}_{hash(entry.get('link', ''))}",
                        title=entry.get('title', 'Untitled'),
                        description=description,
                        content=content,
                        source=source.name,
                        url=entry.get('link', ''),
                        published_at=published_at,
                        author=entry.get('author', ''),
                        tags=self.extract_tags(description + ' ' + content),
                        quality_score=quality_score,
                        sentiment_score=self.calculate_sentiment(description),
                        reading_time_minutes=self.estimate_reading_time(content or description),
                        engagement_prediction=self.predict_engagement(entry.get('title', ''), description)
                    )
                    
                    content_items.append(item)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse RSS entry: {e}")
                    continue
            
            return content_items
            
        except Exception as e:
            logger.error(f"Failed to fetch RSS content from {source.url}: {e}")
            return []
    
    async def fetch_api_content(
        self,
        source: ContentSource,
        cutoff_time: datetime
    ) -> List[ContentItem]:
        """Fetch content from API source"""
        # Placeholder for API-based content sources
        # Would implement specific API integrations (e.g., Goodreads API, NYT Books API)
        return []
    
    async def fetch_scraped_content(
        self,
        source: ContentSource,
        cutoff_time: datetime
    ) -> List[ContentItem]:
        """Fetch content via web scraping"""
        # Placeholder for web scraping
        # Would implement ethical web scraping with rate limiting
        return []
    
    async def deduplicate_content(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """Remove duplicate content based on title similarity"""
        try:
            if not content_items:
                return []
            
            unique_items = []
            seen_titles = set()
            
            for item in content_items:
                # Simple deduplication based on normalized title
                normalized_title = re.sub(r'[^\w\s]', '', item.title.lower())
                title_words = set(normalized_title.split())
                
                # Check for similar titles
                is_duplicate = False
                for seen_title in seen_titles:
                    seen_words = set(seen_title.split())
                    similarity = len(title_words & seen_words) / len(title_words | seen_words)
                    
                    if similarity > 0.8:  # 80% similarity threshold
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_items.append(item)
                    seen_titles.add(normalized_title)
            
            return unique_items
            
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
            return content_items
    
    async def filter_by_topics(
        self,
        content_items: List[ContentItem],
        topics: List[str]
    ) -> List[ContentItem]:
        """Filter content by specified topics"""
        try:
            filtered_items = []
            topic_keywords = [topic.lower() for topic in topics]
            
            for item in content_items:
                item_text = f"{item.title} {item.description} {' '.join(item.tags)}".lower()
                
                # Check if any topic keywords are present
                if any(keyword in item_text for keyword in topic_keywords):
                    filtered_items.append(item)
            
            return filtered_items
            
        except Exception as e:
            logger.error(f"Topic filtering failed: {e}")
            return content_items
    
    async def filter_by_quality(
        self,
        content_items: List[ContentItem],
        quality_threshold: float
    ) -> List[ContentItem]:
        """Filter content by quality score"""
        return [item for item in content_items if item.quality_score >= quality_threshold]
    
    async def personalize_content(
        self,
        user_id: str,
        content_items: List[ContentItem],
        max_items: int
    ) -> List[ContentItem]:
        """Personalize content selection for user"""
        try:
            # For now, sort by quality and engagement prediction
            # In production, would use personalization microservice
            
            # Score items based on quality, freshness, and predicted engagement
            scored_items = []
            for item in content_items:
                # Calculate composite score
                freshness_score = self.calculate_freshness_score(item.published_at)
                composite_score = (
                    item.quality_score * 0.4 +
                    item.engagement_prediction * 0.3 +
                    freshness_score * 0.2 +
                    abs(item.sentiment_score) * 0.1  # Prefer strong sentiment
                )
                
                scored_items.append((composite_score, item))
            
            # Sort by composite score and take top items
            scored_items.sort(reverse=True)
            return [item for _, item in scored_items[:max_items]]
            
        except Exception as e:
            logger.error(f"Content personalization failed: {e}")
            return content_items[:max_items]
    
    def calculate_freshness_score(self, published_at: datetime) -> float:
        """Calculate freshness score (0-1, newer is higher)"""
        hours_old = (datetime.utcnow() - published_at).total_seconds() / 3600
        return max(0.0, 1.0 - (hours_old / 168))  # Decay over 1 week
    
    async def calculate_quality_score(
        self,
        title: str,
        description: str,
        content: str
    ) -> float:
        """Calculate content quality score"""
        try:
            score = 0.5  # Base score
            
            # Check word count
            word_count = len((description + ' ' + content).split())
            if self.quality_classifier["min_word_count"] <= word_count <= self.quality_classifier["max_word_count"]:
                score += 0.2
            
            # Check for quality keywords
            text_lower = (title + ' ' + description + ' ' + content).lower()
            quality_matches = sum(1 for kw in self.quality_classifier["quality_keywords"] if kw in text_lower)
            score += min(0.3, quality_matches * 0.05)
            
            # Penalize spam keywords
            spam_matches = sum(1 for kw in self.quality_classifier["spam_keywords"] if kw in text_lower)
            score -= spam_matches * 0.1
            
            # Check title quality
            if title and len(title.split()) >= 3 and not title.isupper():
                score += 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Quality score calculation failed: {e}")
            return 0.5
    
    def calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score (-1 to 1)"""
        try:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def estimate_reading_time(self, text: str) -> int:
        """Estimate reading time in minutes"""
        word_count = len(text.split())
        return max(1, word_count // 200)  # Assume 200 words per minute
    
    def predict_engagement(self, title: str, description: str) -> float:
        """Predict engagement potential (0-1)"""
        try:
            engagement_signals = [
                "how to", "why", "best", "top", "review", "guide",
                "amazing", "incredible", "must-read", "essential"
            ]
            
            text = (title + ' ' + description).lower()
            signal_count = sum(1 for signal in engagement_signals if signal in text)
            
            # Base prediction on signal presence and text length
            base_score = min(0.8, signal_count * 0.15)
            length_bonus = min(0.2, len(description) / 1000)  # Longer descriptions tend to engage more
            
            return min(1.0, base_score + length_bonus)
            
        except Exception as e:
            return 0.5
    
    def extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text"""
        try:
            # Simple keyword extraction
            book_related_terms = [
                "fiction", "non-fiction", "mystery", "romance", "thriller",
                "fantasy", "sci-fi", "biography", "memoir", "history",
                "novel", "author", "bestseller", "award", "review"
            ]
            
            text_lower = text.lower()
            found_tags = [term for term in book_related_terms if term in text_lower]
            
            return found_tags[:5]  # Limit to 5 tags
            
        except Exception as e:
            return []
    
    def clean_html(self, html_text: str) -> str:
        """Clean HTML from text"""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            return soup.get_text().strip()
        except:
            return html_text
    
    def content_item_to_dict(self, item: ContentItem) -> Dict[str, Any]:
        """Convert ContentItem to dictionary"""
        return {
            "id": item.item_id,
            "title": item.title,
            "description": item.description,
            "content": item.content,
            "source": item.source,
            "url": item.url,
            "published_at": item.published_at.isoformat(),
            "author": item.author,
            "tags": item.tags,
            "quality_score": item.quality_score,
            "sentiment_score": item.sentiment_score,
            "reading_time_minutes": item.reading_time_minutes,
            "engagement_prediction": item.engagement_prediction
        }
    
    async def get_basic_content(self, request: CurationRequest) -> List[Dict[str, Any]]:
        """Get basic content without personalization"""
        try:
            # Get cached content or fetch generic content
            cache_key = f"basic_content:{request.content_types}:{request.freshness_hours}"
            cached = await self.redis.get(cache_key)
            
            if cached:
                return eval(cached.decode())
            
            # Fetch and cache basic content
            fresh_content = await self.fetch_fresh_content(
                request.freshness_hours,
                request.content_types
            )
            
            quality_content = await self.filter_by_quality(fresh_content, 0.5)
            basic_items = [self.content_item_to_dict(item) for item in quality_content[:request.max_items]]
            
            # Cache for 30 minutes
            await self.redis.setex(cache_key, 1800, str(basic_items))
            
            return basic_items
            
        except Exception as e:
            logger.error(f"Failed to get basic content: {e}")
            return []
    
    async def start_content_polling(self):
        """Start background task to continuously poll content sources"""
        async def polling_task():
            while True:
                try:
                    # Poll every 30 minutes
                    await asyncio.sleep(1800)
                    
                    # Update content from all sources
                    fresh_content = await self.fetch_fresh_content(24, ["article", "book", "review"])
                    
                    # Cache fresh content
                    if fresh_content:
                        cached_items = [self.content_item_to_dict(item) for item in fresh_content]
                        await self.redis.setex("latest_content", 3600, str(cached_items))
                    
                    logger.info(f"Content polling completed: {len(fresh_content)} items")
                    
                except Exception as e:
                    logger.error(f"Content polling error: {e}")
        
        asyncio.create_task(polling_task())
    
    async def record_curation_analytics(
        self,
        user_id: str,
        total_candidates: int,
        curated_count: int,
        quality_score: float
    ):
        """Record curation analytics"""
        try:
            analytics_data = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "total_candidates": total_candidates,
                "curated_count": curated_count,
                "quality_score": quality_score,
                "selection_ratio": curated_count / max(1, total_candidates)
            }
            
            await self.redis.lpush("curation_analytics", str(analytics_data))
            await self.redis.ltrim("curation_analytics", 0, 9999)  # Keep last 10k records
            
        except Exception as e:
            logger.error(f"Failed to record curation analytics: {e}")
    
    # API endpoint implementations
    async def get_content_sources(self) -> Dict[str, Any]:
        """Get all content sources"""
        sources = []
        for source in self.content_sources.values():
            sources.append({
                "source_id": source.source_id,
                "name": source.name,
                "url": source.url,
                "source_type": source.source_type,
                "reliability_score": source.reliability_score,
                "last_updated": source.last_updated.isoformat(),
                "active": source.active
            })
        
        return {"sources": sources, "total": len(sources)}
    
    async def add_content_source(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new content source"""
        try:
            source = ContentSource(
                source_id=source_data["source_id"],
                name=source_data["name"],
                url=source_data["url"],
                source_type=source_data["source_type"],
                reliability_score=source_data.get("reliability_score", 0.7),
                last_updated=datetime.utcnow(),
                active=source_data.get("active", True)
            )
            
            self.content_sources[source.source_id] = source
            
            # Save to Redis
            await self.redis.hset("content_sources", source.source_id, str(source_data))
            
            return {"status": "added", "source_id": source.source_id}
            
        except Exception as e:
            logger.error(f"Failed to add content source: {e}")
            raise HTTPException(status_code=500, detail="Failed to add source")
    
    async def generate_content(self, generation_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using AI"""
        # Placeholder for AI content generation
        # Would implement OpenAI integration for content creation
        return {
            "status": "generated",
            "content": {
                "title": "AI-Generated Content",
                "description": "This would be AI-generated content based on the request",
                "generated_at": datetime.utcnow().isoformat()
            }
        }
    
    async def get_trending_topics(self) -> Dict[str, Any]:
        """Get trending topics from recent content"""
        try:
            # Analyze recent content for trending topics
            recent_content = await self.redis.get("latest_content")
            
            if not recent_content:
                return {"topics": [], "timestamp": datetime.utcnow().isoformat()}
            
            content_items = eval(recent_content.decode())
            
            # Extract and count tags
            tag_counts = {}
            for item in content_items:
                for tag in item.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by frequency
            trending = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "topics": [{"topic": topic, "count": count} for topic, count in trending],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {e}")
            return {"topics": [], "error": "Failed to analyze trends"}
    
    async def analyze_content_quality(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content quality"""
        try:
            quality_score = await self.calculate_quality_score(
                content.get("title", ""),
                content.get("description", ""),
                content.get("content", "")
            )
            
            sentiment_score = self.calculate_sentiment(content.get("description", ""))
            reading_time = self.estimate_reading_time(content.get("content", ""))
            engagement_prediction = self.predict_engagement(
                content.get("title", ""),
                content.get("description", "")
            )
            
            return {
                "quality_score": quality_score,
                "sentiment_score": sentiment_score,
                "reading_time_minutes": reading_time,
                "engagement_prediction": engagement_prediction,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Content quality analysis failed: {e}")
            raise HTTPException(status_code=500, detail="Quality analysis failed")
    
    async def get_load_factor(self) -> float:
        """Get current service load"""
        # Simple implementation based on cache size and active sources
        cache_size = len(self.content_cache)
        active_sources = sum(1 for s in self.content_sources.values() if s.active)
        return min(1.0, (cache_size / 1000) + (active_sources / 20))
    
    async def get_service_metadata(self) -> Dict[str, Any]:
        """Get service metadata"""
        return {
            "capabilities": [
                "rss_content_fetching",
                "content_quality_assessment",
                "content_deduplication",
                "topic_filtering",
                "sentiment_analysis",
                "trending_topics",
                "ai_content_generation"
            ],
            "dependencies": ["redis", "aiohttp", "feedparser", "beautifulsoup4", "textblob"],
            "configuration": {
                "max_content_cache": 1000,
                "polling_interval_minutes": 30,
                "supported_source_types": ["rss", "api", "scraping"],
                "quality_threshold_range": [0.0, 1.0]
            }
        }

# Entry point for running the service
if __name__ == "__main__":
    import uvicorn
    
    service = ContentCurationMicroservice(port=8002)
    uvicorn.run(service.app, host="0.0.0.0", port=8002)

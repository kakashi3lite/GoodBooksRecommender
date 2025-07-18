"""
🔍 News Expansion API - MVP Implementation
Senior Lead Engineer Architecture: Expandable news with AI-powered fact hunting
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.news.core.intelligence_engine import NewsArticle, NewsIntelligenceEngine
from src.news.services.fact_hunter import FactHunterEngine
from src.news.services.context_book_recommender import ContextBookRecommender

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["News Expansion"])
cache_manager = AsyncCacheManager()

# MVP Request/Response Models
class NewsExpansionRequest(BaseModel):
    """Request to expand a news story"""
    article_id: Optional[str] = Field(None, description="Article ID to expand")
    article_url: Optional[str] = Field(None, description="Article URL to expand")
    summary_level: str = Field("standard", regex="^(brief|standard|detailed)$")
    include_facts: bool = Field(True, description="Include fact checking")
    include_books: bool = Field(True, description="Include book recommendations")
    include_related: bool = Field(True, description="Include related articles")
    
    @validator('article_id', 'article_url')
    def at_least_one_required(cls, v, values):
        if not v and not values.get('article_url') and not values.get('article_id'):
            raise ValueError('Either article_id or article_url must be provided')
        return v

class FactCheck(BaseModel):
    """Individual fact check result"""
    claim: str = Field(..., description="The claim being verified")
    verdict: str = Field(..., description="True/False/Unverified/Mixed")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    sources: List[str] = Field(default=[], description="Source URLs")
    explanation: str = Field(..., description="Brief explanation")

class BookRecommendation(BaseModel):
    """Context-aware book recommendation"""
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Primary author")
    description: str = Field(..., description="Brief description")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance to article")
    topics_matched: List[str] = Field(default=[], description="Matched topics")
    buy_url: Optional[str] = Field(None, description="Purchase link")
    cover_url: Optional[str] = Field(None, description="Cover image URL")

class RelatedArticle(BaseModel):
    """Related article information"""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="Source publication")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score")
    published_at: Optional[datetime] = Field(None, description="Publication date")

class NewsExpansionResponse(BaseModel):
    """Complete expanded news story"""
    article_id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Article title")
    summary: str = Field(..., description="AI-generated summary")
    topics: List[str] = Field(default=[], description="Extracted topics")
    sentiment: str = Field(..., description="Overall sentiment")
    credibility_score: float = Field(..., ge=0, le=1, description="Credibility assessment")
    
    # Expansion components
    fact_checks: List[FactCheck] = Field(default=[], description="Fact verification results")
    book_recommendations: List[BookRecommendation] = Field(default=[], description="Relevant books")
    related_articles: List[RelatedArticle] = Field(default=[], description="Related news")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Total processing time")
    expanded_at: datetime = Field(default_factory=datetime.now)
    cache_hit: bool = Field(False, description="Whether result was cached")

@router.post("/expand", response_model=NewsExpansionResponse, summary="Expand news story with AI analysis")
async def expand_news_story(
    request: NewsExpansionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Expand a news story with:
    - AI-powered summary and analysis
    - Fact checking with source verification
    - Context-aware book recommendations
    - Related articles discovery
    """
    start_time = datetime.now()
    
    try:
        # Generate cache key
        cache_key = f"news_expansion:{request.article_id or hash(request.article_url)}:{request.summary_level}"
        
        # Check cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            logger.info("News expansion cache hit", cache_key=cache_key)
            cached_result['cache_hit'] = True
            return NewsExpansionResponse(**cached_result)
        
        # Initialize AI engines
        fact_hunter = FactHunterEngine()
        book_recommender = ContextBookRecommender()
        news_engine = NewsIntelligenceEngine(db)
        
        # Get or fetch article
        if request.article_id:
            article = await news_engine.get_article_by_id(request.article_id)
        else:
            article = await news_engine.fetch_article_from_url(request.article_url)
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found or could not be fetched")
        
        # Extract topics and sentiment
        topics = await news_engine.extract_topics(article.content)
        sentiment = await news_engine.analyze_sentiment(article.content)
        
        # Generate enhanced summary
        summary_length_mapping = {
            "brief": "2-3 sentences",
            "standard": "1-2 paragraphs", 
            "detailed": "3-4 paragraphs"
        }
        summary = await news_engine.generate_summary(
            article.content, 
            length=summary_length_mapping[request.summary_level]
        )
        
        # Parallel processing for expansion components
        expansion_tasks = []
        fact_checks = []
        book_recommendations = []
        related_articles = []
        
        # Fact checking
        if request.include_facts:
            expansion_tasks.append(
                fact_hunter.verify_claims(article.content, article.title)
            )
        
        # Book recommendations
        if request.include_books:
            expansion_tasks.append(
                book_recommender.get_context_recommendations(
                    topics=topics,
                    article_content=article.content[:1000],  # First 1000 chars for context
                    n_recommendations=5
                )
            )
        
        # Related articles
        if request.include_related:
            expansion_tasks.append(
                news_engine.find_related_articles(
                    article_content=article.content,
                    topics=topics,
                    limit=5
                )
            )
        
        # Execute all expansion tasks in parallel
        if expansion_tasks:
            import asyncio
            results = await asyncio.gather(*expansion_tasks, return_exceptions=True)
            
            result_index = 0
            if request.include_facts:
                if not isinstance(results[result_index], Exception):
                    fact_checks = results[result_index]
                result_index += 1
            
            if request.include_books:
                if not isinstance(results[result_index], Exception):
                    book_recommendations = results[result_index]
                result_index += 1
            
            if request.include_related:
                if not isinstance(results[result_index], Exception):
                    related_articles = results[result_index]
        
        # Build response
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        expansion_result = {
            "article_id": article.id,
            "title": article.title,
            "summary": summary,
            "topics": topics,
            "sentiment": sentiment,
            "credibility_score": article.credibility_score or 0.8,
            "fact_checks": fact_checks,
            "book_recommendations": book_recommendations,
            "related_articles": related_articles,
            "processing_time_ms": processing_time,
            "expanded_at": datetime.now(),
            "cache_hit": False
        }
        
        # Cache the result for 30 minutes
        await cache_manager.set(cache_key, expansion_result, ttl=1800)
        
        # Log analytics
        logger.info(
            "News expansion completed",
            article_id=article.id,
            processing_time_ms=processing_time,
            topics_found=len(topics),
            facts_checked=len(fact_checks),
            books_recommended=len(book_recommendations),
            related_found=len(related_articles)
        )
        
        return NewsExpansionResponse(**expansion_result)
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(
            "News expansion failed",
            error=str(e),
            processing_time_ms=processing_time,
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to expand news story: {str(e)}"
        )

@router.get("/stories/trending", response_model=List[NewsExpansionResponse], summary="Get trending expandable stories")
async def get_trending_expandable_stories(
    limit: int = Query(10, ge=1, le=50, description="Number of stories to return"),
    category: Optional[str] = Query(None, description="News category filter"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get trending news stories optimized for expansion"""
    try:
        news_engine = NewsIntelligenceEngine(db)
        articles = await news_engine.get_trending_articles(
            limit=limit,
            category=category,
            time_window_hours=24
        )
        
        # Convert to lightweight expansion previews
        expanded_stories = []
        for article in articles:
            preview = {
                "article_id": article.id,
                "title": article.title,
                "summary": article.summary or article.content[:200] + "...",
                "topics": await news_engine.extract_topics(article.content[:500]),
                "sentiment": "neutral",  # Quick sentiment for preview
                "credibility_score": article.credibility_score or 0.8,
                "fact_checks": [],
                "book_recommendations": [],
                "related_articles": [],
                "processing_time_ms": 0,
                "expanded_at": datetime.now(),
                "cache_hit": False
            }
            expanded_stories.append(NewsExpansionResponse(**preview))
        
        logger.info(
            "Trending expandable stories fetched",
            count=len(expanded_stories),
            category=category
        )
        
        return expanded_stories
        
    except Exception as e:
        logger.error("Failed to fetch trending stories", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trending stories: {str(e)}"
        )

@router.get("/expand/{article_id}", response_model=NewsExpansionResponse, summary="Quick expand by article ID")
async def quick_expand_article(
    article_id: str,
    include_facts: bool = Query(True, description="Include fact checking"),
    include_books: bool = Query(True, description="Include book recommendations"),
    db: AsyncSession = Depends(get_async_session)
):
    """Quick expansion endpoint for single article"""
    request = NewsExpansionRequest(
        article_id=article_id,
        summary_level="standard",
        include_facts=include_facts,
        include_books=include_books,
        include_related=True
    )
    
    return await expand_news_story(request, BackgroundTasks(), db)

# Include this router in the main application
def include_expansion_routes(app):
    """Include news expansion routes in FastAPI app"""
    app.include_router(router)

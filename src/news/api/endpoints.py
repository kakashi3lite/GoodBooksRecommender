"""
FastAPI endpoints for AI News Intelligence Engine
Production-ready API with comprehensive error handling and monitoring
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.core.logging import StructuredLogger
from src.news.ai.summarization import AISummarizationPipeline, SummaryLength
from src.news.core.intelligence_engine import NewsArticle, NewsIntelligenceEngine
from src.news.personalization.recommender import HybridNewsRecommender

logger = StructuredLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["News Intelligence"])


# Request/Response Models
class NewsArticleResponse(BaseModel):
    """Response model for news articles"""

    id: str
    title: str
    content: str
    summary: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    credibility_score: float = Field(
        ..., ge=0, le=1, description="Credibility score (0-1)"
    )
    bias_rating: Optional[str] = None
    topics: List[str] = []
    reading_time_minutes: int = Field(..., ge=1, description="Estimated reading time")
    diversity_tag: Optional[str] = None

    class Config:
        from_attributes = True


class PersonalizedFeedRequest(BaseModel):
    """Request model for personalized news feed"""

    user_id: Optional[int] = Field(
        None, gt=0, description="User ID for personalization"
    )
    credibility_threshold: float = Field(
        0.8, ge=0.5, le=1.0, description="Minimum credibility score"
    )
    diversity_enabled: bool = Field(
        True, description="Enable diverse content injection"
    )
    limit: int = Field(20, ge=1, le=100, description="Number of articles to return")
    topics: Optional[List[str]] = Field(None, description="Preferred topics filter")

    @validator("topics")
    def validate_topics(cls, v):
        if v:
            allowed_topics = [
                "technology",
                "science",
                "politics",
                "business",
                "health",
                "environment",
                "sports",
                "entertainment",
            ]
            for topic in v:
                if topic.lower() not in allowed_topics:
                    raise ValueError(
                        f"Invalid topic: {topic}. Allowed: {allowed_topics}"
                    )
        return v


class PersonalizedFeedResponse(BaseModel):
    """Response model for personalized news feed"""

    articles: List[NewsArticleResponse]
    total_count: int
    processing_time_ms: float
    personalization_applied: bool
    diversity_injected: bool
    filters_applied: Dict[str, Any]


class SummarizationRequest(BaseModel):
    """Request model for article summarization"""

    article_ids: List[str] = Field(
        ..., min_items=1, max_items=50, description="Article IDs to summarize"
    )
    summary_length: str = Field(
        "standard", description="Summary length: brief, standard, detailed"
    )
    include_bias_detection: bool = Field(True, description="Include bias analysis")
    include_fact_checking: bool = Field(True, description="Include fact checking")

    @validator("summary_length")
    def validate_summary_length(cls, v):
        if v not in ["brief", "standard", "detailed"]:
            raise ValueError("summary_length must be one of: brief, standard, detailed")
        return v


class TrendingTopicsResponse(BaseModel):
    """Response model for trending topics"""

    topics: List[Dict[str, Any]]
    generated_at: datetime
    time_window_hours: int


class SearchRequest(BaseModel):
    """Request model for intelligent search"""

    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    credibility_threshold: float = Field(0.8, ge=0.5, le=1.0)
    max_results: int = Field(20, ge=1, le=100)
    include_summaries: bool = Field(True, description="Include AI summaries in results")


# API Endpoints
@router.get("/health", summary="Health check for news intelligence system")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI News Intelligence Engine",
        "timestamp": datetime.now(),
        "version": "1.0.0",
    }


@router.post(
    "/feed/personalized",
    response_model=PersonalizedFeedResponse,
    summary="Get personalized news feed",
)
async def get_personalized_feed(
    request: PersonalizedFeedRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get personalized news feed with AI-powered content curation

    - **user_id**: Optional user ID for personalization
    - **credibility_threshold**: Minimum credibility score (0.5-1.0)
    - **diversity_enabled**: Whether to inject diverse perspectives
    - **limit**: Number of articles to return (1-100)
    - **topics**: Optional topic filters
    """
    start_time = datetime.now()

    try:
        # Initialize news intelligence engine
        async with NewsIntelligenceEngine(db) as engine:

            # Get personalized feed
            articles = await engine.get_personalized_feed(
                user_id=request.user_id or 0,  # Anonymous user if no ID
                credibility_threshold=request.credibility_threshold,
                diversity_enabled=request.diversity_enabled,
                limit=request.limit,
            )

            # Apply topic filters if specified
            if request.topics:
                filtered_articles = []
                for article in articles:
                    article_text = f"{article.title} {article.content}".lower()
                    if any(topic.lower() in article_text for topic in request.topics):
                        filtered_articles.append(article)
                articles = filtered_articles

            # Generate summaries in background if needed
            if articles:
                background_tasks.add_task(
                    _generate_summaries_background,
                    [a for a in articles if not a.summary],
                    db,
                )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Log analytics
            logger.info(
                "Personalized feed delivered",
                user_id=request.user_id,
                articles_returned=len(articles),
                processing_time_ms=processing_time,
                credibility_threshold=request.credibility_threshold,
            )

            return PersonalizedFeedResponse(
                articles=[
                    NewsArticleResponse.from_orm(article) for article in articles
                ],
                total_count=len(articles),
                processing_time_ms=processing_time,
                personalization_applied=bool(request.user_id),
                diversity_injected=request.diversity_enabled,
                filters_applied={
                    "credibility_threshold": request.credibility_threshold,
                    "topics": request.topics or [],
                    "diversity_enabled": request.diversity_enabled,
                },
            )

    except Exception as e:
        logger.error(
            "Personalized feed generation failed",
            user_id=request.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate personalized feed: {str(e)}"
        )


@router.post("/summarize", summary="Generate AI summaries for articles")
async def summarize_articles(
    request: SummarizationRequest, db: AsyncSession = Depends(get_async_session)
):
    """
    Generate AI-powered summaries for news articles

    - **article_ids**: List of article IDs to summarize (1-50)
    - **summary_length**: Length preference (brief/standard/detailed)
    - **include_bias_detection**: Whether to include bias analysis
    - **include_fact_checking**: Whether to include fact checking
    """
    start_time = datetime.now()

    try:
        # Get articles from IDs (simplified - in production would query database)
        async with NewsIntelligenceEngine(db) as engine:
            # For demo, we'll use sample articles
            # In production, this would query articles by IDs
            sample_articles = await engine._fetch_trending_news(
                len(request.article_ids)
            )

            # Map summary length
            length_mapping = {
                "brief": SummaryLength.BRIEF,
                "standard": SummaryLength.STANDARD,
                "detailed": SummaryLength.DETAILED,
            }

            # Generate summaries
            async with AISummarizationPipeline() as summarizer:
                summarized_articles = await summarizer.summarize_articles(
                    sample_articles[: len(request.article_ids)],
                    length=length_mapping[request.summary_length],
                    include_bias_detection=request.include_bias_detection,
                    include_fact_checking=request.include_fact_checking,
                )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                "Articles summarized",
                article_count=len(summarized_articles),
                processing_time_ms=processing_time,
                summary_length=request.summary_length,
            )

            return {
                "articles": [
                    NewsArticleResponse.from_orm(article)
                    for article in summarized_articles
                ],
                "processing_time_ms": processing_time,
                "summary_length": request.summary_length,
                "bias_detection_enabled": request.include_bias_detection,
                "fact_checking_enabled": request.include_fact_checking,
            }

    except Exception as e:
        logger.error(
            "Article summarization failed",
            article_ids=request.article_ids,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.get(
    "/trending",
    response_model=TrendingTopicsResponse,
    summary="Get trending news topics",
)
async def get_trending_topics(
    time_window_hours: int = Query(
        24, ge=1, le=168, description="Time window in hours"
    ),
    min_credibility: float = Query(
        0.8, ge=0.5, le=1.0, description="Minimum credibility threshold"
    ),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get trending news topics based on article volume and credibility

    - **time_window_hours**: Time window for trend analysis (1-168 hours)
    - **min_credibility**: Minimum credibility score for included articles
    """
    try:
        async with NewsIntelligenceEngine(db) as engine:
            # Get recent articles
            articles = await engine._fetch_trending_news(100)

            # Filter by credibility
            credible_articles = [
                a for a in articles if a.credibility_score >= min_credibility
            ]

            # Simple topic extraction (in production, would use NLP)
            topic_counts = {}
            for article in credible_articles:
                text = f"{article.title} {article.content}".lower()

                # Simple keyword-based topic detection
                topics = {
                    "technology": [
                        "ai",
                        "artificial intelligence",
                        "tech",
                        "software",
                        "digital",
                    ],
                    "politics": [
                        "government",
                        "election",
                        "policy",
                        "congress",
                        "president",
                    ],
                    "science": [
                        "research",
                        "study",
                        "scientists",
                        "discovery",
                        "medicine",
                    ],
                    "business": [
                        "economy",
                        "market",
                        "company",
                        "financial",
                        "business",
                    ],
                    "climate": [
                        "climate",
                        "environment",
                        "carbon",
                        "sustainability",
                        "green",
                    ],
                }

                for topic, keywords in topics.items():
                    if any(keyword in text for keyword in keywords):
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1

            # Format trending topics
            trending_topics = [
                {
                    "topic": topic,
                    "article_count": count,
                    "trend_score": (
                        count / len(credible_articles) if credible_articles else 0
                    ),
                    "avg_credibility": min_credibility,  # Simplified
                }
                for topic, count in sorted(
                    topic_counts.items(), key=lambda x: x[1], reverse=True
                )
            ]

            return TrendingTopicsResponse(
                topics=trending_topics[:10],  # Top 10 trending topics
                generated_at=datetime.now(),
                time_window_hours=time_window_hours,
            )

    except Exception as e:
        logger.error(f"Trending topics generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get trending topics: {str(e)}"
        )


@router.post("/search", summary="Intelligent news search")
async def intelligent_search(
    request: SearchRequest, db: AsyncSession = Depends(get_async_session)
):
    """
    Intelligent news search with AI-powered relevance ranking

    - **query**: Search query (3-500 characters)
    - **credibility_threshold**: Minimum credibility score
    - **max_results**: Maximum number of results (1-100)
    - **include_summaries**: Whether to include AI summaries
    """
    start_time = datetime.now()

    try:
        async with NewsIntelligenceEngine(db) as engine:
            # Get candidate articles
            articles = await engine._fetch_trending_news(200)

            # Simple search implementation (in production, would use Elasticsearch)
            query_terms = request.query.lower().split()
            matching_articles = []

            for article in articles:
                if article.credibility_score < request.credibility_threshold:
                    continue

                text = f"{article.title} {article.content}".lower()

                # Calculate relevance score
                relevance_score = 0
                for term in query_terms:
                    if term in text:
                        relevance_score += text.count(term)

                if relevance_score > 0:
                    matching_articles.append((article, relevance_score))

            # Sort by relevance and credibility
            matching_articles.sort(
                key=lambda x: (x[1], x[0].credibility_score), reverse=True
            )

            # Get top results
            results = [
                article for article, _ in matching_articles[: request.max_results]
            ]

            # Generate summaries if requested
            if request.include_summaries and results:
                async with AISummarizationPipeline() as summarizer:
                    results = await summarizer.summarize_articles(
                        [a for a in results if not a.summary],
                        length=SummaryLength.BRIEF,
                    )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                "Search completed",
                query=request.query,
                results_count=len(results),
                processing_time_ms=processing_time,
            )

            return {
                "articles": [
                    NewsArticleResponse.from_orm(article) for article in results
                ],
                "query": request.query,
                "total_results": len(results),
                "processing_time_ms": processing_time,
                "credibility_threshold": request.credibility_threshold,
            }

    except Exception as e:
        logger.error("Search failed", query=request.query, error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/feedback", summary="Submit user feedback")
async def submit_feedback(
    user_id: int,
    article_id: str,
    feedback_type: str = Field(..., regex="^(read|liked|shared|dismissed)$"),
    reading_time_seconds: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Submit user feedback to improve personalization

    - **user_id**: User identifier
    - **article_id**: Article identifier
    - **feedback_type**: Type of feedback (read/liked/shared/dismissed)
    - **reading_time_seconds**: Optional reading time tracking
    """
    try:
        # Initialize recommender and update feedback
        recommender = HybridNewsRecommender(db)

        await recommender.update_user_feedback(
            user_id=user_id,
            article_id=article_id,
            feedback_type=feedback_type,
            reading_time_seconds=reading_time_seconds,
        )

        logger.info(
            "User feedback recorded",
            user_id=user_id,
            article_id=article_id,
            feedback_type=feedback_type,
        )

        return {
            "status": "success",
            "message": "Feedback recorded successfully",
            "timestamp": datetime.now(),
        }

    except Exception as e:
        logger.error(
            "Feedback recording failed",
            user_id=user_id,
            article_id=article_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to record feedback: {str(e)}"
        )


@router.get("/analytics/user/{user_id}", summary="Get user analytics")
async def get_user_analytics(
    user_id: int, db: AsyncSession = Depends(get_async_session)
):
    """Get analytics and insights for a specific user"""
    try:
        recommender = HybridNewsRecommender(db)
        analytics = await recommender.get_recommendation_analytics(user_id)

        return {"user_analytics": analytics, "generated_at": datetime.now()}

    except Exception as e:
        logger.error(f"User analytics failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get user analytics: {str(e)}"
        )


# Background task for summary generation
async def _generate_summaries_background(articles: List[NewsArticle], db: AsyncSession):
    """Background task to generate summaries for articles"""
    try:
        if not articles:
            return

        async with AISummarizationPipeline() as summarizer:
            await summarizer.summarize_articles(
                articles,
                length=SummaryLength.STANDARD,
                include_bias_detection=True,
                include_fact_checking=False,  # Skip fact-checking in background for performance
            )

        logger.info(f"Background summarization completed for {len(articles)} articles")

    except Exception as e:
        logger.error(f"Background summarization failed: {e}")


# Error handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=422, content={"detail": f"Invalid input: {str(exc)}"}
    )


@router.exception_handler(TimeoutError)
async def timeout_error_handler(request, exc):
    return JSONResponse(
        status_code=504, content={"detail": "Request timeout - please try again"}
    )


# Include router in main FastAPI app
def include_news_routes(app):
    """Include news intelligence routes in FastAPI app"""
    app.include_router(router)

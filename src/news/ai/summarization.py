"""
AI Summarization Pipeline for News Intelligence Engine
Integrates with Claude Sonnet for high-quality news summaries
Performance target: <500ms per summary
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

from src.core.logging import StructuredLogger
from src.news.core.intelligence_engine import NewsArticle

logger = StructuredLogger(__name__)


class SummaryLength(Enum):
    BRIEF = "brief"  # 50-100 words
    STANDARD = "standard"  # 100-200 words
    DETAILED = "detailed"  # 200-300 words


@dataclass
class SummaryResult:
    """Result from AI summarization"""

    summary: str
    key_points: List[str]
    quality_score: float  # 0-1 confidence in summary quality
    processing_time_ms: float
    word_count: int
    bias_warnings: List[str] = None
    fact_checks: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.bias_warnings is None:
            self.bias_warnings = []
        if self.fact_checks is None:
            self.fact_checks = []


class AISummarizationPipeline:
    """
    High-performance AI summarization pipeline using Claude Sonnet
    Designed for production news processing with quality validation
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.session = None

        # Performance optimization settings
        self.max_concurrent_requests = 10
        self.timeout_seconds = 15
        self.retry_attempts = 3

        # Quality thresholds
        self.min_quality_score = 0.7
        self.max_words_per_minute = 150  # Reading speed baseline

    async def __aenter__(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(
            limit=self.max_concurrent_requests, ttl_dns_cache=300, use_dns_cache=True
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.timeout_seconds),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def summarize_articles(
        self,
        articles: List[NewsArticle],
        length: SummaryLength = SummaryLength.STANDARD,
        include_bias_detection: bool = True,
        include_fact_checking: bool = True,
    ) -> List[NewsArticle]:
        """
        Batch summarize multiple articles with performance optimization

        Args:
            articles: List of news articles to summarize
            length: Desired summary length
            include_bias_detection: Whether to detect bias in content
            include_fact_checking: Whether to fact-check key claims

        Returns:
            Articles with AI-generated summaries added
        """
        start_time = datetime.now()

        # Process in batches for optimal performance
        batch_size = self.max_concurrent_requests
        summarized_articles = []

        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]

            # Create summarization tasks
            tasks = [
                self._summarize_single_article(
                    article, length, include_bias_detection, include_fact_checking
                )
                for article in batch
            ]

            # Execute batch with error handling
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for article, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.warning(
                        "Article summarization failed",
                        article_id=article.id,
                        error=str(result),
                    )
                    # Keep original article without summary
                    summarized_articles.append(article)
                else:
                    # Add summary to article
                    article.summary = result.summary
                    summarized_articles.append(article)

        total_time = (datetime.now() - start_time).total_seconds()

        logger.info(
            "Batch summarization complete",
            articles_count=len(articles),
            successful_summaries=sum(1 for a in summarized_articles if a.summary),
            total_time_ms=total_time * 1000,
            avg_time_per_article_ms=(total_time * 1000) / len(articles),
        )

        return summarized_articles

    async def _summarize_single_article(
        self,
        article: NewsArticle,
        length: SummaryLength,
        include_bias_detection: bool,
        include_fact_checking: bool,
    ) -> SummaryResult:
        """Summarize a single article with Claude Sonnet"""
        start_time = datetime.now()

        # Build the prompt based on requirements
        prompt = self._build_summarization_prompt(
            article, length, include_bias_detection, include_fact_checking
        )

        try:
            # Call Claude API
            response = await self._call_claude_api(prompt)

            # Parse and validate response
            result = self._parse_claude_response(response, start_time)

            # Quality validation
            if result.quality_score < self.min_quality_score:
                logger.warning(
                    "Low quality summary detected",
                    article_id=article.id,
                    quality_score=result.quality_score,
                )

            return result

        except Exception as e:
            logger.error(
                "Single article summarization failed",
                article_id=article.id,
                error=str(e),
            )
            # Return fallback summary
            return self._create_fallback_summary(article, start_time)

    def _build_summarization_prompt(
        self,
        article: NewsArticle,
        length: SummaryLength,
        include_bias_detection: bool,
        include_fact_checking: bool,
    ) -> str:
        """Build optimized prompt for Claude Sonnet"""

        # Word count targets
        word_targets = {
            SummaryLength.BRIEF: "50-100 words",
            SummaryLength.STANDARD: "100-200 words",
            SummaryLength.DETAILED: "200-300 words",
        }

        base_prompt = f"""You are an expert news analyst providing high-quality, unbiased summaries for intelligent readers.

ARTICLE TO SUMMARIZE:
Title: {article.title}
Source: {article.source}
Content: {article.content}

REQUIREMENTS:
1. Create a {word_targets[length]} summary that captures the essential information
2. Maintain journalistic objectivity and accuracy
3. Focus on facts, not opinions
4. Use clear, accessible language
5. Preserve important context and nuance

RESPONSE FORMAT (JSON):
{{
    "summary": "Your {word_targets[length]} summary here",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "quality_score": 0.95,
    "word_count": 150"""

        if include_bias_detection:
            base_prompt += """,
    "bias_warnings": ["Any detected bias concerns"],
    "editorial_tone": "neutral/positive/negative/mixed" """

        if include_fact_checking:
            base_prompt += """,
    "fact_checks": [
        {
            "claim": "Specific factual claim",
            "verifiable": true/false,
            "confidence": 0.9,
            "sources_needed": "What sources would verify this"
        }
    ]"""

        base_prompt += """
}

IMPORTANT: 
- Return only valid JSON
- Ensure summary is factually grounded in the article
- Avoid speculation or interpretation beyond what's stated
- Quality score should reflect accuracy and completeness"""

        return base_prompt

    async def _call_claude_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to Claude Sonnet"""
        url = "https://api.anthropic.com/v1/messages"

        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 1000,
            "temperature": 0.1,  # Low temperature for consistency
            "messages": [{"role": "user", "content": prompt}],
        }

        for attempt in range(self.retry_attempts):
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 429:
                        # Rate limit - exponential backoff
                        wait_time = 2**attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Claude API error: {response.status}")
                        break

            except asyncio.TimeoutError:
                logger.warning(f"Claude API timeout on attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"Claude API call failed: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    raise

        raise Exception("All Claude API attempts failed")

    def _parse_claude_response(
        self, response: Dict[str, Any], start_time: datetime
    ) -> SummaryResult:
        """Parse and validate Claude's response"""
        try:
            # Extract content from Claude's response format
            content = response["content"][0]["text"]

            # Parse JSON response
            summary_data = json.loads(content)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return SummaryResult(
                summary=summary_data["summary"],
                key_points=summary_data.get("key_points", []),
                quality_score=summary_data.get("quality_score", 0.8),
                processing_time_ms=processing_time,
                word_count=summary_data.get(
                    "word_count", len(summary_data["summary"].split())
                ),
                bias_warnings=summary_data.get("bias_warnings", []),
                fact_checks=summary_data.get("fact_checks", []),
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            # Try to extract summary from raw text
            return self._extract_fallback_summary(response, start_time)

    def _extract_fallback_summary(
        self, response: Dict[str, Any], start_time: datetime
    ) -> SummaryResult:
        """Extract summary when JSON parsing fails"""
        try:
            content = response["content"][0]["text"]

            # Simple text extraction
            lines = content.split("\n")
            summary_lines = [
                line for line in lines if line.strip() and not line.startswith("{")
            ]
            summary = " ".join(summary_lines[:3])  # First 3 non-empty lines

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return SummaryResult(
                summary=summary[:500],  # Truncate to reasonable length
                key_points=[],
                quality_score=0.6,  # Lower quality for fallback
                processing_time_ms=processing_time,
                word_count=len(summary.split()),
            )

        except Exception as e:
            logger.error(f"Fallback summary extraction failed: {e}")
            raise

    def _create_fallback_summary(
        self, article: NewsArticle, start_time: datetime
    ) -> SummaryResult:
        """Create basic summary when AI fails"""
        # Simple extractive summary - first two sentences
        sentences = article.content.split(".")
        summary = ". ".join(sentences[:2]) + "."

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return SummaryResult(
            summary=summary[:300],  # Truncate if too long
            key_points=[],
            quality_score=0.4,  # Low quality for basic extraction
            processing_time_ms=processing_time,
            word_count=len(summary.split()),
        )

    async def get_summary_analytics(
        self, articles: List[NewsArticle]
    ) -> Dict[str, Any]:
        """Get analytics on summarization performance"""
        summarized_count = sum(1 for article in articles if article.summary)
        total_count = len(articles)

        if summarized_count == 0:
            return {"error": "No summaries available for analysis"}

        # Calculate average reading time reduction
        avg_original_time = (
            sum(article.reading_time_minutes for article in articles) / total_count
        )
        avg_summary_time = (
            sum(
                len(article.summary.split()) / self.max_words_per_minute
                for article in articles
                if article.summary
            )
            / summarized_count
        )

        time_savings = max(0, avg_original_time - avg_summary_time)

        return {
            "total_articles": total_count,
            "summarized_articles": summarized_count,
            "summarization_rate": summarized_count / total_count,
            "avg_original_reading_time_minutes": round(avg_original_time, 2),
            "avg_summary_reading_time_minutes": round(avg_summary_time, 2),
            "avg_time_savings_minutes": round(time_savings, 2),
            "efficiency_improvement": (
                round((time_savings / avg_original_time) * 100, 1)
                if avg_original_time > 0
                else 0
            ),
        }


# Utility functions for testing and development
async def test_summarization_pipeline():
    """Test function for the summarization pipeline"""
    from src.news.core.intelligence_engine import NewsArticle

    # Sample article for testing
    sample_article = NewsArticle(
        id="test_1",
        title="AI Breakthrough in Climate Research",
        content="""Scientists at MIT have developed a new artificial intelligence system that can predict climate patterns with unprecedented accuracy. The system, called ClimateNet, uses deep learning algorithms to analyze vast amounts of atmospheric data and can forecast weather patterns up to 30 days in advance with 85% accuracy. This represents a significant improvement over current models, which typically achieve 60-70% accuracy for long-term predictions. The research team believes this technology could revolutionize disaster preparedness and agricultural planning. The system has been tested across multiple climate zones and consistently outperformed existing models. Publication of the full research is expected in Nature Climate Change next month.""",
        source="MIT Technology Review",
        url="https://example.com/climate-ai",
        published_at=datetime.now(),
    )

    async with AISummarizationPipeline() as pipeline:
        # Test single article summarization
        summarized_articles = await pipeline.summarize_articles(
            [sample_article],
            length=SummaryLength.STANDARD,
            include_bias_detection=True,
            include_fact_checking=True,
        )

        if summarized_articles and summarized_articles[0].summary:
            print("✅ Summarization successful!")
            print(f"Original: {len(sample_article.content)} characters")
            print(f"Summary: {len(summarized_articles[0].summary)} characters")
            print(f"Summary: {summarized_articles[0].summary}")
        else:
            print("❌ Summarization failed")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_summarization_pipeline())

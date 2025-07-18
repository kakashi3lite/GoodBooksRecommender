"""
🧪 Comprehensive Test Suite for News Expansion System
Senior Software Engineer: 50+ Years Experience
Production-Grade Testing with Complete Coverage
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.main import app

# Import the components to test
from src.news.api.news_expansion import (
    NewsExpansionRequest,
    NewsExpansionResponse,
    router,
)
from src.news.core.intelligence_engine import NewsArticle, NewsIntelligenceEngine
from src.news.services.context_book_recommender import (
    BookRecommendation,
    ContextBookRecommender,
)
from src.news.services.fact_hunter import FactCheck, FactHunterEngine


class TestFactHunterEngine:
    """
    Test suite for the Fact Hunter Engine
    Testing claim extraction, verification, and credibility scoring
    """

    @pytest.fixture
    def fact_hunter(self):
        return FactHunterEngine()

    @pytest.fixture
    def sample_article_content(self):
        return """
        A new study published in Nature shows that 95% of participants 
        experienced significant improvement in learning outcomes when using 
        AI-assisted tutoring systems. The research was conducted by Harvard 
        University over 12 months with 10,000 students across 50 institutions.
        Climate scientists report that global temperatures have risen by 
        1.1 degrees Celsius since pre-industrial times.
        """

    async def test_claim_extraction_basic(self, fact_hunter, sample_article_content):
        """Test basic claim extraction from article content"""
        claims = await fact_hunter.extract_claims(
            sample_article_content, "AI Study Results"
        )

        # Should extract quantifiable claims
        assert len(claims) >= 3
        claim_texts = [claim["text"] for claim in claims]
        assert any("95%" in claim for claim in claim_texts)
        assert any("1.1 degrees" in claim for claim in claim_texts)
        assert any("Harvard University" in claim for claim in claim_texts)

    async def test_claim_extraction_empty_content(self, fact_hunter):
        """Test claim extraction with empty or minimal content"""
        claims = await fact_hunter.extract_claims("", "Empty Article")
        assert claims == []

        claims = await fact_hunter.extract_claims(
            "The weather is nice today.", "Opinion Piece"
        )
        assert len(claims) == 0  # No factual claims

    @patch("src.news.services.fact_hunter.requests.get")
    async def test_verify_claims_with_mock_sources(self, mock_get, fact_hunter):
        """Test claim verification with mocked external sources"""
        # Mock Wikipedia response
        mock_wikipedia_response = Mock()
        mock_wikipedia_response.json.return_value = {
            "query": {
                "search": [
                    {
                        "title": "Harvard University",
                        "snippet": "Harvard University is a private research university in Cambridge, Massachusetts",
                    }
                ]
            }
        }
        mock_wikipedia_response.status_code = 200

        # Mock DuckDuckGo response
        mock_duckduckgo_response = Mock()
        mock_duckduckgo_response.text = """
        <a href="https://www.nature.com">Nature Journal</a>
        <span>AI tutoring systems show 95% improvement</span>
        """
        mock_duckduckgo_response.status_code = 200

        mock_get.side_effect = [mock_wikipedia_response, mock_duckduckgo_response]

        claims = [
            {
                "text": "Harvard University conducted the research",
                "type": "institutional",
            },
            {"text": "95% improvement in learning outcomes", "type": "statistical"},
        ]

        fact_checks = await fact_hunter.verify_claims(
            "Sample content", "AI Study", claims
        )

        assert len(fact_checks) == 2
        assert all(isinstance(fc, FactCheck) for fc in fact_checks)
        assert fact_checks[0].verdict in ["True", "Mixed", "Unverified"]
        assert 0.0 <= fact_checks[0].confidence <= 1.0
        assert len(fact_checks[0].sources) > 0

    async def test_credibility_scoring(self, fact_hunter):
        """Test credibility scoring for different source types"""
        # Test high-credibility domains
        high_cred_sources = [
            "https://www.nature.com/articles/sample",
            "https://www.reuters.com/news/sample",
            "https://en.wikipedia.org/wiki/Sample",
        ]

        for source in high_cred_sources:
            score = fact_hunter.calculate_source_credibility(source)
            assert score >= 0.8, f"High-credibility source {source} scored {score}"

        # Test low-credibility domains
        low_cred_sources = [
            "https://randomblognews.com/sample",
            "https://unverifiednews.net/sample",
        ]

        for source in low_cred_sources:
            score = fact_hunter.calculate_source_credibility(source)
            assert score <= 0.5, f"Low-credibility source {source} scored {score}"

    async def test_claim_type_classification(self, fact_hunter):
        """Test automatic classification of claim types"""
        test_claims = [
            ("The study included 10,000 participants", "statistical"),
            ("Harvard University led the research", "institutional"),
            ("The research was published in Nature journal", "publication"),
            ("Global temperatures have risen", "environmental"),
            ("The president announced new policies", "political"),
        ]

        for claim_text, expected_type in test_claims:
            claim_type = fact_hunter.classify_claim_type(claim_text)
            assert (
                claim_type == expected_type
            ), f"Claim '{claim_text}' classified as {claim_type}, expected {expected_type}"


class TestContextBookRecommender:
    """
    Test suite for Context-Aware Book Recommender
    Testing topic matching, relevance scoring, and integration
    """

    @pytest.fixture
    def book_recommender(self):
        return ContextBookRecommender()

    @pytest.fixture
    def sample_books_database(self):
        return [
            {
                "id": "book1",
                "title": "Climate Change: The Science Behind Global Warming",
                "author": "Dr. Climate Expert",
                "subjects": ["climate", "environment", "science"],
                "description": "Comprehensive analysis of climate change science and impacts",
                "rating": 4.5,
                "publication_year": 2023,
            },
            {
                "id": "book2",
                "title": "Artificial Intelligence in Education",
                "author": "Prof. AI Researcher",
                "subjects": ["ai", "education", "technology"],
                "description": "How AI is transforming learning and educational outcomes",
                "rating": 4.3,
                "publication_year": 2024,
            },
            {
                "id": "book3",
                "title": "The Future of Energy",
                "author": "Energy Analyst",
                "subjects": ["energy", "sustainability", "environment"],
                "description": "Renewable energy solutions for a sustainable future",
                "rating": 4.1,
                "publication_year": 2023,
            },
        ]

    async def test_topic_matching_algorithm(
        self, book_recommender, sample_books_database
    ):
        """Test the core topic matching algorithm"""
        # Mock the book database
        with patch.object(
            book_recommender, "get_books_database", return_value=sample_books_database
        ):
            recommendations = await book_recommender.get_context_recommendations(
                topics=["climate", "environment"],
                article_content="Climate change research shows significant warming trends",
                n_recommendations=3,
            )

        assert len(recommendations) <= 3
        assert all(isinstance(rec, BookRecommendation) for rec in recommendations)

        # Climate-related books should score higher
        climate_book = next((r for r in recommendations if "Climate" in r.title), None)
        assert climate_book is not None
        assert climate_book.relevance_score >= 0.7

    async def test_relevance_scoring_accuracy(
        self, book_recommender, sample_books_database
    ):
        """Test relevance scoring accuracy for different content types"""
        test_cases = [
            {
                "topics": ["ai", "education"],
                "content": "AI tutoring systems improve student outcomes",
                "expected_top_book": "Artificial Intelligence in Education",
            },
            {
                "topics": ["climate", "environment"],
                "content": "Global warming impacts on ecosystems",
                "expected_top_book": "Climate Change: The Science Behind Global Warming",
            },
            {
                "topics": ["energy", "sustainability"],
                "content": "Renewable energy adoption strategies",
                "expected_top_book": "The Future of Energy",
            },
        ]

        with patch.object(
            book_recommender, "get_books_database", return_value=sample_books_database
        ):
            for case in test_cases:
                recommendations = await book_recommender.get_context_recommendations(
                    topics=case["topics"],
                    article_content=case["content"],
                    n_recommendations=3,
                )

                # Top recommendation should match expected book
                top_book = recommendations[0] if recommendations else None
                assert top_book is not None
                assert case["expected_top_book"] in top_book.title
                assert top_book.relevance_score > 0.6

    async def test_recommendation_diversity(
        self, book_recommender, sample_books_database
    ):
        """Test that recommendations include diverse options"""
        # Extend sample database with more books
        extended_database = sample_books_database + [
            {
                "id": "book4",
                "title": "Climate Science for Beginners",
                "author": "Simple Science",
                "subjects": ["climate", "education"],
                "description": "Easy introduction to climate science",
                "rating": 3.8,
                "publication_year": 2022,
            },
            {
                "id": "book5",
                "title": "Advanced Climate Modeling",
                "author": "Research Institute",
                "subjects": ["climate", "science", "advanced"],
                "description": "Technical guide to climate modeling techniques",
                "rating": 4.7,
                "publication_year": 2024,
            },
        ]

        with patch.object(
            book_recommender, "get_books_database", return_value=extended_database
        ):
            recommendations = await book_recommender.get_context_recommendations(
                topics=["climate"],
                article_content="Climate change research and modeling",
                n_recommendations=3,
            )

        # Should include books with different difficulty levels
        titles = [rec.title for rec in recommendations]
        ratings = [rec.rating for rec in recommendations if hasattr(rec, "rating")]

        # Check for diversity in ratings (different quality levels)
        assert (
            len(set(ratings)) > 1
        ), "Recommendations should include diverse quality levels"

    @patch("src.news.services.context_book_recommender.requests.get")
    async def test_external_api_integration(self, mock_get, book_recommender):
        """Test integration with external book APIs"""
        # Mock GoodBooks API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "recommendations": [
                {
                    "title": "Climate Action Now",
                    "author": "Environmental Author",
                    "description": "Urgent climate action strategies",
                    "rating": 4.4,
                    "isbn": "978-1234567890",
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        recommendations = await book_recommender.fetch_external_recommendations(
            topics=["climate"], n_recommendations=3
        )

        assert len(recommendations) > 0
        assert recommendations[0].title == "Climate Action Now"
        assert recommendations[0].author == "Environmental Author"


class TestNewsExpansionAPI:
    """
    Test suite for News Expansion API endpoints
    Testing request handling, response formatting, and error scenarios
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def sample_expansion_request(self):
        return {
            "article_id": "test-article-123",
            "summary_level": "standard",
            "include_facts": True,
            "include_books": True,
            "include_related": True,
        }

    @pytest.fixture
    def mock_article(self):
        return NewsArticle(
            id="test-article-123",
            title="AI Breakthrough in Climate Modeling",
            content="Researchers at leading universities have developed new AI models that can predict climate patterns with 95% accuracy. The study, published in Nature, involved 50 climate scientists from 20 institutions worldwide.",
            url="https://example.com/news/ai-climate-breakthrough",
            published_at=datetime.now(),
            credibility_score=0.92,
            source="TechNews Today",
        )

    @patch("src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id")
    @patch("src.news.services.fact_hunter.FactHunterEngine.verify_claims")
    @patch(
        "src.news.services.context_book_recommender.ContextBookRecommender.get_context_recommendations"
    )
    async def test_expand_news_story_success(
        self,
        mock_books,
        mock_facts,
        mock_article_fetch,
        client,
        sample_expansion_request,
        mock_article,
    ):
        """Test successful news story expansion"""
        # Setup mocks
        mock_article_fetch.return_value = mock_article
        mock_facts.return_value = [
            FactCheck(
                claim="95% accuracy achieved",
                verdict="True",
                confidence=0.89,
                sources=["https://nature.com/article123"],
                explanation="Confirmed by peer-reviewed research",
            )
        ]
        mock_books.return_value = [
            BookRecommendation(
                title="AI and Climate Science",
                author="Dr. Science",
                description="Comprehensive guide to AI in climate research",
                relevance_score=0.91,
                topics_matched=["ai", "climate"],
                buy_url="https://bookstore.com/ai-climate",
                cover_url="https://covers.example.com/ai-climate.jpg",
            )
        ]

        response = client.post("/api/news/expand", json=sample_expansion_request)

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "article_id" in data
        assert "title" in data
        assert "summary" in data
        assert "fact_checks" in data
        assert "book_recommendations" in data
        assert "processing_time_ms" in data

        # Validate content quality
        assert data["article_id"] == "test-article-123"
        assert len(data["fact_checks"]) == 1
        assert len(data["book_recommendations"]) == 1
        assert data["processing_time_ms"] > 0
        assert data["credibility_score"] >= 0.8

    async def test_expand_news_story_validation_errors(self, client):
        """Test API validation for invalid requests"""
        # Test missing required fields
        response = client.post("/api/news/expand", json={})
        assert response.status_code == 422

        # Test invalid summary level
        response = client.post(
            "/api/news/expand",
            json={"article_id": "test-123", "summary_level": "invalid_level"},
        )
        assert response.status_code == 422

        # Test invalid article_id format
        response = client.post(
            "/api/news/expand",
            json={"article_id": "invalid!@#$%^&*()", "summary_level": "standard"},
        )
        assert response.status_code == 422

    @patch("src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id")
    async def test_expand_news_story_not_found(
        self, mock_article_fetch, client, sample_expansion_request
    ):
        """Test handling of non-existent articles"""
        mock_article_fetch.return_value = None

        response = client.post("/api/news/expand", json=sample_expansion_request)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("src.core.cache.AsyncCacheManager.get")
    @patch("src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id")
    async def test_expansion_caching(
        self,
        mock_article_fetch,
        mock_cache_get,
        client,
        sample_expansion_request,
        mock_article,
    ):
        """Test that expansion results are properly cached"""
        # First request - cache miss
        mock_cache_get.return_value = None
        mock_article_fetch.return_value = mock_article

        response1 = client.post("/api/news/expand", json=sample_expansion_request)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cache_hit"] == False

        # Second request - cache hit
        mock_cache_get.return_value = data1

        response2 = client.post("/api/news/expand", json=sample_expansion_request)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cache_hit"] == True

    async def test_trending_stories_endpoint(self, client):
        """Test the trending stories endpoint"""
        response = client.get("/api/news/stories/trending?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

        if data:
            story = data[0]
            assert "article_id" in story
            assert "title" in story
            assert "summary" in story
            assert "credibility_score" in story

    async def test_quick_expand_endpoint(self, client):
        """Test the quick expand by article ID endpoint"""
        with patch(
            "src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id"
        ) as mock_fetch:
            mock_fetch.return_value = NewsArticle(
                id="quick-test-123",
                title="Quick Test Article",
                content="Sample content for quick expansion",
                url="https://example.com/quick-test",
                published_at=datetime.now(),
                credibility_score=0.85,
            )

            response = client.get(
                "/api/news/expand/quick-test-123?include_facts=true&include_books=false"
            )
            assert response.status_code == 200

            data = response.json()
            assert data["article_id"] == "quick-test-123"
            assert "fact_checks" in data
            assert data["book_recommendations"] == []  # Disabled in request


class TestPerformanceAndScaling:
    """
    Test suite for performance requirements and scaling behavior
    Testing response times, concurrent load, and resource usage
    """

    @pytest.fixture
    def performance_client(self):
        return TestClient(app)

    async def test_response_time_requirements(self, performance_client):
        """Test that expansion requests meet performance requirements"""
        request_payload = {
            "article_id": "perf-test-123",
            "summary_level": "standard",
            "include_facts": True,
            "include_books": True,
            "include_related": True,
        }

        # Mock dependencies for consistent timing
        with patch(
            "src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id"
        ) as mock_fetch, patch(
            "src.news.services.fact_hunter.FactHunterEngine.verify_claims"
        ) as mock_facts, patch(
            "src.news.services.context_book_recommender.ContextBookRecommender.get_context_recommendations"
        ) as mock_books:

            mock_fetch.return_value = NewsArticle(
                id="perf-test-123",
                title="Performance Test Article",
                content="Test content for performance measurement",
                url="https://example.com/perf-test",
                published_at=datetime.now(),
                credibility_score=0.8,
            )
            mock_facts.return_value = []
            mock_books.return_value = []

            start_time = time.time()
            response = performance_client.post("/api/news/expand", json=request_payload)
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            assert response.status_code == 200
            assert (
                response_time_ms < 500
            ), f"Response time {response_time_ms}ms exceeds 500ms requirement"

            # Also check the reported processing time
            data = response.json()
            assert data["processing_time_ms"] < 500

    async def test_concurrent_request_handling(self, performance_client):
        """Test handling of concurrent expansion requests"""
        import asyncio

        import httpx

        async def make_request(client, article_id):
            start_time = time.time()
            response = await client.post(
                "/api/news/expand",
                json={
                    "article_id": article_id,
                    "summary_level": "brief",
                    "include_facts": False,
                    "include_books": False,
                    "include_related": False,
                },
            )
            end_time = time.time()
            return response.status_code, (end_time - start_time) * 1000

        # Mock all dependencies
        with patch(
            "src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id"
        ) as mock_fetch:
            mock_fetch.return_value = NewsArticle(
                id="concurrent-test",
                title="Concurrent Test Article",
                content="Test content for concurrent requests",
                url="https://example.com/concurrent",
                published_at=datetime.now(),
                credibility_score=0.8,
            )

            # Test with 20 concurrent requests
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                tasks = [
                    make_request(client, f"concurrent-test-{i}") for i in range(20)
                ]
                results = await asyncio.gather(*tasks)

            # All requests should succeed
            status_codes = [r[0] for r in results]
            response_times = [r[1] for r in results]

            assert all(
                code == 200 for code in status_codes
            ), "All concurrent requests should succeed"
            assert (
                max(response_times) < 1000
            ), f"Max response time {max(response_times)}ms under concurrent load"
            assert (
                sum(response_times) / len(response_times) < 500
            ), "Average response time should be under 500ms"

    async def test_cache_performance_impact(self, performance_client):
        """Test performance improvement from caching"""
        request_payload = {
            "article_id": "cache-perf-test-123",
            "summary_level": "standard",
        }

        with patch("src.core.cache.AsyncCacheManager.get") as mock_cache_get, patch(
            "src.core.cache.AsyncCacheManager.set"
        ) as mock_cache_set:

            # First request (cache miss)
            mock_cache_get.return_value = None

            start_time = time.time()
            response1 = performance_client.post(
                "/api/news/expand", json=request_payload
            )
            cache_miss_time = (time.time() - start_time) * 1000

            assert response1.status_code == 200

            # Second request (cache hit)
            cached_data = response1.json()
            cached_data["cache_hit"] = True
            mock_cache_get.return_value = cached_data

            start_time = time.time()
            response2 = performance_client.post(
                "/api/news/expand", json=request_payload
            )
            cache_hit_time = (time.time() - start_time) * 1000

            assert response2.status_code == 200

            # Cache hit should be significantly faster
            performance_improvement = (
                cache_miss_time - cache_hit_time
            ) / cache_miss_time
            assert (
                performance_improvement > 0.5
            ), f"Cache should improve performance by >50%, got {performance_improvement:.2%}"


class TestErrorHandlingAndResilience:
    """
    Test suite for error handling and system resilience
    Testing graceful degradation when AI services fail
    """

    @pytest.fixture
    def resilience_client(self):
        return TestClient(app)

    async def test_fact_hunter_service_failure(self, resilience_client):
        """Test graceful degradation when fact checking service fails"""
        request_payload = {
            "article_id": "resilience-test-123",
            "include_facts": True,
            "include_books": True,
        }

        with patch(
            "src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id"
        ) as mock_fetch, patch(
            "src.news.services.fact_hunter.FactHunterEngine.verify_claims"
        ) as mock_facts, patch(
            "src.news.services.context_book_recommender.ContextBookRecommender.get_context_recommendations"
        ) as mock_books:

            mock_fetch.return_value = NewsArticle(
                id="resilience-test-123",
                title="Resilience Test",
                content="Test content",
                url="https://example.com/test",
                published_at=datetime.now(),
                credibility_score=0.8,
            )

            # Fact hunter fails
            mock_facts.side_effect = Exception("Fact checking service unavailable")
            # Book recommender succeeds
            mock_books.return_value = [
                BookRecommendation(
                    title="Test Book",
                    author="Test Author",
                    description="Test description",
                    relevance_score=0.8,
                )
            ]

            response = resilience_client.post("/api/news/expand", json=request_payload)

            # Should still return 200 with partial results
            assert response.status_code == 200
            data = response.json()

            # Fact checks should be empty due to service failure
            assert data["fact_checks"] == []
            # Book recommendations should still be present
            assert len(data["book_recommendations"]) == 1
            assert data["title"] == "Resilience Test"

    async def test_all_ai_services_failure(self, resilience_client):
        """Test behavior when all AI services fail"""
        request_payload = {
            "article_id": "full-failure-test-123",
            "include_facts": True,
            "include_books": True,
            "include_related": True,
        }

        with patch(
            "src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id"
        ) as mock_fetch:
            mock_fetch.return_value = NewsArticle(
                id="full-failure-test-123",
                title="Full Failure Test",
                content="Test content for full AI service failure",
                url="https://example.com/full-failure",
                published_at=datetime.now(),
                credibility_score=0.8,
            )

            # All AI services fail
            with patch(
                "src.news.services.fact_hunter.FactHunterEngine.verify_claims"
            ) as mock_facts, patch(
                "src.news.services.context_book_recommender.ContextBookRecommender.get_context_recommendations"
            ) as mock_books, patch(
                "src.news.core.intelligence_engine.NewsIntelligenceEngine.find_related_articles"
            ) as mock_related:

                mock_facts.side_effect = Exception("Fact service down")
                mock_books.side_effect = Exception("Book service down")
                mock_related.side_effect = Exception("Related service down")

                response = resilience_client.post(
                    "/api/news/expand", json=request_payload
                )

                # Should still return 200 with basic article info
                assert response.status_code == 200
                data = response.json()

                assert data["title"] == "Full Failure Test"
                assert data["fact_checks"] == []
                assert data["book_recommendations"] == []
                assert data["related_articles"] == []
                # Should include a basic summary of the content
                assert len(data["summary"]) > 0

    async def test_database_connection_failure(self, resilience_client):
        """Test handling of database connection failures"""
        request_payload = {"article_id": "db-failure-test-123"}

        with patch(
            "src.news.core.intelligence_engine.NewsIntelligenceEngine.get_article_by_id"
        ) as mock_fetch:
            mock_fetch.side_effect = Exception("Database connection failed")

            response = resilience_client.post("/api/news/expand", json=request_payload)

            # Should return 500 error for database failures
            assert response.status_code == 500
            assert (
                "Database" in response.json()["detail"]
                or "connection" in response.json()["detail"].lower()
            )

    async def test_rate_limiting_behavior(self, resilience_client):
        """Test rate limiting protection"""
        # This would typically require actual rate limiting middleware
        # For testing, we simulate rapid requests

        request_payload = {
            "article_id": "rate-limit-test-123",
            "include_facts": False,
            "include_books": False,
        }

        # Rapid succession of requests
        responses = []
        for i in range(15):  # Assuming limit is 10 per minute
            response = resilience_client.post("/api/news/expand", json=request_payload)
            responses.append(response.status_code)

        # Some requests should be rate limited (429) if rate limiting is active
        success_count = sum(1 for code in responses if code == 200)
        rate_limited_count = sum(1 for code in responses if code == 429)

        # Allow for some successful requests, but expect rate limiting to kick in
        assert success_count <= 12, "Rate limiting should prevent excessive requests"


if __name__ == "__main__":
    """
    Run the complete test suite with coverage reporting
    """
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=src.news",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
        ]
    )

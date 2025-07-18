# Backend Unit Test Template
# File: tests/backend/test_news_expansion.py

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the modules to test
from src.api.news.expansion import NewsExpansionAPI
from src.services.fact_hunter import FactHunterService
from src.services.context_book_recommender import ContextBookRecommender
from src.core.exceptions import ValidationError, NetworkError
from src.models.news_models import NewsItem, FactCheck, BookRecommendation


class TestNewsExpansionAPI:
    """Comprehensive test suite for News Expansion API."""
    
    @pytest.fixture
    def mock_fact_hunter(self):
        """Mock fact hunter service."""
        mock = AsyncMock(spec=FactHunterService)
        mock.verify_facts.return_value = [
            FactCheck(
                claim="30 countries signed climate deal",
                verified=True,
                source="Reuters",
                confidence=0.95,
                explanation="Verified through official UN documentation"
            )
        ]
        return mock
    
    @pytest.fixture
    def mock_book_recommender(self):
        """Mock book recommendation service."""
        mock = AsyncMock(spec=ContextBookRecommender)
        mock.get_recommendations.return_value = [
            BookRecommendation(
                id="book-1",
                title="Climate Action Now",
                author="Jane Smith",
                relevance_score=0.89,
                description="Essential reading on climate policy",
                genre=["Environment", "Policy"],
                rating=4.7
            )
        ]
        return mock
    
    @pytest.fixture
    def sample_news_item(self):
        """Sample news item for testing."""
        return NewsItem(
            id="news-1",
            title="Historic Climate Deal Signed",
            summary="30 countries commit to carbon neutrality by 2030",
            url="https://example.com/climate-deal",
            published_at=datetime.now(),
            source="Climate News",
            category="Environment"
        )
    
    @pytest.fixture
    def news_api(self, mock_fact_hunter, mock_book_recommender):
        """News expansion API instance with mocked dependencies."""
        api = NewsExpansionAPI()
        api.fact_hunter = mock_fact_hunter
        api.book_recommender = mock_book_recommender
        return api
    
    @pytest.mark.asyncio
    async def test_expand_news_success(self, news_api, sample_news_item):
        """Test successful news expansion."""
        result = await news_api.expand_news(sample_news_item.id)
        
        assert result.id == sample_news_item.id
        assert result.is_expanded is True
        assert len(result.facts) > 0
        assert len(result.book_recommendations) > 0
        assert result.facts[0].verified is True
        assert result.book_recommendations[0].relevance_score > 0.8
    
    @pytest.mark.asyncio
    async def test_expand_news_with_caching(self, news_api, sample_news_item):
        """Test that expansion results are cached properly."""
        # First call
        result1 = await news_api.expand_news(sample_news_item.id)
        
        # Second call should use cache
        result2 = await news_api.expand_news(sample_news_item.id)
        
        assert result1.id == result2.id
        assert news_api.fact_hunter.verify_facts.call_count == 1  # Only called once
    
    @pytest.mark.asyncio
    async def test_expand_news_invalid_id(self, news_api):
        """Test expansion with invalid news ID."""
        with pytest.raises(ValidationError) as exc_info:
            await news_api.expand_news("invalid-id")
        
        assert "News item not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_expand_news_fact_hunter_failure(self, news_api, sample_news_item, mock_fact_hunter):
        """Test graceful handling of fact hunter failure."""
        mock_fact_hunter.verify_facts.side_effect = NetworkError("External service unavailable")
        
        result = await news_api.expand_news(sample_news_item.id)
        
        # Should still return result with empty facts
        assert result.id == sample_news_item.id
        assert result.facts == []
        assert len(result.book_recommendations) > 0  # Book recommendations should still work
    
    @pytest.mark.asyncio
    async def test_batch_expansion(self, news_api):
        """Test batch news expansion."""
        news_ids = ["news-1", "news-2", "news-3"]
        
        results = await news_api.expand_news_batch(news_ids)
        
        assert len(results) == 3
        for result in results:
            assert result.is_expanded is True
            assert hasattr(result, 'facts')
            assert hasattr(result, 'book_recommendations')
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, news_api, sample_news_item):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        tasks = [news_api.expand_news(sample_news_item.id) for _ in range(10)]
        
        # Some should succeed, some should be rate limited
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least some should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0
    
    def test_performance_benchmark(self, news_api, sample_news_item, benchmark):
        """Benchmark test for expansion performance."""
        async def expand_news():
            return await news_api.expand_news(sample_news_item.id)
        
        # Should complete within 200ms
        result = benchmark(asyncio.run, expand_news())
        assert result.id == sample_news_item.id


class TestFactHunterService:
    """Test suite for fact checking service."""
    
    @pytest.fixture
    def fact_hunter(self):
        """Fact hunter service instance."""
        return FactHunterService()
    
    @pytest.mark.asyncio
    async def test_verify_simple_fact(self, fact_hunter):
        """Test verification of a simple factual claim."""
        claim = "Paris is the capital of France"
        
        facts = await fact_hunter.verify_facts([claim])
        
        assert len(facts) == 1
        assert facts[0].claim == claim
        assert facts[0].verified is True
        assert facts[0].confidence > 0.9
    
    @pytest.mark.asyncio
    async def test_verify_false_claim(self, fact_hunter):
        """Test verification of a false claim."""
        claim = "The Earth is flat"
        
        facts = await fact_hunter.verify_facts([claim])
        
        assert len(facts) == 1
        assert facts[0].verified is False
        assert facts[0].confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_verify_ambiguous_claim(self, fact_hunter):
        """Test verification of an ambiguous claim."""
        claim = "Technology stocks will rise next month"
        
        facts = await fact_hunter.verify_facts([claim])
        
        assert len(facts) == 1
        assert facts[0].confidence < 0.6  # Low confidence for predictions
    
    @pytest.mark.asyncio
    async def test_multiple_sources_verification(self, fact_hunter):
        """Test that multiple sources are consulted for verification."""
        claim = "COVID-19 vaccines are effective"
        
        with patch.object(fact_hunter, '_check_wikipedia') as mock_wiki, \
             patch.object(fact_hunter, '_check_reuters') as mock_reuters, \
             patch.object(fact_hunter, '_check_snopes') as mock_snopes:
            
            mock_wiki.return_value = {"verified": True, "confidence": 0.8}
            mock_reuters.return_value = {"verified": True, "confidence": 0.9}
            mock_snopes.return_value = {"verified": True, "confidence": 0.85}
            
            facts = await fact_hunter.verify_facts([claim])
            
            # All sources should be checked
            mock_wiki.assert_called_once()
            mock_reuters.assert_called_once()
            mock_snopes.assert_called_once()
            
            # High confidence due to multiple source agreement
            assert facts[0].confidence > 0.85


class TestContextBookRecommender:
    """Test suite for context-aware book recommendations."""
    
    @pytest.fixture
    def book_recommender(self):
        """Book recommender service instance."""
        return ContextBookRecommender()
    
    @pytest.mark.asyncio
    async def test_recommend_by_topic(self, book_recommender):
        """Test book recommendations by topic."""
        topic = "artificial intelligence"
        
        recommendations = await book_recommender.get_recommendations_by_topic(topic)
        
        assert len(recommendations) > 0
        assert all(rec.relevance_score > 0.5 for rec in recommendations)
        assert any("AI" in rec.title or "artificial" in rec.title.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_recommend_by_content(self, book_recommender):
        """Test book recommendations based on content analysis."""
        content = """
        The latest breakthrough in quantum computing shows promise for solving
        complex optimization problems. Researchers at major universities are
        developing new algorithms that could revolutionize cryptography.
        """
        
        recommendations = await book_recommender.get_recommendations_by_content(content)
        
        assert len(recommendations) > 0
        topics = [rec.genre for rec in recommendations]
        assert any("Technology" in genre or "Science" in genre for rec in recommendations for genre in rec.genre)
    
    @pytest.mark.asyncio
    async def test_recommendation_diversity(self, book_recommender):
        """Test that recommendations include diverse options."""
        topic = "climate change"
        
        recommendations = await book_recommender.get_recommendations_by_topic(topic, num_recommendations=10)
        
        # Should have diverse genres and authors
        genres = set()
        authors = set()
        for rec in recommendations:
            genres.update(rec.genre)
            authors.add(rec.author)
        
        assert len(genres) >= 3  # At least 3 different genres
        assert len(authors) >= 5  # At least 5 different authors
    
    @pytest.mark.asyncio
    async def test_recommendation_quality_threshold(self, book_recommender):
        """Test that only high-quality recommendations are returned."""
        topic = "obscure technical topic that probably has no books"
        
        recommendations = await book_recommender.get_recommendations_by_topic(topic)
        
        # Should return fewer results for poor matches
        assert all(rec.relevance_score > 0.3 for rec in recommendations)
        assert all(rec.rating > 3.0 for rec in recommendations)


# Performance and Load Tests
class TestPerformance:
    """Performance and load testing."""
    
    @pytest.mark.asyncio
    async def test_concurrent_expansions(self):
        """Test handling of concurrent news expansions."""
        api = NewsExpansionAPI()
        
        # Simulate 50 concurrent requests
        tasks = [api.expand_news(f"news-{i}") for i in range(50)]
        
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # Should handle 50 requests in under 5 seconds
        assert duration < 5.0
        
        # Most requests should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) >= 40  # At least 80% success rate
    
    def test_memory_usage(self):
        """Test memory usage during intensive operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform memory-intensive operations
        api = NewsExpansionAPI()
        for i in range(1000):
            # Simulate processing without actual API calls
            news_item = NewsItem(
                id=f"news-{i}",
                title=f"Test Title {i}",
                summary=f"Test summary {i}",
                url=f"https://example.com/{i}",
                published_at=datetime.now(),
                source="Test Source",
                category="Test"
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

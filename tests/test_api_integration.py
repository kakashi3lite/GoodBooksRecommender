"""
Comprehensive Integration Tests for GoodBooks Recommender API
Tests all endpoints including new RAG, session, and vector search functionality.
Follows Bookworm AI Coding Standards.
"""

import asyncio
import pytest
import httpx
import uuid
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

import pandas as pd
from fastapi.testclient import TestClient
from fastapi import status

# Import the main app and services
from src.api.main import app, initialize_data_and_models
from src.core.settings import settings
from src.core.vector_store import BookVectorStore
from src.core.session_store import RedisSessionStore
from src.services.rag_service import RAGExplanationService


class TestAPIIntegration:
    """Integration tests for the API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        return TestClient(app)
    
    @pytest.fixture
    def api_headers(self):
        """Standard API headers for testing."""
        return {
            "X-API-Key": settings.security.default_api_key,
            "Content-Type": "application/json"
        }
    
    @pytest.fixture
    def sample_books(self):
        """Sample book data for testing."""
        return pd.DataFrame({
            'book_id': [1, 2, 3, 4, 5],
            'title': [
                'The Great Gatsby',
                'To Kill a Mockingbird', 
                'Harry Potter and the Sorcerer\'s Stone',
                'The Lord of the Rings',
                'Pride and Prejudice'
            ],
            'authors': [
                'F. Scott Fitzgerald',
                'Harper Lee',
                'J.K. Rowling',
                'J.R.R. Tolkien',
                'Jane Austen'
            ],
            'average_rating': [4.0, 4.3, 4.5, 4.7, 4.2],
            'ratings_count': [1000, 800, 1500, 1200, 900],
            'tag_name': [
                'classic american literature',
                'classic american literature social issues',
                'fantasy magic young adult',
                'fantasy epic adventure',
                'romance classic british'
            ]
        })
    
    @pytest.fixture
    def sample_ratings(self):
        """Sample ratings data for testing."""
        return pd.DataFrame({
            'user_id': [1, 1, 2, 2, 3, 3, 4, 4, 5],
            'book_id': [1, 2, 2, 3, 3, 4, 4, 5, 1],
            'rating': [5, 4, 3, 5, 4, 5, 3, 4, 5]
        })
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self, sample_books, sample_ratings):
        """Setup test environment with mocked services."""
        # Mock the global services
        with patch('src.api.main.data_loader') as mock_data_loader, \
             patch('src.api.main.recommender') as mock_recommender, \
             patch('src.api.main.vector_store') as mock_vector_store, \
             patch('src.api.main.rag_service') as mock_rag_service, \
             patch('src.api.main.session_store') as mock_session_store, \
             patch('src.api.main.cache_manager') as mock_cache_manager:
            
            # Setup data loader mock
            mock_data_loader.load_datasets_async = AsyncMock(
                return_value=(sample_books, sample_ratings, pd.DataFrame(), pd.DataFrame())
            )
            
            # Setup recommender mock
            mock_recommender.is_fitted = True
            mock_recommender.get_recommendations = MagicMock(return_value=sample_books.head(3))
            mock_recommender.explain_recommendations = MagicMock(
                return_value={"explanation": "Based on similar reading patterns"}
            )
            
            # Setup vector store mock
            mock_vector_store.semantic_search_async = AsyncMock(
                return_value=[
                    {
                        "book_id": 1,
                        "title": "The Great Gatsby",
                        "similarity_score": 0.85,
                        "metadata": {"authors": "F. Scott Fitzgerald"}
                    }
                ]
            )
            mock_vector_store.book_metadata = {
                0: {"title": "The Great Gatsby", "authors": "F. Scott Fitzgerald"}
            }
            mock_vector_store.book_id_to_id = {1: 0}
            
            # Setup RAG service mock
            mock_rag_service.explain_recommendation_async = AsyncMock(
                return_value={
                    "explanation": "This book is recommended because...",
                    "confidence_scores": {"overall_confidence": 0.85}
                }
            )
            mock_rag_service.explain_search_results_async = AsyncMock(
                return_value={
                    "explanation": "These results match your query because...",
                    "relevance_scores": [0.85, 0.78, 0.72]
                }
            )
            
            # Setup session store mock
            mock_session = MagicMock()
            mock_session.session_id = "test-session-123"
            mock_session.user_id = 1
            mock_session.created_at = "2024-01-01T00:00:00"
            mock_session.last_accessed = "2024-01-01T01:00:00"
            mock_session.preferences = {}
            mock_session.interaction_history = []
            mock_session.recommendation_history = []
            mock_session.search_history = []
            
            mock_session_store.create_session_async = AsyncMock(return_value="test-session-123")
            mock_session_store.get_session_async = AsyncMock(return_value=mock_session)
            mock_session_store.delete_session_async = AsyncMock(return_value=True)
            
            # Setup cache manager mock
            mock_cache_manager.connected = True
            mock_cache_manager.get = AsyncMock(return_value=None)
            mock_cache_manager.set = AsyncMock()
            mock_cache_manager.redis.ping = AsyncMock()
            
            yield
    
    def test_root_endpoint(self, client, api_headers):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client, api_headers):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
        assert "checks" in data
        
        # Check that health checks include all services
        checks = data["checks"]
        assert "cache" in checks
        assert "recommender" in checks
        assert "data" in checks
    
    def test_recommendations_endpoint_user_based(self, client, api_headers):
        """Test recommendations endpoint with user_id."""
        payload = {
            "user_id": 1,
            "n_recommendations": 5,
            "include_explanation": True
        }
        
        response = client.post("/recommendations", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response structure
        assert "recommendations" in data
        assert "total_count" in data
        assert "processing_time_ms" in data
        assert "cache_hit" in data
        assert "metadata" in data
        
        # Validate recommendations
        recommendations = data["recommendations"]
        assert len(recommendations) <= 5
        for rec in recommendations:
            assert "title" in rec
            assert "authors" in rec
            assert "average_rating" in rec
            assert "hybrid_score" in rec
    
    def test_recommendations_endpoint_content_based(self, client, api_headers):
        """Test recommendations endpoint with book_title."""
        payload = {
            "book_title": "The Great Gatsby",
            "n_recommendations": 3,
            "include_explanation": False
        }
        
        response = client.post("/recommendations", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 3
        assert data["metadata"]["request_type"] == "content_based"
    
    def test_recommendations_validation_error(self, client, api_headers):
        """Test recommendations endpoint with invalid input."""
        payload = {
            "n_recommendations": 5
            # Missing both user_id and book_title
        }
        
        response = client.post("/recommendations", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
    
    def test_explain_endpoint(self, client, api_headers):
        """Test the RAG explanation endpoint."""
        payload = {
            "book_id": 1,
            "recommendation_type": "hybrid",
            "n_context_books": 5
        }
        
        response = client.post("/explain", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response structure
        assert "explanation" in data
        assert "book_info" in data
        assert "processing_time_ms" in data
        
        # Validate explanation content
        explanation = data["explanation"]
        assert "explanation" in explanation
        assert "confidence_scores" in explanation
    
    def test_explain_endpoint_invalid_book(self, client, api_headers):
        """Test explanation endpoint with invalid book ID."""
        payload = {
            "book_id": 99999,  # Non-existent book
            "recommendation_type": "hybrid"
        }
        
        # Mock vector store to return None for invalid book
        with patch('src.api.main.vector_store.book_id_to_id', {}):
            response = client.post("/explain", json=payload, headers=api_headers)
            
            # Should still work but with empty book_info
            assert response.status_code == status.HTTP_200_OK
    
    def test_session_create(self, client, api_headers):
        """Test session creation."""
        payload = {
            "action": "create",
            "user_id": 123,
            "ttl": 86400
        }
        
        response = client.post("/session", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response structure
        assert "session_id" in data
        assert "session_data" in data
        assert "action_performed" in data
        assert "success" in data
        assert "processing_time_ms" in data
        
        assert data["action_performed"] == "create"
        assert data["success"] is True
        assert data["session_id"] == "test-session-123"
    
    def test_session_get(self, client, api_headers):
        """Test session retrieval."""
        payload = {
            "action": "get",
            "session_id": "test-session-123"
        }
        
        response = client.post("/session", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["action_performed"] == "get"
        assert data["success"] is True
        assert data["session_data"] is not None
        
        # Validate session data structure
        session_data = data["session_data"]
        assert "session_id" in session_data
        assert "user_id" in session_data
        assert "created_at" in session_data
        assert "preferences" in session_data
    
    def test_session_delete(self, client, api_headers):
        """Test session deletion."""
        payload = {
            "action": "delete",
            "session_id": "test-session-123"
        }
        
        response = client.post("/session", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["action_performed"] == "delete"
        assert data["success"] is True
    
    def test_session_invalid_action(self, client, api_headers):
        """Test session endpoint with invalid action."""
        payload = {
            "action": "invalid_action",
            "session_id": "test-session-123"
        }
        
        response = client.post("/session", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_search_endpoint(self, client, api_headers):
        """Test the semantic search endpoint."""
        payload = {
            "query": "fantasy adventure books with magic",
            "k": 10,
            "score_threshold": 0.3,
            "include_explanation": True
        }
        
        response = client.post("/search", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response structure
        assert "results" in data
        assert "total_count" in data
        assert "query" in data
        assert "processing_time_ms" in data
        assert "explanation" in data
        
        # Validate search results
        results = data["results"]
        assert len(results) <= 10
        for result in results:
            assert "book_id" in result
            assert "title" in result
            assert "similarity_score" in result
    
    def test_search_endpoint_without_explanation(self, client, api_headers):
        """Test search endpoint without explanation."""
        payload = {
            "query": "romance novels",
            "k": 5,
            "include_explanation": False
        }
        
        response = client.post("/search", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["explanation"] is None or "explanation" not in data
    
    def test_batch_recommendations(self, client, api_headers):
        """Test batch recommendations endpoint."""
        payload = [
            {
                "user_id": 1,
                "n_recommendations": 3
            },
            {
                "book_title": "The Great Gatsby",
                "n_recommendations": 2
            }
        ]
        
        response = client.post("/recommendations/batch", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "results" in data
        assert "total_requests" in data
        assert data["total_requests"] == 2
        
        results = data["results"]
        assert len(results) == 2
        for result in results:
            assert "status" in result
            if result["status"] == "success":
                assert "data" in result
    
    def test_batch_recommendations_limit(self, client, api_headers):
        """Test batch recommendations with limit exceeded."""
        # Create 11 requests (exceeds limit of 10)
        payload = [{"user_id": i, "n_recommendations": 1} for i in range(11)]
        
        response = client.post("/recommendations/batch", json=payload, headers=api_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_api_stats(self, client, api_headers):
        """Test API statistics endpoint."""
        response = client.get("/stats", headers=api_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "total_requests" in data
        assert "active_requests" in data
        assert "total_recommendations" in data
        assert "environment" in data
        assert "version" in data
    
    def test_book_search(self, client, api_headers):
        """Test book search endpoint."""
        response = client.get(
            "/books/search?query=gatsby&limit=5", 
            headers=api_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "query" in data
        assert "results" in data
        assert "total_count" in data
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        # Enable metrics for test
        with patch.object(settings.api, 'metrics_enabled', True):
            response = client.get("/metrics")
            
            assert response.status_code == status.HTTP_200_OK
            assert "text/plain" in response.headers["content-type"]
    
    def test_authentication_required(self, client):
        """Test that endpoints require authentication."""
        payload = {
            "user_id": 1,
            "n_recommendations": 5
        }
        
        # Request without API key
        response = client.post("/recommendations", json=payload)
        
        # Should fail authentication in production mode
        if not settings.is_development:
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_invalid_api_key(self, client):
        """Test with invalid API key."""
        headers = {
            "X-API-Key": "invalid-key",
            "Content-Type": "application/json"
        }
        
        payload = {
            "user_id": 1,
            "n_recommendations": 5
        }
        
        # Skip test in development mode
        if not settings.is_development:
            response = client.post("/recommendations", json=payload, headers=headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/recommendations")
        
        # In non-testing mode, CORS headers should be present
        if not settings.is_testing:
            assert "access-control-allow-origin" in response.headers
    
    def test_request_id_header(self, client, api_headers):
        """Test that request ID is added to response headers."""
        response = client.get("/", headers=api_headers)
        
        assert "x-request-id" in response.headers
        assert "x-processing-time" in response.headers
    
    def test_error_handling(self, client, api_headers):
        """Test error handling and response format."""
        # Test with invalid JSON
        response = client.post(
            "/recommendations", 
            data="invalid json",
            headers={"X-API-Key": settings.security.default_api_key}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDevelopmentEndpoints:
    """Test development-only endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def api_headers(self):
        return {
            "X-API-Key": settings.security.default_api_key,
            "Content-Type": "application/json"
        }
    
    def test_reset_cache_dev_only(self, client, api_headers):
        """Test cache reset endpoint (development only)."""
        if settings.is_development:
            with patch('src.api.main.cache_manager.clear_all', AsyncMock()):
                response = client.get("/dev/reset-cache", headers=api_headers)
                assert response.status_code == status.HTTP_200_OK
    
    def test_warm_cache_dev_only(self, client, api_headers):
        """Test cache warming endpoint (development only)."""
        if settings.is_development:
            response = client.get("/dev/warm-cache", headers=api_headers)
            assert response.status_code == status.HTTP_200_OK


class TestAsyncEndpoints:
    """Test async behavior of endpoints."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        async with httpx.AsyncClient(app=app, base_url="http://test") as client:
            
            headers = {"X-API-Key": settings.security.default_api_key}
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = client.post(
                    "/recommendations",
                    json={"user_id": i, "n_recommendations": 3},
                    headers=headers
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed or have expected errors
            for response in responses:
                if isinstance(response, httpx.Response):
                    assert response.status_code in [200, 400, 401, 503]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

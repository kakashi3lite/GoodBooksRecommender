# Testing Guide

Comprehensive testing guide for the GoodBooks Recommender system covering unit tests, integration tests, performance tests, and quality assurance.

## 📋 Table of Contents

- [Testing Overview](#-testing-overview)
- [Test Environment Setup](#-test-environment-setup)
- [Unit Testing](#-unit-testing)
- [Integration Testing](#-integration-testing)
- [API Testing](#-api-testing)
- [Performance Testing](#-performance-testing)
- [Load Testing](#-load-testing)
- [Data Quality Testing](#-data-quality-testing)
- [Model Testing](#-model-testing)
- [End-to-End Testing](#-end-to-end-testing)
- [Test Automation](#-test-automation)
- [Continuous Integration](#-continuous-integration)
- [Test Data Management](#-test-data-management)
- [Quality Metrics](#-quality-metrics)
- [Troubleshooting Tests](#-troubleshooting-tests)

## 🎯 Testing Overview

### Testing Strategy

Our testing approach follows the testing pyramid:

```
    /\     E2E Tests (Few)
   /  \    
  /____\   Integration Tests (Some)
 /______\  Unit Tests (Many)
```

### Test Types

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test REST API endpoints
4. **Performance Tests**: Test system performance and scalability
5. **Load Tests**: Test system under high load
6. **Model Tests**: Test ML model accuracy and behavior
7. **E2E Tests**: Test complete user workflows

### Testing Tools

- **pytest**: Python testing framework
- **pytest-asyncio**: Async testing support
- **pytest-cov**: Coverage reporting
- **requests-mock**: HTTP request mocking
- **factory-boy**: Test data generation
- **locust**: Load testing
- **newman**: API testing with Postman collections

## 🛠️ Test Environment Setup

### Prerequisites

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
pip install requests-mock factory-boy faker
pip install locust newman

# Install development dependencies
pip install black flake8 mypy pre-commit
```

### Test Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    performance: Performance tests
    slow: Slow running tests
    model: Model tests
```

### Test Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_data_loader.py
│   ├── test_models.py
│   ├── test_recommender.py
│   └── test_utils.py
├── integration/             # Integration tests
│   ├── test_api_integration.py
│   ├── test_database_integration.py
│   └── test_cache_integration.py
├── api/                     # API tests
│   ├── test_endpoints.py
│   ├── test_validation.py
│   └── test_error_handling.py
├── performance/             # Performance tests
│   ├── test_load.py
│   ├── test_memory.py
│   └── test_response_time.py
├── model/                   # Model tests
│   ├── test_collaborative_filter.py
│   ├── test_content_filter.py
│   └── test_hybrid_recommender.py
├── e2e/                     # End-to-end tests
│   └── test_user_workflows.py
├── data/                    # Test data
│   ├── sample_ratings.csv
│   ├── sample_books.csv
│   └── fixtures/
└── utils/                   # Test utilities
    ├── factories.py
    ├── helpers.py
    └── mock_data.py
```

### Test Configuration File

Create `tests/conftest.py`:

```python
import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.data.data_loader import DataLoader
from src.models.hybrid_recommender import HybridRecommender
from src.config import Config

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        'database_url': 'sqlite:///:memory:',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'cache_ttl': 300,
        'model_params': {
            'collaborative': {
                'n_factors': 10,  # Reduced for faster testing
                'n_epochs': 5
            }
        }
    }

@pytest.fixture
def sample_ratings_data():
    """Sample ratings data for testing"""
    return pd.DataFrame({
        'user_id': [1, 1, 2, 2, 3, 3, 4, 4, 5, 5],
        'book_id': [1, 2, 1, 3, 2, 3, 1, 4, 2, 4],
        'rating': [5, 4, 4, 5, 3, 4, 5, 3, 4, 5]
    })

@pytest.fixture
def sample_books_data():
    """Sample books data for testing"""
    return pd.DataFrame({
        'book_id': [1, 2, 3, 4],
        'title': ['Book One', 'Book Two', 'Book Three', 'Book Four'],
        'authors': ['Author A', 'Author B', 'Author C', 'Author D'],
        'average_rating': [4.5, 4.2, 4.8, 3.9],
        'ratings_count': [1000, 800, 1200, 600],
        'publication_year': [2020, 2019, 2021, 2018],
        'isbn': ['1111111111', '2222222222', '3333333333', '4444444444'],
        'language_code': ['eng', 'eng', 'eng', 'eng']
    })

@pytest.fixture
def mock_data_loader(sample_ratings_data, sample_books_data):
    """Mock data loader with sample data"""
    loader = Mock(spec=DataLoader)
    loader.ratings_df = sample_ratings_data
    loader.books_df = sample_books_data
    loader.load_data.return_value = None
    return loader

@pytest.fixture
def mock_recommender():
    """Mock recommender for testing"""
    recommender = Mock(spec=HybridRecommender)
    recommender.get_recommendations.return_value = [
        {
            'book_id': 1,
            'title': 'Test Book',
            'authors': 'Test Author',
            'average_rating': 4.5,
            'ratings_count': 1000,
            'score': 0.95,
            'explanation': 'Test explanation'
        }
    ]
    return recommender

@pytest.fixture
def api_client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def temp_data_dir():
    """Temporary directory for test data"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis for all tests"""
    with patch('redis.Redis') as mock_redis:
        mock_instance = Mock()
        mock_redis.return_value = mock_instance
        mock_instance.get.return_value = None
        mock_instance.set.return_value = True
        mock_instance.ping.return_value = True
        yield mock_instance
```

## 🧪 Unit Testing

### Data Loader Tests

Create `tests/unit/test_data_loader.py`:

```python
import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import patch, Mock

from src.data.data_loader import DataLoader
from src.config import Config

class TestDataLoader:
    """Test cases for DataLoader class"""
    
    def test_init(self):
        """Test DataLoader initialization"""
        loader = DataLoader()
        assert loader.ratings_df is None
        assert loader.books_df is None
        assert loader.tags_df is None
    
    def test_load_ratings_csv(self, temp_data_dir):
        """Test loading ratings from CSV file"""
        # Create test CSV file
        ratings_data = pd.DataFrame({
            'user_id': [1, 2, 3],
            'book_id': [1, 2, 3],
            'rating': [5, 4, 3]
        })
        
        csv_path = os.path.join(temp_data_dir, 'ratings.csv')
        ratings_data.to_csv(csv_path, index=False)
        
        # Test loading
        loader = DataLoader()
        result = loader._load_ratings_csv(csv_path)
        
        assert len(result) == 3
        assert list(result.columns) == ['user_id', 'book_id', 'rating']
        assert result['user_id'].tolist() == [1, 2, 3]
    
    def test_load_ratings_csv_missing_file(self):
        """Test loading ratings from non-existent file"""
        loader = DataLoader()
        
        with pytest.raises(FileNotFoundError):
            loader._load_ratings_csv('non_existent.csv')
    
    def test_load_ratings_csv_invalid_format(self, temp_data_dir):
        """Test loading ratings from invalid CSV format"""
        # Create invalid CSV file
        invalid_data = pd.DataFrame({
            'wrong_column': [1, 2, 3]
        })
        
        csv_path = os.path.join(temp_data_dir, 'invalid.csv')
        invalid_data.to_csv(csv_path, index=False)
        
        loader = DataLoader()
        
        with pytest.raises(KeyError):
            loader._load_ratings_csv(csv_path)
    
    @patch('src.data.data_loader.sqlite3')
    def test_load_ratings_database(self, mock_sqlite):
        """Test loading ratings from database"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, 1, 5),
            (2, 2, 4),
            (3, 3, 3)
        ]
        
        loader = DataLoader()
        result = loader._load_ratings_database('test.db')
        
        assert len(result) == 3
        assert list(result.columns) == ['user_id', 'book_id', 'rating']
        mock_sqlite.connect.assert_called_once_with('test.db')
    
    def test_preprocess_ratings(self, sample_ratings_data):
        """Test ratings preprocessing"""
        # Add some invalid data
        invalid_data = pd.DataFrame({
            'user_id': [1, 2, None, 4],
            'book_id': [1, None, 3, 4],
            'rating': [5, 4, 6, -1]  # Invalid ratings
        })
        
        loader = DataLoader()
        result = loader._preprocess_ratings(invalid_data)
        
        # Should remove rows with NaN and invalid ratings
        assert len(result) == 1  # Only first row is valid
        assert result.iloc[0]['rating'] == 5
    
    def test_get_user_ratings(self, sample_ratings_data):
        """Test getting ratings for specific user"""
        loader = DataLoader()
        loader.ratings_df = sample_ratings_data
        
        user_ratings = loader.get_user_ratings(user_id=1)
        
        assert len(user_ratings) == 2  # User 1 has 2 ratings
        assert user_ratings['user_id'].unique()[0] == 1
    
    def test_get_user_ratings_nonexistent_user(self, sample_ratings_data):
        """Test getting ratings for non-existent user"""
        loader = DataLoader()
        loader.ratings_df = sample_ratings_data
        
        user_ratings = loader.get_user_ratings(user_id=999)
        
        assert len(user_ratings) == 0
    
    @pytest.mark.parametrize("min_ratings,expected_users", [
        (1, 5),  # All users have at least 1 rating
        (2, 5),  # All users have exactly 2 ratings
        (3, 0),  # No users have 3+ ratings
    ])
    def test_filter_users_by_min_ratings(self, sample_ratings_data, min_ratings, expected_users):
        """Test filtering users by minimum ratings"""
        loader = DataLoader()
        loader.ratings_df = sample_ratings_data
        
        filtered_df = loader._filter_users_by_min_ratings(min_ratings)
        unique_users = filtered_df['user_id'].nunique()
        
        assert unique_users == expected_users
```

### Model Tests

Create `tests/unit/test_models.py`:

```python
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from src.models.collaborative_filter import CollaborativeFilter
from src.models.content_filter import ContentFilter
from src.models.hybrid_recommender import HybridRecommender

class TestCollaborativeFilter:
    """Test cases for CollaborativeFilter"""
    
    def test_init(self):
        """Test CollaborativeFilter initialization"""
        cf = CollaborativeFilter(n_factors=10, n_epochs=5)
        assert cf.n_factors == 10
        assert cf.n_epochs == 5
        assert cf.model is None
    
    def test_fit(self, sample_ratings_data):
        """Test model fitting"""
        cf = CollaborativeFilter(n_factors=5, n_epochs=2)
        
        # Should not raise any exceptions
        cf.fit(sample_ratings_data)
        
        # Model should be trained
        assert cf.model is not None
        assert hasattr(cf.model, 'predict')
    
    def test_fit_empty_data(self):
        """Test fitting with empty data"""
        cf = CollaborativeFilter()
        empty_data = pd.DataFrame(columns=['user_id', 'book_id', 'rating'])
        
        with pytest.raises(ValueError, match="Empty ratings data"):
            cf.fit(empty_data)
    
    def test_predict(self, sample_ratings_data):
        """Test prediction"""
        cf = CollaborativeFilter(n_factors=5, n_epochs=2)
        cf.fit(sample_ratings_data)
        
        # Test prediction for existing user-book pair
        prediction = cf.predict(user_id=1, book_id=1)
        
        assert isinstance(prediction, (int, float))
        assert 1 <= prediction <= 5  # Rating should be in valid range
    
    def test_predict_new_user(self, sample_ratings_data):
        """Test prediction for new user"""
        cf = CollaborativeFilter(n_factors=5, n_epochs=2)
        cf.fit(sample_ratings_data)
        
        # Prediction for new user should return global average
        prediction = cf.predict(user_id=999, book_id=1)
        
        assert isinstance(prediction, (int, float))
        # Should be close to global average
        global_avg = sample_ratings_data['rating'].mean()
        assert abs(prediction - global_avg) < 1.0
    
    def test_get_recommendations(self, sample_ratings_data):
        """Test getting recommendations"""
        cf = CollaborativeFilter(n_factors=5, n_epochs=2)
        cf.fit(sample_ratings_data)
        
        recommendations = cf.get_recommendations(user_id=1, n_recommendations=3)
        
        assert len(recommendations) <= 3
        assert all('book_id' in rec for rec in recommendations)
        assert all('score' in rec for rec in recommendations)
        
        # Scores should be in descending order
        scores = [rec['score'] for rec in recommendations]
        assert scores == sorted(scores, reverse=True)

class TestContentFilter:
    """Test cases for ContentFilter"""
    
    def test_init(self):
        """Test ContentFilter initialization"""
        cf = ContentFilter()
        assert cf.book_features is None
        assert cf.similarity_matrix is None
    
    def test_fit(self, sample_books_data):
        """Test model fitting"""
        cf = ContentFilter()
        cf.fit(sample_books_data)
        
        assert cf.book_features is not None
        assert cf.similarity_matrix is not None
        assert cf.similarity_matrix.shape[0] == len(sample_books_data)
    
    def test_get_similar_books(self, sample_books_data):
        """Test getting similar books"""
        cf = ContentFilter()
        cf.fit(sample_books_data)
        
        similar_books = cf.get_similar_books(book_id=1, n_recommendations=2)
        
        assert len(similar_books) <= 2
        assert all('book_id' in book for book in similar_books)
        assert all('similarity' in book for book in similar_books)
        
        # Should not include the input book itself
        book_ids = [book['book_id'] for book in similar_books]
        assert 1 not in book_ids
    
    def test_get_similar_books_by_title(self, sample_books_data):
        """Test getting similar books by title"""
        cf = ContentFilter()
        cf.fit(sample_books_data)
        
        similar_books = cf.get_similar_books_by_title(
            title="Book One", 
            n_recommendations=2
        )
        
        assert len(similar_books) <= 2
        assert all('book_id' in book for book in similar_books)
        
        # Should not include the input book itself
        titles = [book.get('title', '') for book in similar_books]
        assert "Book One" not in titles

class TestHybridRecommender:
    """Test cases for HybridRecommender"""
    
    def test_init(self):
        """Test HybridRecommender initialization"""
        hr = HybridRecommender(content_weight=0.3, collaborative_weight=0.7)
        assert hr.content_weight == 0.3
        assert hr.collaborative_weight == 0.7
        assert hr.content_model is not None
        assert hr.collaborative_model is not None
    
    def test_weights_sum_to_one(self):
        """Test that weights sum to 1.0"""
        hr = HybridRecommender(content_weight=0.4, collaborative_weight=0.6)
        assert abs((hr.content_weight + hr.collaborative_weight) - 1.0) < 1e-10
    
    def test_fit(self, sample_ratings_data, sample_books_data):
        """Test hybrid model fitting"""
        hr = HybridRecommender()
        
        # Should not raise any exceptions
        hr.fit(sample_ratings_data, sample_books_data)
        
        # Both models should be fitted
        assert hr.collaborative_model.model is not None
        assert hr.content_model.book_features is not None
    
    @patch('src.models.hybrid_recommender.HybridRecommender._has_sufficient_ratings')
    def test_get_recommendations_existing_user(self, mock_sufficient, sample_ratings_data, sample_books_data):
        """Test recommendations for existing user"""
        mock_sufficient.return_value = True
        
        hr = HybridRecommender()
        hr.fit(sample_ratings_data, sample_books_data)
        
        recommendations = hr.get_recommendations(user_id=1, n_recommendations=3)
        
        assert len(recommendations) <= 3
        assert all('book_id' in rec for rec in recommendations)
        assert all('score' in rec for rec in recommendations)
        assert all('explanation' in rec for rec in recommendations)
    
    @patch('src.models.hybrid_recommender.HybridRecommender._has_sufficient_ratings')
    def test_get_recommendations_new_user(self, mock_sufficient, sample_ratings_data, sample_books_data):
        """Test recommendations for new user (cold start)"""
        mock_sufficient.return_value = False
        
        hr = HybridRecommender()
        hr.fit(sample_ratings_data, sample_books_data)
        
        recommendations = hr.get_recommendations(
            book_title="Book One", 
            n_recommendations=3
        )
        
        assert len(recommendations) <= 3
        assert all('book_id' in rec for rec in recommendations)
    
    def test_has_sufficient_ratings(self, sample_ratings_data, sample_books_data):
        """Test checking if user has sufficient ratings"""
        hr = HybridRecommender()
        hr.fit(sample_ratings_data, sample_books_data)
        
        # User 1 has 2 ratings, should be sufficient (default min is 1)
        assert hr._has_sufficient_ratings(user_id=1, min_ratings=1) == True
        assert hr._has_sufficient_ratings(user_id=1, min_ratings=3) == False
        
        # Non-existent user
        assert hr._has_sufficient_ratings(user_id=999, min_ratings=1) == False
```

## 🔗 Integration Testing

### API Integration Tests

Create `tests/integration/test_api_integration.py`:

```python
import pytest
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from src.api.main import app

class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
    
    @patch('src.api.main.recommender')
    def test_recommendations_endpoint_user_id(self, mock_recommender, client):
        """Test recommendations endpoint with user_id"""
        # Mock recommender response
        mock_recommender.get_recommendations.return_value = [
            {
                'book_id': 1,
                'title': 'Test Book',
                'authors': 'Test Author',
                'average_rating': 4.5,
                'ratings_count': 1000,
                'publication_year': 2020,
                'isbn': '1234567890',
                'isbn13': '1234567890123',
                'language_code': 'eng',
                'score': 0.95,
                'explanation': 'Test explanation'
            }
        ]
        
        response = client.post(
            "/recommendations",
            json={"user_id": 123, "n_recommendations": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["title"] == "Test Book"
        
        # Verify recommender was called correctly
        mock_recommender.get_recommendations.assert_called_once_with(
            user_id=123,
            book_title=None,
            n_recommendations=5
        )
    
    @patch('src.api.main.recommender')
    def test_recommendations_endpoint_book_title(self, mock_recommender, client):
        """Test recommendations endpoint with book_title"""
        mock_recommender.get_recommendations.return_value = []
        
        response = client.post(
            "/recommendations",
            json={"book_title": "The Great Gatsby", "n_recommendations": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        
        mock_recommender.get_recommendations.assert_called_once_with(
            user_id=None,
            book_title="The Great Gatsby",
            n_recommendations=3
        )
    
    def test_recommendations_endpoint_missing_params(self, client):
        """Test recommendations endpoint with missing parameters"""
        response = client.post(
            "/recommendations",
            json={"n_recommendations": 5}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "user_id or book_title must be provided" in data["detail"]
    
    def test_recommendations_endpoint_invalid_params(self, client):
        """Test recommendations endpoint with invalid parameters"""
        # Test negative user_id
        response = client.post(
            "/recommendations",
            json={"user_id": -1, "n_recommendations": 5}
        )
        
        assert response.status_code == 422
        
        # Test too many recommendations
        response = client.post(
            "/recommendations",
            json={"user_id": 123, "n_recommendations": 1000}
        )
        
        assert response.status_code == 422
    
    @patch('src.api.main.recommender')
    def test_recommendations_endpoint_server_error(self, mock_recommender, client):
        """Test recommendations endpoint with server error"""
        # Mock recommender to raise exception
        mock_recommender.get_recommendations.side_effect = Exception("Model error")
        
        response = client.post(
            "/recommendations",
            json={"user_id": 123, "n_recommendations": 5}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
```

### Database Integration Tests

Create `tests/integration/test_database_integration.py`:

```python
import pytest
import sqlite3
import pandas as pd
import tempfile
import os
from unittest.mock import patch

from src.data.data_loader import DataLoader

class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create test database with sample data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE ratings (
                user_id INTEGER,
                book_id INTEGER,
                rating REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE books (
                book_id INTEGER PRIMARY KEY,
                title TEXT,
                authors TEXT,
                average_rating REAL,
                ratings_count INTEGER,
                publication_year INTEGER,
                isbn TEXT,
                language_code TEXT
            )
        ''')
        
        # Insert sample data
        ratings_data = [
            (1, 1, 5.0),
            (1, 2, 4.0),
            (2, 1, 4.0),
            (2, 3, 5.0),
            (3, 2, 3.0)
        ]
        cursor.executemany('INSERT INTO ratings VALUES (?, ?, ?)', ratings_data)
        
        books_data = [
            (1, 'Book One', 'Author A', 4.5, 1000, 2020, '1111111111', 'eng'),
            (2, 'Book Two', 'Author B', 4.2, 800, 2019, '2222222222', 'eng'),
            (3, 'Book Three', 'Author C', 4.8, 1200, 2021, '3333333333', 'eng')
        ]
        cursor.executemany('INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?, ?)', books_data)
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    def test_load_ratings_from_database(self, temp_db):
        """Test loading ratings from SQLite database"""
        loader = DataLoader()
        ratings_df = loader._load_ratings_database(temp_db)
        
        assert len(ratings_df) == 5
        assert list(ratings_df.columns) == ['user_id', 'book_id', 'rating']
        assert ratings_df['user_id'].tolist() == [1, 1, 2, 2, 3]
        assert ratings_df['rating'].tolist() == [5.0, 4.0, 4.0, 5.0, 3.0]
    
    def test_load_books_from_database(self, temp_db):
        """Test loading books from SQLite database"""
        loader = DataLoader()
        books_df = loader._load_books_database(temp_db)
        
        assert len(books_df) == 3
        assert 'book_id' in books_df.columns
        assert 'title' in books_df.columns
        assert 'authors' in books_df.columns
        assert books_df['title'].tolist() == ['Book One', 'Book Two', 'Book Three']
    
    def test_database_connection_error(self):
        """Test handling database connection errors"""
        loader = DataLoader()
        
        with pytest.raises(sqlite3.OperationalError):
            loader._load_ratings_database('non_existent.db')
    
    def test_database_query_error(self, temp_db):
        """Test handling database query errors"""
        loader = DataLoader()
        
        # Modify the query to cause an error
        with patch.object(loader, '_get_ratings_query', return_value='INVALID SQL'):
            with pytest.raises(sqlite3.OperationalError):
                loader._load_ratings_database(temp_db)
```

## 🌐 API Testing

### Endpoint Validation Tests

Create `tests/api/test_validation.py`:

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

class TestAPIValidation:
    """Test API input validation"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.parametrize("invalid_payload,expected_status", [
        # Missing both user_id and book_title
        ({"n_recommendations": 5}, 400),
        
        # Invalid user_id type
        ({"user_id": "not_a_number", "n_recommendations": 5}, 422),
        
        # Negative user_id
        ({"user_id": -1, "n_recommendations": 5}, 422),
        
        # Zero user_id
        ({"user_id": 0, "n_recommendations": 5}, 422),
        
        # Invalid n_recommendations type
        ({"user_id": 123, "n_recommendations": "five"}, 422),
        
        # Negative n_recommendations
        ({"user_id": 123, "n_recommendations": -1}, 422),
        
        # Zero n_recommendations
        ({"user_id": 123, "n_recommendations": 0}, 422),
        
        # Too many recommendations
        ({"user_id": 123, "n_recommendations": 1000}, 422),
        
        # Empty book_title
        ({"book_title": "", "n_recommendations": 5}, 422),
        
        # Whitespace-only book_title
        ({"book_title": "   ", "n_recommendations": 5}, 422),
        
        # Both user_id and book_title provided
        ({"user_id": 123, "book_title": "Test Book", "n_recommendations": 5}, 400),
    ])
    def test_invalid_requests(self, client, invalid_payload, expected_status):
        """Test various invalid request payloads"""
        response = client.post("/recommendations", json=invalid_payload)
        assert response.status_code == expected_status
    
    @pytest.mark.parametrize("valid_payload", [
        # Valid user_id request
        {"user_id": 123, "n_recommendations": 5},
        
        # Valid book_title request
        {"book_title": "The Great Gatsby", "n_recommendations": 10},
        
        # Minimum recommendations
        {"user_id": 1, "n_recommendations": 1},
        
        # Maximum recommendations
        {"user_id": 1, "n_recommendations": 100},
        
        # Default n_recommendations (should be handled)
        {"user_id": 123},
        
        # Book title with special characters
        {"book_title": "Book: A Story (2021)", "n_recommendations": 5},
    ])
    def test_valid_requests(self, client, valid_payload):
        """Test valid request payloads"""
        with patch('src.api.main.recommender') as mock_recommender:
            mock_recommender.get_recommendations.return_value = []
            
            response = client.post("/recommendations", json=valid_payload)
            
            # Should not return validation errors
            assert response.status_code != 422
            assert response.status_code != 400
    
    def test_content_type_validation(self, client):
        """Test content type validation"""
        # Missing Content-Type header
        response = client.post("/recommendations", data="{\"user_id\": 123}")
        assert response.status_code == 422
        
        # Wrong Content-Type
        response = client.post(
            "/recommendations",
            data="user_id=123",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 422
    
    def test_malformed_json(self, client):
        """Test malformed JSON handling"""
        response = client.post(
            "/recommendations",
            data="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
```

## ⚡ Performance Testing

### Response Time Tests

Create `tests/performance/test_response_time.py`:

```python
import pytest
import time
import statistics
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.api.main import app

class TestResponseTime:
    """Test API response times"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def measure_response_time(self, client, endpoint, method="GET", json_data=None, iterations=10):
        """Measure average response time for an endpoint"""
        times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json=json_data)
            
            end_time = time.time()
            
            if response.status_code < 500:  # Only count successful requests
                times.append(end_time - start_time)
        
        return {
            'avg': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'std': statistics.stdev(times) if len(times) > 1 else 0
        }
    
    def test_health_endpoint_response_time(self, client):
        """Test health endpoint response time"""
        stats = self.measure_response_time(client, "/health", iterations=20)
        
        # Health endpoint should be very fast
        assert stats['avg'] < 0.1  # Less than 100ms average
        assert stats['max'] < 0.5  # Less than 500ms maximum
    
    @patch('src.api.main.recommender')
    def test_recommendations_endpoint_response_time(self, mock_recommender, client):
        """Test recommendations endpoint response time"""
        # Mock fast response
        mock_recommender.get_recommendations.return_value = [
            {
                'book_id': i,
                'title': f'Book {i}',
                'authors': f'Author {i}',
                'average_rating': 4.0,
                'ratings_count': 1000,
                'score': 0.9,
                'explanation': 'Test'
            } for i in range(5)
        ]
        
        stats = self.measure_response_time(
            client, 
            "/recommendations", 
            method="POST",
            json_data={"user_id": 123, "n_recommendations": 5},
            iterations=15
        )
        
        # Recommendations should be reasonably fast
        assert stats['avg'] < 2.0  # Less than 2 seconds average
        assert stats['max'] < 5.0  # Less than 5 seconds maximum
    
    @patch('src.api.main.recommender')
    def test_recommendations_scalability(self, mock_recommender, client):
        """Test response time with different recommendation counts"""
        mock_recommender.get_recommendations.return_value = []
        
        recommendation_counts = [1, 5, 10, 25, 50, 100]
        response_times = []
        
        for count in recommendation_counts:
            stats = self.measure_response_time(
                client,
                "/recommendations",
                method="POST",
                json_data={"user_id": 123, "n_recommendations": count},
                iterations=5
            )
            response_times.append(stats['avg'])
        
        # Response time should not increase dramatically with recommendation count
        # (assuming the bottleneck is not in the recommendation generation)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Response time should not increase by more than 3x
        assert max_time / min_time < 3.0
```

### Memory Usage Tests

Create `tests/performance/test_memory.py`:

```python
import pytest
import psutil
import os
import gc
from unittest.mock import patch

from src.models.hybrid_recommender import HybridRecommender
from src.data.data_loader import DataLoader

class TestMemoryUsage:
    """Test memory usage of various components"""
    
    def get_memory_usage(self):
        """Get current memory usage in MB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def test_data_loader_memory_usage(self, sample_ratings_data, sample_books_data):
        """Test DataLoader memory usage"""
        gc.collect()  # Clean up before measurement
        initial_memory = self.get_memory_usage()
        
        # Create and use DataLoader
        loader = DataLoader()
        loader.ratings_df = sample_ratings_data
        loader.books_df = sample_books_data
        
        # Perform some operations
        user_ratings = loader.get_user_ratings(user_id=1)
        
        current_memory = self.get_memory_usage()
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable for small dataset
        assert memory_increase < 50  # Less than 50MB for small test data
        
        # Clean up
        del loader
        gc.collect()
    
    def test_model_memory_usage(self, sample_ratings_data, sample_books_data):
        """Test model memory usage"""
        gc.collect()
        initial_memory = self.get_memory_usage()
        
        # Create and train model
        recommender = HybridRecommender()
        recommender.fit(sample_ratings_data, sample_books_data)
        
        # Generate recommendations
        recommendations = recommender.get_recommendations(user_id=1, n_recommendations=5)
        
        current_memory = self.get_memory_usage()
        memory_increase = current_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB for small model
        
        # Clean up
        del recommender
        gc.collect()
    
    def test_memory_leak_detection(self, sample_ratings_data, sample_books_data):
        """Test for memory leaks in repeated operations"""
        gc.collect()
        initial_memory = self.get_memory_usage()
        
        # Perform operations multiple times
        for i in range(10):
            recommender = HybridRecommender()
            recommender.fit(sample_ratings_data, sample_books_data)
            recommendations = recommender.get_recommendations(user_id=1, n_recommendations=5)
            del recommender
            
            if i % 3 == 0:  # Periodic cleanup
                gc.collect()
        
        gc.collect()
        final_memory = self.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly after cleanup
        assert memory_increase < 200  # Less than 200MB increase
    
    @pytest.mark.slow
    def test_large_dataset_memory_usage(self):
        """Test memory usage with larger dataset"""
        import pandas as pd
        import numpy as np
        
        # Create larger synthetic dataset
        n_users = 1000
        n_books = 500
        n_ratings = 10000
        
        np.random.seed(42)
        large_ratings = pd.DataFrame({
            'user_id': np.random.randint(1, n_users + 1, n_ratings),
            'book_id': np.random.randint(1, n_books + 1, n_ratings),
            'rating': np.random.randint(1, 6, n_ratings)
        })
        
        large_books = pd.DataFrame({
            'book_id': range(1, n_books + 1),
            'title': [f'Book {i}' for i in range(1, n_books + 1)],
            'authors': [f'Author {i}' for i in range(1, n_books + 1)],
            'average_rating': np.random.uniform(3.0, 5.0, n_books),
            'ratings_count': np.random.randint(100, 10000, n_books),
            'publication_year': np.random.randint(1950, 2023, n_books),
            'isbn': [f'{i:010d}' for i in range(1, n_books + 1)],
            'language_code': ['eng'] * n_books
        })
        
        gc.collect()
        initial_memory = self.get_memory_usage()
        
        # Train model with larger dataset
        recommender = HybridRecommender()
        recommender.fit(large_ratings, large_books)
        
        current_memory = self.get_memory_usage()
        memory_increase = current_memory - initial_memory
        
        # Memory usage should be reasonable even for larger dataset
        assert memory_increase < 1000  # Less than 1GB
        
        # Test recommendations
        recommendations = recommender.get_recommendations(user_id=1, n_recommendations=10)
        assert len(recommendations) <= 10
        
        # Clean up
        del recommender, large_ratings, large_books
        gc.collect()
```

## 🚀 Load Testing

### Locust Load Tests

Create `tests/performance/locustfile.py`:

```python
from locust import HttpUser, task, between
import json
import random

class RecommendationUser(HttpUser):
    """Simulated user for load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        # Check if API is healthy before starting
        response = self.client.get("/health")
        if response.status_code != 200:
            print(f"API health check failed: {response.status_code}")
    
    @task(3)
    def get_user_recommendations(self):
        """Get recommendations for a user (most common operation)"""
        user_id = random.randint(1, 1000)
        n_recommendations = random.choice([5, 10, 15, 20])
        
        payload = {
            "user_id": user_id,
            "n_recommendations": n_recommendations
        }
        
        with self.client.post(
            "/recommendations",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "recommendations" in data:
                    response.success()
                else:
                    response.failure("Missing recommendations in response")
            elif response.status_code == 400:
                response.failure(f"Bad request: {response.text}")
            elif response.status_code == 500:
                response.failure(f"Server error: {response.text}")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(1)
    def get_similar_books(self):
        """Get similar books (less common operation)"""
        book_titles = [
            "The Great Gatsby",
            "To Kill a Mockingbird",
            "1984",
            "Pride and Prejudice",
            "The Catcher in the Rye",
            "Harry Potter",
            "Lord of the Rings"
        ]
        
        book_title = random.choice(book_titles)
        n_recommendations = random.choice([3, 5, 8])
        
        payload = {
            "book_title": book_title,
            "n_recommendations": n_recommendations
        }
        
        with self.client.post(
            "/recommendations",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Periodic health checks"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    response.success()
                else:
                    response.failure(f"Unhealthy status: {data.get('status')}")
            else:
                response.failure(f"Health check failed: {response.status_code}")

class HeavyUser(HttpUser):
    """Heavy user that makes many requests"""
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    weight = 1  # Lower weight (fewer of these users)
    
    @task
    def rapid_recommendations(self):
        """Make rapid recommendation requests"""
        user_id = random.randint(1, 100)  # Smaller pool for cache hits
        
        payload = {
            "user_id": user_id,
            "n_recommendations": 5
        }
        
        self.client.post("/recommendations", json=payload)

class BurstUser(HttpUser):
    """User that creates burst traffic"""
    
    wait_time = between(10, 30)  # Long wait, then burst
    weight = 1
    
    @task
    def burst_requests(self):
        """Make multiple requests in quick succession"""
        for _ in range(5):
            user_id = random.randint(1, 1000)
            payload = {
                "user_id": user_id,
                "n_recommendations": random.choice([5, 10])
            }
            self.client.post("/recommendations", json=payload)
```

### Load Test Runner

Create `tests/performance/run_load_tests.py`:

```python
#!/usr/bin/env python3
"""
Load test runner for GoodBooks Recommender API

Usage:
    python run_load_tests.py --host http://localhost:8000 --users 50 --spawn-rate 5 --time 300
"""

import argparse
import subprocess
import sys
import time
import requests

def check_api_health(host):
    """Check if API is healthy before starting tests"""
    try:
        response = requests.get(f"{host}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print(f"✅ API is healthy at {host}")
                return True
            else:
                print(f"❌ API is unhealthy: {data.get('status')}")
                return False
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def run_load_test(host, users, spawn_rate, time_limit, user_class="RecommendationUser"):
    """Run load test using Locust"""
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--host", host,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", f"{time_limit}s",
        "--headless",
        "--only-summary",
        user_class
    ]
    
    print(f"🚀 Starting load test with {users} users for {time_limit} seconds...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=time_limit + 60)
        
        print("\n📊 Load Test Results:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ Errors:")
            print(result.stderr)
        
        return result.returncode == 0
    
    except subprocess.TimeoutExpired:
        print("❌ Load test timed out")
        return False
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        return False

def run_performance_suite(host):
    """Run a suite of performance tests"""
    tests = [
        {
            "name": "Light Load Test",
            "users": 10,
            "spawn_rate": 2,
            "time": 60,
            "user_class": "RecommendationUser"
        },
        {
            "name": "Medium Load Test",
            "users": 50,
            "spawn_rate": 5,
            "time": 120,
            "user_class": "RecommendationUser"
        },
        {
            "name": "Heavy Load Test",
            "users": 100,
            "spawn_rate": 10,
            "time": 180,
            "user_class": "RecommendationUser"
        },
        {
            "name": "Burst Load Test",
            "users": 20,
            "spawn_rate": 10,
            "time": 60,
            "user_class": "BurstUser"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n🧪 Running {test['name']}...")
        
        success = run_load_test(
            host=host,
            users=test["users"],
            spawn_rate=test["spawn_rate"],
            time_limit=test["time"],
            user_class=test["user_class"]
        )
        
        results.append({
            "name": test["name"],
            "success": success
        })
        
        # Wait between tests
        if test != tests[-1]:  # Not the last test
            print("⏳ Waiting 30 seconds before next test...")
            time.sleep(30)
    
    # Summary
    print("\n📋 Performance Test Summary:")
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"  {result['name']}: {status}")
    
    return all(result["success"] for result in results)

def main():
    parser = argparse.ArgumentParser(description="Run load tests for GoodBooks Recommender API")
    parser.add_argument("--host", default="http://localhost:8000", help="API host URL")
    parser.add_argument("--users", type=int, default=50, help="Number of concurrent users")
    parser.add_argument("--spawn-rate", type=int, default=5, help="User spawn rate per second")
    parser.add_argument("--time", type=int, default=300, help="Test duration in seconds")
    parser.add_argument("--suite", action="store_true", help="Run full performance test suite")
    parser.add_argument("--user-class", default="RecommendationUser", help="Locust user class to use")
    
    args = parser.parse_args()
    
    # Check API health first
    if not check_api_health(args.host):
        print("❌ API health check failed. Please ensure the API is running and healthy.")
        sys.exit(1)
    
    if args.suite:
        success = run_performance_suite(args.host)
    else:
        success = run_load_test(
            host=args.host,
            users=args.users,
            spawn_rate=args.spawn_rate,
            time_limit=args.time,
            user_class=args.user_class
        )
    
    if success:
        print("\n🎉 All load tests completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some load tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 📊 Data Quality Testing

### Data Validation Tests

Create `tests/data/test_data_quality.py`:

```python
import pytest
import pandas as pd
import numpy as np
from src.data.data_loader import DataLoader
from src.utils.data_validator import DataValidator

class TestDataQuality:
    """Test data quality and validation"""
    
    def test_ratings_data_completeness(self, sample_ratings_data):
        """Test that ratings data has required columns"""
        required_columns = ['user_id', 'book_id', 'rating']
        
        for column in required_columns:
            assert column in sample_ratings_data.columns
            assert not sample_ratings_data[column].isnull().all()
    
    def test_ratings_data_validity(self, sample_ratings_data):
        """Test that ratings data contains valid values"""
        # Check rating range
        assert sample_ratings_data['rating'].min() >= 1
        assert sample_ratings_data['rating'].max() <= 5
        
        # Check for positive IDs
        assert sample_ratings_data['user_id'].min() > 0
        assert sample_ratings_data['book_id'].min() > 0
        
        # Check data types
        assert sample_ratings_data['user_id'].dtype in ['int64', 'int32']
        assert sample_ratings_data['book_id'].dtype in ['int64', 'int32']
        assert sample_ratings_data['rating'].dtype in ['float64', 'int64']
    
    def test_books_data_completeness(self, sample_books_data):
        """Test that books data has required columns"""
        required_columns = ['book_id', 'title', 'authors']
        
        for column in required_columns:
            assert column in sample_books_data.columns
            assert not sample_books_data[column].isnull().all()
    
    def test_books_data_validity(self, sample_books_data):
        """Test that books data contains valid values"""
        # Check for positive book IDs
        assert sample_books_data['book_id'].min() > 0
        
        # Check for non-empty titles
        assert not sample_books_data['title'].str.strip().eq('').any()
        
        # Check average rating range
        if 'average_rating' in sample_books_data.columns:
            valid_ratings = sample_books_data['average_rating'].dropna()
            if len(valid_ratings) > 0:
                assert valid_ratings.min() >= 0
                assert valid_ratings.max() <= 5
    
    def test_data_consistency(self, sample_ratings_data, sample_books_data):
        """Test consistency between ratings and books data"""
        # All books in ratings should exist in books data
        rating_books = set(sample_ratings_data['book_id'].unique())
        available_books = set(sample_books_data['book_id'].unique())
        
        missing_books = rating_books - available_books
        assert len(missing_books) == 0, f"Missing books in books data: {missing_books}"
    
    def test_duplicate_detection(self):
        """Test detection of duplicate records"""
        # Create data with duplicates
        data_with_duplicates = pd.DataFrame({
            'user_id': [1, 1, 2, 2, 1],  # Duplicate: user 1, book 1
            'book_id': [1, 2, 1, 2, 1],
            'rating': [5, 4, 3, 4, 4]   # Different rating for same user-book
        })
        
        # Check for duplicates
        duplicates = data_with_duplicates.duplicated(subset=['user_id', 'book_id'])
        assert duplicates.sum() > 0  # Should detect duplicates
        
        # Remove duplicates (keep last)
        clean_data = data_with_duplicates.drop_duplicates(
            subset=['user_id', 'book_id'], 
            keep='last'
        )
        assert len(clean_data) == 4  # Should have 4 unique user-book pairs
    
    def test_outlier_detection(self):
        """Test detection of outliers in ratings"""
        # Create data with outliers
        normal_ratings = [3, 4, 4, 5, 3, 4, 5, 4]
        outlier_ratings = [10, -1]  # Invalid ratings
        
        all_ratings = normal_ratings + outlier_ratings
        
        # Detect outliers (ratings outside 1-5 range)
        outliers = [r for r in all_ratings if r < 1 or r > 5]
        assert len(outliers) == 2
        assert 10 in outliers
        assert -1 in outliers
    
    @pytest.mark.parametrize("missing_percentage,should_pass", [
        (0.0, True),   # No missing data
        (0.05, True),  # 5% missing - acceptable
        (0.15, False), # 15% missing - too much
        (0.5, False),  # 50% missing - definitely too much
    ])
    def test_missing_data_threshold(self, sample_ratings_data, missing_percentage, should_pass):
        """Test missing data thresholds"""
        # Introduce missing data
        data = sample_ratings_data.copy()
        n_missing = int(len(data) * missing_percentage)
        
        if n_missing > 0:
            missing_indices = np.random.choice(len(data), n_missing, replace=False)
            data.loc[missing_indices, 'rating'] = np.nan
        
        missing_ratio = data['rating'].isnull().sum() / len(data)
        
        if should_pass:
            assert missing_ratio <= 0.1  # 10% threshold
        else:
            assert missing_ratio > 0.1
```

### Data Pipeline Tests

Create `tests/data/test_data_pipeline.py`:

```python
import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import patch, Mock

from src.data.data_loader import DataLoader
from src.data.data_preprocessor import DataPreprocessor

class TestDataPipeline:
    """Test end-to-end data pipeline"""
    
    def test_full_data_pipeline(self, temp_data_dir):
        """Test complete data loading and preprocessing pipeline"""
        # Create test data files
        ratings_data = pd.DataFrame({
            'user_id': [1, 1, 2, 2, 3, 3, 1],  # Duplicate at end
            'book_id': [1, 2, 1, 3, 2, 3, 1],
            'rating': [5, 4, 4, 5, 3, 4, 4]    # Different rating for duplicate
        })
        
        books_data = pd.DataFrame({
            'book_id': [1, 2, 3],
            'title': ['Book One', 'Book Two', 'Book Three'],
            'authors': ['Author A', 'Author B', 'Author C'],
            'average_rating': [4.5, 4.0, 4.8],
            'ratings_count': [1000, 800, 1200]
        })
        
        # Save to CSV files
        ratings_path = os.path.join(temp_data_dir, 'ratings.csv')
        books_path = os.path.join(temp_data_dir, 'books.csv')
        
        ratings_data.to_csv(ratings_path, index=False)
        books_data.to_csv(books_path, index=False)
        
        # Test pipeline
        loader = DataLoader()
        
        # Load data
        loaded_ratings = loader._load_ratings_csv(ratings_path)
        loaded_books = loader._load_books_csv(books_path)
        
        # Verify data loaded correctly
        assert len(loaded_ratings) == 7  # Including duplicate
        assert len(loaded_books) == 3
        
        # Preprocess data (should remove duplicates)
        clean_ratings = loader._preprocess_ratings(loaded_ratings)
        
        # Should have 6 unique user-book pairs (duplicate removed)
        assert len(clean_ratings) == 6
        
        # Verify data consistency
        rating_books = set(clean_ratings['book_id'].unique())
        available_books = set(loaded_books['book_id'].unique())
        assert rating_books.issubset(available_books)
    
    def test_data_pipeline_error_handling(self, temp_data_dir):
        """Test error handling in data pipeline"""
        # Create invalid CSV file
        invalid_path = os.path.join(temp_data_dir, 'invalid.csv')
        with open(invalid_path, 'w') as f:
            f.write("invalid,csv,content\n1,2")
        
        loader = DataLoader()
        
        # Should handle malformed CSV gracefully
        with pytest.raises(Exception):  # Could be various exceptions
            loader._load_ratings_csv(invalid_path)
    
    def test_data_transformation_pipeline(self, sample_ratings_data):
        """Test data transformation steps"""
        preprocessor = DataPreprocessor()
        
        # Test normalization
        normalized_ratings = preprocessor.normalize_ratings(sample_ratings_data)
        
        # Ratings should be normalized to 0-1 range
        assert normalized_ratings['rating'].min() >= 0
        assert normalized_ratings['rating'].max() <= 1
        
        # Test user filtering
        filtered_data = preprocessor.filter_active_users(
            sample_ratings_data, 
            min_ratings=2
        )
        
        # Should only include users with 2+ ratings
        user_counts = filtered_data['user_id'].value_counts()
        assert all(count >= 2 for count in user_counts)
    
    def test_data_splitting(self, sample_ratings_data):
        """Test train/test data splitting"""
        preprocessor = DataPreprocessor()
        
        train_data, test_data = preprocessor.train_test_split(
            sample_ratings_data, 
            test_size=0.2, 
            random_state=42
        )
        
        # Check split proportions
        total_size = len(sample_ratings_data)
        train_size = len(train_data)
        test_size = len(test_data)
        
        assert train_size + test_size == total_size
        assert abs(test_size / total_size - 0.2) < 0.1  # Within 10% of target
        
        # Check no overlap
        train_indices = set(train_data.index)
        test_indices = set(test_data.index)
        assert len(train_indices.intersection(test_indices)) == 0
```

## 🤖 Model Testing

### Model Accuracy Tests

Create `tests/model/test_model_accuracy.py`:

```python
import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from unittest.mock import patch

from src.models.hybrid_recommender import HybridRecommender
from src.models.collaborative_filter import CollaborativeFilter
from src.models.content_filter import ContentFilter

class TestModelAccuracy:
    """Test model accuracy and performance metrics"""
    
    def create_test_train_split(self, ratings_data, test_ratio=0.2):
        """Create train/test split for evaluation"""
        # Sort by timestamp if available, otherwise random
        shuffled = ratings_data.sample(frac=1, random_state=42)
        
        split_idx = int(len(shuffled) * (1 - test_ratio))
        train_data = shuffled.iloc[:split_idx]
        test_data = shuffled.iloc[split_idx:]
        
        return train_data, test_data
    
    def test_collaborative_filter_accuracy(self, sample_ratings_data):
        """Test collaborative filtering accuracy"""
        train_data, test_data = self.create_test_train_split(sample_ratings_data)
        
        # Train model
        cf = CollaborativeFilter(n_factors=5, n_epochs=10)
        cf.fit(train_data)
        
        # Make predictions on test set
        predictions = []
        actuals = []
        
        for _, row in test_data.iterrows():
            pred = cf.predict(row['user_id'], row['book_id'])
            predictions.append(pred)
            actuals.append(row['rating'])
        
        # Calculate metrics
        mse = mean_squared_error(actuals, predictions)
        mae = mean_absolute_error(actuals, predictions)
        rmse = np.sqrt(mse)
        
        # Assertions for reasonable accuracy
        assert rmse < 2.0  # RMSE should be reasonable
        assert mae < 1.5   # MAE should be reasonable
        
        # Predictions should be in valid range
        assert all(1 <= p <= 5 for p in predictions)
    
    def test_content_filter_similarity(self, sample_books_data):
        """Test content-based filtering similarity"""
        cf = ContentFilter()
        cf.fit(sample_books_data)
        
        # Test similarity for each book
        for book_id in sample_books_data['book_id']:
            similar_books = cf.get_similar_books(book_id, n_recommendations=2)
            
            # Should return some similar books (unless only one book)
            if len(sample_books_data) > 1:
                assert len(similar_books) > 0
            
            # Similarity scores should be between 0 and 1
            for book in similar_books:
                assert 0 <= book['similarity'] <= 1
                assert book['book_id'] != book_id  # Shouldn't include itself
    
    def test_hybrid_model_performance(self, sample_ratings_data, sample_books_data):
        """Test hybrid model performance"""
        train_data, test_data = self.create_test_train_split(sample_ratings_data)
        
        # Train hybrid model
        hybrid = HybridRecommender(content_weight=0.3, collaborative_weight=0.7)
        hybrid.fit(train_data, sample_books_data)
        
        # Test recommendations for existing users
        for user_id in train_data['user_id'].unique()[:3]:  # Test first 3 users
            recommendations = hybrid.get_recommendations(
                user_id=user_id, 
                n_recommendations=3
            )
            
            # Should return recommendations
            assert len(recommendations) > 0
            assert len(recommendations) <= 3
            
            # Recommendations should have required fields
            for rec in recommendations:
                assert 'book_id' in rec
                assert 'score' in rec
                assert 'explanation' in rec
                assert 0 <= rec['score'] <= 1
    
    def test_model_consistency(self, sample_ratings_data, sample_books_data):
        """Test model prediction consistency"""
        hybrid = HybridRecommender()
        hybrid.fit(sample_ratings_data, sample_books_data)
        
        user_id = sample_ratings_data['user_id'].iloc[0]
        
        # Get recommendations multiple times
        recs1 = hybrid.get_recommendations(user_id=user_id, n_recommendations=5)
        recs2 = hybrid.get_recommendations(user_id=user_id, n_recommendations=5)
        
        # Results should be consistent (same order, same scores)
        assert len(recs1) == len(recs2)
        
        for r1, r2 in zip(recs1, recs2):
            assert r1['book_id'] == r2['book_id']
            assert abs(r1['score'] - r2['score']) < 1e-6
    
    def test_cold_start_handling(self, sample_ratings_data, sample_books_data):
        """Test handling of cold start problems"""
        hybrid = HybridRecommender()
        hybrid.fit(sample_ratings_data, sample_books_data)
        
        # Test new user (cold start)
        new_user_id = 9999
        recommendations = hybrid.get_recommendations(
            user_id=new_user_id, 
            n_recommendations=5
        )
        
        # Should still return recommendations (popular items or content-based)
        assert len(recommendations) > 0
        
        # Test new book (cold start)
        book_title = sample_books_data['title'].iloc[0]
        similar_books = hybrid.get_recommendations(
            book_title=book_title, 
            n_recommendations=3
        )
        
        # Should return similar books
        assert len(similar_books) > 0
    
    @pytest.mark.parametrize("content_weight,collaborative_weight", [
        (0.0, 1.0),  # Pure collaborative
        (1.0, 0.0),  # Pure content-based
        (0.5, 0.5),  # Balanced
        (0.3, 0.7),  # Collaborative-heavy
        (0.8, 0.2),  # Content-heavy
    ])
    def test_weight_combinations(self, sample_ratings_data, sample_books_data, 
                               content_weight, collaborative_weight):
        """Test different weight combinations in hybrid model"""
        hybrid = HybridRecommender(
            content_weight=content_weight,
            collaborative_weight=collaborative_weight
        )
        hybrid.fit(sample_ratings_data, sample_books_data)
        
        user_id = sample_ratings_data['user_id'].iloc[0]
        recommendations = hybrid.get_recommendations(
            user_id=user_id, 
            n_recommendations=3
        )
        
        # Should always return some recommendations
        assert len(recommendations) > 0
        
        # Scores should be valid
        for rec in recommendations:
            assert 0 <= rec['score'] <= 1
    
    def test_recommendation_diversity(self, sample_ratings_data, sample_books_data):
        """Test diversity of recommendations"""
        hybrid = HybridRecommender()
        hybrid.fit(sample_ratings_data, sample_books_data)
        
        user_id = sample_ratings_data['user_id'].iloc[0]
        recommendations = hybrid.get_recommendations(
            user_id=user_id, 
            n_recommendations=5
        )
        
        # All recommendations should be different books
        book_ids = [rec['book_id'] for rec in recommendations]
        assert len(book_ids) == len(set(book_ids))  # No duplicates
        
        # Scores should be in descending order
         scores = [rec['score'] for rec in recommendations]
         assert scores == sorted(scores, reverse=True)
 ```

## 🔄 CI/CD Testing

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    services:
      redis:
        image: redis:6-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Format check with black
      run: |
        black --check src tests
    
    - name: Type check with mypy
      run: |
        mypy src
    
    - name: Security check with bandit
      run: |
        bandit -r src
    
    - name: Test with pytest
      env:
        REDIS_HOST: localhost
        REDIS_PORT: 6379
      run: |
        pytest tests/ -v --cov=src --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: true
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
```

### Test Coverage Configuration

Create `.coveragerc`:

```ini
[run]
source = src
omit = 
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*
    */settings/*
    manage.py
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

show_missing = True
skip_covered = False
precision = 2

[html]
directory = htmlcov
```

## 📋 Best Practices

### Test Organization

1. **Follow AAA Pattern**:
   ```python
   def test_user_recommendation():
       # Arrange
       user_id = 123
       expected_books = [1, 2, 3]
       
       # Act
       recommendations = recommender.get_recommendations(user_id)
       
       # Assert
       actual_books = [r['book_id'] for r in recommendations]
       assert actual_books == expected_books
   ```

2. **Use Descriptive Test Names**:
   ```python
   # Good
   def test_collaborative_filter_returns_empty_list_for_new_user():
       pass
   
   # Bad
   def test_cf():
       pass
   ```

3. **Test One Thing at a Time**:
   ```python
   # Good - focused test
   def test_rating_validation_rejects_negative_values():
       with pytest.raises(ValueError):
           validate_rating(-1)
   
   def test_rating_validation_rejects_values_above_five():
       with pytest.raises(ValueError):
           validate_rating(6)
   
   # Bad - testing multiple things
   def test_rating_validation():
       with pytest.raises(ValueError):
           validate_rating(-1)
       with pytest.raises(ValueError):
           validate_rating(6)
   ```

### Test Data Management

1. **Use Factories for Test Data**:
   ```python
   # tests/factories.py
   import factory
   import pandas as pd
   
   class RatingFactory(factory.Factory):
       class Meta:
           model = dict
       
       user_id = factory.Sequence(lambda n: n + 1)
       book_id = factory.Sequence(lambda n: n + 1)
       rating = factory.Faker('random_int', min=1, max=5)
   
   def create_ratings_dataframe(n=100):
       ratings = [RatingFactory() for _ in range(n)]
       return pd.DataFrame(ratings)
   ```

2. **Isolate Test Data**:
   ```python
   @pytest.fixture
   def isolated_test_data():
       """Create isolated test data that doesn't affect other tests"""
       return create_ratings_dataframe(50)
   ```

### Performance Testing Guidelines

1. **Set Realistic Thresholds**:
   ```python
   @pytest.mark.performance
   def test_recommendation_response_time():
       start_time = time.time()
       recommendations = recommender.get_recommendations(user_id=1)
       end_time = time.time()
       
       response_time = end_time - start_time
       assert response_time < 2.0  # Should respond within 2 seconds
   ```

2. **Test with Realistic Data Sizes**:
   ```python
   @pytest.mark.slow
   def test_large_dataset_performance():
       # Test with 10k users, 1k books, 100k ratings
       large_dataset = create_large_test_dataset()
       
       start_time = time.time()
       recommender.fit(large_dataset)
       training_time = time.time() - start_time
       
       assert training_time < 300  # Should train within 5 minutes
   ```

## 🐛 Troubleshooting

### Common Test Issues

#### 1. Flaky Tests

**Problem**: Tests pass sometimes, fail other times

**Solutions**:
```python
# Use fixed random seeds
@pytest.fixture(autouse=True)
def set_random_seed():
    np.random.seed(42)
    random.seed(42)

# Use deterministic test data
@pytest.fixture
def deterministic_data():
    return pd.DataFrame({
        'user_id': [1, 1, 2, 2],
        'book_id': [1, 2, 1, 3],
        'rating': [5, 4, 4, 5]
    })

# Add retries for external dependencies
@pytest.mark.flaky(reruns=3)
def test_external_api():
    response = requests.get('http://external-api.com')
    assert response.status_code == 200
```

#### 2. Slow Tests

**Problem**: Tests take too long to run

**Solutions**:
```python
# Use smaller datasets for unit tests
@pytest.fixture
def small_dataset():
    return create_ratings_dataframe(n=10)  # Instead of 10000

# Mock expensive operations
@patch('src.models.expensive_computation')
def test_with_mocked_computation(mock_computation):
    mock_computation.return_value = 'mocked_result'
    # Test logic here

# Use pytest markers to separate fast/slow tests
@pytest.mark.slow
def test_full_model_training():
    pass

# Run only fast tests during development
# pytest -m "not slow"
```

#### 3. Memory Issues

**Problem**: Tests consume too much memory

**Solutions**:
```python
# Clean up after tests
@pytest.fixture
def recommender():
    rec = HybridRecommender()
    yield rec
    # Cleanup
    rec.clear_cache()
    del rec

# Use memory profiling
@pytest.mark.memory
def test_memory_usage():
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Run test logic
    recommender.fit(large_dataset)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Assert memory increase is reasonable (e.g., < 500MB)
    assert memory_increase < 500 * 1024 * 1024
```

#### 4. Database Test Issues

**Problem**: Database tests interfere with each other

**Solutions**:
```python
# Use transactions that rollback
@pytest.fixture
def db_transaction():
    connection = get_db_connection()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()

# Use separate test database
@pytest.fixture(scope='session')
def test_database():
    # Create test database
    create_test_db()
    yield
    # Drop test database
    drop_test_db()

# Clean up test data
@pytest.fixture(autouse=True)
def cleanup_test_data():
    yield
    # Clean up after each test
    clear_test_tables()
```

### Debugging Failed Tests

1. **Use pytest debugging flags**:
   ```bash
   # Stop on first failure
   pytest -x
   
   # Drop into debugger on failure
   pytest --pdb
   
   # Show local variables in traceback
   pytest -l
   
   # Verbose output
   pytest -v -s
   ```

2. **Add debug logging**:
   ```python
   import logging
   
   def test_with_debug_logging():
       logging.basicConfig(level=logging.DEBUG)
       logger = logging.getLogger(__name__)
       
       logger.debug("Starting test")
       result = some_function()
       logger.debug(f"Result: {result}")
       
       assert result == expected
   ```

3. **Use pytest fixtures for debugging**:
   ```python
   @pytest.fixture
   def debug_info(request):
       """Provide debug information for failed tests"""
       yield
       if request.node.rep_call.failed:
           print(f"Test {request.node.name} failed")
           print(f"Test file: {request.node.fspath}")
           # Add more debug info
   ```

## 📊 Test Metrics and Reporting

### Coverage Goals

- **Overall Coverage**: > 90%
- **Critical Paths**: 100% (recommendation logic, data validation)
- **API Endpoints**: 100%
- **Error Handling**: > 95%

### Test Execution Metrics

```bash
# Generate detailed test report
pytest --html=reports/report.html --self-contained-html

# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Performance profiling
pytest --profile --profile-svg
```

### Continuous Monitoring

```python
# tests/conftest.py
import time
import pytest

@pytest.fixture(autouse=True)
def track_test_performance(request):
    """Track test execution time"""
    start_time = time.time()
    yield
    end_time = time.time()
    
    duration = end_time - start_time
    test_name = request.node.name
    
    # Log slow tests
    if duration > 5.0:  # 5 seconds threshold
        print(f"SLOW TEST: {test_name} took {duration:.2f} seconds")
```

This comprehensive testing guide provides the foundation for maintaining high code quality and reliability in the GoodBooks Recommender system. Regular testing ensures that new features don't break existing functionality and that the system performs well under various conditions.
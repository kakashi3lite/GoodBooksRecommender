# Developer Guide

Comprehensive guide for developers working on the GoodBooks Recommender system.

## 📋 Table of Contents

- [Development Environment Setup](#-development-environment-setup)
- [Project Structure](#-project-structure)
- [Development Workflow](#-development-workflow)
- [Testing Strategy](#-testing-strategy)
- [Code Quality Standards](#-code-quality-standards)
- [Architecture Deep Dive](#-architecture-deep-dive)
- [Contributing Guidelines](#-contributing-guidelines)
- [Debugging Guide](#-debugging-guide)

## 🛠 Development Environment Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|----------|
| Python | 3.9-3.11 | Runtime environment |
| Git | 2.30+ | Version control |
| Docker | 20.10+ | Containerization |
| Redis | 6.0+ | Caching layer |
| PostgreSQL | 13+ | Database (optional) |

### Quick Setup

```bash
# 1. Clone and navigate
git clone https://github.com/kakashi3lite/GoodBooksRecommender.git
cd GoodBooksRecommender

# 2. Setup Python environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 4. Setup pre-commit hooks
pre-commit install

# 5. Run initial setup
python scripts/prepare_data.py
python scripts/train_model.py

# 6. Start development server
python -m uvicorn src.api.main:app --reload
```

### IDE Configuration

#### VS Code Settings

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true
    }
}
```

#### PyCharm Configuration

1. **Interpreter:** Set to `./venv/bin/python`
2. **Code Style:** Import `pyproject.toml` settings
3. **Run Configurations:**
   - **API Server:** `uvicorn src.api.main:app --reload`
   - **Tests:** `pytest tests/`

### Environment Variables

Create `.env` file:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG_MODE=true

# Database
DATABASE_URL=sqlite:///./goodbooks.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/goodbooks

# Cache
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL=3600

# Model Parameters
CONTENT_WEIGHT=0.5
N_FACTORS=50
LEARNING_RATE=0.01

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=DEBUG
```

## 📁 Project Structure

```
GoodBooksRecommender/
├── src/                          # Source code
│   ├── __init__.py
│   ├── api/                      # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py              # Main application entry
│   │   ├── auth.py              # Authentication middleware
│   │   ├── cache.py             # Redis caching layer
│   │   ├── docs.py              # API documentation
│   │   └── monitoring.py        # Prometheus metrics
│   ├── data/                     # Data processing
│   │   ├── __init__.py
│   │   └── data_loader.py       # Data loading utilities
│   ├── features/                 # Feature engineering
│   │   ├── __init__.py
│   │   └── feature_extractor.py # TF-IDF and similarity
│   ├── models/                   # ML models
│   │   ├── __init__.py
│   │   ├── collaborative_filter.py  # Matrix factorization
│   │   ├── hybrid_recommender.py    # Combined approach
│   │   ├── explainer.py         # Recommendation explanations
│   │   ├── model_manager.py     # Model lifecycle
│   │   ├── model_updater.py     # Online learning
│   │   └── ab_tester.py         # A/B testing framework
│   ├── analytics/                # Analytics and monitoring
│   │   ├── __init__.py
│   │   ├── user_analytics.py    # User behavior analysis
│   │   ├── recommendation_metrics.py  # Model performance
│   │   ├── cohort_analysis.py   # User cohort analysis
│   │   └── report_generator.py  # Automated reporting
│   ├── user/                     # User management
│   │   ├── __init__.py
│   │   ├── profile_manager.py   # User profiles
│   │   ├── interaction_tracker.py  # User interactions
│   │   └── notification_manager.py # User notifications
│   └── config.py                 # Configuration management
├── tests/                        # Test suites
│   ├── __init__.py
│   ├── test_api.py              # API endpoint tests
│   ├── test_models.py           # Model unit tests
│   ├── test_data.py             # Data processing tests
│   └── fixtures/                # Test data fixtures
├── scripts/                      # Utility scripts
│   ├── prepare_data.py          # Data preparation
│   ├── train_model.py           # Model training
│   └── monitor_performance.py   # Performance monitoring
├── data/                         # Dataset files
│   ├── books.csv
│   ├── ratings.csv
│   ├── tags.csv
│   └── book_tags.csv
├── docs/                         # Documentation
│   ├── README.md                # Main documentation
│   ├── API_REFERENCE.md         # API documentation
│   └── DEVELOPER_GUIDE.md       # This file
├── docker/                       # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── .github/                      # GitHub workflows
│   └── workflows/
│       ├── ci.yml               # Continuous integration
│       └── deploy.yml           # Deployment pipeline
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── pyproject.toml               # Project configuration
├── .gitignore
├── .pre-commit-config.yaml      # Pre-commit hooks
└── README.md                     # Project overview
```

### Module Responsibilities

#### `src/api/`
- **main.py:** FastAPI application setup, route definitions
- **auth.py:** Authentication and authorization middleware
- **cache.py:** Redis caching implementation
- **monitoring.py:** Prometheus metrics collection

#### `src/models/`
- **collaborative_filter.py:** Matrix factorization implementation
- **hybrid_recommender.py:** Combines content and collaborative filtering
- **explainer.py:** Generates recommendation explanations
- **model_manager.py:** Model versioning and deployment

#### `src/data/`
- **data_loader.py:** CSV/database data loading and preprocessing

#### `src/features/`
- **feature_extractor.py:** TF-IDF vectorization and similarity computation

## 🔄 Development Workflow

### Git Workflow

1. **Create Feature Branch**
```bash
git checkout main
git pull origin main
git checkout -b feature/recommendation-explanations
```

2. **Development Cycle**
```bash
# Make changes
vim src/models/explainer.py

# Run tests
pytest tests/test_explainer.py -v

# Check code quality
black src/
flake8 src/
mypy src/

# Commit changes
git add .
git commit -m "feat: add SHAP-based recommendation explanations"
```

3. **Push and Create PR**
```bash
git push origin feature/recommendation-explanations
# Create pull request on GitHub
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(api): add batch recommendation endpoint
fix(models): resolve memory leak in collaborative filter
docs(readme): update installation instructions
test(api): add integration tests for recommendations
```

### Branch Strategy

- **main:** Production-ready code
- **develop:** Integration branch for features
- **feature/*:** Individual feature development
- **hotfix/*:** Critical bug fixes
- **release/*:** Release preparation

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_models.py
│   ├── test_features.py
│   └── test_data.py
├── integration/             # Integration tests
│   ├── test_api.py
│   └── test_workflows.py
├── performance/             # Performance tests
│   └── test_load.py
├── fixtures/                # Test data
│   ├── sample_books.csv
│   └── sample_ratings.csv
└── conftest.py             # Pytest configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py -v

# Run tests matching pattern
pytest -k "test_recommendation" -v

# Run tests with markers
pytest -m "slow" -v
```

### Test Categories

#### Unit Tests
```python
import pytest
from src.models.collaborative_filter import CollaborativeFilter

class TestCollaborativeFilter:
    def test_initialization(self):
        cf = CollaborativeFilter(n_factors=10)
        assert cf.n_factors == 10
        assert cf.learning_rate == 0.01
    
    def test_fit_with_valid_data(self, sample_ratings):
        cf = CollaborativeFilter()
        cf.fit(sample_ratings)
        assert cf.is_fitted
        assert cf.user_factors is not None
    
    @pytest.mark.parametrize("n_factors", [10, 25, 50])
    def test_different_factor_sizes(self, n_factors, sample_ratings):
        cf = CollaborativeFilter(n_factors=n_factors)
        cf.fit(sample_ratings)
        assert cf.user_factors.shape[1] == n_factors
```

#### Integration Tests
```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

class TestRecommendationAPI:
    def test_user_recommendations_flow(self):
        # Test complete user recommendation flow
        response = client.post("/recommendations", 
                              json={"user_id": 1, "n_recommendations": 5})
        assert response.status_code == 200
        
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) == 5
        
        # Verify recommendation structure
        rec = data["recommendations"][0]
        assert "title" in rec
        assert "hybrid_score" in rec
        assert 0 <= rec["hybrid_score"] <= 1
```

#### Performance Tests
```python
import time
import pytest
from src.models.hybrid_recommender import HybridRecommender

class TestPerformance:
    @pytest.mark.slow
    def test_recommendation_speed(self, large_dataset):
        recommender = HybridRecommender()
        recommender.fit(*large_dataset)
        
        start_time = time.time()
        recommendations = recommender.get_recommendations(user_id=1)
        end_time = time.time()
        
        assert end_time - start_time < 0.5  # Should complete in < 500ms
```

### Test Fixtures

```python
# conftest.py
import pytest
import pandas as pd

@pytest.fixture
def sample_books():
    return pd.DataFrame({
        'book_id': [1, 2, 3],
        'title': ['Book A', 'Book B', 'Book C'],
        'authors': ['Author 1', 'Author 2', 'Author 3'],
        'average_rating': [4.5, 3.8, 4.2]
    })

@pytest.fixture
def sample_ratings():
    return pd.DataFrame({
        'user_id': [1, 1, 2, 2, 3],
        'book_id': [1, 2, 1, 3, 2],
        'rating': [5, 4, 3, 5, 4]
    })

@pytest.fixture(scope="session")
def test_client():
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)
```

## 📏 Code Quality Standards

### Code Formatting

**Black Configuration** (pyproject.toml):
```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
(
  /(
      \.eggs
    | \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
  )/
)
'''
```

### Linting

**Flake8 Configuration** (.flake8):
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    build,
    dist
max-complexity = 10
```

### Type Checking

**MyPy Configuration** (pyproject.toml):
```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Pre-commit Hooks

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Documentation Standards

#### Docstring Format

Use Google-style docstrings:

```python
def get_recommendations(self, user_id: int, n_recommendations: int = 5) -> pd.DataFrame:
    """Generate personalized book recommendations for a user.
    
    Args:
        user_id: Unique identifier for the user
        n_recommendations: Number of recommendations to return
        
    Returns:
        DataFrame containing recommended books with scores
        
    Raises:
        ValueError: If user_id is not found in the system
        ModelNotFittedError: If the model hasn't been trained
        
    Example:
        >>> recommender = HybridRecommender()
        >>> recommender.fit(books, ratings)
        >>> recs = recommender.get_recommendations(user_id=123, n_recommendations=10)
        >>> print(f"Found {len(recs)} recommendations")
    """
```

#### Type Hints

Use comprehensive type hints:

```python
from typing import List, Dict, Optional, Union, Tuple
import pandas as pd
import numpy as np

class HybridRecommender:
    def __init__(self, content_weight: float = 0.5) -> None:
        self.content_weight = content_weight
        self.books_data: Optional[pd.DataFrame] = None
    
    def get_recommendations(
        self, 
        user_id: Optional[int] = None,
        book_title: Optional[str] = None,
        n_recommendations: int = 5
    ) -> pd.DataFrame:
        # Implementation
        pass
```

## 🏗 Architecture Deep Dive

### Recommendation Pipeline

```mermaid
graph TD
    A[User Request] --> B[Request Validation]
    B --> C{Cache Hit?}
    C -->|Yes| D[Return Cached Results]
    C -->|No| E[Load User/Book Data]
    E --> F[Content-Based Filtering]
    E --> G[Collaborative Filtering]
    F --> H[Hybrid Score Calculation]
    G --> H
    H --> I[Rank & Filter Results]
    I --> J[Generate Explanations]
    J --> K[Cache Results]
    K --> L[Return Response]
```

### Model Architecture

#### Collaborative Filtering

```python
class CollaborativeFilter:
    """Matrix Factorization using Alternating Least Squares.
    
    Mathematical Foundation:
    R ≈ U × V^T
    
    Where:
    - R: User-Item rating matrix (m × n)
    - U: User factor matrix (m × k)
    - V: Item factor matrix (n × k)
    - k: Number of latent factors
    """
    
    def __init__(self, n_factors: int = 50, learning_rate: float = 0.01):
        self.n_factors = n_factors
        self.learning_rate = learning_rate
    
    def fit(self, ratings: pd.DataFrame) -> None:
        """Train the model using ALS algorithm."""
        # Initialize factor matrices
        self.user_factors = np.random.normal(0, 0.1, (n_users, self.n_factors))
        self.item_factors = np.random.normal(0, 0.1, (n_items, self.n_factors))
        
        # Alternating optimization
        for epoch in range(self.n_epochs):
            self._update_user_factors(ratings)
            self._update_item_factors(ratings)
```

#### Content-Based Filtering

```python
class FeatureExtractor:
    """TF-IDF based content similarity.
    
    Process:
    1. Combine book metadata (title, authors, tags)
    2. Apply TF-IDF vectorization
    3. Compute cosine similarity matrix
    4. Find most similar books
    """
    
    def fit_transform(self, books: pd.DataFrame) -> np.ndarray:
        # Combine text features
        text_features = books['title'] + ' ' + books['authors'] + ' ' + books['tags']
        
        # TF-IDF vectorization
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        tfidf_matrix = self.vectorizer.fit_transform(text_features)
        
        # Compute similarity matrix
        self.similarity_matrix = cosine_similarity(tfidf_matrix)
        return self.similarity_matrix
```

### Caching Strategy

```python
class RecommendationCache:
    """Redis-based caching for recommendations.
    
    Cache Keys:
    - user:{user_id}:recs:{n_recs} -> User-based recommendations
    - book:{book_title}:similar:{n_recs} -> Content-based recommendations
    - hybrid:{user_id}:{book_title}:{n_recs} -> Hybrid recommendations
    """
    
    def __init__(self, redis_client, ttl: int = 3600):
        self.redis = redis_client
        self.ttl = ttl
    
    def get_user_recommendations(self, user_id: int, n_recs: int) -> Optional[List[Dict]]:
        key = f"user:{user_id}:recs:{n_recs}"
        cached = self.redis.get(key)
        return json.loads(cached) if cached else None
    
    def cache_recommendations(self, key: str, recommendations: List[Dict]) -> None:
        self.redis.setex(key, self.ttl, json.dumps(recommendations))
```

## 🤝 Contributing Guidelines

### Pull Request Process

1. **Fork and Clone**
```bash
git clone https://github.com/yourusername/GoodBooksRecommender.git
```

2. **Create Feature Branch**
```bash
git checkout -b feature/amazing-feature
```

3. **Development Checklist**
- [ ] Code follows style guidelines
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No linting errors

4. **Commit and Push**
```bash
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

5. **Create Pull Request**
- Use descriptive title
- Fill out PR template
- Link related issues
- Request reviews

### Code Review Guidelines

#### For Authors
- Keep PRs small and focused
- Write clear commit messages
- Add tests for new features
- Update documentation
- Respond to feedback promptly

#### For Reviewers
- Review within 24 hours
- Focus on logic, not style (automated)
- Suggest improvements, don't just criticize
- Approve when ready

### Issue Templates

#### Bug Report
```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g. Windows 10]
- Python: [e.g. 3.9.7]
- Version: [e.g. 1.0.0]
```

#### Feature Request
```markdown
**Feature Description**
A clear description of the feature.

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives**
Other solutions you've considered.
```

## 🐛 Debugging Guide

### Common Issues

#### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Ensure you're in project root
pwd

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run with module flag
python -m src.api.main
```

#### Memory Issues

**Problem:** High memory usage during model training

**Solutions:**
```python
# 1. Reduce dataset size for development
ratings_sample = ratings.sample(n=50000)

# 2. Adjust model parameters
MODEL_PARAMS = {
    'collaborative': {
        'n_factors': 25,  # Reduce from 50
        'n_epochs': 10    # Reduce from 20
    }
}

# 3. Use batch processing
for batch in pd.read_csv('large_file.csv', chunksize=10000):
    process_batch(batch)
```

#### Performance Issues

**Problem:** Slow API responses

**Debugging:**
```python
import time
import logging

logger = logging.getLogger(__name__)

def timed_function(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

@timed_function
def get_recommendations(user_id):
    # Your implementation
    pass
```

### Logging Configuration

```python
# src/config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# Usage in modules
logger = logging.getLogger(__name__)
logger.info("Starting recommendation generation")
logger.error(f"Failed to load model: {error}")
```

### Profiling

```python
# Performance profiling
import cProfile
import pstats

def profile_recommendations():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    get_recommendations(user_id=123)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    pass
```

### Testing in Development

```bash
# Run API with debug mode
DEBUG_MODE=true python -m uvicorn src.api.main:app --reload

# Test specific endpoint
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}' | jq

# Monitor logs
tail -f logs/app.log

# Check Redis cache
redis-cli
> KEYS *
> GET user:123:recs:5
```

---

**Happy Coding! 🚀**

For questions or support, please:
- Check existing [GitHub Issues](https://github.com/kakashi3lite/GoodBooksRecommender/issues)
- Start a [Discussion](https://github.com/kakashi3lite/GoodBooksRecommender/discussions)
- Contact the maintainers
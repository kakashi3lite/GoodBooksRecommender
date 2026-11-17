# docs/ — Documentation

> ⚠️ Most files in this folder document the **legacy Python/FastAPI stack**, which is
> **not deployed**. For the live product start at
> [`../HANDOFF.md`](../HANDOFF.md), [`../ARCHITECTURE.md`](../ARCHITECTURE.md) and
> [`LIVE_ARCHITECTURE_RUNBOOK.md`](LIVE_ARCHITECTURE_RUNBOOK.md).

**Every document, grouped by task → [`../DOCUMENTATION_INDEX.md`](../DOCUMENTATION_INDEX.md).**

Live-system documents in this folder:

| Document | Purpose |
|---|---|
| [`LIVE_ARCHITECTURE_RUNBOOK.md`](LIVE_ARCHITECTURE_RUNBOOK.md) | Operations, endpoints, incidents, verification logs |
| [`ACCOUNTS.md`](ACCOUNTS.md) | Customer accounts on D1 — contract + upgrade context |
| [`DATA_LAYER.md`](DATA_LAYER.md) | Data flow and recommender rationale |
| [`PROJECT_STATUS.md`](PROJECT_STATUS.md) | Honest status |
| [`archive/`](archive/README.md) | Historical reports (never authoritative) |

The legacy reference material follows.

---

A sophisticated book recommendation engine that combines content-based and collaborative filtering approaches to provide personalized book recommendations.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [User Personas](#-user-personas)
- [Architecture Overview](#-architecture-overview)
- [API Reference](#-api-reference)
- [Installation Guide](#-installation-guide)
- [Development Guide](#-development-guide)
- [Troubleshooting](#-troubleshooting)
- [Performance & Analytics](#-performance--analytics)

## 🚀 Quick Start

### For API Consumers
```bash
# Get recommendations for a user
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "n_recommendations": 5}'

# Get similar books based on a title
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{"book_title": "1984", "n_recommendations": 5}'
```

### For Developers
```bash
git clone https://github.com/kakashi3lite/GoodBooksRecommender.git
cd GoodBooksRecommender
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn src.api.main:app --reload
```

## 👥 User Personas

### 1. API Consumer (Frontend Developer)
**Goals:** Integrate book recommendations into web/mobile applications
**Pain Points:** Need fast, reliable API responses with clear documentation
**Journey:** API Discovery → Integration → Testing → Production

**Key Needs:**
- Clear API endpoints and request/response formats
- Authentication and rate limiting information
- Error handling examples
- Performance benchmarks

### 2. Data Scientist (ML Engineer)
**Goals:** Understand and improve recommendation algorithms
**Pain Points:** Need to analyze model performance and experiment with parameters
**Journey:** Model Understanding → Experimentation → Optimization → Deployment

**Key Needs:**
- Algorithm explanations and mathematical foundations
- Model configuration options
- Performance metrics and evaluation methods
- Training and retraining procedures

### 3. DevOps Engineer (Infrastructure)
**Goals:** Deploy and maintain the recommendation system
**Pain Points:** Need scalable, monitorable deployment solutions
**Journey:** Setup → Deployment → Monitoring → Scaling

**Key Needs:**
- Docker and Kubernetes configurations
- Monitoring and logging setup
- Performance tuning guidelines
- Backup and recovery procedures

### 4. End User (Book Reader)
**Goals:** Discover new books based on preferences
**Pain Points:** Want relevant, diverse recommendations with explanations
**Journey:** Search → Discover → Evaluate → Read

**Key Needs:**
- Personalized recommendations
- Explanation of why books were recommended
- Diverse recommendation types (similar authors, genres, themes)
- Rating and feedback mechanisms

## 🏗 Architecture Overview

```
GoodBooksRecommender/
├── src/
│   ├── api/                 # FastAPI REST endpoints
│   │   ├── main.py         # Main application entry
│   │   ├── auth.py         # Authentication middleware
│   │   ├── cache.py        # Redis caching layer
│   │   └── monitoring.py   # Performance monitoring
│   ├── data/               # Data processing pipeline
│   │   └── data_loader.py  # CSV/Database data loading
│   ├── features/           # Feature engineering
│   │   └── feature_extractor.py  # TF-IDF and similarity
│   ├── models/             # ML recommendation models
│   │   ├── collaborative_filter.py  # Matrix factorization
│   │   ├── hybrid_recommender.py    # Combined approach
│   │   └── explainer.py    # Recommendation explanations
│   ├── analytics/          # Performance analytics
│   └── user/              # User management
├── data/                   # Dataset files
├── tests/                  # Test suites
└── docs/                   # Documentation
```

### Core Components

1. **Hybrid Recommendation Engine**
   - Content-based filtering using TF-IDF on book metadata
   - Collaborative filtering with matrix factorization
   - Weighted combination for optimal recommendations

2. **FastAPI REST Service**
   - High-performance async API endpoints
   - Automatic OpenAPI documentation
   - Request validation with Pydantic

3. **Caching Layer**
   - Redis for recommendation caching
   - Configurable TTL and cache strategies
   - Performance optimization

4. **Analytics & Monitoring**
   - Prometheus metrics collection
   - Performance tracking
   - User behavior analytics

## 📚 API Reference

### Base URL
```
Production: https://api.goodbooks.com
Development: http://localhost:8000
```

### Authentication
Currently, the API is open access. Authentication will be added in future versions.

### Endpoints

#### GET /
**Description:** Health check endpoint

**Response:**
```json
{
  "message": "GoodBooks Recommender API is running"
}
```

#### GET /health
**Description:** Detailed health status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

#### POST /recommendations
**Description:** Get personalized book recommendations

**Request Body:**
```json
{
  "user_id": 123,              // Optional: User ID for collaborative filtering
  "book_title": "1984",        // Optional: Book title for content-based filtering
  "n_recommendations": 5       // Optional: Number of recommendations (default: 5)
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Brave New World",
      "authors": "Aldous Huxley",
      "average_rating": 4.5,
      "hybrid_score": 0.95
    }
  ],
  "explanation": {
    "top_tags": ["dystopian", "classics", "science-fiction"],
    "similar_books": ["Animal Farm", "Fahrenheit 451"],
    "reasoning": "Based on your interest in dystopian literature"
  }
}
```

**Error Responses:**
```json
// 400 Bad Request
{
  "detail": "Either user_id or book_title must be provided"
}

// 500 Internal Server Error
{
  "detail": "Recommendation engine temporarily unavailable"
}
```

### Rate Limiting
- **Development:** No limits
- **Production:** 100 requests per minute per IP

### Response Times
- **Target:** < 100ms for cached recommendations
- **Maximum:** < 500ms for new recommendations

## 🛠 Installation Guide

### Prerequisites
- Python 3.9-3.11
- 4GB+ RAM recommended
- Docker (optional)
- Redis (for caching)

### Local Development Setup

1. **Clone Repository**
```bash
git clone https://github.com/kakashi3lite/GoodBooksRecommender.git
cd GoodBooksRecommender
```

2. **Create Virtual Environment**
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup Data**
```bash
# Download datasets (if not included)
python scripts/prepare_data.py
```

5. **Start Services**
```bash
# Start Redis (if using caching)
redis-server

# Start API server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup

1. **Using Docker Compose (Recommended)**
```bash
docker-compose up --build
```

2. **Manual Docker Build**
```bash
docker build -t goodbooks-recommender .
docker run -p 8000:8000 goodbooks-recommender
```

### Production Deployment

1. **Environment Variables**
```bash
export API_HOST=0.0.0.0
export API_PORT=8000
export REDIS_HOST=redis.example.com
export REDIS_PORT=6379
export DEBUG_MODE=false
```

2. **Using Gunicorn**
```bash
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 💻 Development Guide

### Code Structure

#### Adding New Recommendation Models

1. Create model class in `src/models/`
2. Implement required interface:
```python
class NewRecommender:
    def fit(self, data):
        """Train the model"""
        pass
    
    def predict(self, user_id, n_recommendations):
        """Generate recommendations"""
        pass
```

3. Update `HybridRecommender` to include new model

#### Adding New API Endpoints

1. Add endpoint to `src/api/main.py`:
```python
@app.get("/new-endpoint")
async def new_endpoint():
    return {"message": "New endpoint"}
```

2. Add request/response models if needed:
```python
class NewRequest(BaseModel):
    field: str

class NewResponse(BaseModel):
    result: str
```

### Testing

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_api.py
```

#### Writing Tests
```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_recommendations():
    response = client.post("/recommendations", 
                          json={"user_id": 1})
    assert response.status_code == 200
    assert "recommendations" in response.json()
```

### Code Quality

#### Formatting
```bash
# Format code
black src/

# Check formatting
black --check src/
```

#### Linting
```bash
# Run linter
flake8 src/

# Fix common issues
autopep8 --in-place --recursive src/
```

### Git Workflow

1. **Create Feature Branch**
```bash
git checkout -b feature/new-feature
```

2. **Make Changes and Commit**
```bash
git add .
git commit -m "feat: add new recommendation algorithm"
```

3. **Push and Create PR**
```bash
git push origin feature/new-feature
# Create pull request on GitHub
```

## 🔧 Troubleshooting

### Common Issues

#### API Server Won't Start

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Ensure you're in the project root
pwd  # Should show .../GoodBooksRecommender

# Run with module flag
python -m uvicorn src.api.main:app
```

#### Slow Recommendation Response

**Problem:** API responses taking > 1 second

**Solutions:**
1. Check Redis connection:
```bash
redis-cli ping  # Should return PONG
```

2. Monitor cache hit rate:
```bash
curl http://localhost:8000/metrics | grep cache_hit_rate
```

3. Reduce recommendation count:
```json
{"user_id": 123, "n_recommendations": 3}
```

#### Memory Issues

**Problem:** High memory usage during training

**Solutions:**
1. Reduce dataset size for development:
```python
# In data_loader.py
ratings = ratings.sample(n=100000)  # Use subset
```

2. Adjust model parameters:
```python
# In config.py
MODEL_PARAMS = {
    'collaborative': {
        'n_factors': 25,  # Reduce from 50
        'n_epochs': 10    # Reduce from 20
    }
}
```

#### Database Connection Errors

**Problem:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Update connection string in config
export DATABASE_URL="postgresql://user:pass@localhost:5432/goodbooks"
```

### Debug Mode

Enable debug mode for detailed error messages:
```bash
export DEBUG_MODE=true
python -m uvicorn src.api.main:app --reload
```

### Logging

View application logs:
```bash
# Docker logs
docker-compose logs -f api

# Local logs
tail -f logs/app.log
```

## 📈 Performance & Analytics

### Key Metrics

- **Response Time:** < 100ms (target)
- **Cache Hit Ratio:** > 80%
- **Recommendation Accuracy:** RMSE < 0.9
- **API Uptime:** > 99.9%

### Monitoring

#### Prometheus Metrics
```bash
# View metrics
curl http://localhost:8000/metrics

# Key metrics to monitor:
# - recommendation_request_duration_seconds
# - cache_hit_total
# - model_prediction_accuracy
```

#### Performance Tuning

1. **Enable Caching**
```python
# In config.py
CACHE_TTL = 3600  # 1 hour
REDIS_HOST = 'localhost'
```

2. **Optimize Model Parameters**
```python
# Balance accuracy vs speed
MODEL_PARAMS = {
    'collaborative': {
        'n_factors': 50,      # Higher = more accurate, slower
        'n_epochs': 20        # Higher = more accurate, slower training
    }
}
```

3. **Scale Horizontally**
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
```

### Analytics Dashboard

Access analytics at: `http://localhost:8000/analytics`

- User behavior patterns
- Popular book categories
- Recommendation effectiveness
- System performance metrics

---

## 📞 Support

- **Documentation:** [GitHub Wiki](https://github.com/kakashi3lite/GoodBooksRecommender/wiki)
- **Issues:** [GitHub Issues](https://github.com/kakashi3lite/GoodBooksRecommender/issues)
- **Discussions:** [GitHub Discussions](https://github.com/kakashi3lite/GoodBooksRecommender/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
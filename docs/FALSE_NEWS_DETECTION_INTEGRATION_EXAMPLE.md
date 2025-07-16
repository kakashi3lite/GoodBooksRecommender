# 🚀 False News Detection System - Integration Example

This example shows how to integrate the False News Detection System with the existing GoodBooksRecommender infrastructure.

## 🔧 Integration Steps

### Step 1: Add to Main FastAPI Application

```python
# In src/api/main.py, add the fake news detection router

from src.fakenews.api.detection import fakenews_router

# Add to your existing FastAPI app
app.include_router(fakenews_router, prefix="/api/v1")
```

### Step 2: Extend Database Models

```python
# In src/models/ (extend existing models)

from src.fakenews.models.schemas import DetectionRequest, DetectionResponse

# Add to existing User model
class User(Base):
    # ... existing fields ...
    fakenews_requests = relationship("FakeNewsRequest", back_populates="user")
    fakenews_quota_used = Column(Integer, default=0)
    fakenews_quota_limit = Column(Integer, default=100)
```

### Step 3: Extend Authentication

```python
# In src/auth/security.py, add new permissions

class FakeNewsPermission(Permission):
    ANALYZE_CONTENT = "fakenews:analyze"
    VIEW_RESULTS = "fakenews:view_results"
    ADMIN_ACCESS = "fakenews:admin"
    BATCH_ANALYZE = "fakenews:batch"
    DEEP_ANALYSIS = "fakenews:deep_analysis"

# Add rate limiting rules
FAKENEWS_RATE_LIMITS = {
    UserRole.FREE: {"analyze": "10/hour", "batch": "2/hour"},
    UserRole.PREMIUM: {"analyze": "100/hour", "batch": "20/hour"},
    UserRole.ENTERPRISE: {"analyze": "1000/hour", "batch": "100/hour"}
}
```

### Step 4: Environment Configuration

```bash
# Add to .env file

# Fake News Detection Settings
FAKENEWS_OPENAI_API_KEY=your-openai-key
FAKENEWS_CLAUDE_API_KEY=your-claude-key
FAKENEWS_NEO4J_URI=bolt://localhost:7687
FAKENEWS_NEO4J_USER=neo4j
FAKENEWS_NEO4J_PASSWORD=your-password

# External API Keys
FAKENEWS_FACTCHECK_API_KEY=your-factcheck-key
FAKENEWS_GOOGLE_VISION_API_KEY=your-google-vision-key
FAKENEWS_TINEYE_API_KEY=your-tineye-key

# Performance Settings
FAKENEWS_MODEL_CACHE_SIZE=5
FAKENEWS_RESULT_CACHE_TTL=3600
FAKENEWS_MAX_ANALYSIS_TIMEOUT=300
```

## 🧪 Usage Examples

### Example 1: Simple Text Analysis

```python
import requests

# Login to get JWT token
login_response = requests.post("http://localhost:8000/auth/login", json={
    "username": "user@example.com",
    "password": "password"
})
token = login_response.json()["access_token"]

# Analyze text for fake news
response = requests.post(
    "http://localhost:8000/api/v1/fakenews/detect",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "text_content": "Breaking: Scientists discover cure for aging using simple household items!",
        "source_url": "https://example.com/breaking-news",
        "analysis_depth": "standard",
        "require_explanation": True
    }
)

result = response.json()
print(f"Verdict: {result['verdict']}")
print(f"Confidence: {result['confidence_score']}")
print(f"Explanation: {result['explanation']['summary']}")
```

### Example 2: Image Analysis

```python
# Analyze image for fake content
response = requests.post(
    "http://localhost:8000/api/v1/fakenews/detect",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "image_urls": ["https://example.com/suspicious-image.jpg"],
        "text_content": "This photo shows the event happening yesterday",
        "analysis_depth": "deep",
        "require_explanation": True
    }
)

result = response.json()
print(f"Media Authenticity: {result['media_authenticity']}")
print(f"Deepfake Score: {result['deepfake_probability']}")
```

### Example 3: Batch Processing

```python
# Batch analysis of multiple articles
batch_request = {
    "items": [
        {"text_content": "Article 1 content...", "analysis_depth": "quick"},
        {"text_content": "Article 2 content...", "analysis_depth": "quick"},
        {"text_content": "Article 3 content...", "analysis_depth": "quick"}
    ],
    "batch_name": "daily_news_analysis",
    "callback_url": "https://yourapp.com/webhook/batch-complete"
}

response = requests.post(
    "http://localhost:8000/api/v1/fakenews/batch",
    headers={"Authorization": f"Bearer {token}"},
    json=batch_request
)

batch_id = response.json()["batch_id"]

# Poll for results
import time
while True:
    status_response = requests.get(
        f"http://localhost:8000/api/v1/fakenews/batch/{batch_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    batch_status = status_response.json()
    if batch_status["status"] == "completed":
        print("Batch processing completed!")
        for result in batch_status["results"]:
            print(f"Article: {result['verdict']} (confidence: {result['confidence_score']})")
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again
```

### Example 4: Real-time WebSocket Updates

```javascript
// JavaScript client for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/analysis/request-id-here');

ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    
    if (update.message_type === 'progress_update') {
        console.log(`Progress: ${update.data.progress * 100}%`);
        console.log(`Current stage: ${update.data.current_stage}`);
    } else if (update.message_type === 'analysis_complete') {
        console.log('Analysis completed!');
        console.log(`Verdict: ${update.data.verdict}`);
    }
};
```

## 📊 Monitoring Dashboard Integration

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "False News Detection System",
    "panels": [
      {
        "title": "Detection Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(fakenews_detection_requests_total[5m])",
            "legendFormat": "Requests per second"
          }
        ]
      },
      {
        "title": "Model Performance",
        "type": "stat",
        "targets": [
          {
            "expr": "fakenews_model_accuracy_score",
            "legendFormat": "Accuracy"
          }
        ]
      },
      {
        "title": "Response Times",
        "type": "heatmap",
        "targets": [
          {
            "expr": "fakenews_detection_duration_seconds",
            "legendFormat": "Duration"
          }
        ]
      },
      {
        "title": "Verdict Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "fakenews_verdicts_total",
            "legendFormat": "{{verdict}}"
          }
        ]
      }
    ]
  }
}
```

## 🧪 Testing Examples

### Unit Tests

```python
# tests/test_fakenews_api.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_detect_fake_news():
    # Login to get token
    login_response = client.post("/auth/login", json={
        "username": "test@example.com",
        "password": "testpassword"
    })
    token = login_response.json()["access_token"]
    
    # Test detection
    response = client.post(
        "/api/v1/fakenews/detect",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "text_content": "This is a test article about fake news detection.",
            "analysis_depth": "quick"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "verdict" in data
    assert "confidence_score" in data
    assert data["confidence_score"] >= 0.0
    assert data["confidence_score"] <= 1.0

def test_batch_processing():
    # Test batch processing endpoint
    login_response = client.post("/auth/login", json={
        "username": "test@example.com",
        "password": "testpassword"
    })
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/v1/fakenews/batch",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "items": [
                {"text_content": "Test article 1", "analysis_depth": "quick"},
                {"text_content": "Test article 2", "analysis_depth": "quick"}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert data["total_items"] == 2

def test_health_check():
    response = client.get("/api/v1/fakenews/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
```

### Integration Tests

```python
# tests/test_fakenews_integration.py
import pytest
import asyncio
from src.fakenews.services.detection_service import DetectionService
from src.fakenews.models.schemas import DetectionRequest, AnalysisDepth

@pytest.mark.asyncio
async def test_end_to_end_detection():
    """Test complete detection pipeline."""
    service = DetectionService()
    
    request = DetectionRequest(
        text_content="Scientists claim they found a cure for aging using this one weird trick!",
        analysis_depth=AnalysisDepth.STANDARD,
        require_explanation=True
    )
    
    result = await service.analyze_content(request, user_id=1)
    
    assert result.verdict in ["authentic", "misleading", "false", "uncertain"]
    assert 0.0 <= result.confidence_score <= 1.0
    assert result.explanation is not None
    assert len(result.evidence) > 0

@pytest.mark.asyncio
async def test_ml_model_integration():
    """Test ML model integration."""
    from src.fakenews.ml.ensemble_models import EnsembleDetector
    
    detector = EnsembleDetector()
    
    prediction = await detector.predict(
        "Breaking news: Aliens have landed and they brought the cure for cancer!"
    )
    
    assert prediction.verdict in ["authentic", "misleading", "false", "uncertain"]
    assert 0.0 <= prediction.confidence <= 1.0
    assert len(prediction.model_scores) > 0
```

## 🔒 Security Considerations

### API Security Configuration

```python
# Security middleware configuration
FAKENEWS_SECURITY_CONFIG = {
    "rate_limits": {
        "detect": "100/hour",
        "batch": "10/hour",
        "deep_analysis": "20/hour"
    },
    "input_validation": {
        "max_text_length": 50000,
        "max_image_size": 10485760,  # 10MB
        "allowed_file_types": ["jpg", "jpeg", "png", "gif", "mp4", "avi", "mov"]
    },
    "content_filtering": {
        "malicious_patterns": True,
        "xss_protection": True,
        "sql_injection_protection": True
    }
}
```

## 📈 Performance Optimization

### Caching Strategy

```python
# Multi-level caching implementation
class FakeNewsCacheManager:
    def __init__(self):
        self.redis_client = Redis()
        self.memory_cache = {}
    
    async def get_detection_result(self, content_hash: str):
        # L1: Memory cache
        if content_hash in self.memory_cache:
            return self.memory_cache[content_hash]
        
        # L2: Redis cache
        result = await self.redis_client.get(f"detection:{content_hash}")
        if result:
            self.memory_cache[content_hash] = result
            return result
        
        return None
    
    async def cache_detection_result(self, content_hash: str, result: dict):
        # Cache in both levels
        self.memory_cache[content_hash] = result
        await self.redis_client.setex(
            f"detection:{content_hash}", 
            3600,  # 1 hour TTL
            json.dumps(result)
        )
```

## 🚀 Deployment Configuration

### Docker Compose Extension

```yaml
# Add to existing docker-compose.yml
services:
  fakenews-detector:
    build:
      context: .
      dockerfile: Dockerfile.fakenews
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - FAKENEWS_OPENAI_API_KEY=${FAKENEWS_OPENAI_API_KEY}
      - FAKENEWS_CLAUDE_API_KEY=${FAKENEWS_CLAUDE_API_KEY}
    ports:
      - "8001:8000"
    depends_on:
      - postgres
      - redis
      - neo4j
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    networks:
      - goodbooks-network

  neo4j:
    image: neo4j:5.0
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
    networks:
      - goodbooks-network

volumes:
  neo4j_data:
```

This integration example shows how the False News Detection System seamlessly integrates with the existing GoodBooksRecommender infrastructure while maintaining modularity and scalability.

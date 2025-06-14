# API Reference Guide

## Overview

The GoodBooks Recommender API provides RESTful endpoints for generating personalized book recommendations using hybrid machine learning algorithms.

**Base URL:** `http://localhost:8000` (development)

**Content Type:** `application/json`

**API Version:** `1.0.0`

## Authentication

> **Note:** Currently, the API is open access. Authentication will be implemented in future versions.

## Rate Limiting

| Environment | Limit | Window |
|-------------|-------|--------|
| Development | Unlimited | - |
| Production | 100 requests | 1 minute |

## Endpoints

### Health Check

#### `GET /`

Basic health check endpoint.

**Response:**
```json
{
  "message": "GoodBooks Recommender API is running"
}
```

**Status Codes:**
- `200 OK` - Service is running

---

#### `GET /health`

Detailed health status with system information.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": 3600,
  "cache_status": "connected",
  "model_status": "loaded"
}
```

**Status Codes:**
- `200 OK` - All systems healthy
- `503 Service Unavailable` - System issues detected

---

### Recommendations

#### `POST /recommendations`

Generate personalized book recommendations using hybrid filtering.

**Request Body:**
```json
{
  "user_id": 123,              // Optional: Integer user ID
  "book_title": "1984",        // Optional: String book title
  "n_recommendations": 5       // Optional: Integer (1-50, default: 5)
}
```

**Request Validation:**
- At least one of `user_id` or `book_title` must be provided
- `n_recommendations` must be between 1 and 50
- `book_title` must be a non-empty string if provided
- `user_id` must be a positive integer if provided

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Brave New World",
      "authors": "Aldous Huxley",
      "average_rating": 4.5,
      "hybrid_score": 0.95,
      "book_id": 5470,
      "isbn": "9780060850524",
      "publication_year": 1932,
      "tags": ["dystopian", "classics", "science-fiction"]
    },
    {
      "title": "Animal Farm",
      "authors": "George Orwell",
      "average_rating": 4.3,
      "hybrid_score": 0.92,
      "book_id": 7613,
      "isbn": "9780451526342",
      "publication_year": 1945,
      "tags": ["dystopian", "classics", "political"]
    }
  ],
  "explanation": {
    "method": "hybrid",
    "content_weight": 0.5,
    "collaborative_weight": 0.5,
    "top_tags": ["dystopian", "classics", "science-fiction"],
    "similar_books": ["Fahrenheit 451", "The Handmaid's Tale"],
    "reasoning": "Based on your interest in dystopian literature and similar user preferences"
  },
  "metadata": {
    "request_id": "req_123456789",
    "processing_time_ms": 45,
    "cache_hit": false,
    "model_version": "1.0.0"
  }
}
```

**Status Codes:**
- `200 OK` - Recommendations generated successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Book title not found in database
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server processing error

**Error Response Format:**
```json
{
  "detail": "Error message",
  "error_code": "INVALID_PARAMETERS",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Request Examples

### User-Based Recommendations

```bash
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "n_recommendations": 10
  }'
```

### Content-Based Recommendations

```bash
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "book_title": "The Great Gatsby",
    "n_recommendations": 5
  }'
```

### Hybrid Recommendations

```bash
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 456,
    "book_title": "To Kill a Mockingbird",
    "n_recommendations": 8
  }'
```

## Response Field Descriptions

### Recommendation Object

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Book title |
| `authors` | string | Author name(s), comma-separated |
| `average_rating` | float | Average user rating (1.0-5.0) |
| `hybrid_score` | float | Recommendation confidence (0.0-1.0) |
| `book_id` | integer | Internal book identifier |
| `isbn` | string | ISBN-13 identifier |
| `publication_year` | integer | Year of publication |
| `tags` | array[string] | Associated genre/topic tags |

### Explanation Object

| Field | Type | Description |
|-------|------|-------------|
| `method` | string | Recommendation method used |
| `content_weight` | float | Weight of content-based filtering |
| `collaborative_weight` | float | Weight of collaborative filtering |
| `top_tags` | array[string] | Most relevant tags for recommendations |
| `similar_books` | array[string] | Books with similar characteristics |
| `reasoning` | string | Human-readable explanation |

### Metadata Object

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique request identifier |
| `processing_time_ms` | integer | Processing time in milliseconds |
| `cache_hit` | boolean | Whether result was cached |
| `model_version` | string | ML model version used |

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_PARAMETERS` | 400 | Missing or invalid request parameters |
| `BOOK_NOT_FOUND` | 404 | Specified book title not in database |
| `USER_NOT_FOUND` | 404 | User ID not found (if user validation enabled) |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `MODEL_ERROR` | 500 | Machine learning model error |
| `DATABASE_ERROR` | 500 | Database connection or query error |
| `CACHE_ERROR` | 500 | Redis cache connection error |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Performance Considerations

### Response Times

| Scenario | Target | Maximum |
|----------|--------|----------|
| Cached recommendations | < 50ms | < 100ms |
| User-based (new) | < 200ms | < 500ms |
| Content-based (new) | < 100ms | < 300ms |
| Hybrid (new) | < 300ms | < 800ms |

### Caching Strategy

- **User-based recommendations:** Cached for 1 hour
- **Content-based recommendations:** Cached for 24 hours
- **Cache key format:** `rec:{method}:{user_id}:{book_title}:{n_recs}`

### Optimization Tips

1. **Use appropriate recommendation counts:**
   - Mobile apps: 5-10 recommendations
   - Web interfaces: 10-20 recommendations
   - Batch processing: Up to 50 recommendations

2. **Leverage caching:**
   - Identical requests return cached results
   - Popular books have higher cache hit rates

3. **Request batching:**
   - For multiple users, make separate requests
   - API doesn't currently support batch requests

## SDK Examples

### Python

```python
import requests
import json

class GoodBooksClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_recommendations(self, user_id=None, book_title=None, n_recommendations=5):
        url = f"{self.base_url}/recommendations"
        payload = {"n_recommendations": n_recommendations}
        
        if user_id:
            payload["user_id"] = user_id
        if book_title:
            payload["book_title"] = book_title
            
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

# Usage
client = GoodBooksClient()
recommendations = client.get_recommendations(user_id=123, n_recommendations=10)
print(f"Found {len(recommendations['recommendations'])} recommendations")
```

### JavaScript

```javascript
class GoodBooksClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async getRecommendations(options = {}) {
        const { userId, bookTitle, nRecommendations = 5 } = options;
        
        const payload = { n_recommendations: nRecommendations };
        if (userId) payload.user_id = userId;
        if (bookTitle) payload.book_title = bookTitle;
        
        const response = await fetch(`${this.baseUrl}/recommendations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    }
}

// Usage
const client = new GoodBooksClient();
client.getRecommendations({ userId: 123, nRecommendations: 10 })
    .then(data => console.log(`Found ${data.recommendations.length} recommendations`))
    .catch(error => console.error('Error:', error));
```

### cURL Scripts

```bash
#!/bin/bash
# get_recommendations.sh

API_URL="http://localhost:8000"
USER_ID=${1:-123}
N_RECS=${2:-5}

curl -s -X POST "$API_URL/recommendations" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": $USER_ID,
    \"n_recommendations\": $N_RECS
  }" | jq '.recommendations[] | {title, authors, hybrid_score}'
```

## Testing

### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "GoodBooks Recommender API is running"

def test_user_recommendations():
    response = client.post("/recommendations", json={"user_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 5

def test_content_recommendations():
    response = client.post("/recommendations", json={"book_title": "1984"})
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "explanation" in data

def test_invalid_request():
    response = client.post("/recommendations", json={})
    assert response.status_code == 400
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 -T 'application/json' -p request.json http://localhost:8000/recommendations

# request.json content:
# {"user_id": 123, "n_recommendations": 5}
```

## Monitoring

### Health Monitoring

```bash
# Check API health
curl -f http://localhost:8000/health || echo "API is down"

# Monitor response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/recommendations
```

### Metrics Endpoint

```bash
# Prometheus metrics (if enabled)
curl http://localhost:8000/metrics
```

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Hybrid recommendation engine
- Basic caching support
- OpenAPI documentation

### Planned Features
- Authentication and authorization
- Batch recommendation endpoints
- Real-time model updates
- Advanced analytics endpoints
- GraphQL support

---

**Last Updated:** January 2024  
**API Version:** 1.0.0  
**Documentation Version:** 1.0.0
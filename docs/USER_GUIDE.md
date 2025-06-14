# User Guide

Complete guide for using the GoodBooks Recommender API to get personalized book recommendations.

## 📚 Table of Contents

- [Getting Started](#-getting-started)
- [Quick Start Examples](#-quick-start-examples)
- [API Endpoints](#-api-endpoints)
- [Request Formats](#-request-formats)
- [Response Formats](#-response-formats)
- [Use Cases & Examples](#-use-cases--examples)
- [Best Practices](#-best-practices)
- [Rate Limits & Guidelines](#-rate-limits--guidelines)
- [Error Handling](#-error-handling)
- [SDKs & Libraries](#-sdks--libraries)
- [FAQ](#-faq)

## 🚀 Getting Started

### What is GoodBooks Recommender?

GoodBooks Recommender is a hybrid recommendation system that provides personalized book suggestions based on:

- **Collaborative Filtering**: Recommendations based on similar users' preferences
- **Content-Based Filtering**: Recommendations based on book features and metadata
- **Hybrid Approach**: Combines both methods for better accuracy

### Prerequisites

- Basic understanding of REST APIs
- HTTP client (curl, Postman, or programming language HTTP library)
- API endpoint URL (e.g., `http://localhost:8000` for local development)

### Authentication

Currently, the API doesn't require authentication. In production environments, API keys or OAuth tokens may be required.

## ⚡ Quick Start Examples

### Get Recommendations for a User

```bash
# Get 5 recommendations for user ID 123
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "n_recommendations": 5
  }'
```

### Get Similar Books

```bash
# Get books similar to "The Great Gatsby"
curl -X POST "http://localhost:8000/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "book_title": "The Great Gatsby",
    "n_recommendations": 10
  }'
```

### Check API Health

```bash
# Check if the API is running
curl "http://localhost:8000/health"
```

## 🔗 API Endpoints

### Base URL

```
http://localhost:8000  # Local development
https://api.goodbooks.com  # Production (example)
```

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and welcome message |
| `/recommendations` | POST | Get book recommendations |
| `/health` | GET | API health status |
| `/metrics` | GET | API metrics (if enabled) |

## 📝 Request Formats

### Recommendations Request

**Endpoint:** `POST /recommendations`

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "user_id": 123,                    // Optional: User ID for personalized recommendations
  "book_title": "Book Title",        // Optional: Book title for similar book recommendations
  "n_recommendations": 5             // Optional: Number of recommendations (default: 5, max: 100)
}
```

**Field Descriptions:**

- `user_id` (integer, optional): Unique identifier for the user. Use this for personalized recommendations based on user's reading history.
- `book_title` (string, optional): Title of a book to find similar recommendations. Use this for content-based recommendations.
- `n_recommendations` (integer, optional): Number of recommendations to return. Default is 5, maximum is 100.

**Important Notes:**
- Either `user_id` OR `book_title` must be provided (not both)
- If both are provided, `user_id` takes precedence
- If neither is provided, the request will return an error

## 📊 Response Formats

### Successful Response

**Status Code:** `200 OK`

**Response Body:**

```json
{
  "recommendations": [
    {
      "book_id": 1,
      "title": "To Kill a Mockingbird",
      "authors": "Harper Lee",
      "average_rating": 4.25,
      "ratings_count": 4780653,
      "publication_year": 1960,
      "isbn": "9780061120084",
      "isbn13": "9780061120084",
      "language_code": "eng",
      "score": 0.95,
      "explanation": "Recommended because you enjoyed classic American literature"
    },
    {
      "book_id": 2,
      "title": "1984",
      "authors": "George Orwell",
      "average_rating": 4.19,
      "ratings_count": 3393812,
      "publication_year": 1949,
      "isbn": "9780451524935",
      "isbn13": "9780451524935",
      "language_code": "eng",
      "score": 0.92,
      "explanation": "Users with similar tastes also enjoyed this dystopian classic"
    }
  ],
  "total_recommendations": 2,
  "user_id": 123,
  "request_timestamp": "2023-12-01T10:30:00Z"
}
```

**Field Descriptions:**

- `recommendations`: Array of recommended books
  - `book_id`: Unique identifier for the book
  - `title`: Book title
  - `authors`: Book author(s)
  - `average_rating`: Average rating (1-5 scale)
  - `ratings_count`: Number of ratings received
  - `publication_year`: Year of publication
  - `isbn`/`isbn13`: International Standard Book Numbers
  - `language_code`: Language code (e.g., "eng" for English)
  - `score`: Recommendation confidence score (0-1)
  - `explanation`: Human-readable explanation for the recommendation
- `total_recommendations`: Number of recommendations returned
- `user_id`: User ID from the request (if provided)
- `request_timestamp`: When the request was processed

### Error Response

**Status Codes:** `400`, `422`, `500`

**Response Body:**

```json
{
  "detail": "Either user_id or book_title must be provided",
  "error_code": "MISSING_REQUIRED_FIELD",
  "timestamp": "2023-12-01T10:30:00Z"
}
```

### Health Check Response

**Endpoint:** `GET /health`

**Status Code:** `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "model": "healthy"
  }
}
```

## 💡 Use Cases & Examples

### 1. Personalized Recommendations for Existing Users

**Use Case:** Get recommendations for users who have rated books before.

**Example:**

```python
import requests

def get_user_recommendations(user_id, num_recs=10):
    url = "http://localhost:8000/recommendations"
    payload = {
        "user_id": user_id,
        "n_recommendations": num_recs
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()["recommendations"]
    else:
        print(f"Error: {response.json()['detail']}")
        return None

# Get recommendations for user 456
recommendations = get_user_recommendations(456, 5)
for book in recommendations:
    print(f"📖 {book['title']} by {book['authors']} (Score: {book['score']:.2f})")
    print(f"   {book['explanation']}\n")
```

**Output:**
```
📖 The Catcher in the Rye by J.D. Salinger (Score: 0.94)
   Recommended because you enjoyed coming-of-age stories

📖 Pride and Prejudice by Jane Austen (Score: 0.91)
   Users with similar tastes also loved this classic romance
```

### 2. Content-Based Recommendations (Similar Books)

**Use Case:** Find books similar to a specific title for discovery or "if you liked this" features.

**Example:**

```javascript
// JavaScript example using fetch
async function getSimilarBooks(bookTitle, numRecs = 8) {
    const url = 'http://localhost:8000/recommendations';
    const payload = {
        book_title: bookTitle,
        n_recommendations: numRecs
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.recommendations;
        } else {
            const error = await response.json();
            console.error('Error:', error.detail);
            return null;
        }
    } catch (error) {
        console.error('Network error:', error);
        return null;
    }
}

// Find books similar to Harry Potter
getSimilarBooks('Harry Potter and the Philosopher\'s Stone')
    .then(books => {
        if (books) {
            console.log('📚 Books similar to Harry Potter:');
            books.forEach(book => {
                console.log(`• ${book.title} by ${book.authors}`);
                console.log(`  Rating: ${book.average_rating}/5 (${book.ratings_count.toLocaleString()} ratings)`);
            });
        }
    });
```

### 3. Cold Start Problem (New Users)

**Use Case:** Provide recommendations for new users who haven't rated any books yet.

**Example:**

```python
def get_popular_books(category=None):
    """Get popular books as recommendations for new users"""
    # For new users, use a popular book to get similar recommendations
    popular_books = [
        "The Great Gatsby",
        "To Kill a Mockingbird", 
        "1984",
        "Pride and Prejudice",
        "The Catcher in the Rye"
    ]
    
    all_recommendations = []
    
    for book in popular_books[:2]:  # Use top 2 popular books
        recs = get_similar_books(book, 3)
        if recs:
            all_recommendations.extend(recs)
    
    # Remove duplicates and return top recommendations
    seen_books = set()
    unique_recs = []
    
    for book in all_recommendations:
        if book['book_id'] not in seen_books:
            seen_books.add(book['book_id'])
            unique_recs.append(book)
    
    return unique_recs[:10]

def get_similar_books(book_title, num_recs):
    url = "http://localhost:8000/recommendations"
    payload = {
        "book_title": book_title,
        "n_recommendations": num_recs
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()["recommendations"]
    return None

# Get recommendations for new users
new_user_recs = get_popular_books()
print("📚 Recommended books for new users:")
for book in new_user_recs:
    print(f"• {book['title']} by {book['authors']}")
```

### 4. Batch Recommendations

**Use Case:** Get recommendations for multiple users efficiently.

**Example:**

```python
import asyncio
import aiohttp

async def get_recommendations_async(session, user_id):
    url = "http://localhost:8000/recommendations"
    payload = {"user_id": user_id, "n_recommendations": 5}
    
    async with session.post(url, json=payload) as response:
        if response.status == 200:
            data = await response.json()
            return user_id, data["recommendations"]
        else:
            return user_id, None

async def batch_recommendations(user_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [get_recommendations_async(session, uid) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        return dict(results)

# Get recommendations for multiple users
user_ids = [101, 102, 103, 104, 105]
batch_results = asyncio.run(batch_recommendations(user_ids))

for user_id, recommendations in batch_results.items():
    if recommendations:
        print(f"\n👤 User {user_id} recommendations:")
        for book in recommendations[:3]:  # Show top 3
            print(f"  📖 {book['title']}")
    else:
        print(f"\n❌ No recommendations for User {user_id}")
```

### 5. Building a Recommendation Widget

**Use Case:** Create a web widget that shows book recommendations.

**HTML/JavaScript Example:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Book Recommendations</title>
    <style>
        .recommendation-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            background: #f9f9f9;
        }
        .book-title { font-weight: bold; color: #333; }
        .book-author { color: #666; }
        .book-rating { color: #ff6b35; }
        .explanation { font-style: italic; color: #555; margin-top: 8px; }
    </style>
</head>
<body>
    <div id="recommendations-container">
        <h2>📚 Recommended for You</h2>
        <div id="loading">Loading recommendations...</div>
        <div id="recommendations"></div>
    </div>

    <script>
        async function loadRecommendations(userId) {
            const loadingDiv = document.getElementById('loading');
            const recommendationsDiv = document.getElementById('recommendations');
            
            try {
                const response = await fetch('http://localhost:8000/recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        n_recommendations: 6
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    displayRecommendations(data.recommendations);
                } else {
                    throw new Error('Failed to load recommendations');
                }
            } catch (error) {
                recommendationsDiv.innerHTML = '<p>❌ Error loading recommendations</p>';
                console.error('Error:', error);
            } finally {
                loadingDiv.style.display = 'none';
            }
        }
        
        function displayRecommendations(recommendations) {
            const container = document.getElementById('recommendations');
            
            const html = recommendations.map(book => `
                <div class="recommendation-card">
                    <div class="book-title">${book.title}</div>
                    <div class="book-author">by ${book.authors}</div>
                    <div class="book-rating">
                        ⭐ ${book.average_rating}/5 
                        (${book.ratings_count.toLocaleString()} ratings)
                    </div>
                    <div class="explanation">${book.explanation}</div>
                </div>
            `).join('');
            
            container.innerHTML = html;
        }
        
        // Load recommendations for user ID 123
        loadRecommendations(123);
    </script>
</body>
</html>
```

## ✅ Best Practices

### 1. Request Optimization

- **Cache Results**: Cache recommendations for frequently requested users
- **Batch Requests**: Use async/await for multiple concurrent requests
- **Appropriate Limits**: Don't request more recommendations than you'll display
- **Error Handling**: Always handle API errors gracefully

```python
# Good: Reasonable number of recommendations
recommendations = get_recommendations(user_id=123, n_recommendations=10)

# Avoid: Requesting too many recommendations
# recommendations = get_recommendations(user_id=123, n_recommendations=1000)
```

### 2. User Experience

- **Loading States**: Show loading indicators while fetching recommendations
- **Fallback Content**: Provide fallback recommendations for new users
- **Explanation**: Display recommendation explanations to build trust
- **Diversity**: Mix different types of recommendations

### 3. Performance

- **Client-Side Caching**: Cache recommendations in browser/app storage
- **Pagination**: Load recommendations in batches for large lists
- **Preloading**: Preload recommendations for likely user actions

```javascript
// Example: Client-side caching
class RecommendationCache {
    constructor(ttl = 300000) { // 5 minutes TTL
        this.cache = new Map();
        this.ttl = ttl;
    }
    
    get(key) {
        const item = this.cache.get(key);
        if (item && Date.now() - item.timestamp < this.ttl) {
            return item.data;
        }
        this.cache.delete(key);
        return null;
    }
    
    set(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
}

const recCache = new RecommendationCache();

async function getCachedRecommendations(userId) {
    const cacheKey = `user_${userId}`;
    let recommendations = recCache.get(cacheKey);
    
    if (!recommendations) {
        recommendations = await fetchRecommendations(userId);
        recCache.set(cacheKey, recommendations);
    }
    
    return recommendations;
}
```

### 4. Error Handling

```python
def robust_get_recommendations(user_id, retries=3, timeout=10):
    """Get recommendations with retry logic and timeout"""
    import time
    
    for attempt in range(retries):
        try:
            response = requests.post(
                "http://localhost:8000/recommendations",
                json={"user_id": user_id, "n_recommendations": 5},
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()["recommendations"]
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"Request timeout (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(1)
                continue
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    print("All retry attempts failed")
    return None
```

## ⚡ Rate Limits & Guidelines

### Current Limits

- **Requests per minute**: 60 requests per IP address
- **Requests per hour**: 1000 requests per IP address
- **Concurrent connections**: 10 per IP address
- **Request timeout**: 30 seconds
- **Max recommendations per request**: 100

### Rate Limit Headers

The API returns rate limit information in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1638360000
```

### Handling Rate Limits

```python
def check_rate_limit(response):
    """Check rate limit headers and handle accordingly"""
    if response.status_code == 429:
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        current_time = int(time.time())
        wait_time = max(0, reset_time - current_time)
        
        print(f"Rate limit exceeded. Waiting {wait_time} seconds...")
        time.sleep(wait_time + 1)  # Add 1 second buffer
        return True
    
    remaining = response.headers.get('X-RateLimit-Remaining')
    if remaining and int(remaining) < 5:
        print(f"Warning: Only {remaining} requests remaining")
    
    return False
```

## 🚨 Error Handling

### Common Error Codes

| Status Code | Error Type | Description | Solution |
|-------------|------------|-------------|----------|
| 400 | Bad Request | Invalid request format | Check request body format |
| 422 | Validation Error | Invalid field values | Validate input parameters |
| 429 | Rate Limited | Too many requests | Implement rate limiting |
| 500 | Server Error | Internal server error | Retry request, contact support |
| 503 | Service Unavailable | Service temporarily down | Retry with exponential backoff |

### Error Response Examples

**400 Bad Request:**
```json
{
  "detail": "Either user_id or book_title must be provided",
  "error_code": "MISSING_REQUIRED_FIELD"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "n_recommendations"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 100}
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "request_id": "req_123456789"
}
```

### Error Handling Best Practices

```python
class RecommendationAPIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, status_code, message, error_code=None):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

def handle_api_response(response):
    """Handle API response and raise appropriate exceptions"""
    if response.status_code == 200:
        return response.json()
    
    try:
        error_data = response.json()
        error_message = error_data.get('detail', 'Unknown error')
        error_code = error_data.get('error_code')
    except ValueError:
        error_message = response.text
        error_code = None
    
    if response.status_code == 400:
        raise RecommendationAPIError(400, f"Bad request: {error_message}", error_code)
    elif response.status_code == 422:
        raise RecommendationAPIError(422, f"Validation error: {error_message}", error_code)
    elif response.status_code == 429:
        raise RecommendationAPIError(429, "Rate limit exceeded", error_code)
    elif response.status_code >= 500:
        raise RecommendationAPIError(response.status_code, f"Server error: {error_message}", error_code)
    else:
        raise RecommendationAPIError(response.status_code, f"HTTP {response.status_code}: {error_message}", error_code)

# Usage example
try:
    response = requests.post(url, json=payload)
    data = handle_api_response(response)
    recommendations = data['recommendations']
except RecommendationAPIError as e:
    if e.status_code == 429:
        # Handle rate limiting
        time.sleep(60)
        # Retry request
    elif e.status_code >= 500:
        # Handle server errors
        print(f"Server error: {e.message}")
        # Maybe try again later
    else:
        # Handle client errors
        print(f"Client error: {e.message}")
        # Fix the request
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
    # Handle network issues
```

## 📦 SDKs & Libraries

### Python SDK Example

```python
class GoodBooksClient:
    """Python client for GoodBooks Recommender API"""
    
    def __init__(self, base_url="http://localhost:8000", timeout=30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def get_user_recommendations(self, user_id, n_recommendations=5):
        """Get recommendations for a specific user"""
        return self._make_request({
            "user_id": user_id,
            "n_recommendations": n_recommendations
        })
    
    def get_similar_books(self, book_title, n_recommendations=5):
        """Get books similar to the given title"""
        return self._make_request({
            "book_title": book_title,
            "n_recommendations": n_recommendations
        })
    
    def health_check(self):
        """Check API health status"""
        response = self.session.get(
            f"{self.base_url}/health",
            timeout=self.timeout
        )
        return response.json()
    
    def _make_request(self, payload):
        """Make a recommendation request"""
        response = self.session.post(
            f"{self.base_url}/recommendations",
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            return response.json()["recommendations"]
        else:
            response.raise_for_status()

# Usage
client = GoodBooksClient("http://localhost:8000")

# Get user recommendations
user_recs = client.get_user_recommendations(user_id=123, n_recommendations=10)

# Get similar books
similar_books = client.get_similar_books("The Great Gatsby", n_recommendations=5)

# Check health
health = client.health_check()
print(f"API Status: {health['status']}")
```

### JavaScript/Node.js SDK Example

```javascript
class GoodBooksClient {
    constructor(baseUrl = 'http://localhost:8000', timeout = 30000) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.timeout = timeout;
    }
    
    async getUserRecommendations(userId, nRecommendations = 5) {
        return this._makeRequest({
            user_id: userId,
            n_recommendations: nRecommendations
        });
    }
    
    async getSimilarBooks(bookTitle, nRecommendations = 5) {
        return this._makeRequest({
            book_title: bookTitle,
            n_recommendations: nRecommendations
        });
    }
    
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`, {
            method: 'GET',
            timeout: this.timeout
        });
        
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }
        
        return response.json();
    }
    
    async _makeRequest(payload) {
        const response = await fetch(`${this.baseUrl}/recommendations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload),
            timeout: this.timeout
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(`API Error ${response.status}: ${error.detail}`);
        }
        
        const data = await response.json();
        return data.recommendations;
    }
}

// Usage
const client = new GoodBooksClient('http://localhost:8000');

// Get user recommendations
try {
    const userRecs = await client.getUserRecommendations(123, 10);
    console.log('User recommendations:', userRecs);
} catch (error) {
    console.error('Error:', error.message);
}

// Get similar books
try {
    const similarBooks = await client.getSimilarBooks('The Great Gatsby', 5);
    console.log('Similar books:', similarBooks);
} catch (error) {
    console.error('Error:', error.message);
}
```

## ❓ FAQ

### General Questions

**Q: How accurate are the recommendations?**
A: The hybrid approach typically achieves 75-85% accuracy depending on the user's rating history. Users with more ratings get more accurate recommendations.

**Q: How often are recommendations updated?**
A: Recommendations are generated in real-time based on the current model. The underlying model is retrained periodically (typically weekly) with new data.

**Q: Can I get recommendations for books in different languages?**
A: Yes, the system supports multiple languages. Use the `language_code` field in responses to filter by language.

**Q: What happens if a user has no rating history?**
A: For new users (cold start), the system falls back to content-based recommendations using popular books or books similar to a provided title.

### Technical Questions

**Q: Is there a rate limit?**
A: Yes, currently 60 requests per minute per IP address. Check the `X-RateLimit-*` headers in responses.

**Q: Can I request more than 100 recommendations?**
A: No, the maximum is 100 recommendations per request to ensure good performance.

**Q: How do I handle API timeouts?**
A: Implement retry logic with exponential backoff. Most requests complete within 2-3 seconds.

**Q: Is there a webhook for real-time updates?**
A: Not currently. You need to poll the API for updated recommendations.

### Data Questions

**Q: How many books are in the database?**
A: The system contains information about 10,000+ books with millions of ratings.

**Q: Can I add new books or ratings?**
A: The current API is read-only. Contact the development team for data updates.

**Q: What book metadata is available?**
A: Title, authors, publication year, ISBN, average rating, rating count, language, and genre information.

### Troubleshooting

**Q: Why am I getting "No recommendations found"?**
A: This can happen for:
- Very new users with no rating history
- Invalid user IDs
- Books with insufficient data
- Try using content-based recommendations instead

**Q: Why are recommendations slow?**
A: Possible causes:
- High server load
- Large number of recommendations requested
- Cold cache
- Try reducing `n_recommendations` or implement client-side caching

**Q: How do I report issues or request features?**
A: Contact the development team or create an issue in the project repository.

---

## 📞 Support

For additional help:

- **Documentation**: Check other guides in the `/docs` folder
- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md) for detailed technical documentation
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- **Development**: See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for contributing

**Happy Reading! 📚✨**
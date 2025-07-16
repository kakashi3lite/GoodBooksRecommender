# GoodBooks Recommender System

A sophisticated, production-grade book recommendation engine that combines content-based and collaborative filtering approaches with enterprise-level security and monitoring.

## 🌟 Features

- **Hybrid Recommendation Model**
  - Content-based filtering using TF-IDF on book metadata
  - Collaborative filtering with matrix factorization
  - Weighted combination for optimal recommendations

- **🔒 Enterprise Security**
  - OAuth2 with JWT authentication
  - Role-based access control (RBAC)
  - Data privacy and anonymization
  - Input validation and XSS protection
  - Rate limiting and DDoS protection
  - Content Security Policy (CSP)
  - Comprehensive security headers

- **📊 Production Monitoring**
  - Prometheus metrics and Grafana dashboards
  - Distributed tracing with Jaeger
  - Structured logging with ELK stack
  - Health checks and alerting
  - Performance monitoring

- **Fast and Scalable**
  - FastAPI-based REST API with async/await
  - Redis caching for improved performance
  - Docker containerization and Kubernetes ready
  - Horizontal scaling support

- **Rich Metadata Analysis**
  - Book tags and categories processing
  - User rating patterns analysis
  - Recommendation explanations with RAG
  - A/B testing framework

## 🏗 Architecture

```
src/
├── api/                # FastAPI application with security middleware
├── auth/              # OAuth2/JWT authentication and RBAC
├── middleware/        # Security middleware stack
├── privacy/           # Data privacy and anonymization
├── data/              # Data loading and preprocessing
├── features/          # Feature extraction
├── models/            # Recommendation models
├── core/              # Core utilities (logging, monitoring, tracing)
└── config.py          # Configuration management

security/
├── authentication    # JWT tokens, user management
├── authorization     # Role-based access control
├── data_privacy     # Anonymization, encryption, retention
├── input_validation # XSS, injection protection
├── rate_limiting    # DDoS protection
└── monitoring       # Security event logging
```

## 🔒 Security Features

- **Authentication**: OAuth2 with JWT tokens, secure session management
- **Authorization**: Role-based access control (USER, MODERATOR, ADMIN)
- **Data Privacy**: Automatic PII anonymization, encryption at rest and in transit
- **Input Validation**: XSS and SQL injection protection
- **Rate Limiting**: Configurable rate limits per endpoint and user
- **Security Headers**: Comprehensive security headers (CSP, HSTS, etc.)
- **Monitoring**: Security event logging and alerting
- **Compliance**: GDPR-ready data retention and deletion policies

For detailed security documentation, see [SECURITY_GUIDE.md](docs/SECURITY_GUIDE.md).

## 🚀 Getting Started

### Prerequisites

- Python 3.9-3.11
- Docker and Docker Compose (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/GoodBooksRecommender.git
cd GoodBooksRecommender
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running Locally

1. Start the API server:
```bash
python -m src.api.main
```

2. Or using Docker Compose:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Authentication

The API uses OAuth2 with JWT tokens for authentication:

#### 1. Register a new user:
```bash
POST /auth/register
{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePassword123!"
}
```

#### 2. Login to get JWT tokens:
```bash
POST /auth/login
{
    "username": "johndoe", 
    "password": "SecurePassword123!"
}

Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
        "id": 1,
        "username": "johndoe",
        "role": "USER"
    }
}
```

#### 3. Use token in subsequent requests:
```bash
curl -H "Authorization: Bearer your_jwt_token_here" \
     -X POST http://localhost:8000/recommendations \
     -d '{"user_id": 1, "n_recommendations": 5}'
```

### Get Recommendations

```bash
POST /recommendations
Authorization: Bearer your_jwt_token_here

Request Body:
{
    "user_id": 123,          # Optional (defaults to authenticated user)
    "book_title": "1984",    # Optional
    "n_recommendations": 5   # Optional, default: 5
}

Response:
{
    "recommendations": [
        {
            "title": "Brave New World",
            "authors": "Aldous Huxley",
            "average_rating": 4.5,
            "hybrid_score": 0.95
        },
        ...
    ],
    "explanation": {
        "top_tags": ["dystopian", "classics", ...],
        "similar_books": ["Animal Farm", ...]
    }
}
```

## 🧪 Testing

Run the test suite:
```bash
pytest
```

## 📈 Performance

- Response time: < 100ms for recommendations
- Cache hit ratio: > 80%
- Supports millions of books and users

## 🛠 Development

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "Add your feature"
```

3. Push changes:
```bash
git push origin feature/your-feature-name
```

## �️ Security Testing

Run comprehensive security tests to verify the application's security posture:

```bash
# Install security testing dependencies
pip install -r requirements.txt

# Run security scan
python scripts/security_scan.py --target http://localhost:8000

# Save results to file
python scripts/security_scan.py --target http://localhost:8000 --output security_report.json

# Run OWASP ZAP scan (requires Docker)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -J zap-report.json
```

### Security Features Tested

- ✅ JWT Authentication & Authorization
- ✅ Role-based Access Control (RBAC)
- ✅ Input Validation & Sanitization
- ✅ SQL Injection Protection
- ✅ XSS Protection
- ✅ Rate Limiting
- ✅ Security Headers (CSP, HSTS, etc.)
- ✅ HTTPS Configuration
- ✅ Data Privacy & Anonymization

## 📋 Production Checklist

Before deploying to production, ensure:

- [ ] All security tests pass
- [ ] Environment variables configured
- [ ] TLS certificates installed
- [ ] Monitoring and alerting configured
- [ ] Database connections secured
- [ ] Backup procedures in place
- [ ] Load testing completed
- [ ] Security audit performed

## 📖 Documentation

- [Security Guide](docs/SECURITY_GUIDE.md) - Comprehensive security documentation
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Production deployment instructions
- [Architecture Guide](docs/ARCHITECTURE.md) - System architecture overview
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Development setup and guidelines

## �📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
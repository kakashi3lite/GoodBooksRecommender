# 🔒 GoodBooks Recommender - Security Guide

## Overview

This guide documents the comprehensive security enhancements implemented in the GoodBooks Recommender system, covering authentication, authorization, data privacy, and protection against web vulnerabilities.

## 🔐 Authentication & Authorization

### OAuth2 with JWT Tokens

The system has been upgraded from API key authentication to a robust OAuth2 implementation with JWT tokens:

#### Features
- **Access Tokens**: Short-lived JWT tokens (15 minutes default) for API access
- **Refresh Tokens**: Long-lived tokens (7 days default) for seamless session extension
- **Token Blacklisting**: Secure logout with token invalidation
- **Automatic Token Refresh**: Client-side automatic token renewal

#### Usage

**Register a new user:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com", 
    "password": "SecurePassword123!"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePassword123!"
  }'
```

**Access protected endpoints:**
```bash
curl -X POST http://localhost:8000/recommendations \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "n_recommendations": 5
  }'
```

### Role-Based Access Control (RBAC)

The system implements a three-tier role system:

#### Roles
- **USER**: Basic user with access to recommendations
- **MODERATOR**: Extended access to analytics and experiment results
- **ADMIN**: Full system access including model management

#### Protected Endpoints

| Endpoint | Required Role | Description |
|----------|---------------|-------------|
| `/recommendations` | USER+ | Get recommendations (users can only access their own) |
| `/admin/experiments/*/results` | MODERATOR+ | View A/B test results |
| `/admin/experiments` | ADMIN | Create/manage A/B tests |
| `/admin/models/*` | ADMIN/MODERATOR | Model management |
| `/admin/vector-store/*` | ADMIN/MODERATOR | Vector store management |

#### RBAC Decorators

```python
from src.auth.security import require_roles, UserRole

@app.post("/admin/experiments")
@require_roles([UserRole.ADMIN])
async def create_experiment(
    experiment_request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    # Only admins can access this endpoint
    pass
```

## 🛡️ Security Middleware Stack

The application implements a comprehensive security middleware stack applied in order:

### 1. Security Headers Middleware
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### 2. Content Security Policy (CSP)
- Prevents XSS attacks
- Restricts resource loading to trusted sources
- Applied to both API responses and dashboard

### 3. Rate Limiting Middleware
- Configurable rate limits per endpoint
- IP-based rate limiting
- Graceful degradation under high load

### 4. Input Validation Middleware
- SQL injection prevention
- XSS payload detection
- Request size limits
- Malicious pattern filtering

### 5. Security Middleware
- Request sanitization
- Security header enforcement
- Attack pattern detection

## 🔒 Data Privacy & Protection

### Data Anonymization

User data is automatically anonymized in logs and analytics:

```python
# User IDs are hashed for privacy compliance
anonymized_user_id = data_privacy_service.anonymize_user_id(user_id)

logger.info(
    "Recommendation request received",
    anonymized_user_id=anonymized_user_id,  # Hashed ID
    book_title=request.book_title,
    n_recommendations=request.n_recommendations
)
```

### Data Encryption

#### In Transit
- **TLS 1.3**: All API communications encrypted
- **HTTPS Redirect**: Automatic HTTP to HTTPS redirection
- **Secure Headers**: HSTS implementation

#### At Rest
- **Sensitive Data**: Encrypted using AES-256-GCM
- **Database**: Encrypted connections to PostgreSQL
- **Cache**: Redis connections with TLS

### Data Retention Policies

Automated data cleanup based on retention policies:

#### Default Retention Periods
- **Session Data**: 90 days
- **Log Files**: 1 year
- **Cache Data**: 24 hours (recommendations)
- **Analytics Data**: 2 years (anonymized)

#### Cleanup Process
```python
# Runs daily as background task
async def privacy_cleanup_task():
    while True:
        try:
            await data_privacy_service.cleanup_expired_data()
            logger.info("Data privacy cleanup completed")
        except Exception as e:
            logger.error("Data privacy cleanup failed", error=str(e))
        
        await asyncio.sleep(24 * 60 * 60)  # 24 hours
```

## 🌐 Web Security

### Content Security Policy (CSP)

The dashboard implements a strict CSP:

```html
<meta http-equiv="Content-Security-Policy" content="
    default-src 'self';
    script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
    style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
    font-src 'self' https://fonts.gstatic.com;
    img-src 'self' data: https:;
    connect-src 'self' ws: wss:;
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    object-src 'none';
    upgrade-insecure-requests;
">
```

### Input Validation

All user inputs are validated using Pydantic models:

```python
class RecommendationRequest(BaseModel):
    user_id: Optional[int] = Field(None, gt=0)
    book_title: Optional[str] = Field(None, min_length=1, max_length=500)
    n_recommendations: int = Field(5, ge=1, le=50)
    
    @validator('book_title')
    def sanitize_title(cls, v):
        if v:
            # Remove potential XSS payloads
            return html.escape(v.strip())
        return v
```

### Cross-Origin Resource Sharing (CORS)

Configured with secure defaults:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

## 🔍 Vulnerability Scanning

### OWASP ZAP Integration

Automated security scanning can be performed using OWASP ZAP:

```bash
# Install OWASP ZAP
docker pull owasp/zap2docker-stable

# Run baseline scan
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -J zap-report.json

# Run full scan
docker run -t owasp/zap2docker-stable zap-full-scan.py \
  -t http://localhost:8000 \
  -J zap-full-report.json
```

### Security Testing Script

A security testing script is provided:

```bash
python scripts/security_scan.py --target http://localhost:8000
```

## 📊 Security Monitoring

### Authentication Events

All authentication events are logged with structured logging:

```json
{
  "timestamp": "2025-07-16T10:30:00Z",
  "level": "INFO",
  "event": "user_login_success",
  "user_id": "hashed_user_id",
  "ip_address": "anonymized_ip",
  "user_agent": "Mozilla/5.0..."
}
```

### Security Metrics

Prometheus metrics track security events:

- `goodbooks_auth_attempts_total{result="success|failure"}`
- `goodbooks_rate_limit_violations_total`
- `goodbooks_security_violations_total{type="xss|injection|csrf"}`
- `goodbooks_token_refresh_total{result="success|failure"}`

### Alerting

Security alerts are configured in Prometheus/Alertmanager:

```yaml
groups:
- name: security
  rules:
  - alert: HighFailedLogins
    expr: rate(goodbooks_auth_attempts_total{result="failure"}[5m]) > 10
    for: 2m
    annotations:
      summary: "High number of failed login attempts"
      
  - alert: SecurityViolation
    expr: increase(goodbooks_security_violations_total[1m]) > 0
    for: 0m
    annotations:
      summary: "Security violation detected"
```

## 🔧 Configuration

### Environment Variables

Security-related environment variables:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-256-bit-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# RBAC Configuration
RBAC_ENABLED=true
RBAC_DEFAULT_ROLE=USER

# CSP Configuration
CSP_ENABLED=true
CSP_REPORT_URI=/api/v1/security/csp-report

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Data Privacy
DATA_RETENTION_DAYS=90
ANONYMIZATION_ENABLED=true
ENCRYPTION_KEY=your-encryption-key-here
```

### Security Settings

Configure security settings in `src/core/settings.py`:

```python
class SecuritySettings(BaseSettings):
    # JWT Settings
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    
    # RBAC Settings
    rbac_enabled: bool = Field(True, env="RBAC_ENABLED")
    default_role: UserRole = Field(UserRole.USER, env="RBAC_DEFAULT_ROLE")
    
    # CORS Settings
    cors_origins: List[str] = Field(["http://localhost:3000"], env="CORS_ORIGINS")
    allowed_hosts: List[str] = Field(["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    # CSP Settings
    csp_enabled: bool = Field(True, env="CSP_ENABLED")
    csp_report_uri: str = Field("/api/v1/security/csp-report", env="CSP_REPORT_URI")
```

## 🚨 Incident Response

### Security Incident Workflow

1. **Detection**: Monitoring alerts identify potential security issues
2. **Assessment**: Determine severity and impact
3. **Containment**: Isolate affected systems
4. **Recovery**: Restore secure operations
5. **Post-Incident**: Review and improve security measures

### Emergency Procedures

#### Compromised JWT Secret
```bash
# 1. Rotate JWT secret immediately
export JWT_SECRET_KEY="new-secret-key"

# 2. Restart application to invalidate all tokens
kubectl rollout restart deployment/goodbooks-api

# 3. Force all users to re-authenticate
curl -X POST http://localhost:8000/admin/auth/revoke-all-tokens \
  -H "Authorization: Bearer admin_token"
```

#### Suspicious Activity
```bash
# 1. Check recent authentication events
curl -X GET http://localhost:8000/admin/security/auth-logs \
  -H "Authorization: Bearer admin_token"

# 2. Block suspicious IPs
curl -X POST http://localhost:8000/admin/security/block-ip \
  -H "Authorization: Bearer admin_token" \
  -d '{"ip_address": "malicious.ip.address"}'
```

## 📋 Security Checklist

### Deployment Security

- [ ] TLS certificates properly configured
- [ ] Security headers enabled
- [ ] CSP properly configured
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] JWT secrets rotated
- [ ] Database connections encrypted
- [ ] Redis connections secured
- [ ] Log files properly secured
- [ ] Monitoring alerts configured

### Development Security

- [ ] Dependencies scanned for vulnerabilities
- [ ] Code reviewed for security issues
- [ ] Unit tests include security scenarios
- [ ] Integration tests verify authentication
- [ ] OWASP ZAP scans passing
- [ ] Security documentation updated
- [ ] Incident response plan tested

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-jwt-bcp)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)

---

**Note**: This security implementation follows industry best practices and provides comprehensive protection against common web vulnerabilities. Regular security audits and updates are recommended to maintain the security posture.

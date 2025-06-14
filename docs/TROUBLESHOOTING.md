# Troubleshooting Guide

Comprehensive troubleshooting guide for the GoodBooks Recommender system.

## 📋 Table of Contents

- [Quick Diagnostics](#-quick-diagnostics)
- [Server Issues](#-server-issues)
- [Performance Problems](#-performance-problems)
- [Database Issues](#-database-issues)
- [Cache Problems](#-cache-problems)
- [Model Issues](#-model-issues)
- [API Errors](#-api-errors)
- [Docker Issues](#-docker-issues)
- [Kubernetes Issues](#-kubernetes-issues)
- [Monitoring & Debugging](#-monitoring--debugging)
- [Common Error Messages](#-common-error-messages)
- [Performance Optimization](#-performance-optimization)

## 🔍 Quick Diagnostics

### Health Check Commands

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed system status
curl http://localhost:8000/metrics

# Check all services
docker-compose ps
kubectl get pods -n goodbooks
```

### System Resource Check

```bash
# Memory usage
free -h
docker stats --no-stream

# CPU usage
top -n 1 | head -20

# Disk usage
df -h
du -sh /var/lib/docker

# Network connectivity
ping redis
ping database
telnet localhost 8000
```

### Log Quick Check

```bash
# Application logs (last 50 lines)
docker logs --tail 50 goodbooks-api
kubectl logs --tail=50 deployment/goodbooks-api -n goodbooks

# Error logs only
docker logs goodbooks-api 2>&1 | grep -i error
journalctl -u goodbooks-api | grep -i error

# System logs
dmesg | tail -20
```

## 🚨 Server Issues

### Server Won't Start

**Symptoms:**
- Application fails to start
- Port binding errors
- Import errors

**Common Causes & Solutions:**

#### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000
netstat -tulpn | grep 8000

# Kill process using the port
sudo kill -9 <PID>

# Or use different port
export API_PORT=8001
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001
```

#### Missing Dependencies
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Check for missing system libraries
ldd $(which python) | grep "not found"

# Install missing system dependencies (Ubuntu)
sudo apt update
sudo apt install build-essential libpq-dev python3-dev
```

#### Import Errors
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Test imports manually
python -c "from src.api.main import app; print('Import successful')"

# Check for circular imports
python -c "import src.models.hybrid_recommender"

# Fix PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Configuration Issues
```bash
# Check environment variables
env | grep -E "(DATABASE|REDIS|API)"

# Validate configuration
python -c "from src.config import Config; print(Config.DATABASE_URL)"

# Check file permissions
ls -la src/
ls -la data/
```

### Server Crashes

**Symptoms:**
- Server stops unexpectedly
- OOM (Out of Memory) kills
- Segmentation faults

**Diagnosis:**
```bash
# Check system logs for crashes
dmesg | grep -i "killed process"
journalctl -u goodbooks-api | grep -i "killed\|crash\|segfault"

# Check memory usage before crash
sar -r 1 10  # Monitor memory for 10 seconds

# Check for core dumps
find /var/crash -name "core.*" -mtime -1
ulimit -c unlimited  # Enable core dumps
```

**Solutions:**
```bash
# Increase memory limits (Docker)
docker run -m 4g goodbooks-recommender

# Increase memory limits (Kubernetes)
kubectl patch deployment goodbooks-api -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "api",
          "resources": {
            "limits": {"memory": "8Gi"},
            "requests": {"memory": "4Gi"}
          }
        }]
      }
    }
  }
}'

# Optimize memory usage in code
# Add to src/config.py
MODEL_PARAMS = {
    'collaborative': {
        'n_factors': 25,  # Reduce from default
        'batch_size': 500
    }
}
```

## ⚡ Performance Problems

### Slow Response Times

**Symptoms:**
- API responses > 5 seconds
- Timeouts
- High CPU usage

**Diagnosis:**
```bash
# Measure response times
time curl -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "n_recommendations": 5}'

# Load testing
ab -n 100 -c 10 -T 'application/json' -p request.json http://localhost:8000/recommendations

# Profile application
python -m cProfile -o profile.stats src/api/main.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"
```

**Solutions:**

#### Enable Caching
```python
# Add to src/models/hybrid_recommender.py
from functools import lru_cache

class HybridRecommender:
    @lru_cache(maxsize=1000)
    def get_recommendations_cached(self, user_id, n_recommendations):
        return self.get_recommendations(user_id, n_recommendations)
```

#### Optimize Database Queries
```sql
-- Add indexes
CREATE INDEX CONCURRENTLY idx_ratings_user_id ON ratings(user_id);
CREATE INDEX CONCURRENTLY idx_ratings_book_id ON ratings(book_id);
CREATE INDEX CONCURRENTLY idx_books_title_gin ON books USING gin(to_tsvector('english', title));

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM ratings WHERE user_id = 123;
```

#### Use Connection Pooling
```python
# Update src/data/data_loader.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30
)
```

### High Memory Usage

**Symptoms:**
- Memory usage > 4GB
- Swap usage increasing
- OOM kills

**Diagnosis:**
```bash
# Monitor memory usage
watch -n 1 'free -h && echo "---" && ps aux --sort=-%mem | head -10'

# Check for memory leaks
valgrind --tool=memcheck --leak-check=full python src/api/main.py

# Python memory profiling
pip install memory-profiler
python -m memory_profiler src/api/main.py
```

**Solutions:**
```python
# Implement data streaming
def load_data_in_chunks(file_path, chunk_size=10000):
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        yield chunk
        
# Clear unused variables
import gc
def cleanup_memory():
    gc.collect()
    
# Reduce model complexity
MODEL_PARAMS = {
    'collaborative': {
        'n_factors': 25,  # Reduce from 50
        'regularization': 0.1
    }
}
```

## 🗄️ Database Issues

### Connection Failures

**Symptoms:**
- "Connection refused" errors
- "Too many connections" errors
- Timeout errors

**Diagnosis:**
```bash
# Test database connectivity
psql -h localhost -U goodbooks -d goodbooks -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql
docker logs postgres-container

# Check connection limits
psql -h localhost -U postgres -c "SHOW max_connections;"
psql -h localhost -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

**Solutions:**
```bash
# Increase connection limits
# Edit postgresql.conf
max_connections = 200
shared_buffers = 256MB

# Restart PostgreSQL
sudo systemctl restart postgresql
docker restart postgres-container

# Use connection pooling
pip install psycopg2-pool
```

```python
# Implement connection pooling
from psycopg2 import pool

connection_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=20,
    host="localhost",
    database="goodbooks",
    user="goodbooks",
    password="password"
)
```

### Slow Queries

**Symptoms:**
- Database queries > 1 second
- High database CPU usage
- Query timeouts

**Diagnosis:**
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Check table statistics
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables;
```

**Solutions:**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_ratings_user_book ON ratings(user_id, book_id);
CREATE INDEX CONCURRENTLY idx_books_authors ON books(authors);

-- Update table statistics
ANALYZE ratings;
ANALYZE books;

-- Optimize queries
-- Before:
SELECT * FROM ratings WHERE user_id = 123;

-- After:
SELECT book_id, rating FROM ratings WHERE user_id = 123;
```

### Data Corruption

**Symptoms:**
- Inconsistent query results
- Foreign key violations
- Checksum errors

**Diagnosis:**
```sql
-- Check database integrity
SELECT pg_database.datname, pg_database_size(pg_database.datname) 
FROM pg_database;

-- Check for corruption
SELECT * FROM pg_stat_database WHERE datname = 'goodbooks';

-- Verify constraints
SELECT conname, contype FROM pg_constraint WHERE contype = 'f';
```

**Solutions:**
```bash
# Backup before fixing
pg_dump goodbooks > backup_$(date +%Y%m%d).sql

# Check and repair
vacuum FULL;
reindex DATABASE goodbooks;

# Restore from backup if needed
dropdb goodbooks
createdb goodbooks
psql goodbooks < backup_20231201.sql
```

## 🔄 Cache Problems

### Redis Connection Issues

**Symptoms:**
- "Connection refused" to Redis
- Cache misses
- Timeout errors

**Diagnosis:**
```bash
# Test Redis connectivity
redis-cli ping
redis-cli -h redis-host -p 6379 ping

# Check Redis status
sudo systemctl status redis
docker logs redis-container

# Check Redis configuration
redis-cli config get "*"
```

**Solutions:**
```bash
# Restart Redis
sudo systemctl restart redis
docker restart redis-container

# Check Redis configuration
# /etc/redis/redis.conf
bind 0.0.0.0
port 6379
maxmemory 2gb
maxmemory-policy allkeys-lru

# Test connection with authentication
redis-cli -a password ping
```

### Low Cache Hit Rate

**Symptoms:**
- Cache hit rate < 80%
- Slow response times
- High database load

**Diagnosis:**
```bash
# Check cache statistics
redis-cli info stats | grep keyspace
redis-cli info memory

# Monitor cache operations
redis-cli monitor

# Check cache keys
redis-cli keys "*" | head -20
redis-cli ttl "some-key"
```

**Solutions:**
```python
# Optimize cache strategy
class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        
    def get_or_set(self, key, fetch_func, ttl=3600):
        # Try to get from cache
        cached_value = self.redis_client.get(key)
        if cached_value:
            return json.loads(cached_value)
            
        # Fetch and cache
        value = fetch_func()
        self.redis_client.setex(key, ttl, json.dumps(value))
        return value
        
    def warm_cache(self):
        # Pre-populate cache with popular items
        popular_users = self.get_popular_users()
        for user_id in popular_users:
            key = f"recommendations:user:{user_id}"
            if not self.redis_client.exists(key):
                recs = self.get_recommendations(user_id)
                self.redis_client.setex(key, 3600, json.dumps(recs))
```

### Cache Memory Issues

**Symptoms:**
- Redis memory usage > 90%
- Eviction warnings
- OOM errors

**Diagnosis:**
```bash
# Check memory usage
redis-cli info memory | grep used_memory
redis-cli info stats | grep evicted_keys

# Check largest keys
redis-cli --bigkeys

# Memory usage by key pattern
redis-cli eval "return redis.call('memory', 'usage', KEYS[1])" 1 some-key
```

**Solutions:**
```bash
# Increase Redis memory limit
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru

# Optimize data structures
# Use Redis hashes for related data
redis-cli hset user:123 name "John" age 30

# Set appropriate TTL
redis-cli expire user:123 3600

# Clean up old keys
redis-cli eval "for i=1,#KEYS do redis.call('del', KEYS[i]) end" 0 $(redis-cli keys "old:*")
```

## 🤖 Model Issues

### Model Training Failures

**Symptoms:**
- Training process crashes
- "Insufficient data" errors
- Memory errors during training

**Diagnosis:**
```python
# Check data quality
import pandas as pd

ratings = pd.read_csv('data/ratings.csv')
print(f"Ratings shape: {ratings.shape}")
print(f"Unique users: {ratings['user_id'].nunique()}")
print(f"Unique books: {ratings['book_id'].nunique()}")
print(f"Rating distribution:\n{ratings['rating'].value_counts()}")
print(f"Missing values:\n{ratings.isnull().sum()}")

# Check for data issues
print(f"Duplicate ratings: {ratings.duplicated().sum()}")
print(f"Invalid ratings: {(ratings['rating'] < 1) | (ratings['rating'] > 5).sum()}")
```

**Solutions:**
```python
# Data preprocessing
def clean_ratings_data(ratings_df):
    # Remove duplicates
    ratings_df = ratings_df.drop_duplicates()
    
    # Filter valid ratings
    ratings_df = ratings_df[(ratings_df['rating'] >= 1) & (ratings_df['rating'] <= 5)]
    
    # Remove users/books with too few ratings
    user_counts = ratings_df['user_id'].value_counts()
    book_counts = ratings_df['book_id'].value_counts()
    
    valid_users = user_counts[user_counts >= 5].index
    valid_books = book_counts[book_counts >= 5].index
    
    ratings_df = ratings_df[
        (ratings_df['user_id'].isin(valid_users)) &
        (ratings_df['book_id'].isin(valid_books))
    ]
    
    return ratings_df

# Reduce model complexity for large datasets
MODEL_PARAMS = {
    'collaborative': {
        'n_factors': 25,  # Reduce from 50
        'n_epochs': 10,   # Reduce from 20
        'batch_size': 1000
    }
}
```

### Poor Recommendation Quality

**Symptoms:**
- Low precision/recall scores
- User complaints about recommendations
- Cold start problems

**Diagnosis:**
```python
# Evaluate model performance
from sklearn.metrics import precision_score, recall_score

def evaluate_recommendations(model, test_data):
    predictions = []
    actuals = []
    
    for user_id in test_data['user_id'].unique():
        user_books = test_data[test_data['user_id'] == user_id]['book_id'].tolist()
        recommendations = model.get_recommendations(user_id, n_recommendations=10)
        
        # Check if recommended books are in user's actual books
        rec_books = [rec['book_id'] for rec in recommendations]
        
        for book_id in rec_books:
            predictions.append(1 if book_id in user_books else 0)
            actuals.append(1)
    
    precision = precision_score(actuals, predictions)
    recall = recall_score(actuals, predictions)
    
    return precision, recall

# Check for cold start issues
def analyze_cold_start(ratings_df):
    user_counts = ratings_df['user_id'].value_counts()
    book_counts = ratings_df['book_id'].value_counts()
    
    cold_users = (user_counts < 5).sum()
    cold_books = (book_counts < 5).sum()
    
    print(f"Cold start users: {cold_users}")
    print(f"Cold start books: {cold_books}")
```

**Solutions:**
```python
# Improve hybrid model weights
class HybridRecommender:
    def __init__(self, content_weight=0.3, collaborative_weight=0.7):
        self.content_weight = content_weight
        self.collaborative_weight = collaborative_weight
        
    def get_recommendations(self, user_id=None, book_title=None, n_recommendations=5):
        if user_id and self.has_sufficient_data(user_id):
            # Use collaborative filtering for users with enough data
            collab_recs = self.collaborative_model.get_recommendations(user_id, n_recommendations * 2)
            content_recs = self.content_model.get_recommendations(user_id, n_recommendations)
            
            # Combine recommendations
            combined_recs = self.combine_recommendations(
                collab_recs, content_recs, 
                self.collaborative_weight, self.content_weight
            )
        else:
            # Use content-based for cold start
            combined_recs = self.content_model.get_recommendations(
                book_title=book_title, n_recommendations=n_recommendations
            )
            
        return combined_recs[:n_recommendations]
        
    def has_sufficient_data(self, user_id, min_ratings=5):
        user_ratings = self.ratings_df[self.ratings_df['user_id'] == user_id]
        return len(user_ratings) >= min_ratings
```

## 🌐 API Errors

### HTTP 500 Internal Server Error

**Symptoms:**
- Server returns 500 status code
- "Internal Server Error" message
- Application crashes

**Diagnosis:**
```bash
# Check application logs
docker logs goodbooks-api | grep -i error
kubectl logs deployment/goodbooks-api -n goodbooks | grep -i error

# Check specific error details
curl -v http://localhost:8000/recommendations

# Test with minimal request
curl -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

**Solutions:**
```python
# Add better error handling
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    try:
        # Validate input
        if not request.user_id and not request.book_title:
            raise HTTPException(
                status_code=400, 
                detail="Either user_id or book_title must be provided"
            )
            
        # Get recommendations
        recommendations = recommender.get_recommendations(
            user_id=request.user_id,
            book_title=request.book_title,
            n_recommendations=request.n_recommendations
        )
        
        return RecommendationResponse(recommendations=recommendations)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### HTTP 422 Validation Error

**Symptoms:**
- "Unprocessable Entity" errors
- Pydantic validation failures
- Invalid request format

**Diagnosis:**
```bash
# Test with invalid data
curl -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{"invalid_field": "value"}'

# Check request format
curl -X POST http://localhost:8000/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "not_a_number"}'
```

**Solutions:**
```python
# Improve Pydantic models
from pydantic import BaseModel, validator
from typing import Optional

class RecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    book_title: Optional[str] = None
    n_recommendations: int = 5
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('user_id must be positive')
        return v
        
    @validator('n_recommendations')
    def validate_n_recommendations(cls, v):
        if v <= 0 or v > 100:
            raise ValueError('n_recommendations must be between 1 and 100')
        return v
        
    @validator('book_title')
    def validate_book_title(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('book_title cannot be empty')
        return v.strip() if v else v
```

### HTTP 429 Rate Limit Exceeded

**Symptoms:**
- "Too Many Requests" errors
- Rate limiting triggered
- Blocked requests

**Diagnosis:**
```bash
# Test rate limiting
for i in {1..20}; do
  curl -w "Response: %{http_code}\n" http://localhost:8000/recommendations
  sleep 0.1
done

# Check rate limiting configuration
nginx -T | grep limit_req
```

**Solutions:**
```python
# Implement application-level rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/recommendations")
@limiter.limit("10/minute")
async def get_recommendations(request: Request, rec_request: RecommendationRequest):
    # Implementation here
    pass
```

```nginx
# Nginx rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        location /recommendations {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
        }
    }
}
```

## 🐳 Docker Issues

### Container Won't Start

**Symptoms:**
- Container exits immediately
- "No such file or directory" errors
- Permission denied errors

**Diagnosis:**
```bash
# Check container logs
docker logs container_name
docker logs --details container_name

# Inspect container
docker inspect container_name

# Check if image exists
docker images | grep goodbooks

# Test container interactively
docker run -it goodbooks-recommender /bin/bash
```

**Solutions:**
```dockerfile
# Fix Dockerfile issues
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build Failures

**Symptoms:**
- Docker build fails
- Package installation errors
- Layer caching issues

**Diagnosis:**
```bash
# Build with verbose output
docker build --no-cache --progress=plain -t goodbooks-recommender .

# Check build context size
du -sh .

# Check .dockerignore
cat .dockerignore
```

**Solutions:**
```bash
# Create proper .dockerignore
echo "__pycache__
*.pyc
*.pyo
*.pyd
.git
.pytest_cache
.coverage
.env
README.md
.gitignore
docs/
tests/" > .dockerignore

# Multi-stage build for optimization
# Dockerfile.multistage
FROM python:3.9-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.9-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ ./src/
COPY data/ ./data/
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Network Issues

**Symptoms:**
- Containers can't communicate
- DNS resolution failures
- Port binding issues

**Diagnosis:**
```bash
# Check Docker networks
docker network ls
docker network inspect bridge

# Test container connectivity
docker exec -it container1 ping container2
docker exec -it container1 nslookup container2

# Check port mappings
docker port container_name
netstat -tulpn | grep docker
```

**Solutions:**
```yaml
# docker-compose.yml with custom network
version: '3.8'

services:
  api:
    build: .
    networks:
      - goodbooks-network
    depends_on:
      - redis
      - db
      
  redis:
    image: redis:7-alpine
    networks:
      - goodbooks-network
      
  db:
    image: postgres:15-alpine
    networks:
      - goodbooks-network

networks:
  goodbooks-network:
    driver: bridge
```

## ☸️ Kubernetes Issues

### Pod Startup Issues

**Symptoms:**
- Pods stuck in Pending state
- ImagePullBackOff errors
- CrashLoopBackOff errors

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n goodbooks
kubectl describe pod pod_name -n goodbooks

# Check events
kubectl get events -n goodbooks --sort-by='.lastTimestamp'

# Check logs
kubectl logs pod_name -n goodbooks
kubectl logs pod_name -n goodbooks --previous
```

**Solutions:**
```yaml
# Fix resource constraints
apiVersion: apps/v1
kind: Deployment
metadata:
  name: goodbooks-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: goodbooks-recommender:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        # Add readiness and liveness probes
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Service Discovery Issues

**Symptoms:**
- Services can't reach each other
- DNS resolution failures
- Connection refused errors

**Diagnosis:**
```bash
# Check services
kubectl get services -n goodbooks
kubectl describe service service_name -n goodbooks

# Test service connectivity
kubectl exec -it pod_name -n goodbooks -- nslookup service_name
kubectl exec -it pod_name -n goodbooks -- curl http://service_name:port/health

# Check endpoints
kubectl get endpoints -n goodbooks
```

**Solutions:**
```yaml
# Ensure proper service configuration
apiVersion: v1
kind: Service
metadata:
  name: goodbooks-api-service
  namespace: goodbooks
spec:
  selector:
    app: goodbooks-api  # Must match pod labels
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress Issues

**Symptoms:**
- External access not working
- 404 errors from ingress
- SSL certificate issues

**Diagnosis:**
```bash
# Check ingress
kubectl get ingress -n goodbooks
kubectl describe ingress ingress_name -n goodbooks

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Test ingress rules
curl -H "Host: api.goodbooks.com" http://ingress_ip/health
```

**Solutions:**
```yaml
# Fix ingress configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: goodbooks-ingress
  namespace: goodbooks
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.goodbooks.com
    secretName: goodbooks-tls
  rules:
  - host: api.goodbooks.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: goodbooks-api-service
            port:
              number: 80
```

## 📊 Monitoring & Debugging

### Application Monitoring

```python
# Enhanced logging configuration
import logging
import sys
from pythonjsonlogger import jsonlogger

# Configure structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# JSON formatter for structured logs
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler('/var/log/goodbooks/app.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info({
        "event": "request_start",
        "method": request.method,
        "url": str(request.url),
        "client_ip": request.client.host
    })
    
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    logger.info({
        "event": "request_end",
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "duration": duration
    })
    
    return response
```

### Performance Profiling

```python
# Add profiling endpoint
from cProfile import Profile
from pstats import Stats
from io import StringIO

@app.get("/debug/profile")
async def profile_endpoint():
    """Profile the recommendation endpoint"""
    profiler = Profile()
    profiler.enable()
    
    # Run some recommendations
    for i in range(10):
        recommender.get_recommendations(user_id=i+1, n_recommendations=5)
    
    profiler.disable()
    
    # Get stats
    stats_stream = StringIO()
    stats = Stats(profiler, stream=stats_stream)
    stats.sort_stats('cumulative').print_stats(20)
    
    return {"profile_stats": stats_stream.getvalue()}

# Memory profiling
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function to profile
    pass
```

### Health Checks

```python
# Comprehensive health check
@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database check
    try:
        # Simple query to test database
        result = await database.fetch_one("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Model check
    try:
        # Test model prediction
        test_recs = recommender.get_recommendations(user_id=1, n_recommendations=1)
        health_status["checks"]["model"] = "healthy"
    except Exception as e:
        health_status["checks"]["model"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)
```

## ❌ Common Error Messages

### "ModuleNotFoundError: No module named 'src'"

**Solution:**
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run with module flag
python -m src.api.main

# Or add to sys.path in code
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
```

### "psycopg2.OperationalError: could not connect to server"

**Solution:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection parameters
psql -h localhost -U goodbooks -d goodbooks

# Update connection string
DATABASE_URL="postgresql://goodbooks:password@localhost:5432/goodbooks"
```

### "redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379"

**Solution:**
```bash
# Start Redis
sudo systemctl start redis
docker start redis-container

# Check Redis configuration
redis-cli ping

# Update Redis connection
REDIS_HOST="localhost"
REDIS_PORT="6379"
```

### "FileNotFoundError: [Errno 2] No such file or directory: 'data/ratings.csv'"

**Solution:**
```bash
# Check file exists
ls -la data/

# Download data if missing
wget -O data/ratings.csv https://example.com/ratings.csv

# Update file path in code
RATINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'ratings.csv')
```

### "ValueError: Input contains NaN, infinity or a value too large"

**Solution:**
```python
# Clean data before training
import numpy as np
import pandas as pd

def clean_data(df):
    # Remove NaN values
    df = df.dropna()
    
    # Remove infinite values
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    
    # Check for valid ranges
    if 'rating' in df.columns:
        df = df[(df['rating'] >= 1) & (df['rating'] <= 5)]
    
    return df
```

## 🚀 Performance Optimization

### Quick Wins

1. **Enable Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_book_features(book_id):
    return compute_features(book_id)
```

2. **Use Connection Pooling**
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30
)
```

3. **Optimize Database Queries**
```sql
-- Add indexes
CREATE INDEX CONCURRENTLY idx_ratings_user_id ON ratings(user_id);
CREATE INDEX CONCURRENTLY idx_ratings_book_id ON ratings(book_id);

-- Use LIMIT for large result sets
SELECT * FROM ratings WHERE user_id = 123 LIMIT 1000;
```

4. **Use Async Operations**
```python
import asyncio
import aioredis

async def get_cached_recommendations(user_id):
    redis = await aioredis.from_url("redis://localhost")
    cached = await redis.get(f"recs:{user_id}")
    return json.loads(cached) if cached else None
```

### Advanced Optimizations

1. **Model Optimization**
```python
# Use sparse matrices for large datasets
from scipy.sparse import csr_matrix

class OptimizedCollaborativeFilter:
    def __init__(self):
        self.user_item_matrix = None
        
    def fit(self, ratings_df):
        # Convert to sparse matrix
        self.user_item_matrix = csr_matrix(
            (ratings_df['rating'], 
             (ratings_df['user_id'], ratings_df['book_id']))
        )
```

2. **Batch Processing**
```python
def batch_recommendations(user_ids, batch_size=100):
    for i in range(0, len(user_ids), batch_size):
        batch = user_ids[i:i+batch_size]
        yield process_batch(batch)
```

3. **Precomputed Recommendations**
```python
# Precompute recommendations for popular users
def precompute_recommendations():
    popular_users = get_popular_users(limit=1000)
    
    for user_id in popular_users:
        recs = recommender.get_recommendations(user_id)
        cache_key = f"precomputed:recs:{user_id}"
        redis_client.setex(cache_key, 86400, json.dumps(recs))
```

---

**Need More Help? 🆘**

If you're still experiencing issues:

1. Check the [API Reference](API_REFERENCE.md) for detailed endpoint documentation
2. Review the [Developer Guide](DEVELOPER_GUIDE.md) for development best practices
3. Consult the [Deployment Guide](DEPLOYMENT_GUIDE.md) for production setup
4. Enable debug mode and check detailed logs
5. Contact the development team with specific error messages and logs

**Remember:** Always backup your data before making significant changes!
# Load Balancer Configuration Guide

## Overview

This guide covers load balancer setup for the GoodBooks Recommender system, including both cloud-managed and self-hosted options.

## Cloud Load Balancer Options

### AWS Application Load Balancer (ALB)
- **Recommended for AWS deployments**
- Layer 7 load balancing with advanced routing
- Built-in health checks and SSL termination
- Integration with AWS WAF and Auto Scaling

### Google Cloud Load Balancer
- **Recommended for GCP deployments**
- Global and regional load balancing options
- Built-in DDoS protection
- Integration with Google Cloud Armor

### Azure Application Gateway
- **Recommended for Azure deployments**
- Web application firewall capabilities
- SSL offloading and URL-based routing
- Integration with Azure Monitor

## Self-Hosted Load Balancer (NGINX)

### NGINX Configuration

#### Basic Load Balancer Setup
```nginx
upstream goodbooks_backend {
    least_conn;
    server api-1:8000 max_fails=3 fail_timeout=30s;
    server api-2:8000 max_fails=3 fail_timeout=30s;
    server api-3:8000 max_fails=3 fail_timeout=30s;
    
    # Backup server
    server api-backup:8000 backup;
}

server {
    listen 80;
    listen 443 ssl http2;
    server_name goodbooks-api.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/goodbooks.crt;
    ssl_certificate_key /etc/nginx/ssl/goodbooks.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Main API endpoints
    location /api/ {
        proxy_pass http://goodbooks_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check configuration
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 30s;
        
        # Session affinity (if needed)
        # ip_hash;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://goodbooks_backend/health;
        access_log off;
    }

    # Metrics endpoint (restricted access)
    location /metrics {
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
        
        proxy_pass http://goodbooks_backend/metrics;
        access_log off;
    }

    # Dashboard static files
    location / {
        root /var/www/goodbooks-dashboard;
        try_files $uri $uri/ /index.html;
        
        # Caching for static assets
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### Docker Compose with NGINX Load Balancer

```yaml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./dashboard:/var/www/goodbooks-dashboard:ro
    depends_on:
      - api-1
      - api-2
      - api-3
    networks:
      - goodbooks-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

  # API Instances
  api-1:
    build: .
    environment:
      - ENVIRONMENT=production
      - REDIS_HOST=redis-cluster
      - INSTANCE_ID=api-1
    volumes:
      - ./data:/app/data:ro
    networks:
      - goodbooks-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api-2:
    build: .
    environment:
      - ENVIRONMENT=production
      - REDIS_HOST=redis-cluster
      - INSTANCE_ID=api-2
    volumes:
      - ./data:/app/data:ro
    networks:
      - goodbooks-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api-3:
    build: .
    environment:
      - ENVIRONMENT=production
      - REDIS_HOST=redis-cluster
      - INSTANCE_ID=api-3
    volumes:
      - ./data:/app/data:ro
    networks:
      - goodbooks-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  goodbooks-network:
    driver: bridge
```

## Health Check Configuration

### Application Health Check Endpoint
The `/health` endpoint should return detailed health information:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "instance_id": "api-1",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "ml_models": "healthy",
    "disk_space": "healthy"
  },
  "metrics": {
    "memory_usage_percent": 45.2,
    "cpu_usage_percent": 12.5,
    "active_connections": 15
  }
}
```

### Load Balancer Health Check Settings

#### NGINX Health Check
```nginx
upstream goodbooks_backend {
    server api-1:8000 max_fails=3 fail_timeout=30s;
    server api-2:8000 max_fails=3 fail_timeout=30s;
    server api-3:8000 max_fails=3 fail_timeout=30s;
}

# Health check location
location /health {
    proxy_pass http://goodbooks_backend/health;
    proxy_connect_timeout 5s;
    proxy_read_timeout 10s;
    
    # Mark as failed if response is not 200
    proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
}
```

#### Cloud Load Balancer Health Checks

**AWS ALB:**
- Path: `/health`
- Protocol: HTTP
- Port: 8000
- Healthy threshold: 2
- Unhealthy threshold: 3
- Timeout: 5 seconds
- Interval: 30 seconds

**Google Cloud:**
- Path: `/health`
- Port: 8000
- Check interval: 30 seconds
- Timeout: 5 seconds
- Healthy threshold: 2
- Unhealthy threshold: 3

## Session Affinity (Sticky Sessions)

### When to Use Sticky Sessions
- In-memory session data
- User preference caching
- WebSocket connections

### NGINX Session Affinity
```nginx
upstream goodbooks_backend {
    ip_hash;  # Route based on client IP
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}
```

### Cloud Load Balancer Session Affinity
- **AWS ALB**: Enable stickiness with duration-based cookies
- **Google Cloud**: Use generated cookie or client IP affinity
- **Azure**: Enable session affinity in Application Gateway

## SSL/TLS Configuration

### SSL Certificate Setup
```bash
# Generate self-signed certificate for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/goodbooks.key \
    -out nginx/ssl/goodbooks.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=goodbooks-api.example.com"

# For production, use Let's Encrypt or cloud-managed certificates
```

### NGINX SSL Configuration
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/goodbooks.crt;
    ssl_certificate_key /etc/nginx/ssl/goodbooks.key;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
}
```

## Monitoring and Logging

### NGINX Access Logs
```nginx
http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'rt=$request_time uct="$upstream_connect_time" '
                   'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
}
```

### Metrics Collection
- Request count and response times
- Upstream server status
- SSL certificate expiration
- Cache hit rates

## Auto Scaling Configuration

### Cloud Auto Scaling
- **AWS**: Auto Scaling Groups with ALB
- **Google Cloud**: Managed Instance Groups
- **Azure**: Virtual Machine Scale Sets

### Docker Swarm Auto Scaling
```yaml
version: '3.8'

services:
  api:
    image: goodbooks-api:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Performance Optimization

### Connection Pooling
```nginx
upstream goodbooks_backend {
    keepalive 32;
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

server {
    location /api/ {
        proxy_pass http://goodbooks_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

### Caching Configuration
```nginx
# Proxy caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api/recommendations {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    proxy_pass http://goodbooks_backend;
}
```

## Disaster Recovery

### Multi-Region Setup
- Primary region with full infrastructure
- Standby region with data replication
- DNS-based failover

### Backup Strategies
- Regular configuration backups
- SSL certificate management
- Log aggregation and retention

## Security Considerations

### Rate Limiting
```nginx
# Rate limiting by IP
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}

location /api/auth/ {
    limit_req zone=login burst=5 nodelay;
}
```

### WAF Integration
- Cloud WAF services (AWS WAF, Cloudflare)
- ModSecurity with NGINX
- Custom security rules

### Access Control
```nginx
# Restrict admin endpoints
location /api/admin/ {
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    deny all;
    proxy_pass http://goodbooks_backend;
}
```

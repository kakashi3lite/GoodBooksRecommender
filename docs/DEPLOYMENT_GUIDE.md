# Deployment Guide

Comprehensive deployment guide for the GoodBooks Recommender system across different environments.

## 📋 Table of Contents

- [Deployment Overview](#-deployment-overview)
- [Environment Setup](#-environment-setup)
- [Docker Deployment](#-docker-deployment)
- [Kubernetes Deployment](#-kubernetes-deployment)
- [Cloud Deployment](#-cloud-deployment)
- [Monitoring & Observability](#-monitoring--observability)
- [Security Configuration](#-security-configuration)
- [Performance Tuning](#-performance-tuning)
- [Backup & Recovery](#-backup--recovery)
- [Troubleshooting](#-troubleshooting)

## 🚀 Deployment Overview

### Architecture Components

```mermaid
graph TB
    LB[Load Balancer] --> API1[API Server 1]
    LB --> API2[API Server 2]
    LB --> API3[API Server 3]
    
    API1 --> Redis[Redis Cache]
    API2 --> Redis
    API3 --> Redis
    
    API1 --> DB[(PostgreSQL)]
    API2 --> DB
    API3 --> DB
    
    API1 --> ML[ML Models]
    API2 --> ML
    API3 --> ML
    
    Monitor[Prometheus] --> API1
    Monitor --> API2
    Monitor --> API3
    Monitor --> Redis
    Monitor --> DB
    
    Grafana --> Monitor
```

### Deployment Targets

| Environment | Use Case | Resources | Availability |
|-------------|----------|-----------|-------------|
| Development | Local testing | 2 CPU, 4GB RAM | Single instance |
| Staging | Pre-production testing | 4 CPU, 8GB RAM | Single instance |
| Production | Live service | 8+ CPU, 16+ GB RAM | Multi-instance |

## 🛠 Environment Setup

### System Requirements

#### Minimum Requirements
- **CPU:** 2 cores
- **RAM:** 4GB
- **Storage:** 20GB SSD
- **Network:** 100 Mbps

#### Recommended (Production)
- **CPU:** 8+ cores
- **RAM:** 16+ GB
- **Storage:** 100GB+ SSD
- **Network:** 1 Gbps

### Operating System Support

| OS | Version | Status |
|----|---------|--------|
| Ubuntu | 20.04+ | ✅ Recommended |
| CentOS | 8+ | ✅ Supported |
| RHEL | 8+ | ✅ Supported |
| Amazon Linux | 2 | ✅ Supported |
| Windows Server | 2019+ | ⚠️ Limited support |

### Prerequisites Installation

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3.9-dev -y

# Install system dependencies
sudo apt install build-essential libpq-dev redis-server -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### CentOS/RHEL
```bash
# Update system
sudo yum update -y

# Install Python 3.9+
sudo yum install python39 python39-devel -y

# Install system dependencies
sudo yum groupinstall "Development Tools" -y
sudo yum install postgresql-devel redis -y

# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io -y
sudo systemctl start docker
sudo systemctl enable docker
```

## 🐳 Docker Deployment

### Single Container Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
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

#### Build and Run
```bash
# Build image
docker build -t goodbooks-recommender:latest .

# Run container
docker run -d \
  --name goodbooks-api \
  -p 8000:8000 \
  -e REDIS_HOST=redis \
  -e DATABASE_URL=postgresql://user:pass@db:5432/goodbooks \
  goodbooks-recommender:latest
```

### Docker Compose Deployment

#### docker-compose.yml
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - DATABASE_URL=postgresql://goodbooks:password@db:5432/goodbooks
      - DEBUG_MODE=false
    depends_on:
      - redis
      - db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=goodbooks
      - POSTGRES_USER=goodbooks
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

#### Production docker-compose.prod.yml
```yaml
version: '3.8'

services:
  api:
    image: goodbooks-recommender:${VERSION:-latest}
    environment:
      - REDIS_HOST=redis
      - DATABASE_URL=${DATABASE_URL}
      - DEBUG_MODE=false
      - LOG_LEVEL=INFO
    deploy:
      replicas: 5
      update_config:
        parallelism: 2
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --maxmemory 4gb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### Deployment Commands
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale API services
docker-compose up -d --scale api=5

# Update deployment
docker-compose pull
docker-compose up -d --force-recreate
```

## ☸️ Kubernetes Deployment

### Namespace Configuration

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: goodbooks
  labels:
    name: goodbooks
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: goodbooks-config
  namespace: goodbooks
data:
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  DEBUG_MODE: "false"
  LOG_LEVEL: "INFO"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
  CACHE_TTL: "3600"
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: goodbooks-secrets
  namespace: goodbooks
type: Opaque
data:
  DATABASE_URL: cG9zdGdyZXNxbDovL3VzZXI6cGFzc0BkYjozNDMyL2dvb2Rib29rcw==  # base64 encoded
  REDIS_PASSWORD: cGFzc3dvcmQ=  # base64 encoded
```

### API Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: goodbooks-api
  namespace: goodbooks
  labels:
    app: goodbooks-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: goodbooks-api
  template:
    metadata:
      labels:
        app: goodbooks-api
    spec:
      containers:
      - name: api
        image: goodbooks-recommender:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: goodbooks-config
        - secretRef:
            name: goodbooks-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      imagePullSecrets:
      - name: regcred
```

### Service Configuration

```yaml
# api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: goodbooks-api-service
  namespace: goodbooks
spec:
  selector:
    app: goodbooks-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: goodbooks-ingress
  namespace: goodbooks
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
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

### Redis Deployment

```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: goodbooks
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        args:
        - redis-server
        - --appendonly
        - "yes"
        - --maxmemory
        - "2gb"
        - --maxmemory-policy
        - "allkeys-lru"
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: goodbooks
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### Persistent Volume Claims

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: goodbooks
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: goodbooks-api-hpa
  namespace: goodbooks
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: goodbooks-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deployment Commands

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n goodbooks
kubectl get services -n goodbooks
kubectl get ingress -n goodbooks

# Scale deployment
kubectl scale deployment goodbooks-api --replicas=5 -n goodbooks

# Rolling update
kubectl set image deployment/goodbooks-api api=goodbooks-recommender:v2.0.0 -n goodbooks

# Check logs
kubectl logs -f deployment/goodbooks-api -n goodbooks
```

## ☁️ Cloud Deployment

### AWS Deployment

#### ECS with Fargate

```json
{
  "family": "goodbooks-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "goodbooks-api",
      "image": "account.dkr.ecr.region.amazonaws.com/goodbooks-recommender:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "REDIS_HOST",
          "value": "goodbooks-redis.cache.amazonaws.com"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@goodbooks.cluster.amazonaws.com:5432/goodbooks"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/goodbooks-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Terraform Configuration

```hcl
# main.tf
provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "goodbooks-vpc"
  }
}

# Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "goodbooks-private-${count.index + 1}"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 10}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "goodbooks-public-${count.index + 1}"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "goodbooks-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "goodbooks-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "goodbooks-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 3
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = [aws_security_group.ecs_tasks.id]
    subnets          = aws_subnet.private[*].id
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "goodbooks-api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.api]
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier     = "goodbooks-db"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.medium"
  allocated_storage = 100
  storage_encrypted = true

  db_name  = "goodbooks"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  skip_final_snapshot = true
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "goodbooks-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "goodbooks-redis"
  description                = "Redis cluster for GoodBooks"
  
  node_type                  = "cache.t3.medium"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}
```

### Google Cloud Platform

#### Cloud Run Deployment

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: goodbooks-api
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "100"
        autoscaling.knative.dev/minScale: "1"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "4Gi"
        run.googleapis.com/cpu: "2"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/project-id/goodbooks-recommender:latest
        ports:
        - name: http1
          containerPort: 8000
        env:
        - name: REDIS_HOST
          value: "10.0.0.3"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          timeoutSeconds: 5
          periodSeconds: 10
          failureThreshold: 3
```

#### Deployment Script

```bash
#!/bin/bash
# deploy-gcp.sh

set -e

PROJECT_ID="your-project-id"
REGION="us-central1"
SERVICE_NAME="goodbooks-api"
IMAGE_TAG="latest"

# Build and push image
docker build -t gcr.io/$PROJECT_ID/goodbooks-recommender:$IMAGE_TAG .
docker push gcr.io/$PROJECT_ID/goodbooks-recommender:$IMAGE_TAG

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/goodbooks-recommender:$IMAGE_TAG \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --concurrency 80 \
  --max-instances 100 \
  --min-instances 1 \
  --set-env-vars REDIS_HOST=10.0.0.3 \
  --set-secrets DATABASE_URL=db-credentials:url

echo "Deployment completed!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')"
```

### Azure Deployment

#### Container Instances

```yaml
# azure-container-group.yaml
apiVersion: 2021-03-01
location: East US
name: goodbooks-container-group
properties:
  containers:
  - name: goodbooks-api
    properties:
      image: goodbooksregistry.azurecr.io/goodbooks-recommender:latest
      resources:
        requests:
          cpu: 2
          memoryInGb: 4
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: REDIS_HOST
        value: goodbooks-redis.redis.cache.windows.net
      - name: DATABASE_URL
        secureValue: postgresql://user:pass@goodbooks-db.postgres.database.azure.com:5432/goodbooks
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8000
    dnsNameLabel: goodbooks-api
tags:
  environment: production
  application: goodbooks
```

## 📊 Monitoring & Observability

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'goodbooks-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'node'
    static_configs:
      - targets: ['node_exporter:9100']
```

### Alert Rules

```yaml
# alert_rules.yml
groups:
- name: goodbooks_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }}s"

  - alert: LowCacheHitRate
    expr: rate(cache_hits_total[5m]) / rate(cache_requests_total[5m]) < 0.8
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Low cache hit rate"
      description: "Cache hit rate is {{ $value | humanizePercentage }}"

  - alert: HighMemoryUsage
    expr: (process_resident_memory_bytes / 1024 / 1024) > 3000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}MB"
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "GoodBooks Recommender Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### Application Metrics

```python
# src/api/monitoring.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

CACHE_HITS = Counter('cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')

async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔒 Security Configuration

### SSL/TLS Configuration

#### Nginx SSL Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.goodbooks.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
}

# Rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
}
```

### Environment Security

```bash
# .env.production
# Database
DATABASE_URL=postgresql://user:$(cat /run/secrets/db_password)@db:5432/goodbooks

# Redis
REDIS_HOST=redis
REDIS_PASSWORD=$(cat /run/secrets/redis_password)

# API Keys
API_SECRET_KEY=$(cat /run/secrets/api_secret)
JWT_SECRET_KEY=$(cat /run/secrets/jwt_secret)

# Security
ALLOWED_HOSTS=api.goodbooks.com,localhost
CORS_ORIGINS=https://goodbooks.com,https://www.goodbooks.com
DEBUG_MODE=false
```

### Docker Security

```dockerfile
# Security-hardened Dockerfile
FROM python:3.9-slim

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application
COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup data/ ./data/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start with Gunicorn
CMD ["gunicorn", "src.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## ⚡ Performance Tuning

### Application Optimization

```python
# src/config.py - Production settings
class ProductionConfig(Config):
    # Database connection pooling
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    DATABASE_POOL_TIMEOUT = 30
    
    # Redis connection pooling
    REDIS_POOL_SIZE = 50
    REDIS_POOL_TIMEOUT = 5
    
    # Cache settings
    CACHE_TTL = 3600  # 1 hour
    CACHE_MAX_SIZE = 10000
    
    # Model settings
    MODEL_BATCH_SIZE = 1000
    MODEL_CACHE_SIZE = 5000
    
    # API settings
    MAX_WORKERS = 4
    WORKER_CONNECTIONS = 1000
    KEEPALIVE_TIMEOUT = 5
```

### Database Optimization

```sql
-- PostgreSQL optimization
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100

-- Indexes for performance
CREATE INDEX CONCURRENTLY idx_ratings_user_id ON ratings(user_id);
CREATE INDEX CONCURRENTLY idx_ratings_book_id ON ratings(book_id);
CREATE INDEX CONCURRENTLY idx_books_title ON books USING gin(to_tsvector('english', title));
CREATE INDEX CONCURRENTLY idx_book_tags_book_id ON book_tags(book_id);

-- Analyze tables
ANALYZE ratings;
ANALYZE books;
ANALYZE book_tags;
```

### Redis Optimization

```conf
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 300
timeout 0
tcp-backlog 511
```

### Load Testing

```bash
# Apache Bench
ab -n 10000 -c 100 -T 'application/json' -p request.json http://localhost:8000/recommendations

# wrk
wrk -t12 -c400 -d30s --script=post.lua http://localhost:8000/recommendations

# Locust
locust -f locustfile.py --host=http://localhost:8000
```

```python
# locustfile.py
from locust import HttpUser, task, between
import json

class RecommendationUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_user_recommendations(self):
        self.client.post("/recommendations", 
                        json={"user_id": 123, "n_recommendations": 5})
    
    @task(1)
    def get_content_recommendations(self):
        self.client.post("/recommendations", 
                        json={"book_title": "1984", "n_recommendations": 5})
    
    @task(1)
    def health_check(self):
        self.client.get("/health")
```

## 💾 Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
DB_NAME="goodbooks"
DB_USER="goodbooks"
DB_HOST="localhost"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -b -v -f $BACKUP_DIR/goodbooks_$DATE.backup

# Compress backup
gzip $BACKUP_DIR/goodbooks_$DATE.backup

# Upload to S3
aws s3 cp $BACKUP_DIR/goodbooks_$DATE.backup.gz s3://goodbooks-backups/postgres/

# Clean old local backups (keep 7 days)
find $BACKUP_DIR -name "*.backup.gz" -mtime +7 -delete

echo "Backup completed: goodbooks_$DATE.backup.gz"
```

### Redis Backup

```bash
#!/bin/bash
# backup-redis.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/redis"
REDIS_HOST="localhost"
REDIS_PORT="6379"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create Redis backup
redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb $BACKUP_DIR/dump_$DATE.rdb

# Compress backup
gzip $BACKUP_DIR/dump_$DATE.rdb

# Upload to S3
aws s3 cp $BACKUP_DIR/dump_$DATE.rdb.gz s3://goodbooks-backups/redis/

# Clean old backups
find $BACKUP_DIR -name "*.rdb.gz" -mtime +3 -delete

echo "Redis backup completed: dump_$DATE.rdb.gz"
```

### Automated Backup with Cron

```bash
# crontab -e
# Daily database backup at 2 AM
0 2 * * * /scripts/backup-db.sh >> /var/log/backup-db.log 2>&1

# Redis backup every 6 hours
0 */6 * * * /scripts/backup-redis.sh >> /var/log/backup-redis.log 2>&1

# Weekly full system backup
0 3 * * 0 /scripts/backup-full.sh >> /var/log/backup-full.log 2>&1
```

### Disaster Recovery

```bash
#!/bin/bash
# restore-db.sh

BACKUP_FILE=$1
DB_NAME="goodbooks"
DB_USER="goodbooks"
DB_HOST="localhost"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Download from S3 if needed
if [[ $BACKUP_FILE == s3://* ]]; then
    LOCAL_FILE="/tmp/$(basename $BACKUP_FILE)"
    aws s3 cp $BACKUP_FILE $LOCAL_FILE
    BACKUP_FILE=$LOCAL_FILE
fi

# Decompress if needed
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip $BACKUP_FILE
    BACKUP_FILE=${BACKUP_FILE%.gz}
fi

# Drop existing database
psql -h $DB_HOST -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -h $DB_HOST -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Restore database
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME -v $BACKUP_FILE

echo "Database restored from $BACKUP_FILE"
```

## 🔧 Troubleshooting

### Common Issues

#### High Memory Usage

**Symptoms:**
- OOM kills in containers
- Slow response times
- High swap usage

**Diagnosis:**
```bash
# Check memory usage
docker stats
kubectl top pods -n goodbooks

# Check application memory
curl http://localhost:8000/metrics | grep process_resident_memory

# Profile memory usage
python -m memory_profiler src/api/main.py
```

**Solutions:**
```python
# Optimize model parameters
MODEL_PARAMS = {
    'collaborative': {
        'n_factors': 25,  # Reduce from 50
        'batch_size': 500  # Reduce batch size
    }
}

# Implement data streaming
def load_data_in_chunks(file_path, chunk_size=10000):
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        yield chunk

# Clear unused variables
import gc
gc.collect()
```

#### Database Connection Issues

**Symptoms:**
- Connection timeouts
- "Too many connections" errors
- Slow queries

**Diagnosis:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Check locks
SELECT * FROM pg_locks WHERE NOT granted;
```

**Solutions:**
```python
# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600
)

# Connection retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def execute_query(query):
    with engine.connect() as conn:
        return conn.execute(query)
```

#### Cache Performance Issues

**Symptoms:**
- Low cache hit rates
- High Redis memory usage
- Slow cache operations

**Diagnosis:**
```bash
# Redis info
redis-cli info memory
redis-cli info stats

# Check cache hit rate
redis-cli info stats | grep keyspace_hits

# Monitor slow operations
redis-cli slowlog get 10
```

**Solutions:**
```python
# Optimize cache keys
def generate_cache_key(user_id, book_title, n_recs):
    # Use shorter, more efficient keys
    return f"u:{user_id}:b:{hash(book_title)}:n:{n_recs}"

# Implement cache warming
async def warm_cache():
    popular_users = get_popular_users()
    for user_id in popular_users:
        await get_recommendations(user_id=user_id)

# Use Redis pipelining
import redis

def batch_cache_operations(operations):
    pipe = redis_client.pipeline()
    for op in operations:
        pipe.set(op['key'], op['value'], ex=op['ttl'])
    pipe.execute()
```

### Monitoring Commands

```bash
# System monitoring
top
htop
iotop
netstat -tulpn

# Docker monitoring
docker stats
docker logs -f container_name
docker exec -it container_name /bin/bash

# Kubernetes monitoring
kubectl get pods -n goodbooks
kubectl describe pod pod_name -n goodbooks
kubectl logs -f deployment/goodbooks-api -n goodbooks
kubectl exec -it pod_name -n goodbooks -- /bin/bash

# Application monitoring
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

### Log Analysis

```bash
# Application logs
tail -f /var/log/goodbooks/app.log
grep "ERROR" /var/log/goodbooks/app.log | tail -20

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
journalctl -u goodbooks-api -f
dmesg | tail

# Log aggregation with ELK
# Logstash configuration for parsing application logs
input {
  file {
    path => "/var/log/goodbooks/app.log"
    start_position => "beginning"
  }
}

filter {
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{WORD:logger} - %{WORD:level} - %{GREEDYDATA:message}" }
  }
  
  date {
    match => [ "timestamp", "ISO8601" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "goodbooks-logs-%{+YYYY.MM.dd}"
  }
}
```

---

**Deployment Success! 🚀**

Your GoodBooks Recommender system is now ready for production. Monitor the system closely during the first few days and adjust configurations as needed based on actual usage patterns.

For additional support:
- Check the [troubleshooting section](#-troubleshooting)
- Review [monitoring dashboards](#-monitoring--observability)
- Contact the development team for critical issues
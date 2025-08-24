# GoodBooks Recommender – Project Brief

## Purpose
AI-first platform that recommends books and curated news through a React/TypeScript dashboard backed by a Python FastAPI service.

## Domain
- Book and article recommendations
- News expansion and summarization
- User analytics and A/B experiments

## Key Flows
1. User signs in with JWT-based auth
2. Frontend requests recommendations and news feed
3. Backend serves data, caching results in Redis and persisting in PostgreSQL
4. Analytics and experiments recorded for real-time dashboards

## Public Interfaces
- **Web UI**: `dashboard/index.html`
- **REST API**: `src/api/main.py`, `src/news/api/*`

## Environments
- **Local**: `docker-compose.yml`
- **Monitoring**: `docker-compose.monitoring.yml`
- **Production**: Kubernetes manifests (not in repo) driven by Terraform in `terraform/`

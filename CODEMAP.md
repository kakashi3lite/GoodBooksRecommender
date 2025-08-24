# Code Map

```text
src/
  api/                # FastAPI application and routes
  auth/               # JWT auth, roles, permissions
  components/         # React dashboard components
  analytics/          # Real-time metrics and A/B testing helpers
  core/               # config, logging, monitoring utilities
  hooks/              # React hooks
  models/             # ML models and managers
  news/               # News intelligence and expansion APIs
  services/           # Frontend service clients
  stores/             # Redux/Zustand state containers
  utils/              # Shared utilities
  workers/            # Background jobs

tests/
  frontend/           # Vitest component tests
  backend/            # pytest API tests
  news/               # news engine tests

scripts/              # Dev and analytics scripts
terraform/            # Infrastructure as code modules
```

## Entrypoints
- Frontend: `src/main.tsx`
- Backend API: `src/api/main.py`

# 📚 GoodBooks Recommender - AI Agent Instructions

This document provides essential knowledge to help AI coding agents become productive in the GoodBooks Recommender codebase.

## 🏛️ Architecture Overview

The project is a full-stack book recommendation platform. **Only the edge stack is deployed:**

- **Frontend**: React 18 + TypeScript + Vite ("Futuristic Dashboard"), served by Cloudflare Pages
- **Backend**: Cloudflare **Pages Functions** in `functions/api/**` — the only live API
- **Durable data**: Cloudflare **D1** (`goodbooks-accounts`, binding `DB`) for customer accounts; `localStorage` for reader state
- **Optional**: Supabase Postgres for the book catalog (`SUPABASE_URL` currently unset → embedded catalog)
- **Legacy (not deployed)**: Python FastAPI (`src/api`), PostgreSQL, Redis, Docker, Kubernetes, Terraform

Live URL: <https://books.dalecabra.com> · Deploy: `npm run deploy` (Cloudflare Pages).

### Project Philosophy

- **Chain-of-Thought Design**: Focus on user intent analysis and progressive enhancement
- **Memory Consistency**: State persistence across sessions using localStorage
- **Security-First**: Enterprise-grade security with OAuth2, JWT, and RBAC

## 🔄 Development Workflow

### Essential Commands

```bash
# Frontend Development
npm install                # Install dependencies
npm run dev                # Start development server
npm run build              # Build for production
npm test                   # Run tests
npm run lint:fix           # Fix linting issues

# Backend Development
python -m venv venv        # Create virtual environment
source venv/bin/activate   # Activate (Windows: .\venv\Scripts\activate)
pip install -r requirements.txt  # Install dependencies
uvicorn src.api.main:app --reload  # Start API server
```

### VS Code Tasks

Use the integrated VS Code tasks for common operations:

- `🚀 Start Futuristic Dashboard`: Runs the frontend in dev mode
- `🧪 Validate Dashboard Components`: Runs dashboard tests
- `🎨 Build Futuristic CSS`: Builds minified CSS
- `🤖 Start AI Assistant Server`: Starts the AI support service

## 📁 Codebase Structure

### Frontend Architecture

- `src/components/`: React components organized by feature
  - `Dashboard/`: Main dashboard components
  - `UI/`: Reusable UI elements
  - `AI/`: AI-powered components
- `src/stores/`: Redux state management
  - Uses Redux Toolkit with slice pattern
  - Persistent state with localStorage integration
- `src/hooks/`: Custom React hooks
- `src/services/`: API clients and external services

### Backend Architecture

- `functions/api/`: **live** Pages Functions — `books`, `accounts`, `ai`, `reading`, `analytics`, `news`, JSON 404 catch-all
- `functions/api/_lib/`: shared edge code — `recommender` (TF-IDF + profile scoring + MMR), `catalog`, `db`, `rss`, `ai`, `types`
- `d1/schema.sql`: D1 schema for accounts + audit events
- `src/api/`, `src/core/`, `src/models/`, `src/fakenews/`: **legacy** FastAPI/ML stack, not deployed

## 🧩 Project Conventions

### State Management

- Use Redux for global state and React hooks for local state
- Follow the slice pattern for organizing Redux state
- Add Chain-of-Thought comments explaining state design decisions

### CSS/Styling

- Use CSS modules for component-specific styles
- Follow the design system in `dashboard/css/design-system.css`
- Support both light/dark themes via CSS variables

### Testing

- Frontend: Vitest for unit testing, Cypress for E2E (not Playwright)
- Backend: pytest with fixtures for API testing
- Always run `test_kindle_dashboard.py` after making dashboard changes

## 🔗 Integration Points

### API Integration

- Frontend services in `src/services/` communicate with backend
- API endpoints follow RESTful conventions
- Recommendation API expects user context for personalization

### State & Data Flow

- Use the `books` slice for recommendation data
- Book data structure includes metadata for UI rendering
- Recommendation payloads include explanation fields

## 🚀 Deployment Process

### Cloudflare Pages (the only production pipeline)

- `npm run build` → `npm run deploy` (`wrangler pages deploy dist`)
- CI (`.github/workflows/cloudflare-pages.yml`): type-check → lint → test → build →
  purge Apple-Double files → deploy → live smoke test
- Database: `npm run db:schema` (D1, idempotent) · `npm run db:inspect`
- Docker/Kubernetes/Terraform exist for the legacy stack and are **not** in the deploy path

### Performance Considerations

- Use lazy loading for book cover images
- Implement virtualized lists for large collections
- Target <200ms response time for recommendations

## 🛑 Common Pitfalls

1. **Theme handling**: Always consider both light/dark themes in UI components
2. **State persistence**: Use the store's persistence helpers, not raw localStorage
3. **API typing**: match the JSON contracts of the Pages Functions (`functions/api/**`), not the legacy Python models
4. **Performance**: Large book lists should use virtualization
5. **Security**: Never expose API keys in frontend code

## 📦 Additional Context
- Read `AGENTS.md` first: golden rules, commands, change recipes, known gaps.
- `HANDOFF.md` — current state; `CODEMAP.md` — file map; `ARCHITECTURE.md` — deployed topology.
- `docs/LIVE_ARCHITECTURE_RUNBOOK.md` — operations; `docs/ACCOUNTS.md` — accounts/D1 contract + upgrade context.
- `DOCUMENTATION_INDEX.md` — every document; `docs/archive/` is historical only.
- Run `npm run type-check && npm test && npm run lint` before committing; `npm run docs:check` after moving docs.
- Use commit style `type(scope): summary`.

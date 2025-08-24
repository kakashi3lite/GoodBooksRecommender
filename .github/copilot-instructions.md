# 📚 GoodBooks Recommender - AI Agent Instructions

This document provides essential knowledge to help AI coding agents become productive in the GoodBooks Recommender codebase.

## 🏛️ Architecture Overview

The project is a full-stack book recommendation platform with React/TypeScript frontend and Python/FastAPI backend, structured as:

- **Frontend**: React 18 + TypeScript + Vite, follows a "Futuristic Dashboard" design
- **Backend**: Python FastAPI with hybrid ML recommendation system
- **Data**: PostgreSQL for persistent storage, Redis for caching
- **Deployment**: Docker and Kubernetes for container orchestration

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

- `src/api/`: FastAPI routes and endpoints
- `src/core/`: Core business logic and recommendation engine
- `src/models/`: Data models and schemas
- `src/fakenews/`: False news detection system (new feature)

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

### Docker Workflow

- `docker-compose up` for local development
- Production deployment uses Kubernetes with separate services
- CI/CD pipeline runs tests before deployment

### Performance Considerations

- Use lazy loading for book cover images
- Implement virtualized lists for large collections
- Target <200ms response time for recommendations

## 🛑 Common Pitfalls

1. **Theme handling**: Always consider both light/dark themes in UI components
2. **State persistence**: Use the store's persistence helpers, not raw localStorage
3. **API typing**: Ensure proper TypeScript interfaces match Python models
4. **Performance**: Large book lists should use virtualization
5. **Security**: Never expose API keys in frontend code

## 📦 Additional Context
- See `PROJECT_BRIEF.md`, `CODEMAP.md`, and `ARCHITECTURE.md` for repository overview.
- Consult `AGENTS.md` for structure, coding standards, and commands.
- Run `npm test` and `python -m pytest` before committing.
- Use commit style `type(scope): summary`.

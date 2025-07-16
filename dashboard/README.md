# GoodBooks Recommender Dashboard

## Overview
This dashboard provides a modern, responsive web interface for the GoodBooks Recommender API. It includes comprehensive functionality for book recommendations, search, explanations, and analytics.

## Features

### 1. Main Dashboard
- **Real-time metrics** from `/health` and `/metrics` endpoints
- **Quick recommendation widget** using `/recommendations` endpoint
- **Search functionality** using `/search` endpoint
- **Session management** using `/session` endpoint

### 2. Book Recommendations
- **User-based recommendations** (collaborative filtering)
- **Content-based recommendations** (similar books)
- **Hybrid recommendations** (combined approach)
- **Batch recommendations** for multiple users
- **Explanation integration** using `/explain` endpoint

### 3. Book Search & Discovery
- **Semantic search** using FAISS vector store
- **Advanced filtering** by genre, rating, publication date
- **Book details** with comprehensive information
- **Related books** suggestions

### 4. Analytics & Insights
- **Recommendation performance metrics**
- **User interaction analytics**
- **Popular books and trends**
- **System health monitoring**

### 5. Session Management
- **User session tracking**
- **Preference storage**
- **Interaction history**
- **Personalized recommendations**

## Technical Stack
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Chart.js, Bootstrap 5
- **API Integration**: Fetch API with async/await
- **State Management**: Browser localStorage and sessionStorage
- **Real-time Updates**: WebSocket connections for live metrics
- **Responsive Design**: Mobile-first approach with Bootstrap grid

## API Endpoints Integration

### Core Endpoints
- `GET /` - API information
- `GET /health` - Health check and system status
- `GET /metrics` - Prometheus metrics
- `POST /recommendations` - Get book recommendations
- `POST /explain` - Get recommendation explanations
- `POST /search` - Semantic book search
- `POST /session` - Session management

### Data Models
The dashboard properly handles all API request/response models:
- `RecommendationRequest/Response`
- `ExplainRequest/Response` 
- `SearchRequest/Response`
- `SessionRequest/Response`
- `HealthCheckResponse`

## Files Structure
```
dashboard/
├── index.html              # Main dashboard page
├── wireframes.md          # UI wireframes and design specs
├── css/
│   ├── dashboard.css      # Main dashboard styles
│   ├── components.css     # Reusable component styles
│   └── responsive.css     # Mobile responsiveness
├── js/
│   ├── app.js            # Main application logic
│   ├── api.js            # API client and endpoints
│   ├── components.js     # UI components
│   ├── charts.js         # Analytics and charting
│   └── utils.js          # Utility functions
└── assets/
    ├── images/           # Dashboard images and icons
    └── fonts/           # Custom fonts
```

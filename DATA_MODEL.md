# Data Model

| Model | Fields (key) | Notes |
|-------|--------------|-------|
| `auth.security.User` | `id`, `email`, `role`, `hashed_password` | Stored in PostgreSQL via SQLAlchemy |
| `auth.security.TokenData` | `sub`, `exp`, `scope` | JWT payload |
| `api.main.RecommendationRequest` | `user_id`, `book_title`, `n_recommendations` | Request body for `/recommendations` |
| `api.main.BookRecommendation` | `title`, `author`, `score`, `explanation` | Returned recommendation item |
| `api.main.HealthCheckResponse` | `status`, `checks` | Detailed health info |
| `analytics.real_time_analytics.RealTimeMetrics` | `experiment_id`, `metric_name`, `value` | A/B test metrics |
| `news.api.endpoints.PersonalizedFeedRequest` | `user_id`, `topics`, `limit` | Input for news feed |
| `news.api.news_expansion.NewsExpansionRequest` | `article_id`, `article_url`, `summary_level` | Expand news story |
| Cache entries | Various keys | Stored in Redis with TTL |

## Storage
- **PostgreSQL**: users, books, interactions
- **Redis**: caching and sessions
- **Vector store**: optional embedding storage for recommendations

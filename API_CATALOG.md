# API Catalog

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | API info | None |
| GET | `/health` | System health status | None |
| POST | `/auth/register` | Create user | None |
| POST | `/auth/login` | Obtain JWT tokens | None |
| POST | `/auth/refresh` | Refresh access token | Refresh token |
| POST | `/auth/logout` | Revoke refresh token | Bearer |
| POST | `/recommendations` | Get book recommendations | Bearer |
| POST | `/admin/experiments` | Create A/B experiment | Admin |
| GET | `/admin/experiments/{id}/results` | Experiment results | Admin |
| POST | `/metrics/interaction` | Record user metric | Bearer |
| GET | `/news/health` | News engine health | None |
| POST | `/news/feed/personalized` | Personalized news feed | Bearer |
| POST | `/news/summarize` | Summarize articles | Bearer |
| GET | `/news/trending` | Trending topics | None |
| POST | `/news/search` | Intelligent search | None |
| POST | `/news/feedback` | Submit feedback | Bearer |
| GET | `/news/analytics/user/{user_id}` | User analytics | Bearer |
| POST | `/news/expand` | Expand news story | Bearer |
| GET | `/news/stories/trending` | Trending expandable stories | None |
| GET | `/news/expand/{article_id}` | Quick expand by ID | None |

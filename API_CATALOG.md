# API Catalog

> ⚠️ Two API layers exist. The **live** product runs on Cloudflare Pages Functions
> (`/api/*` — see below). The Python/FastAPI catalog below documents the legacy
> ML backend, which is **not** deployed to production.

## Live API (Cloudflare Pages Functions — deployed on books.dalecabra.com)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/books` | Curated catalog (24 books) | None |
| GET | `/api/books/search?q=` | Catalog search | None |
| GET | `/api/books/recommend` | Profile recommendations | None |
| GET | `/api/books/trending` | Open Library trending (TTL-cached) | None |
| GET | `/api/books/web-search?q=` | Web book search (Google Books + Open Library) | None |
| GET | `/api/books/resolve?isbn=\|key=` | Resolve a book by ISBN / OL key | None |
| GET | `/api/books/insights?isbn=\|id=` | Real book facts + genre expectation | None |
| GET | `/api/news` | Book news from Google News RSS | None |
| POST | `/api/ai/chat` | Conversational reading companion | None |
| POST | `/api/ai/insight` | Reading reflection from real stats | None |
| GET | `/api/analytics/dashboard` | Analytics overview | None |
| GET | `/api/analytics/reading` | Reading analytics | None |

### POST /api/ai/chat — personalized conversational recommendations

```jsonc
{
  // Required
  "message": "recommend me a cozy book",
  // Optional — the reader's real profile (client-built from localStorage log)
  "context": {
    "favoriteGenres": ["Fantasy"],
    "readingGoal": 24,
    "persona": "Immersive Reader",
    "currentBook": { "title": "Dune", "authors": "Frank Herbert", "progressPct": 40, "pageCount": 412 },
    "stats": { "streak": 3, "booksFinished": 5, "pagesThisMonth": 840, "avgPagesPerSession": 42, "distinctDays": 9 },
    "recentlyFinished": [{ "title": "The Martian", "authors": "Andy Weir", "genres": ["Science Fiction"] }]
  },
  // Optional — conversation memory (the anti-"same books" contract)
  "history": [
    { "role": "user", "content": "recommend me a book" },
    { "role": "assistant", "content": "Try these…" }
  ],
  "shown": ["b-01", "b-16"]
}
```

Response:

```jsonc
{
  "reply": "…warm 2–4 sentence answer…",
  "bookSuggestions": [
    {
      "id": "b-04",
      "title": "The House in the Cerulean Sea",
      "authors": "T.J. Klune",
      "cover_url": "https://…",
      "rating": 4.6,
      "reason": "A cozy, found-family fantasy that matches your mood"
    }
  ],
  "model": "MiniMax-M2" // or "goodbooks-hybrid" when the LLM is unavailable
}
```

Personalization rules (server-side):
- `shown` ids are **excluded** every turn, plus the reader's current book and
  recently-finished titles → picks rotate and never repeat.
- When the LLM is configured it returns structured JSON book picks that become the
  suggestion cards (topped up from the web catalog); otherwise a local TF-IDF + profile
  engine serves fresh, reason-carrying picks.

---

## Legacy Python/FastAPI backend (NOT deployed)

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

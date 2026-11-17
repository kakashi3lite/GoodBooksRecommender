# API Catalog

> ⚠️ Two API layers exist. The **live** product runs on Cloudflare Pages Functions
> (`/api/*` — see below). The Python/FastAPI catalog below documents the legacy
> ML backend, which is **not** deployed to production.

## Live API (Cloudflare Pages Functions — deployed on books.dalecabra.com)

All routes are same-origin, return `application/json`, and are safe to call
without a key. Full contracts: [`docs/ACCOUNTS.md`](docs/ACCOUNTS.md),
[`docs/DATA_LAYER.md`](docs/DATA_LAYER.md),
[`docs/LIVE_ARCHITECTURE_RUNBOOK.md`](docs/LIVE_ARCHITECTURE_RUNBOOK.md).

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/books` | Full catalog (`{data, source, count}`) | None |
| GET | `/api/books/search?q=` | Catalog text search | None |
| GET | `/api/books/web-search?q=&limit=` | Live web search (Open Library + Google Books) | None |
| GET | `/api/books/recommend` | Recommendations (`prefs`, `genres`, `q`, `similar_to`, `limit`, `exclude`) | None |
| GET | `/api/books/trending?limit=` | Trending from the web (TTL-cached) | None |
| GET | `/api/books/resolve?isbn=\|key=` | Resolve a book by ISBN / OL key | None |
| GET | `/api/books/insights?isbn=\|id=` | Real book facts + genre expectation | None |
| GET | `/api/books/:id` | Single catalog book | None |
| GET | `/api/books/:id/similar` | "More like this" (TF-IDF cosine) | None |
| GET | `/api/news`, `/api/news/*` | Latest book news (publisher RSS, merged newest-first) | None |
| POST | `/api/ai/chat` | Conversational companion (see below) | None |
| POST | `/api/ai/insight` | Reading reflection from real stats | None |
| GET | `/api/analytics/dashboard` | Performance-panel contract | None |
| GET | `/api/analytics/reading` | Catalog-derived reading metrics | None |
| POST | `/api/reading` | Mirror a reading event (`stored:false` while Supabase is unset) | None |
| GET | `/api/reading` | **405 by design** — reading data is write-only | — |
| GET | `/api/accounts` | Accounts health: `{database:"d1", count}` | None |
| POST | `/api/accounts` | Create → `201` + one-time `accountKey`; existing email without a key → **`409 {error:"email_taken"}`** | None |
| GET | `/api/accounts/:email` | **Owner-only** profile (never the key/hash); unknown account → `401` like a wrong key | `X-Account-Key` |
| PATCH | `/api/accounts/:email` | Update profile | `X-Account-Key` |
| DELETE | `/api/accounts/:email` | Delete account | `X-Account-Key` |
| * | `/api/*` (anything else) | JSON `404 {error:"not_found"}` | — |

Account payload (camelCase; snake_case also accepted):

```jsonc
{
  "email": "reader@example.com",
  "name": "Ada",
  "favoriteGenres": ["Science Fiction"],
  "preferredMoods": ["cozy"],
  "readingGoal": 24,
  "readingLevel": "novice"   // novice | intermediate | expert
}
```

Account status codes: `201` created · `200` updated · `400 invalid_email` /
`invalid_name` / `invalid` · `401 missing_key` / `invalid_key` (also returned for an
unknown account, so existence is not observable) · `409 email_taken` ·
`429 rate_limited` (+ `Retry-After`) · `405 method_not_allowed` (+ `Allow`) ·
`503 database_not_configured`.

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

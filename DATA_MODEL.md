# Data Model

Two data worlds exist: the **live** edge product (D1 + browser state) and the
**legacy** Python stack (PostgreSQL/Redis, not deployed).

## Live: Cloudflare D1 (`goodbooks-accounts`)

Schema: [`d1/schema.sql`](d1/schema.sql) · Contract: [`docs/ACCOUNTS.md`](docs/ACCOUNTS.md)

### `accounts` (one row per email)

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | UUID v4, generated server-side |
| `email` | TEXT NOT NULL, `COLLATE NOCASE`, UNIQUE | normalised to lowercase; `accounts_email_uidx` |
| `name` | TEXT NOT NULL | trimmed, max 80 chars |
| `favorite_genres` | TEXT NOT NULL DEFAULT `'[]'` | **JSON array** (max 24 items) |
| `preferred_moods` | TEXT NOT NULL DEFAULT `'[]'` | **JSON array** (drives pace/personalisation) |
| `reading_goal` | INTEGER NOT NULL DEFAULT 24 | clamped 1–1000 |
| `reading_level` | TEXT NOT NULL DEFAULT `'novice'` | `novice \| intermediate \| expert` |
| `account_key_hash` | TEXT NOT NULL | SHA-256 of the 256-bit client key — **never leaves the server** |
| `created_at`, `updated_at` | TEXT NOT NULL | ISO-8601 timestamps |

### `account_events` (audit)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `account_id` | TEXT | the account's id (retained after delete) |
| `email` | TEXT | |
| `action` | TEXT | `created \| updated \| deleted` |
| `created_at` | TEXT | ISO-8601 |

### Wire shape — `PublicAccount`

```jsonc
{
  "id": "uuid", "email": "reader@example.com", "name": "Ada",
  "favoriteGenres": ["Science Fiction"], "preferredMoods": ["cozy"],
  "readingGoal": 24, "readingLevel": "novice",
  "createdAt": "2026-11-17T…", "updatedAt": "2026-11-17T…"
}
```

`accountKey` is returned **once** (201 create). The hash is never exposed.

## Live: browser state (`localStorage` / `sessionStorage`)

| Key | Shape | Purpose |
|---|---|---|
| `goodbooks_user` | `{ profile, preferences, goals, readingHistory, favorites, isAuthenticated, hasCompletedOnboarding }` | Source of truth for reader state; offline copy of the account profile |
| `goodbooks_account_key` | `{ "<email>": "<64-hex key>" }` | Device write credential (sign-out/delete removes it) |
| `goodbooks_sync_marker` | `{ email, ts }` | 5-minute sync debounce (bypassed by `force`) |
| `goodbooks_onboarded` (session) | `"1"` | Shows the gate once per session in storage-restricted browsers |
| `dashboard_state` | theme/layout/performance | UI preferences |

### `Book` (catalog + API)

`id`, `title`, `authors`, `cover_url`, `rating`, `ratingsCount`, `genres[]`,
`moods[]`, `published_year`, `page_count`, `description` — source:
`src/data/bookCatalog.ts` → `shared/book-catalog.json`.

## Legacy: Python stack (not deployed)

| Model | Fields (key) | Notes |
|---|---|---|
| `auth.security.User` | `id`, `email`, `role`, `hashed_password` | PostgreSQL via SQLAlchemy |
| `auth.security.TokenData` | `sub`, `exp`, `scope` | JWT payload |
| `api.main.RecommendationRequest` | `user_id`, `book_title`, `n_recommendations` | Legacy request body |
| `api.main.BookRecommendation` | `title`, `author`, `score`, `explanation` | Legacy response item |
| `analytics.real_time_analytics.RealTimeMetrics` | `experiment_id`, `metric_name`, `value` | A/B metrics |
| `news.api.*` | feed/expansion requests | News engine |
| Cache entries | various | Redis with TTL |

Optional Supabase Postgres schema (catalog only, currently unconfigured):
[`supabase/migrations/`](supabase/migrations) — apply in filename order.

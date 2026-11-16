# 📡 GoodBooks — Real-Time Data & AI Layer

How the live app serves real data, real-time recommendations, and an AI chat
assistant — all from the edge, with no heavy backend to maintain.

## Architecture

```
Browser (React SPA on Cloudflare Pages)
   │  fetch /api/*            (relative — same origin, CSP-safe)
   ▼
Cloudflare Pages Functions  ─── edge compute, ~µs
   ├── /api/books/*           catalog + recommendations + search + similar
   ├── /api/ai/chat           conversational assistant
   ├── /api/reading           durable reading events (write-only)
   └── /api/* (catch-all)     clean 404 for unknown endpoints
         │
         ├── reads live Supabase Postgres (service-role key, server-side)
         └── falls back to the embedded curated catalog when unconfigured
```

**Why serverless functions instead of a separate backend host?**
- Already deployed on Cloudflare Pages — no new infra, no ops.
- Real-time: every request computes fresh results at the edge (no stale caches).
- Cost: $0 for this workload; scales automatically.
- The existing FastAPI backend (`src/api/`) is documented in
  `docs/DEPLOYMENT_PLAN.md` for a future dedicated host if/when full
  collaborative filtering + training is needed.

## The Recommendation Model (why this, and not something bigger)

Goal: great picks for a curated catalog of ~24 books, personalized per reader,
explainable, real-time, cheap.

| Approach                 | Verdict for this workflow                                    |
| ------------------------ | ------------------------------------------------------------ |
| Collaborative filtering (SVD, matrix factorization) | ❌ No user×book interaction data at scale yet — nothing to learn from. Revisit after ~10k events (see `recommendations_log`). |
| LLM ranking              | ❌ Overkill — ranking a few dozen items with an LLM is slow + costs per request. |
| Embedding models (sentence-transformers) | ⚠️ Only worth it at ~1000+ books. Adds an API dependency for marginal gain on 24 items. |
| **TF-IDF + cosine similarity + profile scoring (chosen)** | ✅ Runs in µs, $0, fully explainable, works cold-start. |

**Implemented model** (`functions/api/_lib/recommender.ts`):
1. **TF-IDF vectors** over weighted text (genres ×5, moods ×3, title ×4,
   authors ×2, description ×1) → cosine similarity for "more like X" and
   free-text queries.
2. **Profile scoring** — exact port of the client engine:
   genre 45% / mood 20% / rating 15% / popularity 10% / recency 10%.
3. **MMR diversity** — re-ranks personalized picks so the top list isn't
   repetitive (λ = 0.3 similarity penalty).
4. **LLM layer (optional, env-gated)** — only for conversational chat
   (`MINIMAX_API_KEY`/`OPENAI_API_KEY` + `AI_BASE_URL` + `AI_MODEL`). Never
   for ranking.

## API Reference

### `GET /api/books`
Full catalog. `{ data: Book[], source: "database" | "catalog", count }`

### `GET /api/books/recommend`
Personalized recommendations. Returns a bare JSON array of books with
`ai_recommendation_score` (0–1 — the frontend renders `×100%`) and
`ai_explanation`.

| Param       | Meaning                                        |
| ----------- | ---------------------------------------------- |
| `prefs`     | JSON `{ favoriteGenres[], readingGoal }`       |
| `genres`    | comma list (used when `prefs` absent)          |
| `q`         | free-text query ("something cozy like ...")    |
| `similar_to`| book id → "more like this"                     |
| `limit`     | result count (default 6)                       |
| `exclude`   | comma list of ids to skip                      |

### `GET /api/books/search?q=...`
Text search across title/authors/genres/description.

### `GET /api/books/:id` and `GET /api/books/:id/similar`

### `POST /api/ai/chat`
`{ message, prefs? }` → `{ reply, bookSuggestions[], model }`

### `POST /api/reading`
Mirrors the reader's local reading activity into Postgres. Write-only by design
(no public read path).

```jsonc
// request
{
  "client_id": "9f1c…-uuid-v4",        // anonymous device id from localStorage
  "event_type": "progress",            // started | progress | finished | wishlisted
  "book_id": "b-11",
  "pages": 42,                         // session delta
  "page": 214,                         // absolute position (check-in)
  "progress": 31,                      // 0..100
  "session_date": "2026-11-17"         // reader's LOCAL day
}
// response
{ "stored": true }                                  // DB configured
{ "stored": false, "reason": "not_configured" }     // graceful no-op
{ "stored": false, "reason": "invalid" }            // 400 — bad body
```

- Called by `src/stores/reading/readingSync.ts` (middleware) — never blocks a
  reducer, never throws, and is skipped entirely when `VITE_SUPABASE_URL` is unset.
- `GET /api/reading` returns **405** on purpose: restoring data to a new device must
  be an explicit, opt-in flow, never an automatic read.

## Real-Time Data (Supabase)

The API reads live rows from Supabase Postgres when configured; otherwise it
serves the embedded curated catalog (same shape, always works).

**Activate the database (one-time, ~5 minutes):**
1. Create a free project at [supabase.com](https://supabase.com).
2. SQL Editor → paste `docs/supabase/schema.sql` → Run (creates tables + RLS +
   seeds the 24-book catalog).
3. Set these env vars on the Cloudflare Pages project
   (Settings → Environment variables → Production):
   - `SUPABASE_URL` = `https://<project-ref>.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY` = Settings → API → service_role (server-only)
   - `VITE_SUPABASE_URL` = same URL
   - `VITE_SUPABASE_ANON_KEY` = Settings → API → anon (public, browser-safe)
4. Redeploy. `/api/books` now reports `source: "database"`.

Optional AI chat upgrade (adds an LLM to the chat assistant — any
OpenAI-compatible provider):
- `MINIMAX_API_KEY` = MiniMax subscription key — set as a Cloudflare **secret**
  (live provider; auto-selects MiniMax base URL + `MiniMax-M2` model)
- `OPENAI_API_KEY` = OpenAI key (`sk-...`), or any other provider key
- `AI_BASE_URL` = provider base URL, e.g. `https://api.minimax.io/v1` (MiniMax)
- `AI_MODEL` = e.g. `MiniMax-M2` (default) or `gpt-4o-mini`
- `AI_PROVIDER` = optional, for custom providers

**Data tables** (see `docs/supabase/schema.sql`): `books`, `profiles`,
`user_preferences`, `reading_activity` (real-time feed), `reading_events`
(write-only mirror of the reader's real sessions — drives `books finished`),
`recommendations_log` (audit + evaluation data for the next recommender).

## Keeping the catalog in sync

- Single source of truth: `src/data/bookCatalog.ts` (frontend) and
  `shared/book-catalog.json` (server). Regenerate the JSON after editing the
  catalog:
  ```bash
  node scripts/export-catalog.cjs   # -> shared/book-catalog.json
  node scripts/seed-supabase.cjs    # -> upserts into Supabase (needs env vars)
  ```
- Frontend builds use `src/data/bookCatalog.ts`; Pages Functions bundle
  `shared/book-catalog.json`.

## Real book covers (Open Library)

Every catalog book has a real `cover_url` (baked into the catalog + shared
JSON). Source: **Open Library** (`https://covers.openlibrary.org/b/id/{id}-M.jpg`)
— free, no API key, real cover scans. (Google Books API was evaluated but its
anonymous daily quota is frequently exhausted → 429.)

- Regenerate/fetch: `node scripts/fetch-covers.cjs` → writes
  `scripts/.covers.json` (gitignored) for review → bake into the catalog.
- `BookCover` lazy-loads the real image and fades it in over the generated art;
  on error it keeps the generated cover (never a broken image).
- Supabase seed includes the covers; the DB row `cover_url` is the source of
  truth once `/api/books` reports `source: database`.

## Asset-cache guard

`_headers` marks `/assets/*` as `immutable`. The Pages Function
`functions/assets/[[route]].ts` prevents the SPA fallback from serving
`index.html` (200 text/html) for a missing hashed asset — which browsers would
otherwise cache for a year (breaking the app with a MIME error). Real assets
pass through untouched; missing assets return a non-cacheable 404.

## Local dev

```bash
npm run dev            # Vite on :3000 (proxies /api to :8000)
npx wrangler pages dev dist   # serves the built site + functions locally
```

## Verified live (2026-08-06)

- **Custom domain**: `https://books.dalecabra.com` — ACTIVE, HTTPS 200, security
  headers served (X-Frame-Options DENY, nosniff, referrer-policy,
  permissions-policy), SPA deep links work, API + chat live.
  (DNS: CNAME `books` → `goodbooks-recommender.pages.dev`, proxied.)
- `GET /api/books` → 24 books, `source: catalog`
- Sci-fi reader → The Martian 93%, Project Hail Mary 90%, Dune 82%
- `q=cozy and uplifting` → The House in the Cerulean Sea, Beach Read
- `similar_to=b-11` (Dune) → The Martian, Circe, A Psalm for the Wild-Built
- `POST /api/ai/chat` → hybrid engine reply + 5 real book cards
- Frontend Discover + AI Assistant consume the live API (scores render as %)

## Remaining step: apply the schema

The live API reports `source: catalog` until the Supabase schema is applied.
Env vars are already set on the Pages project (SUPABASE_URL, SUPABASE_ANON_KEY,
VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, AI_*). Apply `docs/supabase/schema.sql`
in the Supabase SQL editor (project `rqorywqrimcsgekmsxmj`) — or enable the
Supabase GitHub integration so `supabase/migrations/` applies on push. Once the
`books` table exists, `/api/books` reports `source: database` automatically.

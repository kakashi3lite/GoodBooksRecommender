# GoodBooks — Project Brief

## Purpose
A reading companion that recommends books a reader will actually finish, explains
why, and tracks the reading life. React/TypeScript SPA served from Cloudflare
Pages, with a serverless edge API and a durable account store.

**Live:** <https://books.dalecabra.com>

## Domain
- Personalized book recommendations (content-based TF-IDF + profile scoring + MMR)
- Live catalog search across Open Library / Google Books
- Reading shelf, streaks, goals, notes, analytics
- Book news aggregation from publisher RSS feeds
- Accounts that survive a browser wipe (Cloudflare D1)

## Key flows (what actually runs)
1. A visitor completes a 3-step onboarding (or skips as a guest).
2. The browser stores the profile locally and mirrors it to `/api/accounts` → **D1**.
3. Discover/search/recommendations call Pages Functions; the embedded catalog is the
   single source of book metadata.
4. Reading progress, wishlist and notes accumulate in Redux + `localStorage`.
5. The AI companion answers with real book cards, grounded in the reader's own data.

## Public interfaces
- **Web UI**: SPA at `/` (React 18 + Vite), routes: dashboard, discover, reading,
  wishlist, book detail, news, notes, community, analytics
- **API**: Cloudflare Pages Functions under `/api/*` — see
  [`API_CATALOG.md`](API_CATALOG.md) and [`docs/ACCOUNTS.md`](docs/ACCOUNTS.md)
- **Data**: D1 `goodbooks-accounts` (accounts + audit) — [`d1/schema.sql`](d1/schema.sql)

## Environments
- **Local**: `npm run dev` (Vite :3000). Pages Functions run under
  `npx wrangler pages dev dist` when you need the real API locally.
- **Production**: Cloudflare Pages (`goodbooks-recommender`), deployed by
  `npm run deploy` or the GitHub Actions workflow. No container, no cluster.
- **Legacy (not deployed)**: FastAPI + Redis + PostgreSQL + Docker/Kubernetes +
  Terraform — see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Ground truth
[`HANDOFF.md`](HANDOFF.md) · [`AGENTS.md`](AGENTS.md) ·
[`docs/LIVE_ARCHITECTURE_RUNBOOK.md`](docs/LIVE_ARCHITECTURE_RUNBOOK.md) ·
[`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)

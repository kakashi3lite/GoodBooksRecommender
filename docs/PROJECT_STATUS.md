# 📊 GoodBooks Recommender — Project Status (Single Source of Truth)

> **Verified as of**: 2026-08-07 (commit `925b659`, branch `main`)
> **Production**: https://books.dalecabra.com — React 18/Vite SPA + **Cloudflare Pages
> Functions** (`functions/api/**`) as the live backend. The Python FastAPI service in
> `src/api` is **legacy and NOT deployed**. Full operational detail:
> `docs/LIVE_ARCHITECTURE_RUNBOOK.md` (canonical runbook).

---

## Overall Health (production = Cloudflare Pages Functions)

| Dimension | Grade | Notes |
|---|---|---|
| Frontend UI & state | 🟢 **Good** | All routes render, Redux + localStorage, dark/light themes, mobile nav, 71 vitest tests |
| Frontend ↔ Backend | 🟢 **Live** | All `/api/*` served by Pages Functions; live sweep **27/27** (runbook §18) |
| AI chat + reading insight | 🟢 **Live** | Context-aware chat + "AI Reading Insight" on Analytics, personalized from the reader's **real** data (runbook §19) |
| Data layer | 🟡 **Partial** | Supabase env vars configured; **schema not applied** → catalog fallback (`source: "catalog"`) |
| Security | 🟢 **Good** | Security headers (frame/nosniff/referrer/permissions), CSP, secrets only via Cloudflare |
| Reproducibility | 🟢 **Good** | npm + wrangler; documented deploy; `.env.example` + `wrangler.toml` |
| Deployment | 🟢 **Live** | Production branch auto-deploys; `npx wrangler pages deploy dist` |
| Documentation | 🟢 **Current** | `docs/LIVE_ARCHITECTURE_RUNBOOK.md` (19 sections) + this file are canonical |

---

## What Works (verified live, 2026-08-07)

### Frontend
- Vite dev/build; strict TS (`tsc --noEmit` clean); ESLint 0 errors
- Routes: Dashboard, Discover, Currently Reading, Wishlist, Analytics, Community, News, Notes
- Redux slices with localStorage persistence; reading log is the single source of reader data
- **AI chat companion** (Cmd+K) with context-aware replies + real book cards; graceful offline fallback from the real catalog
- **AI Reading Insight** card on `/analytics` (Reflect / Regenerate)
- Responsive 390/834/1280 verified; dark/light themes; no model names in UI

### Backend — Cloudflare Pages Functions (`functions/api/**`)
- `books/[[route]].ts` — catalog, search, recommend (TF-IDF + profile + MMR), trending, web-search,
  resolve, insights, `/:id`, `/:id/similar` (real Open Library / Google Books data)
- `ai/[[route]].ts` — `POST /api/ai/chat` (context-aware LLM + hybrid fallback), `POST /api/ai/insight`
  (reflection + honest template fallback); GET → 405, empty msg/bad JSON → 400
- `news/[[route]].ts` — real Google News RSS (no fabricated fallback)
- `analytics/[[route]].ts` — honest numbers (no fake trends; empty `trends` is intentional)
- `assets/[[route]].ts` — non-cacheable 404 guard; catch-all → JSON 404
- Live endpoint sweep: **27/27 PASS** (runbook §18) + AI surface audit (runbook §19)

### Tests
- **71/71 vitest** (16 files), `tsc --noEmit` clean, `npm run build` succeeds
- Live API checks via `/tmp/llm_audit.sh` and `/tmp/backend_sweep.py` (both pass)

---

## Open Items (priority order)

1. **Apply Supabase schema** — run `docs/supabase/schema.sql` in the Supabase SQL editor, then
   `/api/books` reports `source: "database"` instead of the catalog. No code change needed.
2. **LLM provider key (optional)** — the AI features already degrade to honest fallbacks when the
   key is missing/rate-limited. To enable the full AI: set the provider secret on the Pages project
   (`npx wrangler pages secret put …`) — see runbook §19 env contract.
3. **CI gates for functions** — add a workflow step that runs `find -delete` for Apple Double files
   (`._*`) before deploy (they break the Functions bundle on macOS); see runbook §18 pitfall.
4. **Archive legacy root reports** — the ~35 root `*COMPLETE*`/`MISSION*`/`*REPORT*` files are
   historical; move to `docs/archive/` (don't delete).

---

## Legacy Python backend (`src/api`, `src/models` — NOT deployed)

Preserved for the ML/vector-store code; not wired to production. Known issues (from the previous
phase, commit `d1ee337` era) remain open in that code path: duplicate `FastAPI` app in
`src/api/main.py`, missing REST layer, `BookRecommendation` Pydantic field mismatch, `fakenews`
router unmounted, no Alembic migrations, model trains on boot, loose pins in `requirements.txt`.
None of these affect the live product.

---

## Documentation Truth Table

| Document | Accurate? | Action |
|---|---|---|
| `docs/LIVE_ARCHITECTURE_RUNBOOK.md` | ✅ **canonical** | Keep current (§18 backend audit, §19 AI v2) |
| `docs/PROJECT_STATUS.md` (this) | ✅ canonical | Keep current |
| `CHANGELOG.md` | 🟡 real history | Continue appending (needs an entry for the AI v2 release) |
| `API_CATALOG.md` | 🟡 partial | Verify/refresh against `functions/api/**` |
| `PROJECT_STATUS.md` (root) | 🔴 aspirational | Superseded by this file |
| `TEST_MATRIX.md` | 🟡 legacy | Reflects old Python-era numbers; frontend suite is 71 tests |
| ~35 × `*COMPLETE*` / `MISSION*` / `*REPORT*` | 🔴 historical | Move to `docs/archive/` |

---

## Next Milestones

1. Apply Supabase schema → real `source: "database"` + server-side analytics.
2. CI: add `._*` cleanup + function smoke tests to `.github/workflows/cloudflare-pages.yml`.
3. E2E (frontend) for chat + insight flows.
4. Archive legacy root reports; refresh `API_CATALOG.md`.
5. Product: news digest, community feeds, semantic discovery (all can reuse the AI layer).

**Full detail**: `docs/LIVE_ARCHITECTURE_RUNBOOK.md`


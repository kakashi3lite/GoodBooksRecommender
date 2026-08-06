# 📊 GoodBooks Recommender — Project Status (Single Source of Truth)

> **Verified as of**: 2026-08-06 (commit `d1ee337`, branch `main`)
> **Purpose**: One honest status document. The many root-level `*COMPLETE*`/`MISSION*`/`*REPORT*`
> files claim production readiness that the code does not support — treat this file as canonical.

---

## Overall Health

| Dimension | Grade | Notes |
|---|---|---|
| Frontend UI & state | 🟢 **Good** | All 8 routes render, Redux wired, Tailwind live, 19 tests passing |
| Frontend ↔ Backend connectivity | 🔴 **Broken** | Backend serves **zero** endpoints the frontend calls |
| Backend code breadth | 🟡 **Extensive, unproven** | Auth/RBAC/cache/vector store/AB-testing exist but aren't wired end-to-end |
| Data layer | 🔴 **Missing** | No Alembic migrations, no DB-backed user store, no real dataset loaded |
| Reproducibility | 🔴 **Poor** | No Python lockfile, loose pins, hardcoded secrets in compose |
| Deployment | 🔴 **Not deployable** | `docker-compose up` ships an API that 404s the frontend's contract |
| Documentation | 🟡 **Mostly stale** | ~35 aspirational reports; `HANDOFF.md` + this file are the new source of truth |

---

## What Works (verified)

### Frontend
- Vite dev/build pipelines; Tailwind + PostCSS configured; strict TS (`tsc --noEmit` clean)
- 8 routes: `/`, `/dashboard`, `/discover`, `/reading`, `/wishlist`, `/news`, `/notes`,
  `/community`, `/analytics`
- Redux (7 slices) with localStorage persistence; typed hooks
- **AI Assistant** chat with local fallback (book suggestion cards); Cmd+K toggle
- Graceful fallback everywhere — the UI never breaks without a backend
- Vitest: **19 tests / 5 files** passing (aiSlice, userSlice, notesSlice, AIAssistant,
  NavigationSidebar)
- ESLint 0 errors; production build succeeds with manual chunking

### Backend (module-level)
- FastAPI app with JWT/OAuth2, RBAC, rate limiting, security middleware, CSP
- `HybridRecommender` (TF-IDF content + SVD collaborative, 0.5/0.5), FAISS `BookVectorStore`,
  SHAP explainer, RAG explanation service
- Redis cache (`AsyncCacheManager`, in-memory fallback), session store, privacy/GDPR service
- Prometheus `/metrics`, enhanced multi-component `/health`

---

## What's Broken / Blocking (in priority order)

| # | Issue | File | Impact |
|---|---|---|---|
| 1 | **Duplicate `app = FastAPI(...)`** — second assignment discards the first; news routers die | `src/api/main.py` (~L308 vs ~L571) | `/api/news/*` 404s at runtime |
| 2 | **Missing REST layer** — `/api/books/*`, `/api/ai/*`, `/api/user/*`, `/api/notes/*`, `/api/community/*`, `/api/analytics/*` don't exist | `src/api/` | Every frontend API call fails |
| 3 | **`BookRecommendation(score=...)` vs `hybrid_score`** → Pydantic 500 | `src/api/main.py` | `/recommendations` unusable |
| 4 | Auth mismatch — product endpoint requires JWT, frontend sends none | `src/api/main.py` | No anonymous read path |
| 5 | `fakenews` router never mounted; `/api/v2/*` mounted only via unused `EnhancedFeaturesManager` | `src/api/` | Features invisible |
| 6 | No Alembic migrations; no DB user layer | repo-wide | Auth/persistence not real |
| 7 | Model trains on boot (torch/FAISS) | `src/models/` | Minutes-long startup |
| 8 | No Python lockfile; loose `>=` pins; Pydantic v1/v2 conflict | `requirements.txt` | Non-reproducible |

---

## Feature-by-Feature

| Feature | Frontend | Backend | Wired End-to-End? |
|---|---|---|---|
| Hybrid recommendations | ✅ UI + slice thunks | ⚠️ logic exists, wrong endpoint/contract | 🔴 No |
| Semantic/vector search | — | ⚠️ `BookVectorStore` exists, no endpoint | 🔴 No |
| AI chat assistant | ✅ works w/ fallback | 🔴 no `/api/ai/*` | 🔴 No |
| News dashboard | ✅ demo fallback | ⚠️ routers exist but dead (bug #1) | 🔴 No |
| False-news detection | — | ⚠️ ~85% code, router unmounted | 🔴 No |
| Reading notes | 🚧 placeholder | 🔴 no routes | 🔴 No |
| Community hub | 🚧 placeholder | 🔴 no routes | 🔴 No |
| Analytics dashboard | 🚧 placeholder (charts exist) | 🔴 no `/api/analytics/*` | 🔴 No |
| Theme / brightness / virtualization | ✅ implemented | n/a | ✅ |
| Reading goals / wishlist | ✅ new routes | 🔴 no `/api/user/*` | 🔴 No |

---

## Test Coverage (actual)

- **Frontend**: 19 tests (slices + components). No E2E.
- **Backend**: no verified passing suite (pytest configured, `requirements-dev.txt` missing).
- The legacy `TEST_MATRIX.md` (~60% FE / ~70% BE / 0% E2E) is directionally honest.

---

## Documentation Truth Table

| Document | Accurate? | Action |
|---|---|---|
| `HANDOFF.md` (new) | ✅ canonical | Keep current |
| `docs/PROJECT_STATUS.md` (this) | ✅ canonical | Keep current |
| `docs/DEPLOYMENT_PLAN.md` (new) | ✅ canonical | Keep current |
| `TEST_MATRIX.md` | 🟡 mostly | Update after backend tests land |
| `CHANGELOG.md` | 🟡 real history | Continue appending |
| `docs/API_REFERENCE.md` | 🔴 stale | Rewrite after Phase 1 (or mark deprecated) |
| `API_CATALOG.md` | 🔴 inaccurate | Rewrite or archive |
| `PROJECT_STATUS.md` (root) | 🔴 aspirational | Superseded by this file |
| ~35 × `*COMPLETE*` / `MISSION*` / `*REPORT*` | 🔴 aspirational/duplicative | Move to `docs/archive/` (do not delete — history) |

---

## Next Milestones

1. **M1 (half day)** — Phase 0: fix double-app bug, `BookRecommendation` field, mount routers →
   `/api/news/*` + `/health` verified live.
2. **M2 (1–2 wks)** — Phase 1: `/api/books/*` + `/api/ai/*` + `/api/user/*` + `/api/analytics/*`
   matching `src/utils/api.ts`; frontend shows real data with backend up.
3. **M3 (1–2 wks)** — Phase 2: Alembic, DB-backed auth, model serialization, Python lockfile,
   secrets cleanup.
4. **M4 (1 wk)** — Phase 3: `docker-compose.prod.yml` + nginx + smoke tests; staging deploy.
5. **M5 (later)** — Phase 4: CI gates, E2E, K8s manifests, product features (semantic discovery,
   wrapped, clubs).

**Full detail**: `docs/DEPLOYMENT_PLAN.md`

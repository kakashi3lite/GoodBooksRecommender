# 🗺️ Code Map

> Verified 2026-11-17. ✅ = runs in production · 🟡 = optional · 🏛️ = legacy, not deployed.

```text
.
├── functions/                      ✅ Cloudflare Pages Functions — the live backend
│   ├── api/
│   │   ├── [[route]].ts            JSON 404 for unknown /api/*
│   │   ├── accounts/[[route]].ts   ✅ customer accounts CRUD on D1 (see docs/ACCOUNTS.md)
│   │   ├── books/[[route]].ts      ✅ catalog, search, web-search, recommend, similar, trending, resolve
│   │   ├── ai/[[route]].ts         ✅ /api/ai/chat + /api/ai/insight (env-gated LLM)
│   │   ├── reading/[[route]].ts    ✅ write-only reading events (Supabase; no-op while unset)
│   │   ├── analytics/[[route]].ts  ✅ dashboard + reading metrics
│   │   ├── news/[[route]].ts       ✅ publisher RSS aggregation
│   │   └── _lib/                   shared edge code: recommender, catalog, db, rss, ai, types
│   └── assets/[[route]].ts         ✅ non-cacheable 404 guard for missing hashed assets
│
├── d1/
│   └── schema.sql                  ✅ D1 schema: accounts + account_events (idempotent)
│
├── src/                            ✅ React 18 + TypeScript + Vite SPA
│   ├── App.tsx                     routes + onboarding gate + mount-time account sync
│   ├── main.tsx                    entrypoint
│   ├── components/                 UI: Dashboard, Features, Navigation, Onboarding, AI, News, UI
│   ├── lib/
│   │   ├── accountApi.ts           ✅ /api/accounts client, account-key storage, email rule
│   │   ├── userRepository.ts       ✅ compatibility layer (sync/fetch/update/delete account)
│   │   ├── readingRepository.ts    reading-session persistence helpers
│   │   └── supabaseClient.ts       🟡 legacy browser Supabase client (not used by accounts)
│   ├── stores/                     Redux Toolkit slices: user, books, dashboard, reading, ai, features
│   ├── hooks/                      useAppDispatch/useAppSelector, useFocusTrap, …
│   ├── data/bookCatalog.ts         client-side catalog (single source for covers/metadata)
│   ├── utils/api.ts                typed API contract (API_ENDPOINTS, apiClient)
│   ├── styles/, dashboard/css/     design system (Tailwind + CSS variables, light/dark)
│   ├── api/, core/, models/, news/, fakenews/, newsletter/, middleware/, workers/
│   │                               🏛️ legacy FastAPI/ML stack — not deployed
│   └── services/, store/, auth/, analytics/, privacy/, user/, features/, types/
│                                   mixed: some live helpers, some legacy
│
├── shared/book-catalog.json        ✅ catalog bundled into the functions
├── public/                         ✅ _headers, _redirects, 404.json, og-cover.png
├── tests/                          ✅ Vitest (29 files / 183 tests)
│   ├── accountsApi.test.ts         accounts CRUD contract (fake D1)
│   ├── userRepository.test.ts      client → API integration
│   ├── userSync.test.ts            sync thunk rules (guest skip, force flag)
│   ├── settingsAccount.test.tsx    Settings persistence status + delete flow
│   ├── components/                 UI tests (Onboarding, focus trap, …)
│   ├── backend/, frontend/, news/  🏛️ legacy pytest/vitest suites
│   └── *.test.ts(x)                feature tests (recommender, news, reading, ui)
│
├── scripts/                        build/deploy/data helpers
│   ├── purge-apple-double.cjs      strips macOS ._* files before deploy
│   ├── check-docs-links.cjs        ✅ docs link checker (npm run docs:check)
│   ├── export-catalog.cjs          bookCatalog.ts → shared/book-catalog.json
│   ├── fetch-covers.cjs, seed-supabase.cjs, generate-og-image.cjs
│   └── *.py                        🏛️ legacy ops/ML scripts
│
├── docs/                           living documentation (index: DOCUMENTATION_INDEX.md)
│   ├── LIVE_ARCHITECTURE_RUNBOOK.md  operations + endpoint tables + verification logs
│   ├── ACCOUNTS.md                   accounts/D1 contract + upgrade context
│   ├── DATA_LAYER.md                 data flow + recommendation model rationale
│   ├── PROJECT_STATUS.md             honest status
│   ├── API_REFERENCE.md, API_CATALOG (root)
│   ├── supabase/                     optional Postgres schema + migrations
│   └── archive/                      historical reports (never cite as current)
│
├── supabase/                       🟡 Postgres migrations for the optional catalog DB
├── terraform/, nginx/, monitoring/, airflow/, config/, prompts/, mlruns/, data/
│                                   🏛️ legacy infrastructure / datasets / ML runs
│
├── wrangler.toml                   ✅ Pages config + D1 binding (DB → goodbooks-accounts)
├── package.json                    ✅ scripts: dev, build, deploy, test, db:*
├── tsconfig.json                   src/ + dashboard/ + scripts/ (functions are outside)
└── vite.config.ts, tailwind.config.js, eslint.config.js
```

## Entry points

| Entry point | File |
|---|---|
| Browser app | [`src/main.tsx`](src/main.tsx) |
| Routes + gate | [`src/App.tsx`](src/App.tsx) |
| Edge API (accounts) | [`functions/api/accounts/[[route]].ts`](functions/api/accounts/[[route]].ts) |
| Edge API (books) | [`functions/api/books/[[route]].ts`](functions/api/books/[[route]].ts) |
| Edge API (catch-all) | [`functions/api/[[route]].ts`](functions/api/[[route]].ts) |
| D1 schema | [`d1/schema.sql`](d1/schema.sql) |
| Deploy config | [`wrangler.toml`](wrangler.toml) |
| Agent rules | [`AGENTS.md`](AGENTS.md) |

## Not in the deploy path

`src/api/main.py` (FastAPI), `terraform/`, `docker-compose*.yml`, `Dockerfile`,
`nginx/`, `monitoring/`, `airflow/`, `mlruns/`, `data/`. They are retained for a
future dedicated ML host and are documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

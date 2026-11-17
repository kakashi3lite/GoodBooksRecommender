# 🤖 Agent Handbook — GoodBooks Recommender

Working instructions for AI agents and humans. **Read this before changing code.**
Everything here was verified against the live deployment on **2026-11-17**.

- **Live app**: <https://books.dalecabra.com> (Cloudflare Pages project `goodbooks-recommender`, branch `main`)
- **Live backend**: Cloudflare **Pages Functions** in `functions/api/**` — there is **no running Python server**
- **Durable data**: Cloudflare **D1** database `goodbooks-accounts` (binding `DB`)

---

## 1. Reality check — what is actually deployed

| Layer | Status | Where |
|---|---|---|
| Frontend | ✅ Live | React 18 + TypeScript + Vite → `src/`, entry `src/main.tsx` |
| API | ✅ Live | Pages Functions → `functions/api/**` |
| Customer accounts | ✅ Live | D1 `accounts` + `account_events` → `d1/schema.sql`, `docs/ACCOUNTS.md` |
| Reader state (wishlist, progress, notes) | ✅ Live (client) | Redux + `localStorage` |
| Book catalog | ✅ Live | Embedded catalog (`source: "catalog"`); Supabase Postgres is **optional and currently unconfigured** |
| AI chat / insight | ✅ Live | OpenAI-compatible provider via env (`MINIMAX_API_KEY` + `AI_BASE_URL` + `AI_MODEL`) |
| Python FastAPI (`src/api`, `src/core`, `src/models`, …) | 🟡 Legacy, **not deployed** | Kept for a future dedicated ML host; do not assume it serves the app |
| Terraform / Kubernetes / Docker stacks | 🟡 Legacy, not in the deploy path | `terraform/`, `docker-compose*.yml` |

If a document claims the FastAPI service serves the frontend, it is stale — see
[`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md).

---

## 2. Golden rules (violating these has broken production before)

1. **One source of truth for accounts.** Accounts live in D1, reached through
   `/api/accounts`. Do not reintroduce Supabase `profiles`, do not add a second
   account table, and do not write account rows from the browser.
2. **The account key is the only credential.** The server stores only its
   SHA-256 hash. Never log it, never put it in Redux, never return it twice.
3. **Email validation must match the server.** `isValidAccountEmail()`
   (`src/lib/accountApi.ts`) and `EMAIL_RE` (`functions/api/accounts/[[route]].ts`)
   must stay identical — a mismatch silently drops a customer's account.
4. **Guests are not accounts.** `reader@goodbooks.app` is reserved for
   "explore as guest" and must never be sent to the API.
5. **Offline-first is a hard requirement.** Every network call returns a typed
   `{ synced: false }` / `null` instead of throwing. The UI must work with no API.
6. **Secrets never enter the bundle.** `VITE_*` values are public. Anything
   sensitive stays a Pages secret (`SUPABASE_SERVICE_ROLE_KEY`, `MINIMAX_API_KEY`,
   `OPENAI_API_KEY`).
7. **A deploy is not done until `/api/accounts` answers `{"database":"d1", …}`
   and the smoke tests pass** (CI enforces this).
7b. **Account reads are owner-only.** `GET /api/accounts/:email` requires
   `X-Account-Key`; an unknown account must answer exactly like a wrong key
   (`401`), and a key-less `POST` for an existing email must answer `409` —
   never return a profile from a write path. Keep `tests/accountsApi.test.ts`
   green when changing any of this.
8. **Never render a full-screen overlay without an escape path** (the mobile
   "buttons do nothing" incident — see the runbook §3).
9. **Never PATCH the Pages project's `deployment_configs` to change env vars.**
   `secret_text` values are returned redacted (`""`); writing the object back
   **erases those secrets**. Add secrets only with
   `wrangler pages secret put NAME --project-name goodbooks-recommender`
   (value on stdin), and non-secrets in `wrangler.toml` `[vars]`.

---

## 3. Commands

```bash
# Install
npm ci

# Develop (Vite on :3000; /api is proxied by the Pages functions only in prod)
npm run dev

# Quality gates — all three must be green before a PR
npm run type-check      # tsc --noEmit (src/, dashboard/, scripts/)
npm test                # vitest, 29 files / 183 tests
npm run lint            # eslint src (0 errors required; warnings tolerated)

# Build + deploy to production
npm run build
npm run deploy          # build → purge Apple-Double files → wrangler pages deploy

# Database (Cloudflare D1)
npm run db:schema       # apply d1/schema.sql to the remote database (idempotent)
npm run db:inspect      # list accounts (email, name, goal, timestamps)

# Docs hygiene (run after moving/renaming any .md)
npm run docs:check

# Functions are not part of tsconfig — type-check them explicitly when edited
npx tsc --noEmit --strict --skipLibCheck --target ES2022 --module esnext \
  --moduleResolution bundler --lib es2022,dom "functions/api/accounts/[[route]].ts"
```

There is **no** pre-commit hook. `python -m pytest` only covers the legacy
backend and is not part of the deploy gate.

---

## 3b. Cloudflare environment (read before touching env vars)

| Variable | Where it lives | Notes |
|---|---|---|
| `SUPABASE_URL` | `wrangler.toml` → `[vars]` | Non-secret; shipped with every deploy |
| `SUPABASE_SERVICE_ROLE_KEY` | Pages secret | ⚠️ **currently empty — needs re-entry** (see below) |
| `MINIMAX_API_KEY` / `OPENAI_API_KEY` | Pages secret | ⚠️ **currently empty — AI chat runs the local hybrid engine** |
| `AI_BASE_URL` / `AI_MODEL` | Pages secret | Set (`https://api.minimax.io/v1`, `MiniMax-M2`) |
| `DB` (D1 binding) | `wrangler.toml` → `[[d1_databases]]` | `goodbooks-accounts` |
| `RATE_LIMIT_SALT` | Pages secret | Salt for hashed rate-limit keys (`rate_limits` table) |

Rules learned the hard way (2026-11-17):

1. **Plain vars must be in `wrangler.toml [vars]`.** A var added only in the
   dashboard did not reach the Functions runtime on `wrangler pages deploy`;
   declaring it in `[vars]` did.
2. **Secrets are write-only.** `wrangler pages secret list` proves a name exists,
   not that it has a value. Verify with a presence-only probe
   (`Boolean(env.NAME)`) returned by a deployed function.
3. **Env changes need a redeploy** and ~30–60 s of edge propagation; test the
   deployment URL (`https://<hash>.goodbooks-recommender.pages.dev`) rather than
   the custom domain, which lags.
4. **A binding name cannot exist twice** — a secret and a `[vars]` entry with the
   same name fail the deploy ("Binding name already in use").

Restore the two missing secrets (values never enter git):

```bash
printf '%s' '<SUPABASE_SERVICE_ROLE_KEY>' | npx wrangler pages secret put SUPABASE_SERVICE_ROLE_KEY --project-name goodbooks-recommender
printf '%s' '<MINIMAX_API_KEY>'            | npx wrangler pages secret put MINIMAX_API_KEY            --project-name goodbooks-recommender
npm run deploy   # or push to main
```

## 4. Repository map

| Path | What lives there | Deployed? |
|---|---|---|
| `src/` | React UI, Redux slices, `src/lib/accountApi.ts`, `src/utils/api.ts` | ✅ |
| `functions/api/**` | Edge API (books, accounts, ai, reading, analytics, news) | ✅ |
| `functions/api/_lib/` | Shared edge helpers (recommender, catalog, db, rss, ai, types) | ✅ |
| `d1/schema.sql` | D1 schema for customer accounts | ✅ (applied) |
| `shared/book-catalog.json` | Server-side catalog bundle | ✅ |
| `public/` | `_headers`, `_redirects`, static assets | ✅ |
| `tests/` | Vitest suite (`tests/backend`, `tests/frontend`, `tests/news` are legacy) | ✅ |
| `scripts/` | Build/deploy/seed/export helpers | partly |
| `src/api`, `src/core`, `src/models`, `src/news`, `src/fakenews` | Legacy FastAPI/ML stack | ❌ |
| `terraform/`, `docker-compose*.yml`, `Dockerfile` | Legacy infra | ❌ |
| `docs/` | Living documentation — start at `DOCUMENTATION_INDEX.md` | — |
| `docs/archive/` | Historical reports — never cite as current behaviour | — |

Full tree: [`CODEMAP.md`](CODEMAP.md). Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 5. Recipes

### Add or change an edge endpoint
1. Add the handler under `functions/api/<group>/[[route]].ts` (a `[[route]]`
   file catches `/api/<group>` **and** `/api/<group>/*`).
2. Export one handler per method **plus** `onRequest` — without `onRequest`,
   unsupported methods fall through to the `/api/*` catch-all and answer a
   misleading 404 instead of 405.
3. Return `Content-Type: application/json`, `Cache-Control: no-store` for
   private data, and `X-Content-Type-Options: nosniff`.
4. Add the endpoint to `docs/API_REFERENCE.md`, `API_CATALOG.md` and the
   runbook's endpoint table.
5. Add a test in `tests/` that exercises the handler with a fake binding.

### Change the accounts schema
1. Edit `d1/schema.sql` (idempotent) **and** the TypeScript row type in
   `functions/api/accounts/[[route]].ts`.
2. `npm run db:schema` (remote) — the file is safe to re-run.
3. Update `docs/ACCOUNTS.md` (schema table + wire shape) and `docs/DATA_LAYER.md`.
4. Bump the test fixtures in `tests/accountsApi.test.ts`.

### Add a persisted preference
1. Add the column to `d1/schema.sql` and the row/`PublicAccount` types.
2. Extend `AccountInput`, `buildFields` and the `insert`/`update` statements.
3. Map it in `src/lib/accountApi.ts` (`AccountInput`, `ServerAccount`).
4. Dispatch `syncAccountToServer({ force: true })` from the UI that mutates it.

### Ship a change
```bash
npm run type-check && npm test && npm run lint && npm run build
npm run deploy
# then verify (edge propagation can take ~1 min; retry until 200):
curl -s https://books.dalecabra.com/api/accounts
```

---

## 6. Testing expectations

- **New behaviour needs a test that fails without the change.** Prefer the
  existing files (`tests/accountsApi.test.ts`, `tests/userRepository.test.ts`,
  `tests/userSync.test.ts`, `tests/settingsAccount.test.tsx`).
- Pages Functions are tested by importing `onRequest*` directly with a fake
  `env.DB` (see `tests/accountsApi.test.ts`).
- Client code that touches the network is tested with `vi.stubGlobal('fetch', …)`.
- Do not chase coverage; cover the contract and the edge cases you touched.

---

## 7. Documentation map

| Need | Document |
|---|---|
| Start here (human) | [`HANDOFF.md`](HANDOFF.md) |
| Start here (agent) | this file |
| What's deployed / operations | [`docs/LIVE_ARCHITECTURE_RUNBOOK.md`](docs/LIVE_ARCHITECTURE_RUNBOOK.md) |
| Honest status | [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) |
| Accounts + D1 (with upgrade context) | [`docs/ACCOUNTS.md`](docs/ACCOUNTS.md) |
| Data layer overview | [`docs/DATA_LAYER.md`](docs/DATA_LAYER.md) |
| API surface | [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md), [`API_CATALOG.md`](API_CATALOG.md) |
| Every document | [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) |

**Doc rules:** update the doc in the same change as the code; never add a new
root-level `*_COMPLETE.md` report (use `CHANGELOG.md`); run `npm run docs:check`.

---

## 8. Known gaps / next upgrades

1. **Account restore on a new device** — impossible by design today: reads and
   writes both require the device's key, and there is no recovery flow. Needs an
   explicit restore (emailed one-time token or password/magic-link).
2. **Rate limiting** on `/api/accounts` — creation is open; add a WAF rule.
3. **Reading events** (`/api/reading`) still target Supabase and are a no-op
   while `SUPABASE_URL` is unset. Moving them to D1 is the next data milestone.
4. **Supabase catalog** — `SUPABASE_URL` is not configured, so `/api/books`
   serves the embedded catalog. Either configure it or delete the path.
5. **Sidebar layout** — the sidebar is a tall `fixed` column that scrolls with
   the page, so Sign Out sits at the page bottom on desktop.

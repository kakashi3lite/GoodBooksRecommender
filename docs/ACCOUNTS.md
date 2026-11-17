# 👤 Customer Accounts — Cloudflare D1

Accounts are **durable**. A reader who completes onboarding gets a row in the
Pages project's D1 database (`goodbooks-accounts`), so the account survives a
browser wipe, a different device, and every future deployment. `localStorage`
remains the instant/offline copy; D1 is the source of truth.

> Supabase `profiles` is **no longer used for accounts**. Its schema did not
> match the client payload (`id uuid → auth.users` vs. an email-keyed profile),
> its RLS policy had no insert path, and its signup endpoint was rate-limited.
> The Supabase REST layer is still used for the book catalog only.

---

## 1. Architecture

```
Browser (localStorage = offline copy)
   │  POST /api/accounts            ← relative, same origin (no CORS, no key in the bundle)
   ▼
Cloudflare Pages Function  functions/api/accounts/[[route]].ts
   │  env.DB  (D1 binding from wrangler.toml)
   ▼
D1 database goodbooks-accounts  →  accounts + account_events
```

---

## 2. HTTP API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/accounts` | — | Health probe: `{ database: "d1", count }` |
| `POST` | `/api/accounts` | optional `X-Account-Key` | Create (201, returns `accountKey` once) or update (200) |
| `GET` | `/api/accounts/:email` | — | Public profile (`?email=` also accepted) |
| `PATCH` | `/api/accounts/:email` | `X-Account-Key` | Update profile fields |
| `DELETE` | `/api/accounts/:email` | `X-Account-Key` | Delete the account |

Payload (camelCase; snake_case `favorite_genres`, `preferred_moods`,
`reading_goal`, `reading_level` are accepted too):

```jsonc
{
  "email": "reader@example.com",
  "name": "Ada",
  "favoriteGenres": ["Science Fiction"],
  "preferredMoods": ["cozy"],
  "readingGoal": 24,
  "readingLevel": "novice"        // novice | intermediate | expert
}
```

Status codes: `201` created · `200` exists/updated · `400 invalid_email` ·
`401 missing_key` / `invalid_key` · `404 not_found` · `503 database_not_configured`.

### Ownership without a password
Onboarding collects a name and an email only, so there is no password to check.
The server mints a **256-bit account key** at creation, returns it once, and
stores only its SHA-256 hash. The browser keeps the raw key in `localStorage`
(`goodbooks_account_key`) and sends it as `X-Account-Key` for every write.
There is deliberately **no "log in as any email"** endpoint — a device that
never held the key can read the public profile but cannot modify it.

### Verified live (2026-11-17, `books.dalecabra.com`)
```
POST   /api/accounts                 → 201 {created:true, accountKey:"<64 hex>"}
GET    /api/accounts/<encoded email> → 200 {account:{…}}
PATCH  /api/accounts/<email> + key   → 200 {account:{… updated …}}
PATCH  /api/accounts/<email> no key  → 401 {error:"missing_key"}
PATCH  /api/accounts/<email> bad key → 401 {error:"invalid_key"}
POST   /api/accounts (same email)    → 200 {created:false, exists:true}   (idempotent)
DELETE /api/accounts/<email> + key   → 200 {deleted:true}
GET    /api/accounts/<email>         → 404 {error:"not_found"}
```
Durability was proven by reading a row back from a *later* deployment with its
original `created_at`, and by querying D1 directly with
`wrangler d1 execute goodbooks-accounts --remote`.

### Verified end-to-end in a real browser (2026-11-17)

A headless Chromium run against `https://books.dalecabra.com` drove the actual
customer journey:

1. Fresh visitor → onboarding gate renders.
2. Complete the 3 steps with a real email → **exactly one** `POST /api/accounts`
   → `201`, key stored in `localStorage`.
3. Reload → the gate does **not** return; the dashboard greets the reader.
4. Settings → Account shows *"Saved to Cloudflare — survives clearing this
   browser."*
5. Delete my account (two taps) → `DELETE 200` → key removed → signed out →
   onboarding gate returns; the D1 row is gone.
6. Sign Out alone → key relinquished, gate returns, **the D1 row survives**
   (`GET /api/accounts/:email` → `200`) — signing out is not deletion.

Also verified in the same session: mobile viewport (390×844) skip-as-guest path,
hamburger drawer, all eight routes, live Discover search
(`/api/books/web-search?q=dune` → Dune), wishlist persistence across reload,
dark-mode toggle, and an AI-assistant reply from `/api/ai/chat` (200).

Index usage is confirmed, not assumed:

```bash
npx wrangler d1 execute goodbooks-accounts --remote \
  --command "explain query plan select * from accounts where email = 'x@y.co' collate nocase limit 1;"
# → SEARCH accounts USING INDEX accounts_email_uidx (email=?)
```

---

## 3. Schema

`d1/schema.sql` (idempotent) creates:

| Table | Purpose |
|---|---|
| `accounts` | one row per email (`unique` + `collate nocase`), profile fields, `account_key_hash`, timestamps |
| `account_events` | audit trail — `created` / `updated` / `deleted` |

Apply it:

```bash
npx wrangler d1 execute goodbooks-accounts --remote --file=d1/schema.sql   # production
npx wrangler d1 execute goodbooks-accounts --local  --file=d1/schema.sql   # wrangler pages dev
```

Inspect:

```bash
npx wrangler d1 execute goodbooks-accounts --remote \
  --command "select email, name, reading_goal, created_at from accounts;"
```

---

## 4. Client integration

| File | Responsibility |
|---|---|
| `src/lib/accountApi.ts` | `/api/accounts` client: create/sync, read, update, delete, key storage, 6 s timeout, never throws |
| `src/lib/userRepository.ts` | Compatibility layer (`syncUserAccount`, `fetchUserAccount`, `updateUserAccount`, `deleteUserAccount`) |
| `src/stores/user/userSlice.ts` | `syncAccountToServer` thunk — fires on app mount and on onboarding completion |

Behaviour guarantees:

- **Idempotent** — `syncAccountToServer` may run on every mount; the first call
  creates, later calls update the same row (5-minute local debounce).
- **Guest-safe** — the reserved guest identity `reader@goodbooks.app` is never
  sent to the server, so anonymous visitors cannot collide on one row.
- **Offline-first** — an unreachable API yields `{ synced: false }`; the app
  keeps working from `localStorage` and retries on the next mount.

---

## 5. Operations

- **Delete a reader's data**: call `DELETE /api/accounts/:email` with the
  reader's key, or `deleteUserAccount(email)` from the client.
- **Rotation**: deleting the row and re-creating it issues a fresh key; a client
  holding the old key receives `401 invalid_key` and drops it automatically.
- **Sign Out** relinquishes this device's key (shared-browser safety). The D1
  row stays intact and readable; a device without the key can read the public
  profile but cannot update it — Settings shows "Local only" in that state.
- **CI deploys** read the binding from `wrangler.toml`, so the
  `CLOUDFLARE_API_TOKEN` used by GitHub Actions needs **D1:Edit** in addition to
  Pages:Edit.
- **Abuse**: creation is open (no captcha) because onboarding has no password.
  Put a Cloudflare WAF rate-limiting rule on `/api/accounts` (e.g. 10 POST/min
  per IP) if the endpoint is ever targeted; the handler itself is O(1) per
  request and cannot be used to read another reader's key.
- **Recovery**: D1 Time Travel is enabled on this database —
  `npx wrangler d1 time-travel info goodbooks-accounts` shows the current
  bookmark, and `npx wrangler d1 time-travel restore goodbooks-accounts
  --bookmark=<bookmark>` rolls a bad write back.
- **Retention**: `account_events` is append-only audit data. Trim it with
  `delete from account_events where created_at < date('now','-180 day');` if it
  grows.
- **Not yet migrated**: reading events (`/api/reading`) still target Supabase
  and are a no-op while `SUPABASE_URL` is unset. Moving them into D1 is a
  separate change; the accounts table does not depend on it.

---

## 6. Context for the next upgrade 🧠

This section exists so the next engineer or agent does not have to rediscover
any of it. Everything below was established on **2026-11-17**.

### 6.1 Decisions and why

| Decision | Rationale | Alternative rejected because |
|---|---|---|
| Accounts live in **Cloudflare D1** | Already deployed on Pages; binding needs no credentials, no pool, no cold start; same colo as the request | **Supabase `profiles`**: the Pages project has `SUPABASE_SERVICE_ROLE_KEY` but **not** `SUPABASE_URL`, the service key is encrypted and unreadable, the table contract (`uuid` PK → `auth.users`, `display_name`) did not match the client payload, RLS had no insert path, and `auth.signUp` rate-limited |
| **Same-origin** `/api/accounts` | No CORS grant, no API key in the bundle, CSP stays `connect-src 'self'` | A separate API host would need CORS, a token strategy and another deploy target |
| Ownership proven by a **256-bit account key** | Onboarding has no password to verify; a key gives write authorisation without inventing credentials | Making the endpoint unauthenticated (anyone could edit any row); adding passwords (bigger UX + recovery scope) |
| Store only the **SHA-256 of the key** | A database dump cannot be replayed as a login | Storing the raw key (leaks on any dump/backup) |
| **Server-side** mirroring via a Redux thunk | One code path for create + update; the browser never needs the service role | Writing directly from the browser (would require an anon-write RLS policy) |
| `localStorage` stays the **instant copy** | Offline-first is a product guarantee; the app must never block on the network | Making the app wait for the API (breaks in-app browsers/private mode) |
| **Idempotent** `POST` (create *or* update) | Called on every mount and at onboarding; retries must not duplicate rows | Separate create/update endpoints (more states to get wrong) |

### 6.2 Dead ends — do not repeat

- ❌ **Re-wiring Supabase `profiles` for accounts.** It was tried, the contract
  never matched, and the credentials are not recoverable.
- ❌ **Signing the user up through Supabase Auth to "get a real identity".**
  It rate-limited the client (HTTP 429) and produced an identity nobody used.
- ❌ **A 1-hour sync marker.** It silently swallowed genuine updates; the
  current marker is 5 minutes and **bypassed** by `force: true` for user actions.
- ❌ **Reading `params.route` without decoding.** Pages does not always decode
  the splat, so `encodeURIComponent(email)` (`%40`) failed validation.
- ❌ **Handling only the methods you expect.** Without an `onRequest` export,
  unsupported verbs fall through to the `/api/*` catch-all and return a
  misleading 404 instead of 405.
- ❌ **Persisting the guest identity.** `reader@goodbooks.app` is shared by every
  anonymous visitor; writing it created one colliding row.

### 6.3 Invariants (tests will fail if broken)

1. `EMAIL_RE` in the function and `isValidAccountEmail` in the client are identical.
2. `POST` with no key and an existing email → `200 { created: false, exists: true }`
   and **no write**.
3. `PATCH`/`DELETE` without a valid key → `401`; with a valid key → `200`.
4. Responses never contain `account_key_hash` or `accountKey` (except the single
   201 create response).
5. Exactly **one** in-flight sync per email (`inFlightSyncs`).
6. Guest email never leaves the browser.

### 6.4 Verification recipe (≈2 minutes)

```bash
# 1. Binding + schema are live
curl -s https://books.dalecabra.com/api/accounts
# → {"database":"d1","count":N}

# 2. Full CRUD (create → read → update → reject bad key → delete)
EMAIL="check.$(date +%s)@example.com"
ENC=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$EMAIL")
KEY=$(curl -s -X POST https://books.dalecabra.com/api/accounts \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"name\":\"Check\",\"favoriteGenres\":[\"Fantasy\"],\"readingGoal\":12}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['accountKey'])")
curl -s "https://books.dalecabra.com/api/accounts/$ENC"                 # 200 profile
curl -s -X PATCH "https://books.dalecabra.com/api/accounts/$ENC" \
  -H 'Content-Type: application/json' -H "X-Account-Key: $KEY" -d '{"readingGoal":24}'   # 200
curl -s -o /dev/null -w '%{http_code}\n' -X PATCH \
  "https://books.dalecabra.com/api/accounts/$ENC" -H 'X-Account-Key: wrong' -d '{}'      # 401
curl -s -X DELETE "https://books.dalecabra.com/api/accounts/$ENC" -H "X-Account-Key: $KEY"  # 200
curl -s -o /dev/null -w '%{http_code}\n' "https://books.dalecabra.com/api/accounts/$ENC"   # 404

# 3. Data at rest
npm run db:inspect
npx wrangler d1 execute goodbooks-accounts --remote \
  --command "explain query plan select * from accounts where email='x@y.co' collate nocase limit 1;"
# → SEARCH accounts USING INDEX accounts_email_uidx (email=?)
```

Browser check (rebuild with `npm run build`, serve `dist/`, or use production):
onboard → reload → Settings shows *Saved to Cloudflare* → Delete → gate returns.
Automate it with Playwright's cached Chromium
(`~/Library/Caches/ms-playwright/chromium-*/`) via `playwright-core` and
`executablePath`; note that Playwright's scroll heuristics fight the fixed
sidebar, so scroll the Sign Out button into view, assert `elementFromPoint`
hits it, then dispatch `el.click()`.

### 6.5 File map

| Concern | File |
|---|---|
| Edge CRUD + validation + hashing | [`functions/api/accounts/[[route]].ts`](../functions/api/accounts/[[route]].ts) |
| Binding types (`env.DB`) | [`functions/api/_lib/types.ts`](../functions/api/_lib/types.ts) |
| Schema + audit table | [`d1/schema.sql`](../d1/schema.sql) |
| Client: sync/read/update/delete, key storage, email rule | [`src/lib/accountApi.ts`](../src/lib/accountApi.ts) |
| Compatibility layer used by the store | [`src/lib/userRepository.ts`](../src/lib/userRepository.ts) |
| Sync thunk (mount, onboarding, forced settings writes) | [`src/stores/user/userSlice.ts`](../src/stores/user/userSlice.ts) |
| Signup + skip-as-guest | [`src/components/Onboarding/OnboardingFlow.tsx`](../src/components/Onboarding/OnboardingFlow.tsx) |
| Persistence status + delete account | [`src/components/UI/SettingsModal.tsx`](../src/components/UI/SettingsModal.tsx) |
| Sign-out (relinquishes the key) | [`src/components/Navigation/NavigationSidebar.tsx`](../src/components/Navigation/NavigationSidebar.tsx) |
| Tests | [`tests/accountsApi.test.ts`](../tests/accountsApi.test.ts), [`tests/userRepository.test.ts`](../tests/userRepository.test.ts), [`tests/userSync.test.ts`](../tests/userSync.test.ts), [`tests/settingsAccount.test.tsx`](../tests/settingsAccount.test.tsx) |

### 6.6 Upgrade roadmap (ordered by value)

1. **Restore on a new device** — the row is readable but not writable without
   the key. Options: (a) email a one-time restore token, (b) password +
   magic-link, (c) Supabase Auth *as identity only* with the D1 row keyed by
   `auth.users.id`. Whichever path is chosen, keep D1 as the profile store and
   keep the `X-Account-Key` contract until it is replaced deliberately.
2. **Rate limiting / abuse** — add a Cloudflare WAF rule on `/api/accounts`
   (e.g. 10 POST/min per IP). Creation is open by design (no captcha).
3. **Reading events → D1** — `/api/reading` is still a Supabase no-op. Add a
   `reading_events` table to `d1/schema.sql` and route writes through `env.DB`,
   then the recommender finally has interaction history.
4. **Email verification** (optional) — only if accounts ever hold sensitive data.
5. **Retention job** — trim `account_events` older than 180 days if it grows.

When any of these lands, update this document, `docs/DATA_LAYER.md`,
`docs/PROJECT_STATUS.md`, `CHANGELOG.md`, and run `npm run docs:check`.

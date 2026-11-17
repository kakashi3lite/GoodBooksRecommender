# Security

GoodBooks takes the security of readers' data seriously. This document describes
the current security posture and how to report a vulnerability.

## Deployment security model

The live product (`books.dalecabra.com`) is a static SPA on **Cloudflare Pages**
with a serverless edge API (Pages Functions). There is no always-on backend
server to compromise.

| Area | Posture |
|---|---|
| Transport | HTTPS only (Cloudflare, HSTS-friendly headers) |
| Security headers | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy` — set via `_headers` and the API JSON helper |
| Secrets | All provider keys (Supabase service-role, AI/LLM keys) live **only** as Cloudflare Pages secrets. Never in the repo, never in the browser bundle. `VITE_*` public keys are the only values baked at build time |
| Data | Shelf, notes and progress live in `localStorage` on the device. The **account profile** (email, name, genres, pace, goal) is stored in **Cloudflare D1**; only a SHA-256 hash of the device's account key is kept. No telemetry/tracking |
| Account access | Reads **and** writes require `X-Account-Key` (256-bit, constant-time hash compare); an unknown account answers exactly like a wrong key (401), so the API cannot confirm whether an address exists. Responses are `Cache-Control: no-store` |
| Abuse / cost control | Per-client fixed-window limits in D1 for `/api/accounts` and `/api/ai/*` (hashed IPs, `Retry-After`, fails open) plus a zone WAF rule on `/api/*`. `/api/ai/*` also rejects cross-origin callers, non-JSON bodies and payloads over 64 KB |
| Guest isolation | The shared guest identity `reader@goodbooks.app` is never written to the database |
| AI | LLM calls are server-side via Pages Functions; the browser never sees provider keys |
| Dependencies | `npm audit --omit=dev` reports **0 vulnerabilities** in production deps; remaining advisories are dev-only tooling (vite/vitest/eslint/wrangler), not shipped |
| Malicious input | All edge APIs validate/coerce inputs (400 on bad JSON, empty payloads, unknown ids) |
| Asset cache guard | `/assets/*` 404s non-cacheable SPA fallback HTML to prevent MIME-sniffing attacks |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately instead — it lets us fix and release before details are public:

- Open a [private vulnerability report](https://github.com/kakashi3lite/GoodBooksRecommender/security/advisories/new)
  (GitHub "Security → Report a vulnerability"), or
- Email the maintainers privately via the repository owner's GitHub profile.

When reporting, include:

1. The affected endpoint/URL and version (commit hash if known)
2. A minimal reproduction (steps, payloads) — redact any real credentials
3. Your assessment of impact (what an attacker could do)

We aim to acknowledge reports within 5 business days and ship a fix promptly.
We follow a standard **90-day responsible disclosure** window before details are
made public.

## Hardening notes for maintainers

- **Never commit real credentials.** Use `.env.example` / placeholder values.
- Provider keys are Cloudflare **secrets** (`wrangler pages secret put …`), not
  environment variables in the dashboard.
- Before a release: run `npm audit`, `npm test`, `npm run type-check`,
  `npm run lint`, and re-verify headers + endpoints on the live deployment.
- Apple Double files (`._*`) can corrupt the local git store on macOS/APFS —
  delete them and avoid committing them (`.gitignore` covers `._*`).
- Keep `mlruns/`, `.env*`, local logs, and machine-specific paths out of git
  (`.gitignore` covers these).
- Rotate service-role/LLM keys periodically and after any suspected leak.
- **Accounts**: never re-introduce a raw account key in logs, responses or the
  database. If the `X-Account-Key` contract changes, update
  [`docs/ACCOUNTS.md`](docs/ACCOUNTS.md) and `tests/accountsApi.test.ts` together.
- Consider a Cloudflare WAF rate-limit rule on `/api/accounts` (creation is open
  by design; see [`docs/ACCOUNTS.md` § 6.6](docs/ACCOUNTS.md)).

## Scope

- **In scope**: the SPA, Pages Functions (`/api/*`), and the deployment config.
- **Out of scope**: the legacy Python/ML modules under `src/news/**`, `mlruns/`,
  and any abandoned demo/validation reports — these are not deployed.

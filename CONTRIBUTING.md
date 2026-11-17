# 🤝 Contributing to GoodBooks

Thanks for helping. This project ships a **live product** — every change to `main`
is deployed to <https://books.dalecabra.com> within minutes.

> **Agents and new contributors:** read [`AGENTS.md`](AGENTS.md) (rules, recipes) and
> [`HANDOFF.md`](HANDOFF.md) (current state) before your first change.

---

## 🚀 Setup (2 minutes)

Prerequisites: **Node 22+** and npm. (Python 3.10+ only if you are reviving the
legacy ML stack — see the appendix.)

```bash
git clone https://github.com/kakashi3lite/GoodBooksRecommender.git
cd GoodBooksRecommender
npm ci
npm run dev        # → http://localhost:3000
```

Optional, only if you need the real edge API locally:

```bash
npm run build
npx wrangler pages dev dist     # serves dist/ + functions/ (D1 binding from wrangler.toml)
# local D1 schema for wrangler pages dev:
npx wrangler d1 execute goodbooks-accounts --local --file=d1/schema.sql
```

There is **no** `pre-commit` hook, no Docker requirement, and no Python service to
start for the product.

---

## ✅ Before every PR

```bash
npm run type-check     # tsc --noEmit
npm test               # Vitest — 29 files / 183 tests
npm run lint           # ESLint — 0 errors required
npm run build          # production build
npm run docs:check     # only if you touched documentation
```

CI (`.github/workflows/ci.yml`) runs the same gates and is required to merge.
The deploy workflow additionally smoke-tests the live endpoints after publishing.

---

## 🎯 What to change where

| Change | Files |
|---|---|
| UI / routes / state | `src/components/**`, `src/stores/**`, `src/hooks/**` |
| Edge API | `functions/api/<group>/[[route]].ts` (+ `functions/api/_lib/**`) |
| Accounts / D1 | `functions/api/accounts/[[route]].ts`, `d1/schema.sql`, `src/lib/accountApi.ts` |
| Recommender | `functions/api/_lib/recommender.ts`, `src/utils/**` |
| Docs | `docs/**`, `DOCUMENTATION_INDEX.md` (never a new root `*_COMPLETE.md`) |

**Not in the deploy path:** `src/api`, `src/core`, `src/models`, `src/news`,
`src/fakenews`, `terraform/`, `docker-compose*.yml`, `nginx/`, `monitoring/`.
Changes there do not affect production.

---

## 🧪 Tests

- Add a test that would fail without your change; prefer the existing files.
- Pages Functions: import the handler and pass a fake `env.DB`
  (see [`tests/accountsApi.test.ts`](tests/accountsApi.test.ts)).
- Network-touching browser code: `vi.stubGlobal('fetch', …)`.
- The Python suite (`python -m pytest`) only covers the un-deployed backend.

Full breakdown: [`TEST_MATRIX.md`](TEST_MATRIX.md).

---

## 📚 Documentation

- Update the document in the **same** PR as the code.
- Add new documents under `docs/` and list them in
  [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md).
- Historical reports belong in [`docs/archive/`](docs/archive/README.md).
- `npm run docs:check` must pass (it fails CI on any broken relative link).
- State the verification date on documents that describe production.

---

## 🧭 Contribution types

### 🐛 Bug fixes
- Small: PR with fix + regression test.
- Complex: issue first (repro + root cause), then PR.
- Security: **private** report — see [`SECURITY.md`](SECURITY.md).

Checklist: reproducer test · root cause documented · minimal fix · regression tests ·
docs updated.

### ✨ Features
1. Issue describing the use case.
2. Design note (comment on the issue) for anything touching the API contract or D1.
3. Implementation + tests.
4. Documentation update.

### 📝 Commits & PRs
- Commit style: `type(scope): summary` (`feat(accounts): …`, `fix(ui): …`).
- Keep PRs scoped to one concern; describe the verification you ran.
- `main` is protected: CI must pass; no force-push.

---

## 💻 Coding standards (live stack)

- **TypeScript**: strict mode, no `any` additions, functional components, JSDoc on exports.
- **Edge functions**: JSON responses with `Content-Type`, `no-store` for private
  data, `X-Content-Type-Options: nosniff`; validate and clamp every input; export
  `onRequest` as well as the specific method handlers.
- **State**: Redux Toolkit slices; persist through the store's helpers, never raw
  `localStorage` in components.
- **Accessibility**: focus traps on overlays, `aria-*` on switches, 44px targets.
- **Comments**: explain *why* (the project uses "Chain-of-Thought" comments for
  non-obvious decisions) — not *what*.

Legacy Python conventions (PEP 8, type hints, `black`) apply only if you are
working in `src/**/*.py`.

---

## 📎 Appendix — running the legacy Python stack

Only needed to revive the FastAPI/ML backend (not deployed):

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # heavy: torch, faiss, sentence-transformers
uvicorn src.api.main:app --reload        # :8000
python -m pytest tests/
```

See [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md) and
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

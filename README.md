<div align="center">

# 📚 GoodBooks — Discover Books Made For You

**An AI-first reading companion that learns your taste and recommends books you'll actually finish.**

[![React](https://img.shields.io/badge/React-18+-61dafb?logo=react&logoColor=white)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178c6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5-646cff?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind](https://img.shields.io/badge/Tailwind-CSS-38bdf8?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Redux](https://img.shields.io/badge/Redux-Toolkit-764abc?logo=redux&logoColor=white)](https://redux-toolkit.js.org/)
[![Vitest](https://img.shields.io/badge/tests-37%20passing-6ba81b?logo=vitest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

**Create a free account → tell us what you love → get recommendations with reasons — instantly.**

</div>

---

## ✨ Why GoodBooks?

Most book platforms show you *popular* books. GoodBooks shows you **your** books.

- 🎯 **Truly personalized** — a 30-second taste quiz (genres, reading goal, pace) powers a
  ranking engine that matches books to *your* taste, with a human-readable **why** on every pick.
- 🧠 **An AI companion** — ask "what should I read next?" in plain language and get
  suggestion cards, instantly (works even offline).
- 📊 **Reading insights** — goals, streaks, and a futuristic dashboard that makes your
  reading life feel trackable and beautiful.
- 💾 **Private by design** — your taste profile lives on your device (or a database you own,
  via optional Supabase sync); no credit card, no spam.
- 🔗 **Share-ready** — rich link previews (Open Graph + Twitter cards) for posting on Reddit,
  X, Discord, and more (see `docs/SOCIAL_LAUNCH.md`).
- ⚡ **Fast & resilient** — instant personalized picks, graceful fallbacks, and a buttery
  animated UI (light & dark themes).

## 🚀 Quick Start

> Frontend-first: the dashboard runs standalone with demo + personalized data. The ML backend
> is being wired up (see [roadmap](#-roadmap)).

```bash
npm install
npm run dev
# → http://localhost:3000
```

Open the app → **create your account** → **pick your favorite genres** → your personalized
shelf appears instantly. That's it.

### Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Start the dev server (port 3000) |
| `npm test` | Run the test suite (Vitest, one-shot) |
| `npm run type-check` | Strict TypeScript check |
| `npm run lint` | ESLint (0 errors) |
| `npm run build` | Production build → `dist/` |
| `npm run format` | Prettier formatting |
| `npm run deploy` | Build + deploy to Cloudflare Pages |

## 🌍 Deployment (Cloudflare Pages)

The app is configured for **Cloudflare Pages** — global CDN, automatic HTTPS, native SPA
routing (`_redirects`), and security headers (`_headers`).

**Option A — One command (local)**:
```bash
npx wrangler login          # one-time browser auth
npm run deploy              # builds + deploys to Cloudflare Pages
```

**Option B — Automatic (GitHub Actions)**:
The repo ships `.github/workflows/cloudflare-pages.yml`. Add two repo secrets
(`Settings → Secrets → Actions`) and every push to `main` deploys automatically:
- `CLOUDFLARE_API_TOKEN` — API token with `Cloudflare Pages — Edit` permission
- `CLOUDFLARE_ACCOUNT_ID` — your Cloudflare account ID

The pipeline runs `type-check → lint → test → build → deploy`, so only verified builds ship.

## 🧭 Features

### 🎉 Onboarding that personalizes
A beautiful 3-step flow — **Welcome → Create account → Taste quiz** — that turns a first-time
visitor into a reader with a personalized shelf before they ever see a generic list.

### 🎯 Personalized recommendations
A taste-ranking engine scores the curated catalog against your genres and reading mood:
genre match (45%), mood match (20%), rating (15%), popularity (10%), recency (10%) — and
explains every pick: *"Because you love Science Fiction"*.

### 🤖 AI Reading Assistant
Chat with a book companion (`⌘K` to toggle). Ask for recommendations, mood matches, or
"something like my last thriller" — replies include rich book cards with ratings and a
**personalization reason** on every pick.

The companion is **conversationally personalized**:
- **Never repeats itself** — it remembers every book already suggested this conversation and
  rotates in fresh picks, so asking the same question twice gives different titles.
- **Learns your shelf** — it grounds picks in your real reading (favorite genres, current
  book, recently finished, pace and streak) even if you skipped the taste quiz.
- **Cards match the answer** — when the AI model is live, the suggested books are the ones
  it's actually talking about (matched against the catalog, topped up from Open Library /
  Google Books); offline, a smart local engine takes over with the same freshness rules.
- **"Different picks"** — one tap under any suggestion list swaps in books you haven't seen.

### � Covers & trust (sitewide)
- **Real book covers everywhere** — Open Library cover art loads on the Dashboard (Today's
  Pick, Continue Reading, personalized picks), Discover, the shelf, Wishlist, book details,
  and every AI chat card; a genre-tinted generated cover shows instantly while the real one
  fades in, so there's never a broken image or a blank gap.
- **Social proof** — "· 12K ratings" next to the stars on cards, and full rating volume on
  the detail page, so readers see that others have read and loved each pick.
- **No dead buttons** — Wishlist "Start Reading" actually starts the book and opens the
  shelf; AI suggestion cards open the book's detail page.

### �🗺️ Explore
- **Discover** — personalized picks + search entry point
- **Currently Reading** — your active shelf
- **Wishlist** — books saved for later
- **Reading Analytics** — charts & metrics
- **Book News** — curated literary updates

### 🎨 Futuristic Dashboard
Glassmorphism, neural-network backgrounds, 3D card hovers, dark/light themes, brightness
control, and a performance panel (`⇧P`) — built with React, Framer Motion, Recharts & Tailwind.

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React 18, TypeScript (strict), Vite 5, Tailwind CSS |
| State | Redux Toolkit (7 slices) + localStorage persistence |
| Animations | Framer Motion, React Spring |
| Charts | Recharts |
| Tests | Vitest + Testing Library (37 tests) |
| Backend *(in progress)* | FastAPI, HybridRecommender, FAISS vector store |

## 🧪 Quality

- ✅ `tsc --noEmit` — clean, strict mode
- ✅ ESLint — 0 errors
- ✅ **37 unit/component tests** passing (slices, personalization engine, onboarding flow,
  AI assistant, navigation)
- ✅ Production build with code-splitting

## 🗺️ Roadmap

| Status | Item |
|---|---|
| ✅ Done | Account creation + taste onboarding, personalized picks, AI assistant, dashboard shell |
| 🔄 In progress | Backend `/api/books/*` REST layer, Alembic migrations, real ML serving |
| 🔜 Next | Semantic "vibe" search, Year-in-Books Wrapped, reading identity analytics, book clubs |

> Honest status: the frontend is production-quality and fully usable today; the Python backend
> is being wired to serve real book data (see `HANDOFF.md` / `docs/DEPLOYMENT_PLAN.md`).

## 🤝 Contributing

1. Read [`HANDOFF.md`](HANDOFF.md) — it reflects the real state of the repo.
2. Keep the conventions: Chain-of-Thought comments, JSDoc, `type(scope): summary` commits.
3. Run `npm test`, `npm run type-check`, and `npm run lint` before pushing.

## 📄 License

MIT © GoodBooks Recommender Team

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
- 💾 **Private by design** — your taste profile lives on your device; no credit card, no spam.
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
"something like my last thriller" — replies include rich book cards with ratings.

### 🗺️ Explore
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

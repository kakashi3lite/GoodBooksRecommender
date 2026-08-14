<div align="center">

# 📚 GoodBooks

### The reading companion that learns your taste — and helps you *finish more books*.

> Most book apps show you what's *popular*.
> GoodBooks shows you **your** books — the ones you'll actually finish.

**✨ Live now → [books.dalecabra.com](https://books.dalecabra.com)**

[![Live](https://img.shields.io/badge/LIVE-books.dalecabra.com-8b5cf6?logo=cloudflare&logoColor=white)](https://books.dalecabra.com)
[![React](https://img.shields.io/badge/React-18+-61dafb?logo=react&logoColor=white)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178c6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/tests-100%2B%20passing-22c55e?logo=vitest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

**Tell us three things you love. Get books you'll actually finish — with reasons, not guesses.**
*Works instantly. No credit card. Your reading stays yours.*

</div>

---

## ✨ Why GoodBooks?

Remember the feeling of a book you couldn't put down? The quiet thrill of a
story that seemed written for *you*? GoodBooks is built to give you that feeling
**more often** — by turning everything you already love to read into a
recommendation engine that actually pays attention.

| 🎯 Knows your taste | A 30-second quiz (genres, goal, pace) powers picks ranked for *you* — and every pick explains itself: *"Because you love Science Fiction."* |
|---|---|
| 🧠 A companion that remembers | Ask "what should I read next?" in plain language. It remembers what it already suggested, so you never see the same books twice. |
| 📈 Progress you can feel | Streaks, goals, and a shelf that fills up — reading becomes something you can *see yourself winning*. |
| ☀️ A reason to come back | A fresh **Today's Pick** every day, plus live trending from the web. |
| 🔒 Yours by design | Your taste profile lives on your device. No tracking, no spam, no credit card. |
| ⚡ Beautifully fast | Covers load instantly, dark & light themes, works even when you're offline. |

---

## 🧭 Made for the reader who…

Whatever kind of reader you are, GoodBooks is built around *how you actually read*.

- **The mood reader** — "something cozy tonight" gets you exactly that: warm, gentle picks that match the *feeling* you're after, not just a genre label.
- **The completist** — a wishlist that becomes a reading list, a shelf that tracks your % through every book, and analytics that make your finish streak feel like an achievement.
- **The busy reader** — **Quick reads** filters (≤300 pages) and honest "~2 sessions at your pace" estimates from the AI, so a book never feels like a mountain again.
- **The explorer** — Discover searches the whole web (Google Books + Open Library), surfaces live trending, and every shared link opens a real, complete book page.
- **The returning reader** — streaks, a daily pick, and a companion that remembers your conversation, so every visit picks up right where you left off.

---

## 🚀 Start in 30 seconds

**Step 1 — Open** [books.dalecabra.com](https://books.dalecabra.com)

**Step 2 — Tell us what you love** (or tap *"Skip — explore as guest"* and let your shelf teach us)

**Step 3 — Watch your shelf fill** with picks that explain themselves — then start your first book.

That's it. No accounts required to explore, no email spam, no paywall.

---

## 💫 What you'll find inside

### 🏠 Your Dashboard
A reading life at a glance: your **Today's Pick**, the book you're mid-way through
(with "~hours left at your pace"), your streak, goal progress, and activity — all
from your real reading, nothing fabricated.

### 🔍 Discover
Search *any* book (not just our list) with live results and real covers, filter by
your favorite genres with one tap, browse **Trending Now from the web**, and get
AI picks ranked for you — with a human-readable **why** on every card.

### 📖 Your Shelf
Start a book, log pages with one tap (using *your own* average pace), finish with a
little celebration, and keep notes. Progress bars and "X left" estimates keep the
goal in sight — the finish line always feels closer than it is.

### ❤️ Wishlist
One tap saves a book for later. When you're ready, **Start Reading** moves it
straight onto your shelf — saved-for-later becomes read-today.

### 🤖 The AI Reading Companion
Press `⌘K` and talk like a human:

> *"Something like my last thriller, but with a happier ending."*

It answers with real books, real covers, and a **reason** for each pick. It learns
your genres, your pace, your streak, and what you just finished — and it *never
repeats itself*.

### 📊 Reading Analytics
Streaks, pages this month, books finished, top genres — plus a warm **AI reading
insight** that reflects on your real progress. Your growth, visible.

### 📰 Book News
Fresh, real book news from the web — no filler.

---

## 🧠 Built the way readers think

GoodBooks isn't just a list of features — it's designed around the psychology of
*sticking with reading*:

- **Micro-commitments** — logging pages is one tap, and it uses *your* average, so the habit is effortless to keep.
- **Goal-gradient effect** — every progress bar, "X% complete", and "X left" makes the finish line feel nearer, pulling you forward.
- **Identity** — see your reading persona ("Immersive Reader", "Binge Reader"…) and let it motivate you.
- **Variable reward** — a new Today's Pick every day and fresh AI suggestions keep discovery delightful, not repetitive.
- **Loss aversion, reversed** — your streak and progress are *yours*; losing them feels worse than skipping feels good.
- **Trust** — every filter works, every button does something, every number is real. Nothing fabricated, ever.

---

## 🔒 Your reading stays yours

- Your taste profile and shelf live **on your device**.
- No tracking pixels, no spam, no credit card, no dark patterns.
- Export your whole reading library anytime — it's your data.
- Optional sync keeps things in your control.

---

## 🛠️ For developers & contributors

GoodBooks is a modern, fully-tested frontend with a serverless edge backend
(Cloudflare Pages Functions) — no heavy ML server required.

| Stack | |
|---|---|
| Frontend | React 18 · TypeScript (strict) · Vite 5 · Tailwind CSS · Framer Motion |
| State | Redux Toolkit (8 slices) + localStorage persistence |
| Backend | Cloudflare Pages Functions (`/api/*`) — recommendations, AI chat, live web catalog |
| AI | OpenAI-compatible chat (MiniMax-M2), grounded in real reader data |
| Data | Supabase-ready schema + Open Library / Google Books live catalog |
| Tests | 100+ Vitest tests passing · `tsc` clean · ESLint 0 errors |

```bash
npm install
npm run dev        # local dev → http://localhost:3000
npm test           # one-shot test run
npm run build      # production build
```

Deployment is one command to Cloudflare Pages (`npm run deploy`), or automatic via
the included GitHub Actions workflow.

### Project structure

- `src/components/` — React feature components (Dashboard, Discover, AI, Shelf…)
- `src/stores/` — Redux slices (user, reading, books, ai, analytics…)
- `src/utils/` — recommendation engine, personalization, shared book filters, chat context
- `functions/api/` — serverless edge API (catalog, search, trending, AI chat/insight)
- `tests/` — unit + component tests
- `docs/` — architecture, runbook, data layer, deployment plan

Contributing conventions: Chain-of-Thought comments, JSDoc on every export,
`type(scope): summary` commits, and run `npm test` + `npm run type-check` +
`npm run lint` before pushing.

---

<div align="center">

**📚 Read what you love. Finish what you start.**

[books.dalecabra.com](https://books.dalecabra.com)

MIT © GoodBooks

</div>

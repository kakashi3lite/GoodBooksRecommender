# 📚 GoodBooks Recommender — Live Architecture & Development Context

> **Purpose**: the single source of truth for anyone (human or AI agent) continuing
> development. Covers what is actually deployed, how every feature is wired, the
> mobile dead-button incident and its fix, sharing + live curation architecture,
> the reader-productivity roadmap, and the deploy/verify runbook.
>
> **Live URL**: `https://books.dalecabra.com` (Cloudflare Pages, project
> `goodbooks-recommender`, branch `main`, custom domain `books.dalecabra.com`).

---

## 1. What Is Actually Deployed (2026-08-07)

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 18.3 + Vite 5.4 + TypeScript (strict) | 10 lazy routes, Tailwind + custom CSS, framer-motion, Redux Toolkit |
| API | **Cloudflare Pages Functions** (`functions/api/**`) | The live backend — there is **no Python server** in production |
| Database | Supabase `rqorywqrimcsgekmsxmj` | Schema **not yet applied** — API currently serves the embedded catalog (`source: "catalog"`) |
| Live data | Open Library + Google Books | Trending, ISBN/key resolution, book covers (all key-less) |
| News | Google News RSS → JSON | `functions/api/news/[[route]].ts` |
| AI chat | OpenAI-compatible (env-gated) | `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` as Cloudflare secrets |

### Env vars on the Pages project
- Plain: `SUPABASE_URL`, `SUPABASE_ANON_KEY` (publishable), `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `AI_PROVIDER`, `AI_MODEL`
- **Secret**: `SUPABASE_SERVICE_ROLE_KEY`, `AI_API_KEY`
- `VITE_*` vars are baked at **build time** (see runbook §8). Never commit secrets.

---

## 2. API Surface (edge functions)

All under `functions/api/`, all `GET` unless noted. Every route returns JSON.

| Endpoint | Purpose |
|---|---|
| `GET /api/books` | Full catalog (`{data, source, count}`) |
| `GET /api/books/search?q=` | Real text search over the catalog |
| `GET /api/books/recommend` | Hybrid recommender (`genres=`, `prefs=` JSON, `q=`, `similar_to=`, `limit=`, `exclude=`) |
| `GET /api/books/:id` | Single catalog book |
| `GET /api/books/:id/similar` | "More like this" (TF-IDF cosine) |
| `GET /api/books/trending?limit=` | **Live web curation** — Open Library trending + Google Books newest, TTL-cached 10 min |
| `GET /api/books/resolve?isbn=` or `?key=ol:\|gb:` | **Auto-fetch a shared book** from open-source catalogs |
| `GET /api/news/stories/trending` | Real book news (Google News RSS) |
| `GET /api/ai/chat` | Conversational AI (env-gated) |
| `GET /api/analytics/dashboard`, `/reading` | Analytics metrics |
| `/assets/*` | Non-cacheable 404 guard for missing assets |

### Recommender model (`functions/api/_lib/recommender.ts`)
Hybrid content-based — deliberately no heavy ML:
- TF-IDF + cosine over weighted fields (genres ×5, moods ×3, title ×4, authors ×2, description ×1)
- Profile scoring: genre 45% / mood 20% / rating 15% / popularity 10% / recency 10%
- MMR diversity (λ 0.3)
- **Genre aliases normalized** (`sci-fi` → `Science Fiction`, `self-help` → `Self-Help`, …) — without this the 45% genre weight silently collapsed to 0 and users got irrelevant picks (e.g. Atomic Habits for `genres=sci-fi`). Fixed 2026-08-06.

---

## 3. ⚠️ The "Buttons Do Nothing" Incident — Root Cause & Fix (IMPORTANT)

### Symptom
User reported on their phone: *"after I click any button it does nothing."*

### Root cause
The first-run **onboarding gate** rendered as a full-screen overlay
(`fixed inset-0 z-[60]`, `src/components/Onboarding/OnboardingFlow.tsx`). It is
rendered *inside* the app shell whenever
`!isAuthenticated || !hasCompletedOnboarding`. Any visitor without a persisted
`goodbooks_user` in `localStorage` — in-app browsers (Instagram/X/Facebook),
Safari private mode, or cleared storage — was **permanently blocked**: the
overlay intercepted **every** pointer event, so no button anywhere (even the
hamburger) responded. It had **no escape hatch**.

### The fix (deployed)
1. **"Skip for now — explore as guest"** button on the welcome step
   (`OnboardingFlow.tsx` → `skipForNow()`): registers a guest profile
   (`Reader` / `reader@goodbooks.app`), completes onboarding with default
   genres, and opens the app. The gate is now never a dead end.
2. **sessionStorage fallback** (`goodbooks_onboarded = '1'` set on both
   `handleFinish` and `skipForNow`; read in `App.tsx` via `onboardedThisSession`):
   in storage-restricted browsers the gate shows **once per session**, not on
   every reload.
3. Verified end-to-end in a 390×844 viewport: skip → overlay gone →
   `sessionStorage` flag set → dashboard "Welcome back, Reader! 👋".

### Prevention rule
**Never render a full-screen `z-[60]` overlay without an escape path.** Any
gate (onboarding, login, paywall) must have a skip/guest/close action and must
not render for returning users whose state fails to persist.

---

## 4. Feature Inventory & Button Wiring Map

Every interactive control and where it leads. Verified live (2026-08-07):

| Control | Action | Status |
|---|---|---|
| Hamburger (mobile) | Opens off-canvas drawer (`toggleMobileNav`) | ✅ |
| Drawer nav links | Route via `NavLink` (8 routes) | ✅ |
| **Discover search input** | **Debounced live search** against `/api/books/search` (was a dead "visual entry" input — fixed) | ✅ |
| AI recommendation cards | Navigate to `/book/:id` (shareable detail) | ✅ |
| Share button (cards + detail) | Native share sheet → clipboard copy + toast | ✅ |
| Start Reading | `startReading(bookId)` → reading shelf | ✅ |
| "+ Wishlist" | `toggleFavorite(bookId)` | ✅ |
| "Log 20 pages" (reading shelf) | `logReadingSession` → streak/analytics | ✅ |
| "Add Book" (sidebar) | Navigate to `/discover` | ✅ |
| Quick Recommendation | Dispatches recommendation flow | ✅ |
| Dark Mode | `setTheme` toggle | ✅ |
| Profile / Notifications / Settings | Honest toasts (no fabricated counts) | ✅ |
| Sign Out | `logout()` → returns to gate | ✅ |
| AI Assistant FAB | Toggles assistant panel | ✅ |
| Today's Pick | Daily date-seeded pick + Start Reading + wishlist | ✅ |

---

## 5. Book URL Sharing & Auto-Fetch (new)

The answer to *"does sharing a book URL auto-fetch from open-source sites?"* —
**yes**.

- Every `BookCard` has a **Share** button (top-right). It uses the native
  mobile share sheet (`navigator.share`) when available, else copies
  `https://books.dalecabra.com/book/{id}` to the clipboard with a toast.
- **`/book/:id`** (`src/components/Features/BookDetail.tsx`, lazy route):
  1. tries `/api/books/:id` (catalog),
  2. if the id is external (`isbn:…`, `ol:…`, `gb:…`, or a bare ISBN) →
     `/api/books/resolve?isbn=…` / `?key=…` which **fetches the real record
     from Open Library / Google Books** (title, authors, cover, description,
     year, pages, genres) and labels it *"Live from Open Library / Google Books"*.
- External ids come from the trending feed: Open Library works → `ol:KEY` or
  `isbn:…`; Google Books → `isbn:…` or `gb:ID`.

This means a shared link is **self-sufficient**: anyone who opens it gets the
real book, even if it was never in the curated catalog.

---

## 6. Live Web Curation (new — the app is NOT a fixed list)

`functions/api/_lib/webCatalog.ts`:

- `fetchWebTrending(limit)` — Open Library `/trending/daily.json` → `/trending/now.json`
  fallback, **plus** Google Books `orderBy=newest` across popular subjects;
  merged, de-duplicated by title, interleaved, and cached 10 min (module-level
  Map) to protect third parties.
- `resolveByIsbn(isbn)` — Open Library ISBN data API + work description.
- `resolveByKey(key)` — Open Library work key or Google Books volume id.
- All fetches have a 6 s timeout, a `User-Agent`, and hard multi-source
  fallback. If a provider is down or rate-limited, the feature degrades to the
  other source instead of failing.
- Surfaced in `Discover.tsx` as **"Trending Now — from the web"** (12 cards),
  each linking to its shareable detail page.

---

## 7. Reader-Productivity Features — Current + Roadmap

### Already live (daily-hook mechanics)
1. **Today's Pick** — date-seeded daily recommendation with a reason
   (`src/utils/dailyPick.ts`) → a reason to return daily.
2. **Reading shelf** — start a book, log pages (+20 quick-log), finish, remove
   (`src/stores/reading/readingSlice.ts`, persisted under `goodbooks_reading`).
3. **Reading notes** — add/edit/delete per book (`/notes`).
4. **Analytics** — streak, books finished, pages this month, reading time,
   last-14-days trend, top genres — all derived from real logged sessions.
5. **Wishlist** — persisted favorites resolved against the catalog.
6. **Community hub** — reader profile + badges.
7. **News dashboard** — real book news, no fabricated fallback.

### Roadmap (implementation logic, ordered by impact)
| # | Feature | Logic / where it plugs in |
|---|---|---|
| 1 | **Session timer** ("start a session, count minutes") | New reducer `startSession/stopSession` in `readingSlice`, persisted; converts minutes→pages-equivalent for analytics; UI on `/reading` + dashboard widget. |
| 2 | **Reading progress % derived from pages/page_count** | `logReadingSession` already advances `progressPct` by `pages/300`; change divisor to the book's real `page_count` from the catalog/detail so progress is accurate. |
| 3 | **"Finish book" flow with rating + reflection** | Reuse `finishReading` + `addNote`; add a small modal on the shelf (stars + optional note) before marking finished. |
| 4 | **Series detection** | `similar` endpoint + Google Books `series` metadata; render "Next in series" on `/book/:id`. |
| 5 | **Reading goals progress on dashboard** | `finishedCount / readingGoal` already computed; add a visual progress ring tied to `user.preferences.readingGoal`. |
| 6 | **Offline queue for trending/news** | Cache last `/trending` + news JSON in `localStorage` with a timestamp; show stale-while-revalidate. |
| 7 | **Supabase sync** | Apply `docs/supabase/schema.sql`; `/api/books` flips to `source: "database"`; then persist shelf/notes to the `reading_sessions`/`notes` tables. |

**Guardrails for every new feature**: persist to the Redux slice (never raw
`localStorage` directly), add a `Chain-of-Thought` comment, cover both
light/dark themes, ensure mobile + iPad layouts, and add a Vitest test.

---

## 8. Deploy & Verify Runbook

```bash
# 1. Clean Apple Double files (they break the Cloudflare bundler!)
find . -name '._*' -not -path './node_modules/*' -delete

# 2. Verify
npx tsc --noEmit
npx vitest run          # expect 69/69
npm run lint            # expect 0 errors (warnings OK)

# 3. Build with Supabase env baked in
VITE_SUPABASE_URL="https://rqorywqrimcsgekmsxmj.supabase.co" \
VITE_SUPABASE_ANON_KEY="sb_publishable_<...>" \
npm run build

# 4. Confirm zero demo markers in the bundle
grep -rl 'demo-[0-9]\|FALLBACK_BOOKS\|Lorem ipsum' dist/assets/ || echo "clean"

# 5. Deploy (branch main → production on books.dalecabra.com)
npx wrangler pages deploy dist --project-name goodbooks-recommender --branch main

# 6. Verify live
curl -sI https://books.dalecabra.com | grep -iE 'x-frame-options|x-content-type|permissions-policy'
curl -s "https://books.dalecabra.com/api/books/trending?limit=3"
curl -s "https://books.dalecabra.com/api/books/resolve?isbn=9780385533225"
curl -s "https://books.dalecabra.com/api/books/recommend?genres=sci-fi&limit=3"
```

### Gotchas learned the hard way
- **Cloudflare edge caching**: right after a deploy, the main domain may serve
  the *previous* function response for a few minutes (it happened with
  recommender results and the `resolve` 404). Test on the fresh
  `https://{hash}.goodbooks-recommender.pages.dev` URL to verify new code, then
  re-test the main domain.
- **Apple Double files** (`._*`) break the Functions bundle — always delete
  before building/deploying.
- **HEAD requests** to functions return 404 (only `onRequestGet` is defined) —
  use `GET` when curl-testing.
- **`curl -I`** on the main page returns `HTTP/2 103` early hints then `200`.
- `react-router-dom` is pinned to **7.18.2** (fixes GHSA-wrjc-x8rr-h8h6 open
  redirect). The remaining audit flag (GHSA-qwww-vcr4-c8h2) is **RSC-mode-only**
  and does not apply to this SPA; fixing it would require React 19 (deliberately
  out of scope).
- Browser automation (Playwright) may be intermittently unavailable; curl +
  a deployment-URL check is the reliable verification path.

---

## 9. Known Limitations / Next Actions

1. **Supabase schema not applied** — run `docs/supabase/schema.sql` in the
   Supabase SQL editor (`rqorywqrimcsgekmsxmj`). Until then `/api/books`
   reports `source: "catalog"` and account sync's profile lookup 404s.
2. **GitHub Actions** was down during this session (githubstatus.com incident);
   CI should self-heal on the next push.
3. **Recommended**: a fresh-device (real iPhone) visual pass — all server-side
   verification is done, and the mobile gate fix was verified in an emulated
   390×844 viewport, but a real device check is the final confirmation.
4. **Secrets hygiene**: the user pasted `sb_secret_…` and `sk-proj-…` in chat
   earlier. They exist only as Cloudflare secrets, never in the repo — consider
   rotating them.
5. `src/news/ai/*.py` + `src/news/master/*` are a **Python** subsystem not
   deployed to Cloudflare; leave them unless the Python backend is revived.

---

## 10. Commit History Reference (this session's work)

- `8b914b1` → `6c17411` — remove last demo fallback, trim dead code, fix genre-alias recommender
- `d54feb0` — security: upgrade react-router-dom to 7.18.2
- `6e6f5ff` — fix(mobile): onboarding gate escape + guest path; book sharing + auto-fetch; live web trending; Discover search wired
- `c79e977` — docs: live architecture runbook

## 11. UI/UX Pass (2026-08-07) — dark header, expandable blurbs, bento grid

### Dark-mode header fix (root cause)
`--glass-bg` / `--glass-border` were referenced (mobile topbar, sidebar,
toasts) but **never defined**, so the mobile header fell back to
`rgba(255,255,255,0.85)` — white in dark mode. Fixed by defining both
variables in `design-system.css` light + dark theme blocks:
- Light: `--glass-bg: rgba(255,255,255,0.78)`, `--glass-border: rgba(148,163,184,0.28)`
- Dark: `--glass-bg: rgba(30,30,30,0.72)`, `--glass-border: rgba(148,163,184,0.22)`

Verified computed style in dark mode: `rgba(30, 30, 30, 0.72)`.

### Expandable descriptions
- Every `BookCard` now has a **"Show description / Hide description"** toggle
  (`.book-expand-toggle` + `.book-expanded-desc`) — works on touch (no hover
  dependency). Featured cards keep the blurb open by default.
- **Backend**: Open Library trending works often omit descriptions. Added
  `enrichWithDescriptions` in `webCatalog.ts` — fetches real work records in
  parallel (bounded to 6) and attaches clean blurbs. A `cleanDescription`
  sanitizer strips HTML tags, markdown links, `&nbsp;`, backslashes.

### Bento grid (distinctive sizes)
- New `.bento-grid` + `.bento-item` classes in `book-card.css` with
  `bento-hero` (span 2×2), `bento-wide` (span 2 cols), `bento-tall` (span 2
  rows), `bento-standard`; `grid-auto-flow: dense`; responsive (2-col on
  mobile).
- `src/utils/bento.ts` `bentoPlacement(index)` assigns a size per item (repeats
  every 8). Applied to `AIBookRecommendations` and `WebTrending`.
- `BookCard` gained a `variant?: 'standard' | 'featured'` prop; featured cards
  use a 16:9 cinematic cover band + always-open blurb.
- Search results stay a uniform grid (scannable) but inherit the expand toggle.

### Deployment gotcha reconfirmed
Right after `wrangler pages deploy`, the new deployment's index.html can
reference assets/function bundles that 404 for 30–60 s (propagation). The
browser error boundary can latch onto a transient 404 — hard-reload after the
deploy settles. Verify the fresh deployment URL via curl before testing the
main domain.

## 12. Add-a-Book, Real Logging & Completion Ceremony (2026-08-07)

### Backend (all in `functions/api/`)
| Endpoint | What it does |
|---|---|
| `GET /api/books/web-search?q=&limit=20` | Finds ANY book: catalog hits first, then Google Books (rich descriptions) topped up with Open Library search. Every result has a real description + cover. |
| `GET /api/books/insights?isbn=\|id=\|key=` | 2–4 REAL facts about a book (synopsis, themes, published+pages, reader rating) + a genre-derived "what to expect" line. Nothing fabricated. |

### Frontend
- **Add Book modal** (`src/components/UI/AddBookModal.tsx`, opened from the
  sidebar "Add Book"): debounced web search → results with covers + blurbs →
  "Read" (adds to shelf with a **book snapshot**) or "Save" (wishlist).
- **Book snapshots**: `ReadingEntry` now stores a `book` snapshot at add-time
  (`src/stores/reading/readingSlice.ts`), so web-sourced books render on the
  shelf even though they're not in the catalog. `startReading` now takes
  `{ bookId, book? }`.
- **Real page logging** (`/reading`): no more fake "+20". A session editor
  takes the ACTUAL pages (presets 10/25/50/100 + custom stepper input). Progress
  = logged pages / 300 (roadmap: use the book's real page_count).
- **Completion ceremony** (`src/components/UI/BookCompletionModal.tsx`):
  finishing a book opens a modal with personalized motivation (reading persona,
  pace vs. usual, streak, goal progress — all derived from the real reading
  log) + the book's real facts from `/insights` + the genre expectation.

### Kindle sync — roadmap (needs external credentials)
A true Kindle sync requires Amazon's APIs, which are not open to third parties
(the consumer Kindle API is private; Goodreads was deprecated by Amazon). The
realistic path:
1. **Manual import**: user pastes their Amazon "Your Books" list / a Kindle
   notes export → parse into the shelf. No credentials needed — ship first.
2. **OPDS/Calibre-style import**: accept an `.opf`/CSV export from Calibre
   (users with a local Kindle library).
3. **OAuth (if Amazon ever opens an API)**: store tokens as Cloudflare
   secrets, sync highlights/books via a scheduled Worker.
Recommended first step: the manual paste/CSV import — it delivers the value
with zero external dependency.

## 13. UX/UI Fit Check (2026-08-07)
- **Touch targets**: audited every button on a 390px viewport. Fixed sidebar
  user actions + Quick Recommendation (36→48px), BookCard share button
  (32→36px), Dashboard Start Reading/Wishlist (38→42px), expand-toggle taller.
  Post-fix audit: **zero buttons under 40px**.
- Verified layouts at 390 / 834 / 1280 px: no horizontal overflow anywhere,
  mobile drawer + desktop sidebar both correct, dark mode glass header intact.

## 14. Reader-Bliss UX Pass (2026-08-07)

Psychology principles applied (all backed by the reader's OWN data — nothing
fabricated):

| Principle | Implementation |
|---|---|
| **Micro-commitments / friction** | One-tap quick log on `/reading`: "Log {your avg} pg" uses the reader's real average pages/session (`src/utils/readingInsights.ts` → `computePace`). The detailed editor (presets + custom) is one tap away. |
| **Goal-gradient effect** | "Continue reading" open-loop card on the Dashboard when a book is in progress: title, % done, **~Xh left at your pace**, one-tap log + "Open shelf". |
| **Zeigarnik (open loops)** | The continue card + `Timer` time-left chips on shelf cards pull readers back to unfinished books. |
| **Identity-based habits** | Visible **persona chip** in the welcome header (Binge/Immersive/Consistent/Seasoned/Rising Reader) from real log patterns (`personaOf`). |
| **Readability** | Relaxed line-height (1.65) on expanded blurbs, tightened title/author hierarchy in `book-card.css`. |
| **No dead controls** | Wired the Dashboard's dead "Add Book" (opens modal), "Get Recommendation" (refetch + toast), "Update Goal" (→ /analytics), "Join Community" (→ /community), Eye (refresh), Share (copy link). Removed the dead Download. **Replaced the fake "Log 20 pages" with the adaptive one-tap log.** |

New shared module: `src/utils/readingInsights.ts` (computePace,
estimateHoursLeft, formatHours, personaOf, personaEmoji, distinctReadingDays).

## 15. Mobile Navigation Overhaul (2026-08-07)

The phone view was button-dense with no thumb-zone navigation. Restructured
around the standard mobile pattern:

- **`MobileBottomNav`** (`src/components/Navigation/MobileBottomNav.tsx`, < 768px
  only): persistent bottom tab bar — **Home · Discover · Shelf (with live active
  book-count badge) · More**. Thumb-reachable primary navigation; active-state
  highlighting; 48px min-height tabs; safe-area inset padding.
- **Decluttered drawer**: the bottom bar now owns Home/Discover/Reading, so the
  off-canvas drawer hides those three links on mobile (`.mobile-hide-on-phone`)
  and becomes the "More" surface (Wishlist/Analytics/Community/News + quick
  actions + account). Drawer nav links enforce a 44px min-height.
- **Content clearance**: `.main-content` bottom padding bumped to
  `safe-area + 5.25rem` so the fixed bar never covers content (verified: last
  element scrolls above the bar); the AI FAB sits above the bar.
- **Dashboard declutter**: welcome "Get Recommendation" hidden on mobile
  (`hidden sm:inline-flex`) — Add Book remains, both live in the drawer too.
- Bottom bar + drawer hide on ≥ 768px; iPad/desktop keep the sidebar.
- Verified at 390px: tabs navigate, Shelf badge = active count, drawer opens via
  More, drawer links hidden correctly, no content occlusion.




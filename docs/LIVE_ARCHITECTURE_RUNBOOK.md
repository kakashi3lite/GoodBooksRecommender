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
| AI chat | OpenAI-compatible (env-gated) | MiniMax: `MINIMAX_API_KEY`, `AI_BASE_URL`, `AI_MODEL` as Cloudflare secrets |

### Env vars on the Pages project
- Plain: `SUPABASE_URL`, `SUPABASE_ANON_KEY` (publishable), `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `AI_PROVIDER`
- **Secret**: `SUPABASE_SERVICE_ROLE_KEY`, `MINIMAX_API_KEY`, `AI_BASE_URL` (`https://api.minimax.io/v1`), `AI_MODEL` (`MiniMax-M2`)
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
| `POST /api/ai/chat` | Conversational AI, personalized (env-gated) — see §19 |
| `POST /api/ai/insight` | Reading reflection from real stats |
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
# 7. Verify chat personalization (fresh picks on repeat) — see §19
curl -s -X POST https://books.dalecabra.com/api/ai/chat -H 'Content-Type: application/json' \
  -d '{"message":"recommend me a book","shown":[]}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get("model"),[b["id"] for b in d.get("bookSuggestions",[])])'
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
4. **Secrets hygiene**: all provider keys (Supabase service-role, AI/LLM keys)
   live only as Cloudflare Pages secrets — never in the repo, never in the
   browser bundle. Rotate them periodically as good practice.
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

## 16. Settings, Search & Branding Pass (2026-08-07)

### Settings now actually works (was a "coming soon" toast)
- **`SettingsModal`** (`src/components/UI/SettingsModal.tsx`) opens from the
  drawer "Settings" action AND the dashboard header gear — no more dead button.
  Real, functional controls wired to the stores:
  - **Appearance**: Light / Dark / Auto theme (`dashboardSlice.setTheme`)
  - **Reading**: yearly goal presets (5/12/24/52) + custom, notifications toggle,
    profile privacy (`userSlice.setPreferences`)
  - **Account**: signed-in reader info
  - **Data**: export the whole reading library as JSON (reader-owned data)

### Phone search bar now works with a nice format
- The dashboard header search was client-filtering only 6 books. Now **Enter**
  navigates to `/discover?q=...`; **Discover reads `?q=`** (`useSearchParams`)
  and renders the debounced web-search result grid (covers + blurbs + count).

### Dark-mode switch in the header
- **Mobile top bar**: sun/moon toggle button (App.tsx) — one tap to switch.
- **Dashboard header**: sun/moon toggle beside the bell/settings.
- Same store (`setTheme`) everywhere → consistent across header, settings, and
  the sidebar's Dark Mode action.

### Branding + color psychology (consistent system)
- **Name unified**: "GoodBooks" everywhere (was "BookWise" in the sidebar,
  dashboard header, and mobile top bar — fixed all three).
- **Signature mark**: the `from-blue-600 to-purple-600` gradient is the brand
  gradient (logo tile, welcome hero, primary CTAs, onboarding) — used
  consistently.
- **Semantic palette** (psychology-driven, applied consistently):
  - **Blue** = trust, calm, focus → primary actions, links, Today's Pick
  - **Purple** = imagination, personalization → AI, continue-reading, analytics
  - **Green** = growth, completion → goal progress, finish, success
  - **Amber/orange** = warmth, motivation → streak, flame
  - **Red** = alerts/badges only

## 17. Alignment & Placement Audit (2026-08-07)

A systematic audit ran every page (Dashboard, Discover, Reading, Wishlist,
Analytics, Community, News, Notes, Book Detail) at 3 viewports (390 / 834 /
1280 px) measuring horizontal overflow and touch-target sizes.

**Issues found & fixed:**
1. **Mobile Dashboard overflow** — the Dashboard's own sticky header (logo +
   search + theme/bell/settings) duplicated the mobile top bar and pushed the
   header buttons past the viewport. Fixed: the Dashboard header is now
   `hidden md:block` (mobile gets ONE top bar; search lives on Discover).
2. **Mobile Notes overflow** — the composer (select + Add Note) was a fixed
   flex row wider than 390px. Fixed: `flex-col sm:flex-row` + `min-w-0`.
3. **iPad Discover overflow** — bento cards didn't shrink to their grid cells
   (the card's default width won). Fixed: `.bento-item .book-card { width:100%;
   min-width:0 }`.
4. **Touch targets** — card action buttons (Start Reading / wishlist / share)
   and the BookCard share icon bumped to 40px (`p-3` / `py-3`).
5. **Page-padding consistency** — all feature pages standardized to
   `p-4 sm:p-8` (was mixed `p-8` on mobile).

**Post-fix verification: 0 overflow across all 27 page/viewport combos.**

## 18. Backend Strict Verification (2026-08-07)

An automated sweep hit every endpoint with valid + edge-case inputs. Result:
**27/27 checks passed.**

| Area | Checks (all PASS) |
|---|---|
| Catalog | `/api/books` returns the 24-book catalog (`source: catalog`) |
| Search | hit, no-results, and missing `q` → all correct shapes |
| Recommend | sci-fi genre alias → sci-fi first; `prefs` JSON; malformed prefs → graceful 200; free-text `q`; `similar_to` |
| Book id | found, 404 for unknown, `/similar` works |
| Web | `/trending`, `/web-search` (incl. empty `q`), `/resolve` (isbn + bad-isbn 404), `/insights` (≥2 facts) |
| News | real RSS (USA Today/KWTX/BBC) with links |
| AI chat | GET → 405, POST → reply+picks, empty message → 400, bad JSON → 400 |
| Analytics | dashboard 200; reading 200 |
| Errors | `/api/*` catch-all → 404 JSON; `/assets/*` guard → 404 no-store |

**Issues found & fixed:**
1. **Fabricated analytics trend** — `/api/analytics/reading` generated a
   14-day trend with `Math.random()` (dishonest data). The reader's real
   sessions live client-side, so the server now returns an honest empty
   `trends` array (the client builds its real trend from the reading log).
2. **API responses lacked `X-Content-Type-Options: nosniff`** — added to the
   books API's JSON responses (defense-in-depth for JSON endpoints).
3. **Apple Double files (`._*`) broke the Functions bundle** mid-deploy — the
   `find -delete` step is mandatory immediately before every deploy; they can
   reappear after editing (macOS creates them).

**Note on AI chat**: the LLM layer is OpenAI-compatible and the live provider
is **MiniMax** — `MINIMAX_API_KEY` (secret), `AI_BASE_URL` =
`https://api.minimax.io/v1`, `AI_MODEL` = `MiniMax-M2`. Chat falls back to the
local hybrid engine (real picks, `model: goodbooks-hybrid`) whenever the LLM
is unreachable. A bounded retry (4 attempts, backoff + Retry-After) is in
place so transient 429/5xx don't drop the reply.

## 19. AI Reading Companion v2 — context-aware MiniMax (2026-08-07)

Two LLM surfaces, both powered by MiniMax-M2, both grounded in the reader's
REAL data (the reading log lives client-side in `goodbooks_reading`; the client
sends a real profile — nothing is fabricated server-side).

**1. Context-aware chat** — `POST /api/ai/chat` now accepts an optional
`context` object (see `src/utils/chatContext.ts` `buildChatContext`):
`favoriteGenres`, `readingGoal`, `persona`, `currentBook` (title/author/
progress%), `stats` (streak, booksFinished, pagesThisMonth, avgPagesPerSession,
distinctDays), `recentlyFinished`. The profile is embedded in the USER message
(⚠️ MiniMax rejects large structured SYSTEM blocks — the profile must ride in
the user message; verified by isolating chat-vs-insight failure). Replies get
genuinely personalized (e.g. "at your pace, ~10–12 sessions") and the local
fallback also uses the real context hints. The frontend sends this context on
every message.

**2. AI Reading Insight** — `POST /api/ai/insight` takes the same `context`
and returns `{ insight, model }`: a warm 2–4 sentence reflection on the
reader's real pace/streak/goal/current book. Falls back to an honest template
built from the SAME numbers (model `goodbooks-hybrid`) when the LLM is
unavailable or the profile is empty. UI: "AI Reading Insight" card on
`/analytics` ("Reflect on my reading" / "Regenerate").

**Frontend changes**: chat abort timeout raised 4s → 30s (MiniMax reasoning
replies measure ~2–2.5s+; 4s killed valid replies). Chat header shows the live
model ("Powered by MiniMax-M2"). Offline fallback suggestions now come from the
REAL local catalog (removed hardcoded fake ids). Dead endpoints
(`/api/ai/tooltip|analysis|predict`) removed from the client.

**Live audit (all LLM surfaces, deployment 5531f21b)**:
- Chat with context → MiniMax-M2, personalized reply + 3 real picks ✓
- Chat without context → MiniMax-M2 ✓
- Insight with context → MiniMax-M2 reflection ✓ (verified in-browser)
- Insight with empty profile → honest template (model goodbooks-hybrid) ✓
- GET /api/ai/chat → 405 · empty message → 400 · bad JSON → 400 ✓
- Transient MiniMax 429s fall back gracefully to hybrid (real picks + context)
  — expected under bursty load; human-paced usage engages the LLM most of the
  time.

---

## 20. Conversational Personalization — the "same books every time" fix (2026-08-13)

### Symptom (reported by the owner)
> *"It shows the same titles of books each time I ask it a question."*

Reproduced live: `POST /api/ai/chat` with `{"message":"recommend me a book"}`
returned the **same 3 book cards** (`b-20`, `b-16`, `b-08`) on every request,
even though the LLM *text* differed. Root causes:

1. **Stateless picks** — the suggestion cards always came from the deterministic
   local engine (`recommendFromQuery`). A generic query ("recommend me a book")
   tokenizes to stopwords → near-zero cosine → the list just sorts by rating →
   the same top-3 every time.
2. **No conversation memory** — no record of what was already shown, no
   exclusion, no rotation.
3. **The LLM never influenced the cards** — it wrote the reply, but the cards
   were a fixed ranking that ignored the answer.

### The fix (3 layers, all shipped)

**Layer 1 — conversation memory + exclusion (the hard guarantee).**
- Client (`src/stores/ai/aiSlice.ts`) sends `history` (last 8 turns) and `shown`
  (every book id already suggested this conversation) with each request.
- Server (`functions/api/_lib/ai.ts` `excludeSetFor`) unions `shown` with the
  reader's **current book** and **recently-finished titles** and passes the set
  as `excludeIds` to the recommender → the engine is forced to rotate.
- Verified by test: asking the same question 3× with a growing `shown` set
  returns **zero overlap** across batches (`tests/aiPersonalization.test.ts`).

**Layer 2 — LLM-grounded picks (cards match the answer).**
- The system prompt now asks the model to END its reply with a JSON block:
  `{"books":[{"title","author","reason"}]}` (3–4 real books).
- `parseLlmBookPicks` (lenient — handles fenced JSON, prose, typos) +
  `matchLlmBooksToCatalog` (fuzzy title/author match against the catalog) turn
  those into suggestion cards.
- Books the catalog lacks are **topped up from the live web catalog**
  (`searchWebBooks`, bounded to 2 searches × 4 results) so the cards are real,
  with real covers.
- The local engine always fills any remaining slots (excluding `shown`) so the
  chat renders cards even if the LLM's JSON is unusable.

**Layer 3 — smarter fallback + context-derived taste.**
- `profileFromContext`: when the reader never picked genres, affinity is
  inferred from their real shelf (recently finished + current book genres), so
  even a bare "recommend me a book" is grounded in what they actually read.
- Every suggestion carries a `reason` ("why this book") surfaced in the UI.
- UI: a **"Different picks"** button under every suggestion list re-asks the
  last question with the grown `shown` set (new thunk `requestFreshPicks`).

### Wire contract (POST /api/ai/chat)

```jsonc
{
  "message": "recommend me a cozy book",          // required
  "context": { /* reader profile, client-built */ },
  "history": [{ "role": "user", "content": "…" }], // last 8 turns
  "shown": ["b-01", "b-16"]                        // ids already suggested
}
```

`ChatSuggestion` now includes `reason?: string`. Response model is
`MiniMax-M2` when the LLM answered, `goodbooks-hybrid` for the local engine.

### Files touched
- `functions/api/_lib/ai.ts` — helpers + `handleChat(env, message, prefs, context, history, shown)`
- `functions/api/ai/[[route]].ts` — accepts `history` + `shown`
- `src/utils/api.ts` — `chatWithAI(message, context, history, shown)`
- `src/stores/ai/aiSlice.ts` — builds memory payloads + `requestFreshPicks`
- `src/components/AI/AIAssistant.tsx` — reasons + "Different picks"
- `tests/aiPersonalization.test.ts` — 13 tests (parsing, exclusion, rotation)

### Verify live
```bash
# Same question twice — the second must return DIFFERENT book ids:
curl -s -X POST https://books.dalecabra.com/api/ai/chat -H 'Content-Type: application/json' \
  -d '{"message":"recommend me a book","shown":[]}' | python3 -c 'import sys,json;print([b["id"] for b in json.load(sys.stdin)["bookSuggestions"]])'
# (then repeat with "shown":[<ids from the first reply>])
```







## 21. Covers Sitewide + Reader-Psychology Pass (2026-08-14)

### Covers sitewide (root cause)
`BookCover` renders a genre-tinted **generated cover** instantly and overlays
the **real cover** (`cover_url`) when one exists. The audit found 6 surfaces
that rendered `BookCover` WITHOUT `coverUrl` — so users only ever saw generated
art there, even though real Open Library covers were in the data:

- AI chat suggestion cards (`AIAssistant.tsx`)
- Dashboard "Continue Reading" card
- Dashboard "Today's Pick" card
- Dashboard personalized book list
- Currently Reading shelf cards
- Wishlist cards

**Fix**: pass `coverUrl={book.cover_url}` in all 6 (data was already present).
Verified live (fresh deployment + browser): Dashboard 7/7 covers loaded,
Wishlist 2/2, shelf 2/2, chat 5/5, book detail 1/1. Open Library covers return
`302 → archive.org` (browsers follow; not a data problem).

### BookCover polish (`src/components/UI/BookCover.tsx`)
- `fetchPriority` prop (default `auto`) — passed as lowercase `fetchpriority`
  because React 18.3.1 warns on the camelCase prop.
- One-shot **loading shimmer** over the generated base while the real image
  downloads (perceived performance — progress is visible).
- Real cover **fades + gently scales in** on load (`useState`-driven, not
  classList). State resets when `coverUrl` changes (list recycling).
- Generated art stays as the fallback — never a broken image.

### Reader-psychology refinements
| Lever | Change |
|---|---|
| **Social proof** | `BookCard` now shows "· 12K ratings" beside the stars (`ratingsCount`, optional, threaded through Discover/WebTrending/AIBookRecommendations); BookDetail already showed "· 180,000 ratings". |
| **Trust — no dead CTAs** | Wishlist "Start Reading" was a **button with no handler** — now `dispatch(startReading)` + navigate to `/reading` (verified live: clicking added the book to the shelf and navigated). |
| **Actionability** | AI chat suggestion cards (already cursor-pointer) now open `/book/:id` on click/keyboard — discovery ends in a concrete step. |
| **Perceived performance** | Cover shimmer + fade-in; hero covers can opt into high fetch priority. |

### Files touched
`BookCover.tsx`, `BookCard.tsx`, `AIAssistant.tsx`, `Dashboard.tsx`,
`CurrentlyReading.tsx`, `Wishlist.tsx`, `Discover.tsx`, `WebTrending.tsx`,
`AIBookRecommendations.tsx`, `dashboard/css/book-card.css`,
`tests/components/Wishlist.test.tsx` (new — empty state, cover render, Start
Reading wiring), `tests/components/AIAssistant.test.tsx` (wrap in MemoryRouter
now that suggestion cards use `useNavigate`). 91/91 tests, tsc clean, lint 0.

### Verify live
- Open every surface and confirm `img[src*="openlibrary.org"]` has
  `naturalWidth > 0` (browser). Lazy covers below the fold load on scroll.
- Wishlist: save a book → real cover + "Start Reading" adds it to the shelf.
- Chat: ask for a book → suggestion cards carry covers + reasons + ratings;
  clicking opens the book detail.

## 22. Filters Apply Correctly Sitewide (2026-08-14)

### Root cause
The Dashboard's filter tabs (`all/trending/recommended/new/favorites`) set
`activeFilter` but **never used it** — `filteredBooks` only applied the search
query, so every tab was decorative. The "genre" dropdown was a fake control:
`selectedGenre = 'All Genres'` hardcoded, no menu, no onClick. Discover had no
genre filters at all.

### The fix — one shared filter vocabulary
New module `src/utils/bookFilters.ts` is the single source of truth used by
both Dashboard and Discover, so behavior is identical sitewide:
- `normalizeGenre` — alias-aware ("sci-fi" → "Science Fiction"), mirrors the
  server recommender.
- `BOOK_FILTER_TABS` — honest, data-backed tabs that always return results:
  `For you` (all), `Top rated` (≥4.5★), `Quick reads` (≤300 pages), `Feel-good`
  (cozy/uplifting moods). (An initial "New arrivals" tab was dropped — the
  catalog's newest book is 2022, so it would have been a dead tab.)
- `applyBookFilters` — tab + genre + query combined.
- `genreChipsFor` / `catalogGenreChips` — chips ranked **favorite-first** with
  live counts.

### Reader-psychology choices
| Principle | Implementation |
|---|---|
| **Trust (no dead controls)** | Every tab/chip now filters; verified live. |
| **Hick's law (choice overload)** | 4 meaningful tabs, not 5 vague ones; chips over a mystery dropdown. |
| **Recognition + identity** | Genre chips rank the reader's favorite genres first. |
| **Loss aversion / momentum** | Live counts on every tab + chip; "Showing X of Y picks" line. |
| **Status quo / defaults** | Default tab "For you", default genre "All genres". |

### Wiring
- **Dashboard**: `displayBooks` now carries real fields (full `genres`, `moods`,
  `page_count`, `published_year`, limit 6→9); tabs + chips + search all flow
  through `applyBookFilters`; empty state added.
- **Discover**: genre chip row (catalog counts, favorite-first) filters search
  results client-side AND is passed as `filterGenres` to `AIBookRecommendations`
  + `WebTrending` (both gained an optional alias-aware client filter).

### Verify (all PASS live, deployment 2fe42d11)
- Dashboard: "Quick reads" → "Showing 1 of 9" · "Top rated" → "Showing 5 of 9"
  (all ≥4.5★) · "Mystery" chip → "Showing 2 of 9 in Mystery".
- Discover: "Science Fiction" chip → only The Martian / Project Hail Mary / Dune
  across AI + trending; search "murder" + Mystery → "4 results for \"murder\" in
  Mystery" (all Mystery titles).
- 100/100 tests (new `tests/bookFilters.test.ts`, 9 tests incl. "no dead tabs").

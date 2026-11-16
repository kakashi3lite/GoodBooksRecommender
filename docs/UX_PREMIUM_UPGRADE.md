# 🎛️ Premium UX Upgrade — Reading Companion 2.1

> **Status:** shipped · **Scope:** frontend finish + reading-data integrity + DB contract
> **Verified:** `npm test` 111/111 · `tsc --noEmit` clean · `npm run lint` 0 errors · `npm run build` passing
> **Live:** [books.dalecabra.com](https://books.dalecabra.com)

This document records *why* the interface looks and behaves the way it does. Every
decision below is traceable to either (a) published research, (b) an observed defect in
this codebase, or (c) a documented platform guideline. Nothing here is decorative taste.

---

## 1. Market position — what is actually open

Research (Nov 2026, sources in §6) on the current reading-app landscape:

| Product | Recommendation model | Progress capture | Social default | Gap |
| --- | --- | --- | --- | --- |
| Goodreads | Opaque collaborative filtering | Manual page/% update | Public graph (Amazon-owned) | Discovery is popularity-shaped; progress costs effort |
| The StoryGraph | ML + mood/pace *filters* | Charts-first, manual | Deliberately light | Filters ≠ reasoning; no session model |
| Fable | Community/club-driven | Weekly/monthly goals | Clubs | Now bundled with an ebook subscription |
| Hardcover | History-based + trending | want/reading/read/DNF | Explicit social network | Still a feed-first product |
| Readwise Reader | None (read-it-later) | Position across formats | Single-player | No "finish a book" concept at all |
| Literal / Oku / Bookmory / Likewise | — | — | — | Unverifiable or wound down (see gaps in §6) |

**The unoccupied position GoodBooks takes:** *conversational, constraint-aware
recommendation* (a stated reason per pick, aware of pace and momentum) + *zero-cost
progress capture* + *private by default* + *recovery-first habit design*. No
competitor combines all four.

What we deliberately did **not** copy: infinite feeds, public reading graphs, or
streak-shaming. Those optimise for session volume, not finished books.

---

## 2. Research → design decision mapping

| Finding (source §6) | What we shipped | Where |
| --- | --- | --- |
| **Goal-gradient:** effort rises as the *proportion* remaining shrinks; pre-granting progress accelerates completion (Kivetz et al. 2006) | Progress is now derived from the **real page count**, so "84 pages to go" is literally true. Quick reads (≤300 pages) tab + "~2 sessions at your pace" | `readingSlice.progressOf`, Dashboard tabs |
| **Zeigarnik / Ovsianikina:** unfinished tasks are recalled more easily; the urge to *resume* is a distinct effect | "Pick up where you left off" is a first-class card with a one-tap log — an invitation, never a debt | Dashboard |
| **Implementation intentions:** planning *when/where/how* raises goal attainment (Gollwitzer & Sheeran 2006) | Session logging captures the reader's own average, so the commitment is to a familiar amount, not an abstract target | `readingInsights.computePace` |
| **Choice overload is conditional** (Scheibehenne et al. 2010; Chernev et al. 2015) | We reduced **comparison cost**, not just list length: every card carries one reason, tabs carry live counts, genre chips rank favourites first | `bookFilters`, Dashboard |
| **Loss aversion (Kahneman & Tversky 1979) powers streaks — and is the risk** | **Recovery-first streaks.** One honest repair per missed gap, plus a "start fresh" that is remembered. No punishment loop | `streakAtRisk` / `restoreStreak` |
| **Skeleton screens** beat spinners and must match real geometry (NN/g 2026; Apple HIG) | Cover-shaped 2:3 skeletons in Dashboard + Discover — zero layout shift when data lands | `BookGridSkeleton`, `materials.css` |
| **Motion must be purposeful and optional** (Apple HIG; IBM Carbon productive/expressive) | Two registers: 150 ms *productive* for UI, 420 ms *expressive* reserved for rare moments. Global `prefers-reduced-motion` kill-switch | `materials.css` |
| **Fixed elevation ladder + hairline strokes reads "crafted"** (Vercel Geist Materials) | One material scale (`surface-1/2/3`, `elev-1..4`, 0.625→1.375 rem radii) replaces one-off shadows | `materials.css` |
| **⌘K should perform actions, not only search** (Linear/Raycast pattern) | Command palette executes: log progress, ask the companion, switch theme, jump to any book (live web search) | `CommandPalette.tsx` |
| **Empty states should teach and offer the key task** (NN/g 2021) | Shelf, filter, and search empty states each explain *and* offer the next action | Dashboard / Shelf / Discover |
| **North star = books finished per active reader** (HEART, Rodden et al. 2010) | Every number on screen derives from `readingLog`; nothing fabricated. `reading_events` now mirrors real events to Postgres | `readingSlice`, `/api/reading` |

---

## 3. What shipped

### 3.1 Design system: a materials layer
`dashboard/css/materials.css` (new, imported after `design-system.css`)

- **Elevation ladder** `--elev-1..4` — two-layer soft shadows + 1 px hairline, light and
  dark variants. Radii step with elevation (`.625 → 1.375 rem`).
- **Reading type ramp** `.type-reading` — 68 ch measure, 1.65 line-height, serif, for
  long-form text only. The UI ramp stays compact, so hierarchy is structural rather
  than size-based.
- **`.numeric`** tabular numerals so live stats don't jitter as they update.
- **Skeletons** `.skeleton`, `.skeleton-cover` (true 2:3), `.skeleton-line`.
- **Micro-feedback** `.saved-pulse`, `.progress-just-updated` — precise, tied to the
  action, ~120 ms.
- **`.pressable`** 0.985 scale on `:active` for tactile confirmation.
- **`prefers-reduced-motion`** disables all animation and transitions globally.
- **Focus** — one consistent 2 px accent ring on every interactive element.

### 3.2 ⌘K command palette (new)
`src/components/UI/CommandPalette.tsx`

- Opens with `⌘K` / `Ctrl+K`; `↑ ↓` move, `↵` run, `Esc` close.
- **Actions:** log the reader's usual session on the active book, switch theme, open the
  companion.
- **Navigation:** every route.
- **Books:** live `/api/books/web-search` results (300 ms debounce) → real book pages.
- **Never dead-ends:** a free-text query always becomes *"Ask the companion: …"*.
- Accessibility: `role="dialog"`, `aria-modal`, real listbox + `aria-activedescendant`,
  focus restored to the previously focused element, background scroll locked.
- **Shortcut change:** the AI companion moved to `⌘J`. One shortcut per intent; `⌘K` is
  now the app-wide command surface (documented in README).

### 3.3 Progress integrity — the fix behind the polish
`src/stores/reading/readingSlice.ts`

**Defect:** progress advanced by `pages / 300` regardless of the book. One 60-page
session on *Dune* (688 pp) reported **20%** complete — the line "you're 20% done" was
false, and every downstream estimate inherited the lie. Trust in a reading tracker rests
entirely on its numbers.

**Now:**
- `ReadingEntry.currentPage` is the source of truth; `progressOf(entry)` derives the
  percentage from the book's real `page_count`.
- `pagesLeftOf(entry)` gives an exact "X pages left".
- When a book's length is genuinely unknown (some web results), the legacy estimate is
  kept and the UI *says so* ("Page count unknown — progress is estimated").
- Progress can never exceed 100% or overrun `page_count`.

### 3.4 Zero-friction check-in — "I'm on page N"
`CurrentlyReading.tsx`

Readers hold a **position**, not a delta. The shelf now offers a slider + number input
pre-filled with the current page. The delta from the previous position is logged as a
real session, so the streak and analytics stay honest; moving backwards corrects the
position without inventing pages.

Also on the shelf: primary action dominance (one blue "Log" button, not three equal
ones), `page X of Y · Z left`, and a premium empty state with two concrete next steps.

### 3.5 Recovery-first streaks
`readingSlice.streakAtRisk` · `restoreStreak` · `dismissStreakRecovery`

- If a reader logged a run of ≥3 consecutive days and then missed exactly **one** day,
  the Dashboard offers **"Restore my streak"** — once per gap.
- The repair writes a **0-page** entry: the run survives, the analytics do not lie.
- "Start fresh" is a first-class choice and is remembered (`graceUsedFor`), so the app
  never nags.
- `streakBest` records a private best-ever run.
- Long absences are **not** recoverable — that would make the mechanic meaningless.

**Why not a freeze currency?** A purchasable freeze is a monetisation hook; this product
has no paywall. One honest repair per gap is the minimum mechanic that preserves the
identity without monetising anxiety. Instrument `streak-break churn` (D7 of readers who
broke a streak vs. those who didn't) as a guardrail — if the gap is large, revisit.

### 3.6 Day-boundary correctness
Reading dates were computed with `toISOString()` (**UTC**), while "read today" used the
**local** day. In UTC+5:30 a 1 a.m. session was filed under yesterday, so the streak and
the "read today" pill disagreed. `localDateKey()` is now the single source of truth for
every date in the reading layer.

### 3.7 Loading, empty, and feedback states
- **Dashboard / Discover** — geometry-matched skeletons instead of a text flash.
- **Shelf** — empty state teaches the one-book commitment and offers Discover + Today's Pick.
- **Filtered grid** — "Show all picks" recovery action.
- **Search** — no-match state explains, offers "Clear search" and "Remove genre filter".
- **Cards** — a "saved" pulse next to the progress bar when a session is logged, so the
  confirmation is where the reader is looking.
- **Mobile** — the Today's Pick and Continue Reading cards stack (cover + copy, then
  full-width actions) instead of squeezing the reason text into a 60 px column at 390 px.

### 3.8 Structural defects found while polishing
These were not cosmetic tweaks — each one was visible on the live app.

1. **Every sidebar row broke its own layout.** `mobile-nav.css` shipped
   `.mobile-hide-on-phone { display: block !important }` inside the *desktop* media query
   to neutralise the phone "hide" rule. With `!important` it beat `flex items-center`, so
   the active row's icon box stretched to the full sidebar width and the label overlapped
   it. The desktop rule was unnecessary (the hide rule already lives inside the phone
   query) and has been removed.
2. **Generated covers had invisible typography.** `fontSize: 'min(34%, 3.4rem)'` resolves
   a percentage against the *parent font size* (~14 px), so monograms rendered at ~5 px
   and cover titles at ~2 px. Replaced with explicit per-size type scales; generated
   covers are now legible at every size.
3. **`theme: 'auto'` produced undefined design tokens.** `data-theme` received the raw
   preference (`auto`), but the design system only defines values for `light` and `dark`,
   leaving backgrounds transparent. `data-theme` now carries the **resolved** theme and
   the preference is kept in `data-theme-preference`.
4. **Eight routes painted their own blue→indigo gradient.** That fought the paper-white /
   charcoal design tokens and made each screen feel like a different product. They now
   share `.page-surface`, so colour comes from content (covers, progress, data) rather
   than the wallpaper.

---

## 4. Backend + database contract

The UI must never *look* connected while saving nothing. Two data paths now exist:

### 4.1 Recommendation audit (pre-existing bug, fixed)
`functions/api/_lib/db.ts` has always posted to `recommendations_log`, but the table was
never created — every audit write silently failed. `recommendations_log` is now part of
the schema.

### 4.2 Reading events (new)
```
Browser (local-first readingSlice)
   │  dispatch(startReading | logReadingSession | setProgress | finishReading)
   ▼
readingSync middleware  (non-blocking, no-op when unconfigured)
   │  POST /api/reading { client_id, event_type, book_id, pages, page, progress, session_date }
   ▼
Cloudflare Pages Function  functions/api/reading/[[route]].ts
   │  validates: UUID client_id, known event_type, bounded numbers
   ▼
Supabase Postgres  public.reading_events   (service-role only)
```

**Design rules**
- **Local-first stays the source of truth.** Sync is best-effort: network failures are
  swallowed, nothing blocks a reducer, and the reader's action never waits on analytics.
- **Silent when unconfigured.** Without `VITE_SUPABASE_URL` the middleware never touches
  the network — tests, dev, and offline use stay clean.
- **Write-only.** There is no public read endpoint by design. `reading_events` has RLS
  enabled with **no** anon/authenticated policies; only the server-side service-role key
  writes. Any cross-device restore must be an explicit, opt-in flow later.
- **Anonymous identity.** `client_id` is a UUID v4 generated in the browser and stored in
  `localStorage` (`goodbooks_client_id`). No email, no name, no fingerprint.
- **Honest dates.** `session_date` is the reader's *local* day, so a streak computed in
  SQL matches the one computed in the app.

**Why this matters for the product:** `reading_events` is the interaction history needed
to graduate the recommender from TF-IDF + profile scoring to collaborative filtering. The
data layer doc set the threshold at ~10k events; this is the pipe that fills it.

### 4.3 Activating it
```bash
# 1. Apply the schema (idempotent) — Supabase SQL editor
docs/supabase/schema.sql
#    or: supabase/migrations/20261117090000_reader_data.sql

# 2. Set the frontend flag that turns on sync
VITE_SUPABASE_URL=https://<project-ref>.supabase.co
```
Nothing else changes. `/api/reading` returns `{ stored: false, reason: "not_configured" }`
until both the table and the server env vars exist.

---

## 5. Metrics to watch (instrumentation contract)

| Event | Why | Status |
| --- | --- | --- |
| `book_added` → `started` | Activation proxy: "% who add a book and log once in session 1" | ✅ `reading_events` |
| `progress` (with `pages` + `page`) | Session completion + pace model | ✅ `reading_events` |
| `finished` | **North star:** books finished per active reader | ✅ `reading_events` |
| `rec_shown{rec_id, reason}` | Reason is both a UI requirement and an evaluation label | ⏳ `recommendations_log` (strategy + ids); reason per-card next |
| `streak_broken` / `resume_prompt_shown` | Guardrail: streak-break churn | ⏳ derive from `reading_events.session_date` |
| `palette_opened`, `empty_state_cta` | Command-surface adoption | ⏳ client-side only today |

Set a **first-week baseline** before quoting any industry retention number — the research
brief explicitly could not verify a reading-app-specific D1/D7 figure, and quoted
benchmarks are the easiest way to build the wrong roadmap.

---

## 6. Sources

1. Kivetz, Urminsky & Zheng (2006), *JMR* 43(1):39–58 — goal-gradient + "illusion of progress" — https://doi.org/10.1509/jmkr.43.1.39
2. Zeigarnik (1927) / Ovsianikina (1928) — https://en.wikipedia.org/wiki/Zeigarnik_effect
3. Gollwitzer & Sheeran (2006), *Adv. Exp. Soc. Psych.* 38 — https://doi.org/10.1016/S0065-2601(06)38002-1
4. Scheibehenne, Greifeneder & Todd (2010), *JCR* 37(3) — https://doi.org/10.1086/651235
5. Chernev, Böckenholt & Goodman (2015), *JCP* 25(2) — https://doi.org/10.1016/j.jcps.2014.08.002
6. Kahneman & Tversky (1979), *Econometrica* 47(2) — https://doi.org/10.2307/1914185
7. Apple HIG — Motion — https://developer.apple.com/design/human-interface-guidelines/motion
8. Apple HIG — Loading — https://developer.apple.com/design/human-interface-guidelines/loading
9. IBM Carbon — Motion — https://www.carbondesignsystem.com/building-blocks/foundations/motion/overview
10. Vercel Geist — Materials — https://vercel.com/geist/materials
11. NN/g — Skeleton Screens 101 — https://www.nngroup.com/articles/skeleton-screens/
12. NN/g — Progressive Disclosure — https://www.nngroup.com/articles/progressive-disclosure
13. NN/g — Empty State Interface Design — https://www.nngroup.com/articles/empty-state-interface-design/
14. web.dev — prefers-reduced-motion — https://web.dev/articles/prefers-reduced-motion
15. Rodden, Hutchinson & Fu (2010), CHI — HEART framework
16. The StoryGraph — https://www.thestorygraph.com/ · Goodreads — https://www.goodreads.com/about/us

**Gaps recorded honestly:** no peer-reviewed study of "reading slumps" or streak-loss
effects in reading apps was found. Treat those claims as design hypotheses to instrument,
not as facts to print.

---

## 7. Verification

**Automated**

```bash
npm test          # 111 passed (20 files)
npm run type-check # tsc --noEmit clean
npm run lint      # 0 errors (66 pre-existing warnings)
npm run build     # ✓ built
```

**Manual (headless Chromium, 1440×1000 and 390×844)**

| Check | Result |
| --- | --- |
| `⌘K` opens the palette; typing filters; `↵` runs the command | ✅ navigated to `/analytics` from the palette |
| Palette action mutates real state | ✅ "Switch to light mode" flipped `dashboard.theme` |
| Light + dark themes | ✅ paper-white and charcoal surfaces, readable at both |
| "I'm on page 120" check-in | ✅ `currentPage: 120`, `progressPct: 75` (160 pp book), delta logged as 120 pages with the local date |
| Streak recovery | ✅ banner shown for a 3-day run with one missed day; restore wrote a `0`-page `recovered` entry and set `graceUsedFor` |
| Sidebar layout | ✅ icon box + label inline; active pill + badge aligned |
| Generated cover typography | ✅ monograms legible (D, PH, AP, TS…) |
| Mobile 390 px | ✅ Today's Pick stacks; reason text no longer squeezed to one word per line |
| Console | ✅ no page errors (only `500`s from the intentionally absent local FastAPI proxy) |

---

## 8. Apple form-factor matrix (iPhone / iPad / Mac)

Verified in headless Chromium at native CSS sizes with `deviceScaleFactor: 2`,
after seeding a real in-progress book so every surface renders its busy state.

| Form factor | CSS width | Layout | Sidebar | Content | Overflow |
| --- | --- | --- | --- | --- | --- |
| iPhone SE | 375 × 667 | drawer + tab bar | off-canvas 300px | 375 | 0 |
| iPhone 15 Pro | 393 × 852 | drawer + tab bar | off-canvas 300px | 393 | 0 |
| iPhone Pro Max | 430 × 932 | drawer + tab bar | off-canvas 300px | 430 | 0 |
| iPad mini (portrait) | 744 × 1133 | drawer + tab bar | off-canvas 300px | 744 | 0 |
| iPad Air (portrait) | 820 × 1180 | **icon rail** | 72px | 748 | 0 |
| iPad Pro 11 (portrait) | 834 × 1194 | **icon rail** | 72px | 762 | 0 |
| iPad (landscape) | 1194 × 834 | full sidebar | 280px | 914 | 0 |
| MacBook Air | 1280 × 800 | full sidebar | 280px | 1000 | 0 |
| Mac 1440 | 1440 × 900 | full sidebar | 280px | 1160 | 0 |
| Mac 1920 | 1920 × 1080 | full sidebar | 280px | 1640 | 0 |

### Why a tablet rail exists
A 280px labelled sidebar on an 820px iPad leaves **540px** for the reading UI. In
practice that truncated the Today's Pick title (`A Psalm fo…`), squeezed the
"0 books this month" stat caption onto two lines, and pushed the filter row into
four wrapped rows. An icon rail gives that space back (**748px**) while keeping
every destination one tap away — the same pattern iPad-native apps use.

Bands are re-applied only when they change (`App.tsx`), so a reader who collapses
the sidebar on their Mac keeps it collapsed until the next band change.

### Fixes found by this matrix
| # | Defect | Impact |
| --- | --- | --- |
| 1 | `index.html` linked `/dashboard/css/*.css` and preloaded it, but that path is **not in the build output** | 2 × 404 + a wasted preload on every production page load |
| 2 | Sidebar analytics (`CompactAnalytics`, ~230px wide) rendered inside the 72px rail | Metric cards spilled over the page content on iPad and on any collapsed sidebar |
| 3 | AI assistant FAB sat at `bottom: 1.5rem`, on top of the phone tab bar | Covered the "More" tab — a 41px tap-target collision on every iPhone |
| 4 | The FAB-safe rule (`.ai-toggle`) targeted a class the React button never had | Dead CSS; the real overlap above was never fixed |
| 5 | `initializeDashboard` awaited a **simulated 1-second timer** before `isInitialized` | A full second of "Initializing AI systems…" on every cold load. Now **169–226ms** |
| 6 | `[env.production]` was an empty table in `wrangler.toml`; `_redirects` claimed `/api/*` was not served | Misleading config — Pages Functions do serve `/api/*` |
| 7 | Zero-byte dead files (`FuturisticDashboard.tsx`, 3 services, 2 CSS files) | Redundancy in the tree and one empty CSS import in the entry point |

### Deploy hardening
- `scripts/purge-apple-double.cjs` runs in `npm run deploy` **and** in CI. macOS
  writes `._*` sidecars (23 were present in `dist/` on this external volume) and
  they are not valid JS — they break the Functions bundle. Local and CI deploys
  now behave identically.
- `.app-shell .ai-assistant-fab` / `.app-shell .main-content` / `.app-shell .navigation-sidebar`
  are shell-scoped because Tailwind utilities and `react-components.css` are
  bundled last; a bare class selector loses the cascade tie.

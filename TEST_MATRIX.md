# Test Matrix

Live suite: **29 files / 183 tests** (`npm test`, Vitest). CI runs the whole
suite on every PR and before every deploy.

| Area | Location | What it proves |
|---|---|---|
| Accounts API contract | `tests/accountsApi.test.ts` | Create (201 + one-time key), idempotent repeat, read, key-guarded update/delete, 400/401/404/405/503, percent-encoded email, malformed patch cannot wipe fields |
| Account client | `tests/userRepository.test.ts` | Same-origin POST, key storage/reuse, offline `{synced:false}`, profile mapping, delete clears key + sync marker |
| Sync thunk | `tests/userSync.test.ts` | Only authenticated non-guest users sync; `force` is forwarded |
| Settings → Account | `tests/settingsAccount.test.tsx` | Persistence status ("Saved to Cloudflare" / "Local only"), two-tap delete signs out |
| User slice | `tests/userSlice.test.ts`, `tests/userPersistence.test.ts` | Registration, persisted state, sign-out clears profile + gate flag |
| Onboarding | `tests/components/OnboardingFlow.test.tsx` | 3-step flow, validation parity with the server, real `POST /api/accounts` |
| Recommender | `tests/serverRecommender.test.ts`, `tests/personalization.test.ts`, `tests/readingPace.test.tsx` | TF-IDF/profile ranking, genre aliases, pace↔mood mapping |
| Books/UI | `tests/booksSlice.test.ts`, `tests/bookFilters.test.ts`, `tests/coverArt.test.ts`, `tests/dailyPick.test.ts` | Search/filter/covers/daily pick |
| Reading | `tests/readingSlice.test.ts`, `tests/readingIntegrity.test.ts`, `tests/readerExperience.test.tsx` | Sessions, streaks, progress maths |
| News | `tests/newsFeed.test.ts`, `tests/news/*` | RSS parsing, entity decoding, merge/dedupe |
| AI | `tests/aiSlice.test.ts`, `tests/chatContext.test.ts`, `tests/aiPersonalization.test.ts` | Chat context, anti-repetition, fallbacks |
| Production posture | `tests/productionPosture.test.ts` | Landing/SEO/PWA invariants |
| Legacy Python | `tests/backend/`, `tests/test_*.py` (pytest) | Not part of the deploy gate; exercises the un-deployed FastAPI stack |

## Conventions

- New behaviour gets a test that fails without the change.
- Pages Functions are imported directly and called with a fake `env.DB`
  (see `tests/accountsApi.test.ts`) — no local server needed.
- Browser code that touches the network is tested with `vi.stubGlobal('fetch', …)`.
- Coverage is not chased; contracts and edge cases are.

## Gaps (deliberate)

- No E2E suite in CI. The deploy workflow runs live smoke tests
  (`/`, `/api/books`, `/api/accounts`, custom domain) instead.
- No load tests. The edge is stateless; the only stateful hop is D1.

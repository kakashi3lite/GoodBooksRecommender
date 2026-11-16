/**
 * 🧪 Reading integrity — regression tests for defects found in the reader audit
 *
 * Each test below failed against the shipped build. They encode invariants a
 * reader implicitly trusts:
 *
 *   1. Progress never goes backwards because of a code change (loss aversion:
 *      losing progress is the single most demotivating event in a tracker).
 *   2. Pages logged reflect pages actually read — a 160-page book cannot
 *      contribute 500 pages to a month's total.
 *   3. Finishing a book counts as reading activity for that day (the streak
 *      must credit the peak moment, or the habit loop punishes celebration).
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReadingState } from '../src/stores/reading/readingSlice'

const LEGACY_KEY = 'goodbooks_reading'

describe('reading integrity', () => {
    let reducer: typeof import('../src/stores/reading/readingSlice').default
    let actions: typeof import('../src/stores/reading/readingSlice')

    beforeEach(async () => {
        localStorage.clear()
        vi.resetModules()
        const mod = await import('../src/stores/reading/readingSlice')
        reducer = mod.default
        actions = mod
    })

    /**
     * F1 — legacy progress must survive the upgrade.
     * Before `currentPage` existed, progress was stored only as `progressPct`.
     * Treating a missing `currentPage` as 0 meant the first session after the
     * upgrade recomputed progress from zero: a reader at 50% of a 400-page book
     * dropped to ~2% after logging 10 pages.
     */
    it('migrates legacy progressPct into currentPage so progress never regresses', async () => {
        localStorage.setItem(
            LEGACY_KEY,
            JSON.stringify({
                currentlyReading: [
                    {
                        bookId: 'b-11',
                        book: { title: 'Dune', authors: 'Frank Herbert', cover_url: '', page_count: 400 },
                        progressPct: 50,
                        startedAt: Date.now() - 8.64e7,
                        updatedAt: Date.now() - 8.64e7,
                        finishedAt: null
                        // no currentPage — this is pre-2.2 data
                    }
                ],
                readingLog: [],
                notes: []
            })
        )

        vi.resetModules()
        const mod = await import('../src/stores/reading/readingSlice')
        const restored = mod.default(undefined, { type: '@@INIT' } as never)
        const entry = restored.currentlyReading[0]

        expect(entry.currentPage).toBe(200) // 50% of 400 pages
        expect(mod.progressOf(entry)).toBe(50)

        const after = mod.default(restored, mod.logReadingSession({ bookId: 'b-11', pages: 10 }))
        // 210/400 = 52.5% → rounds to 53, never a drop to 2%.
        expect(mod.progressOf(after.currentlyReading[0])).toBe(53)
        expect(after.currentlyReading[0].currentPage).toBe(210)
    })

    /**
     * F2 — a session cannot contribute more pages than the book has left.
     * Logging 120 pages of a 160-page book already at page 100 recorded 120
     * pages in the monthly total, inflating "pages this month", reading hours,
     * and the reader's average pace forever.
     */
    it('clamps logged pages to the pages actually remaining', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-06',
                book: { title: 'A Psalm', authors: 'Becky Chambers', cover_url: '', page_count: 160 }
            })
        )
        state = reducer(state, actions.setProgress({ bookId: 'b-06', page: 100 }))

        state = reducer(state, actions.logReadingSession({ bookId: 'b-06', pages: 120 }))

        // Only 60 pages remained, so only 60 may be recorded.
        const logged = state.readingLog.slice(-1)[0]
        expect(logged.pages).toBe(60)
        expect(actions.pagesAllTime(state.readingLog)).toBe(160)
        expect(actions.progressOf(state.currentlyReading[0])).toBe(100)
    })

    /**
     * F2b — once a book is finished, further logging must not add pages or
     * sessions. Otherwise a stray tap on the shelf inflates the month.
     */
    it('ignores sessions on a book that is already finished', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-12',
                book: { title: 'The Name of the Wind', authors: 'Patrick Rothfuss', cover_url: '', page_count: 662 }
            })
        )
        state = reducer(state, actions.logReadingSession({ bookId: 'b-12', pages: 662 }))
        state = reducer(state, actions.finishReading('b-12'))
        const before = state.readingLog.length

        state = reducer(state, actions.logReadingSession({ bookId: 'b-12', pages: 30 }))

        expect(state.readingLog.length).toBe(before)
        expect(actions.pagesAllTime(state.readingLog)).toBe(662)
    })

    /**
     * F9 — finishing is reading activity.
     * A reader who closes a book at 11pm without logging a page saw their
     * streak break on the biggest day of their week.
     */
    it('credits the streak on the day a book is finished', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-18',
                book: { title: 'The Martian', authors: 'Andy Weir', cover_url: '', page_count: 384 }
            })
        )
        state = reducer(state, actions.finishReading('b-18'))

        expect(state.readingLog).toHaveLength(1)
        const entry = state.readingLog[0]
        expect(entry.pages).toBe(0) // honest: no pages invented
        expect(entry.finished).toBe(true)
        expect(actions.computeStreak(state.readingLog)).toBe(1)
        expect(actions.pagesAllTime(state.readingLog)).toBe(0)
    })

    /**
     * A check-in is a position, so the pages it credits must be the distance
     * actually travelled inside the book — never the raw number typed.
     */
    it('never credits more pages than the book has when a check-in overshoots', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-16',
                book: { title: 'The Midnight Library', authors: 'Matt Haig', cover_url: '', page_count: 288 }
            })
        )
        state = reducer(state, actions.setProgress({ bookId: 'b-16', page: 144 }))
        state = reducer(state, actions.setProgress({ bookId: 'b-16', page: 999 }))

        const logged = state.readingLog.reduce((sum, entry) => sum + entry.pages, 0)
        expect(state.currentlyReading[0].currentPage).toBe(288)
        expect(logged).toBe(288)
    })

    it('credits the finish even when pages were already logged today', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-13',
                book: { title: 'Gone Girl', authors: 'Gillian Flynn', cover_url: '', page_count: 432 }
            })
        )
        state = reducer(state, actions.logReadingSession({ bookId: 'b-13', pages: 40 }))
        state = reducer(state, actions.finishReading('b-13'))

        // A day can hold both "I read 40 pages" and "I finished the book" —
        // the finish is the moment worth keeping, so it must not be swallowed.
        expect(state.readingLog).toHaveLength(2)
        expect(state.readingLog[0]).toMatchObject({ pages: 40 })
        expect(state.readingLog[1]).toMatchObject({ pages: 0, finished: true })
    })

    it('never records the same finish twice', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-14',
                book: { title: 'Dune', authors: 'Frank Herbert', cover_url: '', page_count: 412 }
            })
        )
        state = reducer(state, actions.finishReading('b-14'))
        state = reducer(state, actions.finishReading('b-14'))

        expect(state.readingLog.filter((entry) => entry.finished)).toHaveLength(1)
    })

    /**
     * The migration must be durable: a reader who opens the app and closes it
     * without logging anything should still have the repaired page position.
     */
    it('writes the migrated page position back to storage', async () => {
        localStorage.setItem(
            LEGACY_KEY,
            JSON.stringify({
                currentlyReading: [
                    {
                        bookId: 'b-15',
                        book: { title: 'Piranesi', authors: 'Susanna Clarke', cover_url: '', page_count: 245 },
                        progressPct: 50,
                        startedAt: Date.now(),
                        updatedAt: Date.now(),
                        finishedAt: null
                    }
                ],
                readingLog: [],
                notes: []
            })
        )

        vi.resetModules()
        await import('../src/stores/reading/readingSlice')

        const persisted = JSON.parse(localStorage.getItem(LEGACY_KEY) as string)
        expect(persisted.currentlyReading[0].currentPage).toBe(123)
    })

    /**
     * Restore must be resilient: a corrupt payload should not white-screen the
     * app, and must not silently discard a readable history either.
     */
    it('recovers from a corrupt persisted payload without throwing', () => {
        localStorage.setItem(LEGACY_KEY, '{"currentlyReading": "not-an-array"}')
        expect(() => reducer(undefined, { type: '@@INIT' } as never)).not.toThrow()
        const state: ReadingState = reducer(undefined, { type: '@@INIT' } as never)
        expect(Array.isArray(state.currentlyReading)).toBe(true)
        expect(Array.isArray(state.readingLog)).toBe(true)
    })
})

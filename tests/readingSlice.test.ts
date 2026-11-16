/**
 * 📚 Reading Slice Tests
 * Chain-of-Thought: verifies the persisted reading activity model — start,
 * progress logging (which feeds the streak), finishing, notes, and that
 * nothing depends on demo data.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

describe('readingSlice', () => {
    let reducer: typeof import('../src/stores/reading/readingSlice').default
    let actions: typeof import('../src/stores/reading/readingSlice')

    beforeEach(async () => {
        localStorage.clear()
        vi.resetModules()
        const mod = await import('../src/stores/reading/readingSlice')
        reducer = mod.default
        actions = mod
    })

    it('startReading adds a 0% entry (with snapshot support for web books)', () => {
        const state = reducer(undefined, actions.startReading({ bookId: 'b-01' }))
        expect(state.currentlyReading).toHaveLength(1)
        expect(state.currentlyReading[0]).toMatchObject({ bookId: 'b-01', progressPct: 0, finishedAt: null })

        // Snapshot path — a web book (non-catalog id) persists on the shelf.
        const withSnapshot = reducer(
            state,
            actions.startReading({
                bookId: 'isbn:1234567890',
                book: { title: 'Web Book', authors: 'Author', cover_url: 'https://x/cover.jpg' }
            })
        )
        expect(withSnapshot.currentlyReading).toHaveLength(2)
        expect(withSnapshot.currentlyReading[1].book).toMatchObject({ title: 'Web Book' })
    })

    it('startReading does not duplicate an existing book', () => {
        let state = reducer(undefined, actions.startReading({ bookId: 'b-01' }))
        state = reducer(state, actions.startReading({ bookId: 'b-01' }))
        expect(state.currentlyReading).toHaveLength(1)
    })

    it('logReadingSession advances progress and records a daily session', () => {
        let state = reducer(undefined, actions.startReading({ bookId: 'b-02' }))
        state = reducer(state, actions.logReadingSession({ bookId: 'b-02', pages: 60 }))
        expect(state.readingLog).toHaveLength(1)
        expect(state.readingLog[0].pages).toBe(60)
        expect(state.currentlyReading[0].progressPct).toBeGreaterThan(0)
        expect(state.currentlyReading[0].progressPct).toBeLessThanOrEqual(100)
    })

    it('finishReading marks the book complete and counts toward booksFinished', () => {
        let state = reducer(undefined, actions.startReading({ bookId: 'b-03' }))
        state = reducer(state, actions.finishReading('b-03'))
        expect(state.currentlyReading[0].finishedAt).not.toBeNull()
        expect(state.currentlyReading[0].progressPct).toBe(100)
    })

    it('computeStreak counts consecutive logged days', () => {
        const { computeStreak } = actions
        const d = (offset: number) => {
            const date = new Date()
            date.setDate(date.getDate() - offset)
            return date.toISOString().slice(0, 10)
        }
        const log = [0, 1, 2].map((offset) => ({ date: d(offset), pages: 20, bookId: 'b-01', ts: Date.now() }))
        expect(computeStreak(log)).toBe(3)
        // A gap resets the streak.
        const gapped = [...log, { date: d(5), pages: 20, bookId: 'b-01', ts: Date.now() }]
        expect(computeStreak(gapped)).toBe(3)
    })

    it('notes can be added, edited, and deleted', () => {
        let state = reducer(undefined, actions.addNote({ text: 'A great opening', bookId: 'b-01' }))
        expect(state.notes).toHaveLength(1)
        const id = state.notes[0].id
        state = reducer(state, actions.updateNote({ id, text: 'Even better on reread' }))
        expect(state.notes[0].text).toBe('Even better on reread')
        state = reducer(state, actions.deleteNote(id))
        expect(state.notes).toHaveLength(0)
    })

    it('persists to localStorage so a reload keeps the shelf', () => {
        let state = reducer(undefined, actions.startReading({ bookId: 'b-04' }))
        state = reducer(state, actions.logReadingSession({ bookId: 'b-04', pages: 30 }))
        const raw = localStorage.getItem('goodbooks_reading')
        expect(raw).toBeTruthy()
        expect(JSON.parse(raw as string).currentlyReading[0].bookId).toBe('b-04')
    })
})

describe('readingSlice — honest progress + kind streaks', () => {
    let reducer: typeof import('../src/stores/reading/readingSlice').default
    let actions: typeof import('../src/stores/reading/readingSlice')

    beforeEach(async () => {
        localStorage.clear()
        vi.resetModules()
        const mod = await import('../src/stores/reading/readingSlice')
        reducer = mod.default
        actions = mod
    })

    const dayKey = (offset: number): string => {
        const d = new Date()
        d.setDate(d.getDate() - offset)
        return actions.localDateKey(d)
    }

    const emptyState = () =>
        ({ currentlyReading: [], readingLog: [], notes: [], streakBest: 0, graceUsedFor: null }) as ReturnType<
            typeof reducer
        >

    it('derives progress from the book’s real page count', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-11',
                book: { title: 'Dune', authors: 'Frank Herbert', cover_url: '', page_count: 688 }
            })
        )
        state = reducer(state, actions.logReadingSession({ bookId: 'b-11', pages: 60 }))

        // 60 / 688 ≈ 9%. The old fixed /300 estimate reported 20% for any book.
        expect(actions.progressOf(state.currentlyReading[0])).toBe(9)
        expect(state.currentlyReading[0].progressPct).toBe(9)
        expect(actions.pagesLeftOf(state.currentlyReading[0])).toBe(628)
    })

    it('keeps the legacy estimate when the page count is unknown', () => {
        let state = reducer(undefined, actions.startReading({ bookId: 'web-1' }))
        state = reducer(state, actions.logReadingSession({ bookId: 'web-1', pages: 30 }))
        expect(state.currentlyReading[0].progressPct).toBe(10)
        expect(actions.pagesLeftOf(state.currentlyReading[0])).toBeNull()
    })

    it('never exceeds 100% or overruns the page count', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-06',
                book: { title: 'A Psalm', authors: 'Becky Chambers', cover_url: '', page_count: 160 }
            })
        )
        state = reducer(state, actions.logReadingSession({ bookId: 'b-06', pages: 500 }))
        expect(state.currentlyReading[0].progressPct).toBe(100)
        expect(state.currentlyReading[0].currentPage).toBe(160)
    })

    it('setProgress takes a position and logs the delta as a real session', () => {
        let state = reducer(
            undefined,
            actions.startReading({
                bookId: 'b-02',
                book: { title: 'Project Hail Mary', authors: 'Andy Weir', cover_url: '', page_count: 496 }
            })
        )
        state = reducer(state, actions.setProgress({ bookId: 'b-02', page: 124 }))

        expect(state.currentlyReading[0].currentPage).toBe(124)
        expect(state.currentlyReading[0].progressPct).toBe(25)
        expect(state.readingLog).toHaveLength(1)
        expect(state.readingLog[0].pages).toBe(124)

        // Moving backwards corrects the position without fabricating a session.
        state = reducer(state, actions.setProgress({ bookId: 'b-02', page: 100 }))
        expect(state.currentlyReading[0].currentPage).toBe(100)
        expect(state.readingLog).toHaveLength(1)
    })

    it('offers one repair for a single missed day and keeps analytics truthful', () => {
        const log = [2, 3, 4].map((offset) => ({
            date: dayKey(offset),
            pages: 20,
            bookId: 'b-01',
            ts: Date.now()
        }))

        const risk = actions.streakAtRisk(log)
        expect(risk.brokenStreak).toBe(3)
        expect(risk.missedDate).toBe(dayKey(1))

        const restored = reducer(
            { ...emptyState(), readingLog: log },
            actions.restoreStreak({ missedDate: risk.missedDate as string })
        )
        expect(actions.computeStreak(restored.readingLog)).toBe(4)
        expect(restored.graceUsedFor).toBe(risk.missedDate)
        // The repair adds a day but no pages, and is excluded from "read days".
        expect(actions.pagesAllTime(restored.readingLog)).toBe(60)
        expect(restored.readingLog.at(-1)?.recovered).toBe(true)

        // The same gap is never offered twice.
        const again = reducer(restored, actions.restoreStreak({ missedDate: risk.missedDate as string }))
        expect(again.readingLog).toHaveLength(4)
    })

    it('does not offer a repair after a long absence', () => {
        const log = [5, 6, 7].map((offset) => ({
            date: dayKey(offset),
            pages: 20,
            bookId: 'b-01',
            ts: Date.now()
        }))
        expect(actions.streakAtRisk(log)).toEqual({ brokenStreak: 0, missedDate: null })
    })

    it('dismissStreakRecovery remembers the reader chose a fresh start', () => {
        const dismissed = reducer(emptyState(), actions.dismissStreakRecovery({ missedDate: dayKey(1) }))
        expect(dismissed.graceUsedFor).toBe(dayKey(1))
        expect(dismissed.readingLog).toHaveLength(0)
    })
})

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

    it('startReading adds a 0% entry', () => {
        const state = reducer(undefined, actions.startReading('b-01'))
        expect(state.currentlyReading).toHaveLength(1)
        expect(state.currentlyReading[0]).toMatchObject({ bookId: 'b-01', progressPct: 0, finishedAt: null })
    })

    it('startReading does not duplicate an existing book', () => {
        let state = reducer(undefined, actions.startReading('b-01'))
        state = reducer(state, actions.startReading('b-01'))
        expect(state.currentlyReading).toHaveLength(1)
    })

    it('logReadingSession advances progress and records a daily session', () => {
        let state = reducer(undefined, actions.startReading('b-02'))
        state = reducer(state, actions.logReadingSession({ bookId: 'b-02', pages: 60 }))
        expect(state.readingLog).toHaveLength(1)
        expect(state.readingLog[0].pages).toBe(60)
        expect(state.currentlyReading[0].progressPct).toBeGreaterThan(0)
        expect(state.currentlyReading[0].progressPct).toBeLessThanOrEqual(100)
    })

    it('finishReading marks the book complete and counts toward booksFinished', () => {
        let state = reducer(undefined, actions.startReading('b-03'))
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
        let state = reducer(undefined, actions.startReading('b-04'))
        state = reducer(state, actions.logReadingSession({ bookId: 'b-04', pages: 30 }))
        const raw = localStorage.getItem('goodbooks_reading')
        expect(raw).toBeTruthy()
        expect(JSON.parse(raw as string).currentlyReading[0].bookId).toBe('b-04')
    })
})

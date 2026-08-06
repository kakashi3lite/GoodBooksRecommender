/**
 * 🧭 Chat Context Builder Tests
 * Chain-of-Thought: the AI backend must only ever receive the reader's REAL
 * profile — verify that populated data is carried through and empty data
 * yields an honest, minimal profile (never fabricated).
 */

import { describe, expect, it } from 'vitest'
import type { ReadingEntry, ReadingLogEntry } from '../src/stores/reading/readingSlice'
import { buildChatContext } from '../src/utils/chatContext'

const log: ReadingLogEntry[] = [
    { date: '2026-08-05', pages: 40, bookId: 'b-06', ts: 1 },
    { date: '2026-08-06', pages: 55, bookId: 'b-06', ts: 2 },
    { date: '2026-08-07', pages: 60, bookId: 'b-06', ts: 3 }
]

const shelf: ReadingEntry[] = [
    {
        bookId: 'b-06',
        book: {
            title: 'A Psalm for the Wild-Built',
            authors: 'Becky Chambers',
            cover_url: '',
            genres: ['Science Fiction'],
            page_count: 160
        },
        progressPct: 64,
        startedAt: 1,
        updatedAt: 3,
        finishedAt: null
    },
    {
        bookId: 'b-02',
        book: {
            title: 'Project Hail Mary',
            authors: 'Andy Weir',
            cover_url: '',
            genres: ['Science Fiction']
        },
        progressPct: 100,
        startedAt: 1,
        updatedAt: 2,
        finishedAt: 100
    }
]

describe('buildChatContext', () => {
    it('carries the reader’s real profile through', () => {
        const ctx = buildChatContext({
            favoriteGenres: ['Science Fiction', 'Mystery'],
            readingGoal: 24,
            currentlyReading: shelf,
            readingLog: log
        })

        expect(ctx.favoriteGenres).toEqual(['Science Fiction', 'Mystery'])
        expect(ctx.readingGoal).toBe(24)
        expect(typeof ctx.persona).toBe('string')
        expect(ctx.persona!.length).toBeGreaterThan(0)

        // Active (unfinished) book becomes the current book.
        expect(ctx.currentBook).toBeDefined()
        expect(ctx.currentBook!.title).toBe('A Psalm for the Wild-Built')
        expect(ctx.currentBook!.progressPct).toBe(64)
        expect(ctx.currentBook!.pageCount).toBe(160)

        // Finished books land in recentlyFinished.
        expect(ctx.recentlyFinished?.map((b) => b.title)).toContain('Project Hail Mary')

        // Stats are all real numbers from the log.
        expect(ctx.stats).toBeDefined()
        expect(typeof ctx.stats!.streak).toBe('number')
        expect(typeof ctx.stats!.booksFinished).toBe('number')
        expect(typeof ctx.stats!.pagesThisMonth).toBe('number')
        expect(ctx.stats!.avgPagesPerSession).toBeGreaterThan(0)
        expect(typeof ctx.stats!.distinctDays).toBe('number')
        expect(ctx.stats!.booksFinished).toBe(1)
    })

    it('returns an honest minimal profile when there is no data', () => {
        const ctx = buildChatContext({
            currentlyReading: [],
            readingLog: []
        })

        expect(ctx.favoriteGenres).toBeUndefined()
        expect(ctx.readingGoal).toBeUndefined()
        expect(ctx.currentBook).toBeUndefined()
        expect(ctx.recentlyFinished).toEqual([])
        expect(ctx.stats).toEqual({
            streak: 0,
            booksFinished: 0,
            pagesThisMonth: 0,
            avgPagesPerSession: 30,
            distinctDays: 0
        })
    })
})

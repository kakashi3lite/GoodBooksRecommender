/**
 * 🧭 Chat Context Builder — sends the reader's REAL profile to the AI backend.
 * Chain-of-Thought: the LLM can only personalize when it sees the reader's
 * actual data. Everything here derives from the persisted reading log + user
 * preferences — no fabricated numbers, ever. If a section has no real data
 * it is simply omitted.
 */

import { BOOK_CATALOG } from '../data/bookCatalog'
import {
    type ReadingEntry,
    type ReadingLogEntry,
    booksFinished,
    computeStreak,
    pagesThisMonth
} from '../stores/reading/readingSlice'
import { computePace, distinctReadingDays, personaOf } from './readingInsights'

export interface ChatContext {
    favoriteGenres?: string[]
    readingGoal?: number
    persona?: string
    currentBook?: {
        title: string
        authors: string
        progressPct: number
        pageCount?: number
    }
    stats?: {
        streak: number
        booksFinished: number
        pagesThisMonth: number
        avgPagesPerSession: number
        distinctDays: number
    }
    recentlyFinished?: Array<{ title: string; authors: string; genres?: string[] }>
}

export interface ChatContextInput {
    favoriteGenres?: string[]
    readingGoal?: number
    currentlyReading: ReadingEntry[]
    readingLog: ReadingLogEntry[]
}

/** Resolve a shelf entry's book snapshot (snapshot first, catalog fallback). */
const bookOf = (entry: ReadingEntry) =>
    entry.book ?? BOOK_CATALOG.find((b) => b.id === entry.bookId)

/**
 * Build the reader's real profile for the AI backend. Only sections with
 * actual data are populated; the stats block always carries the true numbers
 * (which may be 0 for a brand-new reader).
 */
export const buildChatContext = (input: ChatContextInput): ChatContext => {
    const active = input.currentlyReading.find((e) => !e.finishedAt)
    const finished = input.currentlyReading.filter((e) => e.finishedAt)
    const log = input.readingLog

    const streak = computeStreak(log)
    const finishedCount = booksFinished(input.currentlyReading)
    const monthPages = pagesThisMonth(log)
    const pace = computePace(log)
    const distinct = distinctReadingDays(log)
    const persona = personaOf(pace.avgPagesPerSession, distinct, finishedCount)

    const activeBook = active ? bookOf(active) : undefined

    return {
        favoriteGenres:
            input.favoriteGenres && input.favoriteGenres.length > 0
                ? input.favoriteGenres
                : undefined,
        readingGoal:
            input.readingGoal && input.readingGoal > 0 ? input.readingGoal : undefined,
        persona,
        currentBook:
            active && activeBook
                ? {
                    title: activeBook.title,
                    authors: activeBook.authors,
                    progressPct: active.progressPct,
                    pageCount: activeBook.page_count
                }
                : undefined,
        stats: {
            streak,
            booksFinished: finishedCount,
            pagesThisMonth: monthPages,
            avgPagesPerSession: pace.avgPagesPerSession,
            distinctDays: distinct
        },
        recentlyFinished: finished.slice(-5).map((e) => {
            const b = bookOf(e)
            return { title: b?.title ?? e.bookId, authors: b?.authors ?? '', genres: b?.genres }
        })
    }
}

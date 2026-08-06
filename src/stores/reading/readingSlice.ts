/**
 * 📚 Reading Activity Slice — the user's real, persisted reading life
 * Chain-of-Thought: this converts the app from a "demo dashboard" into a real
 * personal reading tracker. Every number on screen (Dashboard stats, sidebar
 * badges, streak, goal progress, Currently Reading, Notes, Analytics) derives
 * from this data — nothing is hardcoded.
 *
 * Memory: persisted to localStorage (per browser). When the Supabase schema is
 * applied, this syncs to the DB via the existing account layer.
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit'

export interface ReadingEntry {
    bookId: string
    /** 0..100 reading progress */
    progressPct: number
    startedAt: number
    updatedAt: number
    finishedAt: number | null
}

export interface ReadingLogEntry {
    /** YYYY-MM-DD local date */
    date: string
    pages: number
    bookId: string
    ts: number
}

export interface Note {
    id: string
    bookId?: string
    text: string
    createdAt: number
    updatedAt: number
}

export interface ReadingState {
    currentlyReading: ReadingEntry[]
    readingLog: ReadingLogEntry[]
    notes: Note[]
}

// ─── Persistence ─────────────────────────────────────────────────────────────

const STORAGE_KEY = 'goodbooks_reading'

const EMPTY: ReadingState = {
    currentlyReading: [],
    readingLog: [],
    notes: []
}

const restore = (): ReadingState => {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (!raw) return EMPTY
        const parsed = JSON.parse(raw) as Partial<ReadingState>
        return {
            currentlyReading: parsed.currentlyReading ?? [],
            readingLog: parsed.readingLog ?? [],
            notes: parsed.notes ?? []
        }
    } catch {
        return EMPTY
    }
}

const persist = (state: ReadingState): void => {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
    } catch {
        // localStorage unavailable — in-memory only.
    }
}

const todayKey = (): string => new Date().toISOString().slice(0, 10)

// ─── Derived helpers (pure, exported for selectors + tests) ─────────────────

/** Consecutive-day reading streak (0 if none; counts today or yesterday as active). */
export const computeStreak = (log: ReadingLogEntry[]): number => {
    if (log.length === 0) return 0
    const days = new Set(log.map((e) => e.date))
    const toKey = (d: Date) => d.toISOString().slice(0, 10)

    // Anchor: today or yesterday (so a streak survives a missed end-of-day).
    const cursor = new Date()
    if (!days.has(toKey(cursor))) {
        cursor.setDate(cursor.getDate() - 1)
        if (!days.has(toKey(cursor))) return 0
    }
    let streak = 0
    while (days.has(toKey(cursor))) {
        streak += 1
        cursor.setDate(cursor.getDate() - 1)
    }
    return streak
}

export const pagesThisMonth = (log: ReadingLogEntry[]): number => {
    const prefix = new Date().toISOString().slice(0, 7)
    return log.filter((e) => e.date.startsWith(prefix)).reduce((s, e) => s + e.pages, 0)
}

export const pagesAllTime = (log: ReadingLogEntry[]): number =>
    log.reduce((s, e) => s + e.pages, 0)

export const booksFinished = (entries: ReadingEntry[]): number =>
    entries.filter((e) => e.finishedAt !== null).length

// ─── Slice ───────────────────────────────────────────────────────────────────

const initialState: ReadingState = restore()

const readingSlice = createSlice({
    name: 'reading',
    initialState,
    reducers: {
        /** Add a book to the active shelf at 0%. */
        startReading: (state, action: PayloadAction<string>) => {
            const bookId = action.payload
            if (state.currentlyReading.some((e) => e.bookId === bookId)) return
            const now = Date.now()
            state.currentlyReading.push({
                bookId,
                progressPct: 0,
                startedAt: now,
                updatedAt: now,
                finishedAt: null
            })
            persist(state)
        },

        /**
         * Log a real reading session (pages) and advance the book's progress.
         * A session also feeds the daily log (streak + analytics).
         */
        logReadingSession: (
            state,
            action: PayloadAction<{ bookId: string; pages: number }>
        ) => {
            const { bookId, pages } = action.payload
            const entry = state.currentlyReading.find((e) => e.bookId === bookId)
            const now = Date.now()

            state.readingLog.push({ date: todayKey(), pages, bookId, ts: now })
            // Keep the log bounded (last 1000 sessions).
            if (state.readingLog.length > 1000) state.readingLog = state.readingLog.slice(-1000)

            if (entry) {
                entry.progressPct = Math.min(100, entry.progressPct + Math.round((pages / 300) * 100))
                entry.updatedAt = now
            }
            persist(state)
        },

        /** Mark a book finished. */
        finishReading: (state, action: PayloadAction<string>) => {
            const entry = state.currentlyReading.find((e) => e.bookId === action.payload)
            if (entry) {
                entry.progressPct = 100
                entry.finishedAt = Date.now()
                entry.updatedAt = Date.now()
            }
            persist(state)
        },

        /** Remove a book from the active shelf (keep its history). */
        removeFromReading: (state, action: PayloadAction<string>) => {
            state.currentlyReading = state.currentlyReading.filter(
                (e) => e.bookId !== action.payload
            )
            persist(state)
        },

        addNote: (state, action: PayloadAction<{ bookId?: string; text: string }>) => {
            const now = Date.now()
            state.notes.unshift({
                id: `n-${now.toString(36)}`,
                bookId: action.payload.bookId,
                text: action.payload.text,
                createdAt: now,
                updatedAt: now
            })
            persist(state)
        },

        updateNote: (state, action: PayloadAction<{ id: string; text: string }>) => {
            const note = state.notes.find((n) => n.id === action.payload.id)
            if (note) {
                note.text = action.payload.text
                note.updatedAt = Date.now()
            }
            persist(state)
        },

        deleteNote: (state, action: PayloadAction<string>) => {
            state.notes = state.notes.filter((n) => n.id !== action.payload)
            persist(state)
        }
    }
})

export const {
    startReading,
    logReadingSession,
    finishReading,
    removeFromReading,
    addNote,
    updateNote,
    deleteNote
} = readingSlice.actions

export default readingSlice.reducer

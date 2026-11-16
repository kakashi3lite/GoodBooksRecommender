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

export interface ReadingBookSnapshot {
    title: string
    authors: string
    cover_url: string
    genres?: string[]
    published_year?: number
    page_count?: number
    description?: string
}

export interface ReadingEntry {
    bookId: string
    /** Snapshot taken at add-time so web-sourced books render on the shelf too. */
    book?: ReadingBookSnapshot
    /** 0..100 reading progress */
    progressPct: number
    /**
     * Furthest page reached (1-based, 0 = untouched). This is the honest
     * source of truth when the book's page count is known, so "X pages
     * left" and the progress bar can never disagree with each other.
     */
    currentPage?: number
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
    /** True for a day repaired by a streak recovery (0 pages, keeps the run alive). */
    recovered?: boolean
    /** True when this entry records "I finished a book today" (0 pages). */
    finished?: boolean
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
    /** Longest streak ever recorded — a private trophy, not a public score. */
    streakBest: number
    /** The missed date already repaired by a streak recovery (one per gap). */
    graceUsedFor: string | null
}

// ─── Persistence ─────────────────────────────────────────────────────────────

const STORAGE_KEY = 'goodbooks_reading'

const EMPTY: ReadingState = {
    currentlyReading: [],
    readingLog: [],
    notes: [],
    streakBest: 0,
    graceUsedFor: null
}

/**
 * Migrate a restored shelf entry to the current shape.
 *
 * Chain-of-Thought (loss aversion): progress is the one number a reader
 * invests in. Entries written before `currentPage` existed carry only
 * `progressPct`; treating a missing page as 0 meant the first session after
 * the upgrade recomputed progress from zero — a reader at 50% of a 400-page
 * book fell to ~2% after logging 10 pages. Deriving the page from the stored
 * percentage preserves what they earned.
 */
const migrateEntry = (entry: ReadingEntry): ReadingEntry => {
    const pageCount = entry.book?.page_count ?? 0
    if (entry.currentPage === undefined && pageCount > 0 && entry.progressPct > 0) {
        return {
            ...entry,
            currentPage: Math.min(pageCount, Math.round((entry.progressPct / 100) * pageCount))
        }
    }
    return entry
}

const asArray = <T,>(value: unknown): T[] => (Array.isArray(value) ? (value as T[]) : [])

const restore = (): ReadingState => {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (!raw) return EMPTY
        const parsed = JSON.parse(raw) as Partial<ReadingState>
        const stored = asArray<ReadingEntry>(parsed.currentlyReading)
        // `migrateEntry` returns the same object when nothing needed fixing, so
        // identity tells us whether a repair happened without diffing fields.
        const repaired = { any: false }
        const currentlyReading = stored.map((entry) => {
            const migrated = migrateEntry(entry)
            if (migrated !== entry) repaired.any = true
            return migrated
        })
        const restored: ReadingState = {
            // `asArray` keeps a corrupt payload (or a hand-edited one) from
            // white-screening the app on the very first render.
            currentlyReading,
            readingLog: asArray<ReadingLogEntry>(parsed.readingLog),
            notes: asArray<Note>(parsed.notes),
            streakBest: parsed.streakBest ?? 0,
            graceUsedFor: parsed.graceUsedFor ?? null
        }
        // Migration is a repair, not a display trick: write it back so a reader
        // who opens the app and closes it without logging anything still has the
        // corrected page position next time.
        if (repaired.any) persist(restored)
        return restored
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

/**
 * Local YYYY-MM-DD date key.
 * Chain-of-Thought: the previous implementation used `toISOString()`, which
 * is UTC — so a 1 a.m. session in UTC+5:30 was filed under *yesterday*, and
 * the streak + "read today" pill disagreed with each other. Dates are a
 * human concept here, so they must be computed in the reader's local day.
 */
export const localDateKey = (d: Date = new Date()): string => {
    const month = `${d.getMonth() + 1}`.padStart(2, '0')
    const day = `${d.getDate()}`.padStart(2, '0')
    return `${d.getFullYear()}-${month}-${day}`
}

const dayKey = (d: Date): string => localDateKey(d)

/** Shift a date key by N days (negative = past). */
const shiftKey = (from: Date, days: number): string => {
    const d = new Date(from)
    d.setDate(d.getDate() + days)
    return dayKey(d)
}

// ─── Derived helpers (pure, exported for selectors + tests) ─────────────────

/** Consecutive-day reading streak (0 if none; counts today or yesterday as active). */
export const computeStreak = (log: ReadingLogEntry[], now: Date = new Date()): number => {
    if (log.length === 0) return 0
    const days = new Set(log.map((e) => e.date))

    // Anchor: today or yesterday (so a streak survives a missed end-of-day).
    const cursor = new Date(now)
    if (!days.has(dayKey(cursor))) {
        cursor.setDate(cursor.getDate() - 1)
        if (!days.has(dayKey(cursor))) return 0
    }
    let streak = 0
    while (days.has(dayKey(cursor))) {
        streak += 1
        cursor.setDate(cursor.getDate() - 1)
    }
    return streak
}

/** Longest run of consecutive reading days in the log. */
export const bestStreak = (log: ReadingLogEntry[]): number => {
    const days = Array.from(new Set(log.map((e) => e.date))).sort()
    let best = 0
    let run = 0
    let previous: Date | null = null
    for (const key of days) {
        const current = new Date(`${key}T00:00:00`)
        if (previous && shiftKey(previous, 1) === key) {
            run += 1
        } else {
            run = 1
        }
        best = Math.max(best, run)
        previous = current
    }
    return best
}

export interface StreakRisk {
    /** The streak that was alive before the missed day (0 when nothing at risk). */
    brokenStreak: number
    /** The missed local date that a recovery would repair. */
    missedDate: string | null
}

/**
 * Detect a single missed day that is still repairable.
 * Chain-of-Thought (recovery-first habit design): streaks motivate through
 * loss aversion, which also makes a break feel like a reason to quit. Instead
 * of a punitive reset we offer ONE honest repair per gap — the reader keeps
 * the identity ("I'm a streak reader"), and we never fabricate activity.
 * A recovery is only offered when one day was missed (not weeks), so it
 * stays believable and the analytics stay truthful.
 */
export const streakAtRisk = (log: ReadingLogEntry[], now: Date = new Date()): StreakRisk => {
    const days = new Set(log.map((e) => e.date))
    if (days.has(shiftKey(now, 0)) || days.has(shiftKey(now, -1))) {
        return { brokenStreak: 0, missedDate: null }
    }
    // Most recent active day must be exactly two days ago.
    if (!days.has(shiftKey(now, -2))) return { brokenStreak: 0, missedDate: null }

    let broken = 0
    for (let offset = 2; offset < 400; offset += 1) {
        if (!days.has(shiftKey(now, -offset))) break
        broken += 1
    }
    return broken >= 3 ? { brokenStreak: broken, missedDate: shiftKey(now, -1) } : { brokenStreak: 0, missedDate: null }
}

export const pagesThisMonth = (log: ReadingLogEntry[]): number => {
    const prefix = localDateKey().slice(0, 7)
    return log.filter((e) => e.date.startsWith(prefix)).reduce((s, e) => s + e.pages, 0)
}

export const pagesAllTime = (log: ReadingLogEntry[]): number =>
    log.reduce((s, e) => s + e.pages, 0)

export const booksFinished = (entries: ReadingEntry[]): number =>
    entries.filter((e) => e.finishedAt !== null).length

/** Pages read for one book (recovered streak days carry 0 pages). */
export const pagesReadFor = (log: ReadingLogEntry[], bookId: string): number =>
    log.filter((l) => l.bookId === bookId).reduce((a, l) => a + l.pages, 0)

/** Honest progress percentage for a shelf entry. */
export const progressOf = (entry: ReadingEntry): number => {
    const pageCount = entry.book?.page_count ?? 0
    if (pageCount > 0) {
        return Math.min(100, Math.round(((entry.currentPage ?? 0) / pageCount) * 100))
    }
    return entry.progressPct
}

/** Pages left for a shelf entry (null when the length is unknown). */
export const pagesLeftOf = (entry: ReadingEntry): number | null => {
    const pageCount = entry.book?.page_count ?? 0
    if (pageCount <= 0) return null
    return Math.max(0, pageCount - (entry.currentPage ?? 0))
}

// ─── Slice ───────────────────────────────────────────────────────────────────

const initialState: ReadingState = restore()

const readingSlice = createSlice({
    name: 'reading',
    initialState,
    reducers: {
        /** Add a book to the active shelf at 0%. Snapshot the book at add-time
         * so catalog AND web-sourced books both resolve on the shelf later. */
        startReading: (state, action: PayloadAction<{ bookId: string; book?: ReadingBookSnapshot }>) => {
            const { bookId, book } = action.payload
            if (state.currentlyReading.some((e) => e.bookId === bookId)) return
            const now = Date.now()
            state.currentlyReading.push({
                bookId,
                book,
                progressPct: 0,
                currentPage: 0,
                startedAt: now,
                updatedAt: now,
                finishedAt: null
            })
            persist(state)
        },

        /**
         * Log a real reading session (pages) and advance the book's progress.
         * A session also feeds the daily log (streak + analytics).
         *
         * Chain-of-Thought: progress is derived from the book's REAL page count
         * (currentPage / page_count). The old fixed `/300` estimate made a
         * 688-page epic look 21% "done" after one session — the single fastest
         * way to lose a reader's trust in every other number on screen.
         */
        logReadingSession: (
            state,
            action: PayloadAction<{ bookId: string; pages: number }>
        ) => {
            const { bookId } = action.payload
            const entry = state.currentlyReading.find((e) => e.bookId === bookId)
            const now = Date.now()

            // A finished book accepts no more sessions: a stray tap on the
            // shelf used to add pages — and "pages this month" — forever.
            if (entry?.finishedAt) return

            const pageCount = entry?.book?.page_count ?? 0
            const readSoFar = entry?.currentPage ?? 0
            const remaining = pageCount > 0 ? Math.max(0, pageCount - readSoFar) : Number.POSITIVE_INFINITY

            // Clamp to what the book can still absorb. Logging 120 pages of a
            // 160-page book already at page 100 recorded 120 pages against the
            // reader's monthly total and permanently inflated their pace.
            const pages = Math.min(Math.max(0, Math.round(action.payload.pages)), remaining)
            if (!Number.isFinite(pages) || pages <= 0) {
                if (entry && pageCount > 0) entry.updatedAt = now
                return
            }

            state.readingLog.push({ date: localDateKey(), pages, bookId, ts: now })
            // Keep the log bounded (last 1000 sessions).
            if (state.readingLog.length > 1000) state.readingLog = state.readingLog.slice(-1000)

            if (entry) {
                entry.currentPage = pageCount > 0 ? Math.min(pageCount, readSoFar + pages) : readSoFar + pages
                entry.progressPct =
                    pageCount > 0
                        ? Math.min(100, Math.round((entry.currentPage / pageCount) * 100))
                        : Math.min(100, entry.progressPct + Math.round((pages / 300) * 100))
                entry.updatedAt = now
            }
            state.streakBest = Math.max(state.streakBest, bestStreak(state.readingLog))
            persist(state)
        },

        /**
         * "I'm on page N" — the zero-friction check-in.
         * Chain-of-Thought: asking for a position (not a delta) matches how
         * readers actually hold a book ("I'm at chapter 9") and removes mental
         * arithmetic. The delta from the previous position is still logged as
         * a real session, so streaks and analytics stay honest.
         */
        setProgress: (
            state,
            action: PayloadAction<{ bookId: string; page: number }>
        ) => {
            const { bookId } = action.payload
            const entry = state.currentlyReading.find((e) => e.bookId === bookId)
            if (!entry) return

            const pageCount = entry.book?.page_count ?? 0
            const requested = Math.max(0, Math.round(action.payload.page))
            // Clamp *before* measuring the delta. Using the raw request let a
            // fat-fingered "999" on a 288-page book log 855 pages read while the
            // saved page said 288 — the reader's monthly totals, goal and pace
            // all inflated from one typo.
            const target = pageCount > 0 ? Math.min(pageCount, requested) : requested
            const previous = entry.currentPage ?? 0
            const delta = target - previous
            const now = Date.now()

            if (delta > 0) {
                state.readingLog.push({ date: localDateKey(), pages: delta, bookId, ts: now })
                if (state.readingLog.length > 1000) state.readingLog = state.readingLog.slice(-1000)
            }

            entry.currentPage = target
            if (pageCount > 0) {
                entry.progressPct = Math.min(
                    100,
                    Math.round((entry.currentPage / pageCount) * 100)
                )
            }
            entry.updatedAt = now
            state.streakBest = Math.max(state.streakBest, bestStreak(state.readingLog))
            persist(state)
        },

        /**
         * Repair a single missed day, once per gap.
         * Chain-of-Thought: recovery-first, not punitive. A 0-page entry keeps
         * the run alive without inventing pages read, so the analytics remain
         * truthful and the reader keeps their identity as a streak reader.
         */
        restoreStreak: (state, action: PayloadAction<{ missedDate: string }>) => {
            const { missedDate } = action.payload
            if (!missedDate) return
            if (state.graceUsedFor === missedDate) return
            if (state.readingLog.some((e) => e.date === missedDate)) return
            state.readingLog.push({
                date: missedDate,
                pages: 0,
                bookId: 'streak-recovery',
                ts: Date.now(),
                recovered: true
            })
            state.graceUsedFor = missedDate
            state.streakBest = Math.max(state.streakBest, bestStreak(state.readingLog))
            persist(state)
        },

        /** Mark a missed gap as consciously let go — the banner won't nag again.
         * Chain-of-Thought: "start fresh" is a legitimate choice. Remembering it
         * respects the reader's decision instead of re-offering the same repair. */
        dismissStreakRecovery: (state, action: PayloadAction<{ missedDate: string }>) => {
            if (!action.payload.missedDate) return
            state.graceUsedFor = action.payload.missedDate
            persist(state)
        },

        /**
         * Mark a book finished.
         *
         * Chain-of-Thought: finishing is the emotional peak of the habit loop —
         * and it used to earn no streak credit at all. A reader who closed a
         * book at 11pm without logging a page saw their run break on the
         * biggest day of the week. We record a 0-page `finished` marker (only
         * when nothing else is logged for that book today) so the streak
         * counts the day while the page totals stay truthful.
         */
        finishReading: (state, action: PayloadAction<string>) => {
            const entry = state.currentlyReading.find((e) => e.bookId === action.payload)
            if (!entry || entry.finishedAt) return

            const now = Date.now()
            entry.progressPct = 100
            entry.currentPage = entry.book?.page_count ?? entry.currentPage
            entry.finishedAt = now
            entry.updatedAt = now

            const today = localDateKey()
            // Dedupe on a *finish* credit, not on any activity: a reader who
            // logged pages this morning and finished the book tonight used to
            // lose the finish entirely (the day's streak survived, the "I
            // finished a book" moment did not).
            const alreadyCredited = state.readingLog.some(
                (logEntry) => logEntry.date === today && logEntry.bookId === entry.bookId && logEntry.finished
            )
            if (!alreadyCredited) {
                state.readingLog.push({
                    date: today,
                    pages: 0,
                    bookId: entry.bookId,
                    ts: now,
                    finished: true
                })
            }
            state.streakBest = Math.max(state.streakBest, bestStreak(state.readingLog))
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
    setProgress,
    restoreStreak,
    dismissStreakRecovery,
    finishReading,
    removeFromReading,
    addNote,
    updateNote,
    deleteNote
} = readingSlice.actions

export default readingSlice.reducer

/**
 * 🔁 Reading sync middleware
 *
 * Chain-of-Thought:
 *   Reading actions happen in reducers (sync, pure). Persisting them must not
 *   make the reducers async, and no component should have to remember to call
 *   a repository — one forgotten call means silently missing data. A slice of
 *   middleware is the right seam: every `started / progress / finished` action
 *   is mirrored exactly once, after the state has been updated.
 *
 *   Dispatch is never blocked and failures are ignored (the local write is the
 *   source of truth). When no database is configured the middleware short-
 *   circuits before touching the network.
 */

import { type Middleware } from '@reduxjs/toolkit'
import { isReadingSyncEnabled, syncReadingEvent } from '../../lib/readingRepository'
import {
    finishReading,
    logReadingSession,
    setProgress,
    startReading,
    type ReadingState
} from './readingSlice'

interface RootLike {
    reading: ReadingState
}

const entryOf = (state: RootLike, bookId: string) =>
    state.reading.currentlyReading.find((entry) => entry.bookId === bookId)

export const createReadingSyncMiddleware = (): Middleware => (store) => (next) => (action) => {
    const result = next(action)

    if (!isReadingSyncEnabled()) return result

    const typed = action as { type?: string; payload?: unknown }
    const state = store.getState() as RootLike

    if (typed.type === startReading.type) {
        const { bookId } = typed.payload as { bookId: string }
        void syncReadingEvent({ event_type: 'started', book_id: bookId, progress: 0 })
        return result
    }

    if (typed.type === logReadingSession.type || typed.type === setProgress.type) {
        const { bookId } = typed.payload as { bookId: string }
        const entry = entryOf(state, bookId)
        const payload = typed.payload as { pages?: number }
        void syncReadingEvent({
            event_type: 'progress',
            book_id: bookId,
            pages: typeof payload.pages === 'number' ? payload.pages : undefined,
            page: entry?.currentPage,
            progress: entry?.progressPct,
            session_date: new Date().toISOString().slice(0, 10)
        })
        return result
    }

    if (typed.type === finishReading.type) {
        const bookId = typed.payload as string
        void syncReadingEvent({ event_type: 'finished', book_id: bookId, progress: 100 })
        return result
    }

    return result
}

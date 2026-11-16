/**
 * 🗄️ Reading Repository — durable reading events with graceful degradation
 *
 * Chain-of-Thought:
 *   The reader's shelf is local-first (localStorage → readingSlice): instant,
 *   private, works offline. This module mirrors real events to the edge API so
 *   the same data can outlive a single browser and feed analytics later.
 *
 *   It is deliberately *best-effort*:
 *     - no Supabase configured → no network call at all (zero cost, no errors)
 *     - network failure         → swallowed, the local action already succeeded
 *     - never blocks a reducer  → the UI never waits on analytics
 *
 *   `client_id` is a random UUID stored on the device. It groups a reader's
 *   own events without collecting an email, name, or any personal identifier.
 */

import { API_BASE_URL } from '../utils/api'

const CLIENT_ID_KEY = 'goodbooks_client_id'

export type ReadingEventType = 'started' | 'progress' | 'finished' | 'wishlisted'

export interface ReadingEventPayload {
    event_type: ReadingEventType
    book_id: string
    pages?: number
    page?: number
    progress?: number
    session_date?: string
}

/**
 * Stable, anonymous device id (UUID v4). Falls back to a manual generator on
 * insecure origins where `crypto.randomUUID` is unavailable.
 */
export const getClientId = (): string | null => {
    if (typeof window === 'undefined') return null
    try {
        const existing = window.localStorage.getItem(CLIENT_ID_KEY)
        if (existing) return existing
        const uuid =
            typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
                ? crypto.randomUUID()
                : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
                    const random = (Math.random() * 16) | 0
                    const value = char === 'x' ? random : (random & 0x3) | 0x8
                    return value.toString(16)
                })
        window.localStorage.setItem(CLIENT_ID_KEY, uuid)
        return uuid
    } catch {
        return null
    }
}

/**
 * Opt-in gate: only talk to the server when the project actually has a
 * database configured. This keeps dev/test/prerender completely silent.
 */
export const isReadingSyncEnabled = (): boolean =>
    Boolean(import.meta.env.VITE_SUPABASE_URL)

/** POST one reading event. Resolves false on any failure — never throws. */
export const syncReadingEvent = async (event: ReadingEventPayload): Promise<boolean> => {
    if (!isReadingSyncEnabled()) return false
    const clientId = getClientId()
    if (!clientId) return false

    try {
        const response = await fetch(`${API_BASE_URL}/api/reading`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ client_id: clientId, ...event }),
            // Analytics must never keep the page alive.
            keepalive: true
        })
        if (!response.ok) return false
        const data = (await response.json()) as { stored?: boolean }
        return Boolean(data.stored)
    } catch {
        return false
    }
}

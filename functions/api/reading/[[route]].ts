/**
 * 📖 /api/reading — durable reading activity (edge)
 *
 *   POST /api/reading
 *     body: {
 *       client_id: string,                     // random UUID kept in localStorage
 *       event_type: 'started' | 'progress' | 'finished' | 'wishlisted',
 *       book_id: string,
 *       pages?: number,                        // session delta (progress only)
 *       page?: number,                         // absolute position, when known
 *       progress?: number,                     // 0..100
 *       session_date?: string                  // YYYY-MM-DD (reader's local day)
 *     }
 *     → { stored: true } | { stored: false, reason: 'not_configured' | 'invalid' }
 *
 * Why this exists
 *   Reading progress is the product's north-star data (finish a book). Today
 *   it lives in the reader's browser (localStorage → readingSlice). This route
 *   mirrors each real event into Postgres when the database is configured, so
 *   the data survives a device change and the recommender eventually has the
 *   interaction history it needs to graduate from TF-IDF to collaborative
 *   filtering (see docs/DATA_LAYER.md).
 *
 * Privacy contract
 *   - Writes only. There is deliberately NO public read endpoint: the browser
 *     is the owner of its reading data. Any future restore flow must be an
 *     explicit, opt-in action.
 *   - `client_id` is a random UUID generated in the browser; it is not derived
 *     from any personal identifier.
 *   - The service-role key stays server-side; the browser never sees it.
 *   - When the DB is not configured the route is a clean no-op (200), so the
 *     app keeps working offline-first.
 */
import { type PagesEnv, type PagesFunction } from '../_lib/types'

const EVENT_TYPES = new Set(['started', 'progress', 'finished', 'wishlisted'])

const json = (data: unknown, status = 200): Response =>
    new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'X-Content-Type-Options': 'nosniff'
        }
    })

/** Trim + clamp any incoming string so a malformed body can't bloat a row. */
const clean = (value: unknown, max = 128): string =>
    typeof value === 'string' ? value.trim().slice(0, max) : ''

const toInt = (value: unknown, min: number, max: number): number => {
    const n = typeof value === 'number' ? value : Number(value)
    if (!Number.isFinite(n)) return 0
    return Math.max(min, Math.min(max, Math.round(n)))
}

interface ReadingEventInput {
    client_id?: unknown
    event_type?: unknown
    book_id?: unknown
    pages?: unknown
    page?: unknown
    progress?: unknown
    session_date?: unknown
}

export const onRequestPost: PagesFunction<PagesEnv> = async (context) => {
    const { request, env } = context

    let body: ReadingEventInput
    try {
        body = (await request.json()) as ReadingEventInput
    } catch {
        return json({ stored: false, reason: 'invalid', message: 'Expected a JSON body' }, 400)
    }

    const clientId = clean(body.client_id, 64)
    const eventType = clean(body.event_type, 24)
    const bookId = clean(body.book_id, 128)

    // `client_id` must look like a UUID — it is the only tenant separator we
    // have, so a weak/empty value would let events collide across readers.
    const isUuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(clientId)
    if (!isUuid || !EVENT_TYPES.has(eventType) || !bookId) {
        return json({ stored: false, reason: 'invalid' }, 400)
    }

    if (!env.SUPABASE_URL || !env.SUPABASE_SERVICE_ROLE_KEY) {
        // Offline-first: nothing to do, but the client should not treat this as an error.
        return json({ stored: false, reason: 'not_configured' })
    }

    const sessionDate = clean(body.session_date, 10)
    const row = {
        client_id: clientId,
        book_id: bookId,
        event_type: eventType,
        pages: toInt(body.pages, 0, 5000),
        page: body.page === undefined ? null : toInt(body.page, 0, 100000),
        progress: toInt(body.progress, 0, 100),
        session_date: /^\d{4}-\d{2}-\d{2}$/.test(sessionDate) ? sessionDate : null,
        created_at: new Date().toISOString()
    }

    try {
        const res = await fetch(`${env.SUPABASE_URL}/rest/v1/reading_events`, {
            method: 'POST',
            headers: {
                apikey: env.SUPABASE_SERVICE_ROLE_KEY,
                Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
                'Content-Type': 'application/json',
                Prefer: 'return=minimal'
            },
            body: JSON.stringify(row)
        })
        if (!res.ok) {
            return json({ stored: false, reason: 'db_error' })
        }
        return json({ stored: true })
    } catch {
        // Never fail the reader's action because analytics could not be saved.
        return json({ stored: false, reason: 'db_error' })
    }
}

/** GET is intentionally unsupported (privacy: no public reads). */
export const onRequestGet: PagesFunction<PagesEnv> = async () =>
    json(
        {
            error: 'method_not_allowed',
            message: 'Reading data is write-only. Restore flows must be explicit.'
        },
        405
    )

/**
 * 🗄️ Server-side Data Layer (Supabase REST)
 * Chain-of-Thought: The Pages Function reads live data from Supabase Postgres
 * when configured, and falls back to the embedded curated catalog otherwise —
 * so the API is always real and becomes database-backed the moment
 * SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set on the Pages project.
 *
 * Security: only the service-role key is used here (server-side, never shipped
 * to the browser). The browser uses the anon key for auth + RLS-scoped reads.
 */
import { type Book, BOOK_CATALOG } from './catalog'

interface Env {
    SUPABASE_URL?: string
    SUPABASE_SERVICE_ROLE_KEY?: string
    SUPABASE_ANON_KEY?: string
}

/**
 * Configured when we have a URL plus at least one key. The service-role key is
 * preferred (full access); the anon/publishable key also works for reading
 * public tables (books has a public SELECT policy).
 */
export const isDbConfigured = (env: Env): boolean =>
    Boolean(env.SUPABASE_URL && (env.SUPABASE_SERVICE_ROLE_KEY || env.SUPABASE_ANON_KEY))

const authHeaders = (env: Env): Record<string, string> => {
    const key = env.SUPABASE_SERVICE_ROLE_KEY ?? env.SUPABASE_ANON_KEY ?? ''
    return {
        apikey: key,
        Authorization: `Bearer ${key}`
    }
}

interface SupabaseRow {
    id: string
    title: string
    authors: string
    cover_url?: string | null
    rating?: number | null
    ratings_count?: number | null
    genres?: string[] | null
    moods?: string[] | null
    published_year?: number | null
    page_count?: number | null
    description?: string | null
}

const mapRow = (row: SupabaseRow): Book => ({
    id: row.id,
    title: row.title,
    authors: row.authors,
    cover_url: row.cover_url ?? '',
    rating: row.rating ?? 0,
    ratingsCount: row.ratings_count ?? 0,
    genres: row.genres ?? [],
    moods: row.moods ?? [],
    published_year: row.published_year ?? 0,
    page_count: row.page_count ?? 0,
    description: row.description ?? ''
})

/** Fetch the full live catalog from Supabase; null when unconfigured. */
export const fetchBooks = async (env: Env): Promise<Book[] | null> => {
    if (!isDbConfigured(env)) return null
    try {
        const res = await fetch(
            `${env.SUPABASE_URL}/rest/v1/books?select=*&order=rating.desc`,
            { headers: authHeaders(env) }
        )
        if (!res.ok) return null
        const rows = (await res.json()) as SupabaseRow[]
        if (!Array.isArray(rows) || rows.length === 0) return null
        return rows.map(mapRow)
    } catch {
        return null
    }
}

/**
 * Best-effort catalog: live DB first, embedded catalog as fallback.
 * Returns both so callers can report the data source.
 */
export const loadCatalog = async (
    env: Env
): Promise<{ books: Book[]; source: 'database' | 'catalog' }> => {
    const dbBooks = await fetchBooks(env)
    if (dbBooks) return { books: dbBooks, source: 'database' }
    return { books: BOOK_CATALOG, source: 'catalog' }
}

/**
 * Record a recommendation event (audit + future evaluation data).
 * Fire-and-forget; never blocks the response and never fails the request.
 * Only the service-role key can write — anon key skips silently.
 */
export const logRecommendation = async (
    env: Env,
    entry: {
        user_id?: string
        strategy: string
        book_ids: string[]
        context?: string
    }
): Promise<void> => {
    if (!env.SUPABASE_SERVICE_ROLE_KEY || !env.SUPABASE_URL) return
    try {
        await fetch(`${env.SUPABASE_URL}/rest/v1/recommendations_log`, {
            method: 'POST',
            headers: {
                apikey: env.SUPABASE_SERVICE_ROLE_KEY,
                Authorization: `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
                'Content-Type': 'application/json',
                Prefer: 'return=minimal'
            },
            body: JSON.stringify({
                ...entry,
                created_at: new Date().toISOString()
            })
        })
    } catch {
        // Best-effort logging — ignore failures.
    }
}

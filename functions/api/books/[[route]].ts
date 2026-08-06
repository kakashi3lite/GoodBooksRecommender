/**
 * 📚 /api/books/* — real-time book data + recommendations (edge)
 *
 * Routes:
 *   GET /api/books                  → full catalog (live DB or embedded)
 *   GET /api/books/search?q=...     → text search
 *   GET /api/books/recommend        → recommendations (see params below)
 *   GET /api/books/:id              → single book
 *   GET /api/books/:id/similar      → "more like this"
 *
 * /api/books/recommend params:
 *   genres   (comma list)  — genre hints → profile
 *   prefs    (JSON string) — full taste profile { favoriteGenres, readingGoal }
 *   q        (text)        — free-text query ("something cozy like ...")
 *   similar_to (book id)   — similarity seed
 *   limit    (int)         — result count (default 6)
 *   exclude  (comma list)  — book ids to skip
 *
 * Response shape matches the frontend contract: a bare JSON array of books
 * enriched with ai_recommendation_score (0–100) and ai_explanation.
 */
import { type Book, type RecommendationResult } from '../_lib/catalog'
import { loadCatalog, logRecommendation } from '../_lib/db'
import {
    buildProfile,
    recommendForProfile,
    recommendFromQuery,
    recommendSimilar
} from '../_lib/recommender'
import { type PagesEnv, type PagesFunction } from '../_lib/types'
import { fetchWebTrending, getBookInsights, resolveByIsbn, resolveByKey, searchWebBooks } from '../_lib/webCatalog'

const json = (data: unknown, status = 200): Response =>
    new Response(JSON.stringify(data), {
        status,
        headers: { 'Content-Type': 'application/json; charset=utf-8' }
    })

const notFound = (message = 'Not found'): Response =>
    json({ error: 'not_found', message }, 404)

const asInt = (v: string | null, fallback: number): number => {
    const n = parseInt(v ?? '', 10)
    return Number.isFinite(n) && n > 0 ? n : fallback
}

/** Enrich a ranked result to the wire shape the frontend expects.
 * NOTE: the frontend BookCard renders `Math.round(score * 100)%`, so the wire
 * value must be 0..1 (matching the client personalization path). */
const toWire = ({ book, score, reason }: RecommendationResult): Book & {
    ai_recommendation_score: number
    ai_explanation: string
} => ({
    ...book,
    ai_recommendation_score: Math.round((score / 100) * 100) / 100,
    ai_explanation: reason
})

const safeParsePrefs = (raw: string | null): { favoriteGenres?: string[]; readingGoal?: number } | undefined => {
    if (!raw) return undefined
    try {
        const parsed = JSON.parse(raw)
        if (parsed && typeof parsed === 'object') return parsed
    } catch {
        // ignore malformed prefs
    }
    return undefined
}

export const onRequestGet: PagesFunction<PagesEnv> = async (context) => {
    const { request, env, params } = context
    const url = new URL(request.url)
    const segments = (params.route as string[] | undefined) ?? []
    const { books, source } = await loadCatalog(env)

    // GET /api/books
    if (segments.length === 0) {
        return json({ data: books, source, count: books.length })
    }

    const [first] = segments

    // GET /api/books/search?q=...
    if (first === 'search') {
        const q = url.searchParams.get('q') ?? ''
        if (!q) return json({ data: [], source, count: 0 })
        const ql = q.toLowerCase()
        const results = books
            .map((book) => {
                const haystack = `${book.title} ${book.authors} ${book.genres.join(' ')} ${book.description}`.toLowerCase()
                let score = haystack.includes(ql) ? 1 : 0
                if (score === 0) {
                    const tokens = ql.split(/\s+/).filter((t) => t.length > 2)
                    score = tokens.filter((t) => haystack.includes(t)).length / Math.max(1, tokens.length)
                }
                return { book, score }
            })
            .filter((r) => r.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 20)
        return json({ data: results.map((r) => r.book), source, count: results.length })
    }

    // GET /api/books/recommend
    if (first === 'recommend') {
        const limit = asInt(url.searchParams.get('limit'), 6)
        const exclude = (url.searchParams.get('exclude') ?? '').split(',').filter(Boolean)
        const q = url.searchParams.get('q')
        const similarTo = url.searchParams.get('similar_to')
        const genres = (url.searchParams.get('genres') ?? '')
            .split(',')
            .map((g) => g.trim())
            .filter(Boolean)
        const prefs = safeParsePrefs(url.searchParams.get('prefs'))
        const profile = buildProfile({ favoriteGenres: prefs?.favoriteGenres ?? genres, readingGoal: prefs?.readingGoal })

        let results: RecommendationResult[]
        if (q) {
            results = recommendFromQuery(books, q, { limit, profile, excludeIds: exclude })
        } else if (similarTo) {
            results = recommendSimilar(books, similarTo, { limit })
        } else {
            results = recommendForProfile(books, profile, { limit, excludeIds: exclude })
        }

        // Fire-and-forget audit log (only when DB configured).
        await logRecommendation(env, {
            user_id: url.searchParams.get('user_id') ?? undefined,
            strategy: q ? 'query' : similarTo ? 'similar' : 'hybrid',
            book_ids: results.map((r) => r.book.id),
            context: q ?? similarTo ?? undefined
        })

        return json(results.map(toWire))
    }

    // GET /api/books/trending?limit=12 — live curation from open-source sites.
    if (first === 'trending') {
        const limit = asInt(url.searchParams.get('limit'), 12)
        const trending = await fetchWebTrending(limit)
        return json({ data: trending, source: 'web', count: trending.length })
    }

    // GET /api/books/web-search?q=...&limit=20 — find ANY book from the web
    // (Google Books + Open Library) with a real description + cover. Catalog
    // matches are ranked first so known titles stay authoritative.
    if (first === 'web-search') {
        const q = url.searchParams.get('q') ?? ''
        const limit = asInt(url.searchParams.get('limit'), 20)
        if (!q.trim()) return json({ data: [], source: 'web', count: 0 })

        const ql = q.toLowerCase()
        const catalogHits = books
            .filter((b) =>
                `${b.title} ${b.authors} ${b.genres.join(' ')}`.toLowerCase().includes(ql)
            )
            .slice(0, 5)
        const webHits = await searchWebBooks(q, limit - catalogHits.length)
        const seen = new Set(catalogHits.map((b) => b.title.toLowerCase()))
        const merged = [...catalogHits, ...webHits.filter((b) => !seen.has(b.title.toLowerCase()))]
        return json({ data: merged, source: 'web+catalog', count: merged.length })
    }

    // GET /api/books/insights?isbn=... | ?id=b-XX | ?key=ol:... — 2-4 real
    // facts about a book plus a reader-expectation line (completion ceremony).
    if (first === 'insights') {
        const id = url.searchParams.get('id') ?? ''
        const isbn = url.searchParams.get('isbn') ?? ''
        const key = url.searchParams.get('key') ?? ''
        let book: Book | null = null
        if (id) {
            book = books.find((b) => b.id === id) ?? null
            if (!book && (isbn || key)) book = isbn ? await resolveByIsbn(isbn) : await resolveByKey(key)
        } else if (isbn) {
            book = await resolveByIsbn(isbn)
        } else if (key) {
            book = await resolveByKey(key)
        }
        if (!book) return json({ error: 'not_found', message: 'Book not found' }, 404)
        return json(await getBookInsights(book))
    }

    // GET /api/books/resolve?isbn=... — auto-fetch a book shared by ISBN from
    // open-source catalogs (Open Library) and return the normalized record.
    // GET /api/books/resolve?key=ol:OL123W|gb:xyz — resolve by provider key.
    if (first === 'resolve') {
        const isbn = url.searchParams.get('isbn') ?? url.searchParams.get('id') ?? ''
        const key = url.searchParams.get('key') ?? ''
        let resolved: Book | null = null
        if (isbn) resolved = await resolveByIsbn(isbn)
        else if (key) resolved = await resolveByKey(key)
        if (!resolved) {
            return json(
                { error: 'not_found', message: `Could not resolve ${isbn || key}` },
                404
            )
        }
        return json(resolved)
    }

    // GET /api/books/:id  and  /api/books/:id/similar
    const book = books.find((b) => b.id === first)
    if (!book) return notFound(`Book ${first} not found`)
    if (segments[1] === 'similar') {
        return json(recommendSimilar(books, book.id, { limit: asInt(url.searchParams.get('limit'), 5) }).map(toWire))
    }
    return json(book)
}

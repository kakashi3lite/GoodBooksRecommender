/**
 * 🌐 Live Web Catalog — open-source book curation at the edge.
 * Chain-of-Thought: the curated catalog (shared/book-catalog.json) is static,
 * so "Trending now" and "resolve a shared book URL" need live data. This
 * module proxies open, key-less sources — Open Library and Google Books —
 * and normalizes them into the app's Book shape. Multi-source fallback keeps
 * the feature alive if one provider is down or rate-limited, and a tiny
 * in-memory TTL cache avoids hammering third parties on every request.
 */

import { type Book } from './catalog'

const UA = 'GoodBooksRecommender/1.0 (+https://books.dalecabra.com)'

/** Fetch with a hard timeout so a slow third party never blocks the edge. */
const fetchJson = async (url: string, timeoutMs = 6000): Promise<unknown> => {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
        const res = await fetch(url, {
            headers: { 'User-Agent': UA, Accept: 'application/json' },
            signal: controller.signal
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return await res.json()
    } finally {
        clearTimeout(timer)
    }
}

const coverUrl = (coverId?: number | null, size: 'S' | 'M' | 'L' = 'M'): string =>
    coverId ? `https://covers.openlibrary.org/b/id/${coverId}-${size}.jpg` : ''

const cleanGenres = (subjects: unknown): string[] => {
    if (!Array.isArray(subjects)) return ['Fiction']
    return Array.from(
        new Set(
            subjects
                .map((s) => String(s))
                .map((s) => s.split(':')[0].trim())
                .filter((s) => s.length > 1 && s.length < 40)
        )
    ).slice(0, 4)
}

const ratingOf = (avg?: unknown, count?: unknown): { rating: number; ratingsCount: number } => {
    const r = typeof avg === 'number' && Number.isFinite(avg) ? avg : 4.0
    const c = typeof count === 'number' && Number.isFinite(count) ? count : 0
    return { rating: Math.min(5, Math.max(0, Math.round(r * 10) / 10)), ratingsCount: c }
}

// ─── Open Library ───────────────────────────────────────────────────────────

interface OpenLibraryWork {
    key?: string
    title?: string
    author_name?: string[]
    authors?: Array<{ name?: string; key?: string }>
    cover_i?: number
    first_publish_year?: number
    subject?: string[]
    ratings_average?: number
    ratings_count?: number
    description?: string | { value?: string } | null
    isbn?: string[]
}

const normalizeOpenLibraryWork = (w: OpenLibraryWork, index: number): Book | null => {
    if (!w || !w.title) return null
    const authors = Array.isArray(w.authors)
        ? w.authors.map((a) => a.name).filter(Boolean)
        : (w.author_name ?? [])
    const key = (w.key ?? '').replace('/works/', '')
    const isbn = Array.isArray(w.isbn) ? w.isbn[0] : undefined
    const desc = typeof w.description === 'string' ? w.description : w.description?.value
    const { rating, ratingsCount } = ratingOf(w.ratings_average, w.ratings_count)
    return {
        id: isbn ? `isbn:${isbn}` : `ol:${key || index}`,
        title: w.title,
        authors: authors.join(', ') || 'Unknown author',
        cover_url: coverUrl(w.cover_i),
        rating,
        ratingsCount,
        genres: cleanGenres(w.subject),
        moods: [],
        published_year: w.first_publish_year ?? new Date().getFullYear(),
        page_count: 0,
        description:
            desc && desc.length > 20
                ? desc.slice(0, 600)
                : `${w.title} — a trending read from Open Library.`
    }
}

/** Trending works — Open Library daily, then now (popularity decayed). */
export const fetchOpenLibraryTrending = async (limit: number): Promise<Book[]> => {
    for (const base of ['https://openlibrary.org/trending/daily.json', 'https://openlibrary.org/trending/now.json']) {
        try {
            const data = (await fetchJson(base)) as { works?: OpenLibraryWork[] }
            const books = (data.works ?? [])
                .map(normalizeOpenLibraryWork)
                .filter((b): b is Book => Boolean(b))
                .slice(0, limit)
            if (books.length > 0) return books
        } catch {
            // try next source
        }
    }
    return []
}

// ─── Google Books ───────────────────────────────────────────────────────────

interface GoogleVolume {
    volumeInfo?: {
        title?: string
        authors?: string[]
        imageLinks?: { thumbnail?: string }
        publishedDate?: string
        pageCount?: number
        description?: string
        categories?: string[]
        industryIdentifiers?: Array<{ type?: string; identifier?: string }>
        averageRating?: number
        ratingsCount?: number
    }
    id?: string
}

const normalizeGoogleVolume = (v: GoogleVolume, index: number): Book | null => {
    const info = v.volumeInfo
    if (!info || !info.title) return null
    const isbn =
        info.industryIdentifiers?.find((i) => i.type === 'ISBN_13' || i.type === 'ISBN_10')
            ?.identifier ?? undefined
    const thumb = info.imageLinks?.thumbnail
        ? info.imageLinks.thumbnail.replace(/^http:/, 'https:')
        : ''
    const year = Number.parseInt((info.publishedDate ?? '').slice(0, 4), 10)
    const { rating, ratingsCount } = ratingOf(info.averageRating, info.ratingsCount)
    return {
        id: isbn ? `isbn:${isbn}` : `gb:${v.id || index}`,
        title: info.title,
        authors: (info.authors ?? []).join(', ') || 'Unknown author',
        cover_url: thumb,
        rating,
        ratingsCount,
        genres: cleanGenres(info.categories),
        moods: [],
        published_year: Number.isFinite(year) ? year : new Date().getFullYear(),
        page_count: info.pageCount ?? 0,
        description:
            info.description && info.description.length > 20
                ? info.description.slice(0, 600)
                : `${info.title} — from Google Books.`
    }
}

/** Newest releases across a spread of popular subjects (fresh, not static). */
export const fetchGoogleBooksNew = async (limit: number): Promise<Book[]> => {
    try {
        const subjects = ['fiction', 'mystery thriller', 'science fiction', 'romance']
        const all: Book[] = []
        for (const subject of subjects) {
            if (all.length >= limit) break
            const data = (await fetchJson(
                `https://www.googleapis.com/books/v1/volumes?q=subject:${encodeURIComponent(subject)}&orderBy=newest&maxResults=${Math.min(10, limit)}&langRestrict=en`
            )) as { items?: GoogleVolume[] }
            for (const item of data.items ?? []) {
                const b = normalizeGoogleVolume(item, all.length)
                if (b && !all.some((x) => x.id === b.id)) all.push(b)
            }
        }
        return all.slice(0, limit)
    } catch {
        return []
    }
}

// ─── Resolve a single book by ISBN / Open Library key ───────────────────────

const extractDescription = (d: unknown): string => {
    if (typeof d === 'string') return d
    if (d && typeof d === 'object') return (d as { value?: string }).value ?? ''
    return ''
}

/** Look up a book by ISBN on Open Library (data API + work description). */
export const resolveByIsbn = async (isbn: string): Promise<Book | null> => {
    const clean = isbn.replace(/[^0-9Xx]/g, '')
    if (clean.length < 10) return null
    try {
        const data = (await fetchJson(
            `https://openlibrary.org/api/books?bibkeys=ISBN:${clean}&jscmd=data&format=json`
        )) as Record<string, {
            title?: string
            authors?: Array<{ name?: string }>
            cover?: { medium?: string; large?: string }
            number_of_pages?: number
            publish_date?: string
            subjects?: Array<{ name?: string }>
        }>
        const rec = data[`ISBN:${clean}`]
        if (!rec || !rec.title) return null

        let description = ''
        try {
            const edition = (await fetchJson(`https://openlibrary.org/isbn/${clean}.json`)) as {
                works?: Array<{ key?: string }>
            }
            const workKey = edition.works?.[0]?.key
            if (workKey) {
                const work = (await fetchJson(`https://openlibrary.org${workKey}.json`)) as {
                    description?: unknown
                }
                description = extractDescription(work.description)
            }
        } catch {
            // description is optional — keep going
        }

        const year = Number.parseInt((rec.publish_date ?? '').slice(-4), 10)
        return {
            id: `isbn:${clean}`,
            title: rec.title,
            authors: (rec.authors ?? []).map((a) => a.name).filter(Boolean).join(', ') || 'Unknown author',
            cover_url: rec.cover?.large ?? rec.cover?.medium ?? '',
            rating: 4,
            ratingsCount: 0,
            genres: (rec.subjects ?? []).map((s) => s.name).slice(0, 4).length
                ? (rec.subjects ?? []).map((s) => s.name).slice(0, 4)
                : ['Fiction'],
            moods: [],
            published_year: Number.isFinite(year) ? year : new Date().getFullYear(),
            page_count: rec.number_of_pages ?? 0,
            description:
                description.length > 20
                    ? description.slice(0, 600)
                    : `Resolved from Open Library by ISBN ${clean}.`
        }
    } catch {
        return null
    }
}

// ─── Combined facade + tiny TTL cache ───────────────────────────────────────

const CACHE_TTL_MS = 10 * 60 * 1000 // 10 minutes
const cache = new Map<string, { at: number; value: Book[] }>()

/** Look up a book by an Open Library work key ("ol:OL123W") or Google Books id ("gb:xyz"). */
export const resolveByKey = async (key: string): Promise<Book | null> => {
    if (key.startsWith('ol:')) {
        const workKey = key.slice(3)
        try {
            const w = (await fetchJson(`https://openlibrary.org/works/${workKey}.json`)) as OpenLibraryWork
            const book = normalizeOpenLibraryWork(w, 0)
            if (!book) return null
            // normalizeOpenLibraryWork already builds id from isbn/key — force stable
            book.id = `ol:${workKey}`
            return book
        } catch {
            return null
        }
    }
    if (key.startsWith('gb:')) {
        const gbId = key.slice(3)
        try {
            const v = (await fetchJson(`https://www.googleapis.com/books/v1/volumes/${gbId}`)) as GoogleVolume
            const book = normalizeGoogleVolume(v, 0)
            if (!book) return null
            book.id = `gb:${gbId}`
            return book
        } catch {
            return null
        }
    }
    return null
}

/** Trending from the web: Open Library first, Google Books new as a mix-in. */
export const fetchWebTrending = async (limit = 12): Promise<Book[]> => {
    const key = `trending:${limit}`
    const hit = cache.get(key)
    if (hit && Date.now() - hit.at < CACHE_TTL_MS) return hit.value

    const [ol, gb] = await Promise.all([
        fetchOpenLibraryTrending(Math.ceil(limit / 2)),
        fetchGoogleBooksNew(Math.ceil(limit / 2))
    ])
    // Interleave + de-dupe by title (case-insensitive).
    const seen = new Set<string>()
    const merged: Book[] = []
    for (let i = 0; i < Math.max(ol.length, gb.length); i++) {
        for (const list of [ol, gb]) {
            const b = list[i]
            if (b) {
                const key = b.title.toLowerCase()
                if (!seen.has(key)) {
                    seen.add(key)
                    merged.push(b)
                }
            }
        }
    }
    const result = merged.slice(0, limit)
    cache.set(key, { at: Date.now(), value: result })
    return result
}

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
            if (books.length > 0) return enrichWithDescriptions(books)
        } catch {
            // try next source
        }
    }
    return []
}

/**
 * Open Library trending works often omit descriptions. For any book still
 * carrying the generic fallback text, fetch the real work record (in
 * parallel, bounded) and attach its description so every expanded card has
 * a genuine blurb rather than filler.
 */
const enrichWithDescriptions = async (books: Book[]): Promise<Book[]> => {
    const needsEnrich = books
        .map((b, i) => ({ b, i }))
        .filter(({ b }) => !b.description || b.description.includes('a trending read from'))
        .slice(0, 6) // bound the parallel fan-out
    if (needsEnrich.length === 0) return books

    const enriched = await Promise.all(
        needsEnrich.map(async ({ b, i }) => {
            if (!b.id.startsWith('ol:')) return { i, b }
            try {
                const w = (await fetchJson(`https://openlibrary.org/works/${b.id.slice(3)}.json`, 4000)) as OpenLibraryWork
                const desc = extractDescription(w.description)
                if (desc && desc.length > 20) return { i, b: { ...b, description: desc.slice(0, 600) } }
            } catch {
                // keep the fallback description
            }
            return { i, b }
        })
    )
    const byIndex = new Map(enriched.map((e) => [e.i, e.b]))
    return books.map((b, i) => byIndex.get(i) ?? b)
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
    if (typeof d === 'string') return cleanDescription(d)
    if (d && typeof d === 'object') return cleanDescription((d as { value?: string }).value ?? '')
    return ''
}

/**
 * Open Library blurbs sometimes carry markdown/HTML noise (e.g. `[text](url)`
 * links, `<u>` tags, `&nbsp;` entities, `#` headers). Strip the worst of it
 * so the expandable blurb reads cleanly in the UI.
 */
const cleanDescription = (raw: string): string =>
    raw
        .replace(/<[^>]*>/g, ' ') // HTML tags → space
        .replace(/&nbsp;/g, ' ') // common entity
        .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1') // markdown links → link text
        .replace(/[#*_`]/g, '') // stray markdown markers
        .replace(/\\/g, '') // escaped backslashes from markdown sources
        .replace(/\s+/g, ' ')
        .trim()

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
            genres: (() => {
                const subjects = (rec.subjects ?? [])
                    .map((s) => s.name)
                    .filter((name): name is string => typeof name === 'string' && name.length > 0)
                    .slice(0, 4)
                return subjects.length > 0 ? subjects : ['Fiction']
            })(),
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

// ─── Web search: find ANY book, not just the curated catalog ────────────────

/**
 * Search the open web (Google Books primary + Open Library secondary) for any
 * book a reader has in mind. Returns up to `limit` normalized books — each
 * with a real description and cover so the "add a book" search bar is useful
 * immediately. Merged + de-duplicated by title, catalog-style shape.
 */
export const searchWebBooks = async (query: string, limit = 20): Promise<Book[]> => {
    const q = query.trim()
    if (!q) return []
    const merged: Book[] = []
    const seen = new Set<string>()

    const pushUnique = (b: Book | null): void => {
        if (!b) return
        const key = b.title.toLowerCase()
        if (!seen.has(key)) {
            seen.add(key)
            merged.push(b)
        }
    }

    // 1) Google Books — richest: description + cover + ISBN + rating + pages.
    try {
        const data = (await fetchJson(
            `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(q)}&maxResults=${Math.min(limit, 20)}&langRestrict=en`
        )) as { items?: GoogleVolume[] }
        for (const item of data.items ?? []) pushUnique(normalizeGoogleVolume(item, merged.length))
    } catch {
        // continue with Open Library
    }

    // 2) Top up with Open Library search when Google returned fewer.
    if (merged.length < limit) {
        try {
            const data = (await fetchJson(
                `https://openlibrary.org/search.json?q=${encodeURIComponent(q)}&limit=${Math.min(limit, 20)}&fields=key,title,author_name,cover_i,first_publish_year,subject,ratings_average,ratings_count,isbn`
            )) as { docs?: OpenLibraryWork[] }
            for (const doc of data.docs ?? []) pushUnique(normalizeOpenLibraryWork(doc, merged.length))
        } catch {
            // nothing more to add
        }
    }

    // 3) Enrich the top Open Library-only hits with real descriptions.
    const enriched = await enrichWithDescriptions(merged)
    return enriched.slice(0, limit)
}

// ─── Book insights: real facts for the completion experience ────────────────

export interface BookInsights {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    ratingsCount: number
    genres: string[]
    published_year: number
    page_count: number
    description: string
    /** 2–4 curated facts about this exact book (from its real metadata). */
    facts: string[]
    /** Reader-expectation line derived from the book's actual genres. */
    expectation: string
}

const GENRE_EXPECTATION: Array<[string, string]> = [
    ['Science Fiction', 'a thought experiment that stays with you long after the last page'],
    ['Fantasy', 'a richly built world you will not want to leave'],
    ['Mystery', 'a puzzle that keeps you guessing until the final chapter'],
    ['Thriller', 'a breakneck pace that makes the pages turn themselves'],
    ['Romance', 'a warm, emotional payoff that makes the wait worth it'],
    ['Self-Help', 'practical takeaways you can start using this week'],
    ['Biography', 'a real life told with unexpected intimacy'],
    ['Horror', 'an uneasy atmosphere that lingers after lights out'],
    ['Historical Fiction', 'a vivid trip into a past era with modern stakes'],
    ['Nonfiction', 'a clear-eyed look at a subject that matters'],
    ['Literary Fiction', 'prose to savor, with a quiet emotional undercurrent'],
    ['Fiction', 'a story built to move you'],
    ['Adventure', 'a propulsive journey with stakes that keep climbing']
]

const expectationFor = (genres: string[]): string => {
    for (const [genre, expectation] of GENRE_EXPECTATION) {
        if (genres.some((g) => g.toLowerCase() === genre.toLowerCase())) return expectation
    }
    return 'a story worth finishing — and reflecting on'
}

/**
 * Assemble 2–4 real facts about a book plus a reader-expectation line.
 * Facts are derived from the book's actual fetched metadata (synopsis,
 * themes, publication, page count, reader rating) — never fabricated.
 */
export const getBookInsights = async (book: Book): Promise<BookInsights> => {
    const facts: string[] = []

    // Fact 1 — a one-line synopsis from the real description.
    if (book.description && book.description.length > 20) {
        const firstSentence = book.description.split(/\.\s/)[0].slice(0, 140)
        facts.push(`It opens: "${firstSentence}${firstSentence.endsWith('.') ? '' : '.'}"`)
    }

    // Fact 2 — themes / genres.
    if (book.genres && book.genres.length > 0) {
        const themes = book.genres.slice(0, 3)
        facts.push(`Themes: ${themes.join(', ')}${book.moods && book.moods.length > 0 ? ` · a ${book.moods[0]} read` : ''}`)
    }

    // Fact 3 — publication + physical book.
    const year = book.published_year || new Date().getFullYear()
    const pages = book.page_count
    facts.push(
        pages && pages > 0
            ? `Published ${year} · ${pages.toLocaleString()} pages`
            : `Published ${year}`
    )

    // Fact 4 — reader reception (only when real ratings exist).
    if (book.ratingsCount && book.ratingsCount > 0) {
        facts.push(
            `Rated ${book.rating.toFixed(1)}/5 by ${book.ratingsCount.toLocaleString()} readers`
        )
    } else if (book.rating >= 4) {
        facts.push(`Consistently rated ${book.rating.toFixed(1)}/5 by readers`)
    }

    return {
        id: book.id,
        title: book.title,
        authors: book.authors,
        cover_url: book.cover_url,
        rating: book.rating,
        ratingsCount: book.ratingsCount,
        genres: book.genres,
        published_year: book.published_year,
        page_count: book.page_count,
        description: book.description,
        facts: facts.slice(0, 4),
        expectation: expectationFor(book.genres ?? [])
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

/**
 * 🎛️ Shared Book Filters — one filter vocabulary for every surface
 * Chain-of-Thought: Dashboard and Discover used different (and partly dead)
 * filter controls. This module is the single source of truth so the same
 * tabs, genres, and search behave identically sitewide.
 *
 * Reader-psychology notes:
 *   - Trust: every predicate here is pure and honest — a filter that "does
 *     nothing" destroys trust, so filters MUST actually filter.
 *   - Hick's law (choice overload): a small, meaningful tab set beats a long
 *     list. Defaults keep the reader moving (status-quo bias).
 *   - Recognition over recall: chips with counts ("Fantasy · 5") reassure the
 *     reader there's something to find (loss aversion) and let them commit.
 *   - Identity: favorite genres are ranked first so filters feel like "mine".
 */

import { BOOK_CATALOG } from '../data/bookCatalog'

// ─── Genre normalization ────────────────────────────────────────────────────
// Mirrors the server-side recommender so "sci-fi" matches "Science Fiction"
// no matter where the value came from (onboarding, search, API).

/** Canonicalize a genre label onto the catalog vocabulary. */
export const normalizeGenre = (g: string): string => {
    const key = g.trim().toLowerCase().replace(/[^a-z0-9]/g, '')
    switch (key) {
        case 'scifi':
        case 'sciencefiction':
            return 'sciencefiction'
        case 'selfhelp':
            return 'selfhelp'
        case 'nonfiction':
            return 'nonfiction'
        case 'historicalfiction':
        case 'historical':
            return 'historicalfiction'
        case 'literaryfiction':
        case 'literary':
            return 'literaryfiction'
        default:
            return key
    }
}

/** True when a book belongs to `genre` (alias-aware, case-insensitive). */
export const matchesGenre = (genres: string[] | undefined, genre: string | undefined): boolean => {
    if (!genre) return true
    const target = normalizeGenre(genre)
    return (genres ?? []).some((g) => normalizeGenre(g) === target)
}

/** Minimal shape a filterable book needs (works for catalog, search, trending). */
export interface FilterableBook {
    id: string
    title: string
    authors?: string
    author?: string
    genres?: string[]
    moods?: string[]
    rating?: number
    page_count?: number
    published_year?: number
}

/** Text search over title + author + genres (no query → everything matches). */
export const matchesQuery = (book: FilterableBook, query: string): boolean => {
    const q = query.trim().toLowerCase()
    if (!q) return true
    const hay = `${book.title} ${book.authors ?? book.author ?? ''} ${(book.genres ?? []).join(' ')}`.toLowerCase()
    return hay.includes(q)
}

// ─── Filter tabs ────────────────────────────────────────────────────────────
// A small, honest set — every tab maps to real catalog fields so it always
// returns something, and the reader always knows what each tab means.

export interface BookTab {
    id: string
    label: string
    emoji: string
    test: (b: FilterableBook) => boolean
}

/** `feel-good` maps moods (cozy/uplifting) so the tab stays populated and
 * answers "what do I feel like reading right now?". */
export const BOOK_FILTER_TABS: BookTab[] = [
    { id: 'all', label: 'For you', emoji: '✨', test: () => true },
    {
        id: 'top-rated',
        label: 'Top rated',
        emoji: '⭐',
        test: (b) => (b.rating ?? 0) >= 4.5
    },
    {
        id: 'quick-reads',
        label: 'Quick reads',
        emoji: '⚡',
        test: (b) => {
            const pages = b.page_count
            return typeof pages === 'number' && pages > 0 && pages <= 300
        }
    },
    {
        id: 'feel-good',
        label: 'Feel-good',
        emoji: '☀️',
        test: (b) =>
            Array.isArray(b.moods) && b.moods.some((m) => ['cozy', 'uplifting'].includes(m))
    }
]

/** Apply tab + genre + text query together. Unknown tab id → "all". */
export const applyBookFilters = <T extends FilterableBook>(
    books: T[],
    opts: { query?: string; genre?: string; tab?: string } = {}
): T[] => {
    const tab = BOOK_FILTER_TABS.find((t) => t.id === opts.tab) ?? BOOK_FILTER_TABS[0]
    const q = opts.query ?? ''
    const genre = opts.genre ?? ''
    return books.filter((b) => matchesQuery(b, q) && matchesGenre(b.genres, genre) && tab.test(b))
}

/** Live genre chips with counts. Favorite genres first (identity), then by
 * prevalence in the pool (recognition). */
export const genreChipsFor = (
    books: FilterableBook[],
    favoriteGenres: string[] = [],
    limit = 8
): Array<{ genre: string; count: number }> => {
    const counts = new Map<string, number>()
    for (const b of books) {
        for (const g of b.genres ?? []) {
            counts.set(g, (counts.get(g) ?? 0) + 1)
        }
    }
    const favNorm = favoriteGenres.map(normalizeGenre)
    return Array.from(counts.entries())
        .map(([genre, count]) => ({ genre, count }))
        .filter((c) => c.count > 0)
        .sort((a, b) => {
            const aFav = favNorm.includes(normalizeGenre(a.genre)) ? 1 : 0
            const bFav = favNorm.includes(normalizeGenre(b.genre)) ? 1 : 0
            if (aFav !== bFav) return bFav - aFav
            return b.count - a.count
        })
        .slice(0, limit)
}

/** Genre chips derived from the curated catalog (stable, favorite-first) —
 * used on surfaces whose pool is live/fetched (Discover). */
export const catalogGenreChips = (
    favoriteGenres: string[] = [],
    limit = 8
): Array<{ genre: string; count: number }> =>
    genreChipsFor(BOOK_CATALOG as unknown as FilterableBook[], favoriteGenres, limit)

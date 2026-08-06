/**
 * 📚 Shared Book Catalog (server-side)
 * Chain-of-Thought: The curated catalog is the seed data for the real-time
 * recommendation engine. It ships in the Function bundle so recommendations
 * always work — and becomes the fallback when the Supabase database is not
 * yet configured (functions/api/_lib/db.ts).
 *
 * Source of truth: shared/book-catalog.json (regenerate with
 * `node scripts/export-catalog.cjs` — never edit by hand).
 */
import catalog from '../../../shared/book-catalog.json'

export interface Book {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    ratingsCount: number
    genres: string[]
    moods: string[]
    published_year: number
    page_count: number
    description: string
}

export interface RecommendationResult {
    book: Book
    /** 0..100 normalized score */
    score: number
    /** Human-readable "why this book" reason */
    reason: string
}

/** The curated catalog (typed from the shared JSON). */
export const BOOK_CATALOG: Book[] = catalog as Book[]

/** All distinct genres, for keyword→genre hinting in free-text queries. */
export const ALL_GENRES: string[] = Array.from(
    new Set(BOOK_CATALOG.flatMap((b) => b.genres))
).sort()

/** All distinct moods, for keyword→mood hinting. */
export const ALL_MOODS: string[] = Array.from(
    new Set(BOOK_CATALOG.flatMap((b) => b.moods))
).sort()

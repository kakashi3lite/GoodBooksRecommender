/**
 * ✨ Today's Pick — deterministic daily recommendation.
 * Chain-of-Thought: a date-seeded rotation through the catalog gives every
 * visitor a real, fresh "reason to come back tomorrow" with zero backend.
 * Same day → same pick (stable, shareable); day changes → new pick.
 */

import { BOOK_CATALOG, type CatalogBook } from '../data/bookCatalog'

const daySeed = (d: Date): number =>
    d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate()

/** The single book featured today (rotates daily). */
export const getDailyPick = (d: Date = new Date()): CatalogBook => {
    const index = daySeed(d) % BOOK_CATALOG.length
    return BOOK_CATALOG[index]
}

/** A short, human reason for the day's pick. */
export const dailyPickReason = (book: CatalogBook): string => {
    if (book.rating >= 4.6) return `A ${book.rating.toFixed(1)}★ reader favorite`
    if (book.moods?.includes('cozy')) return 'A cozy pick for today'
    if (book.genres?.includes('Science Fiction')) return 'A sci-fi journey for today'
    if (book.genres?.includes('Fantasy')) return 'An escape into fantasy'
    return `A well-loved ${(book.genres?.[0] ?? 'book').toLowerCase()} worth reading`
}

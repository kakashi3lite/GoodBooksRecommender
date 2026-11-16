/**
 * 📊 Reading statistics — pure, testable derivations for the analytics page.
 *
 * Chain-of-Thought:
 *   The Analytics page used to fall back to "the catalog's overall spread" when
 *   a reader had no data, and render that as *their* genre breakdown. A brand
 *   new reader saw a confident chart of tastes they had never expressed — the
 *   fastest way to teach someone that the numbers in this app are decoration.
 *   An empty state is honest; a fabricated chart is not.
 *
 * Keeping this pure (ids + catalog in, slices out) means the honesty rule is
 * covered by a unit test instead of a screenshot review.
 */

export interface CatalogLike {
    id: string
    genres?: string[]
}

export interface GenreSlice {
    name: string
    count: number
    /** Bar width, 0–100, relative to the most-read genre. */
    pct: number
}

/**
 * Genre distribution for the books a reader actually engaged with.
 *
 * @param bookIds  favourites + finished book ids (duplicates are counted once)
 * @param catalog  lookup source (curated catalog or API results)
 * @param limit    how many slices to return
 * @returns slices sorted by count, or `[]` when there is nothing to show
 */
export const buildGenreBreakdown = (
    bookIds: string[],
    catalog: CatalogLike[],
    limit = 8
): GenreSlice[] => {
    const byId = new Map(catalog.map((book) => [book.id, book]))
    const counts = new Map<string, number>()

    // De-duplicate: a book that is both wishlisted and finished is one taste
    // signal, not two.
    for (const id of new Set(bookIds)) {
        const book = byId.get(id)
        if (!book) continue
        for (const genre of book.genres ?? []) {
            counts.set(genre, (counts.get(genre) ?? 0) + 1)
        }
    }

    if (counts.size === 0) return []

    const max = Math.max(...counts.values())
    return Array.from(counts.entries())
        .map(([name, count]) => ({ name, count, pct: Math.round((count / max) * 100) }))
        .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
        .slice(0, limit)
}

/** Distinct days with a real reading session (recovered days excluded). */
export const readingDays = (log: Array<{ date: string; recovered?: boolean }>): number =>
    new Set(log.filter((entry) => !entry.recovered).map((entry) => entry.date)).size

/**
 * Average pages per calendar day the reader was actually active.
 * Returns 0 rather than a fabricated baseline when there is no history.
 */
export const pagesPerActiveDay = (
    log: Array<{ pages: number; recovered?: boolean }>
): number => {
    const sessions = log.filter((entry) => !entry.recovered)
    if (sessions.length === 0) return 0
    const days = new Set(
        log.filter((entry) => !entry.recovered).map((entry) => (entry as { date?: string }).date)
    )
    const activeDays = Math.max(1, days.size)
    return Math.round(sessions.reduce((total, entry) => total + entry.pages, 0) / activeDays)
}

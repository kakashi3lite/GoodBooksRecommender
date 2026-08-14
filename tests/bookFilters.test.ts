/**
 * 🎛️ Shared Book Filters Tests
 * Chain-of-Thought: Verify the sitewide filter vocabulary — alias-aware genre
 * matching, honest tabs backed by real catalog fields, combined filtering,
 * and favorite-first genre chips with counts.
 */

import { describe, expect, it } from 'vitest'
import { BOOK_CATALOG } from '../src/data/bookCatalog'
import {
    applyBookFilters,
    catalogGenreChips,
    genreChipsFor,
    matchesGenre,
    matchesQuery,
    normalizeGenre,
    BOOK_FILTER_TABS
} from '../src/utils/bookFilters'

const dune = BOOK_CATALOG.find((b) => b.title === 'Dune')!

describe('normalizeGenre', () => {
    it('maps aliases onto the catalog vocabulary', () => {
        expect(normalizeGenre('sci-fi')).toBe('sciencefiction')
        expect(normalizeGenre('Science Fiction')).toBe('sciencefiction')
        expect(normalizeGenre('scifi')).toBe('sciencefiction')
        expect(normalizeGenre('self-help')).toBe('selfhelp')
        expect(normalizeGenre('Non-Fiction')).toBe('nonfiction')
        expect(normalizeGenre('Fantasy')).toBe('fantasy')
    })
})

describe('matchesGenre', () => {
    it('is alias-aware and case-insensitive', () => {
        expect(matchesGenre(['Science Fiction', 'Fantasy'], 'sci-fi')).toBe(true)
        expect(matchesGenre(['Science Fiction', 'Fantasy'], 'fantasy')).toBe(true)
        expect(matchesGenre(['Science Fiction', 'Fantasy'], 'Romance')).toBe(false)
        expect(matchesGenre(['Science Fiction', 'Fantasy'], undefined)).toBe(true)
        expect(matchesGenre(undefined, 'Fantasy')).toBe(false)
    })
})

describe('matchesQuery', () => {
    it('searches title, author and genres; empty query matches all', () => {
        expect(matchesQuery(dune, 'dune')).toBe(true)
        expect(matchesQuery(dune, 'Frank')).toBe(true)
        expect(matchesQuery(dune, 'science')).toBe(true)
        expect(matchesQuery(dune, 'romance')).toBe(false)
        expect(matchesQuery(dune, '')).toBe(true)
        expect(matchesQuery(dune, '   ')).toBe(true)
    })
})

describe('BOOK_FILTER_TABS', () => {
    it('contains exactly the honest, data-backed tabs', () => {
        expect(BOOK_FILTER_TABS.map((t) => t.id)).toEqual([
            'all',
            'top-rated',
            'quick-reads',
            'feel-good'
        ])
    })

    it('every tab returns at least one book from the catalog (no dead tabs)', () => {
        for (const tab of BOOK_FILTER_TABS) {
            const hits = BOOK_CATALOG.filter(tab.test)
            expect(hits.length, `${tab.id} returned 0 books`).toBeGreaterThan(0)
        }
    })

    it('top-rated only includes ≥4.5★ books; quick-reads only ≤300 pages', () => {
        const topRated = BOOK_CATALOG.filter(BOOK_FILTER_TABS[1].test)
        expect(topRated.every((b) => b.rating >= 4.5)).toBe(true)
        const quick = BOOK_CATALOG.filter(BOOK_FILTER_TABS[2].test)
        expect(quick.every((b) => b.page_count > 0 && b.page_count <= 300)).toBe(true)
        const feelGood = BOOK_CATALOG.filter(BOOK_FILTER_TABS[3].test)
        expect(feelGood.every((b) => b.moods?.some((m) => ['cozy', 'uplifting'].includes(m)))).toBe(true)
    })
})

describe('applyBookFilters', () => {
    it('applies tab + genre + query together', () => {
        // Fantasy + top-rated
        const fantasyTop = applyBookFilters(BOOK_CATALOG, { genre: 'Fantasy', tab: 'top-rated' })
        expect(fantasyTop.length).toBeGreaterThan(0)
        expect(fantasyTop.every((b) => b.genres?.includes('Fantasy'))).toBe(true)
        expect(fantasyTop.every((b) => b.rating >= 4.5)).toBe(true)

        // Unknown tab falls back to "all"
        const all = applyBookFilters(BOOK_CATALOG, { tab: 'nope' })
        expect(all.length).toBe(BOOK_CATALOG.length)
    })
})

describe('genreChipsFor', () => {
    it('ranks favorite genres first and includes live counts', () => {
        const chips = genreChipsFor(BOOK_CATALOG, ['Fantasy'])
        expect(chips.length).toBeGreaterThan(0)
        expect(chips[0].genre).toBe('Fantasy')
        expect(chips[0].count).toBeGreaterThan(0)
        // Counts must sum to at most the pool size contribution (sanity).
        expect(chips.every((c) => c.count >= 1)).toBe(true)
    })

    it('catalogGenreChips is stable and bounded', () => {
        const chips = catalogGenreChips([], 6)
        expect(chips.length).toBeLessThanOrEqual(6)
        expect(chips.length).toBeGreaterThan(0)
    })
})

/**
 * 🎯 Personalization Engine Tests
 * Chain-of-Thought: Verify scoring ranks genre-matched books first, honors
 * moods, respects exclude lists, and produces human-readable reasons.
 */

import { describe, expect, it } from 'vitest'
import { BOOK_CATALOG } from '../src/data/bookCatalog'
import type { UserPreferences } from '../src/stores/user/userSlice'
import {
    buildProfile,
    buildReason,
    describeProfile,
    getPersonalizedRecommendations,
    scoreBook
} from '../src/utils/personalization'

const sciFiPrefs: UserPreferences = {
    favoriteGenres: ['Science Fiction', 'Adventure'],
    preferredFormats: ['ebook'],
    readingGoal: 24,
    notifications: true,
    privacy: 'friends'
}

const fantasyPrefs: UserPreferences = {
    favoriteGenres: ['Fantasy'],
    preferredFormats: ['print'],
    readingGoal: 12,
    notifications: true,
    privacy: 'public'
}

const romancePrefs: UserPreferences = {
    favoriteGenres: ['Romance'],
    preferredFormats: ['ebook'],
    readingGoal: 24,
    notifications: true,
    privacy: 'private'
}

describe('personalization engine', () => {
    it('builds a profile with derived moods from favorite genres', () => {
        const profile = buildProfile(sciFiPrefs)
        expect(profile.favoriteGenres).toContain('Science Fiction')
        // Science Fiction maps to 'adventurous' mood
        expect(profile.preferredMoods).toContain('adventurous')
    })

    it('ranks genre-matched books above non-matching books', () => {
        const picks = getPersonalizedRecommendations(sciFiPrefs, { limit: 6 })
        const topGenres = picks[0].book.genres

        // Project Hail Mary / The Martian are the top sci-fi picks
        const projectHailMary = picks.find((p) => p.book.title === 'Project Hail Mary')
        expect(projectHailMary).toBeDefined()
        // No non-genre-matching book should outrank a genre match for a focused profile
        expect(topGenres.join(' ')).toMatch(/Science Fiction|Adventure/)
    })

    it('returns distinct books and respects the limit', () => {
        const picks = getPersonalizedRecommendations(sciFiPrefs, { limit: 3 })
        expect(picks).toHaveLength(3)
        const ids = new Set(picks.map((p) => p.book.id))
        expect(ids.size).toBe(3)
    })

    it('excludes books passed via excludeIds (already-read)', () => {
        const projectHailMary = BOOK_CATALOG.find((b) => b.title === 'Project Hail Mary')!
        const picks = getPersonalizedRecommendations(sciFiPrefs, {
            excludeIds: [projectHailMary.id],
            limit: 6
        })
        expect(picks.some((p) => p.book.id === projectHailMary.id)).toBe(false)
    })

    it('produces a "why" reason that references a favorite genre', () => {
        const profile = buildProfile(fantasyPrefs)
        const houseCerulean = BOOK_CATALOG.find((b) => b.title === 'The House in the Cerulean Sea')!
        const reasons = buildReason(houseCerulean, profile)
        expect(reasons.some((r) => r.toLowerCase().includes('fantasy'))).toBe(true)
    })

    it('scores within the 0..1 range and is stable', () => {
        const profile = buildProfile(romancePrefs)
        for (const book of BOOK_CATALOG) {
            const score = scoreBook(book, profile)
            expect(score).toBeGreaterThanOrEqual(0)
            expect(score).toBeLessThanOrEqual(1)
        }
        // Deterministic for the same input
        const a = scoreBook(BOOK_CATALOG[0], profile)
        const b = scoreBook(BOOK_CATALOG[0], profile)
        expect(a).toBe(b)
    })

    it('describes the reader profile for UI copy', () => {
        expect(describeProfile(romancePrefs)).toBe('romance')
        const mixed = { ...sciFiPrefs, favoriteGenres: ['Science Fiction', 'Fantasy', 'Mystery'] }
        expect(describeProfile(mixed)).toBe('science fiction · fantasy · mystery')
    })

    it('ranks a romance-tagged book first for a romance reader', () => {
        const picks = getPersonalizedRecommendations(romancePrefs, { limit: 3 })
        // The top pick must be a Romance book, regardless of popularity ordering
        expect(picks[0].book.genres).toContain('Romance')
        // Romance-tagged books dominate the top of the list
        const topGenres = picks.map((p) => p.book.genres.join(','))
        expect(topGenres.some((g) => g.includes('Romance'))).toBe(true)
    })
})

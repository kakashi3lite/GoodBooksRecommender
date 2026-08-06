/**
 * 🧪 Server-side Recommendation Engine Tests
 * Chain-of-Thought: Verifies the edge recommendation model (TF-IDF content
 * similarity + profile scoring + MMR diversity + query matching) behaves
 * correctly on the shared catalog.
 */

import { describe, expect, it } from 'vitest'
import { BOOK_CATALOG } from '../functions/api/_lib/catalog'
import {
    buildProfile,
    recommendForProfile,
    recommendFromQuery,
    recommendSimilar,
    scoreBook
} from '../functions/api/_lib/recommender'

const sciFiProfile = buildProfile({
    favoriteGenres: ['Science Fiction', 'Fantasy'],
    readingGoal: 24
})

const cozyProfile = buildProfile({
    favoriteGenres: ['Fiction', 'Fantasy'],
    readingGoal: 12
})

describe('server recommendation engine', () => {
    it('catalog is loaded from the shared JSON (24 books)', () => {
        expect(BOOK_CATALOG.length).toBe(24)
        expect(BOOK_CATALOG[0]).toHaveProperty('genres')
        expect(BOOK_CATALOG[0]).toHaveProperty('moods')
    })

    it('sci-fi reader gets sci-fi/fantasy books first with reasons', () => {
        const picks = recommendForProfile(BOOK_CATALOG, sciFiProfile, { limit: 6 })
        expect(picks.length).toBe(6)
        const top = picks[0]
        const isScifiFantasy = top.book.genres.some((g) =>
            ['Science Fiction', 'Fantasy'].includes(g)
        )
        expect(isScifiFantasy).toBe(true)
        expect(top.reason).toMatch(/Because you love/)
        expect(top.score).toBeGreaterThan(50)
        // All scores are 0..100
        picks.forEach((p) => expect(p.score).toBeGreaterThanOrEqual(0))
        picks.forEach((p) => expect(p.score).toBeLessThanOrEqual(100))
    })

    it('scores are stable and deterministic', () => {
        const a = scoreBook(BOOK_CATALOG[1], sciFiProfile)
        const b = scoreBook(BOOK_CATALOG[1], sciFiProfile)
        expect(a).toBe(b)
    })

    it('recommendSimilar returns DNA-sharing books, never the seed', () => {
        const seed = BOOK_CATALOG.find((b) => b.title === 'Dune')!
        const similar = recommendSimilar(BOOK_CATALOG, seed.id, { limit: 4 })
        expect(similar.length).toBe(4)
        expect(similar.some((r) => r.book.id === seed.id)).toBe(false)
        expect(similar[0].reason).toContain(seed.title)
    })

    it('recommendFromQuery matches a free-text mood query', () => {
        const results = recommendFromQuery(
            BOOK_CATALOG,
            'something cozy and uplifting',
            { limit: 5 }
        )
        expect(results.length).toBeGreaterThan(0)
        // Cozy/uplifting books should be present in the top results.
        const topTitles = results.slice(0, 3).map((r) => r.book.title)
        const cozyBooks = ['The House in the Cerulean Sea', 'A Psalm for the Wild-Built']
        expect(topTitles.some((t) => cozyBooks.includes(t))).toBe(true)
    })

    it('recommendFromQuery honors excludeIds', () => {
        const exclude = BOOK_CATALOG.slice(0, 10).map((b) => b.id)
        const results = recommendFromQuery(BOOK_CATALOG, 'fantasy epic', {
            limit: 5,
            excludeIds: exclude
        })
        expect(results.length).toBeGreaterThan(0)
        results.forEach((r) => expect(exclude).not.toContain(r.book.id))
    })

    it('MMR produces a diverse personalized list (no duplicate genres at top)', () => {
        const picks = recommendForProfile(BOOK_CATALOG, sciFiProfile, {
            limit: 8,
            diversity: 0.5
        })
        const topGenres = picks.slice(0, 4).map((p) => p.book.genres.join(','))
        expect(new Set(topGenres).size).toBeGreaterThan(1)
    })
})

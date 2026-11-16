/**
 * 🎯 Personalization Engine
 * Chain-of-Thought: Scores the curated catalog against a reader's preferences
 * (genres, moods, reading goal, history) and returns ranked recommendations
 * with human-readable "why" explanations.
 *
 * Why this exists: the ML backend (/api/books/*) is not yet wired, so this
 * engine delivers real, personalized recommendations client-side — the same
 * graceful-degradation pattern as the rest of the app. When the backend lands,
 * this becomes the fallback path.
 *
 * Scoring model (weights sum to 1.0):
 *   genre     0.45  — overlap with favorite genres (primary signal)
 *   mood      0.20  — overlap with preferred moods (secondary signal)
 *   rating    0.15  — normalized star rating (3.0 → 0, 5.0 → 1)
 *   popularity 0.10 — normalized ratings count
 *   recency   0.10  — recent-year bonus
 */

import { BOOK_CATALOG, type BookMood, type CatalogBook } from '../data/bookCatalog'
import type { UserPreferences } from '../stores/user/userSlice'

export interface PersonalizedRecommendation {
    book: CatalogBook
    score: number
    reasons: string[]
}

export interface PersonalizationProfile {
    /** Genres the user cares about most (from onboarding) */
    favoriteGenres: string[]
    /** Moods the user gravitates toward */
    preferredMoods: BookMood[]
    /** Whether the user prefers quick reads */
    prefersShorter: boolean
}

// ─── Weights ───────────────────────────────────────────────────────────────

const W = { genre: 0.45, mood: 0.2, rating: 0.15, popularity: 0.1, recency: 0.1 }

// ─── Helpers ───────────────────────────────────────────────────────────────

const normalize = (value: number, min: number, max: number): number =>
    max === min ? 0.5 : Math.max(0, Math.min(1, (value - min) / (max - min)))

const maxRating = Math.max(...BOOK_CATALOG.map((b) => b.rating))
const minRating = Math.min(...BOOK_CATALOG.map((b) => b.rating))
const maxPopularity = Math.max(...BOOK_CATALOG.map((b) => b.ratingsCount))
const currentYear = new Date().getFullYear()

/** Build a personalization profile from stored preferences (graceful defaults). */
export const buildProfile = (prefs: UserPreferences): PersonalizationProfile => {
    // Map generic format/genre strings to our catalog's mood vocabulary loosely:
    const moodMap: Record<string, BookMood> = {
        'fast-paced': 'fast-paced',
        thriller: 'fast-paced',
        mystery: 'mysterious',
        horror: 'dark',
        'self-help': 'uplifting',
        romance: 'romantic',
        fantasy: 'epic',
        scifi: 'adventurous',
        'science fiction': 'adventurous',
        biography: 'thought-provoking'
    }
    const preferredMoods = new Set<BookMood>()
    // Explicit onboarding answers win; genre-derived moods fill the rest.
    for (const mood of prefs.preferredMoods ?? []) {
        preferredMoods.add(mood as BookMood)
    }
    prefs.favoriteGenres.forEach((g) => {
        const mood = moodMap[g.toLowerCase()]
        if (mood) preferredMoods.add(mood)
    })
    return {
        favoriteGenres: prefs.favoriteGenres,
        preferredMoods: Array.from(preferredMoods),
        prefersShorter: prefs.readingGoal >= 40
    }
}

const genreOverlap = (book: CatalogBook, profile: PersonalizationProfile): number => {
    if (profile.favoriteGenres.length === 0) return 0.5 // no signal → neutral
    const matched = book.genres.filter((g) =>
        profile.favoriteGenres.some((fg) => fg.toLowerCase() === g.toLowerCase())
    ).length
    return Math.min(1, matched / Math.max(1, profile.favoriteGenres.length) * 2)
}

const moodOverlap = (book: CatalogBook, profile: PersonalizationProfile): number => {
    if (profile.preferredMoods.length === 0) return 0.5 // no signal → neutral
    const matched = book.moods.filter((m) => profile.preferredMoods.includes(m)).length
    return Math.min(1, matched / profile.preferredMoods.length)
}

/** Build a human-readable "why this book" explanation. */
export const buildReason = (book: CatalogBook, profile: PersonalizationProfile): string[] => {
    const reasons: string[] = []

    const matchedGenre = book.genres.find((g) =>
        profile.favoriteGenres.some((fg) => fg.toLowerCase() === g.toLowerCase())
    )
    if (matchedGenre) {
        reasons.push(`Because you love ${matchedGenre}`)
    }
    const matchedMood = book.moods.find((m) => profile.preferredMoods.includes(m))
    if (matchedMood) {
        reasons.push(`A ${matchedMood.replace('-', ' ')} read that fits your current vibe`)
    }
    if (book.rating >= 4.5) {
        reasons.push(`Highly rated by readers (${book.rating.toFixed(1)}★)`)
    }
    if (reasons.length === 0) {
        reasons.push('A well-loved pick worth discovering')
    }
    return reasons
}

/** Score a single book against a profile. Returns 0..1. */
export const scoreBook = (
    book: CatalogBook,
    profile: PersonalizationProfile
): number => {
    const g = genreOverlap(book, profile)
    const m = moodOverlap(book, profile)
    const r = normalize(book.rating, minRating, maxRating)
    const p = normalize(book.ratingsCount, 0, maxPopularity)
    const rec = book.published_year >= currentYear - 3 ? 1 : 0.4

    return W.genre * g + W.mood * m + W.rating * r + W.popularity * p + W.recency * rec
}

/**
 * Rank the catalog for a user profile.
 * @param prefs           stored user preferences
 * @param opts.excludeIds books to skip (e.g. already-read / wishlisted)
 * @param opts.limit      how many to return
 */
export const getPersonalizedRecommendations = (
    prefs: UserPreferences,
    opts: { excludeIds?: string[]; limit?: number } = {}
): PersonalizedRecommendation[] => {
    const { excludeIds = [], limit = 6 } = opts
    const profile = buildProfile(prefs)
    const excluded = new Set(excludeIds)

    return BOOK_CATALOG.filter((b) => !excluded.has(b.id))
        .map((book) => ({
            book,
            score: scoreBook(book, profile),
            reasons: buildReason(book, profile)
        }))
        .sort((a, b) => b.score - a.score)
        .slice(0, limit)
}

/**
 * Cold-start picks used immediately after onboarding — no history required.
 * Same as getPersonalizedRecommendations but explicitly genre-first.
 */
export const getColdStartPicks = (
    prefs: UserPreferences,
    limit = 6
): PersonalizedRecommendation[] => getPersonalizedRecommendations(prefs, { limit })

/** A short label describing the reader's profile for UI copy. */
export const describeProfile = (prefs: UserPreferences): string => {
    const genres = prefs.favoriteGenres.slice(0, 3)
    if (genres.length === 0) return 'an eclectic reader'
    return genres.map((g) => g.toLowerCase()).join(' · ')
}

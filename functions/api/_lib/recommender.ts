/**
 * 🎯 Real-time Recommendation Engine (server-side, edge)
 * Chain-of-Thought: Hybrid content-based recommender designed to be efficient
 * for this exact workflow — a curated catalog of a few dozen books — without
 * overkilling it with heavyweight models.
 *
 * Model rationale (why TF-IDF content-based + profile scoring):
 *   1. The catalog is small (24 curated books) — embedding/LLM ranking is
 *      overkill for ranking a few dozen items.
 *   2. There is no user×book interaction history at scale yet — collaborative
 *      filtering (SVD/matrix factorization) has no data to learn from.
 *   3. Content signals are rich (title, authors, description, genres, moods),
 *      which is exactly what TF-IDF + cosine similarity exploits.
 *   4. It runs in microseconds at the edge (real-time), is fully explainable
 *      ("Because you love Fantasy"), and costs $0 per request.
 *
 * Layers:
 *   - TF-IDF vectors over weighted text fields (genres/moods boosted)
 *   - Profile scoring — exact port of the client engine (genre 45%, mood 20%,
 *     rating 15%, popularity 10%, recency 10%)
 *   - Maximal Marginal Relevance (MMR) for diversity in personalized picks
 *   - Cosine similarity for "similar to X" and free-text query matching
 *
 * LLM layer (optional, env-gated) is deliberately NOT used for ranking — see
 * functions/api/_lib/ai.ts. It only powers conversational chat.
 */

import { type Book, type RecommendationResult, BOOK_CATALOG } from './catalog'

// ─── Tokenization ──────────────────────────────────────────────────────────

/** Small English stopword list tuned for book text (no domain words dropped). */
const STOPWORDS = new Set(
    `a an and are as at be by for from has he in is it its of on that the to was were will with you your this his her their they them she not but or if what who when where how all any can do had have just more most one our out so some than then there these up we about into over after before between under again further once only own same too very should now while could would might must may don like get got make made much many us am been being did does doing`.split(
        ' '
    )
)

const tokenize = (text: string): string[] =>
    text
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, ' ')
        .split(/\s+/)
        .filter((t) => t.length > 1 && !STOPWORDS.has(t))

/** Weighted document text — field weights encode domain importance. */
const FIELD_WEIGHTS: Array<[keyof Book, number]> = [
    ['genres', 5],
    ['moods', 3],
    ['title', 4],
    ['authors', 2],
    ['description', 1]
]

const documentText = (book: Book): string[] => {
    const tokens: string[] = []
    for (const [field, weight] of FIELD_WEIGHTS) {
        const value = book[field]
        if (Array.isArray(value)) {
            for (const item of value) for (let i = 0; i < weight; i++) tokens.push(...tokenize(String(item)))
        } else {
            for (let i = 0; i < weight; i++) tokens.push(...tokenize(String(value ?? '')))
        }
    }
    return tokens
}

// ─── TF-IDF Vectorizer ──────────────────────────────────────────────────────

interface Vectorizer {
    idf: Map<string, number>
    vectorFor: (tokens: string[]) => Map<string, number>
    cosine: (a: Map<string, number>, b: Map<string, number>) => number
}

export const buildVectorizer = (books: Book[]): Vectorizer => {
    const docFreq = new Map<string, number>()
    const tokenSets = books.map(documentText)

    for (const tokens of tokenSets) {
        const seen = new Set<string>()
        for (const t of tokens) {
            if (!seen.has(t)) {
                seen.add(t)
                docFreq.set(t, (docFreq.get(t) ?? 0) + 1)
            }
        }
    }

    const N = books.length
    const idf = new Map<string, number>()
    for (const [term, df] of docFreq) {
        idf.set(term, Math.log(1 + N / (1 + df)))
    }

    const vectorFor = (tokens: string[]): Map<string, number> => {
        const tf = new Map<string, number>()
        for (const t of tokens) tf.set(t, (tf.get(t) ?? 0) + 1)
        const vec = new Map<string, number>()
        for (const [term, count] of tf) {
            const w = idf.get(term)
            if (w !== undefined) vec.set(term, (1 + Math.log(count)) * w)
        }
        return vec
    }

    const cosine = (a: Map<string, number>, b: Map<string, number>): number => {
        let dot = 0
        let normA = 0
        let normB = 0
        const [small, big] = a.size <= b.size ? [a, b] : [b, a]
        for (const [term, w] of small) {
            normA += w * w
            const other = big.get(term)
            if (other !== undefined) dot += w * other
        }
        for (const [, w] of big) normB += w * w
        if (dot === 0) return 0
        return dot / (Math.sqrt(normA) * Math.sqrt(normB))
    }

    return { idf, vectorFor, cosine }
}

// Precompute once per isolate (the worker caches modules between requests).
const VECTORIZER = buildVectorizer(BOOK_CATALOG)
const BOOK_VECTORS = new Map<string, Map<string, number>>(
    BOOK_CATALOG.map((b) => [b.id, VECTORIZER.vectorFor(documentText(b))])
)

// ─── Profile scoring (exact port of src/utils/personalization.ts) ───────────

export interface Profile {
    favoriteGenres: string[]
    preferredMoods: string[]
    prefersShorter: boolean
}

const W = { genre: 0.45, mood: 0.2, rating: 0.15, popularity: 0.1, recency: 0.1 }

const maxRating = Math.max(...BOOK_CATALOG.map((b) => b.rating))
const minRating = Math.min(...BOOK_CATALOG.map((b) => b.rating))
const maxPopularity = Math.max(...BOOK_CATALOG.map((b) => b.ratingsCount))
const currentYear = new Date().getFullYear()

const normalize = (value: number, min: number, max: number): number =>
    max === min ? 0.5 : Math.max(0, Math.min(1, (value - min) / (max - min)))

const MOOD_MAP: Record<string, string> = {
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

/** Build a profile from raw preferences (genres + reading goal). */
export const buildProfile = (prefs: {
    favoriteGenres?: string[]
    readingGoal?: number
}): Profile => {
    const favoriteGenres = prefs.favoriteGenres ?? []
    const preferredMoods = Array.from(
        new Set(
            favoriteGenres
                .map((g) => MOOD_MAP[g.toLowerCase()])
                .filter((m): m is string => Boolean(m))
        )
    )
    return {
        favoriteGenres,
        preferredMoods,
        prefersShorter: (prefs.readingGoal ?? 24) >= 40
    }
}

const genreOverlap = (book: Book, profile: Profile): number => {
    if (profile.favoriteGenres.length === 0) return 0.5
    const matched = book.genres.filter((g) =>
        profile.favoriteGenres.some((fg) => fg.toLowerCase() === g.toLowerCase())
    ).length
    return Math.min(1, (matched / Math.max(1, profile.favoriteGenres.length)) * 2)
}

const moodOverlap = (book: Book, profile: Profile): number => {
    if (profile.preferredMoods.length === 0) return 0.5
    const matched = book.moods.filter((m) => profile.preferredMoods.includes(m)).length
    return Math.min(1, matched / profile.preferredMoods.length)
}

/** Score a book against a profile → 0..1. */
export const scoreBook = (book: Book, profile: Profile): number => {
    const g = genreOverlap(book, profile)
    const m = moodOverlap(book, profile)
    const r = normalize(book.rating, minRating, maxRating)
    const p = normalize(book.ratingsCount, 0, maxPopularity)
    const rec = book.published_year >= currentYear - 3 ? 1 : 0.4
    return W.genre * g + W.mood * m + W.rating * r + W.popularity * p + W.recency * rec
}

/** Build a human-readable reason (matches the client engine). */
export const buildReason = (book: Book, profile: Profile): string => {
    const matchedGenre = book.genres.find((g) =>
        profile.favoriteGenres.some((fg) => fg.toLowerCase() === g.toLowerCase())
    )
    if (matchedGenre) return `Because you love ${matchedGenre}`
    const matchedMood = book.moods.find((m) => profile.preferredMoods.includes(m))
    if (matchedMood) return `A ${matchedMood.replace('-', ' ')} read that fits your current vibe`
    if (book.rating >= 4.5) return `Highly rated by readers (${book.rating.toFixed(1)}★)`
    return 'A well-loved pick worth discovering'
}

// ─── Recommendation APIs ────────────────────────────────────────────────────

const toResult = (book: Book, score01: number, reason: string): RecommendationResult => ({
    book,
    score: Math.round(score01 * 100),
    reason
})

/**
 * Personalized picks with MMR diversity.
 * Ranks by profile score but penalizes picks that are too similar to the ones
 * already selected (λ weights similarity vs. relevance) so the list feels
 * varied instead of repetitive.
 */
export const recommendForProfile = (
    books: Book[],
    profile: Profile,
    opts: { limit?: number; excludeIds?: string[]; diversity?: number } = {}
): RecommendationResult[] => {
    const { limit = 6, excludeIds = [], diversity = 0.3 } = opts
    const excluded = new Set(excludeIds)
    const pool = books.filter((b) => !excluded.has(b.id))
    const selected: Book[] = []

    while (selected.length < limit && pool.length > 0) {
        let best: Book | null = null
        let bestScore = -Infinity
        for (const book of pool) {
            const relevance = scoreBook(book, profile)
            let sim = 0
            if (selected.length > 0) {
                const vec = BOOK_VECTORS.get(book.id)
                sim = vec
                    ? Math.max(...selected.map((s) => VECTORIZER.cosine(vec, BOOK_VECTORS.get(s.id)!)))
                    : 0
            }
            const score = relevance - diversity * sim
            if (score > bestScore) {
                bestScore = score
                best = book
            }
        }
        if (!best) break
        selected.push(best)
        pool.splice(pool.indexOf(best), 1)
    }

    return selected.map((book) =>
        toResult(book, scoreBook(book, profile), buildReason(book, profile))
    )
}

/** "More like X" — pure TF-IDF cosine similarity. */
export const recommendSimilar = (
    books: Book[],
    seedId: string,
    opts: { limit?: number } = {}
): RecommendationResult[] => {
    const { limit = 5 } = opts
    const seed = books.find((b) => b.id === seedId)
    if (!seed) return []
    const seedVec = VECTORIZER.vectorFor(documentText(seed))

    return books
        .filter((b) => b.id !== seedId)
        .map((book) => ({
            book,
            sim: VECTORIZER.cosine(seedVec, BOOK_VECTORS.get(book.id)!)
        }))
        .sort((a, b) => b.sim - a.sim)
        .slice(0, limit)
        .map(({ book, sim }) =>
            toResult(book, sim, `Shares DNA with ${seed.title}`)
        )
}

/**
 * Free-text query matching ("something cozy like The House in the Cerulean
 * Sea"). Combines TF-IDF cosine against the query text with genre/mood
 * keyword hints so plain-language requests work.
 */
export const recommendFromQuery = (
    books: Book[],
    query: string,
    opts: { limit?: number; profile?: Profile; excludeIds?: string[] } = {}
): RecommendationResult[] => {
    const { limit = 6, profile, excludeIds = [] } = opts
    const q = query.toLowerCase()
    const excluded = new Set(excludeIds)

    // Keyword hints → genre/mood filters boost.
    const hintGenres = ALL_GENRES_FOR_QUERY.filter((g) => q.includes(g.toLowerCase()))
    const hintMoods = ALL_MOODS_FOR_QUERY.filter((m) => q.includes(m.toLowerCase()))

    const qVec = VECTORIZER.vectorFor(tokenize(query))

    return books
        .filter((b) => !excluded.has(b.id))
        .map((book) => {
            let sim = VECTORIZER.cosine(qVec, BOOK_VECTORS.get(book.id)!)
            if (hintGenres.some((g) => book.genres.includes(g))) sim += 0.35
            if (hintMoods.some((m) => book.moods.includes(m))) sim += 0.25
            // Blend in profile relevance if provided (e.g. assistant context).
            if (profile) sim += scoreBook(book, profile) * 0.2
            return { book, sim }
        })
        .sort((a, b) => b.sim - a.sim)
        .slice(0, limit)
        .map(({ book, sim }) => {
            const reason =
                hintGenres.find((g) => book.genres.includes(g)) ||
                hintMoods.find((m) => book.moods.includes(m))
            return toResult(book, Math.min(1, sim), reason ? `Matches ${reason.toLowerCase()}` : 'Matches what you asked for')
        })
}

// Precomputed query hint vocabularies (avoid re-deriving per request).
const ALL_GENRES_FOR_QUERY: string[] = Array.from(
    new Set(BOOK_CATALOG.flatMap((b) => b.genres))
)
const ALL_MOODS_FOR_QUERY: string[] = Array.from(
    new Set(BOOK_CATALOG.flatMap((b) => b.moods))
)

export { VECTORIZER }

/**
 * 🧪 AI Chat Personalization Tests
 * Chain-of-Thought: Verifies the anti-"same books" layer — conversation-aware
 * exclusion (shown/current/finished), profile-from-context fallback, LLM JSON
 * book-pick parsing, and that the LOCAL engine (no LLM keys) rotates picks
 * when the same question is asked repeatedly with a growing `shown` set.
 */

import { describe, expect, it } from 'vitest'
import {
    excludeSetFor,
    handleChat,
    isNearDuplicate,
    matchLlmBooksToCatalog,
    normalizeTitle,
    parseLlmBookPicks,
    profileFromContext,
    sanitizeControlChars,
    type ChatContext
} from '../functions/api/_lib/ai'
import { BOOK_CATALOG } from '../functions/api/_lib/catalog'

const NO_ENV = {}

describe('normalizeTitle', () => {
    it('strips articles, punctuation and case for fuzzy matching', () => {
        expect(normalizeTitle('The Name of the Wind')).toBe('name of wind')
        expect(normalizeTitle('name of the wind')).toBe('name of wind')
        expect(normalizeTitle('  Project  Hail  Mary!  ')).toBe('project hail mary')
    })
})

describe('sanitizeControlChars', () => {
    it('removes raw control characters but keeps newlines and tabs', () => {
        const dirty = 'wonderful choice \u0014 it\u0007s short\nand \t fine'
        const clean = sanitizeControlChars(dirty)
        expect(clean).not.toContain('\u0014')
        expect(clean).not.toContain('\u0007')
        expect(clean).toContain('\n')
        expect(clean).toContain('\t')
        // Output must be valid strict JSON when serialized.
        expect(() => JSON.parse(JSON.stringify({ reply: clean }))).not.toThrow()
    })
})

describe('isNearDuplicate', () => {
    it('flags same-author anthology editions that embed the title', () => {
        const existing: Array<{ title: string; authors: string }> = [
            { title: 'The Murder of Roger Ackroyd', authors: 'Agatha Christie' }
        ]
        const anthology = {
            id: 'x',
            title: "Masterpieces of Murder (And Then There Were None / Death on the Nile / The Murder of Roger Ackroyd / Witness for the Prosecution)",
            authors: 'Agatha Christie',
            cover_url: '',
            rating: 4,
            ratingsCount: 0,
            genres: ['Mystery'],
            moods: [],
            published_year: 1939,
            page_count: 0,
            description: ''
        }
        expect(isNearDuplicate(existing as any, anthology as any)).toBe(true)
    })

    it('keeps a different book by the same author', () => {
        const existing: Array<{ title: string; authors: string }> = [
            { title: 'The Murder of Roger Ackroyd', authors: 'Agatha Christie' }
        ]
        const other = {
            id: 'y',
            title: 'Death on the Nile',
            authors: 'Agatha Christie',
            cover_url: '',
            rating: 4,
            ratingsCount: 0,
            genres: ['Mystery'],
            moods: [],
            published_year: 1937,
            page_count: 0,
            description: ''
        }
        expect(isNearDuplicate(existing as any, other as any)).toBe(false)
    })

    it('flags edition/adaptation titles that contain the existing title', () => {
        const existing: Array<{ title: string; authors: string }> = [
            { title: '1984', authors: 'George Orwell' },
            { title: 'The House in the Cerulean Sea', authors: 'T.J. Klune' }
        ]
        const adaptation = {
            id: 'z',
            title: '1984 (adaptation)',
            authors: 'George Orwell; adapted',
            cover_url: '',
            rating: 4,
            ratingsCount: 0,
            genres: ['Fiction'],
            moods: [],
            published_year: 1949,
            page_count: 0,
            description: ''
        }
        const workbook = {
            id: 'w',
            title: 'Workbook on House in the Cerulean Sea',
            authors: 'Someone Else',
            cover_url: '',
            rating: 3,
            ratingsCount: 0,
            genres: ['Study Aids'],
            moods: [],
            published_year: 2022,
            page_count: 0,
            description: ''
        }
        // Different author string, but the title contains the existing one.
        expect(isNearDuplicate(existing as any, adaptation as any)).toBe(true)
        expect(isNearDuplicate(existing as any, workbook as any)).toBe(true)
    })
})

describe('parseLlmBookPicks', () => {
    it('extracts books from a fenced JSON block with surrounding prose', () => {
        const reply = `Here are three great picks for you!
\`\`\`json
{"books":[
  {"title":"Dune","author":"Frank Herbert","reason":"Classic sci-fi worldbuilding"},
  {"title":"The Martian","author":"Andy Weir","reason":"Survival science"},
  {"title":"Piranesi","author":"Susanna Clarke","reason":"Strange and beautiful"}
]}
\`\`\`
Happy reading!`
        const picks = parseLlmBookPicks(reply)
        expect(picks).toHaveLength(3)
        expect(picks[0].title).toBe('Dune')
        expect(picks[2].reason).toContain('beautiful')
    })

    it('extracts a bare JSON object embedded in prose (no fences)', () => {
        const reply = `My picks: {"books":[{"title":"Circe","author":"Madeline Miller","reason":"Myth retold"}]} Hope that helps!`
        const picks = parseLlmBookPicks(reply)
        expect(picks).toHaveLength(1)
        expect(picks[0].title).toBe('Circe')
    })

    it('returns [] for replies with no parseable books JSON', () => {
        expect(parseLlmBookPicks('I love reading books!')).toEqual([])
        expect(parseLlmBookPicks('{"not_books": true}')).toEqual([])
    })

    it('drops entries without a real title', () => {
        const picks = parseLlmBookPicks(
            '{"books":[{"title":"","reason":"empty"},{"title":"Dune"}]}'
        )
        expect(picks).toHaveLength(1)
        expect(picks[0].title).toBe('Dune')
    })
})

describe('matchLlmBooksToCatalog', () => {
    it('matches LLM titles to real catalog books and reports missing ones', () => {
        const { catalog, missing } = matchLlmBooksToCatalog([
            { title: 'Dune', author: 'Frank Herbert', reason: 'Classic' },
            { title: 'The Name of the Wind', author: 'Patrick Rothfuss', reason: 'Epic fantasy' },
            { title: 'A Totally Made-Up Book', author: 'Nobody', reason: 'Fake' }
        ])
        expect(catalog.map((s) => s.title)).toContain('Dune')
        expect(catalog.map((s) => s.title)).toContain('The Name of the Wind')
        expect(catalog.every((s) => s.reason)).toBe(true)
        expect(missing.map((m) => m.title)).toContain('A Totally Made-Up Book')
    })
})

describe('excludeSetFor', () => {
    it('excludes already-shown ids, the current book and recently finished', () => {
        const dune = BOOK_CATALOG.find((b) => b.title === 'Dune')!
        const martian = BOOK_CATALOG.find((b) => b.title === 'The Martian')!
        const context: ChatContext = {
            currentBook: { title: 'Dune', authors: 'Frank Herbert', progressPct: 40 },
            recentlyFinished: [{ title: 'The Martian', authors: 'Andy Weir', genres: ['Science Fiction'] }]
        }
        const excluded = excludeSetFor(['b-01', 'b-02'], context)
        expect(excluded.has('b-01')).toBe(true)
        expect(excluded.has('b-02')).toBe(true)
        expect(excluded.has(dune.id)).toBe(true)
        expect(excluded.has(martian.id)).toBe(true)
    })
})

describe('profileFromContext', () => {
    it('derives genre affinity from the reader shelf when prefs are empty', () => {
        const profile = profileFromContext(
            {},
            {
                recentlyFinished: [
                    { title: 'Dune', authors: 'Frank Herbert', genres: ['Science Fiction', 'Fantasy'] },
                    { title: 'The Martian', authors: 'Andy Weir', genres: ['Science Fiction', 'Adventure'] }
                ]
            }
        )
        expect(profile.favoriteGenres).toContain('Science Fiction')
        expect(profile.favoriteGenres.length).toBeGreaterThan(0)
        expect(profile.favoriteGenres.length).toBeLessThanOrEqual(3)
    })

    it('keeps explicit prefs and ignores context inference', () => {
        const profile = profileFromContext(
            { favoriteGenres: ['Romance'] },
            { recentlyFinished: [{ title: 'Dune', authors: 'x', genres: ['Science Fiction'] }] }
        )
        expect(profile.favoriteGenres).toEqual(['Romance'])
    })
})

describe('handleChat (local engine, no LLM keys)', () => {
    it('returns DIFFERENT books when the same question is repeated with shown', async () => {
        const first = await handleChat(NO_ENV, 'recommend me a book', {}, undefined, [], [])
        expect(first.bookSuggestions).toBeDefined()
        expect(first.bookSuggestions!.length).toBeGreaterThan(0)
        const firstIds = first.bookSuggestions!.map((s) => s.id)

        // Second identical question, but now the first batch is "shown".
        const second = await handleChat(NO_ENV, 'recommend me a book', {}, undefined, [], firstIds)
        const secondIds = second.bookSuggestions!.map((s) => s.id)
        expect(secondIds.length).toBeGreaterThan(0)
        expect(secondIds.some((id) => firstIds.includes(id))).toBe(false)

        // Third question excludes both prior batches → still fresh.
        const third = await handleChat(
            NO_ENV,
            'recommend me a book',
            {},
            undefined,
            [],
            [...firstIds, ...secondIds]
        )
        const thirdIds = third.bookSuggestions!.map((s) => s.id)
        expect(thirdIds.some((id) => firstIds.includes(id) || secondIds.includes(id))).toBe(false)
    })

    it('never recommends the current book or recently finished titles', async () => {
        const context: ChatContext = {
            currentBook: { title: 'Dune', authors: 'Frank Herbert', progressPct: 50 },
            recentlyFinished: [{ title: 'The Martian', authors: 'Andy Weir', genres: ['Science Fiction'] }]
        }
        const result = await handleChat(
            NO_ENV,
            'recommend something like science fiction',
            {},
            context,
            [],
            []
        )
        const ids = result.bookSuggestions!.map((s) => s.id)
        expect(ids).not.toContain('b-11') // Dune
        expect(ids).not.toContain('b-18') // The Martian
    })

    it('suggestions carry personalization reasons', async () => {
        const result = await handleChat(NO_ENV, 'something cozy', {}, undefined, [], [])
        expect(result.bookSuggestions!.every((s) => s.reason)).toBe(true)
    })

    it('falls back to local engine with reasons even without any env config', async () => {
        const result = await handleChat(NO_ENV, 'recommend a thriller', {}, undefined, [], [])
        expect(result.model).toBe('goodbooks-hybrid')
        expect(result.reply.length).toBeGreaterThan(0)
        expect(result.bookSuggestions!.length).toBeGreaterThan(0)
    })
})

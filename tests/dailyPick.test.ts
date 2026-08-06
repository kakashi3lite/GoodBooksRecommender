/**
 * ✨ Daily Pick Tests
 * Chain-of-Thought: the daily hook must be deterministic per day and always
 * return a real catalog book.
 */

import { describe, expect, it } from 'vitest'
import { BOOK_CATALOG } from '../src/data/bookCatalog'
import { dailyPickReason, getDailyPick } from '../src/utils/dailyPick'

describe('dailyPick', () => {
    it('returns a real catalog book for any date', () => {
        const pick = getDailyPick(new Date('2026-08-07T12:00:00'))
        expect(BOOK_CATALOG.some((b) => b.id === pick.id)).toBe(true)
        expect(pick.title).toBeTruthy()
    })

    it('is stable within the same day', () => {
        const a = getDailyPick(new Date('2026-08-07T00:00:00'))
        const b = getDailyPick(new Date('2026-08-07T23:59:59'))
        expect(a.id).toBe(b.id)
    })

    it('produces a human reason', () => {
        const pick = getDailyPick(new Date('2026-08-07T12:00:00'))
        expect(dailyPickReason(pick).length).toBeGreaterThan(0)
    })
})

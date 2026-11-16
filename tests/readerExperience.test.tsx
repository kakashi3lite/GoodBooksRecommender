/**
 * 🧪 New-component coverage — progressbar semantics, latest-wins, honest stats
 *
 * These pin the three accessibility/honesty primitives introduced by the
 * reader-audit fixes, so a future refactor cannot silently:
 *   - drop the progressbar role (screen readers lose the core metric),
 *   - reintroduce out-of-order search results,
 *   - or bring back the catalog fallback that fabricated a reader's taste.
 */

import { act, render, renderHook, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ProgressBar from '../src/components/UI/ProgressBar'
import { BOOK_CATALOG } from '../src/data/bookCatalog'
import { useLatestRequest } from '../src/hooks/useLatestRequest'
import { buildGenreBreakdown, pagesPerActiveDay, readingDays } from '../src/utils/readingStats'

describe('ProgressBar', () => {
    it('exposes progressbar semantics with a label and value text', () => {
        render(
            <ProgressBar value={53} label="Dune progress" valueText="page 210 of 400" />
        )
        const bar = screen.getByRole('progressbar', { name: 'Dune progress' })
        expect(bar).toHaveAttribute('aria-valuenow', '53')
        expect(bar).toHaveAttribute('aria-valuemin', '0')
        expect(bar).toHaveAttribute('aria-valuemax', '100')
        expect(bar).toHaveAttribute('aria-valuetext', 'page 210 of 400')
    })

    it('clamps values outside 0..100 instead of rendering a broken bar', () => {
        const { rerender } = render(<ProgressBar value={148} label="over" />)
        expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100')

        rerender(<ProgressBar value={-20} label="under" />)
        expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')

        rerender(<ProgressBar value={Number.NaN} label="nan" />)
        expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0')
    })
})

describe('useLatestRequest', () => {
    it('discards a slow older result and keeps the newest one', async () => {
        const { result } = renderHook(() => useLatestRequest())

        let resolveOld: (value: string) => void = () => { }
        let resolveNew: (value: string) => void = () => { }

        let oldPromise: Promise<string | null> = Promise.resolve(null)
        let newPromise: Promise<string | null> = Promise.resolve(null)

        await act(async () => {
            oldPromise = result.current.run(
                () => new Promise<string>((resolve) => { resolveOld = resolve })
            )
            newPromise = result.current.run(
                () => new Promise<string>((resolve) => { resolveNew = resolve })
            )
        })

        // The newer request resolves first, the older one afterwards.
        resolveNew('dunes')
        resolveOld('dune')

        await act(async () => {
            await expect(newPromise).resolves.toBe('dunes')
            await expect(oldPromise).resolves.toBeNull()
        })
    })

    it('aborts the in-flight request when cancelled', async () => {
        const { result } = renderHook(() => useLatestRequest())
        let seenSignal: AbortSignal | null = null

        const promise = result.current.run(
            (signal) =>
                new Promise<string>((resolve) => {
                    seenSignal = signal
                    signal.addEventListener('abort', () => resolve('aborted'))
                })
        )
        act(() => result.current.cancel())

        await expect(promise).resolves.toBeNull()
        expect(seenSignal?.aborted).toBe(true)
    })
})

describe('buildGenreBreakdown', () => {
    it('returns nothing when the reader has no books (no fabricated chart)', () => {
        expect(buildGenreBreakdown([], BOOK_CATALOG)).toEqual([])
        // Unknown ids must not resurrect a catalog-wide distribution.
        expect(buildGenreBreakdown(['not-a-book'], BOOK_CATALOG)).toEqual([])
    })

    it('counts a book once even when it is both wishlisted and finished', () => {
        const book = BOOK_CATALOG[0]
        const once = buildGenreBreakdown([book.id], BOOK_CATALOG)
        const twice = buildGenreBreakdown([book.id, book.id], BOOK_CATALOG)
        expect(twice).toEqual(once)
        expect(once[0].count).toBe(1)
        expect(once[0].pct).toBe(100)
    })

    it('sorts by count and scales bars against the top genre', () => {
        const slices = buildGenreBreakdown(
            BOOK_CATALOG.slice(0, 6).map((book) => book.id),
            BOOK_CATALOG
        )
        expect(slices.length).toBeGreaterThan(0)
        expect(slices[0].pct).toBe(100)
        for (let i = 1; i < slices.length; i += 1) {
            expect(slices[i - 1].count).toBeGreaterThanOrEqual(slices[i].count)
        }
    })
})

describe('readingStats day helpers', () => {
    it('ignores recovered days when counting active days and averages', () => {
        const log = [
            { date: '2026-11-15', pages: 40 },
            { date: '2026-11-16', pages: 20 },
            { date: '2026-11-14', pages: 0, recovered: true }
        ]
        expect(readingDays(log)).toBe(2)
        expect(pagesPerActiveDay(log)).toBe(30)
    })

    it('returns 0 rather than inventing a baseline with no history', () => {
        expect(pagesPerActiveDay([])).toBe(0)
    })
})

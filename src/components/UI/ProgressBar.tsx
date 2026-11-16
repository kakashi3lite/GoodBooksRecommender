/**
 * 📈 ProgressBar — the app's core metric, exposed as a real progressbar.
 *
 * Chain-of-Thought (accessibility):
 *   Reading progress is the number this product is built around, and it was
 *   rendered as a bare `<div>` with an inline width — literally invisible to a
 *   screen reader. A reader using VoiceOver got a book title and silence where
 *   "68% complete, 214 of 688 pages" should be.
 *
 *   This component centralises three things that are easy to get wrong per
 *   call-site:
 *     1. Semantics — `role="progressbar"` + aria-valuenow/min/max and a label.
 *     2. Clamping — a value outside 0..100 can never produce a broken bar
 *        (progress overruns used to be possible before sessions were clamped).
 *     3. Motion safety — the fill transition is disabled under
 *        `prefers-reduced-motion` (handled globally in materials.css).
 *
 * It is deliberately dumb: no state, no timers, no animation library.
 */

import React from 'react'

type ProgressTone = 'accent' | 'success' | 'gradient'

interface ProgressBarProps {
    /** 0–100. Values outside the range are clamped. */
    value: number
    /** Screen-reader label, e.g. "Dune reading progress". */
    label: string
    /** Optional human-readable value text, e.g. "214 of 688 pages". */
    valueText?: string
    /** Bar height in Tailwind units (1 = 4px). */
    size?: 1 | 1.5 | 2
    tone?: ProgressTone
    className?: string
}

const TONE_CLASS: Record<ProgressTone, string> = {
    accent: 'bg-blue-600',
    success: 'bg-green-500',
    gradient: 'bg-gradient-to-r from-purple-500 to-blue-500'
}

const TRACK_HEIGHT: Record<NonNullable<ProgressBarProps['size']>, string> = {
    1: 'h-1',
    1.5: 'h-1.5',
    2: 'h-2'
}

/**
 * Accessible, clamped progress bar.
 *
 * @example
 * <ProgressBar value={progressOf(entry)} label={`${book.title} progress`} valueText={`${entry.currentPage} of ${book.page_count} pages`} />
 */
const ProgressBar: React.FC<ProgressBarProps> = ({
    value,
    label,
    valueText,
    size = 2,
    tone = 'accent',
    className = ''
}) => {
    const clamped = Math.max(0, Math.min(100, Math.round(Number.isFinite(value) ? value : 0)))

    return (
        <div
            role="progressbar"
            aria-label={label}
            aria-valuenow={clamped}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuetext={valueText ?? `${clamped}%`}
            className={`w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700 ${TRACK_HEIGHT[size]} ${className}`}
        >
            <div
                className={`h-full rounded-full transition-all duration-300 ${TONE_CLASS[tone]}`}
                style={{ width: `${clamped}%` }}
            />
        </div>
    )
}

export default ProgressBar

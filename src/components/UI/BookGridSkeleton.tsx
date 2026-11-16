/**
 * BookGridSkeleton — geometry-matched loading placeholders.
 *
 * Chain-of-Thought:
 *   Spinners tell a reader "wait"; skeletons tell them "here's what's coming".
 *   Because this mirrors the real card grid (2:3 cover + two text lines +
 *   action row), the layout does not reflow when data lands — the page feels
 *   instant instead of jumpy. See NN/g "Skeleton Screens" and Apple HIG
 *   "Loading": placeholders should match the content they replace.
 *
 * Pure CSS shimmer (materials.css) — no animation library, no layout cost.
 */

import React from 'react'

interface BookGridSkeletonProps {
    /** How many placeholder cards to render (match the real grid slice). */
    count?: number
    className?: string
}

const SkeletonCard: React.FC = () => (
    <div className="surface-1 p-4" aria-hidden="true">
        <div className="mb-3 flex items-start gap-3">
            <div className="w-[4.5rem] shrink-0">
                <div className="skeleton skeleton-cover" />
            </div>
            <div className="min-w-0 flex-1 space-y-2 pt-1">
                <div className="skeleton skeleton-line-lg w-11/12" />
                <div className="skeleton skeleton-line w-7/12" />
                <div className="skeleton skeleton-line w-9/12" />
            </div>
        </div>
        <div className="space-y-2">
            <div className="skeleton skeleton-line w-full" />
            <div className="skeleton skeleton-line w-10/12" />
            <div className="skeleton h-9 w-full rounded-xl" />
        </div>
    </div>
)

/**
 * Renders a responsive grid of skeleton book cards.
 * Announce politely so screen readers know content is loading, not missing.
 */
const BookGridSkeleton: React.FC<BookGridSkeletonProps> = ({
    count = 6,
    className = 'grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3'
}) => (
    <div className={className} role="status" aria-live="polite" aria-label="Loading recommendations">
        <span className="sr-only">Loading recommendations…</span>
        {Array.from({ length: count }).map((_, index) => (
            <SkeletonCard key={index} />
        ))}
    </div>
)

export default BookGridSkeleton

/**
 * 📚 Virtualized Book List Component
 * Chain-of-Thought: Render large book collections efficiently with a virtualized
 * window — only visible rows mount to the DOM.
 * Time Complexity: O(windowSize) DOM nodes regardless of collection size
 */

import React, { useEffect, useRef, useState } from 'react'
import { BookCard } from './BookCard'

export interface VirtualizedBook {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    genres?: string[]
    description?: string
    ai_recommendation_score?: number
}

interface VirtualizedBookListProps {
    books: VirtualizedBook[]
    /** Number of columns in the responsive grid */
    columns?: number
    /** Fixed row height in px */
    rowHeight?: number
    /** Container height in px */
    height?: number
    onBookClick?: (book: VirtualizedBook) => void
    className?: string
}

/**
 * VirtualizedBookList — windowed grid for very large book lists.
 * Uses an overscan buffer so scrolling stays smooth at 60fps.
 */
const VirtualizedBookList: React.FC<VirtualizedBookListProps> = ({
    books,
    columns = 4,
    rowHeight = 380,
    height = 800,
    onBookClick,
    className = ''
}) => {
    const containerRef = useRef<HTMLDivElement>(null)
    const [scrollTop, setScrollTop] = useState(0)
    const [viewportWidth, setViewportWidth] = useState(0)

    // Track container dimensions for responsive column count
    useEffect(() => {
        const el = containerRef.current
        if (!el) return

        const updateWidth = () => setViewportWidth(el.clientWidth)
        updateWidth()

        const observer = new ResizeObserver(updateWidth)
        observer.observe(el)
        return () => observer.disconnect()
    }, [])

    // Clamp columns based on actual viewport width
    const effectiveColumns = Math.max(
        1,
        Math.min(columns, viewportWidth > 0 ? Math.floor(viewportWidth / 220) : columns)
    )

    const rowCount = Math.ceil(books.length / effectiveColumns)
    const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - 1)
    const endRow = Math.min(
        rowCount,
        Math.ceil((scrollTop + height) / rowHeight) + 1
    )

    const visibleBooks = books.slice(
        startRow * effectiveColumns,
        endRow * effectiveColumns
    )

    return (
        <div
            ref={containerRef}
            className={`virtualized-book-list overflow-auto ${className}`}
            style={{ height }}
            onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
            role="list"
            aria-label="Book collection"
        >
            <div
                style={{
                    height: rowCount * rowHeight,
                    position: 'relative'
                }}
            >
                <div
                    className="grid gap-4"
                    style={{
                        gridTemplateColumns: `repeat(${effectiveColumns}, minmax(0, 1fr))`,
                        transform: `translateY(${startRow * rowHeight}px)`
                    }}
                >
                    {visibleBooks.map((book) => (
                        <div key={book.id} style={{ height: rowHeight }} role="listitem">
                            <BookCard
                                book={book as never}
                                onClick={() => onBookClick?.(book)}
                            />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default VirtualizedBookList

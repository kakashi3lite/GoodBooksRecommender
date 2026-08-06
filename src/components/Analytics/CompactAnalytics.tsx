/**
 * 📊 CompactAnalytics — lightweight sidebar analytics
 * Chain-of-Thought: the previous sidebar analytics bundled all of recharts
 * (≈380 KB gzip chunk) on EVERY page just to render compact tiles. This
 * replacement renders the same real metrics with pure CSS bars — zero chart
 * library, zero extra bytes on the critical path.
 *
 * Memory: reads performance metrics + book cache from Redux (same sources).
 * Forward-Thinking: keeps the real API analytics reachable via
 * `/api/analytics/*` (see functions/api/analytics) without the bundle cost.
 */

import { motion } from 'framer-motion'
import React, { useEffect, useState } from 'react'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { selectBookCache } from '../../stores/books/booksSlice'
import {
    selectPerformanceMetrics,
    trackPerformanceMetrics
} from '../../stores/dashboard/dashboardSlice'

interface GenreBar {
    name: string
    count: number
    pct: number
}

/**
 * Lightweight sidebar analytics — real metrics, CSS-only visualization.
 */
export const CompactAnalytics: React.FC = () => {
    const dispatch = useAppDispatch()
    const performanceMetrics = useAppSelector(selectPerformanceMetrics)
    const bookCache = useAppSelector(selectBookCache)

    // Local genre distribution (pure CSS bars — no chart lib needed).
    const [genreBars, setGenreBars] = useState<GenreBar[]>([])

    // Keep the performance metrics fresh while the sidebar is visible.
    useEffect(() => {
        dispatch(trackPerformanceMetrics())
    }, [dispatch])

    // Derive a compact genre breakdown from the cached catalog.
    useEffect(() => {
        const counts = new Map<string, number>()
        for (const book of Object.values(bookCache)) {
            for (const genre of book.genres ?? []) {
                counts.set(genre, (counts.get(genre) ?? 0) + 1)
            }
        }
        const total = Array.from(counts.values()).reduce((a, b) => a + b, 0) || 1
        setGenreBars(
            Array.from(counts.entries())
                .map(([name, count]) => ({ name, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 5)
                .map((item) => ({ ...item, pct: Math.round((item.count / total) * 100) }))
        )
    }, [bookCache])

    const booksCompleted = Object.values(bookCache).length
    const formattedMemory =
        performanceMetrics.memoryUsage !== null
            ? `${performanceMetrics.memoryUsage.toFixed(1)} MB`
            : 'Not available'

    return (
        <motion.div
            className="dashboard-analytics-compact"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4 }}
            aria-label="Dashboard metrics"
        >
            <h3 className="analytics-title">Dashboard Metrics</h3>

            <div className="metrics-container">
                <div className="metric-item">
                    <span className="metric-label">Load Time</span>
                    <span className="metric-value">
                        {Math.round(performanceMetrics.loadTime)}ms
                    </span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">Memory</span>
                    <span className="metric-value">{formattedMemory}</span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">Books Completed</span>
                    <span className="metric-value">{booksCompleted}</span>
                </div>
                <div className="metric-item">
                    <span className="metric-label">Reading Streak</span>
                    <span className="metric-value">
                        {Math.max(0, Math.floor((Date.now() - performanceMetrics.lastUpdated) / 86_400_000))} days
                    </span>
                </div>
            </div>

            {/* Lightweight genre distribution — CSS bars, no chart library */}
            {genreBars.length > 0 && (
                <div className="compact-genres" aria-label="Genre distribution">
                    <h4 className="compact-genres-title">Top Genres</h4>
                    <ul className="compact-genre-list">
                        {genreBars.map((genre) => (
                            <li className="compact-genre-row" key={genre.name}>
                                <span className="compact-genre-name" title={genre.name}>
                                    {genre.name}
                                </span>
                                <span className="compact-genre-track">
                                    <span
                                        className="compact-genre-fill"
                                        style={{ width: `${genre.pct}%` }}
                                    />
                                </span>
                                <span className="compact-genre-count">{genre.count}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </motion.div>
    )
}

export default CompactAnalytics

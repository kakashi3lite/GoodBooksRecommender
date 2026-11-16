/**
 * 🔍 Discover Page
 * Chain-of-Thought: AI-powered book discovery with a REAL search box.
 * The search input queries the live API (/api/books/search?q=) with
 * debouncing, so typing actually returns results — no more dead input.
 * Below it: personalized AI recommendations + live web trending.
 */

import { motion } from 'framer-motion'
import { Search, Sparkles, X } from 'lucide-react'
import React, { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useLatestRequest } from '../../hooks/useLatestRequest'
import { useAppSelector } from '../../hooks/redux'
import { API_ENDPOINTS } from '../../utils/api'
import { catalogGenreChips, matchesGenre } from '../../utils/bookFilters'
import AIBookRecommendations from '../AI/AIBookRecommendations'
import { BookCard } from '../UI/BookCard'
import WebTrending from './WebTrending'

interface SearchResult {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    ratingsCount?: number
    genres: string[]
    published_year: number
    description: string
}

/**
 * Discover — the reader's exploration surface: live search + AI picks + web trends.
 * Accepts an optional ?q= query param (e.g. from the dashboard header search).
 */
const Discover: React.FC = () => {
    const [searchParams] = useSearchParams()
    const [query, setQuery] = useState(() => searchParams.get('q') ?? '')
    const [results, setResults] = useState<SearchResult[]>([])
    const [searching, setSearching] = useState(false)
    const [searched, setSearched] = useState(false)
    const [activeGenre, setActiveGenre] = useState('')
    const debounceRef = useRef<number | undefined>(undefined)
    // Latest-wins: a slow answer for an older query must never replace a newer one.
    const { run: runLatest } = useLatestRequest()
    const navigate = useNavigate()
    const favoriteGenres = useAppSelector((state) => state.user.preferences?.favoriteGenres ?? [])

    // Reader-first genre chips: favorite genres ranked first, with live counts
    // from the catalog (recognition + identity + loss-aversion reassurance).
    const genreChips = catalogGenreChips(favoriteGenres)
    const genreFilter = activeGenre ? [activeGenre] : []

    // Applied to every section so the filter behaves identically sitewide.
    const visibleResults = results.filter((b) => matchesGenre(b.genres, activeGenre))

    /**
     * Chain-of-Thought: keep the box in sync when arriving with ?q= (e.g. the
     * dashboard header search navigates here with a query).
     */
    useEffect(() => {
        const q = searchParams.get('q')
        if (q !== null) setQuery(q)
    }, [searchParams])

    /**
     * Chain-of-Thought: debounced live search — 350ms after the user pauses,
     * query the edge API (catalog hits + Google Books + Open Library) and
     * render a real result grid. Finds ANY book, not just the curated list.
     */
    useEffect(() => {
        if (!query.trim()) {
            setResults([])
            setSearched(false)
            return
        }
        setSearching(true)
        window.clearTimeout(debounceRef.current)
        debounceRef.current = window.setTimeout(async () => {
            try {
                const data = await runLatest(async (signal) => {
                    const res = await fetch(
                        `${API_ENDPOINTS.books.webSearch()}?q=${encodeURIComponent(query.trim())}&limit=20`,
                        { signal }
                    )
                    return (await res.json()) as { data?: SearchResult[] }
                })
                // `null` = a newer query already started; leave its state alone.
                if (data) {
                    setResults(data.data ?? [])
                    setSearched(true)
                    setSearching(false)
                }
            } catch {
                setResults([])
                setSearched(true)
                setSearching(false)
            }
        }, 350)
        return () => window.clearTimeout(debounceRef.current)
    }, [query, runLatest])

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="min-h-screen page-surface p-4 sm:p-8"
        >
            <div className="max-w-7xl mx-auto">
                {/* Hero */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                        <Sparkles className="w-8 h-8 text-purple-500" />
                        Discover Your Next Favorite Book
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Search the catalog, get AI picks, and browse live trending from the web.
                    </p>
                </div>

                {/* Real search bar */}
                <div className="relative mb-8 max-w-2xl">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search books, authors, or genres — try 'dune' or 'cozy'…"
                        className="w-full pl-12 pr-10 py-3 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white placeholder-gray-400 shadow-lg"
                        aria-label="Search books"
                    />
                    {query && (
                        <button
                            type="button"
                            aria-label="Clear search"
                            onClick={() => setQuery('')}
                            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Genre filter — favorite-first chips with counts. Applies to
                    search results, AI picks, and trending (sitewide consistency). */}
                {genreChips.length > 0 && (
                    <div className="mb-8 flex flex-wrap items-center gap-2" aria-label="Filter by genre">
                        <button
                            onClick={() => setActiveGenre('')}
                            aria-pressed={activeGenre === ''}
                            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${activeGenre === ''
                                ? 'bg-purple-600 text-white'
                                : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                                }`}
                        >
                            All genres
                        </button>
                        {genreChips.map((chip) => (
                            <button
                                key={chip.genre}
                                onClick={() => setActiveGenre(activeGenre === chip.genre ? '' : chip.genre)}
                                aria-pressed={activeGenre === chip.genre}
                                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${activeGenre === chip.genre
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                                    }`}
                            >
                                {chip.genre}
                                <span className={`ml-1.5 ${activeGenre === chip.genre ? 'text-purple-100' : 'text-gray-400'}`}>
                                    {chip.count}
                                </span>
                            </button>
                        ))}
                    </div>
                )}

                {/* Search results */}
                {searched && (
                    <section className="mb-12" aria-label="Search results">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                            {searching
                                ? 'Searching…'
                                : visibleResults.length > 0
                                    ? `${visibleResults.length} result${visibleResults.length === 1 ? '' : 's'} for "${query}"${activeGenre ? ` in ${activeGenre}` : ''}`
                                    : `No matches for "${query}"${activeGenre ? ` in ${activeGenre}` : ''}`}
                        </h2>

                        {/* Cover-shaped skeletons: the grid keeps its geometry while
                            the live search resolves, so results don't "pop" the layout. */}
                        {searching && (
                            <div
                                className="grid"
                                role="status"
                                aria-live="polite"
                                aria-label="Searching for books"
                                style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
                                    gap: '1.25rem'
                                }}
                            >
                                <span className="sr-only">Searching for books…</span>
                                {Array.from({ length: 8 }).map((_, index) => (
                                    <div key={index} className="space-y-2" aria-hidden="true">
                                        <div className="skeleton skeleton-cover" />
                                        <div className="skeleton skeleton-line-lg w-10/12" />
                                        <div className="skeleton skeleton-line w-7/12" />
                                    </div>
                                ))}
                            </div>
                        )}

                        {!searching && visibleResults.length > 0 && (
                            <div
                                className="grid gap-5"
                                style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
                                    gap: '1.25rem'
                                }}
                            >
                                {visibleResults.map((book) => (
                                    <BookCard
                                        key={book.id}
                                        book={book}
                                        onClick={() => navigate(`/book/${encodeURIComponent(book.id)}`)}
                                    />
                                ))}
                            </div>
                        )}
                        {!searching && visibleResults.length === 0 && (
                            <div className="surface-1 max-w-xl p-6">
                                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                                    No exact match — but the web is wide
                                </p>
                                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                    Try a shorter title, the author&apos;s name, or describe the
                                    feeling you want (for example “cozy fantasy”). Live trending is
                                    waiting below, too.
                                </p>
                                <div className="mt-4 flex flex-wrap gap-2">
                                    <button
                                        onClick={() => setQuery('')}
                                        className="pressable rounded-xl bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700"
                                    >
                                        Clear search
                                    </button>
                                    {activeGenre && (
                                        <button
                                            onClick={() => setActiveGenre('')}
                                            className="pressable rounded-xl border border-gray-300 bg-white px-4 py-2 text-xs font-semibold text-gray-700 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
                                        >
                                            Remove “{activeGenre}” filter
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}
                    </section>
                )}

                {/* AI Recommendations + live web trending */}
                {(!searched || visibleResults.length === 0) && (
                    <>
                        <AIBookRecommendations limit={12} strategy="hybrid" filterGenres={genreFilter} />
                        <WebTrending limit={12} filterGenres={genreFilter} />
                    </>
                )}
            </div>
        </motion.div>
    )
}

export default Discover

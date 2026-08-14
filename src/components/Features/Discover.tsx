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
import { API_ENDPOINTS } from '../../utils/api'
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
    const debounceRef = useRef<number | undefined>(undefined)
    const navigate = useNavigate()

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
                const res = await fetch(
                    `${API_ENDPOINTS.books.webSearch()}?q=${encodeURIComponent(query.trim())}&limit=20`
                )
                const data = (await res.json()) as { data?: SearchResult[] }
                setResults(data.data ?? [])
            } catch {
                setResults([])
            } finally {
                setSearching(false)
                setSearched(true)
            }
        }, 350)
        return () => window.clearTimeout(debounceRef.current)
    }, [query])

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-950 dark:to-indigo-950 p-4 sm:p-8"
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

                {/* Search results */}
                {searched && (
                    <section className="mb-12" aria-label="Search results">
                        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                            {searching
                                ? 'Searching…'
                                : results.length > 0
                                    ? `${results.length} result${results.length === 1 ? '' : 's'} for "${query}"`
                                    : `No matches for "${query}"`}
                        </h2>
                        {!searching && results.length > 0 && (
                            <div
                                className="grid gap-5"
                                style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
                                    gap: '1.25rem'
                                }}
                            >
                                {results.map((book) => (
                                    <BookCard
                                        key={book.id}
                                        book={book}
                                        onClick={() => navigate(`/book/${encodeURIComponent(book.id)}`)}
                                    />
                                ))}
                            </div>
                        )}
                        {!searching && results.length === 0 && (
                            <p className="text-gray-500 dark:text-gray-400 text-sm">
                                Try a different title, author, or genre — or check the live trending feed below.
                            </p>
                        )}
                    </section>
                )}

                {/* AI Recommendations + live web trending */}
                {(!searched || results.length === 0) && (
                    <>
                        <AIBookRecommendations limit={12} strategy="hybrid" />
                        <WebTrending limit={12} />
                    </>
                )}
            </div>
        </motion.div>
    )
}

export default Discover

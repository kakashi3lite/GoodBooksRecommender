/**
 * 🌍 Web Trending — live book curation from open-source sites.
 * Chain-of-Thought: the static catalog is finite, so this section pulls
 * fresh trending + newest releases from Open Library and Google Books via
 * the edge API (/api/books/trending). Each card links to its shareable
 * /book/:id detail page, which auto-fetches the full record on open — so
 * the app actively curates from the web instead of showing a fixed list.
 */

import { Globe, TrendingUp } from 'lucide-react'
import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_ENDPOINTS } from '../../utils/api'
import { bentoPlacement } from '../../utils/bento'
import { BookCard } from '../UI/BookCard'

interface TrendingBook {
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

const WebTrending: React.FC<{ limit?: number }> = ({ limit = 12 }) => {
    const navigate = useNavigate()
    const [books, setBooks] = useState<TrendingBook[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    useEffect(() => {
        let cancelled = false
        const load = async () => {
            try {
                const res = await fetch(`${API_ENDPOINTS.books.trending()}?limit=${limit}`)
                if (!res.ok) throw new Error(`HTTP ${res.status}`)
                const data = (await res.json()) as { data?: TrendingBook[] }
                if (!cancelled) setBooks(data.data ?? [])
            } catch {
                if (!cancelled) setError('Live feed unavailable right now.')
            } finally {
                if (!cancelled) setLoading(false)
            }
        }
        void load()
        return () => {
            cancelled = true
        }
    }, [limit])

    return (
        <section className="mt-12" aria-label="Trending books from the web">
            <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    Trending Now — from the web
                </h2>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300">
                    <Globe className="w-3 h-3" /> Live · Open Library + Google Books
                </span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                Fresh picks curated in real time — tap any book for details and a shareable link.
            </p>

            {loading && (
                <div className="py-10 text-center text-gray-500 dark:text-gray-400">
                    <div className="animate-spin w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full mx-auto mb-3" />
                    Fetching the latest from the web…
                </div>
            )}

            {!loading && error && (
                <div className="py-10 text-center">
                    <p className="text-gray-500 dark:text-gray-400">{error}</p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        Your personalized picks above are always available.
                    </p>
                </div>
            )}

            {!loading && !error && books.length > 0 && (
                <div className="bento-grid">
                    {books.map((book, index) => {
                        const placement = bentoPlacement(index)
                        return (
                            <div key={book.id} className={`bento-item ${placement.className}`}>
                                <BookCard
                                    book={book}
                                    variant={placement.featured ? 'featured' : 'standard'}
                                    onClick={() => navigate(`/book/${encodeURIComponent(book.id)}`)}
                                />
                            </div>
                        )
                    })}
                </div>
            )}
        </section>
    )
}

export default WebTrending

/**
 * 📖 Book Detail — the shareable destination for any book URL.
 * Chain-of-Thought: a book link like /book/b-11 or /book/isbn:9780385533225
 * must always resolve. We first try the catalog; when the id is an external
 * one (shared from Trending, or an ISBN), we auto-fetch the real record from
 * open-source catalogs (Open Library / Google Books) via /api/books/resolve.
 * This makes every shared URL self-sufficient and real — never a dead end.
 */

import { ArrowLeft, BookmarkPlus, BookOpen, Check, Share2, Sparkles, Star } from 'lucide-react'
import React, { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { startReading } from '../../stores/reading/readingSlice'
import { toggleFavorite } from '../../stores/user/userSlice'
import { API_ENDPOINTS } from '../../utils/api'
import BookCover from '../UI/BookCover'

interface DetailBook {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    ratingsCount?: number
    genres?: string[]
    published_year?: number
    page_count?: number
    description?: string
    source?: string
}

/** True for ids that look like an external reference (not a catalog b-XX id). */
const isExternalId = (id: string): boolean =>
    id.startsWith('isbn:') || id.startsWith('ol:') || id.startsWith('gb:') || /^\d{9,13}[Xx]?$/.test(id)

const resolveUrl = (id: string): string => {
    const base = `${API_ENDPOINTS.books.resolve()}`
    if (id.startsWith('ol:') || id.startsWith('gb:')) return `${base}?key=${encodeURIComponent(id)}`
    return `${base}?isbn=${encodeURIComponent(id.replace(/^isbn:/, ''))}`
}

const BookDetail: React.FC = () => {
    const { id = '' } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const dispatch = useAppDispatch()

    const [book, setBook] = useState<DetailBook | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')
    const [copied, setCopied] = useState(false)

    const favorites = useAppSelector((state) => state.user.favorites)
    const inWishlist = favorites.includes(book?.id ?? '')
    const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
    const inShelf = currentlyReading.some((e) => e.bookId === book?.id)

    const shareUrl = typeof window !== 'undefined' ? `${window.location.origin}/book/${id}` : ''

    useEffect(() => {
        let cancelled = false
        const load = async () => {
            setLoading(true)
            setError('')
            try {
                // 1) Try the catalog/API by id.
                const res = await fetch(`${API_ENDPOINTS.books.getById(id)}`)
                if (res.ok) {
                    const data = (await res.json()) as DetailBook
                    if (!cancelled) setBook({ ...data, source: 'catalog' })
                    return
                }
                // 2) External id (ISBN / provider key) → auto-fetch from open source.
                if (isExternalId(id)) {
                    const ext = await fetch(resolveUrl(id))
                    if (ext.ok) {
                        const data = (await ext.json()) as DetailBook
                        if (!cancelled) setBook({ ...data, source: 'web' })
                        return
                    }
                }
                if (!cancelled) setError('We couldn’t find that book. The link may be out of date.')
            } catch {
                if (!cancelled) setError('Network error — check your connection and try again.')
            } finally {
                if (!cancelled) setLoading(false)
            }
        }
        void load()
        return () => {
            cancelled = true
        }
    }, [id])

    const handleShare = useCallback(async () => {
        try {
            if (navigator.share) {
                await navigator.share({
                    title: book?.title ?? 'Book',
                    text: `Check out "${book?.title}" by ${book?.authors} on GoodBooks`,
                    url: shareUrl
                })
                return
            }
        } catch {
            // user dismissed native sheet — fall through to clipboard copy
        }
        try {
            await navigator.clipboard.writeText(shareUrl)
            setCopied(true)
            toast.success('Link copied — anyone can open it 📎')
            setTimeout(() => setCopied(false), 2000)
        } catch {
            toast.error('Could not copy the link')
        }
    }, [book, shareUrl])

    const handleStartReading = () => {
        if (!book) return
        dispatch(
            startReading({
                bookId: book.id,
                book: {
                    title: book.title,
                    authors: book.authors,
                    cover_url: book.cover_url,
                    genres: book.genres,
                    published_year: book.published_year,
                    page_count: book.page_count,
                    description: book.description
                }
            })
        )
        toast.success(`Added "${book.title}" to your reading shelf 📖`)
    }

    const handleWishlist = () => {
        if (!book) return
        dispatch(toggleFavorite(book.id))
        toast.success(inWishlist ? 'Removed from wishlist' : 'Added to wishlist ❤️')
    }

    if (loading) {
        return (
            <div className="min-h-screen page-surface flex items-center justify-center p-8">
                <div className="text-center">
                    <div className="animate-spin w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-400">Loading book…</p>
                </div>
            </div>
        )
    }

    if (error || !book) {
        return (
            <div className="min-h-screen page-surface flex items-center justify-center p-8">
                <div className="text-center max-w-md">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                        Book not found
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">{error || 'No such book.'}</p>
                    <button
                        onClick={() => navigate('/discover')}
                        className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold"
                    >
                        Browse Discover
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen page-surface p-4 sm:p-8">
            <div className="max-w-4xl mx-auto">
                {/* Back */}
                <button
                    onClick={() => navigate(-1)}
                    className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-6"
                >
                    <ArrowLeft className="w-4 h-4" /> Back
                </button>

                <div className="bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-700 shadow-xl overflow-hidden">
                    <div className="flex flex-col sm:flex-row">
                        {/* Cover */}
                        <div className="sm:w-64 shrink-0 bg-gradient-to-br from-blue-600/10 to-purple-600/10 p-6 flex items-center justify-center">
                            <BookCover
                                title={book.title}
                                author={book.authors}
                                coverUrl={book.cover_url}
                                genres={book.genres}
                                seed={book.id}
                                size="lg"
                                rounded="lg"
                            />
                        </div>

                        {/* Info */}
                        <div className="flex-1 p-6 sm:p-8">
                            {book.source === 'web' && (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 mb-3">
                                    <Sparkles className="w-3 h-3" /> Live from Open Library / Google Books
                                </span>
                            )}
                            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 dark:text-white mb-1">
                                {book.title}
                            </h1>
                            <p className="text-gray-600 dark:text-gray-400 mb-4">{book.authors}</p>

                            <div className="flex items-center gap-3 mb-4">
                                <div className="flex items-center gap-0.5" aria-label={`Rating ${book.rating} of 5`}>
                                    {[1, 2, 3, 4, 5].map((i) => (
                                        <Star
                                            key={i}
                                            className={`w-4 h-4 ${i <= Math.round(book.rating)
                                                ? 'text-yellow-400 fill-yellow-400'
                                                : 'text-gray-300 dark:text-gray-600'
                                                }`}
                                        />
                                    ))}
                                </div>
                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                    {book.rating.toFixed(1)}
                                    {book.ratingsCount ? ` · ${book.ratingsCount.toLocaleString()} ratings` : ''}
                                </span>
                            </div>

                            <div className="flex flex-wrap gap-2 mb-5">
                                {book.genres?.slice(0, 5).map((g) => (
                                    <span
                                        key={g}
                                        className="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                                    >
                                        {g}
                                    </span>
                                ))}
                                {book.published_year ? (
                                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
                                        {book.published_year}
                                    </span>
                                ) : null}
                                {book.page_count ? (
                                    <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
                                        {book.page_count} pages
                                    </span>
                                ) : null}
                            </div>

                            {book.description && (
                                <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-6">
                                    {book.description}
                                </p>
                            )}

                            {/* Actions */}
                            <div className="flex flex-wrap gap-3">
                                <button
                                    onClick={handleStartReading}
                                    disabled={inShelf}
                                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-semibold shadow-lg shadow-blue-500/25 disabled:opacity-50"
                                >
                                    <BookOpen className="w-4 h-4" />
                                    {inShelf ? 'On your shelf' : 'Start Reading'}
                                </button>
                                <button
                                    onClick={handleWishlist}
                                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm font-semibold hover:bg-gray-50 dark:hover:bg-gray-800"
                                >
                                    <BookmarkPlus className="w-4 h-4" />
                                    {inWishlist ? 'In Wishlist' : '+ Wishlist'}
                                </button>
                                <button
                                    onClick={handleShare}
                                    className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm font-semibold hover:bg-gray-50 dark:hover:bg-gray-800"
                                >
                                    {copied ? <Check className="w-4 h-4 text-green-500" /> : <Share2 className="w-4 h-4" />}
                                    {copied ? 'Copied!' : 'Share'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default BookDetail

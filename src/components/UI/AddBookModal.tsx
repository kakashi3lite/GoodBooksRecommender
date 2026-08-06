/**
 * ➕ Add Book — find ANY book (web search) and add it to your shelf or wishlist.
 * Chain-of-Thought: the reader has a book in mind that may not be in the
 * curated catalog. This modal searches Google Books + Open Library via
 * /api/books/web-search — every result carries a real description and cover —
 * and lets the user add it to their reading shelf (with a snapshot so it
 * renders forever) or their wishlist.
 */

import { BookOpen, BookmarkPlus, Loader2, Plus, Search, X } from 'lucide-react'
import React, { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { startReading } from '../../stores/reading/readingSlice'
import { toggleFavorite } from '../../stores/user/userSlice'
import { API_ENDPOINTS } from '../../utils/api'
import BookCover from './BookCover'

interface WebBook {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    genres?: string[]
    published_year?: number
    page_count?: number
    description?: string
}

interface AddBookModalProps {
    open: boolean
    onClose: () => void
}

const AddBookModal: React.FC<AddBookModalProps> = ({ open, onClose }) => {
    const dispatch = useAppDispatch()
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<WebBook[]>([])
    const [searching, setSearching] = useState(false)
    const [searched, setSearched] = useState(false)
    const debounceRef = useRef<number | undefined>(undefined)
    const favorites = useAppSelector((state) => state.user.favorites)

    // Reset when the modal opens.
    useEffect(() => {
        if (open) {
            setQuery('')
            setResults([])
            setSearched(false)
        }
    }, [open])

    /**
     * Chain-of-Thought: debounced web search — pause typing, then hit the
     * edge API which merges catalog hits + Google Books + Open Library.
     */
    useEffect(() => {
        if (!open || !query.trim()) {
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
                const data = (await res.json()) as { data?: WebBook[] }
                setResults(data.data ?? [])
            } catch {
                setResults([])
            } finally {
                setSearching(false)
                setSearched(true)
            }
        }, 400)
        return () => window.clearTimeout(debounceRef.current)
    }, [query, open])

    if (!open) return null

    const addToShelf = (book: WebBook) => {
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
        toast.success(`"${book.title}" added to your reading shelf 📖`)
    }

    const toggleWishlist = (book: WebBook) => {
        dispatch(toggleFavorite(book.id))
        toast.success(
            favorites.includes(book.id) ? 'Removed from wishlist' : 'Added to wishlist ❤️'
        )
    }

    return (
        <div
            className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            role="dialog"
            aria-modal="true"
            aria-label="Add a book"
            onClick={onClose}
        >
            <div
                className="w-full max-w-2xl max-h-[85vh] flex flex-col rounded-3xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                        <Plus className="w-5 h-5 text-blue-600" /> Add a Book
                    </h2>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close"
                        className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Search */}
                <div className="px-6 py-4">
                    <div className="relative">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search any book, author, or ISBN…"
                            autoFocus
                            className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            aria-label="Search any book"
                        />
                    </div>
                </div>

                {/* Results */}
                <div className="flex-1 overflow-y-auto px-6 pb-6">
                    {searching && (
                        <div className="flex items-center gap-2 justify-center py-10 text-gray-500 dark:text-gray-400">
                            <Loader2 className="w-5 h-5 animate-spin" /> Searching the web…
                        </div>
                    )}
                    {!searching && searched && results.length === 0 && (
                        <p className="text-center py-10 text-gray-500 dark:text-gray-400">
                            No matches found. Try a different title or author.
                        </p>
                    )}
                    {!searching && results.length > 0 && (
                        <ul className="space-y-3">
                            {results.map((book) => {
                                const inWishlist = favorites.includes(book.id)
                                return (
                                    <li
                                        key={book.id}
                                        className="flex gap-4 p-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
                                    >
                                        <div className="w-14 shrink-0">
                                            <BookCover
                                                title={book.title}
                                                author={book.authors}
                                                coverUrl={book.cover_url}
                                                genres={book.genres}
                                                seed={book.id}
                                                size="sm"
                                                rounded="md"
                                            />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                                                {book.title}
                                            </h3>
                                            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                                                {book.authors}
                                                {book.published_year ? ` · ${book.published_year}` : ''}
                                            </p>
                                            {book.description && (
                                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                                                    {book.description}
                                                </p>
                                            )}
                                        </div>
                                        <div className="flex flex-col gap-2 shrink-0">
                                            <button
                                                type="button"
                                                onClick={() => addToShelf(book)}
                                                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors"
                                            >
                                                <BookOpen className="w-3.5 h-3.5" /> Read
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => toggleWishlist(book)}
                                                aria-label="Toggle wishlist"
                                                className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-semibold transition-colors ${inWishlist
                                                        ? 'border-red-300 dark:border-red-700 text-red-600 dark:text-red-400'
                                                        : 'border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                                                    }`}
                                            >
                                                <BookmarkPlus className="w-3.5 h-3.5" />
                                                {inWishlist ? 'Saved' : 'Save'}
                                            </button>
                                        </div>
                                    </li>
                                )
                            })}
                        </ul>
                    )}
                </div>
            </div>
        </div>
    )
}

export default AddBookModal

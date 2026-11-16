/**
 * ❤️ Wishlist Page
 * Chain-of-Thought: Books saved for later, pulled from the user slice.
 * Memory: Favorites persist via Redux + localStorage.
 */

import { motion } from 'framer-motion'
import { Heart } from 'lucide-react'
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { startReading } from '../../stores/reading/readingSlice'
import { toggleFavorite } from '../../stores/user/userSlice'
import BookCover from '../UI/BookCover'

/**
 * Wishlist — the reader's saved-for-later shelf.
 * Empty state guides the user toward discovery.
 */
const Wishlist: React.FC = () => {
    const dispatch = useAppDispatch()
    const navigate = useNavigate()
    const favorites = useAppSelector((state) => state.user.favorites)
    const recommendations = useAppSelector((state) => state.books.recommendations)

    // Resolve favorite IDs against live API books, then the curated catalog —
    // so the shelf always renders, even before the API responds.
    const byId = (id: string) =>
        recommendations.find((b) => b.id === id) ?? BOOK_CATALOG.find((b) => b.id === id)

    const wishlistBooks = favorites
        .map((id) => byId(id))
        .filter((b): b is NonNullable<typeof b> => Boolean(b))

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="min-h-screen page-surface p-4 sm:p-8"
        >
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                        <Heart className="w-8 h-8 text-red-500" />
                        Your Wishlist
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        {wishlistBooks.length} saved {wishlistBooks.length === 1 ? 'book' : 'books'} for later
                    </p>
                </div>

                {wishlistBooks.length === 0 ? (
                    <div className="text-center py-24">
                        <div className="text-5xl mb-4">💝</div>
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                            Nothing saved yet
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400 mt-2">
                            Tap the heart on any book to save it here for later.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {wishlistBooks.map((book) => (
                            <div
                                key={book.id}
                                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-lg hover:shadow-xl transition-shadow"
                            >
                                <div className="mb-4 flex justify-center">
                                    <BookCover
                                        title={book.title}
                                        author={book.authors}
                                        coverUrl={book.cover_url}
                                        genres={book.genres}
                                        seed={book.id}
                                        size="lg"
                                    />
                                </div>
                                <div className="flex items-start justify-between">
                                    <div>
                                        <h3 className="font-semibold text-gray-900 dark:text-white">
                                            {book.title}
                                        </h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">
                                            {book.authors}
                                        </p>
                                        <p className="text-xs text-yellow-500 mt-1">★ {book.rating.toFixed(1)}</p>
                                    </div>
                                    <button
                                        onClick={() => dispatch(toggleFavorite(book.id))}
                                        className="p-2 rounded-full bg-red-50 dark:bg-red-900/20 text-red-500 hover:scale-110 transition-transform"
                                        aria-label={`Remove ${book.title} from wishlist`}
                                    >
                                        <Heart className="w-4 h-4 fill-current" />
                                    </button>
                                </div>
                                {/* Commitment in action: "Start Reading" actually
                                    moves the wishlist book onto the shelf and
                                    takes the reader there — saved-for-later is
                                    the first step, reading is the reward. */}
                                <button
                                    onClick={() => {
                                        dispatch(
                                            startReading({
                                                bookId: book.id,
                                                book: {
                                                    title: book.title,
                                                    authors: book.authors,
                                                    cover_url: book.cover_url ?? '',
                                                    genres: book.genres,
                                                    published_year: book.published_year,
                                                    page_count: book.page_count,
                                                    description: book.description
                                                }
                                            })
                                        )
                                        navigate('/reading')
                                    }}
                                    className="mt-5 w-full py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white text-sm font-medium transition-colors"
                                >
                                    Start Reading
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </motion.div>
    )
}

export default Wishlist

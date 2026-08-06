/**
 * 📖 Currently Reading Page
 * Chain-of-Thought: a real, persisted reading shelf — progress updates live
 * from the reading slice, and every action (log pages / finish / remove)
 * writes back to localStorage. No demo data, no hardcoded "45% complete".
 */

import { motion } from 'framer-motion'
import { BookOpen, Check, Clock, Plus, Trash2 } from 'lucide-react'
import React from 'react'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import {
    finishReading,
    logReadingSession,
    removeFromReading
} from '../../stores/reading/readingSlice'
import BookCover from '../UI/BookCover'

const CurrentlyReading: React.FC = () => {
    const dispatch = useAppDispatch()
    const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
    const recommendations = useAppSelector((state) => state.books.recommendations)

    const bookById = (id: string) =>
        recommendations.find((b) => b.id === id) ?? BOOK_CATALOG.find((b) => b.id === id)

    const shelf = currentlyReading
        .map((entry) => ({ entry, book: bookById(entry.bookId) }))
        .filter(
            (x): x is { entry: (typeof currentlyReading)[number]; book: NonNullable<ReturnType<typeof bookById>> } =>
                Boolean(x.book)
        )
        .sort((a, b) => (a.entry.finishedAt ? 1 : 0) - (b.entry.finishedAt ? 1 : 0))

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-950 dark:to-indigo-950 p-8"
        >
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                        <BookOpen className="w-8 h-8 text-blue-600" />
                        Currently Reading
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Your active shelf — log pages to grow your streak.
                    </p>
                </div>

                {shelf.length === 0 ? (
                    <div className="text-center py-24">
                        <div className="text-5xl mb-4">📖</div>
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                            Your shelf is empty
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400 mt-2">
                            Head to Discover or grab today&apos;s pick to start reading.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {shelf.map(({ entry, book }) => {
                            const done = entry.finishedAt !== null
                            return (
                                <div
                                    key={book.id}
                                    className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-lg hover:shadow-xl transition-shadow"
                                >
                                    <div className="mb-4 flex justify-center">
                                        <BookCover
                                            title={book.title}
                                            author={book.authors}
                                            genres={book.genres}
                                            seed={book.id}
                                            size="lg"
                                        />
                                    </div>
                                    <h3 className="font-semibold text-gray-900 dark:text-white">
                                        {book.title}
                                    </h3>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">
                                        {book.authors}
                                    </p>
                                    <div className="mt-4 flex items-center justify-between text-sm">
                                        <span className="flex items-center text-gray-500 dark:text-gray-400">
                                            <Clock className="w-3.5 h-3.5 mr-1" />
                                            {done ? 'Finished 🎉' : `${entry.progressPct}% complete`}
                                        </span>
                                    </div>
                                    <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all ${done ? 'bg-green-500' : 'bg-blue-600'}`}
                                            style={{ width: `${done ? 100 : entry.progressPct}%` }}
                                        />
                                    </div>
                                    <div className="mt-5 flex gap-2">
                                        {!done && (
                                            <>
                                                <button
                                                    onClick={() =>
                                                        dispatch(logReadingSession({ bookId: book.id, pages: 20 }))
                                                    }
                                                    className="flex-1 flex items-center justify-center gap-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
                                                >
                                                    <Plus className="w-4 h-4" /> +20 pages
                                                </button>
                                                <button
                                                    onClick={() => dispatch(finishReading(book.id))}
                                                    className="flex items-center justify-center gap-1 py-2.5 rounded-xl bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
                                                    aria-label="Mark finished"
                                                >
                                                    <Check className="w-4 h-4" />
                                                </button>
                                            </>
                                        )}
                                        <button
                                            onClick={() => dispatch(removeFromReading(book.id))}
                                            className="flex items-center justify-center py-2.5 px-3 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300 hover:text-red-500 transition-colors"
                                            aria-label="Remove from shelf"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>
        </motion.div>
    )
}

export default CurrentlyReading

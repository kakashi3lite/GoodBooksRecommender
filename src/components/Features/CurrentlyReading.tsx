/**
 * 📖 Currently Reading Page
 * Chain-of-Thought: a real, persisted reading shelf. Progress updates come
 * only from logged sessions — there is no fake "+20" shortcut. Instead a
 * session dialog lets the reader log the ACTUAL pages they read (custom
 * number or quick presets), and finishing a book opens a completion ceremony
 * that pulls real facts about the book + personalized motivation.
 *
 * Books added from the web (not in the curated catalog) render from the
 * snapshot captured at add-time (readingSlice ReadingEntry.book).
 */

import { motion } from 'framer-motion'
import { BookOpen, Check, Clock, Minus, Plus, Sparkles, Timer, Trash2, Zap } from 'lucide-react'
import React, { useState } from 'react'
import toast from 'react-hot-toast'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import {
    finishReading,
    logReadingSession,
    removeFromReading,
    type ReadingBookSnapshot
} from '../../stores/reading/readingSlice'
import {
    computePace,
    estimateHoursLeft,
    formatHours
} from '../../utils/readingInsights'
import BookCompletionModal from '../UI/BookCompletionModal'
import BookCover from '../UI/BookCover'

const PAGE_PRESETS = [10, 25, 50, 100]

interface SessionState {
    bookId: string
}

interface ShelfBook {
    id: string
    title: string
    authors: string
    cover_url: string
    genres?: string[]
    page_count?: number
}

const CurrentlyReading: React.FC = () => {
    const dispatch = useAppDispatch()
    const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
    const readingLog = useAppSelector((state) => state.reading.readingLog)
    const recommendations = useAppSelector((state) => state.books.recommendations)

    // Real pace — used for the one-tap quick log (your own average, honest).
    const { avgPagesPerSession } = computePace(readingLog)

    const [session, setSession] = useState<SessionState | null>(null)
    const [pagesInput, setPagesInput] = useState('')
    const [completionBook, setCompletionBook] = useState<ShelfBook | null>(null)

    /**
     * Chain-of-Thought: resolve a shelf entry to displayable book data —
     * catalog / recommendations first, then the snapshot stored at add-time
     * (this is what makes web-added books work on the shelf).
     */
    const resolveBook = (
        entryId: string,
        snapshot?: ReadingBookSnapshot
    ): ShelfBook => {
        const found =
            recommendations.find((b) => b.id === entryId) ?? BOOK_CATALOG.find((b) => b.id === entryId)
        if (found) {
            return {
                id: found.id,
                title: found.title,
                authors: found.authors,
                cover_url: found.cover_url ?? '',
                genres: found.genres,
                page_count: found.page_count
            }
        }
        if (snapshot) {
            return {
                id: entryId,
                title: snapshot.title,
                authors: snapshot.authors,
                cover_url: snapshot.cover_url,
                genres: snapshot.genres,
                page_count: snapshot.page_count
            }
        }
        return { id: entryId, title: entryId, authors: 'Unknown', cover_url: '' }
    }

    const shelf = currentlyReading
        .map((entry) => ({ entry, book: resolveBook(entry.bookId, entry.book) }))
        .sort((a, b) => (a.entry.finishedAt ? 1 : 0) - (b.entry.finishedAt ? 1 : 0))

    const openSession = (bookId: string) => {
        setPagesInput('')
        setSession({ bookId })
    }

    const commitSession = () => {
        if (!session) return
        const pages = Number(pagesInput)
        if (!Number.isFinite(pages) || pages <= 0) return
        dispatch(logReadingSession({ bookId: session.bookId, pages: Math.round(pages) }))
        toast.success(`Logged ${Math.round(pages)} pages — keep it going! 📚`)
        setSession(null)
    }

    /** One-tap quick log using the reader's own average session (honest + fast). */
    const quickLog = (bookId: string, bookTitle: string) => {
        dispatch(logReadingSession({ bookId, pages: avgPagesPerSession }))
        toast.success(
            `Logged your usual ${avgPagesPerSession} pages — "${bookTitle}" is moving along 🔥`
        )
    }

    const handleFinish = (book: ShelfBook) => {
        dispatch(finishReading(book.id))
        setCompletionBook(book)
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-950 dark:to-indigo-950 p-4 sm:p-8"
        >
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                        <BookOpen className="w-8 h-8 text-blue-600" />
                        Currently Reading
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Your active shelf — log the pages you actually read to grow your streak and
                        analytics.
                    </p>
                </div>

                {shelf.length === 0 ? (
                    <div className="text-center py-24">
                        <div className="text-5xl mb-4">📖</div>
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                            Your shelf is empty
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400 mt-2">
                            Head to Discover, tap “Add Book” in the sidebar, or grab today&apos;s pick to
                            start reading.
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                        {shelf.map(({ entry, book }) => {
                            const done = entry.finishedAt !== null
                            const pagesRead = readingLog
                                .filter((l) => l.bookId === book.id)
                                .reduce((a, l) => a + l.pages, 0)
                            const pagesLeft = book.page_count
                                ? Math.max(0, book.page_count - pagesRead)
                                : 0
                            const hoursLeft =
                                pagesLeft > 0 ? formatHours(estimateHoursLeft(pagesLeft, avgPagesPerSession)) : null
                            return (
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
                                        {!done && hoursLeft && (
                                            <span className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-300">
                                                <Timer className="w-3.5 h-3.5" /> {hoursLeft} left
                                            </span>
                                        )}
                                    </div>
                                    <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all ${done ? 'bg-green-500' : 'bg-blue-600'}`}
                                            style={{ width: `${done ? 100 : entry.progressPct}%` }}
                                        />
                                    </div>

                                    {/* Real session logging */}
                                    {!done && (
                                        <div className="mt-5 space-y-2">
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => quickLog(book.id, book.title)}
                                                    className="flex-1 inline-flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
                                                    aria-label={`Quick log ${avgPagesPerSession} pages`}
                                                >
                                                    <Zap className="w-4 h-4" /> Log {avgPagesPerSession} pg
                                                </button>
                                                <button
                                                    onClick={() => openSession(book.id)}
                                                    className="inline-flex items-center justify-center gap-1 py-2.5 px-3 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium transition-colors"
                                                >
                                                    Custom
                                                </button>
                                                <button
                                                    onClick={() => handleFinish(book)}
                                                    className="inline-flex items-center justify-center gap-1 py-2.5 px-4 rounded-xl bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
                                                    aria-label="Mark finished"
                                                >
                                                    <Check className="w-4 h-4" /> Finish
                                                </button>
                                            </div>

                                            {/* Inline session editor */}
                                            {session?.bookId === book.id && (
                                                <div className="rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-3">
                                                    <p className="text-xs font-semibold text-blue-700 dark:text-blue-300 mb-2">
                                                        How many pages did you read this session?
                                                    </p>
                                                    <div className="flex gap-1.5 mb-2">
                                                        {PAGE_PRESETS.map((p) => (
                                                            <button
                                                                key={p}
                                                                type="button"
                                                                onClick={() => setPagesInput(String(p))}
                                                                className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-colors ${pagesInput === String(p)
                                                                    ? 'bg-blue-600 text-white'
                                                                    : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-gray-600'
                                                                    }`}
                                                            >
                                                                {p}
                                                            </button>
                                                        ))}
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <div className="flex items-center gap-1 flex-1">
                                                            <button
                                                                type="button"
                                                                aria-label="Decrease pages"
                                                                onClick={() =>
                                                                    setPagesInput(String(
                                                                        Math.max(1, (Number(pagesInput) || 0) - 5)
                                                                    ))
                                                                }
                                                                className="p-2 rounded-lg bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                                                            >
                                                                <Minus className="w-4 h-4" />
                                                            </button>
                                                            <input
                                                                type="number"
                                                                min={1}
                                                                value={pagesInput}
                                                                onChange={(e) => setPagesInput(e.target.value)}
                                                                placeholder="Pages…"
                                                                aria-label="Pages read"
                                                                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500"
                                                            />
                                                            <button
                                                                type="button"
                                                                aria-label="Increase pages"
                                                                onClick={() =>
                                                                    setPagesInput(String(
                                                                        (Number(pagesInput) || 0) + 5
                                                                    ))
                                                                }
                                                                className="p-2 rounded-lg bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300"
                                                            >
                                                                <Plus className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                        <button
                                                            type="button"
                                                            onClick={commitSession}
                                                            disabled={!pagesInput || Number(pagesInput) <= 0}
                                                            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm font-semibold transition-colors"
                                                        >
                                                            Log
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {done && (
                                        <div className="mt-5 flex gap-2">
                                            <span className="flex-1 inline-flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 text-sm font-medium">
                                                <Sparkles className="w-4 h-4" /> Completed
                                            </span>
                                            <button
                                                onClick={() => dispatch(removeFromReading(book.id))}
                                                className="flex items-center justify-center py-2.5 px-3 rounded-xl bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300 hover:text-red-500 transition-colors"
                                                aria-label="Remove from shelf"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                )}
            </div>

            {/* Completion ceremony */}
            <BookCompletionModal
                bookId={completionBook?.id ?? ''}
                bookTitle={completionBook?.title ?? ''}
                bookAuthors={completionBook?.authors ?? ''}
                coverUrl={completionBook?.cover_url ?? ''}
                open={completionBook !== null}
                onClose={() => setCompletionBook(null)}
            />
        </motion.div>
    )
}

export default CurrentlyReading
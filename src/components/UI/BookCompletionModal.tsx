/**
 * 🎉 Book Completion — the finish-line ceremony.
 * Chain-of-Thought: finishing a book should feel earned and motivate the next
 * one. This modal (1) fetches 2–4 REAL facts about the finished book from the
 * web (/api/books/insights), (2) shows the reader-expectation line, and
 * (3) adds a PERSONALIZED motivation built from the reader's own reading log
 * (pace, streak, goal progress, persona) — every number is real, nothing
 * fabricated.
 */

import { Award, BookOpen, Flame, Loader2, Sparkles, Target, TrendingUp, X } from 'lucide-react'
import React, { useEffect, useState } from 'react'
import { useAppSelector } from '../../hooks/redux'
import { booksFinished, computeStreak } from '../../stores/reading/readingSlice'
import { API_ENDPOINTS } from '../../utils/api'
import BookCover from './BookCover'

interface Insights {
    id: string
    title: string
    authors: string
    cover_url: string
    rating: number
    genres: string[]
    published_year: number
    page_count: number
    description: string
    facts: string[]
    expectation: string
}

interface CompletionProps {
    bookId: string
    bookTitle: string
    bookAuthors: string
    coverUrl: string
    open: boolean
    onClose: () => void
}

/** Real, honest motivators derived from the reader's actual log. */
const buildMotivations = (input: {
    finishedCount: number
    streak: number
    readingGoal: number
    pagesThisBook: number
    bookPages: number
    daysToFinish: number
    avgPagesPerSession: number
    sessionsThisBook: number
}): string[] => {
    const lines: string[] = []
    const { finishedCount, streak, readingGoal, pagesThisBook, bookPages, daysToFinish, avgPagesPerSession, sessionsThisBook } = input

    if (bookPages > 0 && daysToFinish > 0) {
        const pace = Math.round(bookPages / Math.max(1, daysToFinish))
        const avgPace = Math.max(1, Math.round(avgPagesPerSession * Math.max(1, sessionsThisBook) / Math.max(1, daysToFinish)))
        lines.push(
            pace >= avgPace
                ? `You averaged ~${pace} pages/day — faster than your usual ~${avgPace}. That's momentum.`
                : `You read ~${pace} pages/day on this one, staying consistent with your ~${avgPace} pace.`
        )
    } else if (pagesThisBook > 0) {
        lines.push(`You logged ${pagesThisBook} pages on this book across ${Math.max(1, sessionsThisBook)} session${sessionsThisBook === 1 ? '' : 's'}.`)
    }

    if (streak > 0) {
        lines.push(`Your ${streak}-day streak is alive — finish the chain tomorrow too. 🔥`)
    }
    if (readingGoal > 0) {
        const remaining = Math.max(0, readingGoal - finishedCount)
        lines.push(
            remaining === 0
                ? `You've hit your ${readingGoal}-book yearly goal — incredible. 🏆`
                : `${finishedCount} book${finishedCount === 1 ? '' : 's'} done — ${remaining} to go on your ${readingGoal}-book goal.`
        )
    }
    if (lines.length === 0) {
        lines.push('Every finished book compounds — this one is in the bank. Keep going.')
    }
    return lines.slice(0, 3)
}

/** Reader persona from real log patterns. */
const personaOf = (avgPagesPerSession: number, distinctDays: number, finishedCount: number): string => {
    if (avgPagesPerSession >= 50) return 'Binge Reader'
    if (distinctDays >= 5) return 'Consistent Reader'
    if (finishedCount >= 5) return 'Seasoned Reader'
    return 'Rising Reader'
}

const BookCompletionModal: React.FC<CompletionProps> = ({
    bookId,
    bookTitle,
    bookAuthors,
    coverUrl,
    open,
    onClose
}) => {
    const [insights, setInsights] = useState<Insights | null>(null)
    const [loadingInsights, setLoadingInsights] = useState(true)

    // Real reading stats from the store.
    const readingLog = useAppSelector((state) => state.reading.readingLog)
    const shelf = useAppSelector((state) => state.reading.currentlyReading)
    const readingGoal = useAppSelector((state) => state.user.preferences.readingGoal)

    useEffect(() => {
        if (!open) return
        setLoadingInsights(true)
        setInsights(null)
        const q = bookId.startsWith('isbn:') || bookId.startsWith('ol:') || bookId.startsWith('gb:')
            ? `?key=${encodeURIComponent(bookId)}`
            : `?id=${encodeURIComponent(bookId)}`
        fetch(`${API_ENDPOINTS.books.insights()}${q}`)
            .then((r) => (r.ok ? r.json() : null))
            .then((d) => setInsights(d as Insights | null))
            .catch(() => setInsights(null))
            .finally(() => setLoadingInsights(false))
    }, [open, bookId])

    if (!open) return null

    const finishedCount = booksFinished(shelf)
    const streak = computeStreak(readingLog)
    const entries = shelf.find((e) => e.bookId === bookId)
    const daysToFinish = entries?.startedAt
        ? Math.max(1, Math.round((Date.now() - entries.startedAt) / 86400000))
        : 0
    const sessionsThisBook = readingLog.filter((l) => l.bookId === bookId).length
    const pagesThisBook = readingLog.filter((l) => l.bookId === bookId).reduce((a, l) => a + l.pages, 0)
    const avgPagesPerSession = readingLog.length
        ? Math.round(readingLog.reduce((a, l) => a + l.pages, 0) / readingLog.length)
        : 0
    const distinctDays = new Set(readingLog.map((l) => l.date)).size
    const persona = personaOf(avgPagesPerSession, distinctDays, finishedCount)

    const motivations = buildMotivations({
        finishedCount,
        streak,
        readingGoal,
        pagesThisBook,
        bookPages: insights?.page_count ?? 0,
        daysToFinish,
        avgPagesPerSession,
        sessionsThisBook
    })

    return (
        <div
            className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            role="dialog"
            aria-modal="true"
            aria-label="Book complete"
            onClick={onClose}
        >
            <div
                className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-3xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Hero */}
                <div className="bg-gradient-to-r from-green-600 to-teal-600 p-6 text-white relative">
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close"
                        className="absolute top-4 right-4 p-1.5 rounded-lg bg-white/20 hover:bg-white/30"
                    >
                        <X className="w-5 h-5" />
                    </button>
                    <div className="flex items-center gap-4">
                        <div className="w-16 shrink-0 rounded-lg overflow-hidden bg-white/10">
                            <BookCover
                                title={bookTitle}
                                author={bookAuthors}
                                coverUrl={coverUrl}
                                size="sm"
                                rounded="md"
                            />
                        </div>
                        <div>
                            <div className="text-xs font-semibold uppercase tracking-wider text-green-100">
                                Book complete
                            </div>
                            <h2 className="text-xl font-bold leading-tight mt-1">{bookTitle}</h2>
                            <p className="text-sm text-green-100">{bookAuthors}</p>
                        </div>
                    </div>
                </div>

                <div className="p-6 space-y-5">
                    {/* Personalized motivation */}
                    <div className="rounded-2xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4">
                        <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300 text-sm font-bold mb-2">
                            <Award className="w-4 h-4" /> Your finish — {persona}
                        </div>
                        <ul className="space-y-2">
                            {motivations.map((m, i) => (
                                <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-200">
                                    <TrendingUp className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                                    {m}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Real facts about the book */}
                    <div>
                        <div className="flex items-center gap-2 text-gray-900 dark:text-white text-sm font-bold mb-2">
                            <BookOpen className="w-4 h-4 text-green-600" /> About this book
                        </div>
                        {loadingInsights ? (
                            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                <Loader2 className="w-4 h-4 animate-spin" /> Fetching real facts…
                            </div>
                        ) : insights ? (
                            <ul className="space-y-2">
                                {insights.facts.map((f, i) => (
                                    <li key={i} className="flex gap-2 text-sm text-gray-600 dark:text-gray-300">
                                        <Sparkles className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                                        {f}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                Facts unavailable right now — your progress is still saved.
                            </p>
                        )}
                    </div>

                    {/* What to expect next */}
                    {insights?.expectation && (
                        <div className="rounded-2xl bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 p-4">
                            <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300 text-sm font-bold mb-1">
                                <Target className="w-4 h-4" /> For readers of this genre
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-200">
                                {insights.expectation}
                            </p>
                        </div>
                    )}

                    <div className="flex items-center justify-between pt-1 text-xs text-gray-400 dark:text-gray-500">
                        <span className="flex items-center gap-1">
                            <Flame className="w-3.5 h-3.5 text-orange-500" /> {streak}-day streak
                        </span>
                        <span className="flex items-center gap-1">
                            <Target className="w-3.5 h-3.5 text-green-500" /> {finishedCount}/{readingGoal} goal
                        </span>
                    </div>

                    <button
                        type="button"
                        onClick={onClose}
                        className="w-full py-3 rounded-xl bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white font-semibold transition-colors"
                    >
                        On to the next one 🚀
                    </button>
                </div>
            </div>
        </div>
    )
}

export default BookCompletionModal

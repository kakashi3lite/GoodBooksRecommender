/**
 * 📊 Advanced Analytics — real reading insights (no placeholders, no chart lib)
 * Chain-of-Thought: every number derives from the user's persisted reading
 * activity (reading slice) + the live catalog. Charts are pure CSS so this
 * page stays in the tiny lazy route chunk.
 */

import { motion } from 'framer-motion'
import { BarChart3, BookOpen, CalendarDays, Flame, Library, RefreshCw, Sparkles } from 'lucide-react'
import React, { useCallback, useMemo, useState } from 'react'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppSelector } from '../../hooks/redux'
import {
  booksFinished,
  computeStreak,
  pagesAllTime,
  pagesThisMonth
} from '../../stores/reading/readingSlice'
import { AIService } from '../../utils/api'
import { buildChatContext } from '../../utils/chatContext'
import { pluralize } from '../../utils/readingInsights'
import { buildGenreBreakdown } from '../../utils/readingStats'

const AdvancedAnalytics: React.FC = () => {
  const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
  const readingLog = useAppSelector((state) => state.reading.readingLog)
  const favorites = useAppSelector((state) => state.user.favorites)
  const preferences = useAppSelector((state) => state.user.preferences)

  const [insight, setInsight] = useState<string | null>(null)
  const [insightLoading, setInsightLoading] = useState(false)
  const [insightError, setInsightError] = useState(false)

  // Ask the AI companion to reflect on the reader's REAL stats (MiniMax LLM,
  // with an honest template fallback server-side).
  const reflect = useCallback(async () => {
    if (insightLoading) return
    setInsightLoading(true)
    setInsightError(false)
    try {
      const ctx = buildChatContext({
        favoriteGenres: preferences.favoriteGenres,
        readingGoal: preferences.readingGoal,
        currentlyReading,
        readingLog
      })
      const res = (await AIService.getInsight(ctx)) as { insight: string }
      setInsight(res.insight)
    } catch {
      setInsightError(true)
    } finally {
      setInsightLoading(false)
    }
  }, [insightLoading, preferences, currentlyReading, readingLog])

  const streak = computeStreak(readingLog)
  const finished = booksFinished(currentlyReading)
  const monthPages = pagesThisMonth(readingLog)
  const totalPages = pagesAllTime(readingLog)

  /**
   * Genre distribution from the reader's OWN books (favourites + finished).
   * Chain-of-Thought: this used to fall back to the whole catalog's spread when
   * there was no data, showing a brand-new reader a confident chart of tastes
   * they had never expressed. Empty now renders an honest empty state.
   */
  const genreBreakdown = useMemo(
    () =>
      buildGenreBreakdown(
        [...favorites, ...currentlyReading.filter((e) => e.finishedAt).map((e) => e.bookId)],
        BOOK_CATALOG
      ),
    [favorites, currentlyReading]
  )

  // 14-day reading trend from real sessions.
  const trend = useMemo(() => {
    const days = Array.from({ length: 14 }, (_, i) => {
      const d = new Date()
      d.setDate(d.getDate() - (13 - i))
      return d.toISOString().slice(0, 10)
    })
    const byDate = new Map<string, number>()
    for (const log of readingLog) byDate.set(log.date, (byDate.get(log.date) ?? 0) + log.pages)
    const max = Math.max(1, ...days.map((d) => byDate.get(d) ?? 0))
    return days.map((d) => ({
      label: new Date(d + 'T00:00:00').toLocaleDateString(undefined, { day: 'numeric', month: 'short' }),
      pages: byDate.get(d) ?? 0,
      pct: Math.round(((byDate.get(d) ?? 0) / max) * 100)
    }))
  }, [readingLog])

  const hoursRead = Math.round(totalPages / 40)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="min-h-screen page-surface p-4 sm:p-8"
    >
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3 mb-2">
          <BarChart3 className="w-8 h-8 text-purple-600" />
          Reading Analytics
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Your real reading life — built from every session you log.
        </p>

        {/* AI Reading Insight — a warm reflection on the reader's real stats */}
        <div className="rounded-2xl bg-gradient-to-r from-blue-600/5 to-purple-600/5 dark:from-blue-900/20 dark:to-purple-900/20 border border-blue-200/60 dark:border-blue-800/50 p-6 mb-8">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              AI Reading Insight
            </h2>
            <button
              onClick={reflect}
              disabled={insightLoading}
              className="inline-flex items-center gap-1.5 text-xs px-3 py-2 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${insightLoading ? 'animate-spin' : ''}`} />
              {insightLoading ? 'Reflecting…' : insight ? 'Regenerate' : 'Reflect on my reading'}
            </button>
          </div>
          {insightError ? (
            <p className="text-sm text-red-500">
              Couldn&apos;t reach the AI service right now — try again in a moment.
            </p>
          ) : insight ? (
            <p className="text-gray-700 dark:text-gray-200 leading-relaxed">{insight}</p>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Let the AI companion look at your real reading stats and write a short
              reflection on your pace, streak, and goals.
            </p>
          )}
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { icon: Flame, label: 'Streak', value: pluralize(streak, 'day'), color: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20' },
            { icon: BookOpen, label: 'Books Finished', value: `${finished}`, color: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20' },
            { icon: Library, label: 'Pages This Month', value: `${monthPages}`, color: 'text-green-600 bg-green-50 dark:bg-green-900/20' },
            { icon: CalendarDays, label: 'Reading Time', value: `${hoursRead}h`, color: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20' }
          ].map((stat) => (
            <div key={stat.label} className={`rounded-2xl p-5 ${stat.color.split(' ').slice(1).join(' ')}`}>
              <stat.icon className={`w-6 h-6 ${stat.color.split(' ')[0]}`} />
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">{stat.value}</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 14-day trend */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Last 14 Days</h2>
            {trend.some((t) => t.pages > 0) ? (
              <div className="flex items-end gap-1.5 h-32">
                {trend.map((day, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className={`w-full rounded-t ${day.pages > 0 ? 'bg-blue-600' : 'bg-gray-200 dark:bg-gray-700'}`}
                      style={{ height: `${Math.max(4, day.pct)}%` }}
                      title={`${day.pages} pages`}
                    />
                    {i % 2 === 0 && (
                      <span className="text-[9px] text-gray-400">{day.label}</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Log your first reading session and your trend appears here.
              </p>
            )}
          </div>

          {/* Genre breakdown */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Top Genres</h2>
            {genreBreakdown.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                No genres yet — finish or save a book and your taste map starts here.
              </p>
            ) : (
              <ul className="space-y-3">
                {genreBreakdown.map((g) => (
                  <li key={g.name} className="flex items-center gap-3">
                    <span className="flex-0 w-28 text-sm text-gray-700 dark:text-gray-300 truncate">{g.name}</span>
                    <span
                      className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
                      role="img"
                      aria-label={`${g.name}: ${g.count} book${g.count === 1 ? '' : 's'}`}
                    >
                      <span
                        className="block h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-600"
                        style={{ width: `${g.pct}%` }}
                      />
                    </span>
                    <span className="w-6 text-right text-xs text-gray-500">{g.count}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default AdvancedAnalytics

/**
 * 📊 Advanced Analytics — real reading insights (no placeholders, no chart lib)
 * Chain-of-Thought: every number derives from the user's persisted reading
 * activity (reading slice) + the live catalog. Charts are pure CSS so this
 * page stays in the tiny lazy route chunk.
 */

import { motion } from 'framer-motion'
import { BarChart3, BookOpen, CalendarDays, Flame, Library } from 'lucide-react'
import React, { useMemo } from 'react'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppSelector } from '../../hooks/redux'
import {
  booksFinished,
  computeStreak,
  pagesAllTime,
  pagesThisMonth
} from '../../stores/reading/readingSlice'

const AdvancedAnalytics: React.FC = () => {
  const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
  const readingLog = useAppSelector((state) => state.reading.readingLog)
  const favorites = useAppSelector((state) => state.user.favorites)

  const streak = computeStreak(readingLog)
  const finished = booksFinished(currentlyReading)
  const monthPages = pagesThisMonth(readingLog)
  const totalPages = pagesAllTime(readingLog)

  // Genre distribution from the user's favorites + finished books (real).
  const genreBreakdown = useMemo(() => {
    const counts = new Map<string, number>()
    for (const id of [
      ...favorites,
      ...currentlyReading.filter((e) => e.finishedAt).map((e) => e.bookId)
    ]) {
      const book = BOOK_CATALOG.find((b) => b.id === id)
      if (!book) continue
      for (const g of book.genres ?? []) counts.set(g, (counts.get(g) ?? 0) + 1)
    }
    // Fall back to the catalog's overall spread when the user has no data yet.
    if (counts.size === 0) {
      for (const book of BOOK_CATALOG) for (const g of book.genres ?? []) counts.set(g, (counts.get(g) ?? 0) + 1)
    }
    const max = Math.max(1, ...counts.values())
    return Array.from(counts.entries())
      .map(([name, count]) => ({ name, count, pct: Math.round((count / max) * 100) }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8)
  }, [favorites, currentlyReading])

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
      className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-950 dark:to-indigo-950 p-4 sm:p-8"
    >
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3 mb-2">
          <BarChart3 className="w-8 h-8 text-purple-600" />
          Reading Analytics
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Your real reading life — built from every session you log.
        </p>

        {/* Stat cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { icon: Flame, label: 'Streak', value: `${streak} days`, color: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20' },
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
            <ul className="space-y-3">
              {genreBreakdown.map((g) => (
                <li key={g.name} className="flex items-center gap-3">
                  <span className="flex-0 w-28 text-sm text-gray-700 dark:text-gray-300 truncate">{g.name}</span>
                  <span className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <span
                      className="block h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-600"
                      style={{ width: `${g.pct}%` }}
                    />
                  </span>
                  <span className="w-6 text-right text-xs text-gray-500">{g.count}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default AdvancedAnalytics

/**
 * 👥 Community Hub → Reader Profile
 * Chain-of-Thought: an honest, real "community" page — your own reading
 * identity (stats, badges, recent activity) derived from persisted data.
 * A social layer (posts, follows) can extend this later; it will never show
 * fabricated numbers.
 */

import { motion } from 'framer-motion'
import { Award, BookOpen, Flame, Heart, Share2, Users } from 'lucide-react'
import React, { useMemo } from 'react'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppSelector } from '../../hooks/redux'
import {
  booksFinished,
  computeStreak,
  pagesAllTime,
  pagesThisMonth
} from '../../stores/reading/readingSlice'

const CommunityHub: React.FC = () => {
  const userProfile = useAppSelector((state) => state.user.profile)
  const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
  const readingLog = useAppSelector((state) => state.reading.readingLog)
  const favorites = useAppSelector((state) => state.user.favorites)
  const notes = useAppSelector((state) => state.reading.notes)

  const streak = computeStreak(readingLog)
  const finished = booksFinished(currentlyReading)
  const monthPages = pagesThisMonth(readingLog)
  const totalPages = pagesAllTime(readingLog)

  const initials = userProfile.name
    .split(' ')
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()

  // Real, earned badges.
  const badges = useMemo(() => {
    const list: Array<{ label: string; emoji: string }> = []
    if (streak >= 3) list.push({ label: '🔥 On a roll', emoji: '🔥' })
    if (streak >= 7) list.push({ label: 'Weekly Streak', emoji: '📆' })
    if (finished >= 1) list.push({ label: 'Book Finisher', emoji: '🏁' })
    if (finished >= 5) list.push({ label: 'Bookworm', emoji: '🐛' })
    if (favorites.length >= 3) list.push({ label: 'Curator', emoji: '💝' })
    if (notes.length >= 3) list.push({ label: 'Deep Reader', emoji: '📝' })
    if (totalPages >= 1000) list.push({ label: '1K Pages', emoji: '📚' })
    return list
  }, [streak, finished, favorites.length, notes.length, totalPages])

  // Recent activity (real sessions + notes).
  const activity = useMemo(() => {
    const events = readingLog.map((log) => ({
      ts: log.ts,
      text: `Read ${log.pages} pages of ${BOOK_CATALOG.find((b) => b.id === log.bookId)?.title ?? log.bookId}`
    }))
    for (const note of notes) {
      events.push({
        ts: note.updatedAt,
        text: `Wrote a note${note.bookId ? ` on ${BOOK_CATALOG.find((b) => b.id === note.bookId)?.title ?? ''}` : ''}`
      })
    }
    return events.sort((a, b) => b.ts - a.ts).slice(0, 5)
  }, [readingLog, notes])

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-950 dark:to-indigo-950 p-4 sm:p-8"
    >
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3 mb-8">
          <Users className="w-8 h-8 text-indigo-600" />
          Your Reader Profile
        </h1>

        {/* Profile card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xl font-bold">
              {initials || 'R'}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">{userProfile.name}</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">{userProfile.email}</p>
              <p className="text-xs text-gray-400 capitalize mt-1">Reading Level: {userProfile.readingLevel}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
            {[
              { icon: Flame, label: 'Streak', value: `${streak}d` },
              { icon: BookOpen, label: 'Finished', value: `${finished}` },
              { icon: Heart, label: 'Wishlist', value: `${favorites.length}` },
              { icon: Share2, label: 'Pages', value: `${totalPages}` }
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <stat.icon className="w-5 h-5 mx-auto text-indigo-500" />
                <p className="text-xl font-bold text-gray-900 dark:text-white mt-1">{stat.value}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Badges */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-yellow-500" /> Badges
          </h3>
          {badges.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {badges.map((b) => (
                <span key={b.label} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-yellow-50 dark:bg-yellow-900/20 text-sm text-yellow-800 dark:text-yellow-200 border border-yellow-200 dark:border-yellow-800">
                  {b.emoji} {b.label}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Read for {3 - Math.min(2, streak)} more day(s) to earn your first badge.
            </p>
          )}
        </div>

        {/* Recent activity */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h3>
          {activity.length > 0 ? (
            <ul className="space-y-3">
              {activity.map((event, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="text-lg">📖</span>
                  <div>
                    <p className="text-gray-900 dark:text-white">{event.text}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(event.ts).toLocaleString(undefined, {
                        hour: 'numeric',
                        minute: '2-digit',
                        day: 'numeric',
                        month: 'short'
                      })}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Your reading activity will appear here — {monthPages} pages read this month so far.
            </p>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default CommunityHub

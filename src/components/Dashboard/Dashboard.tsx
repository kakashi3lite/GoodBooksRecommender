/**
 * 📊 Futuristic AI Dashboard - Production-Ready Book Intelligence Platform
 * Chain-of-Thought: Comprehensive AI-powered book discovery with advanced analytics
 * Memory: Persistent user preferences, reading history, and recommendation context
 * Forward-Thinking: Scalable architecture with enterprise-grade UI components
 */

import { AnimatePresence, motion } from 'framer-motion'
import {
  Activity,
  BarChart3,
  Bell,
  BookmarkPlus,
  BookOpen,
  Clock,
  Eye,
  Heart,
  Moon,
  Search,
  Settings,
  Share,
  Sparkles,
  Star,
  Sun,
  Target,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react'
import React, { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { fetchRecommendations } from '../../stores/books/booksSlice'
import { setTheme } from '../../stores/dashboard/dashboardSlice'
import {
  booksFinished,
  computeStreak,
  dismissStreakRecovery,
  logReadingSession,
  pagesAllTime,
  pagesThisMonth,
  progressOf,
  restoreStreak,
  startReading,
  streakAtRisk
} from '../../stores/reading/readingSlice'
import { toggleFavorite } from '../../stores/user/userSlice'
import { applyBookFilters, BOOK_FILTER_TABS, genreChipsFor } from '../../utils/bookFilters'
import { dailyPickReason, getDailyPick } from '../../utils/dailyPick'
import { describeProfile, getPersonalizedRecommendations } from '../../utils/personalization'
import {
  computePace,
  distinctReadingDays,
  estimateHoursLeft,
  formatHours,
  personaEmoji,
  personaOf
} from '../../utils/readingInsights'
import AddBookModal from '../UI/AddBookModal'
import BookCover from '../UI/BookCover'
import BookGridSkeleton from '../UI/BookGridSkeleton'
import SettingsModal from '../UI/SettingsModal'

// Enhanced Animation Variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      delayChildren: 0.1,
      staggerChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100
    }
  }
}

const cardHoverVariants = {
  hover: {
    scale: 1.02,
    y: -5,
    boxShadow: "0 20px 40px rgba(0,0,0,0.1)",
    transition: { duration: 0.2 }
  }
}

// Enhanced Dashboard Component with Modern UI Elements
const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const [addBookOpen, setAddBookOpen] = useState(false)
  const storeRecommendations = useAppSelector((state) => state.books.recommendations)
  const storeLoading = useAppSelector((state) => state.books.loading)
  const userPreferences = useAppSelector((state) => state.user.preferences)
  const userProfile = useAppSelector((state) => state.user.profile)
  const isAuthenticated = useAppSelector((state) => state.user.isAuthenticated)
  const hasCompletedOnboarding = useAppSelector(
    (state) => state.user.hasCompletedOnboarding
  )

  const [activeFilter, setActiveFilter] = useState('all')
  const [activeGenre, setActiveGenre] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showNotifications, setShowNotifications] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const theme = useAppSelector((state) => state.dashboard.theme)

  // ── Real, persisted reading data — every number on this page is derived. ──
  const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
  const readingLog = useAppSelector((state) => state.reading.readingLog)
  const favorites = useAppSelector((state) => state.user.favorites)
  const readingGoal = userPreferences.readingGoal
  const finishedCount = booksFinished(currentlyReading)
  const streak = computeStreak(readingLog)
  const monthPages = pagesThisMonth(readingLog)
  const totalPages = pagesAllTime(readingLog)
  const goalProgressPct =
    readingGoal > 0 ? Math.min(100, Math.round((finishedCount / readingGoal) * 100)) : 0
  const dailyPick = getDailyPick()

  // ── Reader-bliss layer ────────────────────────────────────────────────────
  // Identity + open-loop pull: the reader's persona is visible, and the
  // in-progress book gets a "pick up where you left off" nudge with an honest
  // time-to-finish estimate and a one-tap log (their own average session).
  const pace = computePace(readingLog)
  const persona = personaOf(pace.avgPagesPerSession, distinctReadingDays(readingLog), finishedCount)

  const activeEntry = currentlyReading.find((e) => e.finishedAt === null)
  const activeBook = activeEntry
    ? storeRecommendations.find((b) => b.id === activeEntry.bookId) ??
    BOOK_CATALOG.find((b) => b.id === activeEntry.bookId) ??
    (activeEntry.book
      ? {
        id: activeEntry.bookId,
        title: activeEntry.book.title,
        authors: activeEntry.book.authors,
        cover_url: activeEntry.book.cover_url,
        genres: activeEntry.book.genres,
        page_count: activeEntry.book.page_count
      }
      : null)
    : null
  const activePagesRead = activeEntry
    ? readingLog.filter((l) => l.bookId === activeEntry.bookId).reduce((a, l) => a + l.pages, 0)
    : 0
  const activeHoursLeft =
    activeBook && activeBook.page_count && activeBook.page_count > 0
      ? formatHours(
        estimateHoursLeft(Math.max(0, activeBook.page_count - activePagesRead), pace.avgPagesPerSession)
      )
      : null

  // ── Kind habit scaffolding ────────────────────────────────────────────────
  // A missed day shouldn't erase an identity. One honest repair per gap keeps
  // the run (and the motivation) alive without inventing pages read.
  const graceUsedFor = useAppSelector((state) => state.reading.graceUsedFor)
  const risk = useMemo(() => streakAtRisk(readingLog), [readingLog])
  const canRestoreStreak =
    risk.missedDate !== null && risk.brokenStreak >= 3 && graceUsedFor !== risk.missedDate

  // Inline micro-feedback: briefly confirm the save on the card itself, so the
  // reader does not have to look away to a toast to know it worked.
  const [justLoggedId, setJustLoggedId] = useState<string | null>(null)

  const flashLogged = (bookId: string) => {
    setJustLoggedId(bookId)
    window.setTimeout(() => setJustLoggedId(null), 1200)
  }

  const quickLogActive = () => {
    if (!activeEntry) return
    dispatch(logReadingSession({ bookId: activeEntry.bookId, pages: pace.avgPagesPerSession }))
    flashLogged(activeEntry.bookId)
    toast.success(
      `Logged your usual ${pace.avgPagesPerSession} pages — ${activeBook?.title ?? 'your book'} awaits! 🔥`
    )
  }

  const refreshRecommendations = () => {
    dispatch(fetchRecommendations({ limit: 6, strategy: 'hybrid' }))
    toast.success('Refreshing your recommendations… ✨')
  }

  /** Enter on the header search → full results on Discover (web search). */
  const submitSearch = () => {
    const q = searchQuery.trim()
    navigate(q ? `/discover?q=${encodeURIComponent(q)}` : '/discover')
  }

  // Real stats — all derived from persisted reading activity.
  const booksThisMonth = Math.round(monthPages / 300)
  const stats = [
    {
      icon: BookOpen,
      label: 'Books Finished',
      value: `${finishedCount}`,
      change: `${readingLog.length} sessions logged`,
      changePercent: `${booksThisMonth} book${booksThisMonth === 1 ? '' : 's'} this month`,
      color: 'bg-blue-500',
      trend: 'up'
    },
    {
      icon: Target,
      label: 'Reading Goal',
      value: `${finishedCount}/${readingGoal}`,
      change: `${Math.max(0, readingGoal - finishedCount)} to go`,
      changePercent: `${goalProgressPct}% complete`,
      color: 'bg-green-500',
      trend: 'up'
    },
    {
      icon: Star,
      label: 'Streak',
      value: `${streak} days`,
      // When a run is paused, say so — a lone "0 days" next to a recovery
      // banner reads like a contradiction.
      change: canRestoreStreak
        ? `${risk.brokenStreak}-day run paused`
        : streak > 0
          ? 'keep it going 🔥'
          : 'read today to start',
      changePercent: canRestoreStreak ? 'restore above' : streak > 0 ? 'on fire' : 'start today',
      color: 'bg-yellow-500',
      trend: 'up'
    },
    {
      icon: Activity,
      label: 'Pages This Month',
      value: `${monthPages}`,
      change: `${totalPages} pages all-time`,
      changePercent: `${readingLog.length} sessions`,
      color: 'bg-purple-500',
      trend: 'up'
    }
  ]

  const bookTitle = (id: string): string =>
    storeRecommendations.find((b) => b.id === id)?.title ??
    BOOK_CATALOG.find((b) => b.id === id)?.title ??
    id

  // Real activity feed — derived from the user's actual reading sessions.
  const activities = useMemo(() => {
    const sessions = [...readingLog].sort((a, b) => b.ts - a.ts).slice(0, 4)
    return sessions.length > 0
      ? sessions.map((log) => ({
        action: 'Read',
        book: `${bookTitle(log.bookId)} · ${log.pages} pages`,
        time: new Date(log.ts).toLocaleString(undefined, {
          hour: 'numeric',
          minute: '2-digit',
          day: 'numeric',
          month: 'short'
        }),
        icon: '📖'
      }))
      : [
        {
          action: 'No sessions yet',
          book: 'Start reading to build your streak',
          time: 'today',
          icon: '🌱'
        }
      ]
  }, [readingLog, storeRecommendations])

  /**
   * Chain-of-Thought: Rank the catalog against the reader's taste profile.
   * Personalization is instant and offline — no demo fallback; every card is
   * a real catalog book ranked for this reader. We expose the real fields
   * (genres, page count, year, moods) so the filter tabs and genre chips
   * below are backed by honest data.
   */
  const displayBooks = useMemo(() => {
    return getPersonalizedRecommendations(userPreferences, { limit: 9 }).map(
      (rec) => ({
        id: rec.book.id,
        title: rec.book.title,
        author: rec.book.authors,
        authors: rec.book.authors,
        cover_url: rec.book.cover_url,
        rating: rec.book.rating,
        progress: 0,
        genres: rec.book.genres,
        moods: rec.book.moods,
        page_count: rec.book.page_count,
        published_year: rec.book.published_year,
        trending: false,
        timeToRead: `${Math.max(2, Math.round(rec.book.page_count / 120))}h`,
        description: rec.book.description,
        reason: rec.reasons[0] ?? undefined
      })
    )
  }, [userPreferences])

  // Real progress lookup (persisted) + client-side search/genre/tab filter.
  const progressFor = (id: string): number => {
    const entry = currentlyReading.find((e) => e.bookId === id)
    return entry ? progressOf(entry) : 0
  }

  // The heart of this pass: filters that ACTUALLY filter. Tabs + genre chips
  // + search all flow through the shared vocabulary (src/utils/bookFilters.ts).
  const filteredBooks = useMemo(
    () =>
      applyBookFilters(displayBooks, {
        query: searchQuery,
        genre: activeGenre,
        tab: activeFilter
      }),
    [displayBooks, searchQuery, activeGenre, activeFilter]
  )

  // Live per-tab counts (loss-aversion: the reader knows what each tab holds
  // before committing; no tab ever looks like a dead end).
  const tabCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const tab of BOOK_FILTER_TABS) {
      counts[tab.id] = applyBookFilters(displayBooks, {
        query: searchQuery,
        genre: activeGenre,
        tab: tab.id
      }).length
    }
    return counts
  }, [displayBooks, searchQuery, activeGenre])

  // Genre chips ranked favorite-first (identity) with counts (recognition).
  const genreChips = useMemo(
    () => genreChipsFor(displayBooks, userPreferences.favoriteGenres ?? []),
    [displayBooks, userPreferences.favoriteGenres]
  )

  useEffect(() => {
    // Chain-of-Thought: Fetch personalized recommendations from the backend on mount.
    // The books slice caches results for 5 minutes to avoid redundant requests.
    dispatch(fetchRecommendations({ limit: 6, strategy: 'hybrid' }))
  }, [dispatch])

  return (
    <motion.div
      className="min-h-screen page-surface"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Enhanced Header with Search and Controls — hidden on phones (the
          mobile top bar owns the header there; search lives on Discover) */}
      <motion.header
        className="hidden md:block sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-700"
        variants={itemVariants}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Title */}
            <div className="flex items-center space-x-4">
              <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                📚 GoodBooks
              </div>
              <span className="hidden sm:block text-sm text-gray-500 dark:text-gray-400">
                Intelligent Reading Companion
              </span>
            </div>

            {/* Search Bar */}
            <div className="flex-1 max-w-lg mx-8">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search any book, author, or ISBN…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') submitSearch()
                  }}
                  aria-label="Search any book"
                  className="w-full pl-10 pr-16 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900 px-1.5 py-0.5 font-mono text-[10px] text-gray-500 dark:text-gray-400">
                  ⌘K
                </kbd>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              <button
                onClick={() => dispatch(setTheme(theme === 'dark' ? 'light' : 'dark'))}
                aria-label="Toggle dark mode"
                className="p-2.5 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-amber-400 transition-colors"
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2.5 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
              </button>
              <button
                onClick={() => setSettingsOpen(true)}
                aria-label="Open settings"
                className="p-2.5 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Dashboard Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section with Quick Actions */}
        <motion.div
          className="mb-8"
          variants={itemVariants}
        >
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-6 text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <h1 className="text-3xl font-bold">Welcome back, {userProfile.name.split(' ')[0]}! 👋</h1>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white/20 text-xs font-semibold" title="Your reading persona">
                    {personaEmoji(persona)} {persona}
                  </span>
                </div>
                <p className="text-blue-100 mb-4">
                  {readingGoal - finishedCount > 0
                    ? `You're ${readingGoal - finishedCount} book${readingGoal - finishedCount === 1 ? '' : 's'} away from your ${readingGoal}-book goal.`
                    : `Goal crushed — ${finishedCount}/${readingGoal} books finished. 🎉`}
                  {streak > 0 ? ` ${streak}-day streak, keep it going!` : ' Start a streak with a few pages today.'}
                </p>
                <div className="flex space-x-4">
                  <button
                    onClick={() => setAddBookOpen(true)}
                    className="bg-white/20 hover:bg-white/30 px-4 py-2.5 rounded-lg transition-all duration-200 flex items-center space-x-2"
                  >
                    <BookmarkPlus className="w-4 h-4" />
                    <span>Add Book</span>
                  </button>
                  <button
                    onClick={refreshRecommendations}
                    className="hidden sm:inline-flex bg-white/20 hover:bg-white/30 px-4 py-2.5 rounded-lg transition-all duration-200 items-center space-x-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>Get Recommendation</span>
                  </button>
                </div>
              </div>
              <div className="hidden lg:block">
                <div className="relative w-32 h-32">
                  <div className="absolute inset-0 bg-white/20 rounded-full"></div>
                  <div className="absolute inset-2 bg-white/10 rounded-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-2xl font-bold">{goalProgressPct}%</div>
                      <div className="text-xs text-blue-100">Complete</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Streak recovery — a missed day is a pause, not a verdict */}
        {canRestoreStreak && (
          <motion.div className="mb-8" variants={itemVariants}>
            <div className="surface-2 flex flex-wrap items-center gap-4 p-4">
              <span className="text-2xl" aria-hidden="true">🩹</span>
              <div className="min-w-0 flex-1">
                <p className="type-eyebrow text-amber-600 dark:text-amber-400">Streak recovery</p>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">
                  Your {risk.brokenStreak}-day streak is paused — one missed day doesn&apos;t have to end it.
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Restore the day once, or start fresh. Both count as showing up.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => {
                    dispatch(restoreStreak({ missedDate: risk.missedDate as string }))
                    toast.success('Streak restored — welcome back! 🔥')
                  }}
                  className="pressable px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-sm font-semibold"
                >
                  Restore my streak
                </button>
                <button
                  onClick={() => {
                    dispatch(dismissStreakRecovery({ missedDate: risk.missedDate as string }))
                    toast('Fresh start. Today counts. 🌱', { icon: '🌱' })
                  }}
                  className="pressable px-4 py-2.5 rounded-xl bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm font-semibold"
                >
                  Start fresh
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Continue Reading — the open loop that pulls readers back */}
        {activeEntry && activeBook && (
          <motion.div className="mb-8" variants={itemVariants}>
            <div className="surface-2 flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
              <div className="flex min-w-0 flex-1 items-center gap-4">
                <BookCover
                  title={activeBook.title}
                  author={activeBook.authors}
                  coverUrl={activeBook.cover_url}
                  genres={activeBook.genres}
                  seed={activeBook.id}
                  size="sm"
                  rounded="md"
                  showText={false}
                />
                <div className="min-w-0 flex-1">
                  <p className="type-eyebrow text-purple-600 dark:text-purple-400">
                    ⏳ Pick up where you left off
                  </p>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white truncate">
                    {activeBook.title}
                  </h3>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-600 dark:text-gray-400">
                    <span className="numeric">{progressFor(activeEntry.bookId)}% done</span>
                    {activeHoursLeft && (
                      <span className="inline-flex items-center gap-1 text-purple-600 dark:text-purple-300">
                        <Clock className="w-3.5 h-3.5" /> {activeHoursLeft} left at your pace
                      </span>
                    )}
                  </div>
                  <div className="mt-2 w-full max-w-xs rounded-full bg-gray-200 h-1.5 dark:bg-gray-700">
                    <div
                      className="h-1.5 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300"
                      style={{ width: `${progressFor(activeEntry.bookId)}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="flex flex-shrink-0 gap-2">
                <button
                  onClick={quickLogActive}
                  className="pressable flex-1 rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-purple-700 sm:flex-none"
                >
                  ⚡ Log {pace.avgPagesPerSession} pg
                </button>
                <button
                  onClick={() => navigate('/reading')}
                  className="pressable flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-semibold text-gray-700 transition-colors dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 sm:flex-none"
                >
                  Open shelf
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Today's Pick — a fresh daily reason to come back */}
        <motion.div className="mb-8" variants={itemVariants}>
          <div className="surface-2 flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
            <div className="flex min-w-0 flex-1 items-center gap-4">
              <BookCover
                title={dailyPick.title}
                author={dailyPick.authors}
                coverUrl={dailyPick.cover_url}
                genres={dailyPick.genres}
                seed={dailyPick.id}
                size="sm"
                rounded="md"
                showText={false}
              />
              <div className="min-w-0 flex-1">
                <p className="type-eyebrow text-blue-600 dark:text-blue-400">
                  ✨ Today&apos;s Pick
                </p>
                <h3 className="truncate text-lg font-bold text-gray-900 dark:text-white">
                  {dailyPick.title}
                </h3>
                <p className="truncate text-sm text-gray-600 dark:text-gray-400">
                  {dailyPick.authors} · {dailyPick.rating}★
                </p>
                <p className="mt-1 text-xs text-purple-700 dark:text-purple-300">
                  {dailyPickReason(dailyPick)}
                </p>
              </div>
            </div>
            <div className="flex flex-shrink-0 gap-2">
              <button
                onClick={() => dispatch(startReading({ bookId: dailyPick.id, book: dailyPick }))}
                className="pressable flex-1 rounded-lg bg-blue-600 px-3 py-2.5 text-sm text-white transition-colors hover:bg-blue-700 sm:flex-none"
              >
                Start Reading
              </button>
              <button
                onClick={() => dispatch(toggleFavorite(dailyPick.id))}
                className="pressable flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 sm:flex-none"
              >
                + Wishlist
              </button>
            </div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
          variants={itemVariants}
        >
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all duration-200"
              variants={cardHoverVariants}
              whileHover="hover"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
                <div className="text-right">
                  <div className="text-sm text-green-600 dark:text-green-400 flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    {stat.changePercent}
                  </div>
                </div>
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                <p className="text-gray-600 dark:text-gray-400 text-sm">{stat.label}</p>
                <p className="text-gray-500 dark:text-gray-500 text-xs mt-1">
                  {stat.change}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Filters — honest, working, reader-first.
            Tabs carry live counts; genre chips rank the reader's favorites
            first; the result line reassures with momentum. */}
        <motion.div className="mb-8" variants={itemVariants}>
          <div className="flex flex-wrap gap-2 mb-3">
            {BOOK_FILTER_TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveFilter(tab.id)}
                aria-pressed={activeFilter === tab.id}
                className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${activeFilter === tab.id
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
              >
                <span className="mr-1.5">{tab.emoji}</span>
                {tab.label}
                <span
                  className={`ml-2 text-xs ${activeFilter === tab.id ? 'text-blue-100' : 'text-gray-400'}`}
                >
                  {tabCounts[tab.id] ?? 0}
                </span>
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setActiveGenre('')}
              aria-pressed={activeGenre === ''}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${activeGenre === ''
                ? 'bg-purple-600 text-white'
                : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
            >
              All genres
            </button>
            {genreChips.map((chip) => (
              <button
                key={chip.genre}
                onClick={() => setActiveGenre(activeGenre === chip.genre ? '' : chip.genre)}
                aria-pressed={activeGenre === chip.genre}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${activeGenre === chip.genre
                  ? 'bg-purple-600 text-white'
                  : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
              >
                {chip.genre}
                <span
                  className={`ml-1.5 ${activeGenre === chip.genre ? 'text-purple-100' : 'text-gray-400'}`}
                >
                  {chip.count}
                </span>
              </button>
            ))}
          </div>

          <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
            Showing {filteredBooks.length} of {displayBooks.length} picks
            {activeGenre ? ` in ${activeGenre}` : ''}
            {searchQuery.trim() ? ` matching "${searchQuery.trim()}"` : ''}
          </p>
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Book Recommendations - Main Section */}
          <motion.div
            className="lg:col-span-3"
            variants={itemVariants}
          >
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <Sparkles className="w-5 h-5 mr-2 text-blue-600" />
                    AI-Powered Recommendations
                    {storeLoading && (
                      <span className="ml-3 text-xs text-blue-600 dark:text-blue-400 animate-pulse">
                        AI is analyzing…
                      </span>
                    )}
                  </h2>
                  <div className="flex space-x-2">
                    <button
                      onClick={refreshRecommendations}
                      aria-label="Refresh recommendations"
                      className="p-2.5 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {isAuthenticated && hasCompletedOnboarding && (
                  <p className="mt-2 text-xs text-blue-700 dark:text-blue-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    Personalized for {userProfile.name} — {describeProfile(userPreferences)}
                  </p>
                )}
              </div>

              <div className="p-6">
                {storeLoading && filteredBooks.length === 0 ? (
                  // Geometry-matched skeleton: the grid keeps its shape while
                  // picks load, so nothing jumps when the data lands.
                  <BookGridSkeleton count={6} />
                ) : filteredBooks.length === 0 ? (
                  <div className="py-12 text-center">
                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-100 dark:bg-gray-700 text-xl">
                      🔍
                    </div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      Nothing matches those filters yet
                    </p>
                    <p className="mx-auto mt-1 max-w-sm text-xs text-gray-500 dark:text-gray-400">
                      Your picks are still here — clear the search or genre to see them again.
                    </p>
                    <button
                      onClick={() => {
                        setSearchQuery('')
                        setActiveGenre('')
                        setActiveFilter('all')
                      }}
                      className="pressable mt-4 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
                    >
                      Show all picks
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredBooks.map((book) => (
                      <motion.div
                        key={book.id}
                        className="group bg-gray-50 dark:bg-gray-700 rounded-xl p-4 hover:shadow-lg transition-all duration-200"
                        variants={cardHoverVariants}
                        whileHover="hover"
                      >
                        <div className="flex items-start space-x-3 mb-3">
                          <BookCover
                            title={book.title}
                            author={book.author}
                            coverUrl={book.cover_url}
                            genres={book.genres}
                            seed={book.id}
                            size="sm"
                            rounded="md"
                            showText={false}
                          />
                          <div className="flex-1 min-w-0">
                            {book.trending && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 mb-1">
                                🔥 Trending
                              </span>
                            )}
                            <h3 className="font-semibold text-gray-900 dark:text-white text-sm leading-tight group-hover:text-blue-600 transition-colors">
                              {book.title}
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400 text-xs">{book.author}</p>
                          </div>
                        </div>

                        <p className="text-gray-600 dark:text-gray-400 text-xs mb-3 line-clamp-2">
                          {book.description}
                        </p>

                        {(book as any).reason && (
                          <p className="text-[11px] text-purple-700 dark:text-purple-300 flex items-center gap-1 mb-3">
                            <Sparkles className="w-3 h-3 flex-shrink-0" />
                            {(book as any).reason}
                          </p>
                        )}

                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="flex items-center text-yellow-600">
                              <Star className="w-3 h-3 mr-1 fill-current" />
                              {book.rating}
                            </span>
                            <span className="text-gray-500 flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {book.timeToRead}
                            </span>
                          </div>

                          {progressFor(book.id) > 0 && (
                            <div
                              className={`space-y-1 ${justLoggedId === book.id ? 'progress-just-updated' : ''}`}
                            >
                              <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                                <span>Progress</span>
                                <span className="numeric flex items-center gap-1">
                                  {progressFor(book.id)}%
                                  {justLoggedId === book.id && (
                                    <span className="saved-pulse text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                                      saved
                                    </span>
                                  )}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                                <div
                                  className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${progressFor(book.id)}%` }}
                                ></div>
                              </div>
                            </div>
                          )}

                          <div className="flex space-x-2 pt-2">
                            <button
                              onClick={() => {
                                if (progressFor(book.id) > 0) {
                                  // Honest quick log: the reader's own average session.
                                  dispatch(
                                    logReadingSession({ bookId: book.id, pages: pace.avgPagesPerSession })
                                  )
                                  flashLogged(book.id)
                                  toast.success(`Logged ${pace.avgPagesPerSession} pages — keep it going! 📚`)
                                } else {
                                  dispatch(
                                    startReading({
                                      bookId: book.id,
                                      book: {
                                        title: book.title,
                                        authors: book.author,
                                        cover_url: book.cover_url ?? '',
                                        genres: book.genres,
                                        description: book.description,
                                        page_count: book.page_count
                                      }
                                    })
                                  )
                                }
                              }}
                              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs py-3 px-3 rounded-lg transition-colors"
                            >
                              {progressFor(book.id) > 0
                                ? `Log ${pace.avgPagesPerSession} pg`
                                : 'Start Reading'}
                            </button>
                            <button
                              onClick={() => dispatch(toggleFavorite(book.id))}
                              className={`p-3 transition-colors ${favorites.includes(book.id) ? 'text-red-500' : 'text-gray-400 hover:text-red-500'}`}
                              aria-label="Toggle wishlist"
                            >
                              <Heart className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                const url = `${window.location.origin}/book/${encodeURIComponent(book.id)}`
                                navigator.clipboard
                                  .writeText(url)
                                  .then(() => toast.success('Link copied — share it with a reader 📎'))
                                  .catch(() => toast.error('Could not copy the link'))
                              }}
                              className="p-3 text-gray-400 hover:text-blue-500 transition-colors"
                              aria-label="Share book"
                            >
                              <Share className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          {/* Sidebar with Activity and Analytics */}
          <motion.div
            className="lg:col-span-1 space-y-6"
            variants={itemVariants}
          >
            {/* Reading Activity */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-green-600" />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {activities.map((activity, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <span className="text-lg">{activity.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 dark:text-white">
                        {activity.action} <strong>{activity.book}</strong>
                      </p>
                      <p className="text-xs text-gray-500">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Reading Analytics */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2 text-purple-600" />
                This Month
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Books This Month</span>
                    <span className="font-medium">{Math.round(monthPages / 300)}</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div className="bg-purple-600 h-2 rounded-full" style={{ width: `${Math.min(100, (monthPages / 300 / Math.max(1, readingGoal)) * 100)}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Reading Time</span>
                    <span className="font-medium">{Math.round(monthPages / 40)}h</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: `${Math.min(100, (monthPages / 1200) * 100)}%` }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Streak</span>
                    <span className="font-medium">{streak} days</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div className="bg-orange-600 h-2 rounded-full" style={{ width: `${Math.min(100, (streak / 30) * 100)}%` }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                <Zap className="w-5 h-5 mr-2 text-yellow-600" />
                Quick Actions
              </h3>
              <div className="space-y-3">
                <button
                  onClick={() => setAddBookOpen(true)}
                  className="w-full flex items-center justify-center space-x-2 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <BookmarkPlus className="w-4 h-4" />
                  <span>Add New Book</span>
                </button>
                <button
                  onClick={() => navigate('/analytics')}
                  className="w-full flex items-center justify-center space-x-2 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  <Target className="w-4 h-4" />
                  <span>Update Goal</span>
                </button>
                <button
                  onClick={() => navigate('/community')}
                  className="w-full flex items-center justify-center space-x-2 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                >
                  <Users className="w-4 h-4" />
                  <span>Join Community</span>
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Notification Panel */}
      <AnimatePresence>
        {showNotifications && (
          <motion.div
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className="fixed top-16 right-4 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 p-4"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900 dark:text-white">Notifications</h3>
              <button
                onClick={() => setShowNotifications(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Today&apos;s Pick is ready ✨</p>
                <p className="text-xs text-blue-700 dark:text-blue-300">{dailyPick.title} — {dailyPickReason(dailyPick)}</p>
              </div>
              <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm font-medium text-green-900 dark:text-green-100">Reading Goal Progress</p>
                <p className="text-xs text-green-700 dark:text-green-300">You&apos;re {goalProgressPct}% to your {readingGoal}-book goal{streak > 0 ? ` with a ${streak}-day streak!` : '.'}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add Book — web search modal */}
      <AddBookModal open={addBookOpen} onClose={() => setAddBookOpen(false)} />
      {/* Settings — real preferences panel */}
      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </motion.div>
  )
}

export default Dashboard

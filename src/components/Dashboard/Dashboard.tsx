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
  ChevronDown,
  Clock,
  Download,
  Eye,
  Filter,
  Heart,
  Search,
  Settings,
  Share,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  Users,
  Zap
} from 'lucide-react'
import React, { useEffect, useMemo, useState } from 'react'
import { BOOK_CATALOG } from '../../data/bookCatalog'
import { useAppDispatch, useAppSelector } from '../../hooks/redux'
import { fetchRecommendations } from '../../stores/books/booksSlice'
import {
  booksFinished,
  computeStreak,
  logReadingSession,
  pagesAllTime,
  pagesThisMonth,
  startReading
} from '../../stores/reading/readingSlice'
import { toggleFavorite } from '../../stores/user/userSlice'
import { dailyPickReason, getDailyPick } from '../../utils/dailyPick'
import { describeProfile, getPersonalizedRecommendations } from '../../utils/personalization'
import BookCover from '../UI/BookCover'

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
  const storeRecommendations = useAppSelector((state) => state.books.recommendations)
  const storeLoading = useAppSelector((state) => state.books.loading)
  const userPreferences = useAppSelector((state) => state.user.preferences)
  const userProfile = useAppSelector((state) => state.user.profile)
  const isAuthenticated = useAppSelector((state) => state.user.isAuthenticated)
  const hasCompletedOnboarding = useAppSelector(
    (state) => state.user.hasCompletedOnboarding
  )

  const [activeFilter, setActiveFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showNotifications, setShowNotifications] = useState(false)

  // ── Real, persisted reading data — every number on this page is derived. ──
  const currentlyReading = useAppSelector((state) => state.reading.currentlyReading)
  const readingLog = useAppSelector((state) => state.reading.readingLog)
  const favorites = useAppSelector((state) => state.user.favorites)
  const selectedGenre = 'All Genres'
  const readingGoal = userPreferences.readingGoal
  const finishedCount = booksFinished(currentlyReading)
  const streak = computeStreak(readingLog)
  const monthPages = pagesThisMonth(readingLog)
  const totalPages = pagesAllTime(readingLog)
  const goalProgressPct =
    readingGoal > 0 ? Math.min(100, Math.round((finishedCount / readingGoal) * 100)) : 0
  const dailyPick = getDailyPick()

  const filterOptions = ['all', 'trending', 'recommended', 'new', 'favorites']

  // Real stats — all derived from persisted reading activity.
  const stats = [
    {
      icon: BookOpen,
      label: 'Books Finished',
      value: `${finishedCount}`,
      change: `${readingLog.length} sessions logged`,
      changePercent: `${Math.round(monthPages / 300)} books this month`,
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
      change: streak > 0 ? 'keep it going 🔥' : 'read today to start',
      changePercent: streak > 0 ? 'on fire' : 'start today',
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
   * a real catalog book ranked for this reader.
   */
  const displayBooks = useMemo(() => {
    return getPersonalizedRecommendations(userPreferences, { limit: 6 }).map(
      (rec) => ({
        id: rec.book.id,
        title: rec.book.title,
        author: rec.book.authors,
        rating: rec.book.rating,
        progress: 0,
        genre: rec.book.genres[0] ?? 'Fiction',
        trending: false,
        timeToRead: `${Math.max(2, Math.round(rec.book.page_count / 120))}h`,
        description: rec.book.description,
        reason: rec.reasons[0] ?? undefined
      })
    )
  }, [userPreferences])

  // Real progress lookup (persisted) + client-side search filter.
  const progressFor = (id: string): number =>
    currentlyReading.find((e) => e.bookId === id)?.progressPct ?? 0

  const filteredBooks = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return displayBooks
    return displayBooks.filter((b) =>
      `${b.title} ${b.author} ${b.genre}`.toLowerCase().includes(q)
    )
  }, [displayBooks, searchQuery])

  useEffect(() => {
    // Chain-of-Thought: Fetch personalized recommendations from the backend on mount.
    // The books slice caches results for 5 minutes to avoid redundant requests.
    dispatch(fetchRecommendations({ limit: 6, strategy: 'hybrid' }))
  }, [dispatch])

  return (
    <motion.div
      className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Enhanced Header with Search and Controls */}
      <motion.header
        className="sticky top-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-700"
        variants={itemVariants}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Title */}
            <div className="flex items-center space-x-4">
              <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                📚 BookWise AI
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
                  placeholder="Search books, authors, or genres..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                <Bell className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
              </button>
              <button className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
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
                <h1 className="text-3xl font-bold mb-2">Welcome back, {userProfile.name.split(' ')[0]}! 👋</h1>
                <p className="text-blue-100 mb-4">
                  {readingGoal - finishedCount > 0
                    ? `You're ${readingGoal - finishedCount} book${readingGoal - finishedCount === 1 ? '' : 's'} away from your ${readingGoal}-book goal.`
                    : `Goal crushed — ${finishedCount}/${readingGoal} books finished. 🎉`}
                  {streak > 0 ? ` ${streak}-day streak, keep it going!` : ' Start a streak with a few pages today.'}
                </p>
                <div className="flex space-x-4">
                  <button className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-all duration-200 flex items-center space-x-2">
                    <BookmarkPlus className="w-4 h-4" />
                    <span>Add Book</span>
                  </button>
                  <button className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-all duration-200 flex items-center space-x-2">
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

        {/* Today's Pick — a fresh daily reason to come back */}
        <motion.div className="mb-8" variants={itemVariants}>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-blue-200 dark:border-blue-900 p-4 flex items-center gap-4">
            <BookCover
              title={dailyPick.title}
              author={dailyPick.authors}
              genres={dailyPick.genres}
              seed={dailyPick.id}
              size="sm"
              rounded="md"
              showText={false}
            />
            <div className="flex-1 min-w-0">
              <p className="text-xs uppercase tracking-wider text-blue-600 dark:text-blue-400 font-semibold">
                ✨ Today&apos;s Pick
              </p>
              <h3 className="text-lg font-bold text-gray-900 dark:text-white truncate">{dailyPick.title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {dailyPick.authors} · {dailyPick.rating}★
              </p>
              <p className="text-xs text-purple-700 dark:text-purple-300 mt-1">
                {dailyPickReason(dailyPick)}
              </p>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <button
                onClick={() => dispatch(startReading(dailyPick.id))}
                className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                Start Reading
              </button>
              <button
                onClick={() => dispatch(toggleFavorite(dailyPick.id))}
                className="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm rounded-lg transition-colors"
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

        {/* Filters and Genre Selection */}
        <motion.div
          className="flex flex-wrap items-center justify-between mb-8 gap-4"
          variants={itemVariants}
        >
          <div className="flex flex-wrap gap-2">
            {filterOptions.map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${activeFilter === filter
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
              >
                {filter.charAt(0).toUpperCase() + filter.slice(1)}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-4">
            <div className="relative">
              <button
                className="flex items-center space-x-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <Filter className="w-4 h-4" />
                <span className="text-sm">{selectedGenre}</span>
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </div>
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
                    <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                      <Eye className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                      <Download className="w-4 h-4" />
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
                          genres={book.genre ? [book.genre] : undefined}
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
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                              <span>Progress</span>
                              <span>{progressFor(book.id)}%</span>
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
                                dispatch(logReadingSession({ bookId: book.id, pages: 20 }))
                              } else {
                                dispatch(startReading(book.id))
                              }
                            }}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs py-2 px-3 rounded-lg transition-colors"
                          >
                            {progressFor(book.id) > 0 ? 'Log 20 pages' : 'Start Reading'}
                          </button>
                          <button
                            onClick={() => dispatch(toggleFavorite(book.id))}
                            className={`p-2 transition-colors ${favorites.includes(book.id) ? 'text-red-500' : 'text-gray-400 hover:text-red-500'}`}
                            aria-label="Toggle wishlist"
                          >
                            <Heart className="w-3 h-3" />
                          </button>
                          <button className="p-2 text-gray-400 hover:text-blue-500 transition-colors">
                            <Share className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
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
                <button className="w-full flex items-center justify-center space-x-2 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                  <BookmarkPlus className="w-4 h-4" />
                  <span>Add New Book</span>
                </button>
                <button className="w-full flex items-center justify-center space-x-2 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                  <Target className="w-4 h-4" />
                  <span>Update Goal</span>
                </button>
                <button className="w-full flex items-center justify-center space-x-2 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors">
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
    </motion.div>
  )
}

export default Dashboard

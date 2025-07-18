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
import React, { useEffect, useState } from 'react'

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
  const [activeFilter, setActiveFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedGenre, setSelectedGenre] = useState('All Genres')
  const [showNotifications, setShowNotifications] = useState(false)
  const [bookmarkCount, setBookmarkCount] = useState(15)
  const [readingGoal, setReadingGoal] = useState(52)
  const [currentProgress, setCurrentProgress] = useState(34)

  // Sample data for enhanced dashboard
  const genres = ['All Genres', 'Fiction', 'Non-Fiction', 'Mystery', 'Romance', 'Sci-Fi', 'Biography', 'History']
  const filterOptions = ['all', 'trending', 'recommended', 'new', 'favorites']

  const stats = [
    { 
      icon: BookOpen, 
      label: 'Books Read', 
      value: '127', 
      change: '+12', 
      changePercent: '+10.4%',
      color: 'bg-blue-500',
      trend: 'up'
    },
    { 
      icon: Target, 
      label: 'Reading Goal', 
      value: `${currentProgress}/${readingGoal}`, 
      change: '+5', 
      changePercent: '+15.2%',
      color: 'bg-green-500',
      trend: 'up'
    },
    { 
      icon: Star, 
      label: 'Avg Rating', 
      value: '8.7', 
      change: '+0.3', 
      changePercent: '+3.6%',
      color: 'bg-yellow-500',
      trend: 'up'
    },
    { 
      icon: Users, 
      label: 'Community', 
      value: '2.4K', 
      change: '+156', 
      changePercent: '+6.9%',
      color: 'bg-purple-500',
      trend: 'up'
    }
  ]

  const recentBooks = [
    {
      id: 1,
      title: "The Seven Husbands of Evelyn Hugo",
      author: "Taylor Jenkins Reid",
      cover: "📚",
      rating: 4.8,
      progress: 85,
      genre: "Fiction",
      trending: true,
      timeToRead: "2h 30m",
      description: "A captivating novel about Hollywood's golden age and the secrets of a reclusive icon."
    },
    {
      id: 2,
      title: "Atomic Habits",
      author: "James Clear",
      cover: "🧠",
      rating: 4.9,
      progress: 100,
      genre: "Self-Help",
      trending: false,
      timeToRead: "6h 15m",
      description: "Tiny changes, remarkable results. The ultimate guide to habit formation."
    },
    {
      id: 3,
      title: "Project Hail Mary",
      author: "Andy Weir",
      cover: "🚀",
      rating: 4.7,
      progress: 45,
      genre: "Sci-Fi",
      trending: true,
      timeToRead: "4h 45m",
      description: "A lone astronaut must save humanity in this thrilling space adventure."
    },
    {
      id: 4,
      title: "The Silent Patient",
      author: "Alex Michaelides",
      cover: "🔍",
      rating: 4.6,
      progress: 0,
      genre: "Mystery",
      trending: false,
      timeToRead: "5h 10m",
      description: "A woman's act of violence against her husband and her refusal to speak."
    },
    {
      id: 5,
      title: "Educated",
      author: "Tara Westover",
      cover: "🎓",
      rating: 4.8,
      progress: 67,
      genre: "Biography",
      trending: true,
      timeToRead: "7h 20m",
      description: "A memoir about education, family, and the struggle for self-invention."
    },
    {
      id: 6,
      title: "Where the Crawdads Sing",
      author: "Delia Owens",
      cover: "🌿",
      rating: 4.5,
      progress: 23,
      genre: "Fiction",
      trending: false,
      timeToRead: "6h 45m",
      description: "A coming-of-age mystery set in the marshlands of North Carolina."
    }
  ]

  const activities = [
    { action: "Finished reading", book: "Atomic Habits", time: "2 hours ago", icon: "✅" },
    { action: "Added to wishlist", book: "The Seven Moons of Maali Almeida", time: "5 hours ago", icon: "❤️" },
    { action: "Rated 5 stars", book: "Project Hail Mary", time: "1 day ago", icon: "⭐" },
    { action: "Shared review", book: "The Silent Patient", time: "2 days ago", icon: "📝" }
  ]

  useEffect(() => {
    console.log('🚀 Enhanced Futuristic Dashboard initializing...')
    // Initialize dashboard data and AI recommendations
  }, [])

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
                <h1 className="text-3xl font-bold mb-2">Welcome back, Reader! 👋</h1>
                <p className="text-blue-100 mb-4">
                  You're {readingGoal - currentProgress} books away from your {readingGoal}-book goal. Keep it up!
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
                      <div className="text-2xl font-bold">{Math.round((currentProgress / readingGoal) * 100)}%</div>
                      <div className="text-xs text-blue-100">Complete</div>
                    </div>
                  </div>
                </div>
              </div>
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
                  {stat.change} this month
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
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeFilter === filter
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
              </div>

              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {recentBooks.map((book) => (
                    <motion.div
                      key={book.id}
                      className="group bg-gray-50 dark:bg-gray-700 rounded-xl p-4 hover:shadow-lg transition-all duration-200"
                      variants={cardHoverVariants}
                      whileHover="hover"
                    >
                      <div className="flex items-start space-x-3 mb-3">
                        <div className="text-3xl">{book.cover}</div>
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

                        {book.progress > 0 && (
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                              <span>Progress</span>
                              <span>{book.progress}%</span>
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                              <div 
                                className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                style={{ width: `${book.progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}

                        <div className="flex space-x-2 pt-2">
                          <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs py-2 px-3 rounded-lg transition-colors">
                            {book.progress > 0 ? 'Continue' : 'Start Reading'}
                          </button>
                          <button className="p-2 text-gray-400 hover:text-red-500 transition-colors">
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
                    <span className="text-gray-600 dark:text-gray-400">Books Read</span>
                    <span className="font-medium">5/8</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div className="bg-purple-600 h-2 rounded-full" style={{ width: '62%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Reading Time</span>
                    <span className="font-medium">24h</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: '80%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">Streak</span>
                    <span className="font-medium">12 days</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div className="bg-orange-600 h-2 rounded-full" style={{ width: '95%' }}></div>
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
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">New Recommendation Available!</p>
                <p className="text-xs text-blue-700 dark:text-blue-300">Based on your reading of "Atomic Habits"</p>
              </div>
              <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm font-medium text-green-900 dark:text-green-100">Reading Goal Progress</p>
                <p className="text-xs text-green-700 dark:text-green-300">You're 65% complete for this month!</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

export default Dashboard

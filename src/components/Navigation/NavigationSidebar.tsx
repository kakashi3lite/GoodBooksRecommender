/**
 * 🧭 Enhanced Navigation Sidebar - Futuristic Design
 * Production-grade navigation with advanced interactions
 */

import { AnimatePresence, motion } from 'framer-motion'
import {
  Bell,
  BookmarkPlus,
  BookOpen,
  Heart,
  Home,
  LogOut,
  Menu,
  Moon,
  Newspaper,
  Search,
  Settings,
  Star,
  Target,
  TrendingUp,
  User,
  Users,
  X,
  Zap
} from 'lucide-react'
import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'

// Navigation Items with Enhanced Icons and Descriptions
const navigationItems = [
  {
    id: 'dashboard',
    path: '/',
    icon: Home,
    label: 'Dashboard',
    description: 'Your reading overview',
    badge: null,
    color: 'text-blue-600'
  },
  {
    id: 'discover',
    path: '/discover',
    icon: Search,
    label: 'Discover',
    description: 'Find new books',
    badge: 'New',
    color: 'text-green-600'
  },
  {
    id: 'reading',
    path: '/reading',
    icon: BookOpen,
    label: 'Currently Reading',
    description: '3 books in progress',
    badge: '3',
    color: 'text-orange-600'
  },
  {
    id: 'wishlist',
    path: '/wishlist',
    icon: Heart,
    label: 'Wishlist',
    description: 'Books to read later',
    badge: '12',
    color: 'text-red-600'
  },
  {
    id: 'analytics',
    path: '/analytics',
    icon: TrendingUp,
    label: 'Reading Analytics',
    description: 'Track your progress',
    badge: null,
    color: 'text-purple-600'
  },
  {
    id: 'community',
    path: '/community',
    icon: Users,
    label: 'Community',
    description: 'Connect with readers',
    badge: '5',
    color: 'text-indigo-600'
  },
  {
    id: 'news',
    path: '/news',
    icon: Newspaper,
    label: 'Book News',
    description: 'Latest literary updates',
    badge: 'Hot',
    color: 'text-yellow-600'
  }
]

const userActions = [
  {
    id: 'profile',
    icon: User,
    label: 'Profile',
    action: () => console.log('Profile clicked')
  },
  {
    id: 'notifications',
    icon: Bell,
    label: 'Notifications',
    action: () => console.log('Notifications clicked'),
    badge: '3'
  },
  {
    id: 'theme',
    icon: Moon,
    label: 'Dark Mode',
    action: () => console.log('Theme toggled')
  },
  {
    id: 'settings',
    icon: Settings,
    label: 'Settings',
    action: () => console.log('Settings clicked')
  },
  {
    id: 'logout',
    icon: LogOut,
    label: 'Sign Out',
    action: () => console.log('Logout clicked')
  }
]

// Animation variants
const sidebarVariants = {
  open: {
    width: "280px",
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 15
    }
  },
  closed: {
    width: "72px",
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 15
    }
  }
}

const itemVariants = {
  open: {
    opacity: 1,
    x: 0,
    transition: {
      type: "spring",
      stiffness: 100
    }
  },
  closed: {
    opacity: 0,
    x: -20,
    transition: {
      type: "spring",
      stiffness: 100
    }
  }
}

interface NavigationSidebarProps {
  className?: string
}

const NavigationSidebar: React.FC<NavigationSidebarProps> = ({ className = '' }) => {
  const [isExpanded, setIsExpanded] = useState(true)

  const toggleSidebar = () => setIsExpanded(!isExpanded)

  return (
    <motion.aside
      className={`fixed left-0 top-0 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 z-40 ${className}`}
      variants={sidebarVariants}
      animate={isExpanded ? "open" : "closed"}
      initial="open"
    >
      <div className="flex flex-col h-full">
        {/* Header with Logo and Toggle */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <AnimatePresence mode="wait">
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex items-center space-x-3"
              >
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <BookOpen className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h2 className="font-bold text-gray-900 dark:text-white text-lg">BookWise</h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400">AI Reading Assistant</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            {isExpanded ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* User Profile Section */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">JD</span>
            </div>
            <AnimatePresence mode="wait">
              {isExpanded && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="flex-1 min-w-0"
                >
                  <h3 className="font-semibold text-gray-900 dark:text-white text-sm">John Doe</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">john.doe@example.com</p>
                  <div className="flex items-center mt-1">
                    <Star className="w-3 h-3 text-yellow-500 mr-1" />
                    <span className="text-xs text-gray-600 dark:text-gray-400">Reading Level: Expert</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Quick Stats */}
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-4 border-b border-gray-200 dark:border-gray-700"
          >
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <BookOpen className="w-4 h-4 text-blue-600" />
                  <span className="text-xl font-bold text-blue-600">24</span>
                </div>
                <p className="text-xs text-blue-600 mt-1">Books Read</p>
              </div>
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <Target className="w-4 h-4 text-green-600" />
                  <span className="text-xl font-bold text-green-600">68%</span>
                </div>
                <p className="text-xs text-green-600 mt-1">Goal Progress</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Navigation Menu */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          <div className="space-y-1">
            {navigationItems.map((item) => (
              <NavLink
                key={item.id}
                to={item.path}
                className={({ isActive }) =>
                  `group flex items-center space-x-3 px-3 py-3 rounded-xl transition-all duration-200 relative ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 shadow-lg'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className={`p-2 rounded-lg ${isActive ? 'bg-blue-600 text-white' : 'group-hover:bg-gray-200 dark:group-hover:bg-gray-700'}`}>
                      <item.icon className="w-4 h-4" />
                    </div>
                    
                    <AnimatePresence mode="wait">
                      {isExpanded && (
                        <motion.div
                          variants={itemVariants}
                          initial="closed"
                          animate="open"
                          exit="closed"
                          className="flex-1 min-w-0"
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-sm">{item.label}</p>
                              <p className="text-xs opacity-70">{item.description}</p>
                            </div>
                            {item.badge && (
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                item.badge === 'New' || item.badge === 'Hot'
                                  ? 'bg-red-100 text-red-600 dark:bg-red-900/20 dark:text-red-400'
                                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                              }`}>
                                {item.badge}
                              </span>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {isActive && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute left-0 top-0 w-1 h-full bg-blue-600 rounded-r-full"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Quick Actions */}
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="p-4 border-t border-gray-200 dark:border-gray-700"
          >
            <div className="space-y-2">
              <button className="w-full flex items-center justify-center space-x-2 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg">
                <BookmarkPlus className="w-4 h-4" />
                <span className="font-medium">Add Book</span>
              </button>
              <button className="w-full flex items-center justify-center space-x-2 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <Zap className="w-4 h-4" />
                <span className="text-sm">Quick Recommendation</span>
              </button>
            </div>
          </motion.div>
        )}

        {/* User Actions */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-1">
          {userActions.map((action) => (
            <button
              key={action.id}
              onClick={action.action}
              className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <action.icon className="w-4 h-4" />
              <AnimatePresence mode="wait">
                {isExpanded && (
                  <motion.div
                    variants={itemVariants}
                    initial="closed"
                    animate="open"
                    exit="closed"
                    className="flex-1 flex items-center justify-between"
                  >
                    <span className="text-sm">{action.label}</span>
                    {action.badge && (
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-600 dark:bg-red-900/20 dark:text-red-400 rounded-full">
                        {action.badge}
                      </span>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </button>
          ))}
        </div>
      </div>
    </motion.aside>
  )
}

export default NavigationSidebar

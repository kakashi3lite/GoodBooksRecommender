/**
 * 📖 Currently Reading Page
 * Chain-of-Thought: Show books the reader has in progress with progress bars.
 * Memory: Reads shelf state from the books slice.
 */

import { motion } from 'framer-motion'
import { BookOpen, Clock } from 'lucide-react'
import React from 'react'
import { useAppSelector } from '../../hooks/redux'

/**
 * CurrentlyReading — a clean shelf view of in-progress books.
 * Falls back to a friendly empty state when the shelf is clear.
 */
const CurrentlyReading: React.FC = () => {
  const recommendations = useAppSelector((state) => state.books.recommendations)

  // For now, surface recommendations as the "currently reading" shelf.
  // A dedicated shelf API will refine this in a later milestone.
  const inProgress = recommendations.slice(0, 3)

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
            Your active shelf — pick up where you left off.
          </p>
        </div>

        {inProgress.length === 0 ? (
          <div className="text-center py-24">
            <div className="text-5xl mb-4">📖</div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              Your shelf is empty
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Head to Discover to find your next book.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {inProgress.map((book) => (
              <div
                key={book.id}
                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 shadow-lg hover:shadow-xl transition-shadow"
              >
                <div className="text-4xl mb-4">📖</div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {book.title}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {book.authors}
                </p>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="flex items-center text-gray-500 dark:text-gray-400">
                    <Clock className="w-3.5 h-3.5 mr-1" /> 45% complete
                  </span>
                </div>
                <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '45%' }} />
                </div>
                <button className="mt-5 w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors">
                  Continue Reading
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default CurrentlyReading

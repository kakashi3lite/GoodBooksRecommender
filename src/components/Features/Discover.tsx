/**
 * 🔍 Discover Page
 * Chain-of-Thought: AI-powered book discovery with semantic search and
 * personalized recommendations.
 * Forward-Thinking: Semantic "vibe" search will plug into this surface.
 */

import { motion } from 'framer-motion'
import { Search, Sparkles } from 'lucide-react'
import React, { useState } from 'react'
import AIBookRecommendations from '../AI/AIBookRecommendations'

/**
 * Discover — the reader's exploration surface. Renders the (now fixed)
 * AIBookRecommendations grid alongside a search entry point.
 */
const Discover: React.FC = () => {
    const [query, setQuery] = useState('')

    return (
        <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-gray-900 dark:via-blue-950 dark:to-indigo-950 p-8"
        >
            <div className="max-w-7xl mx-auto">
                {/* Hero */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                        <Sparkles className="w-8 h-8 text-purple-500" />
                        Discover Your Next Favorite Book
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400 mt-2">
                        Powered by our hybrid AI engine — content signals, collaborative patterns, and
                        community wisdom.
                    </p>
                </div>

                {/* Search bar (visual entry; deep semantic search is a roadmap feature) */}
                <div className="relative mb-8 max-w-2xl">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search books, authors, or genres..."
                        className="w-full pl-12 pr-4 py-3 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white placeholder-gray-400 shadow-lg"
                        aria-label="Search books"
                    />
                </div>

                {/* AI Recommendations */}
                <AIBookRecommendations limit={12} strategy="hybrid" />
            </div>
        </motion.div>
    )
}

export default Discover

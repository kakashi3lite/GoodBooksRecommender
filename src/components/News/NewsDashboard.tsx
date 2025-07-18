/**
 * 📰 News Dashboard - MVP Implementation
 * Senior Lead Engineer: Simple expandable news dashboard with AI-powered insights
 */

import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ExpandableNewsItem from './ExpandableNewsItem'

interface NewsStory {
  id: string
  title: string
  source?: string
  published_at?: string
  preview?: string
  credibility_score?: number
  topics?: string[]
}

interface NewsDashboardProps {
  className?: string
}

const NewsDashboard: React.FC<NewsDashboardProps> = ({ className = "" }) => {
  const [stories, setStories] = useState<NewsStory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedCount, setExpandedCount] = useState(0)

  // Fetch trending news stories
  const fetchTrendingStories = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await fetch('/api/news/stories/trending?limit=10', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch news: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Convert API response to component format
      const newsStories: NewsStory[] = data.map((story: any) => ({
        id: story.article_id,
        title: story.title,
        source: story.source || 'Unknown Source',
        published_at: story.published_at || new Date().toISOString(),
        preview: story.summary || 'Click to expand and see AI-powered analysis...',
        credibility_score: story.credibility_score,
        topics: story.topics
      }))

      setStories(newsStories)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load news'
      setError(errorMessage)
      console.error('News fetch failed:', err)
      
      // Fallback to demo data
      setStories(getDemoStories())
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Demo data for development/fallback
  const getDemoStories = (): NewsStory[] => [
    {
      id: "demo-1",
      title: "Climate Deal Signed by 30 Countries",
      source: "Reuters",
      published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      preview: "International agreement aims to reduce global emissions by 40% by 2030...",
      credibility_score: 0.92,
      topics: ["climate", "environment", "politics"]
    },
    {
      id: "demo-2", 
      title: "Tech Layoffs Surge in 2025 Q2",
      source: "TechCrunch",
      published_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      preview: "Major technology companies announce workforce reductions as AI automation accelerates...",
      credibility_score: 0.88,
      topics: ["technology", "business", "economy"]
    },
    {
      id: "demo-3",
      title: "Breakthrough in Quantum Computing Research",
      source: "Science Daily",
      published_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      preview: "Scientists achieve 99.9% fidelity in quantum error correction, paving way for practical applications...",
      credibility_score: 0.95,
      topics: ["science", "technology", "research"]
    },
    {
      id: "demo-4",
      title: "Global Health Initiative Launches",
      source: "WHO",
      published_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
      preview: "World Health Organization announces new program to combat infectious diseases in developing nations...",
      credibility_score: 0.97,
      topics: ["health", "global", "medicine"]
    },
    {
      id: "demo-5",
      title: "Artificial Intelligence in Education Study Results",
      source: "Nature",
      published_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
      preview: "Comprehensive analysis shows 34% improvement in learning outcomes with AI-assisted tutoring...",
      credibility_score: 0.94,
      topics: ["education", "ai", "technology", "research"]
    }
  ]

  // Handle story expansion
  const handleStoryExpand = useCallback((articleId: string) => {
    setExpandedCount(prev => prev + 1)
    
    // Track analytics (placeholder)
    console.log(`Story expanded: ${articleId}`)
  }, [])

  // Load stories on component mount
  useEffect(() => {
    fetchTrendingStories()
  }, [fetchTrendingStories])

  return (
    <div className={`max-w-4xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className="mb-8">
        <motion.h1 
          className="text-3xl font-bold text-gray-900 mb-2"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          🌐 News Dashboard
        </motion.h1>
        
        <motion.p 
          className="text-gray-600 mb-4"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Top news stories with AI-powered fact checking and context-aware book recommendations
        </motion.p>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>📊 {stories.length} stories loaded</span>
            <span>🔍 {expandedCount} expanded</span>
            <span>⚡ AI-powered analysis</span>
          </div>
          
          <button
            onClick={fetchTrendingStories}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors text-sm font-medium"
          >
            {isLoading ? '⟳ Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && stories.length === 0 && (
        <motion.div 
          className="flex items-center justify-center py-12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading top news stories...</p>
          </div>
        </motion.div>
      )}

      {/* Error State */}
      {error && (
        <motion.div 
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="flex items-center gap-2 text-red-700">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">Failed to load news</span>
          </div>
          <p className="text-red-600 text-sm mt-1">{error}</p>
          <p className="text-red-600 text-sm">Showing demo data instead.</p>
        </motion.div>
      )}

      {/* News Stories */}
      <div className="space-y-4">
        <AnimatePresence>
          {stories.map((story, index) => (
            <motion.div
              key={story.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ 
                duration: 0.3, 
                delay: index * 0.05 
              }}
            >
              <ExpandableNewsItem
                article={story}
                onExpand={handleStoryExpand}
                className="hover:scale-[1.02] transition-transform duration-200"
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {!isLoading && stories.length === 0 && (
        <motion.div 
          className="text-center py-12"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3v6M9 12l2 2 4-4" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No news stories available</h3>
          <p className="text-gray-600 mb-4">Try refreshing or check back later for the latest news.</p>
          <button
            onClick={fetchTrendingStories}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Retry Loading
          </button>
        </motion.div>
      )}

      {/* Footer Info */}
      <motion.div 
        className="mt-12 pt-6 border-t border-gray-200 text-center text-sm text-gray-500"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <div className="flex items-center justify-center gap-6">
          <span>🤖 AI-Powered Analysis</span>
          <span>📚 Context-Aware Books</span>
          <span>🔍 Fact Verification</span>
          <span>⚡ Real-time Updates</span>
        </div>
        <p className="mt-2">
          Powered by GoodBooks AI • News data refreshed every 30 minutes
        </p>
      </motion.div>
    </div>
  )
}

export default NewsDashboard

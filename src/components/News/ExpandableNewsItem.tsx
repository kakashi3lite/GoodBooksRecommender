/**
 * 📰 Expandable News Item Component - MVP Implementation
 * Senior Lead Engineer: Clean, performant expandable news interface
 */

import { AnimatePresence, motion } from 'framer-motion'
import React, { memo, useCallback, useState } from 'react'
// Simple SVG icons to replace Heroicons
const ChevronDownIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
  </svg>
)

const ChevronRightIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
  </svg>
)

const ExternalLinkIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
  </svg>
)

const BookOpenIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25A8.966 8.966 0 0 1 18 3.75c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
  </svg>
)

const CheckCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clipRule="evenodd" />
  </svg>
)

const XCircleIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm-1.72 6.97a.75.75 0 1 0-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 1 0 1.06 1.06L12 13.06l1.72 1.72a.75.75 0 1 0 1.06-1.06L13.06 12l1.72-1.72a.75.75 0 1 0-1.06-1.06L12 10.94l-1.72-1.72Z" clipRule="evenodd" />
  </svg>
)

const ExclamationTriangleIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path fillRule="evenodd" d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003ZM12 8.25a.75.75 0 0 1 .75.75v3.75a.75.75 0 0 1-1.5 0V9a.75.75 0 0 1 .75-.75Zm0 8.25a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Z" clipRule="evenodd" />
  </svg>
)

interface FactCheck {
  claim: string
  verdict: 'True' | 'False' | 'Unverified' | 'Mixed'
  confidence: number
  sources: string[]
  explanation: string
}

interface BookRecommendation {
  title: string
  author: string
  description: string
  relevance_score: number
  topics_matched: string[]
  buy_url?: string
  cover_url?: string
}

interface RelatedArticle {
  title: string
  url: string
  source: string
  relevance_score: number
  published_at?: string
}

interface NewsExpansion {
  article_id: string
  title: string
  summary: string
  topics: string[]
  sentiment: string
  credibility_score: number
  fact_checks: FactCheck[]
  book_recommendations: BookRecommendation[]
  related_articles: RelatedArticle[]
  processing_time_ms: number
  cache_hit: boolean
}

interface ExpandableNewsItemProps {
  article: {
    id: string
    title: string
    source?: string
    published_at?: string
    preview?: string
  }
  onExpand?: (articleId: string) => void
  className?: string
}

const ExpandableNewsItem: React.FC<ExpandableNewsItemProps> = memo(({
  article,
  onExpand,
  className = ""
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [expansion, setExpansion] = useState<NewsExpansion | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleExpand = useCallback(async () => {
    if (isExpanded) {
      setIsExpanded(false)
      return
    }

    if (expansion) {
      setIsExpanded(true)
      return
    }

    try {
      setIsLoading(true)
      setError(null)
      
      // Call the news expansion API
      const response = await fetch(`/api/news/expand/${article.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (!response.ok) {
        throw new Error(`Failed to expand news: ${response.statusText}`)
      }

      const expansionData: NewsExpansion = await response.json()
      setExpansion(expansionData)
      setIsExpanded(true)
      
      // Call optional expansion callback
      onExpand?.(article.id)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to expand news'
      setError(errorMessage)
      console.error('News expansion failed:', err)
    } finally {
      setIsLoading(false)
    }
  }, [article.id, expansion, isExpanded, onExpand])

  const getVerdictIcon = (verdict: string) => {
    switch (verdict) {
      case 'True':
        return <CheckCircleIcon className="w-4 h-4 text-green-500" />
      case 'False':
        return <XCircleIcon className="w-4 h-4 text-red-500" />
      case 'Mixed':
        return <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500" />
      default:
        return <ExclamationTriangleIcon className="w-4 h-4 text-gray-400" />
    }
  }

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'True':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'False':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'Mixed':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  return (
    <motion.div
      className={`border border-gray-200 rounded-lg bg-white shadow-sm hover:shadow-md transition-shadow ${className}`}
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      {/* News Item Header */}
      <div 
        className="p-4 cursor-pointer flex items-start justify-between hover:bg-gray-50 transition-colors"
        onClick={handleExpand}
      >
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 mb-2 leading-tight">
            {article.title}
          </h3>
          
          {article.preview && (
            <p className="text-gray-600 text-sm mb-2 line-clamp-2">
              {article.preview}
            </p>
          )}
          
          <div className="flex items-center gap-3 text-xs text-gray-500">
            {article.source && (
              <span className="font-medium">{article.source}</span>
            )}
            {article.published_at && (
              <span>{new Date(article.published_at).toLocaleDateString()}</span>
            )}
            {expansion?.credibility_score && (
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-green-400"></div>
                {Math.round(expansion.credibility_score * 100)}% credible
              </span>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          {isLoading && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          )}
          {isExpanded ? (
            <ChevronDownIcon className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRightIcon className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t border-gray-100">
              
              {/* Error State */}
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-red-600 text-sm">{error}</p>
                </div>
              )}

              {/* Expansion Content */}
              {expansion && (
                <div className="mt-4 space-y-6">
                  
                  {/* Summary */}
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">📄 Summary</h4>
                    <p className="text-gray-700 leading-relaxed">{expansion.summary}</p>
                    
                    {expansion.topics.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {expansion.topics.map((topic, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Fact Checks */}
                  {expansion.fact_checks.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        🧠 AI-Verified Facts
                        <span className="text-xs text-gray-500 font-normal">
                          ({expansion.fact_checks.length} claims checked)
                        </span>
                      </h4>
                      
                      <div className="space-y-3">
                        {expansion.fact_checks.map((fact, index) => (
                          <div
                            key={index}
                            className={`p-3 rounded-lg border ${getVerdictColor(fact.verdict)}`}
                          >
                            <div className="flex items-start justify-between mb-2">
                              <span className="text-sm font-medium flex items-center gap-2">
                                {getVerdictIcon(fact.verdict)}
                                {fact.verdict}
                              </span>
                              <span className="text-xs opacity-75">
                                {Math.round(fact.confidence * 100)}% confidence
                              </span>
                            </div>
                            
                            <p className="text-sm mb-2 italic">"{fact.claim}"</p>
                            <p className="text-xs opacity-90">{fact.explanation}</p>
                            
                            {fact.sources.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1">
                                {fact.sources.slice(0, 2).map((source, srcIndex) => (
                                  <a
                                    key={srcIndex}
                                    href={source}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs underline hover:no-underline flex items-center gap-1"
                                  >
                                    Source {srcIndex + 1}
                                    <ExternalLinkIcon className="w-3 h-3" />
                                  </a>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Book Recommendations */}
                  {expansion.book_recommendations.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        📚 Related Books
                        <span className="text-xs text-gray-500 font-normal">
                          (Context-aware recommendations)
                        </span>
                      </h4>
                      
                      <div className="grid gap-3 sm:grid-cols-2">
                        {expansion.book_recommendations.map((book, index) => (
                          <div
                            key={index}
                            className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                          >
                            <div className="flex gap-3">
                              {book.cover_url && (
                                <img
                                  src={book.cover_url}
                                  alt={book.title}
                                  className="w-12 h-16 object-cover rounded shadow-sm"
                                  onError={(e) => {
                                    e.currentTarget.style.display = 'none'
                                  }}
                                />
                              )}
                              
                              <div className="flex-1 min-w-0">
                                <h5 className="font-medium text-gray-900 text-sm leading-tight mb-1">
                                  {book.title}
                                </h5>
                                <p className="text-xs text-gray-600 mb-1">by {book.author}</p>
                                <p className="text-xs text-gray-700 line-clamp-2 mb-2">
                                  {book.description}
                                </p>
                                
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-green-600 font-medium">
                                    {Math.round(book.relevance_score * 100)}% relevant
                                  </span>
                                  
                                  {book.buy_url && (
                                    <a
                                      href={book.buy_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                                    >
                                      <BookOpenIcon className="w-3 h-3" />
                                      View
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Related Articles */}
                  {expansion.related_articles.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">🔗 Related Stories</h4>
                      
                      <div className="space-y-2">
                        {expansion.related_articles.map((related, index) => (
                          <a
                            key={index}
                            href={related.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1 min-w-0">
                                <h5 className="font-medium text-gray-900 text-sm leading-tight mb-1">
                                  {related.title}
                                </h5>
                                <div className="flex items-center gap-3 text-xs text-gray-500">
                                  <span>{related.source}</span>
                                  {related.published_at && (
                                    <span>{new Date(related.published_at).toLocaleDateString()}</span>
                                  )}
                                  <span>{Math.round(related.relevance_score * 100)}% related</span>
                                </div>
                              </div>
                              <ExternalLinkIcon className="w-4 h-4 text-gray-400 ml-2" />
                            </div>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Processing Info */}
                  <div className="text-xs text-gray-400 border-t border-gray-100 pt-3">
                    Processed in {expansion.processing_time_ms}ms
                    {expansion.cache_hit && " (cached)"}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
})

ExpandableNewsItem.displayName = 'ExpandableNewsItem'

export default ExpandableNewsItem

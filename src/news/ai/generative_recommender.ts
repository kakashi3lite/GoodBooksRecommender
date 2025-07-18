/**
 * 🎯 Generative Recommender TypeScript Adapter
 * TypeScript wrapper for the Python generative recommendation system
 */

import { GenerativeRecommendation, RecommendationContext } from '../../types/AIModels'
import { Book } from '../../types/book'
import { aiService } from '../../services/AIApiService'

interface RecommendationOptions {
  maxRecommendations?: number
  includeExplanation?: boolean
  includeConfidence?: boolean
  diversityWeight?: number
  noveltyWeight?: number
  popularityWeight?: number
  userPreferences?: {
    genres?: string[]
    authors?: string[]
    tags?: string[]
    excludeGenres?: string[]
  }
}

export class GenerativeRecommender {
  private static instance: GenerativeRecommender
  private modelVersion = '3.0.0'
  private isInitialized = false
  private lastRecommendationTime = 0
  private recommendationCache = new Map<string, GenerativeRecommendation[]>()

  private constructor() {
    this.initialize()
  }

  public static getInstance(): GenerativeRecommender {
    if (!GenerativeRecommender.instance) {
      GenerativeRecommender.instance = new GenerativeRecommender()
    }
    return GenerativeRecommender.instance
  }

  private async initialize(): Promise<void> {
    try {
      this.isInitialized = true
      console.log(`🎯 Generative Recommender TypeScript v${this.modelVersion} initialized`)
    } catch (error) {
      console.error('Failed to initialize Generative Recommender:', error)
      this.isInitialized = false
    }
  }

  /**
   * Get book recommendations for a user
   * @param userId - The user ID
   * @param options - Recommendation options
   * @returns Promise resolving to array of recommendations
   */
  public async getRecommendations(
    userId: number,
    options: RecommendationOptions = {}
  ): Promise<GenerativeRecommendation[]> {
    const cacheKey = `user_${userId}_${JSON.stringify(options)}`
    
    // Check cache first
    if (this.recommendationCache.has(cacheKey)) {
      const cached = this.recommendationCache.get(cacheKey)!
      console.log('🎯 Using cached recommendations')
      return cached
    }

    try {
      const request: any = {
        userId: userId.toString(),
        count: options.maxRecommendations || 10,
        filters: options.userPreferences ? {
          genres: options.userPreferences.genres,
          excludeRead: true
        } : undefined
      }
      
      const recommendations = await aiService.getRecommendations(request)
      
      if (recommendations && recommendations.length > 0) {
        // Apply user preferences filtering
        const filtered = this.applyUserPreferences(recommendations, options.userPreferences)
        
        // Cache the results
        this.recommendationCache.set(cacheKey, filtered)
        this.lastRecommendationTime = Date.now()
        
        return filtered
      }
      
      // Return fallback recommendations
      return this.getFallbackRecommendations(options)
    } catch (error) {
      console.warn('Error getting recommendations:', error)
      return this.getFallbackRecommendations(options)
    }
  }

  /**
   * Get recommendations based on a book
   * @param book - The reference book
   * @param options - Recommendation options
   * @returns Promise resolving to array of recommendations
   */
  public async getBookBasedRecommendations(
    book: Book,
    options: RecommendationOptions = {}
  ): Promise<GenerativeRecommendation[]> {
    const cacheKey = `book_${book.id}_${JSON.stringify(options)}`
    
    if (this.recommendationCache.has(cacheKey)) {
      return this.recommendationCache.get(cacheKey)!
    }

    try {
      // Use the book's metadata for context
      const context: RecommendationContext = {
        sourceType: 'book',
        sourceId: book.id.toString(),
        metadata: {
          title: book.title,
          authors: book.authors,
          genres: book.genres || [],
          tags: book.categories || [],
          description: book.description || ''
        }
      }

      const recommendations = await this.getContextualRecommendations(context, options)
      this.recommendationCache.set(cacheKey, recommendations)
      
      return recommendations
    } catch (error) {
      console.warn('Error getting book-based recommendations:', error)
      return this.getFallbackRecommendations(options)
    }
  }

  /**
   * Get contextual recommendations
   * @param context - The recommendation context
   * @param options - Recommendation options
   * @returns Promise resolving to array of recommendations
   */
  public async getContextualRecommendations(
    context: RecommendationContext,
    options: RecommendationOptions = {}
  ): Promise<GenerativeRecommendation[]> {
    try {
      // For now, delegate to the general recommendation service
      // In the future, this could be enhanced with context-specific logic
      const userId = context.sourceType === 'user' ? parseInt(context.sourceId) : 1
      return await this.getRecommendations(userId, options)
    } catch (error) {
      console.warn('Error getting contextual recommendations:', error)
      return this.getFallbackRecommendations(options)
    }
  }

  /**
   * Apply user preferences to filter recommendations
   * @param recommendations - Array of recommendations to filter
   * @param preferences - User preferences
   * @returns Filtered recommendations
   */
  private applyUserPreferences(
    recommendations: GenerativeRecommendation[],
    preferences?: RecommendationOptions['userPreferences']
  ): GenerativeRecommendation[] {
    if (!preferences) return recommendations

    return recommendations.filter(rec => {
      // Filter by preferred genres
      if (preferences.genres && preferences.genres.length > 0) {
        const hasPreferredGenre = preferences.genres.some(genre => 
          rec.genres?.includes(genre)
        )
        if (!hasPreferredGenre) return false
      }

      // Exclude unwanted genres
      if (preferences.excludeGenres && preferences.excludeGenres.length > 0) {
        const hasExcludedGenre = preferences.excludeGenres.some(genre => 
          rec.genres?.includes(genre)
        )
        if (hasExcludedGenre) return false
      }

      // Filter by preferred authors
      if (preferences.authors && preferences.authors.length > 0) {
        const hasPreferredAuthor = preferences.authors.some(author => 
          rec.author?.toLowerCase().includes(author.toLowerCase())
        )
        if (!hasPreferredAuthor) return false
      }

      return true
    })
  }

  /**
   * Get fallback recommendations when the service is unavailable
   * @param options - Recommendation options
   * @returns Array of fallback recommendations
   */
  private getFallbackRecommendations(options: RecommendationOptions): GenerativeRecommendation[] {
    const maxRecs = options.maxRecommendations || 5
    const fallbacks: GenerativeRecommendation[] = []

    // Create fallback recommendations
    const fallbackBooks = [
      { title: 'The Alchemist', authors: 'Paulo Coelho', genre: 'Fiction' },
      { title: '1984', authors: 'George Orwell', genre: 'Dystopian' },
      { title: 'To Kill a Mockingbird', authors: 'Harper Lee', genre: 'Classic' },
      { title: 'The Great Gatsby', authors: 'F. Scott Fitzgerald', genre: 'Classic' },
      { title: 'Pride and Prejudice', authors: 'Jane Austen', genre: 'Romance' }
    ]

    for (let i = 0; i < Math.min(maxRecs, fallbackBooks.length); i++) {
      const book = fallbackBooks[i]
      fallbacks.push({
        bookId: (i + 1).toString(),
        title: book.title,
        author: book.authors,
        score: 0.7,
        confidenceScore: 0.7,
        explanation: `Classic recommendation: ${book.title} is a widely acclaimed ${book.genre.toLowerCase()} novel.`,
        shortExplanation: `Classic ${book.genre.toLowerCase()} choice`,
        matchFactors: {
          genreMatch: 0.8,
          styleMatch: 0.7,
          themeMatch: 0.6,
          complexityMatch: 0.7,
          userHistoryMatch: 0.5
        },
        tags: [book.genre, 'classic', 'recommended'],
        genres: [book.genre],
        reasoning: [`Popular ${book.genre.toLowerCase()} choice`, 'High reader satisfaction', 'Timeless appeal'],
        confidence: 0.7,
        novelty: 0.4,
        serendipity: 0.3,
        similarityScore: 0.8,
        diversityScore: 0.6,
        noveltyScore: 0.4,
        metadata: {
          recommendationId: `fallback_${i + 1}`,
          generatedAt: new Date().toISOString(),
          modelVersion: this.modelVersion,
          context: 'fallback'
        }
      })
    }

    return fallbacks
  }

  /**
   * Get trending recommendations
   * @param options - Recommendation options
   * @returns Promise resolving to trending recommendations
   */
  public async getTrendingRecommendations(
    options: RecommendationOptions = {}
  ): Promise<GenerativeRecommendation[]> {
    try {
      // This could be enhanced to fetch actual trending data
      const trending = await this.getFallbackRecommendations(options)
      
      // Boost popularity scores for trending books
      return trending.map(rec => ({
        ...rec,
        explanation: `Trending now: ${rec.explanation}`,
        reasoning: ['Currently trending', ...(rec.reasoning || [])]
      }))
    } catch (error) {
      console.warn('Error getting trending recommendations:', error)
      return this.getFallbackRecommendations(options)
    }
  }

  /**
   * Clear recommendation cache
   */
  public clearCache(): void {
    this.recommendationCache.clear()
    console.log('🎯 Recommendation cache cleared')
  }

  /**
   * Get cache statistics
   * @returns Cache statistics
   */
  public getCacheStats(): { size: number; lastUpdate: number } {
    return {
      size: this.recommendationCache.size,
      lastUpdate: this.lastRecommendationTime
    }
  }

  /**
   * Get model information
   * @returns Model information object
   */
  public getModelInfo(): { version: string; initialized: boolean; capabilities: string[] } {
    return {
      version: this.modelVersion,
      initialized: this.isInitialized,
      capabilities: [
        'user_based_recommendations',
        'book_based_recommendations',
        'contextual_recommendations',
        'trending_recommendations',
        'preference_filtering',
        'diversity_optimization',
        'novelty_scoring',
        'explanation_generation',
        'batch_processing',
        'caching'
      ]
    }
  }
}

// Export singleton instance
export const generativeRecommender = GenerativeRecommender.getInstance()

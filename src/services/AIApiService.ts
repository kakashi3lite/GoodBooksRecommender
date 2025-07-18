/**
 * 🤖 AI API Service
 * Production-grade API service for AI component integration
 */

import { ELearnFitResult, ScoreRAGSummary, GenerativeRecommendation, RecommendationRequest } from '../types/AIModels'

class AIApiService {
  private baseUrl: string = '/api/ai'
  private cache = new Map<string, any>()
  
  // Cache TTL in milliseconds (5 minutes)
  private cacheTTL: number = 5 * 60 * 1000

  // Helper to handle API responses with caching
  private async fetchWithCache<T>(
    endpoint: string, 
    params: Record<string, any> = {}, 
    cacheKey?: string
  ): Promise<T> {
    // Generate cache key if not provided
    const key = cacheKey || `${endpoint}:${JSON.stringify(params)}`
    
    // Check cache first
    const cached = this.cache.get(key)
    if (cached && cached.expiry > Date.now()) {
      return cached.data as T
    }
    
    try {
      // Build URL with query params
      const url = new URL(`${this.baseUrl}/${endpoint}`, window.location.origin)
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, value.toString())
        }
      })
      
      // Fetch from API
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }
      
      const data = await response.json()
      
      // Cache the result
      this.cache.set(key, {
        data,
        expiry: Date.now() + this.cacheTTL
      })
      
      return data as T
    } catch (error) {
      console.error(`Error fetching from ${endpoint}:`, error)
      throw error
    }
  }

  // ELearnFit Optimizer API
  async getOptimizedScore(bookId: string, userId?: string): Promise<ELearnFitResult> {
    try {
      return await this.fetchWithCache<ELearnFitResult>(
        'optimize-score',
        { bookId, userId },
        `optimize-score:${bookId}:${userId}`
      )
    } catch (error) {
      console.warn('ELearnFit API unavailable, using fallback')
      // Fallback if API fails
      return {
        bookId,
        rawScore: Math.random() * 0.3 + 0.4, // 0.4-0.7
        optimizedScore: Math.random() * 0.3 + 0.6, // 0.6-0.9
        confidenceLevel: 0.7,
        optimizationFactors: {
          userPreference: Math.random(),
          trending: Math.random(),
          contextual: Math.random(),
          temporal: Math.random(),
          diversity: Math.random()
        },
        metadata: {
          processingTime: Math.random() * 50 + 10,
          modelVersion: 'fallback-v1.0',
          lastUpdated: new Date().toISOString()
        }
      }
    }
  }
  
  // ScoreRAG Summarization API
  async getSummary(text: string): Promise<ScoreRAGSummary | null> {
    if (!text || text.length < 10) return null
    
    try {
      return await this.fetchWithCache<ScoreRAGSummary>(
        'summarize',
        { text: text.substring(0, 1000) }, // Limit text length
        `summarize:${text.substring(0, 50)}`
      )
    } catch (error) {
      console.warn('ScoreRAG API unavailable, using fallback')
      // Fallback if API fails
      const sentences = text.split('.').filter(s => s.trim().length > 0)
      const summary = sentences.slice(0, 2).join('.') + '.'
      
      return {
        originalText: text,
        summaryText: summary.length > 200 ? summary.substring(0, 200) + '...' : summary,
        summaryScore: 0.75,
        keyInsights: ['AI-generated summary', 'Fallback mode active'],
        sentimentScore: 0,
        themes: ['general'],
        complexity: 'intermediate' as const,
        readingTime: Math.ceil(text.length / 1000),
        metadata: {
          processingTime: 45,
          modelVersion: 'fallback-v1.0',
          confidence: 0.5
        }
      }
    }
  }
  
  // Generative Recommender API
  async getRecommendations(request: RecommendationRequest): Promise<GenerativeRecommendation[]> {
    try {
      const response = await this.fetchWithCache<{ recommendations: GenerativeRecommendation[] }>(
        'recommendations',
        request,
        `recommendations:${request.userId}:${request.count || 5}`
      )
      return response.recommendations
    } catch (error) {
      console.warn('Recommendation API unavailable, using fallback')
      // Fallback if API fails
      return this.getFallbackRecommendations(request.count || 5)
    }
  }
  
  private getFallbackRecommendations(count: number): GenerativeRecommendation[] {
    const fallbackBooks = [
      {
        bookId: '1',
        title: 'The Pragmatic Programmer',
        author: 'Hunt & Thomas',
        explanation: 'Perfect for developers seeking practical programming wisdom and best practices.',
        shortExplanation: 'Essential programming wisdom'
      },
      {
        bookId: '2',
        title: 'Clean Code',
        author: 'Robert C. Martin',
        explanation: 'Fundamental guide to writing maintainable, readable code that scales.',
        shortExplanation: 'Master clean coding practices'
      },
      {
        bookId: '3',
        title: 'System Design Interview',
        author: 'Alex Xu',
        explanation: 'Comprehensive guide to designing scalable systems and acing technical interviews.',
        shortExplanation: 'Scale system design skills'
      },
      {
        bookId: '4',
        title: 'Designing Data-Intensive Applications',
        author: 'Martin Kleppmann',
        explanation: 'Deep dive into building reliable, scalable, and maintainable data systems.',
        shortExplanation: 'Master data architecture'
      },
      {
        bookId: '5',
        title: 'The Clean Coder',
        author: 'Robert C. Martin',
        explanation: 'Professional ethics and practices for software craftsmen.',
        shortExplanation: 'Professional software development'
      }
    ]
    
    return fallbackBooks.slice(0, count).map(book => ({
      ...book,
      score: Math.random() * 0.3 + 0.7, // 0.7-1.0
      matchFactors: {
        genreMatch: Math.random(),
        styleMatch: Math.random(),
        themeMatch: Math.random(),
        complexityMatch: Math.random(),
        userHistoryMatch: Math.random()
      },
      tags: ['programming', 'software-engineering', 'fallback'],
      confidence: 0.6,
      novelty: Math.random() * 0.4 + 0.3,
      serendipity: Math.random() * 0.5 + 0.2
    }))
  }

  // Clear cache
  clearCache(): void {
    this.cache.clear()
  }

  // Get cache stats
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    }
  }
}

export const aiService = new AIApiService()

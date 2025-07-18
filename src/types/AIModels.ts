/**
 * 🤖 AI Models Type Definitions
 * TypeScript interfaces for AI component integration
 */

export interface ELearnFitResult {
  bookId: string
  rawScore: number
  optimizedScore: number
  confidenceLevel: number
  optimizationFactors: {
    userPreference: number
    trending: number
    contextual: number
    temporal: number
    diversity: number
  }
  metadata?: {
    processingTime: number
    modelVersion: string
    lastUpdated: string
  }
}

export interface ScoreRAGSummary {
  originalText: string
  summaryText: string
  summaryScore: number
  keyInsights: string[]
  sentimentScore: number
  themes: string[]
  complexity: 'beginner' | 'intermediate' | 'advanced'
  readingTime: number // estimated minutes
  metadata?: {
    processingTime: number
    modelVersion: string
    confidence: number
  }
}

export interface GenerativeRecommendation {
  bookId: string
  title: string
  author: string
  score: number
  confidenceScore: number
  explanation: string
  shortExplanation: string
  matchFactors: {
    genreMatch: number
    styleMatch: number
    themeMatch: number
    complexityMatch: number
    userHistoryMatch: number
  }
  tags: string[]
  genres?: string[]
  reasoning?: string[]
  confidence: number
  novelty: number // how different this recommendation is
  serendipity: number // how surprising this recommendation is
  similarityScore?: number
  diversityScore?: number
  noveltyScore?: number
  metadata?: {
    recommendationId: string
    generatedAt: string
    modelVersion: string
    context?: string
  }
}

export interface RecommendationContext {
  sourceType: 'user' | 'book' | 'search' | 'trending'
  sourceId: string
  metadata?: {
    title?: string
    authors?: string
    genres?: string[]
    tags?: string[]
    description?: string
  }
}

export interface ParticleFeedVisualization {
  nodes: Array<{
    id: string
    title: string
    size: number
    group: number
    x?: number
    y?: number
    color?: string
    author?: string
    score?: number
  }>
  links: Array<{
    source: string
    target: string
    value: number
    type?: 'similarity' | 'author' | 'genre' | 'user-behavior'
  }>
  metadata: {
    totalNodes: number
    totalLinks: number
    maxScore: number
    minScore: number
    generatedAt: string
  }
}

export interface AIPerformanceMetrics {
  modelLatency: Record<string, number>
  recommendationAccuracy: number
  userSatisfactionScore: number
  coverageRate: number
  diversityScore: number
  noveltyScore: number
  lastUpdated: string
}

export interface AIModelConfig {
  modelType: 'collaborative' | 'content-based' | 'hybrid' | 'neural'
  version: string
  parameters: Record<string, any>
  isActive: boolean
  performance: AIPerformanceMetrics
}

export interface UserProfile {
  id: string
  preferences: {
    genres: string[]
    authors: string[]
    readingSpeed: 'slow' | 'average' | 'fast'
    sessionLength: 'short' | 'medium' | 'long'
    complexity: 'light' | 'moderate' | 'complex'
    mood: string[]
  }
  readingHistory: {
    totalBooks: number
    averageRating: number
    favoriteGenres: string[]
    readingStreak: number
    lastActivity: string
  }
  aiSettings: {
    recommendationStyle: 'conservative' | 'balanced' | 'adventurous'
    diversityPreference: number // 0-1
    noveltyTolerance: number // 0-1
    explanationDetail: 'minimal' | 'standard' | 'detailed'
  }
}

export interface RecommendationRequest {
  userId: string
  count?: number
  filters?: {
    genres?: string[]
    excludeRead?: boolean
    minRating?: number
    maxPages?: number
  }
  context?: {
    currentMood?: string
    availableTime?: number // minutes
    device?: 'mobile' | 'tablet' | 'desktop'
    location?: 'home' | 'commute' | 'travel'
  }
}

export interface RecommendationResponse {
  recommendations: GenerativeRecommendation[]
  metadata: {
    totalCandidates: number
    processingTime: number
    modelUsed: string
    requestId: string
    generatedAt: string
  }
  debugInfo?: {
    scoringBreakdown: Record<string, number>
    filteringSteps: string[]
    modelConfidence: number
  }
}

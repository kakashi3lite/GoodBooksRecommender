/**
 * 📚 Book Type Definitions
 * Production-grade TypeScript interfaces for book data structures
 */

export interface Book {
  id: string
  title: string
  authors: string
  author?: string // Legacy support
  description?: string
  isbn?: string
  isbn13?: string
  averageRating?: number
  ratingsCount?: number
  publicationYear?: number
  publishedDate?: string
  publisher?: string
  pageCount?: number
  language?: string
  categories?: string[]
  genres?: string[]
  imageLinks?: {
    thumbnail?: string
    smallThumbnail?: string
    small?: string
    medium?: string
    large?: string
    extraLarge?: string
  }
  
  // AI-enhanced fields
  aiRecommendationScore?: number
  ai_recommendation_score?: number // Legacy support
  matchFactors?: {
    genreMatch: number
    styleMatch: number
    themeMatch: number
    complexityMatch: number
  }
  
  // User interaction data
  userRating?: number
  readingStatus?: 'want-to-read' | 'currently-reading' | 'read'
  dateAdded?: string
  dateStarted?: string
  dateRead?: string
  personalNotes?: string
  
  // Visual presentation
  emoji?: string
  coverUrl?: string
  
  // Analytics
  viewCount?: number
  clickCount?: number
  lastViewed?: string
}

export interface BookCollection {
  id: string
  name: string
  description?: string
  books: Book[]
  isPublic: boolean
  createdAt: string
  updatedAt: string
}

export interface ReadingSession {
  id: string
  bookId: string
  startTime: string
  endTime?: string
  pagesRead?: number
  currentPage?: number
  notes?: string
  mood?: 'focused' | 'relaxed' | 'motivated' | 'tired'
  environment?: 'quiet' | 'noisy' | 'music' | 'outdoors'
}

export interface BookRecommendation extends Book {
  score: number
  explanation: string
  confidence: number
  recommendationType: 'collaborative' | 'content-based' | 'hybrid' | 'ai-generated'
  reasoning?: string[]
}

export interface BookFilter {
  genres?: string[]
  authors?: string[]
  ratingRange?: [number, number]
  yearRange?: [number, number]
  pageRange?: [number, number]
  language?: string[]
  readingStatus?: string[]
  hasDescription?: boolean
  hasImage?: boolean
}

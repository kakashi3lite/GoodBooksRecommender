/**
 * 📚 Books State Management
 * Chain-of-Thought: Manage book data, recommendations, and user interactions
 * Memory: Cache book details and recommendation history for O(1) retrieval
 * Forward-Thinking: Support for reading notes and community features
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import axios from 'axios'
import { API_ENDPOINTS } from '@utils/api'

export interface Book {
  id: string
  title: string
  authors: string
  rating: number
  ratingsCount?: number
  cover_url?: string
  description?: string
  genres: string[]
  published_year?: number
  isbn?: string
  page_count?: number
  ai_recommendation_score?: number
  ai_explanation?: string
}

export interface Recommendation {
  book: Book
  score: number
  reason: string
  aiGenerated: boolean
  timestamp: number
}

/**
 * Async thunk for fetching book recommendations
 * Chain-of-Thought: Fetch from real API with pre-aggregated data for O(1) retrieval
 * Time Complexity: Network I/O is O(1), processing is O(n) where n is result count
 */
export const fetchRecommendations = createAsyncThunk(
  'books/fetchRecommendations',
  async ({ userId, limit, strategy, genres, page = 1 }: { 
    userId?: string, 
    limit?: number, 
    strategy?: string,
    genres?: string[],
    page?: number
  }, { rejectWithValue, getState }) => {
    try {
      // Record API call start time for performance metrics
      const startTime = performance.now()
      
      // Extract current state to check for existing data
      const state = getState() as { books: BooksState }
      const { lastFetched } = state.books
      
      // Only fetch if data is stale (older than 5 minutes) or doesn't exist
      const isDataStale = !lastFetched || (Date.now() - lastFetched) > 5 * 60 * 1000
      
      // If we have enough cached recommendations and data isn't stale, use cache
      if (!isDataStale && state.books.recommendations.length >= (limit || 20) && page === 1) {
        return {
          recommendations: state.books.recommendations,
          fromCache: true,
          delta: []
        }
      }
      
      const params: Record<string, any> = {
        user_id: userId,
        limit: limit || 20,
        strategy: strategy || 'hybrid',
        genres: genres?.join(','),
        page: page
      }
      
      // Fetch with delta support - only get new items since last fetch if needed
      if (lastFetched && page === 1) {
        params.since = new Date(lastFetched).toISOString()
      }
      
      const response = await axios.get(API_ENDPOINTS.books.recommend(), { params })
      
      // Calculate API latency for metrics
      const apiLatency = performance.now() - startTime
      
      // Process and return the response data
      return {
        recommendations: response.data,
        fromCache: false,
        delta: params.since ? response.data : [],
        apiLatency
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch recommendations')
    }
  }
)

/**
 * Async thunk for fetching book details
 * Chain-of-Thought: Only fetch if not already cached for O(1) retrieval
 * Time Complexity: O(1) lookup for cached items
 */
export const fetchBookDetails = createAsyncThunk(
  'books/fetchBookDetails',
  async (bookId: string, { rejectWithValue, getState }) => {
    try {
      // Check if we already have this book in cache
      const state = getState() as { books: BooksState }
      const cachedBook = state.books.cache[bookId]
      
      // If cached and has full details, return from cache
      if (cachedBook && cachedBook.description) {
        return { book: cachedBook, fromCache: true }
      }
      
      // Fetch book details from API
      const startTime = performance.now()
      const response = await axios.get(API_ENDPOINTS.books.getById(bookId))
      const apiLatency = performance.now() - startTime
      
      return { 
        book: response.data,
        fromCache: false,
        apiLatency
      }
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch book details')
    }
  }
)

export interface BooksState {
  books: Book[]
  recommendations: Book[]
  recentRecommendations: Book[]
  favorites: string[]
  currentBook: Book | null
  loading: boolean
  error: string | null
  searchQuery: string
  filters: {
    genres: string[]
    minRating: number
    yearRange: [number, number]
    searchTerm: string
  }
  cache: Record<string, Book>
  lastFetched: number | null
  stats: {
    totalBooks: number
    totalGenres: number
    averageRating: number
    popularGenres: Record<string, number>
  }
  deltaSize: number
  viewHistory: string[] // IDs of books the user has viewed
}

/**
 * Initial state with optimal defaults
 * Chain-of-Thought: Set up state for O(1) lookups with proper indexing
 */
const initialState: BooksState = {
  books: [],
  recommendations: [],
  recentRecommendations: [],
  favorites: [],
  currentBook: null,
  loading: false,
  error: null,
  searchQuery: '',
  filters: {
    genres: [],
    minRating: 0,
    yearRange: [1900, new Date().getFullYear()],
    searchTerm: ''
  },
  cache: {},
  lastFetched: null,
  stats: {
    totalBooks: 0,
    totalGenres: 0,
    averageRating: 0,
    popularGenres: {}
  },
  deltaSize: 0,
  viewHistory: []
}

const booksSlice = createSlice({
  name: 'books',
  initialState,
  reducers: {
    setBooks: (state, action: PayloadAction<Book[]>) => {
      state.books = action.payload
      // Cache books for O(1) lookup efficiency
      action.payload.forEach(book => {
        state.cache[book.id] = book
      })
      
      // Update stats
      state.stats.totalBooks = state.books.length
      
      // Extract unique genres
      const allGenres = new Set<string>()
      const genreCounts: Record<string, number> = {}
      
      state.books.forEach(book => {
        book.genres.forEach(genre => {
          allGenres.add(genre)
          genreCounts[genre] = (genreCounts[genre] || 0) + 1
        })
      })
      
      state.stats.totalGenres = allGenres.size
      state.stats.popularGenres = genreCounts
      
      // Calculate average rating
      const totalRating = state.books.reduce((sum, book) => sum + book.rating, 0)
      state.stats.averageRating = totalRating / state.books.length
    },
    
    setRecommendations: (state, action: PayloadAction<Book[]>) => {
      state.recommendations = action.payload
    },
    
    addToRecentRecommendations: (state, action: PayloadAction<Book>) => {
      // Add to front of array for O(1) access to most recent items
      state.recentRecommendations = [
        action.payload, 
        ...state.recentRecommendations.filter(book => book.id !== action.payload.id)
      ].slice(0, 20) // Keep only 20 most recent items
      
      // Cache book for O(1) lookup
      state.cache[action.payload.id] = action.payload
    },
    
    addToFavorites: (state, action: PayloadAction<string>) => {
      if (!state.favorites.includes(action.payload)) {
        state.favorites.push(action.payload)
      }
    },
    
    removeFromFavorites: (state, action: PayloadAction<string>) => {
      state.favorites = state.favorites.filter(id => id !== action.payload)
    },
    
    setCurrentBook: (state, action: PayloadAction<Book | null>) => {
      state.currentBook = action.payload
      
      // Track in view history
      if (action.payload) {
        const bookId = action.payload.id
        state.viewHistory = [
          bookId,
          ...state.viewHistory.filter(id => id !== bookId)
        ].slice(0, 50) // Keep last 50 viewed books
      }
    },
    
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload
    },
    
    setFilters: (state, action: PayloadAction<Partial<BooksState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    
    clearCache: (state) => {
      state.cache = {}
      state.lastFetched = null
    },
    
    // Delta loading optimization
    updateDeltaSize: (state, action: PayloadAction<number>) => {
      state.deltaSize = action.payload
    }
  },
  
  extraReducers: (builder) => {
    builder
      // Handle fetchRecommendations
      .addCase(fetchRecommendations.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchRecommendations.fulfilled, (state, action) => {
        state.loading = false
        
        // Handle response
        const { recommendations, fromCache, delta } = action.payload
        
        if (!fromCache) {
          // Update cache with all books
          recommendations.forEach((book: Book) => {
            state.cache[book.id] = { ...state.cache[book.id], ...book }
          })
          
          // Update recommendations - either replace or append
          if (delta && delta.length > 0) {
            // Delta update - add new recommendations to the front
            const newIds = new Set(delta.map((book: Book) => book.id))
            
            state.recommendations = [
              ...delta,
              ...state.recommendations.filter(book => !newIds.has(book.id))
            ]
            
            state.deltaSize = delta.length
          } else {
            // Full update
            state.recommendations = recommendations
          }
          
          state.lastFetched = Date.now()
        }
      })
      .addCase(fetchRecommendations.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string || 'Failed to fetch recommendations'
      })
      
      // Handle fetchBookDetails
      .addCase(fetchBookDetails.pending, () => {
        // Don't set global loading for individual book details
        // This allows multiple requests without blocking the UI
      })
      .addCase(fetchBookDetails.fulfilled, (state, action) => {
        const { book } = action.payload
        
        // Update cache with detailed book info
        state.cache[book.id] = book
        
        // If this is the current book, update it
        if (state.currentBook?.id === book.id) {
          state.currentBook = book
        }
        
        // Also update in recommendations if present
        state.recommendations = state.recommendations.map(rec => 
          rec.id === book.id ? { ...rec, ...book } : rec
        )
      })
      .addCase(fetchBookDetails.rejected, (state, action) => {
        state.error = action.payload as string || 'Failed to fetch book details'
      })
  }
})

export const {
  setBooks,
  setRecommendations,
  addToRecentRecommendations,
  addToFavorites,
  removeFromFavorites,
  setCurrentBook,
  setSearchQuery,
  setFilters,
  setLoading,
  setError,
  clearCache,
  updateDeltaSize
} = booksSlice.actions

// Optimized selectors for memoized component access
export const selectBooks = (state: { books: BooksState }) => state.books.books
export const selectRecommendations = (state: { books: BooksState }) => state.books.recommendations
export const selectFavorites = (state: { books: BooksState }) => state.books.favorites
export const selectCurrentBook = (state: { books: BooksState }) => state.books.currentBook
export const selectBookCache = (state: { books: BooksState }) => state.books.cache

// Selector with memoization for O(1) book lookup by ID
export const selectBookById = (id: string) => 
  (state: { books: BooksState }) => state.books.cache[id]

// Selector for filtered recommendations
export const selectFilteredRecommendations = (state: { books: BooksState }) => {
  const { recommendations, filters } = state.books
  
  return recommendations.filter(book => {
    // Filter by genre if specified
    if (filters.genres.length > 0) {
      const hasMatchingGenre = book.genres.some(g => 
        filters.genres.includes(g.toLowerCase())
      )
      if (!hasMatchingGenre) return false
    }
    
    // Filter by minimum rating
    if (book.rating < filters.minRating) return false
    
    // Filter by year range
    if (
      book.published_year && 
      (book.published_year < filters.yearRange[0] || book.published_year > filters.yearRange[1])
    ) {
      return false
    }
    
    // Filter by search term
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase()
      const matchesTitle = book.title.toLowerCase().includes(searchLower)
      const matchesAuthor = book.authors.toLowerCase().includes(searchLower)
      const matchesDesc = book.description?.toLowerCase().includes(searchLower) || false
      
      if (!matchesTitle && !matchesAuthor && !matchesDesc) return false
    }
    
    return true
  })
}

export default booksSlice.reducer

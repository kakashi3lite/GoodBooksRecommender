/**
 * 🌐 API Routes and Endpoints
 * Chain-of-Thought: RESTful API design for scalable book recommendations
 * Memory: Consistent API patterns for frontend consumption
 * Forward-Thinking: Extensible endpoints for future features
 */

// Base API configuration
export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000'

// API Endpoints
export const API_ENDPOINTS = {
  // Core book recommendations
  books: {
    getAll: () => `${API_BASE_URL}/api/books`,
    getById: (id: string) => `${API_BASE_URL}/api/books/${id}`,
    search: () => `${API_BASE_URL}/api/books/search`,
    recommend: () => `${API_BASE_URL}/api/books/recommend`,
    similar: (id: string) => `${API_BASE_URL}/api/books/${id}/similar`
  },
  
  // AI-powered features
  ai: {
    chat: () => `${API_BASE_URL}/api/ai/chat`,
    tooltip: () => `${API_BASE_URL}/api/ai/tooltip`,
    analysis: () => `${API_BASE_URL}/api/ai/analysis`,
    predict: () => `${API_BASE_URL}/api/ai/predict`
  },
  
  // User management
  user: {
    profile: () => `${API_BASE_URL}/api/user/profile`,
    preferences: () => `${API_BASE_URL}/api/user/preferences`,
    history: () => `${API_BASE_URL}/api/user/history`,
    favorites: () => `${API_BASE_URL}/api/user/favorites`
  },
  
  // Forward-Thinking: Future feature endpoints
  notes: {
    getAll: () => `${API_BASE_URL}/api/notes`,
    create: () => `${API_BASE_URL}/api/notes`,
    update: (id: string) => `${API_BASE_URL}/api/notes/${id}`,
    delete: (id: string) => `${API_BASE_URL}/api/notes/${id}`,
    search: () => `${API_BASE_URL}/api/notes/search`
  },
  
  community: {
    posts: () => `${API_BASE_URL}/api/community/posts`,
    comments: () => `${API_BASE_URL}/api/community/comments`,
    discussions: () => `${API_BASE_URL}/api/community/discussions`,
    reviews: () => `${API_BASE_URL}/api/community/reviews`
  },
  
  analytics: {
    dashboard: () => `${API_BASE_URL}/api/analytics/dashboard`,
    reading: () => `${API_BASE_URL}/api/analytics/reading`,
    trends: () => `${API_BASE_URL}/api/analytics/trends`,
    performance: () => `${API_BASE_URL}/api/analytics/performance`
  }
}

// HTTP Client with error handling
export class APIClient {
  private baseURL: string
  
  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }
  
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseURL}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    })
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`)
    }
    
    return response.json()
  }
  
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }
  
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    })
  }
  
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    })
  }
  
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

// Default API client instance
export const apiClient = new APIClient()

// Specific API service functions
export const BookService = {
  getRecommendations: async (userId?: string) => {
    return apiClient.get(API_ENDPOINTS.books.recommend())
  },
  
  searchBooks: async (query: string) => {
    return apiClient.get(`${API_ENDPOINTS.books.search()}?q=${encodeURIComponent(query)}`)
  },
  
  getBookDetails: async (bookId: string) => {
    return apiClient.get(API_ENDPOINTS.books.getById(bookId))
  }
}

export const AIService = {
  generateTooltip: async (bookId: string, context: string) => {
    return apiClient.post(API_ENDPOINTS.ai.tooltip(), { bookId, context })
  },
  
  chatWithAI: async (message: string) => {
    return apiClient.post(API_ENDPOINTS.ai.chat(), { message })
  }
}

// Forward-Thinking: Future services
export const NotesService = {
  getAllNotes: async () => apiClient.get(API_ENDPOINTS.notes.getAll()),
  createNote: async (note: any) => apiClient.post(API_ENDPOINTS.notes.create(), note),
  updateNote: async (id: string, note: any) => apiClient.put(API_ENDPOINTS.notes.update(id), note),
  deleteNote: async (id: string) => apiClient.delete(API_ENDPOINTS.notes.delete(id))
}

export const CommunityService = {
  getPosts: async () => apiClient.get(API_ENDPOINTS.community.posts()),
  createPost: async (post: any) => apiClient.post(API_ENDPOINTS.community.posts(), post)
}

export const AnalyticsService = {
  getDashboardData: async () => apiClient.get(API_ENDPOINTS.analytics.dashboard()),
  getReadingAnalytics: async () => apiClient.get(API_ENDPOINTS.analytics.reading())
}

/**
 * GoodBooks Recommender Dashboard - API Client
 * Handles all API communication with JWT authentication, error handling and caching
 */

class APIClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    this.requestCounter = 0;
    this.token = this.getStoredToken();
    this.refreshToken = this.getStoredRefreshToken();
  }

  /**
   * Get stored JWT token from localStorage
   */
  getStoredToken() {
    try {
      return localStorage.getItem('goodbooks_access_token');
    } catch (e) {
      console.warn('Failed to get stored token:', e);
      return null;
    }
  }

  /**
   * Get stored refresh token from localStorage
   */
  getStoredRefreshToken() {
    try {
      return localStorage.getItem('goodbooks_refresh_token');
    } catch (e) {
      console.warn('Failed to get stored refresh token:', e);
      return null;
    }
  }

  /**
   * Store authentication tokens securely
   */
  storeTokens(accessToken, refreshToken) {
    try {
      localStorage.setItem('goodbooks_access_token', accessToken);
      if (refreshToken) {
        localStorage.setItem('goodbooks_refresh_token', refreshToken);
      }
      this.token = accessToken;
      this.refreshToken = refreshToken;
    } catch (e) {
      console.error('Failed to store tokens:', e);
    }
  }

  /**
   * Clear stored tokens (logout)
   */
  clearTokens() {
    try {
      localStorage.removeItem('goodbooks_access_token');
      localStorage.removeItem('goodbooks_refresh_token');
      this.token = null;
      this.refreshToken = null;
    } catch (e) {
      console.error('Failed to clear tokens:', e);
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!this.token;
  }

  /**
   * Get authentication headers
   */
  getAuthHeaders() {
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  /**
   * Make HTTP request with error handling, authentication, and caching
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const requestId = ++this.requestCounter;
    
    // Check cache for GET requests
    if (!options.method || options.method === 'GET') {
      const cached = this.getFromCache(url);
      if (cached) {
        console.log(`[API] Cache hit for ${endpoint}`);
        return cached;
      }
    }

    const startTime = performance.now();
    
    try {
      console.log(`[API] Request ${requestId}: ${options.method || 'GET'} ${endpoint}`);
      
      const defaultOptions = {
        headers: this.getAuthHeaders()
      };

      let response = await fetch(url, { ...defaultOptions, ...options });
      
      // Handle token refresh on 401 Unauthorized
      if (response.status === 401 && this.refreshToken && endpoint !== '/auth/refresh') {
        console.log('[API] Token expired, attempting refresh...');
        const refreshed = await this.refreshAccessToken();
        
        if (refreshed) {
          // Retry the original request with new token
          defaultOptions.headers = this.getAuthHeaders();
          response = await fetch(url, { ...defaultOptions, ...options });
        } else {
          // Refresh failed, redirect to login
          this.handleAuthenticationFailure();
          throw new Error('Authentication failed');
        }
      }
      
      const endTime = performance.now();
      
      console.log(`[API] Response ${requestId}: ${response.status} (${Math.round(endTime - startTime)}ms)`);

      if (!response.ok) {
        const errorData = await response.text();
        let errorMessage;
        
        try {
          const errorJson = JSON.parse(errorData);
          errorMessage = errorJson.detail || errorJson.message || `HTTP ${response.status}`;
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        
        throw new APIError(errorMessage, response.status, errorData);
      }

      const data = await response.json();
      
      // Cache successful GET requests
      if (!options.method || options.method === 'GET') {
        this.setCache(url, data);
      }

      return data;
    } catch (error) {
      const endTime = performance.now();
      console.error(`[API] Error ${requestId}: ${error.message} (${Math.round(endTime - startTime)}ms)`);
      
      if (error instanceof APIError) {
        throw error;
      }
      
      throw new APIError(`Network error: ${error.message}`, 0, error);
    }
  }

  /**
   * GET request wrapper
   */
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  /**
   * POST request wrapper
   */
  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  /**
   * Cache management
   */
  getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clearCache() {
    this.cache.clear();
    console.log('[API] Cache cleared');
  }

  // ===== API ENDPOINTS =====

  /**
   * Health check
   */
  async getHealth() {
    return this.get('/health');
  }

  /**
   * Get system metrics
   */
  async getMetrics() {
    return this.get('/metrics');
  }

  // =====================================
  // AUTHENTICATION METHODS
  // =====================================

  /**
   * Register a new user account
   */
  async register(username, email, password) {
    try {
      const response = await this.post('/auth/register', {
        username,
        email,
        password
      });
      
      console.log('[API] User registered successfully');
      return response;
    } catch (error) {
      console.error('[API] Registration failed:', error);
      throw error;
    }
  }

  /**
   * Login user and store tokens
   */
  async login(username, password) {
    try {
      const response = await this.post('/auth/login', {
        username,
        password
      });
      
      if (response.access_token) {
        this.storeTokens(response.access_token, response.refresh_token);
        console.log('[API] Login successful');
      }
      
      return response;
    } catch (error) {
      console.error('[API] Login failed:', error);
      throw error;
    }
  }

  /**
   * Logout user and clear tokens
   */
  async logout() {
    try {
      if (this.token) {
        await this.post('/auth/logout');
      }
    } catch (error) {
      console.warn('[API] Logout request failed:', error);
    } finally {
      this.clearTokens();
      console.log('[API] Logout completed');
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken() {
    if (!this.refreshToken) {
      return false;
    }

    try {
      const response = await this.post('/auth/refresh', {
        refresh_token: this.refreshToken
      });
      
      if (response.access_token) {
        this.storeTokens(response.access_token, this.refreshToken);
        console.log('[API] Token refreshed successfully');
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('[API] Token refresh failed:', error);
      this.clearTokens();
      return false;
    }
  }

  /**
   * Handle authentication failure (redirect to login)
   */
  handleAuthenticationFailure() {
    this.clearTokens();
    console.log('[API] Authentication failed, redirecting to login');
    
    // Dispatch custom event for UI to handle
    window.dispatchEvent(new CustomEvent('authenticationFailed'));
  }

  /**
   * Get book recommendations
   */
  async getRecommendations(params = {}) {
    const {
      user_id,
      book_title,
      n_recommendations = 5,
      include_explanation = false,
      cache_ttl
    } = params;

    const payload = {
      n_recommendations,
      include_explanation
    };

    if (user_id) payload.user_id = user_id;
    if (book_title) payload.book_title = book_title;
    if (cache_ttl) payload.cache_ttl = cache_ttl;

    return this.post('/recommendations', payload);
  }

  /**
   * Get batch recommendations
   */
  async getBatchRecommendations(userIds, nRecommendations = 5) {
    return this.post('/recommendations/batch', {
      user_ids: userIds,
      n_recommendations: nRecommendations
    });
  }

  /**
   * Search books
   */
  async searchBooks(query, filters = {}) {
    const params = new URLSearchParams({
      q: query,
      ...filters
    });
    
    return this.get(`/books/search?${params}`);
  }

  /**
   * Get book explanation
   */
  async explainRecommendation(bookId, type = 'hybrid', contextBooks = 5) {
    return this.post('/explain', {
      book_id: bookId,
      recommendation_type: type,
      n_context_books: contextBooks
    });
  }

  /**
   * Semantic search
   */
  async semanticSearch(query, options = {}) {
    const {
      k = 5,
      score_threshold = 0.0,
      include_explanation = false
    } = options;

    return this.post('/search', {
      query,
      k,
      score_threshold,
      include_explanation
    });
  }

  /**
   * Session management
   */
  async manageSession(action, options = {}) {
    const {
      session_id,
      user_id,
      ttl
    } = options;

    const payload = { action };
    if (session_id) payload.session_id = session_id;
    if (user_id) payload.user_id = user_id;
    if (ttl) payload.ttl = ttl;

    return this.post('/session', payload);
  }

  /**
   * Create session
   */
  async createSession(userId, ttl = 86400) {
    return this.manageSession('create', { user_id: userId, ttl });
  }

  /**
   * Get session
   */
  async getSession(sessionId) {
    return this.manageSession('get', { session_id: sessionId });
  }

  /**
   * Update session
   */
  async updateSession(sessionId, data) {
    return this.manageSession('update', { session_id: sessionId, ...data });
  }

  /**
   * Delete session
   */
  async deleteSession(sessionId) {
    return this.manageSession('delete', { session_id: sessionId });
  }

  /**
   * Get system statistics
   */
  async getStats() {
    return this.get('/stats');
  }

  /**
   * Development endpoints (if available)
   */
  async resetCache() {
    try {
      return this.get('/dev/reset-cache');
    } catch (error) {
      console.warn('[API] Development endpoint not available:', error.message);
      return null;
    }
  }

  async warmCache() {
    try {
      return this.get('/dev/warm-cache');
    } catch (error) {
      console.warn('[API] Development endpoint not available:', error.message);
      return null;
    }
  }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
  constructor(message, status = 0, response = null) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
  }

  get isNetworkError() {
    return this.status === 0;
  }

  get isClientError() {
    return this.status >= 400 && this.status < 500;
  }

  get isServerError() {
    return this.status >= 500;
  }
}

/**
 * API Response wrapper with type checking
 */
class APIResponse {
  constructor(data, endpoint, cached = false) {
    this.data = data;
    this.endpoint = endpoint;
    this.cached = cached;
    this.timestamp = Date.now();
  }

  get isRecommendation() {
    return this.data.recommendations !== undefined;
  }

  get isSearch() {
    return this.data.results !== undefined;
  }

  get isExplanation() {
    return this.data.explanation !== undefined;
  }

  get isHealth() {
    return this.data.status !== undefined;
  }

  get isSession() {
    return this.data.session_id !== undefined;
  }

  get processingTime() {
    return this.data.processing_time_ms || 0;
  }

  get totalCount() {
    return this.data.total_count || 0;
  }
}

/**
 * Request queue for handling rate limiting
 */
class RequestQueue {
  constructor(maxConcurrent = 5, delayMs = 100) {
    this.maxConcurrent = maxConcurrent;
    this.delayMs = delayMs;
    this.queue = [];
    this.active = 0;
  }

  async add(requestFn) {
    return new Promise((resolve, reject) => {
      this.queue.push({ requestFn, resolve, reject });
      this.process();
    });
  }

  async process() {
    if (this.active >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    this.active++;
    const { requestFn, resolve, reject } = this.queue.shift();

    try {
      const result = await requestFn();
      resolve(result);
    } catch (error) {
      reject(error);
    } finally {
      this.active--;
      
      // Add delay between requests
      setTimeout(() => {
        this.process();
      }, this.delayMs);
    }
  }
}

// Export classes
window.APIClient = APIClient;
window.APIError = APIError;
window.APIResponse = APIResponse;
window.RequestQueue = RequestQueue;

// Create global API client instance
window.api = new APIClient();

console.log('[API] API Client initialized');

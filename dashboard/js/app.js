/**
 * GoodBooks Recommender Dashboard - Main Application
 * Main application logic and initialization
 */

/**
 * Main Dashboard Application
 */
class DashboardApp {
  constructor() {
    this.currentPage = 'home';
    this.components = new Map();
    this.isInitialized = false;
    this.sessionId = null;
    
    // Bind methods
    this.handleNavigation = this.handleNavigation.bind(this);
    this.handleSearch = this.handleSearch.bind(this);
    this.handleRecommendation = this.handleRecommendation.bind(this);
  }

  /**
   * Initialize the application
   */
  async initialize() {
    if (this.isInitialized) return;
    
    logger.info('Initializing dashboard application...');
    performance.start('app-init');

    try {
      // Check API connection
      await this.checkAPIConnection();
      
      // Initialize session
      await this.initializeSession();
      
      // Setup navigation
      this.setupNavigation();
      
      // Load initial page
      await this.loadPage(this.getCurrentPageFromURL());
      
      // Setup global event listeners
      this.setupEventListeners();
      
      this.isInitialized = true;
      const initTime = performance.end('app-init');
      
      logger.info(`Dashboard initialized successfully in ${initTime.toFixed(2)}ms`);
      Alert.show('Dashboard ready', 'success', 3000);
      
    } catch (error) {
      logger.error('Failed to initialize dashboard:', error);
      Alert.show('Failed to initialize dashboard', 'error');
      this.renderErrorPage(error);
    }
  }

  /**
   * Check API connection
   */
  async checkAPIConnection() {
    try {
      const health = await api.getHealth();
      logger.info('API connection established', { status: health.status });
      return health;
    } catch (error) {
      logger.error('API connection failed:', error);
      throw new Error('Unable to connect to the API server. Please check if the server is running.');
    }
  }

  /**
   * Initialize user session
   */
  async initializeSession() {
    try {
      // Check for existing session
      const savedSessionId = storage.get('sessionId');
      
      if (savedSessionId) {
        try {
          const session = await api.getSession(savedSessionId);
          this.sessionId = savedSessionId;
          logger.info('Existing session restored', { sessionId: this.sessionId });
          return;
        } catch (error) {
          logger.warn('Failed to restore session, creating new one');
        }
      }
      
      // Create new session
      const response = await api.createSession(Date.now()); // Use timestamp as user ID
      this.sessionId = response.session_id;
      storage.set('sessionId', this.sessionId);
      
      logger.info('New session created', { sessionId: this.sessionId });
      
    } catch (error) {
      logger.warn('Session initialization failed:', error);
      // Continue without session
    }
  }

  /**
   * Setup navigation
   */
  setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', this.handleNavigation);
    });

    // Mobile menu toggle
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (mobileToggle && navMenu) {
      mobileToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
      });
    }

    // Handle browser back/forward
    window.addEventListener('popstate', () => {
      this.loadPage(this.getCurrentPageFromURL());
    });
  }

  /**
   * Setup global event listeners
   */
  setupEventListeners() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      logger.error('Unhandled promise rejection:', event.reason);
      Alert.show('An unexpected error occurred', 'error');
    });

    // Handle general errors
    window.addEventListener('error', (event) => {
      logger.error('JavaScript error:', event.error);
    });

    // Handle online/offline status
    window.addEventListener('online', () => {
      Alert.show('Connection restored', 'success');
    });

    window.addEventListener('offline', () => {
      Alert.show('Connection lost', 'warning');
    });
  }

  /**
   * Get current page from URL
   */
  getCurrentPageFromURL() {
    const path = window.location.pathname;
    return path.split('/').pop() || 'home';
  }

  /**
   * Handle navigation
   */
  handleNavigation(event) {
    event.preventDefault();
    const link = event.target.closest('.nav-link');
    const page = link.dataset.page || link.href.split('/').pop();
    
    this.loadPage(page);
    
    // Update URL
    const url = page === 'home' ? '/' : `/${page}`;
    window.history.pushState({ page }, '', url);
  }

  /**
   * Load and render a page
   */
  async loadPage(pageName) {
    if (!pageName || pageName === 'index.html') {
      pageName = 'home';
    }

    logger.info(`Loading page: ${pageName}`);
    performance.start(`page-${pageName}`);

    try {
      // Clear existing components
      this.clearComponents();
      
      // Update active navigation
      this.updateActiveNavigation(pageName);
      
      // Load page content
      switch (pageName) {
        case 'home':
          await this.loadHomePage();
          break;
        case 'search':
          await this.loadSearchPage();
          break;
        case 'analytics':
          await this.loadAnalyticsPage();
          break;
        case 'recommendations':
          await this.loadRecommendationsPage();
          break;
        default:
          this.loadNotFoundPage();
      }
      
      this.currentPage = pageName;
      const loadTime = performance.end(`page-${pageName}`);
      logger.info(`Page '${pageName}' loaded in ${loadTime.toFixed(2)}ms`);
      
    } catch (error) {
      logger.error(`Failed to load page '${pageName}':`, error);
      Alert.show(`Failed to load page: ${error.message}`, 'error');
    }
  }

  /**
   * Load home page
   */
  async loadHomePage() {
    const mainContent = document.querySelector('.main-content');
    
    mainContent.innerHTML = `
      <div class="container">
        <div class="page-header">
          <h1 class="page-title">📚 Dashboard</h1>
          <p class="page-subtitle">Welcome to the GoodBooks Recommender System</p>
        </div>
        
        <div class="dashboard-grid">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">System Health</h3>
            </div>
            <div id="health-monitor"></div>
          </div>
          
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Quick Actions</h3>
            </div>
            <div class="card-content">
              <div class="flex flex-col gap-4">
                <button class="btn btn-primary" data-action="get-recommendations">
                  🎯 Get Recommendations
                </button>
                <button class="btn btn-secondary" data-action="search-books">
                  🔍 Search Books
                </button>
                <button class="btn btn-outline" data-action="view-analytics">
                  📊 View Analytics
                </button>
              </div>
            </div>
          </div>
          
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Recent Activity</h3>
            </div>
            <div class="card-content">
              <div class="chart-container">
                <canvas id="activity-chart"></canvas>
              </div>
            </div>
          </div>
          
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Featured Books</h3>
            </div>
            <div id="featured-books"></div>
          </div>
        </div>
      </div>
    `;

    // Initialize components
    await this.initializeHomeComponents();
  }

  /**
   * Initialize home page components
   */
  async initializeHomeComponents() {
    // Health monitor
    const healthContainer = document.getElementById('health-monitor');
    if (healthContainer) {
      const healthMonitor = new HealthMonitor(healthContainer);
      await healthMonitor.initialize();
      this.components.set('health-monitor', healthMonitor);
    }

    // Activity chart
    const chartManager = new ChartManager();
    const sampleData = chartManager.generateSampleData();
    chartManager.createRealTimeChart('activity-chart');
    this.components.set('chart-manager', chartManager);

    // Featured books
    await this.loadFeaturedBooks();

    // Quick actions
    this.setupQuickActions();
  }

  /**
   * Load featured books
   */
  async loadFeaturedBooks() {
    const container = document.getElementById('featured-books');
    if (!container) return;

    try {
      // Get sample recommendations to show as featured books
      const recommendations = await api.getRecommendations({
        n_recommendations: 3,
        user_id: 1 // Sample user
      });

      if (recommendations.recommendations && recommendations.recommendations.length > 0) {
        container.innerHTML = '';
        
        recommendations.recommendations.forEach(book => {
          const bookDiv = document.createElement('div');
          new BookCard(bookDiv, book, { showActions: false, showGenres: false });
          container.appendChild(bookDiv);
        });
      } else {
        container.innerHTML = '<p class="text-muted">No featured books available</p>';
      }
      
    } catch (error) {
      logger.error('Failed to load featured books:', error);
      container.innerHTML = '<p class="text-muted">Unable to load featured books</p>';
    }
  }

  /**
   * Setup quick actions
   */
  setupQuickActions() {
    document.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      
      switch (action) {
        case 'get-recommendations':
          this.loadPage('recommendations');
          break;
        case 'search-books':
          this.loadPage('search');
          break;
        case 'view-analytics':
          this.loadPage('analytics');
          break;
      }
    });
  }

  /**
   * Load search page
   */
  async loadSearchPage() {
    const mainContent = document.querySelector('.main-content');
    
    mainContent.innerHTML = `
      <div class="container">
        <div class="page-header">
          <h1 class="page-title">🔍 Book Search</h1>
          <p class="page-subtitle">Search for books using semantic search</p>
        </div>
        
        <div id="search-component"></div>
        <div id="search-results"></div>
      </div>
    `;

    // Initialize search component
    const searchContainer = document.getElementById('search-component');
    const resultsContainer = document.getElementById('search-results');
    
    const searchComponent = new SearchComponent(searchContainer);
    const resultsComponent = new ResultsComponent(resultsContainer);
    
    // Handle search events
    searchComponent.on('search', async (data) => {
      await this.performSearch(data, searchComponent, resultsComponent);
    });

    searchComponent.on('clear', () => {
      resultsComponent.setResults([]);
    });

    // Handle result actions
    resultsComponent.on('action', (data) => {
      this.handleBookAction(data.action, data.result);
    });

    this.components.set('search', searchComponent);
    this.components.set('results', resultsComponent);
  }

  /**
   * Perform search
   */
  async performSearch(data, searchComponent, resultsComponent) {
    const { query, filters } = data;
    
    searchComponent.setLoading(true);
    performance.start('search');
    
    try {
      const response = await api.semanticSearch(query, {
        k: parseInt(filters.k) || 10,
        score_threshold: parseFloat(filters.threshold) || 0.0,
        include_explanation: filters.explanation || false
      });

      const searchTime = performance.end('search');
      
      resultsComponent.setResults(
        response.results || [],
        query,
        response.processing_time_ms || searchTime
      );
      
      logger.info(`Search completed: ${response.results?.length || 0} results in ${searchTime.toFixed(2)}ms`);
      
    } catch (error) {
      logger.error('Search failed:', error);
      Alert.show(`Search failed: ${error.message}`, 'error');
      resultsComponent.setResults([], query, 0);
    } finally {
      searchComponent.setLoading(false);
    }
  }

  /**
   * Handle book actions
   */
  handleBookAction(action, book) {
    switch (action) {
      case 'recommend':
        this.getBookRecommendations(book);
        break;
      case 'explain':
        this.explainBook(book);
        break;
      case 'details':
        this.showBookDetails(book);
        break;
    }
  }

  /**
   * Get recommendations for a book
   */
  async getBookRecommendations(book) {
    try {
      const response = await api.getRecommendations({
        book_title: book.title,
        n_recommendations: 5,
        include_explanation: true
      });

      this.showRecommendationsModal(response, book.title);
      
    } catch (error) {
      logger.error('Failed to get recommendations:', error);
      Alert.show('Failed to get recommendations', 'error');
    }
  }

  /**
   * Show recommendations in modal
   */
  showRecommendationsModal(recommendations, title) {
    const content = `
      <div class="recommendation-results">
        <p class="text-muted mb-4">Recommendations based on "${title}"</p>
        
        ${recommendations.recommendations.map(book => `
          <div class="result-item">
            <div class="result-content">
              <h4 class="result-title">${Utils.escapeHtml(book.title)}</h4>
              <p class="result-author">${Utils.escapeHtml(book.authors)}</p>
              <div class="result-meta">
                <span>⭐ ${book.average_rating.toFixed(2)}</span>
                <span class="result-similarity">${(book.hybrid_score * 100).toFixed(1)}% match</span>
              </div>
              ${book.explanation ? `
                <p class="explanation-text">${Utils.escapeHtml(book.explanation)}</p>
              ` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;

    const modal = new Modal({ title: 'Book Recommendations' });
    modal.show(content);
  }

  /**
   * Explain book recommendation
   */
  async explainBook(book) {
    try {
      const response = await api.explainRecommendation(book.book_id || 1);
      this.showExplanationModal(response, book);
      
    } catch (error) {
      logger.error('Failed to get explanation:', error);
      Alert.show('Failed to get explanation', 'error');
    }
  }

  /**
   * Show explanation in modal
   */
  showExplanationModal(explanation, book) {
    const content = `
      <div class="explanation-content">
        <div class="book-info mb-4">
          <h4>${Utils.escapeHtml(book.title)}</h4>
          <p class="text-muted">${Utils.escapeHtml(book.authors)}</p>
        </div>
        
        <div class="explanation-text">
          ${explanation.explanation.text || 'No explanation available'}
        </div>
        
        ${explanation.explanation.confidence_scores ? `
          <div class="confidence-scores mt-4">
            <h5>Confidence Scores</h5>
            ${Object.entries(explanation.explanation.confidence_scores).map(([key, value]) => `
              <div class="score-item">
                <span>${Utils.camelToTitle(key)}</span>
                <span class="score-value">${(value * 100).toFixed(1)}%</span>
              </div>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `;

    const modal = new Modal({ title: 'Recommendation Explanation' });
    modal.show(content);
  }

  /**
   * Show book details
   */
  showBookDetails(book) {
    const content = `
      <div class="book-details">
        <div class="book-header">
          <div class="book-cover-placeholder large">📚</div>
          <div class="book-info">
            <h3>${Utils.escapeHtml(book.title)}</h3>
            <p class="author">${Utils.escapeHtml(book.authors)}</p>
            <div class="rating">
              <span>⭐ ${book.average_rating?.toFixed(2) || 'N/A'}</span>
              ${book.ratings_count ? `<span>(${Utils.formatNumber(book.ratings_count)} ratings)</span>` : ''}
            </div>
          </div>
        </div>
        
        ${book.publication_date ? `<p><strong>Published:</strong> ${book.publication_date}</p>` : ''}
        ${book.num_pages ? `<p><strong>Pages:</strong> ${book.num_pages}</p>` : ''}
        ${book.publisher ? `<p><strong>Publisher:</strong> ${book.publisher}</p>` : ''}
        ${book.genres ? `
          <div class="genres">
            <strong>Genres:</strong>
            <div class="genre-tags">
              ${book.genres.split('|').map(genre => 
                `<span class="genre-tag">${genre}</span>`
              ).join('')}
            </div>
          </div>
        ` : ''}
      </div>
    `;

    const modal = new Modal({ title: 'Book Details' });
    modal.show(content);
  }

  /**
   * Load recommendations page
   */
  async loadRecommendationsPage() {
    const mainContent = document.querySelector('.main-content');
    
    mainContent.innerHTML = `
      <div class="container">
        <div class="page-header">
          <h1 class="page-title">🎯 Recommendations</h1>
          <p class="page-subtitle">Get personalized book recommendations</p>
        </div>
        
        <div class="recommendation-form">
          <h3>Get Recommendations</h3>
          
          <div class="form-row">
            <div class="form-col">
              <div class="radio-group">
                <label class="radio-option">
                  <input type="radio" name="rec-type" value="user" class="radio-input">
                  User-based (Collaborative)
                </label>
                <label class="radio-option">
                  <input type="radio" name="rec-type" value="content" class="radio-input" checked>
                  Content-based
                </label>
              </div>
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-col">
              <label class="form-label">User ID (for collaborative)</label>
              <input type="number" class="form-input" id="user-id" placeholder="Enter user ID" min="1">
            </div>
            <div class="form-col">
              <label class="form-label">Book Title (for content-based)</label>
              <input type="text" class="form-input" id="book-title" placeholder="Enter book title">
            </div>
          </div>
          
          <div class="form-row">
            <div class="form-col">
              <label class="form-label">Number of recommendations</label>
              <select class="form-select" id="num-recommendations">
                <option value="5" selected>5 recommendations</option>
                <option value="10">10 recommendations</option>
                <option value="15">15 recommendations</option>
                <option value="20">20 recommendations</option>
              </select>
            </div>
            <div class="form-col">
              <div class="checkbox-group">
                <label class="checkbox-option">
                  <input type="checkbox" class="checkbox-input" id="include-explanation">
                  Include explanations
                </label>
              </div>
            </div>
          </div>
          
          <div class="form-actions">
            <button class="btn btn-primary" id="get-recommendations">
              🎯 Get Recommendations
            </button>
            <button class="btn btn-ghost" id="clear-form">
              🗑️ Clear
            </button>
          </div>
        </div>
        
        <div id="recommendation-results"></div>
      </div>
    `;

    this.setupRecommendationForm();
  }

  /**
   * Setup recommendation form
   */
  setupRecommendationForm() {
    const getBtn = document.getElementById('get-recommendations');
    const clearBtn = document.getElementById('clear-form');
    const resultsContainer = document.getElementById('recommendation-results');

    getBtn.addEventListener('click', async () => {
      await this.handleRecommendationRequest(resultsContainer);
    });

    clearBtn.addEventListener('click', () => {
      this.clearRecommendationForm();
      resultsContainer.innerHTML = '';
    });

    // Form validation
    const radioButtons = document.querySelectorAll('input[name="rec-type"]');
    radioButtons.forEach(radio => {
      radio.addEventListener('change', this.updateFormVisibility);
    });

    this.updateFormVisibility();
  }

  /**
   * Update form field visibility based on recommendation type
   */
  updateFormVisibility() {
    const recType = document.querySelector('input[name="rec-type"]:checked').value;
    const userIdField = document.getElementById('user-id');
    const bookTitleField = document.getElementById('book-title');

    if (recType === 'user') {
      userIdField.disabled = false;
      bookTitleField.disabled = true;
      bookTitleField.value = '';
    } else {
      userIdField.disabled = true;
      userIdField.value = '';
      bookTitleField.disabled = false;
    }
  }

  /**
   * Handle recommendation request
   */
  async handleRecommendationRequest(resultsContainer) {
    const recType = document.querySelector('input[name="rec-type"]:checked').value;
    const userId = parseInt(document.getElementById('user-id').value);
    const bookTitle = document.getElementById('book-title').value.trim();
    const numRecs = parseInt(document.getElementById('num-recommendations').value);
    const includeExplanation = document.getElementById('include-explanation').checked;

    // Validation
    if (recType === 'user' && (!userId || userId <= 0)) {
      Alert.show('Please enter a valid user ID', 'warning');
      return;
    }

    if (recType === 'content' && !bookTitle) {
      Alert.show('Please enter a book title', 'warning');
      return;
    }

    const getBtn = document.getElementById('get-recommendations');
    getBtn.disabled = true;
    getBtn.textContent = '⏳ Getting recommendations...';

    try {
      const params = {
        n_recommendations: numRecs,
        include_explanation: includeExplanation
      };

      if (recType === 'user') {
        params.user_id = userId;
      } else {
        params.book_title = bookTitle;
      }

      const response = await api.getRecommendations(params);
      this.displayRecommendations(response, resultsContainer);

    } catch (error) {
      logger.error('Recommendation request failed:', error);
      Alert.show(`Failed to get recommendations: ${error.message}`, 'error');
    } finally {
      getBtn.disabled = false;
      getBtn.textContent = '🎯 Get Recommendations';
    }
  }

  /**
   * Display recommendations
   */
  displayRecommendations(response, container) {
    const { recommendations, total_count, processing_time_ms, cache_hit } = response;

    if (!recommendations || recommendations.length === 0) {
      container.innerHTML = `
        <div class="alert alert-info">
          <div class="alert-icon">ℹ️</div>
          <div class="alert-content">
            <div class="alert-message">No recommendations found</div>
          </div>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="recommendation-results">
        <div class="results-header">
          <h3>📋 Recommendations (${total_count} found)</h3>
          <div class="results-meta">
            <span>⏱️ ${processing_time_ms}ms</span>
            <span class="cache-indicator ${cache_hit ? 'cache-hit' : 'cache-miss'}">
              ${cache_hit ? '💾 Cached' : '🔄 Fresh'}
            </span>
          </div>
        </div>
        
        <div class="recommendations-grid">
          ${recommendations.map(book => `
            <div class="recommendation-card" data-book-id="${book.book_id || ''}">
              <div class="book-card">
                <div class="book-card-header">
                  <div class="book-cover-placeholder">📚</div>
                  <div class="book-info">
                    <h4 class="book-title">${Utils.escapeHtml(book.title)}</h4>
                    <p class="book-author">${Utils.escapeHtml(book.authors)}</p>
                    <div class="book-meta">
                      <div class="book-rating">
                        <span>⭐ ${book.average_rating.toFixed(2)}</span>
                        ${book.ratings_count ? `<span>(${Utils.formatNumber(book.ratings_count)})</span>` : ''}
                      </div>
                      <div class="book-score">
                        <span>Score: </span>
                        <span class="score-value">${(book.hybrid_score * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                ${book.explanation ? `
                  <div class="book-explanation">
                    <p class="explanation-text">${Utils.escapeHtml(book.explanation)}</p>
                  </div>
                ` : ''}
                
                <div class="book-actions">
                  <button class="btn btn-sm btn-outline" data-action="explain" data-book-id="${book.book_id || ''}">
                    💡 Explain
                  </button>
                  <button class="btn btn-sm btn-ghost" data-action="details" data-book-id="${book.book_id || ''}">
                    📖 Details
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Add event listeners for book actions
    container.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      const bookId = e.target.dataset.bookId;
      
      if (action && bookId) {
        const book = recommendations.find(b => b.book_id == bookId);
        if (book) {
          this.handleBookAction(action, book);
        }
      }
    });
  }

  /**
   * Clear recommendation form
   */
  clearRecommendationForm() {
    document.getElementById('user-id').value = '';
    document.getElementById('book-title').value = '';
    document.getElementById('num-recommendations').value = '5';
    document.getElementById('include-explanation').checked = false;
    document.querySelector('input[name="rec-type"][value="content"]').checked = true;
    this.updateFormVisibility();
  }

  /**
   * Load analytics page
   */
  async loadAnalyticsPage() {
    const mainContent = document.querySelector('.main-content');
    
    mainContent.innerHTML = `
      <div class="container">
        <div class="page-header">
          <h1 class="page-title">📊 Analytics</h1>
          <p class="page-subtitle">System performance and usage analytics</p>
        </div>
        
        <div id="analytics-dashboard"></div>
      </div>
    `;

    // Initialize analytics dashboard
    const container = document.getElementById('analytics-dashboard');
    const analyticsDashboard = new AnalyticsDashboard(container);
    await analyticsDashboard.initialize();
    
    this.components.set('analytics', analyticsDashboard);
  }

  /**
   * Load 404 page
   */
  loadNotFoundPage() {
    const mainContent = document.querySelector('.main-content');
    
    mainContent.innerHTML = `
      <div class="container">
        <div class="text-center">
          <h1 class="page-title">📄 Page Not Found</h1>
          <p class="page-subtitle">The page you're looking for doesn't exist.</p>
          <button class="btn btn-primary" onclick="app.loadPage('home')">
            🏠 Go Home
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Render error page
   */
  renderErrorPage(error) {
    const mainContent = document.querySelector('.main-content');
    
    mainContent.innerHTML = `
      <div class="container">
        <div class="text-center">
          <h1 class="page-title">❌ Error</h1>
          <p class="page-subtitle">Something went wrong</p>
          <div class="alert alert-error">
            <div class="alert-content">
              <div class="alert-message">${Utils.escapeHtml(error.message)}</div>
            </div>
          </div>
          <button class="btn btn-primary" onclick="window.location.reload()">
            🔄 Reload Page
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Update active navigation
   */
  updateActiveNavigation(pageName) {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.dataset.page === pageName || 
          (pageName === 'home' && link.dataset.page === undefined)) {
        link.classList.add('active');
      }
    });
  }

  /**
   * Clear all components
   */
  clearComponents() {
    this.components.forEach(component => {
      if (component.destroy) {
        component.destroy();
      }
    });
    this.components.clear();
  }

  /**
   * Destroy the application
   */
  destroy() {
    this.clearComponents();
    this.isInitialized = false;
    logger.info('Dashboard application destroyed');
  }
}

// Global application instance
let app;

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  try {
    app = new DashboardApp();
    await app.initialize();
    
    // Expose app globally for debugging
    window.app = app;
    
  } catch (error) {
    console.error('Failed to initialize application:', error);
    
    // Show basic error message
    document.body.innerHTML = `
      <div style="padding: 2rem; text-align: center;">
        <h1>⚠️ Application Error</h1>
        <p>Failed to initialize the dashboard application.</p>
        <p><strong>Error:</strong> ${error.message}</p>
        <button onclick="window.location.reload()" style="margin-top: 1rem; padding: 0.5rem 1rem;">
          🔄 Reload Page
        </button>
      </div>
    `;
  }
});

// Export DashboardApp
window.DashboardApp = DashboardApp;

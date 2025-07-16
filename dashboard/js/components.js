/**
 * GoodBooks Recommender Dashboard - UI Components
 * Reusable UI components for the dashboard
 */

/**
 * Base Component class
 */
class Component {
  constructor(container) {
    this.container = typeof container === 'string' 
      ? document.querySelector(container) 
      : container;
    this.state = {};
    this.listeners = new Map();
  }

  setState(newState) {
    this.state = { ...this.state, ...newState };
    this.render();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  render() {
    // Override in subclasses
  }

  destroy() {
    this.listeners.clear();
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}

/**
 * Book Card Component
 */
class BookCard extends Component {
  constructor(container, book, options = {}) {
    super(container);
    this.book = book;
    this.options = {
      showActions: true,
      showExplanation: false,
      showGenres: true,
      ...options
    };
    this.render();
  }

  render() {
    const { book, options } = this;
    const genres = this.parseGenres(book.genres || '');
    
    this.container.innerHTML = `
      <div class="book-card" data-book-id="${book.book_id || ''}">
        <div class="book-card-header">
          <div class="book-cover-placeholder">
            📚
          </div>
          <div class="book-info">
            <h3 class="book-title">${this.escapeHtml(book.title || 'Unknown Title')}</h3>
            <p class="book-author">${this.escapeHtml(book.authors || 'Unknown Author')}</p>
            <div class="book-meta">
              <div class="book-rating">
                <span class="star">⭐</span>
                <span>${(book.average_rating || 0).toFixed(2)}</span>
                ${book.ratings_count ? `<span class="text-muted">(${this.formatNumber(book.ratings_count)})</span>` : ''}
              </div>
              ${book.hybrid_score !== undefined ? `
                <div class="book-score">
                  <span>Score:</span>
                  <span class="score-value">${(book.hybrid_score * 100).toFixed(1)}%</span>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
        
        ${options.showGenres && genres.length > 0 ? `
          <div class="book-genres">
            ${genres.map(genre => `<span class="genre-tag">${genre}</span>`).join('')}
          </div>
        ` : ''}
        
        ${options.showExplanation && book.explanation ? `
          <div class="book-explanation">
            <p class="explanation-text">${this.escapeHtml(book.explanation)}</p>
          </div>
        ` : ''}
        
        ${options.showActions ? `
          <div class="book-actions">
            <button class="btn btn-sm btn-primary" data-action="recommend">
              🎯 Recommend
            </button>
            <button class="btn btn-sm btn-outline" data-action="explain">
              💡 Explain
            </button>
            <button class="btn btn-sm btn-ghost" data-action="details">
              📖 Details
            </button>
          </div>
        ` : ''}
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const card = this.container.querySelector('.book-card');
    
    card.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      if (action) {
        e.preventDefault();
        this.emit('action', { action, book: this.book });
      }
    });
  }

  parseGenres(genresString) {
    if (!genresString) return [];
    return genresString.split('|').slice(0, 3); // Limit to 3 genres
  }

  formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

/**
 * Search Component
 */
class SearchComponent extends Component {
  constructor(container, options = {}) {
    super(container);
    this.options = {
      placeholder: 'Search books...',
      showFilters: true,
      debounceMs: 300,
      ...options
    };
    this.debounceTimer = null;
    this.render();
  }

  render() {
    this.container.innerHTML = `
      <div class="search-container">
        <div class="form-group">
          <input 
            type="text" 
            class="search-input" 
            placeholder="${this.options.placeholder}"
            value="${this.state.query || ''}"
          >
          <span class="search-icon">🔍</span>
        </div>
        
        ${this.options.showFilters ? `
          <div class="filters-container">
            <div class="filters-grid">
              <div class="filter-group">
                <label class="filter-label">Results</label>
                <select class="filter-select" data-filter="k">
                  <option value="5">5 results</option>
                  <option value="10" selected>10 results</option>
                  <option value="20">20 results</option>
                </select>
              </div>
              
              <div class="filter-group">
                <label class="filter-label">Threshold</label>
                <select class="filter-select" data-filter="threshold">
                  <option value="0.0" selected>Any match</option>
                  <option value="0.3">Good match (30%)</option>
                  <option value="0.5">Strong match (50%)</option>
                  <option value="0.7">Excellent match (70%)</option>
                </select>
              </div>
              
              <div class="filter-group">
                <div class="checkbox-group">
                  <label class="checkbox-option">
                    <input type="checkbox" class="checkbox-input" data-filter="explanation">
                    Include explanations
                  </label>
                </div>
              </div>
            </div>
            
            <div class="filter-actions">
              <button class="btn btn-sm btn-primary" data-action="search">
                🔍 Search
              </button>
              <button class="btn btn-sm btn-ghost" data-action="clear">
                🗑️ Clear
              </button>
            </div>
          </div>
        ` : ''}
      </div>
    `;

    this.attachEventListeners();
  }

  attachEventListeners() {
    const input = this.container.querySelector('.search-input');
    const searchBtn = this.container.querySelector('[data-action="search"]');
    const clearBtn = this.container.querySelector('[data-action="clear"]');
    const filters = this.container.querySelectorAll('[data-filter]');

    input.addEventListener('input', (e) => {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.setState({ query: e.target.value });
        if (e.target.value.trim()) {
          this.performSearch();
        }
      }, this.options.debounceMs);
    });

    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.performSearch();
      }
    });

    if (searchBtn) {
      searchBtn.addEventListener('click', () => this.performSearch());
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearSearch());
    }

    filters.forEach(filter => {
      filter.addEventListener('change', () => {
        this.updateFilters();
      });
    });
  }

  updateFilters() {
    const filters = {};
    this.container.querySelectorAll('[data-filter]').forEach(element => {
      const key = element.dataset.filter;
      if (element.type === 'checkbox') {
        filters[key] = element.checked;
      } else {
        filters[key] = element.value;
      }
    });
    
    this.setState({ filters });
  }

  performSearch() {
    const query = this.state.query?.trim();
    if (!query) return;

    this.emit('search', {
      query,
      filters: this.state.filters || {}
    });
  }

  clearSearch() {
    this.container.querySelector('.search-input').value = '';
    this.setState({ query: '', results: null });
    this.emit('clear');
  }

  setLoading(loading) {
    const searchBtn = this.container.querySelector('[data-action="search"]');
    if (searchBtn) {
      searchBtn.disabled = loading;
      searchBtn.innerHTML = loading ? '⏳ Searching...' : '🔍 Search';
    }
  }
}

/**
 * Results Component
 */
class ResultsComponent extends Component {
  constructor(container, options = {}) {
    super(container);
    this.options = {
      itemsPerPage: 10,
      showPagination: true,
      ...options
    };
    this.currentPage = 1;
  }

  setResults(results, query = '', processingTime = 0) {
    this.setState({
      results,
      query,
      processingTime,
      totalPages: Math.ceil(results.length / this.options.itemsPerPage)
    });
  }

  render() {
    const { results, query, processingTime, totalPages } = this.state;
    
    if (!results) {
      this.container.innerHTML = '';
      return;
    }

    if (results.length === 0) {
      this.container.innerHTML = `
        <div class="search-results">
          <div class="text-center">
            <p class="text-muted">No results found for "${query}"</p>
          </div>
        </div>
      `;
      return;
    }

    const startIdx = (this.currentPage - 1) * this.options.itemsPerPage;
    const endIdx = startIdx + this.options.itemsPerPage;
    const pageResults = results.slice(startIdx, endIdx);

    this.container.innerHTML = `
      <div class="search-results">
        <div class="search-results-header">
          <div class="results-count">
            ${results.length} results found
            ${query ? ` for "${query}"` : ''}
          </div>
          <div class="results-time">
            ${processingTime}ms
          </div>
        </div>
        
        <div class="results-grid">
          ${pageResults.map(result => `
            <div class="result-item" data-book-id="${result.book_id || ''}">
              <div class="result-cover-placeholder">📚</div>
              <div class="result-content">
                <h4 class="result-title">${this.escapeHtml(result.title || 'Unknown Title')}</h4>
                <p class="result-author">${this.escapeHtml(result.authors || 'Unknown Author')}</p>
                <div class="result-meta">
                  ${result.average_rating ? `<span>⭐ ${result.average_rating.toFixed(2)}</span>` : ''}
                  ${result.similarity_score !== undefined ? `
                    <span class="result-similarity">
                      ${(result.similarity_score * 100).toFixed(1)}% match
                    </span>
                  ` : ''}
                  ${result.publication_date ? `<span>📅 ${result.publication_date}</span>` : ''}
                </div>
                ${result.explanation ? `
                  <p class="explanation-text">${this.escapeHtml(result.explanation)}</p>
                ` : ''}
                <div class="result-actions">
                  <button class="btn btn-sm btn-primary" data-action="recommend">
                    🎯 Recommend
                  </button>
                  <button class="btn btn-sm btn-outline" data-action="explain">
                    💡 Explain
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
        
        ${this.options.showPagination && totalPages > 1 ? this.renderPagination() : ''}
      </div>
    `;

    this.attachEventListeners();
  }

  renderPagination() {
    const { totalPages } = this.state;
    const maxVisiblePages = 5;
    const startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    let paginationHTML = `
      <div class="pagination">
        <button 
          class="pagination-btn" 
          data-page="prev" 
          ${this.currentPage === 1 ? 'disabled' : ''}
        >
          ← Previous
        </button>
    `;

    for (let i = startPage; i <= endPage; i++) {
      paginationHTML += `
        <button 
          class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
          data-page="${i}"
        >
          ${i}
        </button>
      `;
    }

    paginationHTML += `
        <button 
          class="pagination-btn" 
          data-page="next" 
          ${this.currentPage === totalPages ? 'disabled' : ''}
        >
          Next →
        </button>
        
        <div class="pagination-info">
          Page ${this.currentPage} of ${totalPages}
        </div>
      </div>
    `;

    return paginationHTML;
  }

  attachEventListeners() {
    this.container.addEventListener('click', (e) => {
      const action = e.target.dataset.action;
      const page = e.target.dataset.page;
      
      if (action) {
        const resultItem = e.target.closest('.result-item');
        const bookId = resultItem?.dataset.bookId;
        const result = this.state.results.find(r => r.book_id == bookId);
        
        this.emit('action', { action, result });
      }
      
      if (page) {
        this.handlePageChange(page);
      }
    });
  }

  handlePageChange(page) {
    const { totalPages } = this.state;
    
    if (page === 'prev' && this.currentPage > 1) {
      this.currentPage--;
    } else if (page === 'next' && this.currentPage < totalPages) {
      this.currentPage++;
    } else if (!isNaN(page)) {
      this.currentPage = parseInt(page);
    }
    
    this.render();
    this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

/**
 * Modal Component
 */
class Modal extends Component {
  constructor(options = {}) {
    super(null);
    this.options = {
      title: 'Modal',
      size: 'medium',
      closeOnBackdrop: true,
      showCloseButton: true,
      ...options
    };
    this.overlay = null;
  }

  show(content, title) {
    if (title) this.options.title = title;
    
    this.overlay = document.createElement('div');
    this.overlay.className = 'modal-overlay';
    this.overlay.innerHTML = `
      <div class="modal ${this.options.size}">
        <div class="modal-header">
          <h3 class="modal-title">${this.escapeHtml(this.options.title)}</h3>
          ${this.options.showCloseButton ? `
            <button class="modal-close" data-action="close">×</button>
          ` : ''}
        </div>
        <div class="modal-content">
          ${content}
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" data-action="close">Close</button>
        </div>
      </div>
    `;

    document.body.appendChild(this.overlay);
    this.attachEventListeners();
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    this.emit('show');
  }

  hide() {
    if (this.overlay) {
      this.overlay.remove();
      this.overlay = null;
    }
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    this.emit('hide');
  }

  attachEventListeners() {
    if (!this.overlay) return;

    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay && this.options.closeOnBackdrop) {
        this.hide();
      }
      
      if (e.target.dataset.action === 'close') {
        this.hide();
      }
    });

    // Close on Escape key
    const handleKeydown = (e) => {
      if (e.key === 'Escape') {
        this.hide();
        document.removeEventListener('keydown', handleKeydown);
      }
    };
    
    document.addEventListener('keydown', handleKeydown);
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

/**
 * Alert Component
 */
class Alert {
  static show(message, type = 'info', duration = 5000) {
    const alertContainer = this.getOrCreateContainer();
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} fade-in`;
    
    const icons = {
      success: '✅',
      warning: '⚠️',
      error: '❌',
      info: 'ℹ️'
    };

    alertElement.innerHTML = `
      <div class="alert-icon">${icons[type] || icons.info}</div>
      <div class="alert-content">
        <div class="alert-message">${this.escapeHtml(message)}</div>
      </div>
    `;

    alertContainer.appendChild(alertElement);

    // Auto remove
    if (duration > 0) {
      setTimeout(() => {
        alertElement.style.opacity = '0';
        setTimeout(() => {
          alertElement.remove();
        }, 300);
      }, duration);
    }

    return alertElement;
  }

  static getOrCreateContainer() {
    let container = document.querySelector('.alert-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'alert-container';
      container.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 2000;
        max-width: 400px;
        pointer-events: none;
      `;
      document.body.appendChild(container);
    }
    return container;
  }

  static escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Export components
window.Component = Component;
window.BookCard = BookCard;
window.SearchComponent = SearchComponent;
window.ResultsComponent = ResultsComponent;
window.Modal = Modal;
window.Alert = Alert;

console.log('[Components] UI Components initialized');

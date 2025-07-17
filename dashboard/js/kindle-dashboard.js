/**
 * 📖 Kindle Paperwhite Dashboard
 * Main implementation of the e-ink inspired book recommendation dashboard
 */

class KindleDashboard {
  constructor() {
    this.container = null;
    this.themeManager = null;
    this.brightnessController = null;
    this.bookGrid = null;
    this.isInitialized = false;
    
    // Components
    this.header = null;
    this.sidebar = null;
    this.mainContent = null;
    this.footer = null;
    
    // State
    this.currentSection = 'library';
    this.books = [];
    this.recommendations = [];
    this.isLoading = false;
    
    // Settings
    this.settings = {
      autoTheme: false,
      autoBrightness: false,
      fontSize: 'medium',
      lineSpacing: 'normal',
      margins: 'medium'
    };
  }

  /**
   * Initialize the dashboard
   * @param {HTMLElement|string} container - Container element or selector
   */
  async init(container) {
    try {
      this.container = typeof container === 'string' 
        ? document.querySelector(container) 
        : container;

      if (!this.container) {
        throw new Error('Dashboard container not found');
      }

      // Initialize managers
      this.themeManager = new ThemeManager();
      this.brightnessController = new BrightnessController();

      // Load settings
      this.loadSettings();

      // Create layout
      this.createLayout();

      // Initialize components
      this.initializeComponents();

      // Load initial data
      await this.loadInitialData();

      // Set up event listeners
      this.setupEventListeners();

      this.isInitialized = true;
      
      // Dispatch ready event
      this.dispatchEvent('dashboard:ready');
      
      console.log('Kindle Dashboard initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Kindle Dashboard:', error);
      this.handleError(error);
    }
  }

  /**
   * Create main layout structure
   */
  createLayout() {
    this.container.innerHTML = '';
    this.container.className = 'kindle-dashboard';

    // Add skip link for accessibility
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-link';
    skipLink.textContent = 'Skip to main content';
    this.container.appendChild(skipLink);

    // Create header
    this.header = this.createHeader();
    this.container.appendChild(this.header);

    // Create main layout
    const mainLayout = document.createElement('div');
    mainLayout.className = 'dashboard-layout';

    // Create sidebar
    this.sidebar = this.createSidebar();
    mainLayout.appendChild(this.sidebar);

    // Create main content
    this.mainContent = this.createMainContent();
    mainLayout.appendChild(this.mainContent);

    this.container.appendChild(mainLayout);

    // Create footer
    this.footer = this.createFooter();
    this.container.appendChild(this.footer);
  }

  /**
   * Create header component
   */
  createHeader() {
    const header = document.createElement('header');
    header.className = 'dashboard-header';
    header.setAttribute('role', 'banner');

    // Logo/Title section
    const titleSection = document.createElement('div');
    titleSection.className = 'header-title';
    
    const logo = document.createElement('h1');
    logo.className = 'dashboard-logo';
    logo.innerHTML = '📚 <span>GoodBooks</span>';
    titleSection.appendChild(logo);

    // Search section
    const searchSection = document.createElement('div');
    searchSection.className = 'header-search';
    searchSection.appendChild(this.createSearchBar());

    // Controls section
    const controlsSection = document.createElement('div');
    controlsSection.className = 'header-controls';
    
    // Brightness control
    this.brightnessController.createControl(controlsSection, {
      size: 'sm',
      showPercentage: true,
      showIcons: true
    });

    // Theme toggle
    this.themeManager.createToggle(controlsSection, {
      variant: 'compact',
      size: 'sm',
      showLabels: false
    });

    // Settings button
    const settingsBtn = document.createElement('button');
    settingsBtn.className = 'header-settings-btn';
    settingsBtn.innerHTML = '⚙️';
    settingsBtn.setAttribute('aria-label', 'Open settings');
    settingsBtn.addEventListener('click', () => this.openSettings());
    controlsSection.appendChild(settingsBtn);

    header.appendChild(titleSection);
    header.appendChild(searchSection);
    header.appendChild(controlsSection);

    return header;
  }

  /**
   * Create search bar
   */
  createSearchBar() {
    const searchContainer = document.createElement('div');
    searchContainer.className = 'search-container';

    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'search-input';
    searchInput.placeholder = 'Search books, authors, genres...';
    searchInput.setAttribute('aria-label', 'Search books');

    const searchBtn = document.createElement('button');
    searchBtn.className = 'search-btn';
    searchBtn.innerHTML = '🔍';
    searchBtn.setAttribute('aria-label', 'Search');

    // Search functionality
    const performSearch = () => {
      const query = searchInput.value.trim();
      if (query) {
        this.searchBooks(query);
      }
    };

    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        performSearch();
      }
    });

    searchBtn.addEventListener('click', performSearch);

    searchContainer.appendChild(searchInput);
    searchContainer.appendChild(searchBtn);

    return searchContainer;
  }

  /**
   * Create sidebar navigation
   */
  createSidebar() {
    const sidebar = document.createElement('nav');
    sidebar.className = 'dashboard-sidebar';
    sidebar.setAttribute('role', 'navigation');
    sidebar.setAttribute('aria-label', 'Dashboard navigation');

    const nav = document.createElement('ul');
    nav.className = 'sidebar-nav';

    const navItems = [
      { id: 'library', label: 'My Library', icon: '📚' },
      { id: 'recommendations', label: 'Recommendations', icon: '🎯' },
      { id: 'reading', label: 'Currently Reading', icon: '📖' },
      { id: 'wishlist', label: 'Wishlist', icon: '⭐' },
      { id: 'analytics', label: 'Reading Stats', icon: '📊' }
    ];

    navItems.forEach(item => {
      const li = document.createElement('li');
      const link = document.createElement('button');
      link.className = 'sidebar-link';
      link.setAttribute('data-section', item.id);
      link.innerHTML = `<span class="nav-icon">${item.icon}</span><span class="nav-label">${item.label}</span>`;
      link.setAttribute('aria-label', item.label);

      if (item.id === this.currentSection) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      }

      link.addEventListener('click', () => this.navigateToSection(item.id));

      li.appendChild(link);
      nav.appendChild(li);
    });

    sidebar.appendChild(nav);

    // User profile section
    const userSection = document.createElement('div');
    userSection.className = 'sidebar-user';
    userSection.innerHTML = `
      <div class="user-avatar">👤</div>
      <div class="user-info">
        <div class="user-name">Book Lover</div>
        <div class="user-stats">42 books read</div>
      </div>
    `;
    sidebar.appendChild(userSection);

    return sidebar;
  }

  /**
   * Create main content area
   */
  createMainContent() {
    const main = document.createElement('main');
    main.className = 'dashboard-main';
    main.setAttribute('id', 'main-content');
    main.setAttribute('role', 'main');

    // Section header
    const sectionHeader = document.createElement('div');
    sectionHeader.className = 'section-header';
    
    const sectionTitle = document.createElement('h2');
    sectionTitle.className = 'section-title';
    sectionTitle.textContent = 'My Library';
    
    const sectionActions = document.createElement('div');
    sectionActions.className = 'section-actions';
    
    sectionHeader.appendChild(sectionTitle);
    sectionHeader.appendChild(sectionActions);
    main.appendChild(sectionHeader);

    // Content area
    const contentArea = document.createElement('div');
    contentArea.className = 'content-area';
    main.appendChild(contentArea);

    return main;
  }

  /**
   * Create footer
   */
  createFooter() {
    const footer = document.createElement('footer');
    footer.className = 'dashboard-footer';
    footer.setAttribute('role', 'contentinfo');

    footer.innerHTML = `
      <div class="footer-content">
        <div class="footer-section">
          <span class="footer-title">GoodBooks Dashboard</span>
          <span class="footer-subtitle">Your personal reading companion</span>
        </div>
        <div class="footer-section">
          <span class="footer-stats">Last sync: Just now</span>
        </div>
      </div>
    `;

    return footer;
  }

  /**
   * Initialize components
   */
  initializeComponents() {
    // Initialize book grid
    this.bookGrid = new BookGrid();
    const contentArea = this.mainContent?.querySelector('.content-area');
    if (contentArea) {
      this.bookGrid.create(contentArea, {
        variant: this.currentSection,
        onAction: (action, book) => this.handleBookAction(action, book)
      });
    }

    // Set up brightness and theme callbacks
    this.brightnessController.onChange = (value) => {
      this.dispatchEvent('brightness:change', { value });
    };

    this.themeManager.addObserver((theme, effectiveTheme) => {
      this.dispatchEvent('theme:change', { theme, effectiveTheme });
    });
  }

  /**
   * Load initial data
   */
  async loadInitialData() {
    this.setLoading(true);

    try {
      // Load library books
      this.books = await this.fetchBooks();
      
      // Load recommendations
      this.recommendations = await this.fetchRecommendations();
      
      // Display current section
      this.displaySection(this.currentSection);
      
    } catch (error) {
      console.error('Failed to load initial data:', error);
      this.showErrorMessage('Failed to load books. Please try again.');
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Fetch books from API
   */
  async fetchBooks() {
    // Mock data for now - replace with actual API call
    return [
      {
        id: 1,
        title: "The Midnight Library",
        author: "Matt Haig",
        coverUrl: "https://images-na.ssl-images-amazon.com/images/I/71h2TkLYJcL.jpg",
        rating: 4.2,
        progress: 45,
        genres: ["Fiction", "Philosophy", "Contemporary"]
      },
      {
        id: 2,
        title: "Atomic Habits",
        author: "James Clear",
        coverUrl: "https://images-na.ssl-images-amazon.com/images/I/81wgcld4wxL.jpg",
        rating: 4.6,
        progress: 78,
        genres: ["Self-Help", "Psychology", "Business"]
      },
      {
        id: 3,
        title: "Dune",
        author: "Frank Herbert",
        coverUrl: "https://images-na.ssl-images-amazon.com/images/I/81FTfSqyUsL.jpg",
        rating: 4.3,
        progress: 0,
        genres: ["Science Fiction", "Adventure", "Classic"]
      }
    ];
  }

  /**
   * Fetch recommendations from API
   */
  async fetchRecommendations() {
    // Mock data for now - replace with actual API call
    return [
      {
        id: 4,
        title: "Project Hail Mary",
        author: "Andy Weir",
        coverUrl: "https://images-na.ssl-images-amazon.com/images/I/81fHfmQ0xUL.jpg",
        rating: 4.5,
        matchScore: 95,
        genres: ["Science Fiction", "Thriller", "Space"]
      },
      {
        id: 5,
        title: "The Seven Husbands of Evelyn Hugo",
        author: "Taylor Jenkins Reid",
        coverUrl: "https://images-na.ssl-images-amazon.com/images/I/81FTB7manzL.jpg",
        rating: 4.4,
        matchScore: 87,
        genres: ["Fiction", "Romance", "Historical"]
      }
    ];
  }

  /**
   * Navigate to a section
   * @param {string} sectionId
   */
  navigateToSection(sectionId) {
    if (this.currentSection === sectionId) return;

    // Update active nav item
    const navLinks = this.sidebar?.querySelectorAll('.sidebar-link');
    navLinks?.forEach(link => {
      const isActive = link.getAttribute('data-section') === sectionId;
      link.classList.toggle('active', isActive);
      link.setAttribute('aria-current', isActive ? 'page' : 'false');
    });

    this.currentSection = sectionId;
    this.displaySection(sectionId);
    
    this.dispatchEvent('navigation:change', { section: sectionId });
  }

  /**
   * Display section content
   * @param {string} sectionId
   */
  displaySection(sectionId) {
    const sectionTitle = this.mainContent?.querySelector('.section-title');
    if (sectionTitle) {
      sectionTitle.textContent = this.getSectionTitle(sectionId);
    }

    // Clear and update book grid
    this.bookGrid?.clear();
    
    let booksToShow = [];
    let gridOptions = {};

    switch (sectionId) {
      case 'library':
        booksToShow = this.books;
        gridOptions = { 
          variant: 'library',
          showProgress: true 
        };
        break;

      case 'recommendations':
        booksToShow = this.recommendations;
        gridOptions = { 
          variant: 'recommendation',
          showMatchScore: true 
        };
        break;

      case 'reading':
        booksToShow = this.books.filter(book => book.progress > 0 && book.progress < 100);
        gridOptions = { 
          variant: 'reading',
          showProgress: true 
        };
        break;

      case 'wishlist':
        // Mock wishlist data
        booksToShow = [];
        break;

      case 'analytics':
        this.displayAnalytics();
        return;
    }

    // Update grid variant
    if (this.bookGrid?.element) {
      this.bookGrid.element.className = `book-grid ${sectionId}`;
    }

    // Add books to grid
    if (booksToShow.length > 0) {
      this.bookGrid?.addBooks(booksToShow, gridOptions);
    } else {
      this.showEmptyState(sectionId);
    }
  }

  /**
   * Get section title
   * @param {string} sectionId
   */
  getSectionTitle(sectionId) {
    const titles = {
      library: 'My Library',
      recommendations: 'Recommended for You',
      reading: 'Currently Reading',
      wishlist: 'My Wishlist',
      analytics: 'Reading Analytics'
    };
    return titles[sectionId] || 'Books';
  }

  /**
   * Display analytics section
   */
  displayAnalytics() {
    const contentArea = this.mainContent?.querySelector('.content-area');
    if (!contentArea) return;

    contentArea.innerHTML = `
      <div class="analytics-grid">
        <div class="analytics-card">
          <h3>Books Read This Year</h3>
          <div class="analytics-value">42</div>
          <div class="analytics-change">+8 from last year</div>
        </div>
        <div class="analytics-card">
          <h3>Average Rating</h3>
          <div class="analytics-value">4.2 ⭐</div>
          <div class="analytics-change">+0.3 from last year</div>
        </div>
        <div class="analytics-card">
          <h3>Reading Streak</h3>
          <div class="analytics-value">15 days</div>
          <div class="analytics-change">Personal best!</div>
        </div>
        <div class="analytics-card">
          <h3>Favorite Genre</h3>
          <div class="analytics-value">Science Fiction</div>
          <div class="analytics-change">32% of reading time</div>
        </div>
      </div>
    `;
  }

  /**
   * Show empty state
   * @param {string} sectionId
   */
  showEmptyState(sectionId) {
    const contentArea = this.mainContent?.querySelector('.content-area');
    if (!contentArea) return;

    const emptyMessages = {
      library: 'Your library is empty. Add some books to get started!',
      recommendations: 'No recommendations available. Add some books to your library first.',
      reading: 'No books currently in progress. Start reading something new!',
      wishlist: 'Your wishlist is empty. Add books you want to read later.'
    };

    contentArea.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📚</div>
        <div class="empty-message">${emptyMessages[sectionId] || 'No content available.'}</div>
        <button class="empty-action" onclick="window.kindleDashboard.navigateToSection('recommendations')">
          Discover Books
        </button>
      </div>
    `;
  }

  /**
   * Handle book actions
   * @param {string} action
   * @param {Object} book
   */
  handleBookAction(action, book) {
    console.log(`Book action: ${action}`, book);

    switch (action) {
      case 'continue':
      case 'start':
        this.openReader(book);
        break;
        
      case 'add':
        this.addToLibrary(book);
        break;
        
      case 'details':
        this.showBookDetails(book);
        break;
        
      case 'preview':
        this.previewBook(book);
        break;
        
      default:
        console.warn(`Unknown book action: ${action}`);
    }
  }

  /**
   * Open book reader
   * @param {Object} book
   */
  openReader(book) {
    // Create reading overlay
    const overlay = document.createElement('div');
    overlay.className = 'reading-overlay';
    overlay.innerHTML = `
      <div class="reading-header">
        <button class="reading-close" aria-label="Close reader">✕</button>
        <div class="reading-title">${book.title}</div>
        <div class="reading-controls">
          ${this.brightnessController.element?.outerHTML || ''}
        </div>
      </div>
      <div class="reading-content">
        <div class="reading-page">
          <h1>Chapter 1</h1>
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
          <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
        </div>
        <div class="reading-navigation">
          <button class="reading-prev" aria-label="Previous page">‹</button>
          <span class="reading-progress">Page 1 of 284</span>
          <button class="reading-next" aria-label="Next page">›</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    // Close handler
    const closeBtn = overlay.querySelector('.reading-close');
    closeBtn?.addEventListener('click', () => {
      overlay.remove();
    });

    // Escape key handler
    const escapeHandler = (e) => {
      if (e.key === 'Escape') {
        overlay.remove();
        document.removeEventListener('keydown', escapeHandler);
      }
    };
    document.addEventListener('keydown', escapeHandler);
  }

  /**
   * Add book to library
   * @param {Object} book
   */
  addToLibrary(book) {
    // Add progress property for library books
    const libraryBook = { ...book, progress: 0 };
    this.books.push(libraryBook);
    
    // Show success message
    this.showNotification(`"${book.title}" added to your library!`, 'success');
    
    // Refresh current view if showing library
    if (this.currentSection === 'library') {
      this.displaySection('library');
    }
  }

  /**
   * Show book details
   * @param {Object} book
   */
  showBookDetails(book) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="book-details-modal">
        <button class="modal-close" aria-label="Close details">✕</button>
        <div class="book-details-content">
          <div class="book-details-cover">
            <img src="${book.coverUrl}" alt="Cover of ${book.title}" />
          </div>
          <div class="book-details-info">
            <h2>${book.title}</h2>
            <p class="book-details-author">by ${book.author}</p>
            <div class="book-details-rating">
              ${'★'.repeat(Math.floor(book.rating))}${'☆'.repeat(5 - Math.floor(book.rating))}
              ${book.rating}/5
            </div>
            <div class="book-details-genres">
              ${book.genres?.map(genre => `<span class="genre-tag">${genre}</span>`).join('') || ''}
            </div>
            <p class="book-details-description">
              A compelling story that will keep you turning pages late into the night. 
              This book offers deep insights and memorable characters that will stay with you long after reading.
            </p>
            <div class="book-details-actions">
              <button class="btn-primary">Add to Library</button>
              <button class="btn-secondary">Preview</button>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Close handlers
    const closeBtn = modal.querySelector('.modal-close');
    closeBtn?.addEventListener('click', () => modal.remove());

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });
  }

  /**
   * Preview book
   * @param {Object} book
   */
  previewBook(book) {
    this.showNotification(`Opening preview for "${book.title}"...`, 'info');
  }

  /**
   * Search books
   * @param {string} query
   */
  async searchBooks(query) {
    this.setLoading(true);
    
    try {
      // Mock search - replace with actual API call
      const searchResults = this.books.filter(book => 
        book.title.toLowerCase().includes(query.toLowerCase()) ||
        book.author.toLowerCase().includes(query.toLowerCase())
      );

      this.bookGrid?.clear();
      
      if (searchResults.length > 0) {
        this.bookGrid?.addBooks(searchResults, { variant: 'library' });
      } else {
        this.showEmptyState('search');
      }

      // Update section title
      const sectionTitle = this.mainContent?.querySelector('.section-title');
      if (sectionTitle) {
        sectionTitle.textContent = `Search Results for "${query}"`;
      }
      
    } catch (error) {
      console.error('Search failed:', error);
      this.showErrorMessage('Search failed. Please try again.');
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Open settings panel
   */
  openSettings() {
    const settingsModal = document.createElement('div');
    settingsModal.className = 'modal-overlay';
    settingsModal.innerHTML = `
      <div class="settings-modal">
        <div class="settings-header">
          <h2>Settings</h2>
          <button class="modal-close" aria-label="Close settings">✕</button>
        </div>
        <div class="settings-content">
          <div class="settings-section">
            <h3>Appearance</h3>
            <div class="setting-item">
              <label>Theme</label>
              <div id="settings-theme-toggle"></div>
            </div>
            <div class="setting-item">
              <label>Brightness</label>
              <div id="settings-brightness-control"></div>
            </div>
            <div class="setting-item">
              <label>
                <input type="checkbox" ${this.settings.autoBrightness ? 'checked' : ''} id="auto-brightness">
                Auto-adjust brightness based on time
              </label>
            </div>
          </div>
          <div class="settings-section">
            <h3>Reading</h3>
            <div class="setting-item">
              <label for="font-size">Font Size</label>
              <select id="font-size">
                <option value="small" ${this.settings.fontSize === 'small' ? 'selected' : ''}>Small</option>
                <option value="medium" ${this.settings.fontSize === 'medium' ? 'selected' : ''}>Medium</option>
                <option value="large" ${this.settings.fontSize === 'large' ? 'selected' : ''}>Large</option>
              </select>
            </div>
            <div class="setting-item">
              <label for="line-spacing">Line Spacing</label>
              <select id="line-spacing">
                <option value="tight" ${this.settings.lineSpacing === 'tight' ? 'selected' : ''}>Tight</option>
                <option value="normal" ${this.settings.lineSpacing === 'normal' ? 'selected' : ''}>Normal</option>
                <option value="relaxed" ${this.settings.lineSpacing === 'relaxed' ? 'selected' : ''}>Relaxed</option>
              </select>
            </div>
          </div>
        </div>
        <div class="settings-footer">
          <button class="btn-secondary" id="settings-reset">Reset to Defaults</button>
          <button class="btn-primary" id="settings-save">Save Changes</button>
        </div>
      </div>
    `;

    document.body.appendChild(settingsModal);

    // Add theme toggle to settings
    const themeToggleContainer = settingsModal.querySelector('#settings-theme-toggle');
    if (themeToggleContainer) {
      this.themeManager.createToggle(themeToggleContainer, {
        variant: 'radio-style',
        size: 'sm'
      });
    }

    // Add brightness control to settings
    const brightnessContainer = settingsModal.querySelector('#settings-brightness-control');
    if (brightnessContainer) {
      this.brightnessController.createControl(brightnessContainer, {
        size: 'md',
        showPercentage: true
      });
    }

    // Event handlers
    const closeBtn = settingsModal.querySelector('.modal-close');
    closeBtn?.addEventListener('click', () => settingsModal.remove());

    const saveBtn = settingsModal.querySelector('#settings-save');
    saveBtn?.addEventListener('click', () => {
      this.saveSettingsFromModal(settingsModal);
      settingsModal.remove();
    });

    const resetBtn = settingsModal.querySelector('#settings-reset');
    resetBtn?.addEventListener('click', () => {
      this.resetSettings();
      settingsModal.remove();
    });
  }

  /**
   * Save settings from modal
   * @param {HTMLElement} modal
   */
  saveSettingsFromModal(modal) {
    const autoBrightness = modal.querySelector('#auto-brightness')?.checked || false;
    const fontSize = modal.querySelector('#font-size')?.value || 'medium';
    const lineSpacing = modal.querySelector('#line-spacing')?.value || 'normal';

    this.settings = {
      ...this.settings,
      autoBrightness,
      fontSize,
      lineSpacing
    };

    this.brightnessController.setAutoAdjust(autoBrightness);
    this.saveSettings();
    this.showNotification('Settings saved successfully!', 'success');
  }

  /**
   * Reset settings to defaults
   */
  resetSettings() {
    this.settings = {
      autoTheme: false,
      autoBrightness: false,
      fontSize: 'medium',
      lineSpacing: 'normal',
      margins: 'medium'
    };

    this.themeManager.setTheme('system');
    this.brightnessController.setValue(70);
    this.brightnessController.setAutoAdjust(false);
    
    this.saveSettings();
    this.showNotification('Settings reset to defaults!', 'info');
  }

  /**
   * Set loading state
   * @param {boolean} loading
   */
  setLoading(loading) {
    this.isLoading = loading;
    this.container?.classList.toggle('loading', loading);
    this.bookGrid?.setLoading(loading);
  }

  /**
   * Show notification
   * @param {string} message
   * @param {string} type
   */
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      notification.remove();
    }, 3000);
  }

  /**
   * Show error message
   * @param {string} message
   */
  showErrorMessage(message) {
    this.showNotification(message, 'error');
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'k':
            e.preventDefault();
            this.focusSearch();
            break;
          case ',':
            e.preventDefault();
            this.openSettings();
            break;
          case 'd':
            e.preventDefault();
            this.themeManager.toggle();
            break;
        }
      }
    });

    // Window resize handler
    window.addEventListener('resize', () => {
      this.handleResize();
    });

    // Theme change handler
    document.addEventListener('themechange', (e) => {
      console.log('Theme changed:', e.detail);
    });
  }

  /**
   * Focus search input
   */
  focusSearch() {
    const searchInput = this.header?.querySelector('.search-input');
    searchInput?.focus();
  }

  /**
   * Handle window resize
   */
  handleResize() {
    // Responsive adjustments
    const width = window.innerWidth;
    
    if (width < 768) {
      this.container?.classList.add('mobile');
    } else {
      this.container?.classList.remove('mobile');
    }
  }

  /**
   * Load settings from localStorage
   */
  loadSettings() {
    try {
      const saved = localStorage.getItem('kindle-dashboard-settings');
      if (saved) {
        this.settings = { ...this.settings, ...JSON.parse(saved) };
      }
    } catch (error) {
      console.warn('Failed to load settings:', error);
    }
  }

  /**
   * Save settings to localStorage
   */
  saveSettings() {
    try {
      localStorage.setItem('kindle-dashboard-settings', JSON.stringify(this.settings));
    } catch (error) {
      console.warn('Failed to save settings:', error);
    }
  }

  /**
   * Dispatch custom event
   * @param {string} eventName
   * @param {Object} detail
   */
  dispatchEvent(eventName, detail = {}) {
    const event = new CustomEvent(eventName, {
      detail: { dashboard: this, ...detail }
    });
    document.dispatchEvent(event);
  }

  /**
   * Handle error
   * @param {Error} error
   */
  handleError(error) {
    console.error('Dashboard error:', error);
    this.showErrorMessage('Something went wrong. Please refresh the page.');
  }

  /**
   * Destroy dashboard
   */
  destroy() {
    this.themeManager?.destroy();
    this.brightnessController?.destroy();
    this.bookGrid?.destroy();
    
    if (this.container) {
      this.container.innerHTML = '';
      this.container.className = '';
    }

    this.isInitialized = false;
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Global instance
  window.kindleDashboard = new KindleDashboard();
  
  // Initialize with default container
  const container = document.getElementById('dashboard-container') || document.body;
  window.kindleDashboard.init(container);
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = KindleDashboard;
}

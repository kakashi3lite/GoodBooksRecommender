/**
 * 📖 Book Card Component
 * Kindle Paperwhite-inspired book display cards with interactive features
 */

class BookCard {
  constructor() {
    this.element = null;
    this.book = null;
    this.variant = 'library'; // 'library', 'recommendation', 'reading'
    this.onAction = null;
    
    // Loading states
    this.isLoading = false;
    this.imageLoaded = false;
  }

  /**
   * Create book card element
   * @param {Object} book - Book data
   * @param {Object} options - Configuration options
   */
  create(book, options = {}) {
    const {
      variant = 'library',
      size = 'default',
      showProgress = false,
      showMatchScore = false,
      showGenres = false,
      onAction = null,
      className = ''
    } = options;

    this.book = book;
    this.variant = variant;
    this.onAction = onAction;

    // Create main container
    this.element = document.createElement('article');
    this.element.className = `book-card ${variant} ${size} ${className}`;
    this.element.setAttribute('role', 'article');
    this.element.setAttribute('aria-label', `Book: ${book.title} by ${book.author}`);
    this.element.setAttribute('tabindex', '0');

    // Create cover section
    this.createCover();

    // Create content section
    this.createContent({
      showProgress,
      showMatchScore,
      showGenres
    });

    // Attach event listeners
    this.attachEventListeners();

    return this.element;
  }

  /**
   * Create book cover section
   */
  createCover() {
    const cover = document.createElement('div');
    cover.className = 'book-cover';

    if (this.book.coverUrl) {
      const img = document.createElement('img');
      img.className = 'book-cover-image';
      img.src = this.book.coverUrl;
      img.alt = `Cover of ${this.book.title}`;
      img.loading = 'lazy';
      
      // Handle image load/error
      img.addEventListener('load', () => {
        this.imageLoaded = true;
        this.element?.classList.add('image-loaded');
      });
      
      img.addEventListener('error', () => {
        this.createPlaceholderCover(cover);
      });
      
      cover.appendChild(img);
    } else {
      this.createPlaceholderCover(cover);
    }

    this.element.appendChild(cover);
  }

  /**
   * Create placeholder cover when no image available
   * @param {HTMLElement} container
   */
  createPlaceholderCover(container) {
    // Clear existing content
    container.innerHTML = '';
    
    const placeholder = document.createElement('div');
    placeholder.className = 'book-cover-placeholder';
    placeholder.textContent = '📖';
    placeholder.setAttribute('aria-label', 'Book cover placeholder');
    
    container.appendChild(placeholder);
  }

  /**
   * Create book content section
   * @param {Object} options
   */
  createContent(options) {
    const content = document.createElement('div');
    content.className = 'book-content';

    // Title
    const title = document.createElement('h3');
    title.className = 'book-title';
    title.textContent = this.book.title;
    content.appendChild(title);

    // Author
    const author = document.createElement('p');
    author.className = 'book-author';
    author.textContent = `by ${this.book.author}`;
    content.appendChild(author);

    // Metadata container
    const metadata = document.createElement('div');
    metadata.className = 'book-metadata';

    // Rating
    if (this.book.rating) {
      metadata.appendChild(this.createRating());
    }

    // Progress (for library books)
    if (options.showProgress && this.book.progress !== undefined) {
      metadata.appendChild(this.createProgress());
    }

    // Match score (for recommendations)
    if (options.showMatchScore && this.book.matchScore !== undefined) {
      metadata.appendChild(this.createMatchScore());
    }

    // Genres
    if (options.showGenres && this.book.genres?.length) {
      metadata.appendChild(this.createGenres());
    }

    content.appendChild(metadata);

    // Actions
    content.appendChild(this.createActions());

    this.element.appendChild(content);
  }

  /**
   * Create rating display
   * @returns {HTMLElement}
   */
  createRating() {
    const rating = document.createElement('div');
    rating.className = 'book-rating';
    rating.setAttribute('aria-label', `Rating: ${this.book.rating} out of 5 stars`);

    const stars = document.createElement('div');
    stars.className = 'book-stars';
    stars.setAttribute('role', 'img');
    stars.setAttribute('aria-hidden', 'true');

    // Create 5 stars
    for (let i = 1; i <= 5; i++) {
      const star = document.createElement('span');
      star.className = 'star';
      
      if (i <= Math.floor(this.book.rating)) {
        star.classList.add('filled');
        star.textContent = '★';
      } else if (i - 0.5 <= this.book.rating) {
        star.classList.add('half');
        star.textContent = '★';
      } else {
        star.textContent = '☆';
      }
      
      stars.appendChild(star);
    }

    rating.appendChild(stars);

    // Rating text
    const ratingText = document.createElement('span');
    ratingText.className = 'book-rating-text';
    ratingText.textContent = this.book.rating.toFixed(1);
    rating.appendChild(ratingText);

    return rating;
  }

  /**
   * Create progress bar
   * @returns {HTMLElement}
   */
  createProgress() {
    const progressContainer = document.createElement('div');
    progressContainer.className = 'book-progress';

    const progressBar = document.createElement('div');
    progressBar.className = 'book-progress-bar';
    progressBar.setAttribute('role', 'progressbar');
    progressBar.setAttribute('aria-valuemin', '0');
    progressBar.setAttribute('aria-valuemax', '100');
    progressBar.setAttribute('aria-valuenow', this.book.progress.toString());
    progressBar.setAttribute('aria-label', `Reading progress: ${this.book.progress}%`);

    const progressFill = document.createElement('div');
    progressFill.className = 'book-progress-fill';
    progressFill.style.width = `${this.book.progress}%`;

    progressBar.appendChild(progressFill);
    progressContainer.appendChild(progressBar);

    const progressText = document.createElement('div');
    progressText.className = 'book-progress-text';
    progressText.textContent = `${this.book.progress}% complete`;
    progressContainer.appendChild(progressText);

    return progressContainer;
  }

  /**
   * Create match score display
   * @returns {HTMLElement}
   */
  createMatchScore() {
    const matchScore = document.createElement('div');
    matchScore.className = 'book-match-score';
    matchScore.setAttribute('aria-label', `Match score: ${this.book.matchScore}%`);

    const icon = document.createElement('span');
    icon.className = 'match-icon';
    icon.textContent = '🎯';
    icon.setAttribute('aria-hidden', 'true');

    const percentage = document.createElement('span');
    percentage.className = 'match-percentage';
    percentage.textContent = `${this.book.matchScore}% Match`;

    matchScore.appendChild(icon);
    matchScore.appendChild(percentage);

    return matchScore;
  }

  /**
   * Create genres display
   * @returns {HTMLElement}
   */
  createGenres() {
    const genresContainer = document.createElement('div');
    genresContainer.className = 'book-genres';
    genresContainer.setAttribute('aria-label', `Genres: ${this.book.genres.join(', ')}`);

    // Show max 3 genres to avoid overcrowding
    const displayGenres = this.book.genres.slice(0, 3);
    
    displayGenres.forEach(genre => {
      const genreTag = document.createElement('span');
      genreTag.className = 'book-genre';
      genreTag.textContent = genre;
      genresContainer.appendChild(genreTag);
    });

    return genresContainer;
  }

  /**
   * Create action buttons
   * @returns {HTMLElement}
   */
  createActions() {
    const actions = document.createElement('div');
    actions.className = 'book-actions';

    const actionButtons = this.getActionButtons();
    
    actionButtons.forEach(action => {
      const button = document.createElement('button');
      button.className = `book-action ${action.variant || ''}`;
      button.textContent = action.label;
      button.setAttribute('aria-label', action.ariaLabel || action.label);
      
      if (action.disabled) {
        button.disabled = true;
        button.setAttribute('aria-disabled', 'true');
      }

      button.addEventListener('click', (e) => {
        e.stopPropagation();
        this.handleAction(action.type);
      });

      actions.appendChild(button);
    });

    return actions;
  }

  /**
   * Get action buttons based on variant and book state
   * @returns {Array}
   */
  getActionButtons() {
    switch (this.variant) {
      case 'library':
        if (this.book.progress && this.book.progress > 0) {
          return [
            { type: 'continue', label: 'Continue', variant: 'primary', ariaLabel: 'Continue reading' },
            { type: 'details', label: 'Details', ariaLabel: 'View book details' }
          ];
        } else {
          return [
            { type: 'start', label: 'Start Reading', variant: 'primary', ariaLabel: 'Start reading this book' },
            { type: 'details', label: 'Details', ariaLabel: 'View book details' }
          ];
        }

      case 'recommendation':
        return [
          { type: 'add', label: 'Add to Library', variant: 'primary', ariaLabel: 'Add book to library' },
          { type: 'preview', label: 'Preview', ariaLabel: 'Preview book' }
        ];

      case 'reading':
        return [
          { type: 'continue', label: 'Continue', variant: 'primary', ariaLabel: 'Continue reading' },
          { type: 'bookmark', label: 'Bookmark', ariaLabel: 'Add bookmark' }
        ];

      default:
        return [
          { type: 'details', label: 'Details', ariaLabel: 'View book details' }
        ];
    }
  }

  /**
   * Handle action button click
   * @param {string} actionType
   */
  handleAction(actionType) {
    if (this.onAction && typeof this.onAction === 'function') {
      this.onAction(actionType, this.book);
    }

    // Dispatch custom event
    const event = new CustomEvent('bookaction', {
      detail: {
        action: actionType,
        book: this.book,
        card: this
      },
      bubbles: true
    });
    
    this.element?.dispatchEvent(event);
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    if (!this.element) return;

    // Card click (but not on buttons)
    this.element.addEventListener('click', (e) => {
      // Don't trigger if clicking on buttons or interactive elements
      if (e.target.closest('.book-action, button, a')) {
        return;
      }
      
      this.handleAction('details');
    });

    // Keyboard navigation
    this.element.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        this.handleAction('details');
      }
    });

    // Mouse enter/leave for hover effects
    this.element.addEventListener('mouseenter', () => {
      this.element?.classList.add('hover');
    });

    this.element.addEventListener('mouseleave', () => {
      this.element?.classList.remove('hover');
    });
  }

  /**
   * Set loading state
   * @param {boolean} loading
   */
  setLoading(loading) {
    this.isLoading = loading;
    
    if (this.element) {
      this.element.classList.toggle('loading', loading);
      
      // Disable interactions during loading
      const actions = this.element.querySelectorAll('.book-action');
      actions.forEach(action => {
        action.disabled = loading;
        action.setAttribute('aria-disabled', loading ? 'true' : 'false');
      });
    }
  }

  /**
   * Update book data
   * @param {Object} newBook
   */
  updateBook(newBook) {
    this.book = { ...this.book, ...newBook };
    
    // Update title
    const title = this.element?.querySelector('.book-title');
    if (title) {
      title.textContent = this.book.title;
    }

    // Update author
    const author = this.element?.querySelector('.book-author');
    if (author) {
      author.textContent = `by ${this.book.author}`;
    }

    // Update progress if exists
    if (this.book.progress !== undefined) {
      const progressFill = this.element?.querySelector('.book-progress-fill');
      const progressText = this.element?.querySelector('.book-progress-text');
      
      if (progressFill) {
        progressFill.style.width = `${this.book.progress}%`;
      }
      
      if (progressText) {
        progressText.textContent = `${this.book.progress}% complete`;
      }
    }

    // Update match score if exists
    if (this.book.matchScore !== undefined) {
      const matchPercentage = this.element?.querySelector('.match-percentage');
      if (matchPercentage) {
        matchPercentage.textContent = `${this.book.matchScore}% Match`;
      }
    }

    // Update aria-label
    this.element?.setAttribute('aria-label', `Book: ${this.book.title} by ${this.book.author}`);
  }

  /**
   * Set selected state
   * @param {boolean} selected
   */
  setSelected(selected) {
    if (this.element) {
      this.element.classList.toggle('selected', selected);
      this.element.setAttribute('aria-selected', selected ? 'true' : 'false');
    }
  }

  /**
   * Set featured state
   * @param {boolean} featured
   */
  setFeatured(featured) {
    if (this.element) {
      this.element.classList.toggle('featured', featured);
    }
  }

  /**
   * Set disabled state
   * @param {boolean} disabled
   */
  setDisabled(disabled) {
    if (this.element) {
      this.element.classList.toggle('disabled', disabled);
      this.element.setAttribute('aria-disabled', disabled ? 'true' : 'false');
      
      if (disabled) {
        this.element.setAttribute('tabindex', '-1');
      } else {
        this.element.setAttribute('tabindex', '0');
      }
    }
  }

  /**
   * Animate card entrance
   */
  animateIn() {
    if (!this.element) return;

    this.element.style.opacity = '0';
    this.element.style.transform = 'translateY(20px)';
    
    // Force reflow
    this.element.offsetHeight;
    
    this.element.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
    this.element.style.opacity = '1';
    this.element.style.transform = 'translateY(0)';
    
    // Clean up inline styles after animation
    setTimeout(() => {
      if (this.element) {
        this.element.style.opacity = '';
        this.element.style.transform = '';
        this.element.style.transition = '';
      }
    }, 300);
  }

  /**
   * Get book data
   * @returns {Object}
   */
  getBook() {
    return this.book;
  }

  /**
   * Get card element
   * @returns {HTMLElement}
   */
  getElement() {
    return this.element;
  }

  /**
   * Destroy the book card
   */
  destroy() {
    if (this.element) {
      this.element.remove();
    }
    
    this.element = null;
    this.book = null;
    this.onAction = null;
  }
}

/**
 * Book Grid Component
 * Manages a collection of book cards
 */
class BookGrid {
  constructor() {
    this.element = null;
    this.cards = [];
    this.books = [];
    this.variant = 'library';
    this.onAction = null;
  }

  /**
   * Create book grid
   * @param {HTMLElement} container
   * @param {Object} options
   */
  create(container, options = {}) {
    const {
      variant = 'library',
      className = '',
      onAction = null
    } = options;

    this.variant = variant;
    this.onAction = onAction;

    this.element = document.createElement('div');
    this.element.className = `book-grid ${variant} ${className}`;
    this.element.setAttribute('role', 'grid');
    this.element.setAttribute('aria-label', `${variant} books`);

    container.appendChild(this.element);
    return this.element;
  }

  /**
   * Add books to grid
   * @param {Array} books
   * @param {Object} options
   */
  addBooks(books, options = {}) {
    books.forEach(book => {
      this.addBook(book, options);
    });
  }

  /**
   * Add single book to grid
   * @param {Object} book
   * @param {Object} options
   */
  addBook(book, options = {}) {
    const card = new BookCard();
    const cardElement = card.create(book, {
      variant: this.variant,
      onAction: this.onAction,
      ...options
    });

    this.element?.appendChild(cardElement);
    this.cards.push(card);
    this.books.push(book);

    // Animate in
    setTimeout(() => card.animateIn(), 50);

    return card;
  }

  /**
   * Clear all books
   */
  clear() {
    this.cards.forEach(card => card.destroy());
    this.cards = [];
    this.books = [];
    
    if (this.element) {
      this.element.innerHTML = '';
    }
  }

  /**
   * Set loading state
   * @param {boolean} loading
   */
  setLoading(loading) {
    this.cards.forEach(card => card.setLoading(loading));
  }

  /**
   * Get all cards
   * @returns {Array}
   */
  getCards() {
    return this.cards;
  }

  /**
   * Get all books
   * @returns {Array}
   */
  getBooks() {
    return this.books;
  }

  /**
   * Destroy the grid
   */
  destroy() {
    this.clear();
    
    if (this.element) {
      this.element.remove();
    }
    
    this.element = null;
    this.onAction = null;
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BookCard, BookGrid };
}

// Global export for browser
if (typeof window !== 'undefined') {
  window.BookCard = BookCard;
  window.BookGrid = BookGrid;
}

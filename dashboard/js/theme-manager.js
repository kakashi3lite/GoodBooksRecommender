/**
 * 🎨 Theme Manager - Kindle Paperwhite E-ink Simulation
 * Handles theme switching with smooth transitions and system preference detection
 * Optimized for e-ink display characteristics and paper-white reading experience
 */

class ThemeManager {
  constructor() {
    this.currentTheme = 'system'; // 'light', 'dark', 'system'
    this.systemTheme = 'light';
    this.isTransitioning = false;
    this.observers = [];
    
    // E-ink display characteristics
    this.eInkSimulation = {
      enabled: true,
      refreshRate: 250, // Simulated e-ink refresh rate in ms
      ghostingEffect: false, // Subtle ghosting for authentic e-ink feel
      paperTexture: true // Paper-white texture simulation
    };
    
    // Media query for system theme detection
    this.mediaQuery = null;
    
    this.init();
  }

  /**
   * Initialize the theme manager
   */
  init() {
    this.loadSettings();
    this.setupSystemThemeDetection();
    this.applyTheme();
    
    // Initial system theme check
    this.updateSystemTheme();
  }

  /**
   * Setup system theme detection
   */
  setupSystemThemeDetection() {
    // Check if browser supports dark mode detection
    if (window.matchMedia) {
      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      // Add listener for system theme changes
      this.mediaQuery.addEventListener('change', (e) => {
        this.updateSystemTheme();
        
        // If using system theme, apply the new theme
        if (this.currentTheme === 'system') {
          this.applyTheme();
        }
      });
    }
  }

  /**
   * Update system theme based on media query
   */
  updateSystemTheme() {
    if (this.mediaQuery) {
      this.systemTheme = this.mediaQuery.matches ? 'dark' : 'light';
    } else {
      // Fallback: assume light theme if no support
      this.systemTheme = 'light';
    }
  }

  /**
   * Get the effective theme (resolves 'system' to actual theme)
   * @returns {string} The effective theme ('light' or 'dark')
   */
  getEffectiveTheme() {
    if (this.currentTheme === 'system') {
      return this.systemTheme;
    }
    return this.currentTheme;
  }

  /**
   * Set the theme
   * @param {string} theme - Theme to set ('light', 'dark', 'system')
   * @param {boolean} smooth - Whether to use smooth transition
   */
  setTheme(theme, smooth = true) {
    if (!['light', 'dark', 'system'].includes(theme)) {
      console.warn(`Invalid theme: ${theme}`);
      return;
    }

    const oldTheme = this.getEffectiveTheme();
    this.currentTheme = theme;
    const newTheme = this.getEffectiveTheme();

    // Only transition if theme actually changed
    if (oldTheme !== newTheme) {
      this.applyTheme(smooth);
    }

    // Save settings
    this.saveSettings();

    // Notify observers
    this.notifyObservers(theme, newTheme);
  }

  /**
   * Apply the current theme to the document
   * @param {boolean} smooth - Whether to use smooth transition
   */
  applyTheme(smooth = true) {
    const effectiveTheme = this.getEffectiveTheme();
    
    if (smooth && !this.isTransitioning) {
      this.isTransitioning = true;
      
      // Add transition class
      document.documentElement.style.setProperty('--transition-duration', '200ms');
      
      // Apply theme
      document.documentElement.setAttribute('data-theme', effectiveTheme);
      
      // Remove transition after completion
      setTimeout(() => {
        document.documentElement.style.removeProperty('--transition-duration');
        this.isTransitioning = false;
      }, 200);
    } else {
      // Immediate theme change
      document.documentElement.setAttribute('data-theme', effectiveTheme);
    }

    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(effectiveTheme);
    
    // Dispatch custom event
    this.dispatchThemeEvent(effectiveTheme);
  }

  /**
   * Update meta theme-color for mobile browsers
   * @param {string} theme
   */
  updateMetaThemeColor(theme) {
    let metaThemeColor = document.querySelector('meta[name="theme-color"]');
    
    if (!metaThemeColor) {
      metaThemeColor = document.createElement('meta');
      metaThemeColor.name = 'theme-color';
      document.head.appendChild(metaThemeColor);
    }

    // Set theme color based on current theme
    const colors = {
      light: '#FAFAF9',
      dark: '#1E1E1E'
    };
    
    metaThemeColor.content = colors[theme] || colors.light;
  }

  /**
   * Dispatch theme change event
   * @param {string} effectiveTheme
   */
  dispatchThemeEvent(effectiveTheme) {
    const event = new CustomEvent('themechange', {
      detail: {
        theme: this.currentTheme,
        effectiveTheme: effectiveTheme,
        systemTheme: this.systemTheme
      }
    });
    
    document.dispatchEvent(event);
  }

  /**
   * Toggle between light and dark themes
   */
  toggle() {
    const effectiveTheme = this.getEffectiveTheme();
    const newTheme = effectiveTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }

  /**
   * Get current theme
   * @returns {string}
   */
  getTheme() {
    return this.currentTheme;
  }

  /**
   * Check if dark theme is active
   * @returns {boolean}
   */
  isDarkMode() {
    return this.getEffectiveTheme() === 'dark';
  }

  /**
   * Check if light theme is active
   * @returns {boolean}
   */
  isLightMode() {
    return this.getEffectiveTheme() === 'light';
  }

  /**
   * Check if system theme is being used
   * @returns {boolean}
   */
  isSystemMode() {
    return this.currentTheme === 'system';
  }

  /**
   * Add theme change observer
   * @param {Function} callback - Callback function (theme, effectiveTheme) => void
   */
  addObserver(callback) {
    if (typeof callback === 'function') {
      this.observers.push(callback);
    }
  }

  /**
   * Remove theme change observer
   * @param {Function} callback
   */
  removeObserver(callback) {
    const index = this.observers.indexOf(callback);
    if (index > -1) {
      this.observers.splice(index, 1);
    }
  }

  /**
   * Notify all observers of theme change
   * @param {string} theme
   * @param {string} effectiveTheme
   */
  notifyObservers(theme, effectiveTheme) {
    this.observers.forEach(callback => {
      try {
        callback(theme, effectiveTheme);
      } catch (error) {
        console.warn('Theme observer error:', error);
      }
    });
  }

  /**
   * Create theme toggle component
   * @param {HTMLElement} container - Container element
   * @param {Object} options - Configuration options
   */
  createToggle(container, options = {}) {
    const {
      variant = 'buttons', // 'buttons', 'compact', 'dropdown'
      size = 'md',
      showLabels = true,
      className = ''
    } = options;

    const toggle = document.createElement('div');
    toggle.className = `theme-toggle ${variant} size-${size} ${className}`;
    toggle.setAttribute('role', 'radiogroup');
    toggle.setAttribute('aria-label', 'Theme selection');

    if (variant === 'dropdown') {
      this.createDropdownToggle(toggle);
    } else {
      this.createButtonToggle(toggle, showLabels);
    }

    container.appendChild(toggle);
    return toggle;
  }

  /**
   * Create button-style theme toggle
   * @param {HTMLElement} container
   * @param {boolean} showLabels
   */
  createButtonToggle(container, showLabels) {
    const themes = [
      { value: 'light', icon: '☀️', label: 'Light' },
      { value: 'dark', icon: '🌙', label: 'Dark' },
      { value: 'system', icon: '💻', label: 'System' }
    ];

    themes.forEach(theme => {
      const button = document.createElement('button');
      button.className = 'theme-option';
      button.setAttribute('data-theme', theme.value);
      button.setAttribute('role', 'radio');
      button.setAttribute('aria-checked', this.currentTheme === theme.value ? 'true' : 'false');
      button.setAttribute('aria-label', `${theme.label} theme`);

      // Icon
      const icon = document.createElement('span');
      icon.className = 'theme-icon';
      icon.textContent = theme.icon;
      icon.setAttribute('aria-hidden', 'true');
      button.appendChild(icon);

      // Label
      if (showLabels) {
        const label = document.createElement('span');
        label.className = 'theme-label';
        label.textContent = theme.label;
        button.appendChild(label);
      }

      // Set active state
      if (this.currentTheme === theme.value) {
        button.classList.add('active');
      }

      // Click handler
      button.addEventListener('click', () => {
        this.setTheme(theme.value);
        this.updateToggleState(container);
      });

      container.appendChild(button);
    });
  }

  /**
   * Create dropdown-style theme toggle
   * @param {HTMLElement} container
   */
  createDropdownToggle(container) {
    container.classList.add('dropdown');

    const themes = {
      light: { icon: '☀️', label: 'Light' },
      dark: { icon: '🌙', label: 'Dark' },
      system: { icon: '💻', label: 'System' }
    };

    // Current theme display
    const current = document.createElement('button');
    current.className = 'theme-current';
    current.setAttribute('aria-haspopup', 'listbox');
    current.setAttribute('aria-expanded', 'false');

    const currentThemeData = themes[this.currentTheme];
    current.innerHTML = `
      <span class="theme-icon">${currentThemeData.icon}</span>
      <span class="theme-label">${currentThemeData.label}</span>
      <span class="theme-dropdown-icon">▼</span>
    `;

    // Options container
    const options = document.createElement('div');
    options.className = 'theme-options';
    options.setAttribute('role', 'listbox');

    Object.entries(themes).forEach(([value, data]) => {
      const option = document.createElement('button');
      option.className = 'theme-option';
      option.setAttribute('data-theme', value);
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', this.currentTheme === value ? 'true' : 'false');

      option.innerHTML = `
        <span class="theme-icon">${data.icon}</span>
        <span class="theme-label">${data.label}</span>
      `;

      if (this.currentTheme === value) {
        option.classList.add('active');
      }

      option.addEventListener('click', () => {
        this.setTheme(value);
        this.updateDropdownToggle(container);
        this.closeDropdown(container);
      });

      options.appendChild(option);
    });

    // Toggle dropdown
    current.addEventListener('click', () => {
      this.toggleDropdown(container);
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!container.contains(e.target)) {
        this.closeDropdown(container);
      }
    });

    container.appendChild(current);
    container.appendChild(options);
  }

  /**
   * Update toggle state after theme change
   * @param {HTMLElement} toggle
   */
  updateToggleState(toggle) {
    const options = toggle.querySelectorAll('.theme-option');
    
    options.forEach(option => {
      const isActive = option.getAttribute('data-theme') === this.currentTheme;
      option.classList.toggle('active', isActive);
      option.setAttribute('aria-checked', isActive ? 'true' : 'false');
      option.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
  }

  /**
   * Update dropdown toggle after theme change
   * @param {HTMLElement} toggle
   */
  updateDropdownToggle(toggle) {
    const themes = {
      light: { icon: '☀️', label: 'Light' },
      dark: { icon: '🌙', label: 'Dark' },
      system: { icon: '💻', label: 'System' }
    };

    const current = toggle.querySelector('.theme-current');
    const currentThemeData = themes[this.currentTheme];
    
    if (current && currentThemeData) {
      current.innerHTML = `
        <span class="theme-icon">${currentThemeData.icon}</span>
        <span class="theme-label">${currentThemeData.label}</span>
        <span class="theme-dropdown-icon">▼</span>
      `;
    }

    this.updateToggleState(toggle);
  }

  /**
   * Toggle dropdown open/close
   * @param {HTMLElement} toggle
   */
  toggleDropdown(toggle) {
    const isOpen = toggle.classList.contains('open');
    
    if (isOpen) {
      this.closeDropdown(toggle);
    } else {
      this.openDropdown(toggle);
    }
  }

  /**
   * Open dropdown
   * @param {HTMLElement} toggle
   */
  openDropdown(toggle) {
    toggle.classList.add('open');
    
    const current = toggle.querySelector('.theme-current');
    if (current) {
      current.setAttribute('aria-expanded', 'true');
    }
  }

  /**
   * Close dropdown
   * @param {HTMLElement} toggle
   */
  closeDropdown(toggle) {
    toggle.classList.remove('open');
    
    const current = toggle.querySelector('.theme-current');
    if (current) {
      current.setAttribute('aria-expanded', 'false');
    }
  }

  /**
   * Load settings from localStorage
   */
  loadSettings() {
    try {
      const settings = localStorage.getItem('theme-settings');
      if (settings) {
        const parsed = JSON.parse(settings);
        this.currentTheme = ['light', 'dark', 'system'].includes(parsed.theme) 
          ? parsed.theme 
          : 'system';
      }
    } catch (error) {
      console.warn('Failed to load theme settings:', error);
      this.currentTheme = 'system';
    }
  }

  /**
   * Save settings to localStorage
   */
  saveSettings() {
    try {
      const settings = {
        theme: this.currentTheme,
        lastUpdated: Date.now()
      };
      localStorage.setItem('theme-settings', JSON.stringify(settings));
    } catch (error) {
      console.warn('Failed to save theme settings:', error);
    }
  }

  /**
   * Get theme preferences for analytics
   * @returns {Object}
   */
  getAnalytics() {
    return {
      currentTheme: this.currentTheme,
      effectiveTheme: this.getEffectiveTheme(),
      systemTheme: this.systemTheme,
      isSystemSupported: !!this.mediaQuery,
      lastUpdated: Date.now()
    };
  }

  /**
   * Destroy the theme manager
   */
  destroy() {
    // Remove media query listener
    if (this.mediaQuery) {
      this.mediaQuery.removeEventListener('change', this.updateSystemTheme);
    }

    // Clear observers
    this.observers = [];

    // Remove theme attribute
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.style.removeProperty('--transition-duration');
  }

  /**
   * Apply e-ink display optimizations
   * Simulates Kindle Paperwhite display characteristics
   */
  applyEInkOptimizations() {
    if (!this.eInkSimulation.enabled) return;
    
    const root = document.documentElement;
    
    // Add e-ink simulation class for CSS targeting
    root.classList.add('e-ink-simulation');
    
    // Apply paper-white texture if enabled
    if (this.eInkSimulation.paperTexture) {
      root.classList.add('paper-texture');
    }
    
    // Simulate e-ink refresh rate with subtle delay
    if (this.eInkSimulation.refreshRate > 0) {
      root.style.setProperty('--e-ink-refresh-rate', `${this.eInkSimulation.refreshRate}ms`);
    }
    
    // Add subtle ghosting effect for authentic e-ink feel
    if (this.eInkSimulation.ghostingEffect) {
      root.classList.add('e-ink-ghosting');
    }
  }

  /**
   * Toggle e-ink simulation mode
   * @param {boolean} enabled
   */
  setEInkSimulation(enabled) {
    this.eInkSimulation.enabled = enabled;
    const root = document.documentElement;
    
    if (enabled) {
      this.applyEInkOptimizations();
    } else {
      root.classList.remove('e-ink-simulation', 'paper-texture', 'e-ink-ghosting');
    }
    
    this.saveSettings();
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeManager;
}

// Global export for browser
if (typeof window !== 'undefined') {
  window.ThemeManager = ThemeManager;
}

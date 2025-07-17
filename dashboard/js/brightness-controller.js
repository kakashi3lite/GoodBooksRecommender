/**
 * 🎛️ Brightness Controller
 * Manages screen brightness with smooth transitions and persistence
 */

class BrightnessController {
  constructor() {
    this.value = 70; // Default brightness (0-100)
    this.isDragging = false;
    this.element = null;
    this.slider = null;
    this.handle = null;
    this.fill = null;
    this.percentage = null;
    this.icons = { sun: null, moon: null };
    
    // Callbacks
    this.onChange = null;
    this.onRangeChange = null;
    
    // Auto-brightness settings
    this.autoAdjust = false;
    this.autoAdjustInterval = null;
    
    this.init();
  }

  /**
   * Initialize the brightness controller
   */
  init() {
    this.loadSettings();
    this.applyBrightness();
    this.startAutoAdjustment();
  }

  /**
   * Create brightness control element
   * @param {HTMLElement} container - Container element
   * @param {Object} options - Configuration options
   */
  createControl(container, options = {}) {
    const {
      size = 'md',
      showPercentage = true,
      showIcons = true,
      className = ''
    } = options;

    // Create main container
    this.element = document.createElement('div');
    this.element.className = `brightness-control size-${size} ${className}`;
    this.element.setAttribute('data-range', this.getBrightnessRange());

    // Create sun icon
    if (showIcons) {
      this.icons.sun = this.createIcon('sun', '☀️');
      this.element.appendChild(this.icons.sun);
    }

    // Create slider container
    const sliderContainer = document.createElement('div');
    sliderContainer.className = 'brightness-slider';
    sliderContainer.setAttribute('role', 'slider');
    sliderContainer.setAttribute('aria-label', 'Screen brightness');
    sliderContainer.setAttribute('aria-valuemin', '0');
    sliderContainer.setAttribute('aria-valuemax', '100');
    sliderContainer.setAttribute('aria-valuenow', this.value.toString());
    sliderContainer.setAttribute('aria-valuetext', `${this.value} percent brightness`);
    sliderContainer.setAttribute('tabindex', '0');

    // Create fill bar
    this.fill = document.createElement('div');
    this.fill.className = 'brightness-fill';
    this.fill.style.width = `${this.value}%`;

    // Create handle
    this.handle = document.createElement('div');
    this.handle.className = 'brightness-handle';
    this.handle.style.left = `${this.value}%`;
    this.handle.setAttribute('tabindex', '0');
    this.handle.setAttribute('role', 'button');
    this.handle.setAttribute('aria-label', 'Brightness slider handle');

    sliderContainer.appendChild(this.fill);
    sliderContainer.appendChild(this.handle);
    this.slider = sliderContainer;
    this.element.appendChild(sliderContainer);

    // Create moon icon
    if (showIcons) {
      this.icons.moon = this.createIcon('moon', '🌙');
      this.element.appendChild(this.icons.moon);
    }

    // Create percentage display
    if (showPercentage) {
      this.percentage = document.createElement('span');
      this.percentage.className = 'brightness-percentage';
      this.percentage.textContent = `${this.value}%`;
      this.element.appendChild(this.percentage);
    }

    // Attach event listeners
    this.attachEventListeners();

    // Append to container
    container.appendChild(this.element);

    return this.element;
  }

  /**
   * Create icon element
   * @param {string} type - Icon type (sun/moon)
   * @param {string} content - Icon content
   */
  createIcon(type, content) {
    const icon = document.createElement('span');
    icon.className = `brightness-icon ${type}`;
    icon.textContent = content;
    icon.setAttribute('aria-hidden', 'true');
    return icon;
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    if (!this.slider || !this.handle) return;

    // Mouse events
    this.slider.addEventListener('mousedown', this.handleMouseDown.bind(this));
    this.slider.addEventListener('click', this.handleClick.bind(this));
    
    // Touch events
    this.slider.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
    
    // Keyboard events
    this.slider.addEventListener('keydown', this.handleKeyDown.bind(this));
    this.handle.addEventListener('keydown', this.handleKeyDown.bind(this));
    
    // Global mouse events for dragging
    document.addEventListener('mousemove', this.handleMouseMove.bind(this));
    document.addEventListener('mouseup', this.handleMouseUp.bind(this));
    
    // Global touch events for dragging
    document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
    document.addEventListener('touchend', this.handleTouchEnd.bind(this));
  }

  /**
   * Handle mouse down event
   * @param {MouseEvent} e
   */
  handleMouseDown(e) {
    e.preventDefault();
    this.startDrag(this.getPositionFromEvent(e));
  }

  /**
   * Handle touch start event
   * @param {TouchEvent} e
   */
  handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    this.startDrag(this.getPositionFromEvent(touch));
  }

  /**
   * Handle click event
   * @param {MouseEvent} e
   */
  handleClick(e) {
    if (this.isDragging) return;
    
    const position = this.getPositionFromEvent(e);
    this.updateValue(position);
  }

  /**
   * Handle mouse move event
   * @param {MouseEvent} e
   */
  handleMouseMove(e) {
    if (!this.isDragging) return;
    
    e.preventDefault();
    const position = this.getPositionFromEvent(e);
    this.updateValue(position);
  }

  /**
   * Handle touch move event
   * @param {TouchEvent} e
   */
  handleTouchMove(e) {
    if (!this.isDragging) return;
    
    e.preventDefault();
    const touch = e.touches[0];
    const position = this.getPositionFromEvent(touch);
    this.updateValue(position);
  }

  /**
   * Handle mouse up event
   */
  handleMouseUp() {
    if (this.isDragging) {
      this.stopDrag();
    }
  }

  /**
   * Handle touch end event
   */
  handleTouchEnd() {
    if (this.isDragging) {
      this.stopDrag();
    }
  }

  /**
   * Handle keyboard events
   * @param {KeyboardEvent} e
   */
  handleKeyDown(e) {
    let newValue = this.value;
    let handled = true;

    switch (e.key) {
      case 'ArrowLeft':
      case 'ArrowDown':
        newValue = Math.max(0, this.value - (e.shiftKey ? 10 : 5));
        break;
      case 'ArrowRight':
      case 'ArrowUp':
        newValue = Math.min(100, this.value + (e.shiftKey ? 10 : 5));
        break;
      case 'Home':
        newValue = 0;
        break;
      case 'End':
        newValue = 100;
        break;
      case 'PageDown':
        newValue = Math.max(0, this.value - 25);
        break;
      case 'PageUp':
        newValue = Math.min(100, this.value + 25);
        break;
      default:
        handled = false;
    }

    if (handled) {
      e.preventDefault();
      this.setValue(newValue);
    }
  }

  /**
   * Start dragging
   * @param {number} position
   */
  startDrag(position) {
    this.isDragging = true;
    this.element?.classList.add('dragging');
    this.handle?.classList.add('dragging');
    
    this.updateValue(position);
    
    // Add body class to prevent text selection
    document.body.style.userSelect = 'none';
  }

  /**
   * Stop dragging
   */
  stopDrag() {
    this.isDragging = false;
    this.element?.classList.remove('dragging');
    this.handle?.classList.remove('dragging');
    
    // Remove body class
    document.body.style.userSelect = '';
    
    // Save settings
    this.saveSettings();
    
    // Trigger change callback
    if (this.onChange) {
      this.onChange(this.value);
    }
  }

  /**
   * Get position from mouse/touch event
   * @param {MouseEvent|Touch} e
   * @returns {number} Position percentage (0-100)
   */
  getPositionFromEvent(e) {
    if (!this.slider) return 0;
    
    const rect = this.slider.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    
    return percentage;
  }

  /**
   * Update brightness value
   * @param {number} position - Position percentage (0-100)
   */
  updateValue(position) {
    const newValue = Math.round(position);
    this.setValue(newValue);
  }

  /**
   * Set brightness value
   * @param {number} value - Brightness value (0-100)
   */
  setValue(value) {
    const clampedValue = Math.max(0, Math.min(100, value));
    const oldValue = this.value;
    
    this.value = clampedValue;
    
    // Update visual elements
    this.updateVisuals();
    
    // Apply brightness
    this.applyBrightness();
    
    // Update range data attribute
    this.updateRangeAttribute();
    
    // Trigger immediate callback for smooth updates
    if (this.onChange && oldValue !== this.value) {
      this.onChange(this.value);
    }
  }

  /**
   * Update visual elements
   */
  updateVisuals() {
    if (this.fill) {
      this.fill.style.width = `${this.value}%`;
    }
    
    if (this.handle) {
      this.handle.style.left = `${this.value}%`;
    }
    
    if (this.percentage) {
      this.percentage.textContent = `${this.value}%`;
      this.percentage.classList.add('value-changed');
      
      // Remove animation class after animation completes
      setTimeout(() => {
        this.percentage?.classList.remove('value-changed');
      }, 300);
    }
    
    if (this.slider) {
      this.slider.setAttribute('aria-valuenow', this.value.toString());
      this.slider.setAttribute('aria-valuetext', `${this.value} percent brightness`);
    }
  }

  /**
   * Apply brightness to page content
   */
  applyBrightness() {
    document.documentElement.style.setProperty('--brightness', `${this.value}%`);
  }

  /**
   * Update range data attribute for styling
   */
  updateRangeAttribute() {
    if (!this.element) return;
    
    const range = this.getBrightnessRange();
    this.element.setAttribute('data-range', range);
    
    if (this.onRangeChange) {
      this.onRangeChange(range);
    }
  }

  /**
   * Get brightness range category
   * @returns {string} Range category (low, balanced, high)
   */
  getBrightnessRange() {
    if (this.value <= 20) return 'low';
    if (this.value >= 80) return 'high';
    return 'balanced';
  }

  /**
   * Auto-adjust brightness based on time of day
   */
  autoAdjustBrightness() {
    if (!this.autoAdjust) return;
    
    const hour = new Date().getHours();
    let suggestedBrightness;
    
    if (hour >= 6 && hour < 9) {          // Morning
      suggestedBrightness = 70;
    } else if (hour >= 9 && hour < 18) {  // Day
      suggestedBrightness = 85;
    } else if (hour >= 18 && hour < 22) { // Evening
      suggestedBrightness = 50;
    } else {                              // Night
      suggestedBrightness = 25;
    }
    
    // Only auto-adjust if difference is significant
    if (Math.abs(this.value - suggestedBrightness) > 10) {
      this.setValue(suggestedBrightness);
    }
  }

  /**
   * Start auto-brightness adjustment
   */
  startAutoAdjustment() {
    if (this.autoAdjustInterval) {
      clearInterval(this.autoAdjustInterval);
    }
    
    // Check every 15 minutes
    this.autoAdjustInterval = setInterval(() => {
      this.autoAdjustBrightness();
    }, 15 * 60 * 1000);
    
    // Initial check
    this.autoAdjustBrightness();
  }

  /**
   * Stop auto-brightness adjustment
   */
  stopAutoAdjustment() {
    if (this.autoAdjustInterval) {
      clearInterval(this.autoAdjustInterval);
      this.autoAdjustInterval = null;
    }
  }

  /**
   * Set auto-adjust preference
   * @param {boolean} enabled
   */
  setAutoAdjust(enabled) {
    this.autoAdjust = enabled;
    
    if (enabled) {
      this.startAutoAdjustment();
    } else {
      this.stopAutoAdjustment();
    }
    
    this.saveSettings();
  }

  /**
   * Load settings from localStorage
   */
  loadSettings() {
    try {
      const settings = localStorage.getItem('brightness-settings');
      if (settings) {
        const parsed = JSON.parse(settings);
        this.value = Math.max(0, Math.min(100, parsed.value || 70));
        this.autoAdjust = parsed.autoAdjust || false;
      }
    } catch (error) {
      console.warn('Failed to load brightness settings:', error);
      this.value = 70;
      this.autoAdjust = false;
    }
  }

  /**
   * Save settings to localStorage
   */
  saveSettings() {
    try {
      const settings = {
        value: this.value,
        autoAdjust: this.autoAdjust,
        lastUpdated: Date.now()
      };
      localStorage.setItem('brightness-settings', JSON.stringify(settings));
    } catch (error) {
      console.warn('Failed to save brightness settings:', error);
    }
  }

  /**
   * Destroy the brightness controller
   */
  destroy() {
    this.stopAutoAdjustment();
    
    if (this.element) {
      this.element.remove();
    }
    
    // Reset brightness
    document.documentElement.style.removeProperty('--brightness');
    
    // Clean up references
    this.element = null;
    this.slider = null;
    this.handle = null;
    this.fill = null;
    this.percentage = null;
    this.icons = { sun: null, moon: null };
  }

  /**
   * Get current brightness value
   * @returns {number}
   */
  getValue() {
    return this.value;
  }

  /**
   * Check if auto-adjust is enabled
   * @returns {boolean}
   */
  isAutoAdjustEnabled() {
    return this.autoAdjust;
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BrightnessController;
}

// Global export for browser
if (typeof window !== 'undefined') {
  window.BrightnessController = BrightnessController;
}

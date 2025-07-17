/**
 * GoodBooks Recommender Dashboard - Optimized Utility Functions
 * High-performance helper functions with memoization and efficient algorithms
 */

/**
 * Optimized Utility Functions with Memoization
 */
const Utils = {
  // Memoization cache for expensive operations
  _memoCache: new Map(),
  _memoMaxSize: 1000,

  /**
   * Memoized function wrapper for expensive computations
   */
  memoize(fn, keyFn = (...args) => JSON.stringify(args)) {
    return (...args) => {
      const key = keyFn(...args);
      
      if (this._memoCache.has(key)) {
        return this._memoCache.get(key);
      }
      
      // Implement LRU cache behavior
      if (this._memoCache.size >= this._memoMaxSize) {
        const firstKey = this._memoCache.keys().next().value;
        this._memoCache.delete(firstKey);
      }
      
      const result = fn(...args);
      this._memoCache.set(key, result);
      return result;
    };
  },

  /**
   * High-performance debounce with immediate execution option
   */
  debounce(func, wait, immediate = false) {
    let timeout;
    let lastArgs;
    let lastThis;
    
    const later = () => {
      timeout = null;
      if (!immediate && lastArgs) {
        func.apply(lastThis, lastArgs);
        lastArgs = null;
      }
    };

    const debounced = function(...args) {
      lastArgs = args;
      lastThis = this;
      
      const callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      
      if (callNow) {
        func.apply(this, args);
      }
    };

    debounced.cancel = () => {
      clearTimeout(timeout);
      timeout = null;
      lastArgs = null;
    };

    return debounced;
  },

  /**
   * Optimized throttle with trailing execution
   */
  throttle(func, limit) {
    let inThrottle;
    let lastFunc;
    let lastRan;
    
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        lastRan = Date.now();
        inThrottle = true;
      } else {
        clearTimeout(lastFunc);
        lastFunc = setTimeout(() => {
          if ((Date.now() - lastRan) >= limit) {
            func.apply(this, args);
            lastRan = Date.now();
          }
        }, limit - (Date.now() - lastRan));
      }
    };
  },

  /**
   * Format numbers with appropriate suffixes
   */
  formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  },

  /**
   * Format bytes to human readable
   */
  formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  },

  /**
   * Format duration in milliseconds to human readable
   */
  formatDuration(ms) {
    if (ms < 1000) {
      return `${ms}ms`;
    }
    if (ms < 60000) {
      return `${(ms / 1000).toFixed(1)}s`;
    }
    if (ms < 3600000) {
      return `${(ms / 60000).toFixed(1)}m`;
    }
    return `${(ms / 3600000).toFixed(1)}h`;
  },

  /**
   * Format date to relative time
   */
  formatRelativeTime(date) {
    const now = new Date();
    const diff = now - new Date(date);
    
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return `${seconds} second${seconds > 1 ? 's' : ''} ago`;
  },

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  /**
   * Strip HTML tags
   */
  stripHtml(html) {
    const div = document.createElement('div');
    div.innerHTML = html;
    return div.textContent || div.innerText || '';
  },

  /**
   * Truncate text with ellipsis
   */
  truncate(text, maxLength, suffix = '...') {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - suffix.length) + suffix;
  },

  /**
   * Capitalize first letter
   */
  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  },

  /**
   * Convert camelCase to Title Case
   */
  camelToTitle(str) {
    return str
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (match) => match.toUpperCase())
      .trim();
  },

  /**
   * Generate random ID
   */
  generateId(prefix = 'id') {
    return `${prefix}-${Math.random().toString(36).substring(2, 9)}`;
  },

  /**
   * Deep clone object
   */
  deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => this.deepClone(item));
    if (typeof obj === 'object') {
      const clonedObj = {};
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          clonedObj[key] = this.deepClone(obj[key]);
        }
      }
      return clonedObj;
    }
  },

  /**
   * Check if object is empty
   */
  isEmpty(obj) {
    if (obj == null) return true;
    if (Array.isArray(obj) || typeof obj === 'string') return obj.length === 0;
    return Object.keys(obj).length === 0;
  },

  /**
   * Get query parameters from URL
   */
  getQueryParams() {
    return new URLSearchParams(window.location.search);
  },

  /**
   * Set query parameter in URL
   */
  setQueryParam(key, value) {
    const url = new URL(window.location);
    url.searchParams.set(key, value);
    window.history.pushState({}, '', url);
  },

  /**
   * Remove query parameter from URL
   */
  removeQueryParam(key) {
    const url = new URL(window.location);
    url.searchParams.delete(key);
    window.history.pushState({}, '', url);
  },

  /**
   * Validate email format
   */
  isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  },

  /**
   * Validate URL format
   */
  isValidUrl(url) {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Generate color palette
   */
  generateColorPalette(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
      const hue = (i * 360) / count;
      colors.push(`hsl(${hue}, 70%, 50%)`);
    }
    return colors;
  },

  /**
   * Calculate color luminance
   */
  getLuminance(hex) {
    const rgb = this.hexToRgb(hex);
    if (!rgb) return 0;
    
    const { r, g, b } = rgb;
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  },

  /**
   * Convert hex to RGB
   */
  hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  },

  /**
   * Get contrast color (black or white)
   */
  getContrastColor(hex) {
    const luminance = this.getLuminance(hex);
    return luminance > 0.5 ? '#000000' : '#ffffff';
  }
};

/**
 * Local Storage Manager
 */
class StorageManager {
  constructor(prefix = 'goodbooks') {
    this.prefix = prefix;
  }

  /**
   * Set item in localStorage
   */
  set(key, value) {
    try {
      const item = {
        value,
        timestamp: Date.now(),
        expires: null
      };
      localStorage.setItem(`${this.prefix}-${key}`, JSON.stringify(item));
      return true;
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
      return false;
    }
  }

  /**
   * Get item from localStorage
   */
  get(key, defaultValue = null) {
    try {
      const itemStr = localStorage.getItem(`${this.prefix}-${key}`);
      if (!itemStr) return defaultValue;
      
      const item = JSON.parse(itemStr);
      
      // Check if expired
      if (item.expires && Date.now() > item.expires) {
        this.remove(key);
        return defaultValue;
      }
      
      return item.value;
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return defaultValue;
    }
  }

  /**
   * Set item with expiration
   */
  setWithExpiry(key, value, ttlMs) {
    try {
      const item = {
        value,
        timestamp: Date.now(),
        expires: Date.now() + ttlMs
      };
      localStorage.setItem(`${this.prefix}-${key}`, JSON.stringify(item));
      return true;
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
      return false;
    }
  }

  /**
   * Remove item from localStorage
   */
  remove(key) {
    try {
      localStorage.removeItem(`${this.prefix}-${key}`);
      return true;
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
      return false;
    }
  }

  /**
   * Clear all items with prefix
   */
  clear() {
    try {
      const keys = Object.keys(localStorage).filter(key => 
        key.startsWith(`${this.prefix}-`)
      );
      keys.forEach(key => localStorage.removeItem(key));
      return true;
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
      return false;
    }
  }

  /**
   * Get all keys with prefix
   */
  keys() {
    return Object.keys(localStorage)
      .filter(key => key.startsWith(`${this.prefix}-`))
      .map(key => key.replace(`${this.prefix}-`, ''));
  }
}

/**
 * Event Emitter
 */
class EventEmitter {
  constructor() {
    this.events = {};
  }

  on(event, callback) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);
  }

  off(event, callback) {
    if (!this.events[event]) return;
    
    const index = this.events[event].indexOf(callback);
    if (index > -1) {
      this.events[event].splice(index, 1);
    }
  }

  emit(event, data) {
    if (!this.events[event]) return;
    
    this.events[event].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in event listener for '${event}':`, error);
      }
    });
  }

  once(event, callback) {
    const onceCallback = (data) => {
      callback(data);
      this.off(event, onceCallback);
    };
    this.on(event, onceCallback);
  }

  removeAllListeners(event) {
    if (event) {
      delete this.events[event];
    } else {
      this.events = {};
    }
  }
}

/**
 * High-Performance Monitor with Resource Tracking
 */
class PerformanceMonitor {
  constructor(options = {}) {
    this.marks = new Map();
    this.measures = new Map();
    this.resourceMetrics = new Map();
    this.maxHistorySize = options.maxHistorySize || 100;
    this.autoCleanup = options.autoCleanup !== false;
    
    // Use high-resolution time when available
    this.now = performance.now ? performance.now.bind(performance) : Date.now;
    
    if (this.autoCleanup) {
      this._setupAutoCleanup();
    }
  }

  /**
   * Setup automatic cleanup of old measurements
   */
  _setupAutoCleanup() {
    setInterval(() => {
      if (this.measures.size > this.maxHistorySize) {
        const entries = Array.from(this.measures.entries());
        const toDelete = entries.slice(0, entries.length - this.maxHistorySize);
        toDelete.forEach(([key]) => this.measures.delete(key));
      }
    }, 60000); // Cleanup every minute
  }

  /**
   * Start timing with optional resource tracking
   */
  start(name, trackResources = false) {
    const startTime = this.now();
    
    this.marks.set(name, {
      startTime,
      trackResources,
      resourcesStart: trackResources ? this._captureResourceMetrics() : null
    });
  }

  /**
   * End timing and return comprehensive metrics
   */
  end(name) {
    const endTime = this.now();
    const markData = this.marks.get(name);
    
    if (!markData) {
      console.warn(`No start mark found for '${name}'`);
      return null;
    }
    
    const duration = endTime - markData.startTime;
    const metrics = {
      duration,
      startTime: markData.startTime,
      endTime
    };
    
    // Add resource metrics if tracking was enabled
    if (markData.trackResources && markData.resourcesStart) {
      const resourcesEnd = this._captureResourceMetrics();
      metrics.resources = this._calculateResourceDiff(markData.resourcesStart, resourcesEnd);
    }
    
    this.measures.set(name, metrics);
    this.marks.delete(name);
    
    return metrics;
  }

  /**
   * Capture current resource metrics
   */
  _captureResourceMetrics() {
    const memory = performance.memory ? {
      usedJSHeapSize: performance.memory.usedJSHeapSize,
      totalJSHeapSize: performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
    } : null;

    return {
      memory,
      timestamp: this.now()
    };
  }

  /**
   * Calculate resource usage difference
   */
  _calculateResourceDiff(start, end) {
    const diff = {};
    
    if (start.memory && end.memory) {
      diff.memoryDelta = end.memory.usedJSHeapSize - start.memory.usedJSHeapSize;
      diff.memoryPeak = Math.max(start.memory.usedJSHeapSize, end.memory.usedJSHeapSize);
    }
    
    return diff;
  }

  /**
   * Get comprehensive performance statistics
   */
  getStats() {
    const durations = Array.from(this.measures.values()).map(m => m.duration);
    
    if (durations.length === 0) {
      return null;
    }

    durations.sort((a, b) => a - b);
    
    return {
      count: durations.length,
      min: durations[0],
      max: durations[durations.length - 1],
      mean: durations.reduce((a, b) => a + b, 0) / durations.length,
      median: durations[Math.floor(durations.length / 2)],
      p95: durations[Math.floor(durations.length * 0.95)],
      p99: durations[Math.floor(durations.length * 0.99)]
    };
  }

  /**
   * Time a function execution with automatic cleanup
   */
  async timeFunction(name, fn, options = {}) {
    const measureKey = `${name}_${Date.now()}`;
    this.start(measureKey, options.trackResources);
    
    try {
      const result = await fn();
      const metrics = this.end(measureKey);
      
      if (options.logResults !== false) {
        console.log(`${name} completed in ${metrics.duration.toFixed(2)}ms`, metrics);
      }
      
      return { result, metrics };
    } catch (error) {
      this.end(measureKey);
      throw error;
    }
  }

  /**
   * Clear all measurements and marks
   */
  clear() {
    this.marks.clear();
    this.measures.clear();
    this.resourceMetrics.clear();
  }
}

/**
 * Logger
 */
class Logger {
  constructor(name = 'Dashboard') {
    this.name = name;
    this.levels = {
      DEBUG: 0,
      INFO: 1,
      WARN: 2,
      ERROR: 3
    };
    this.currentLevel = this.levels.INFO;
  }

  setLevel(level) {
    this.currentLevel = this.levels[level.toUpperCase()] || this.levels.INFO;
  }

  log(level, message, ...args) {
    if (this.levels[level] >= this.currentLevel) {
      const timestamp = new Date().toISOString();
      const prefix = `[${timestamp}] [${this.name}] [${level}]`;
      
      switch (level) {
        case 'ERROR':
          console.error(prefix, message, ...args);
          break;
        case 'WARN':
          console.warn(prefix, message, ...args);
          break;
        case 'DEBUG':
          console.debug(prefix, message, ...args);
          break;
        default:
          console.log(prefix, message, ...args);
      }
    }
  }

  debug(message, ...args) {
    this.log('DEBUG', message, ...args);
  }

  info(message, ...args) {
    this.log('INFO', message, ...args);
  }

  warn(message, ...args) {
    this.log('WARN', message, ...args);
  }

  error(message, ...args) {
    this.log('ERROR', message, ...args);
  }
}

// Global instances
window.Utils = Utils;
window.StorageManager = StorageManager;
window.EventEmitter = EventEmitter;
window.PerformanceMonitor = PerformanceMonitor;
window.Logger = Logger;

// Create global instances
window.storage = new StorageManager('goodbooks');
window.events = new EventEmitter();
window.performance = new PerformanceMonitor();
window.logger = new Logger('Dashboard');

console.log('[Utils] Utility functions and classes initialized');

/**
 * 🎛️ Dashboard State Management
 * Chain-of-Thought: Manage UI state, theme, layout, and AI mode
 * Memory: Persistent dashboard preferences and animation states
 * Forward-Thinking: Extensible for new UI features and AI capabilities
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { AnalyticsService } from '../../utils/api'

// Type definitions
export interface DashboardState {
  isInitialized: boolean
  theme: 'light' | 'dark' | 'auto'
  brightness: number
  layout: 'grid' | 'list' | 'carousel'
  aiMode: 'basic' | 'enhanced' | 'neural'
  animations: boolean
  sidebarCollapsed: boolean
  loading: boolean
  error: string | null
  
  // Memory: Component states
  componentStates: Record<string, any>
  lastInteraction: number
  
  // Performance metrics
  performanceMetrics: {
    loadTime: number
    renderTime: number
    apiLatency: Record<string, number>
    memoryUsage: number | null
    lastUpdated: number
  }
  performancePanelVisible: boolean
  
  // Forward-Thinking: Future UI features
  voiceEnabled: boolean
  accessibilityMode: boolean
  performanceMode: 'smooth' | 'performance' | 'battery'
}

const initialState: DashboardState = {
  isInitialized: false,
  theme: 'dark',
  brightness: 75,
  layout: 'grid',
  aiMode: 'enhanced',
  animations: true,
  sidebarCollapsed: false,
  loading: false,
  error: null,
  componentStates: {},
  lastInteraction: Date.now(),
  
  performanceMetrics: {
    loadTime: 0,
    renderTime: 0,
    apiLatency: {},
    memoryUsage: null,
    lastUpdated: Date.now()
  },
  performancePanelVisible: false,
  
  voiceEnabled: false,
  accessibilityMode: false,
  performanceMode: 'smooth'
}

/**
 * Async thunk for dashboard initialization
 * Chain-of-Thought: Load saved preferences and initialize AI systems
 */
export const initializeDashboard = createAsyncThunk(
  'dashboard/initialize',
  async () => {
    try {
      // Record start time for performance metrics
      const startTime = performance.now()
      
      // Memory: Load saved preferences
      const savedPreferences = localStorage.getItem('dashboard_preferences')
      const preferences = savedPreferences ? JSON.parse(savedPreferences) : {}
      
      // Load performance mode based on device capabilities
      const performanceMode = detectOptimalPerformanceMode()
      
      // Simulate AI initialization
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Calculate load time
      const loadTime = performance.now() - startTime
      
      return {
        ...preferences,
        isInitialized: true,
        lastInteraction: Date.now(),
        performanceMetrics: {
          loadTime,
          renderTime: 0,
          apiLatency: {},
          memoryUsage: null,
          lastUpdated: Date.now()
        },
        performanceMode
      }
    } catch (error) {
      throw new Error(`Dashboard initialization failed: ${error}`)
    }
  }
)

/**
 * Async thunk for tracking performance metrics
 * Chain-of-Thought: Collect metrics for optimization opportunities
 * Time Complexity: O(1) operation for metrics collection
 */
export const trackPerformanceMetrics = createAsyncThunk(
  'dashboard/trackPerformanceMetrics',
  async () => {
    try {
      // Get memory usage if available in browser
      const memoryInfo = (performance as any).memory
      const memoryUsage = memoryInfo ? memoryInfo.usedJSHeapSize / (1024 * 1024) : null
      
      // Get API performance metrics using the analytics dashboard endpoint
      const analyticsResponse = await AnalyticsService.getDashboardData()
      const performanceData = (analyticsResponse as any)?.performance || {}
      
      return {
        renderTime: performanceData.averageRenderTime || 0,
        apiLatency: performanceData.endpointLatency || {},
        memoryUsage,
        lastUpdated: Date.now()
      }
    } catch (error) {
      console.error('Failed to track performance metrics:', error)
      // Return empty metrics, don't fail the action
      return {
        renderTime: 0,
        apiLatency: {},
        memoryUsage: null,
        lastUpdated: Date.now()
      }
    }
  }
)

/**
 * Utility function to detect optimal performance mode based on device
 * Chain-of-Thought: Set performance defaults based on device capabilities
 */
function detectOptimalPerformanceMode(): 'smooth' | 'performance' | 'battery' {
  // Check if running in browser
  if (typeof window === 'undefined') return 'smooth'
  
  // Check if device is mobile
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  
  // Check if device has low memory (if memory API is available)
  const hasLowMemory = (navigator as any).deviceMemory && (navigator as any).deviceMemory < 4
  
  // Check if device is in battery saving mode (if battery API is available)
  const isBatterySaving = (navigator as any).getBattery && (navigator as any).getBattery().then((battery: any) => {
    return battery.charging === false && battery.level < 0.2
  }).catch(() => false)
  
  if (isMobile || hasLowMemory) return 'performance'
  if (isBatterySaving) return 'battery'
  return 'smooth'
}

/**
 * Dashboard slice with reducers and actions
 */
const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    // Loading state
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload
    },
    
    // Theme and appearance
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload
      state.lastInteraction = Date.now()
      
      // Persist theme preference
      try {
        const preferences = localStorage.getItem('dashboard_preferences')
        const parsed = preferences ? JSON.parse(preferences) : {}
        localStorage.setItem('dashboard_preferences', JSON.stringify({
          ...parsed,
          theme: action.payload
        }))
      } catch (e) {
        console.error('Failed to save theme preference:', e)
      }
    },
    
    setBrightness: (state, action: PayloadAction<number>) => {
      state.brightness = Math.max(10, Math.min(100, action.payload))
      state.lastInteraction = Date.now()
    },
    
    // Layout and UI
    setLayout: (state, action: PayloadAction<'grid' | 'list' | 'carousel'>) => {
      state.layout = action.payload
      state.lastInteraction = Date.now()
    },
    
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed
      state.lastInteraction = Date.now()
    },
    
    toggleAnimations: (state) => {
      state.animations = !state.animations
      state.lastInteraction = Date.now()
    },
    
    // AI mode management
    setAIMode: (state, action: PayloadAction<'basic' | 'enhanced' | 'neural'>) => {
      state.aiMode = action.payload
      state.lastInteraction = Date.now()
    },
    
    // Memory: Component state management
    setComponentState: (state, action: PayloadAction<{ componentId: string; state: any }>) => {
      state.componentStates[action.payload.componentId] = action.payload.state
      state.lastInteraction = Date.now()
    },
    
    clearComponentState: (state, action: PayloadAction<string>) => {
      delete state.componentStates[action.payload]
    },
    
    // Performance tracking
    updateRenderTime: (state, action: PayloadAction<number>) => {
      state.performanceMetrics.renderTime = action.payload
      state.performanceMetrics.lastUpdated = Date.now()
    },
    
    updateApiLatency: (state, action: PayloadAction<{ endpoint: string; latency: number }>) => {
      state.performanceMetrics.apiLatency[action.payload.endpoint] = action.payload.latency
      state.performanceMetrics.lastUpdated = Date.now()
    },
    
    // Forward-Thinking: Future features
    toggleVoice: (state) => {
      state.voiceEnabled = !state.voiceEnabled
      state.lastInteraction = Date.now()
    },
    
    toggleAccessibilityMode: (state) => {
      state.accessibilityMode = !state.accessibilityMode
      state.lastInteraction = Date.now()
    },
    
    togglePerformancePanel: (state) => {
      state.performancePanelVisible = !state.performancePanelVisible
      state.lastInteraction = Date.now()
    },
    
    setPerformanceMode: (state, action: PayloadAction<'smooth' | 'performance' | 'battery'>) => {
      state.performanceMode = action.payload
      state.lastInteraction = Date.now()
    },
    
    // Error handling
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    
    clearError: (state) => {
      state.error = null
    }
  },
  
  extraReducers: (builder) => {
    builder
      .addCase(initializeDashboard.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(initializeDashboard.fulfilled, (state, action) => {
        state.loading = false
        Object.assign(state, action.payload)
      })
      .addCase(initializeDashboard.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Initialization failed'
        // Fallback to basic mode
        state.aiMode = 'basic'
        state.isInitialized = true
      })
      .addCase(trackPerformanceMetrics.fulfilled, (state, action) => {
        state.performanceMetrics = {
          ...state.performanceMetrics,
          ...action.payload
        }
      })
  }
})

// Export actions
export const {
  setTheme,
  setBrightness,
  setLayout,
  toggleSidebar,
  toggleAnimations,
  setAIMode,
  setComponentState,
  clearComponentState,
  toggleVoice,
  toggleAccessibilityMode,
  togglePerformancePanel,
  setPerformanceMode,
  updateRenderTime,
  updateApiLatency,
  setError,
  clearError,
  setLoading
} = dashboardSlice.actions

// Selectors for optimized component access
export const selectDashboardState = (state: { dashboard: DashboardState }) => state.dashboard
export const selectTheme = (state: { dashboard: DashboardState }) => state.dashboard.theme
export const selectAIMode = (state: { dashboard: DashboardState }) => state.dashboard.aiMode
export const selectPerformanceMode = (state: { dashboard: DashboardState }) => state.dashboard.performanceMode
export const selectPerformanceMetrics = (state: { dashboard: DashboardState }) => state.dashboard.performanceMetrics
export const selectPerformancePanelVisible = (state: { dashboard: DashboardState }) => state.dashboard.performancePanelVisible
export const selectComponentState = (componentId: string) => 
  (state: { dashboard: DashboardState }) => state.dashboard.componentStates[componentId]

export default dashboardSlice.reducer

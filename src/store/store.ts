/**
 * 🏪 Redux Store Configuration
 * Production-grade store setup with proper typing
 */

import { configureStore } from '@reduxjs/toolkit'

// Create a simple initial state
const initialState = {
  dashboard: {
    isInitialized: false,
    theme: 'dark' as 'light' | 'dark',
    aiMode: 'enhanced' as 'basic' | 'enhanced' | 'experimental',
    layout: 'grid' as 'grid' | 'list' | 'masonry',
    performanceMode: 'performance' as 'performance' | 'battery',
    performancePanelVisible: false
  },
  ui: {
    theme: 'dark' as 'light' | 'dark',
    isLoading: false
  }
}

// Simple reducer functions
const dashboardReducer = (state = initialState.dashboard, action: any) => {
  switch (action.type) {
    case 'dashboard/initializeDashboard':
      return { ...state, isInitialized: true }
    case 'dashboard/trackPerformanceMetrics':
      console.log('📊 Tracking performance metrics')
      return state
    case 'dashboard/togglePerformancePanel':
      return { ...state, performancePanelVisible: !state.performancePanelVisible }
    default:
      return state
  }
}

const uiReducer = (state = initialState.ui, action: any) => {
  switch (action.type) {
    case 'ui/setTheme':
      return { ...state, theme: action.payload }
    case 'ui/setLoading':
      return { ...state, isLoading: action.payload }
    default:
      return state
  }
}

export const store = configureStore({
  reducer: {
    dashboard: dashboardReducer,
    ui: uiReducer
  }
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// Action creators
export const initializeDashboard = () => ({ type: 'dashboard/initializeDashboard' })
export const trackPerformanceMetrics = () => ({ type: 'dashboard/trackPerformanceMetrics' })
export const togglePerformancePanel = () => ({ type: 'dashboard/togglePerformancePanel' })
export const setTheme = (theme: 'light' | 'dark') => ({ type: 'ui/setTheme', payload: theme })
export const setLoading = (loading: boolean) => ({ type: 'ui/setLoading', payload: loading })

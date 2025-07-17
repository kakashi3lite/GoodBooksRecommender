/**
 * 🧠 Redux Store Configuration
 * Chain-of-Thought: Centralized state management for AI recommendations and UI state
 * Memory: Persistent state across sessions with localStorage integration
 * Forward-Thinking: Extensible store structure for future features
 */

import { configureStore } from '@reduxjs/toolkit'
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'

// Slice imports
import dashboardSlice from './dashboard/dashboardSlice'
import booksSlice from './books/booksSlice'
import aiSlice from './ai/aiSlice'
import userSlice from './user/userSlice'

// Forward-Thinking: Future feature slices
import notesSlice from './features/notesSlice'
import communitySlice from './features/communitySlice'
import analyticsSlice from './features/analyticsSlice'

/**
 * Configure the Redux store with middleware and devtools
 * Memory: Enable state persistence and restore functionality
 */
export const store = configureStore({
  reducer: {
    dashboard: dashboardSlice,
    books: booksSlice,
    ai: aiSlice,
    user: userSlice,
    // Forward-Thinking: Future features
    notes: notesSlice,
    community: communitySlice,
    analytics: analyticsSlice
  },
  
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        ignoredPaths: ['ai.modelInstance', 'dashboard.animationRefs']
      }
    }),
    
  devTools: process.env.NODE_ENV !== 'production' && {
    name: 'Futuristic Dashboard',
    trace: true,
    traceLimit: 25
  }
})

// Type definitions for TypeScript integration
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// Typed hooks for components
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector

/**
 * Memory: Store state persistence utility
 * Chain-of-Thought: Save critical state to localStorage for session continuity
 */
export const saveState = (state: Partial<RootState>) => {
  try {
    const serializedState = JSON.stringify({
      dashboard: {
        theme: state.dashboard?.theme,
        brightness: state.dashboard?.brightness,
        layout: state.dashboard?.layout,
        aiMode: state.dashboard?.aiMode
      },
      user: state.user,
      // Only save essential state, not large data structures
    })
    localStorage.setItem('dashboard_state', serializedState)
  } catch (error) {
    console.warn('Failed to save state to localStorage:', error)
  }
}

export const loadState = (): Partial<RootState> | undefined => {
  try {
    const serializedState = localStorage.getItem('dashboard_state')
    if (serializedState === null) {
      return undefined
    }
    return JSON.parse(serializedState)
  } catch (error) {
    console.warn('Failed to load state from localStorage:', error)
    return undefined
  }
}

// Memory: Auto-save state on changes
store.subscribe(() => {
  saveState(store.getState())
})

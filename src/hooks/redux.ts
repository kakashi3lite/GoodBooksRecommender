/**
 * 🪝 Redux Hooks for Type-Safe State Management
 * Chain-of-Thought: Provide type-safe hooks for component state access
 * Memory: Cached selectors for performance optimization
 * Forward-Thinking: Extensible hook patterns for future features
 */

import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'
import type { RootState, AppDispatch } from '../stores/store'

// Use throughout the app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector

// Custom hooks for common state selections
export const useDashboard = () => useAppSelector(state => state.dashboard)
export const useBooks = () => useAppSelector(state => state.books)
export const useAI = () => useAppSelector(state => state.ai)
export const useUser = () => useAppSelector(state => state.user)

// Forward-Thinking: Feature-specific hooks
export const useNotes = () => useAppSelector(state => state.notes)
export const useCommunity = () => useAppSelector(state => state.community)
export const useAnalytics = () => useAppSelector(state => state.analytics)

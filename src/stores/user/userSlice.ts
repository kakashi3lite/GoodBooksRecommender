/**
 * 👤 User State Management
 * Chain-of-Thought: Manage user profile, preferences, reading goals, and history
 * Memory: Persist user preferences across sessions via localStorage
 * Forward-Thinking: Extensible for RBAC, social features, and analytics
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { apiClient, API_ENDPOINTS } from '../../utils/api'

// ─── Types ────────────────────────────────────────────────────────────────

export interface ReadingGoal {
  id: string
  title: string
  type: 'count' | 'pages' | 'genre' | 'author'
  target: number
  current: number
  unit: string
  year: number
}

export interface UserProfile {
  id: string | null
  name: string
  email: string
  avatar?: string
  readingLevel: 'novice' | 'intermediate' | 'expert'
}

export interface UserPreferences {
  favoriteGenres: string[]
  preferredFormats: string[]
  readingGoal: number
  notifications: boolean
  privacy: 'public' | 'friends' | 'private'
}

export interface UserSliceState {
  profile: UserProfile
  preferences: UserPreferences
  goals: ReadingGoal[]
  readingHistory: string[]
  favorites: string[]
  loading: boolean
  error: string | null
}

// ─── Initial State ────────────────────────────────────────────────────────

const initialState: UserSliceState = {
  profile: {
    id: null,
    name: 'Reader',
    email: 'reader@goodbooks.app',
    readingLevel: 'intermediate'
  },
  preferences: {
    favoriteGenres: ['Fiction', 'Sci-Fi', 'Mystery'],
    preferredFormats: ['ebook', 'print'],
    readingGoal: 52,
    notifications: true,
    privacy: 'friends'
  },
  goals: [],
  readingHistory: [],
  favorites: [],
  loading: false,
  error: null
}

// ─── Async Thunks ──────────────────────────────────────────────────────────

/**
 * Fetch the current user's profile from the API.
 * Chain-of-Thought: Gracefully fall back to local defaults when the backend is down.
 */
export const fetchProfile = createAsyncThunk(
  'user/fetchProfile',
  async (_, { rejectWithValue }) => {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 4000)
      const data = await apiClient.get<any>(API_ENDPOINTS.user.profile())
      clearTimeout(timeout)
      return data
    } catch (error) {
      console.warn('[User] Backend unavailable, using local profile:', error)
      return rejectWithValue('Backend unavailable')
    }
  }
)

/**
 * Update user preferences (optimistic, persisted locally).
 */
export const updatePreferences = createAsyncThunk(
  'user/updatePreferences',
  async (preferences: Partial<UserPreferences>) => {
    try {
      await apiClient.put(API_ENDPOINTS.user.preferences(), preferences)
      return preferences
    } catch (error) {
      // Still apply locally even if the API is down — the user shouldn't lose their choices
      console.warn('[User] Could not sync preferences, applying locally:', error)
      return preferences
    }
  }
)

// ─── Slice ─────────────────────────────────────────────────────────────────

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setProfile: (state, action: PayloadAction<Partial<UserProfile>>) => {
      state.profile = { ...state.profile, ...action.payload }
    },

    setPreferences: (state, action: PayloadAction<Partial<UserPreferences>>) => {
      state.preferences = { ...state.preferences, ...action.payload }
    },

    addGoal: (state, action: PayloadAction<ReadingGoal>) => {
      state.goals = [action.payload, ...state.goals]
    },

    updateGoalProgress: (state, action: PayloadAction<{ id: string; current: number }>) => {
      const goal = state.goals.find((g) => g.id === action.payload.id)
      if (goal) {
        goal.current = Math.min(goal.target, Math.max(0, action.payload.current))
      }
    },

    removeGoal: (state, action: PayloadAction<string>) => {
      state.goals = state.goals.filter((g) => g.id !== action.payload)
    },

    toggleFavorite: (state, action: PayloadAction<string>) => {
      const id = action.payload
      state.favorites = state.favorites.includes(id)
        ? state.favorites.filter((f) => f !== id)
        : [...state.favorites, id]
    },

    addToHistory: (state, action: PayloadAction<string>) => {
      state.readingHistory = [
        action.payload,
        ...state.readingHistory.filter((id) => id !== action.payload)
      ].slice(0, 100)
    },

    resetUser: () => initialState
  },

  extraReducers: (builder) => {
    builder
      .addCase(fetchProfile.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.loading = false
        const data = action.payload as any
        if (data?.profile) {
          state.profile = { ...state.profile, ...data.profile }
        }
        if (data?.preferences) {
          state.preferences = { ...state.preferences, ...data.preferences }
        }
      })
      .addCase(fetchProfile.rejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as string) ?? 'Failed to load profile'
      })
      .addCase(updatePreferences.fulfilled, (state, action) => {
        state.preferences = { ...state.preferences, ...action.payload }
      })
  }
})

export const {
  setProfile,
  setPreferences,
  addGoal,
  updateGoalProgress,
  removeGoal,
  toggleFavorite,
  addToHistory,
  resetUser
} = userSlice.actions

// ─── Selectors ─────────────────────────────────────────────────────────────

export const selectUserProfile = (state: { user: UserSliceState }) => state.user.profile
export const selectUserPreferences = (state: { user: UserSliceState }) => state.user.preferences
export const selectReadingGoals = (state: { user: UserSliceState }) => state.user.goals
export const selectFavorites = (state: { user: UserSliceState }) => state.user.favorites
export const selectUserLoading = (state: { user: UserSliceState }) => state.user.loading

export default userSlice.reducer

/**
 * 👤 User State Management
 * Chain-of-Thought: Manage user profile, preferences, reading goals, and history
 * Memory: Persist user preferences across sessions via localStorage
 * Forward-Thinking: Extensible for RBAC, social features, and analytics
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { API_ENDPOINTS, apiClient } from '../../utils/api'

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
  /**
   * Mood vocabulary captured by onboarding ("Quick reads" → fast-paced, etc.).
   * Chain-of-Thought: onboarding used to ask for reading pace and silently
   * discard the answer — a question with no consequence erodes trust in every
   * other question. This is the field that makes the answer matter, and it
   * feeds the same mood dimension the recommender already scores (20%).
   */
  preferredMoods: string[]
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
  /** True once the user has created an account (local, graceful). */
  isAuthenticated: boolean
  /** True once the taste-onboarding quiz is complete. */
  hasCompletedOnboarding: boolean
  loading: boolean
  error: string | null
}

// ─── Persistence ─────────────────────────────────────────────────────────────

const STORAGE_KEY = 'goodbooks_user'

/** Reserved identity for "explore as guest" — never persisted to the server. */
const GUEST_EMAIL = 'reader@goodbooks.app'

interface PersistedUser {
  profile: UserProfile
  preferences: UserPreferences
  goals: ReadingGoal[]
  readingHistory: string[]
  favorites: string[]
  isAuthenticated: boolean
  hasCompletedOnboarding: boolean
}

/**
 * Write the reader's account to localStorage.
 * Chain-of-Thought: previously only `register`/`login`/`completeOnboarding`
 * called this, so a wishlist save, a goal change or a settings tweak lived in
 * memory only and silently reverted on the next load. `store.ts` now calls this
 * whenever the user slice changes, and the reducers above may still call it for
 * an immediate, synchronous write.
 */
export const persistUserState = (state: UserSliceState): void => {
  try {
    const payload: PersistedUser = {
      profile: state.profile,
      preferences: state.preferences,
      goals: state.goals,
      readingHistory: state.readingHistory,
      favorites: state.favorites,
      isAuthenticated: state.isAuthenticated,
      hasCompletedOnboarding: state.hasCompletedOnboarding
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
  } catch (error) {
    console.warn('[User] Failed to persist user state:', error)
  }
}

const restoreUser = (): Partial<UserSliceState> | undefined => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return undefined
    const parsed = JSON.parse(raw) as PersistedUser
    return {
      profile: parsed.profile,
      preferences: parsed.preferences,
      goals: parsed.goals ?? [],
      readingHistory: parsed.readingHistory ?? [],
      favorites: parsed.favorites ?? [],
      isAuthenticated: parsed.isAuthenticated,
      hasCompletedOnboarding: parsed.hasCompletedOnboarding
    }
  } catch (error) {
    console.warn('[User] Failed to restore user state:', error)
    return undefined
  }
}

// ─── Initial State ────────────────────────────────────────────────────────

const baseInitialState: UserSliceState = {
  profile: {
    id: null,
    name: 'Reader',
    email: 'reader@goodbooks.app',
    readingLevel: 'intermediate'
  },
  preferences: {
    favoriteGenres: ['Fiction', 'Science Fiction', 'Mystery'],
    preferredFormats: ['ebook', 'print'],
    preferredMoods: [],
    readingGoal: 24,
    notifications: true,
    privacy: 'friends'
  },
  goals: [],
  readingHistory: [],
  favorites: [],
  isAuthenticated: false,
  hasCompletedOnboarding: false,
  loading: false,
  error: null
}

const initialState: UserSliceState = { ...baseInitialState, ...restoreUser() }

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

/**
 * Push the local account to the database (best-effort).
 * Chain-of-Thought: the account must outlive the browser, so every mount (and
 * every onboarding completion) mirrors it into D1 through /api/accounts. The
 * import stays dynamic so the network/client code is not in the initial bundle.
 */
export const syncAccountToServer = createAsyncThunk(
  'user/syncAccountToServer',
  async (arg: { force?: boolean } | undefined, { getState }) => {
    const { user } = getState() as { user: UserSliceState }
    if (!user.isAuthenticated) return { synced: false }
    // Guests share the reserved `reader@goodbooks.app` identity — persisting it
    // would write one row for every anonymous visitor and let them collide.
    const email = user.profile.email.trim().toLowerCase()
    if (!email || email === GUEST_EMAIL) return { synced: false }
    const { syncUserAccount } = await import('../../lib/userRepository')
    return syncUserAccount(
      {
        email,
        name: user.profile.name,
        favoriteGenres: user.preferences.favoriteGenres,
        preferredMoods: user.preferences.preferredMoods,
        readingGoal: user.preferences.readingGoal,
        readingLevel: user.profile.readingLevel
      },
      { force: arg?.force === true }
    )
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

    // ── Auth & Onboarding ────────────────────────────────────────────────

    /**
     * Create an account (local-first). The backend /auth/register endpoint
     * will sync this in a later milestone; the app is fully usable today.
     */
    register: (state, action: PayloadAction<{ name: string; email: string }>) => {
      state.profile = {
        id: `u-${Date.now().toString(36)}`,
        name: action.payload.name.trim() || 'Reader',
        email: action.payload.email.trim() || 'reader@goodbooks.app',
        readingLevel: 'novice'
      }
      state.isAuthenticated = true
      state.error = null
      persistUserState(state)
    },

    /** Restore a previously created account. */
    login: (state, action: PayloadAction<{ email: string; name?: string }>) => {
      state.profile = {
        ...state.profile,
        name: action.payload.name ?? state.profile.name,
        email: action.payload.email.trim() || state.profile.email
      }
      state.isAuthenticated = true
      state.error = null
      persistUserState(state)
    },

    /** Sign out — returns to the onboarding/landing gate. */
    logout: (state) => {
      state.isAuthenticated = false
      state.hasCompletedOnboarding = false
      state.profile = { ...baseInitialState.profile }
      state.preferences = { ...baseInitialState.preferences }
      state.goals = []
      state.readingHistory = []
      state.favorites = []
      try {
        localStorage.removeItem(STORAGE_KEY)
        // The "gate shows once per session" flag exists to stop a storage-less
        // browser from re-gating on every reload — it must not survive an
        // explicit sign-out, or "Sign Out" would silently drop the reader into
        // the app as a guest.
        sessionStorage.removeItem('goodbooks_onboarded')
      } catch (error) {
        console.warn('[User] Failed to clear persisted user:', error)
      }
    },

    /**
     * Complete the taste-onboarding quiz. Merges preferences so the
     * personalization engine can rank recommendations immediately.
     */
    completeOnboarding: (
      state,
      action: PayloadAction<Partial<UserPreferences>>
    ) => {
      state.preferences = { ...state.preferences, ...action.payload }
      state.hasCompletedOnboarding = true
      state.error = null
      persistUserState(state)
    },

    resetUser: () => {
      try {
        localStorage.removeItem(STORAGE_KEY)
      } catch (error) {
        console.warn('[User] Failed to clear persisted user:', error)
      }
      return { ...baseInitialState }
    }
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
      .addCase(syncAccountToServer.fulfilled, (state, action) => {
        // Non-fatal: the app continues on local accounts either way
        if (action.payload.synced) {
          state.error = null
        }
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
  register,
  login,
  logout,
  completeOnboarding,
  resetUser
} = userSlice.actions

// ─── Selectors ─────────────────────────────────────────────────────────────

export const selectUserProfile = (state: { user: UserSliceState }) => state.user.profile
export const selectUserPreferences = (state: { user: UserSliceState }) => state.user.preferences
export const selectReadingGoals = (state: { user: UserSliceState }) => state.user.goals
export const selectFavorites = (state: { user: UserSliceState }) => state.user.favorites
export const selectUserLoading = (state: { user: UserSliceState }) => state.user.loading
export const selectIsAuthenticated = (state: { user: UserSliceState }) =>
  state.user.isAuthenticated
export const selectHasCompletedOnboarding = (state: { user: UserSliceState }) =>
  state.user.hasCompletedOnboarding

export default userSlice.reducer

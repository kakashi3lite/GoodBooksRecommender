/**
 * 📊 Analytics State Management
 * Chain-of-Thought: Manage reading statistics, genre breakdowns, and trends
 * Memory: Cache analytics data with timestamps
 * Forward-Thinking: Extensible for identity analytics and wrapped reports
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { AnalyticsService } from '../../utils/api'

// ─── Types ────────────────────────────────────────────────────────────────

export interface GenreDatum {
  genre: string
  count: number
}

export interface TrendDatum {
  month: string
  books: number
  pages: number
}

export interface ReadingStats {
  totalBooks: number
  totalPages: number
  totalHours: number
  averageRating: number
  currentStreak: number
  longestStreak: number
  booksThisYear: number
}

export interface AnalyticsSliceState {
  stats: ReadingStats
  genreBreakdown: GenreDatum[]
  trends: TrendDatum[]
  loading: boolean
  error: string | null
  lastUpdated: number | null
}

// ─── Initial State ────────────────────────────────────────────────────────

const initialState: AnalyticsSliceState = {
  stats: {
    totalBooks: 0,
    totalPages: 0,
    totalHours: 0,
    averageRating: 0,
    currentStreak: 0,
    longestStreak: 0,
    booksThisYear: 0
  },
  genreBreakdown: [],
  trends: [],
  loading: false,
  error: null,
  lastUpdated: null
}

// ─── Async Thunks ──────────────────────────────────────────────────────────

/** Fetch the full reading analytics payload. */
export const fetchReadingAnalytics = createAsyncThunk(
  'analytics/fetchReadingAnalytics',
  async (_, { rejectWithValue }) => {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 4000)
      const data = await AnalyticsService.getReadingAnalytics()
      clearTimeout(timeout)
      return data as Partial<AnalyticsSliceState>
    } catch (error) {
      console.warn('[Analytics] Backend unavailable:', error)
      return rejectWithValue('Backend unavailable')
    }
  }
)

// ─── Slice ─────────────────────────────────────────────────────────────────

const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    setStats: (state, action: PayloadAction<Partial<ReadingStats>>) => {
      state.stats = { ...state.stats, ...action.payload }
    },
    setGenreBreakdown: (state, action: PayloadAction<GenreDatum[]>) => {
      state.genreBreakdown = action.payload
    },
    setTrends: (state, action: PayloadAction<TrendDatum[]>) => {
      state.trends = action.payload
    },
    clearAnalytics: (state) => {
      state.stats = initialState.stats
      state.genreBreakdown = []
      state.trends = []
      state.lastUpdated = null
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchReadingAnalytics.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchReadingAnalytics.fulfilled, (state, action) => {
        state.loading = false
        state.stats = { ...state.stats, ...action.payload.stats }
        state.genreBreakdown = action.payload.genreBreakdown ?? state.genreBreakdown
        state.trends = action.payload.trends ?? state.trends
        state.lastUpdated = Date.now()
      })
      .addCase(fetchReadingAnalytics.rejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as string) ?? 'Failed to load analytics'
      })
  }
})

export const { setStats, setGenreBreakdown, setTrends, clearAnalytics } = analyticsSlice.actions

// ─── Selectors ─────────────────────────────────────────────────────────────

export const selectReadingStats = (state: { analytics: AnalyticsSliceState }) =>
  state.analytics.stats
export const selectGenreBreakdown = (state: { analytics: AnalyticsSliceState }) =>
  state.analytics.genreBreakdown
export const selectTrends = (state: { analytics: AnalyticsSliceState }) => state.analytics.trends
export const selectAnalyticsLoading = (state: { analytics: AnalyticsSliceState }) =>
  state.analytics.loading

export default analyticsSlice.reducer


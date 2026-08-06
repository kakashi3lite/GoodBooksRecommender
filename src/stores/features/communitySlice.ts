/**
 * 👥 Community State Management
 * Chain-of-Thought: Manage community posts, comments, and discussions
 * Memory: Cache posts for instant browsing
 * Forward-Thinking: Extensible for book clubs and social features
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { CommunityService } from '../../utils/api'

// ─── Types ────────────────────────────────────────────────────────────────

export interface CommunityPost {
  id: string
  title: string
  content: string
  author: string
  authorId: string
  bookId?: string
  bookTitle?: string
  tags: string[]
  likes: number
  comments: CommunityComment[]
  createdAt: number
}

export interface CommunityComment {
  id: string
  content: string
  author: string
  createdAt: number
}

export interface CommunitySliceState {
  posts: CommunityPost[]
  loading: boolean
  error: string | null
}

// ─── Initial State ────────────────────────────────────────────────────────

const initialState: CommunitySliceState = {
  posts: [],
  loading: false,
  error: null
}

// ─── Async Thunks ──────────────────────────────────────────────────────────

/** Fetch community posts. */
export const fetchPosts = createAsyncThunk(
  'community/fetchPosts',
  async (_, { rejectWithValue }) => {
    try {
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 4000)
      const data = await CommunityService.getPosts()
      clearTimeout(timeout)
      return data as CommunityPost[]
    } catch (error) {
      console.warn('[Community] Backend unavailable:', error)
      return rejectWithValue('Backend unavailable')
    }
  }
)

/** Create a community post. */
export const createPost = createAsyncThunk(
  'community/createPost',
  async (post: Omit<CommunityPost, 'id' | 'likes' | 'comments' | 'createdAt'>) => {
    try {
      const data = await CommunityService.createPost(post)
      return data as CommunityPost
    } catch (error) {
      // Create locally so posts always work in demo mode
      const localPost: CommunityPost = {
        ...post,
        id: `local-${Date.now()}`,
        likes: 0,
        comments: [],
        createdAt: Date.now()
      }
      console.warn('[Community] Backend unavailable, posted locally:', error)
      return localPost
    }
  }
)

// ─── Slice ─────────────────────────────────────────────────────────────────

const communitySlice = createSlice({
  name: 'community',
  initialState,
  reducers: {
    likePost: (state, action: PayloadAction<string>) => {
      const post = state.posts.find((p) => p.id === action.payload)
      if (post) {
        post.likes += 1
      }
    },
    addComment: (
      state,
      action: PayloadAction<{ postId: string; comment: CommunityComment }>
    ) => {
      const post = state.posts.find((p) => p.id === action.payload.postId)
      if (post) {
        post.comments.push(action.payload.comment)
      }
    },
    clearPosts: (state) => {
      state.posts = []
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPosts.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchPosts.fulfilled, (state, action) => {
        state.loading = false
        state.posts = action.payload
      })
      .addCase(fetchPosts.rejected, (state, action) => {
        state.loading = false
        state.error = (action.payload as string) ?? 'Failed to load posts'
      })
      .addCase(createPost.fulfilled, (state, action) => {
        state.posts = [action.payload, ...state.posts]
      })
  }
})

export const { likePost, addComment, clearPosts } = communitySlice.actions

// ─── Selectors ─────────────────────────────────────────────────────────────

export const selectPosts = (state: { community: CommunitySliceState }) => state.community.posts
export const selectPostsByTag = (state: { community: CommunitySliceState }, tag: string) =>
  state.community.posts.filter((p) => p.tags.includes(tag))
export const selectTrendingPosts = (state: { community: CommunitySliceState }, limit = 5) =>
  [...state.community.posts].sort((a, b) => b.likes - a.likes).slice(0, limit)

export default communitySlice.reducer


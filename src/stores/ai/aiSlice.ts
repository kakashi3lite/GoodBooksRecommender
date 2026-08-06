/**
 * 🤖 AI Assistant State Management
 * Chain-of-Thought: Manage conversational AI interactions, streaming state, and context
 * Memory: Persist chat history across sessions via localStorage
 * Forward-Thinking: Extensible for streaming responses and multi-turn context
 */

import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit'
import { BOOK_CATALOG, type BookMood } from '../../data/bookCatalog'
import { AIService } from '../../utils/api'
import { buildChatContext } from '../../utils/chatContext'
import type { ReadingEntry, ReadingLogEntry } from '../reading/readingSlice'
import type { UserPreferences } from '../user/userSlice'

// ─── Types ────────────────────────────────────────────────────────────────

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp: number
  /** Optional book suggestion rendered as a card in the chat */
  bookSuggestions?: Array<{
    id: string
    title: string
    authors: string
    cover_url?: string
    rating?: number
  }>
}

export interface AISliceState {
  enabled: boolean
  isOpen: boolean
  isStreaming: boolean
  messages: ChatMessage[]
  conversationContext: string[]
  error: string | null
  lastInteraction: number
}

// ─── Initial State ────────────────────────────────────────────────────────

const initialState: AISliceState = {
  enabled: true,
  isOpen: false,
  isStreaming: false,
  messages: [],
  conversationContext: [],
  error: null,
  lastInteraction: Date.now()
}

// ─── Fallback responses (used only when the backend is unreachable) ─────────
// Suggestion cards always come from the REAL local catalog — never fabricated.

const FALLBACK_REPLIES: Array<{
  keywords: string[]
  reply: string
  genres: string[]
  moods: BookMood[]
}> = [
    {
      keywords: ['recommend', 'suggest', 'what should i read', 'next book', 'book to read'],
      reply: "Based on your reading history, I'd suggest exploring these picks:",
      genres: [],
      moods: []
    },
    {
      keywords: ['mood', 'feeling', 'sad', 'happy', 'cozy', 'stressed'],
      reply:
        'Reading is a great way to reset your mood. I recommend something with a warm, uplifting tone — try a literary comfort read with a found-family theme.',
      genres: [],
      moods: ['cozy', 'uplifting']
    },
    {
      keywords: ['similar', 'like', 'same as', 'more like'],
      reply:
        'If you loved that book, these share its DNA — similar pacing, prose style, and thematic depth:',
      genres: [],
      moods: []
    },
    {
      keywords: ['sci-fi', 'science fiction', 'sci fi', 'space', 'future'],
      reply: 'Here are some strong science-fiction picks to keep the pages turning:',
      genres: ['Science Fiction'],
      moods: []
    },
    {
      keywords: ['mystery', 'thriller', 'crime', 'suspense'],
      reply: 'For readers who love a good puzzle, these picks deliver:',
      genres: ['Mystery', 'Thriller'],
      moods: []
    },
    {
      keywords: ['fantasy', 'magic', 'wizard', 'epic'],
      reply: 'These fantasy picks are perfect for getting lost in another world:',
      genres: ['Fantasy'],
      moods: []
    },
    {
      keywords: ['romance', 'love story'],
      reply: 'A little romance goes a long way — here are some warm picks:',
      genres: ['Romance'],
      moods: []
    },
    {
      keywords: ['cozy'],
      reply: 'Cozy reads, coming right up — warm, gentle, and uplifting:',
      genres: [],
      moods: ['cozy']
    }
  ]

const DEFAULT_FALLBACK = {
  reply:
    "I'm your AI reading companion. Ask me to recommend a book, match your mood, or find something similar to a favorite. Try: \"Recommend a cozy fantasy\" or \"Something like my last thriller.\""
}

/** Top-3 REAL catalog books scored by genre/mood match for the query. */
function buildFallbackReply(message: string): ChatMessage['bookSuggestions'] {
  const lower = message.toLowerCase()
  const match = FALLBACK_REPLIES.find(({ keywords }) =>
    keywords.some((keyword) => lower.includes(keyword))
  )
  return BOOK_CATALOG.map((book) => {
    let score = book.rating * 0.1
    if (match) {
      if (match.genres.some((g) => book.genres.includes(g))) score += 3
      if (match.moods.some((m) => book.moods.includes(m))) score += 2
    }
    return { book, score }
  })
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map(({ book }) => ({
      id: book.id,
      title: book.title,
      authors: book.authors,
      cover_url: book.cover_url,
      rating: book.rating
    }))
}

function buildFallbackContent(message: string): string {
  const lower = message.toLowerCase()
  const match = FALLBACK_REPLIES.find(({ keywords }) =>
    keywords.some((keyword) => lower.includes(keyword))
  )
  return match ? match.reply : DEFAULT_FALLBACK.reply
}

// ─── Async Thunk: Send Message ─────────────────────────────────────────────

/**
 * Send a chat message to the AI backend.
 * Chain-of-Thought: Attempt real API call, gracefully fall back to local
 * heuristics when the backend is unavailable so the UX never breaks.
 */
export const sendMessage = createAsyncThunk(
  'ai/sendMessage',
  async (message: string, thunkAPI) => {
    // Defensive reads: a store without reading/user slices (tests, SSR) just
    // yields an empty reader profile.
    const state = thunkAPI.getState() as {
      reading?: { currentlyReading?: ReadingEntry[]; readingLog?: ReadingLogEntry[] }
      user?: { preferences?: UserPreferences }
    }
    // Send the reader's REAL profile so the LLM can personalize the reply.
    const context = buildChatContext({
      favoriteGenres: state.user?.preferences?.favoriteGenres,
      readingGoal: state.user?.preferences?.readingGoal,
      currentlyReading: state.reading?.currentlyReading ?? [],
      readingLog: state.reading?.readingLog ?? []
    })

    try {
      // MiniMax-M2 reasoning replies can take a few seconds — allow up to 30s.
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 30000)

      const response = await AIService.chatWithAI(message, context)
      clearTimeout(timeout)

      const data = response as any
      if (data && typeof data.reply === 'string') {
        return {
          reply: data.reply,
          suggestions: data.bookSuggestions ?? undefined
        }
      }
      // Backend responded but in an unexpected shape
      return {
        reply: buildFallbackContent(message),
        suggestions: buildFallbackReply(message)
      }
    } catch (error) {
      // Backend unreachable — use the local heuristic so chat still works
      console.warn('[AI Assistant] Backend unavailable, using local fallback:', error)
      return {
        reply: buildFallbackContent(message),
        suggestions: buildFallbackReply(message)
      }
    }
  }
)

// ─── Slice ─────────────────────────────────────────────────────────────────

const aiSlice = createSlice({
  name: 'ai',
  initialState,
  reducers: {
    toggleAssistant: (state) => {
      state.isOpen = !state.isOpen
      state.lastInteraction = Date.now()
    },

    openAssistant: (state) => {
      state.isOpen = true
      state.lastInteraction = Date.now()
    },

    closeAssistant: (state) => {
      state.isOpen = false
      state.lastInteraction = Date.now()
    },

    addMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.messages.push(action.payload)
      // Keep conversation context to the most recent 20 messages
      state.conversationContext = state.messages.slice(-20).map((m) => m.content)
      state.lastInteraction = Date.now()
    },

    clearConversation: (state) => {
      state.messages = []
      state.conversationContext = []
      state.lastInteraction = Date.now()
    },

    setStreaming: (state, action: PayloadAction<boolean>) => {
      state.isStreaming = action.payload
    },

    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    }
  },

  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.isStreaming = true
        state.error = null
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isStreaming = false
        state.messages.push({
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: action.payload.reply,
          timestamp: Date.now(),
          bookSuggestions: action.payload.suggestions
        })
        state.conversationContext = state.messages.slice(-20).map((m) => m.content)
        state.lastInteraction = Date.now()
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isStreaming = false
        state.error = (action.payload as string) ?? 'Failed to reach the AI service'
      })
  }
})

export const {
  toggleAssistant,
  openAssistant,
  closeAssistant,
  addMessage,
  clearConversation,
  setStreaming,
  setError
} = aiSlice.actions

// ─── Selectors ─────────────────────────────────────────────────────────────

export const selectIsAssistantOpen = (state: { ai: AISliceState }) => state.ai.isOpen
export const selectIsStreaming = (state: { ai: AISliceState }) => state.ai.isStreaming
export const selectChatHistory = (state: { ai: AISliceState }) => state.ai.messages
export const selectConversationContext = (state: { ai: AISliceState }) =>
  state.ai.conversationContext
export const selectAIError = (state: { ai: AISliceState }) => state.ai.error

export default aiSlice.reducer

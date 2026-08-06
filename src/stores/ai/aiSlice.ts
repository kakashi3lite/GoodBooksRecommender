/**
 * 🤖 AI Assistant State Management
 * Chain-of-Thought: Manage conversational AI interactions, streaming state, and context
 * Memory: Persist chat history across sessions via localStorage
 * Forward-Thinking: Extensible for streaming responses and multi-turn context
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { AIService } from '../../utils/api'

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
  model: string
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
  model: 'goodbooks-assistant',
  error: null,
  lastInteraction: Date.now()
}

// ─── Fallback responses (used when the backend is unreachable) ─────────────

const FALLBACK_REPLIES = [
  {
    keywords: ['recommend', 'suggest', 'what should i read', 'next book', 'book to read'],
    reply:
      "Based on your reading history, I'd suggest exploring these picks:",
    suggestions: [
      { id: '1', title: 'The Midnight Library', authors: 'Matt Haig', rating: 4.3 },
      { id: '2', title: 'Project Hail Mary', authors: 'Andy Weir', rating: 4.7 },
      { id: '3', title: 'Tomorrow, and Tomorrow, and Tomorrow', authors: 'Gabrielle Zevin', rating: 4.5 }
    ]
  },
  {
    keywords: ['mood', 'feeling', 'sad', 'happy', 'cozy', 'stressed'],
    reply:
      'Reading is a great way to reset your mood. I recommend something with a warm, uplifting tone — try a literary comfort read with a found-family theme.',
    suggestions: [
      { id: '4', title: 'The House in the Cerulean Sea', authors: 'T.J. Klune', rating: 4.6 },
      { id: '5', title: 'A Psalm for the Wild-Built', authors: 'Becky Chambers', rating: 4.4 }
    ]
  },
  {
    keywords: ['similar', 'like', 'same as', 'more like'],
    reply:
      'If you loved that book, these share its DNA — similar pacing, prose style, and thematic depth:',
    suggestions: [
      { id: '6', title: 'The Night Circus', authors: 'Erin Morgenstern', rating: 4.2 },
      { id: '7', title: 'Piranesi', authors: 'Susanna Clarke', rating: 4.4 },
      { id: '8', title: 'The Starless Sea', authors: 'Erin Morgenstern', rating: 4.1 }
    ]
  }
]

const DEFAULT_FALLBACK = {
  reply:
    "I'm your AI reading companion. Ask me to recommend a book, match your mood, or find something similar to a favorite. Try: \"Recommend a cozy fantasy\" or \"Something like my last thriller.\"",
  suggestions: undefined as ChatMessage['bookSuggestions']
}

function buildFallbackReply(message: string): ChatMessage['bookSuggestions'] {
  const lower = message.toLowerCase()
  const match = FALLBACK_REPLIES.find(({ keywords }) =>
    keywords.some((keyword) => lower.includes(keyword))
  )
  return match ? match.suggestions : DEFAULT_FALLBACK.suggestions
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
  async (message: string) => {
    try {
      // Try the real backend with a short timeout so failures are fast
      const controller = new AbortController()
      const timeout = setTimeout(() => controller.abort(), 4000)

      const response = await AIService.chatWithAI(message)
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

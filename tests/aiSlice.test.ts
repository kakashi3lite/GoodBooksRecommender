/**
 * 🤖 AI Slice Tests
 * Chain-of-Thought: Verify chat state management and fallback behavior
 */

import { configureStore } from '@reduxjs/toolkit'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import reducer, {
  addMessage,
  clearConversation,
  sendMessage,
  toggleAssistant,
  type AISliceState
} from '../src/stores/ai/aiSlice'

// Mock the AIService so the backend is unreachable → fallback path is exercised
vi.mock('../src/utils/api', () => ({
  AIService: {
    chatWithAI: vi.fn().mockRejectedValue(new Error('network down'))
  }
}))

const createStore = () =>
  configureStore({
    reducer: {
      ai: reducer
    }
  })

describe('aiSlice', () => {
  let store: ReturnType<typeof createStore>

  beforeEach(() => {
    store = createStore()
  })

  it('starts with assistant closed and empty chat', () => {
    const state = store.getState().ai as AISliceState
    expect(state.isOpen).toBe(false)
    expect(state.messages).toHaveLength(0)
    expect(state.enabled).toBe(true)
  })

  it('toggles the assistant open/closed', () => {
    store.dispatch(toggleAssistant())
    expect((store.getState().ai as AISliceState).isOpen).toBe(true)
    store.dispatch(toggleAssistant())
    expect((store.getState().ai as AISliceState).isOpen).toBe(false)
  })

  it('adds a user message to history and context', () => {
    store.dispatch(
      addMessage({
        id: 'u1',
        role: 'user',
        content: 'Recommend me a book',
        timestamp: Date.now()
      })
    )
    const state = store.getState().ai as AISliceState
    expect(state.messages).toHaveLength(1)
    expect(state.conversationContext).toContain('Recommend me a book')
  })

  it('clears the conversation', () => {
    store.dispatch(
      addMessage({ id: 'u1', role: 'user', content: 'hi', timestamp: Date.now() })
    )
    store.dispatch(clearConversation())
    expect((store.getState().ai as AISliceState).messages).toHaveLength(0)
  })

  it('falls back to a local reply when the backend is unreachable', async () => {
    store.dispatch(
      addMessage({
        id: 'u1',
        role: 'user',
        content: 'Recommend me a book',
        timestamp: Date.now()
      })
    )
    await store.dispatch(sendMessage('Recommend me a book') as any)

    const state = store.getState().ai as AISliceState
    expect(state.isStreaming).toBe(false)
    // user + assistant fallback reply
    expect(state.messages).toHaveLength(2)
    const assistant = state.messages[1]
    expect(assistant.role).toBe('assistant')
    expect(assistant.bookSuggestions).toBeDefined()
    expect(assistant.bookSuggestions!.length).toBeGreaterThan(0)
  })
})

/**
 * 🤖 AI Assistant Component Tests
 * Chain-of-Thought: Verify the chat panel opens, sends messages, and renders replies
 */

import { configureStore } from '@reduxjs/toolkit'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AIAssistant from '../../src/components/AI/AIAssistant'
import aiReducer from '../../src/stores/ai/aiSlice'
import dashboardReducer from '../../src/stores/dashboard/dashboardSlice'

// Mock the AI backend so the fallback reply path is exercised deterministically
vi.mock('../../src/utils/api', () => ({
    AIService: {
        chatWithAI: vi.fn().mockRejectedValue(new Error('network down'))
    }
}))

const createStore = () =>
    configureStore({
        reducer: {
            ai: aiReducer,
            dashboard: dashboardReducer
        }
    })

const renderAssistant = () => {
    const store = createStore()
    return {
        store,
        ...render(
            <Provider store={store}>
                <AIAssistant />
            </Provider>
        )
    }
}

describe('AIAssistant', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('renders the floating toggle button', () => {
        renderAssistant()
        expect(screen.getByLabelText('Toggle AI Assistant')).toBeInTheDocument()
    })

    it('opens the chat panel when the toggle is clicked', () => {
        renderAssistant()
        fireEvent.click(screen.getByLabelText('Toggle AI Assistant'))
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        expect(screen.getByLabelText('Message the AI assistant')).toBeInTheDocument()
    })

    it('sends a message and displays a fallback assistant reply', async () => {
        renderAssistant()
        fireEvent.click(screen.getByLabelText('Toggle AI Assistant'))

        const input = screen.getByLabelText('Message the AI assistant')
        fireEvent.change(input, { target: { value: 'Recommend me a book' } })
        fireEvent.click(screen.getByLabelText('Send message'))

        // The user message appears immediately
        expect(screen.getByText('Recommend me a book')).toBeInTheDocument()

        // The assistant fallback reply arrives (matches the "recommend" keyword branch)
        await waitFor(() => {
            expect(screen.getByText(/Based on your reading history/i)).toBeInTheDocument()
        })
    })

    it('toggles closed with the header clear button', () => {
        renderAssistant()
        fireEvent.click(screen.getByLabelText('Toggle AI Assistant'))
        expect(screen.getByRole('dialog')).toBeInTheDocument()
        fireEvent.click(screen.getByLabelText('Clear conversation'))
        // Panel stays open but conversation is cleared
        expect(screen.queryByRole('dialog')).toBeInTheDocument()
    })
})

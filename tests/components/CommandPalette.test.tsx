/**
 * ⌘K Command Palette tests
 * Chain-of-Thought: the palette is a keyboard surface — the behaviours worth
 * pinning are the shortcut, filtering, and that running a command actually
 * mutates real state (not just closes the dialog).
 */

import { configureStore } from '@reduxjs/toolkit'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CommandPalette from '../../src/components/UI/CommandPalette'
import aiReducer from '../../src/stores/ai/aiSlice'
import booksReducer from '../../src/stores/books/booksSlice'
import dashboardReducer from '../../src/stores/dashboard/dashboardSlice'
import readingReducer from '../../src/stores/reading/readingSlice'
import userReducer from '../../src/stores/user/userSlice'

const createStore = () =>
    configureStore({
        reducer: {
            dashboard: dashboardReducer,
            ai: aiReducer,
            user: userReducer,
            reading: readingReducer,
            books: booksReducer
        }
    })

const renderPalette = () => {
    const store = createStore()
    render(
        <Provider store={store}>
            <MemoryRouter>
                <CommandPalette />
            </MemoryRouter>
        </Provider>
    )
    return store
}

const pressShortcut = () => {
    act(() => {
        fireEvent.keyDown(window, { key: 'k', metaKey: true })
    })
}

describe('CommandPalette', () => {
    beforeEach(() => {
        localStorage.clear()
        // Live book search is out of scope here — keep the network quiet.
        vi.stubGlobal(
            'fetch',
            vi.fn().mockResolvedValue({ ok: true, json: async () => ({ data: [] }) })
        )
    })

    afterEach(() => {
        vi.unstubAllGlobals()
    })

    it('stays closed until ⌘K is pressed', () => {
        renderPalette()
        expect(screen.queryByRole('dialog', { name: 'Command palette' })).not.toBeInTheDocument()
        pressShortcut()
        expect(screen.getByRole('dialog', { name: 'Command palette' })).toBeInTheDocument()
    })

    it('lists navigation and actions, and filters as you type', () => {
        renderPalette()
        pressShortcut()

        expect(screen.getByText('Discover books')).toBeInTheDocument()
        expect(screen.getByText('Ask the reading companion')).toBeInTheDocument()

        fireEvent.change(screen.getByLabelText('Search commands and books'), {
            target: { value: 'analytics' }
        })
        expect(screen.getByText('Reading Analytics')).toBeInTheDocument()
        expect(screen.queryByText('Discover books')).not.toBeInTheDocument()
    })

    it('runs the highlighted command (theme toggle switches real state)', async () => {
        const store = createStore()
        render(
            <Provider store={store}>
                <MemoryRouter>
                    <CommandPalette />
                </MemoryRouter>
            </Provider>
        )
        const before = store.getState().dashboard.theme

        pressShortcut()
        fireEvent.change(screen.getByLabelText('Search commands and books'), {
            target: { value: 'light mode' }
        })
        await waitFor(() => expect(screen.getByText('Switch to light mode')).toBeInTheDocument())
        fireEvent.keyDown(window, { key: 'Enter' })

        expect(store.getState().dashboard.theme).toBe('light')
        expect(before).not.toBe('light')
    })

    it('closes on Escape', async () => {
        renderPalette()
        pressShortcut()
        // Escape is owned by useFocusTrap, which listens on `document` — where
        // real keydowns from inside the dialog bubble before reaching window.
        fireEvent.keyDown(document, { key: 'Escape' })
        // AnimatePresence keeps the surface mounted for its exit animation.
        await waitFor(() =>
            expect(screen.queryByRole('dialog', { name: 'Command palette' })).not.toBeInTheDocument()
        )
    })
})

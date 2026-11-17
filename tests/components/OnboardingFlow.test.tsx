/**
 * 🎉 Onboarding Flow Component Test
 * Chain-of-Thought: Verify the 3-step flow (welcome → account → taste quiz)
 * creates an account and completes onboarding end-to-end.
 */

import { configureStore } from '@reduxjs/toolkit'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import OnboardingFlow from '../../src/components/Onboarding/OnboardingFlow'
import userReducer from '../../src/stores/user/userSlice'

const createStore = () =>
    configureStore({
        reducer: {
            user: userReducer
        }
    })

const renderFlow = () => {
    const store = createStore()
    return {
        store,
        ...render(
            <Provider store={store}>
                <OnboardingFlow />
            </Provider>
        )
    }
}

describe('OnboardingFlow', () => {
    beforeEach(() => {
        localStorage.clear()
        // jsdom's fetch cannot resolve a relative URL; stub it so the
        // best-effort account sync never touches the real network.
        vi.stubGlobal(
            'fetch',
            vi.fn().mockResolvedValue(
                new Response(
                    JSON.stringify({ created: true, accountKey: 'k'.repeat(64) }),
                    { status: 201, headers: { 'Content-Type': 'application/json' } }
                )
            )
        )
    })

    afterEach(() => {
        vi.unstubAllGlobals()
    })

    it('renders the welcome step first', () => {
        renderFlow()
        expect(screen.getByText(/Discover books made for you/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Continue/i })).toBeInTheDocument()
    })

    it('walks through account creation and taste quiz to completion', async () => {
        const { store } = renderFlow()

        // Step 0 → 1: welcome → account (AnimatePresence exit is async)
        fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
        const nameInput = await screen.findByPlaceholderText('Ada Lovelace')

        // Fill the account form
        fireEvent.change(nameInput, { target: { value: 'Maya Reader' } })
        fireEvent.change(await screen.findByPlaceholderText('ada@example.com'), {
            target: { value: 'maya@example.com' }
        })
        fireEvent.click(screen.getByRole('button', { name: /Continue/i }))

        // Step 2: taste quiz — pick a genre + finish
        const sciFi = await screen.findByText('Science Fiction')
        fireEvent.click(sciFi)
        fireEvent.click(await screen.findByRole('button', { name: /Show me my books/i }))

        // Account created + onboarding complete
        const state = store.getState().user as any
        expect(state.isAuthenticated).toBe(true)
        expect(state.hasCompletedOnboarding).toBe(true)
        expect(state.profile.name).toBe('Maya Reader')
        expect(state.preferences.favoriteGenres).toContain('Science Fiction')
    })

    it('disables Continue until the account form is valid', async () => {
        renderFlow()
        fireEvent.click(screen.getByRole('button', { name: /Continue/i }))

        const nameInput = await screen.findByPlaceholderText('Ada Lovelace')
        const continueBtn = screen.getByRole('button', { name: /Continue/i })
        expect(continueBtn).toBeDisabled()

        fireEvent.change(nameInput, { target: { value: 'A' } })
        // email still invalid → still disabled
        expect(screen.getByRole('button', { name: /Continue/i })).toBeDisabled()

        fireEvent.change(screen.getByPlaceholderText('ada@example.com'), {
            target: { value: 'a@b.co' }
        })
        expect(screen.getByRole('button', { name: /Continue/i })).not.toBeDisabled()
    })

    it('writes the new account to /api/accounts when onboarding completes', async () => {
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(
                JSON.stringify({ created: true, accountKey: 'k'.repeat(64) }),
                { status: 201, headers: { 'Content-Type': 'application/json' } }
            )
        )
        vi.stubGlobal('fetch', fetchMock)
        renderFlow()

        fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
        fireEvent.change(await screen.findByPlaceholderText('Ada Lovelace'), {
            target: { value: 'Durable Reader' }
        })
        fireEvent.change(await screen.findByPlaceholderText('ada@example.com'), {
            target: { value: 'Durable@Example.com' }
        })
        fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
        fireEvent.click(await screen.findByText('Fantasy'))
        fireEvent.click(await screen.findByRole('button', { name: /Show me my books/i }))

        await waitFor(() => expect(fetchMock).toHaveBeenCalled())
        const [url, init] = fetchMock.mock.calls[0]
        expect(url).toBe('/api/accounts')
        expect(init.method).toBe('POST')
        expect(JSON.parse(init.body)).toMatchObject({
            email: 'durable@example.com',
            name: 'Durable Reader',
            favoriteGenres: ['Fantasy']
        })
    })

    it('does not require a dot-less address (server parity on validation)', async () => {
        renderFlow()
        fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
        fireEvent.change(await screen.findByPlaceholderText('Ada Lovelace'), {
            target: { value: 'Ada' }
        })
        fireEvent.change(await screen.findByPlaceholderText('ada@example.com'), {
            target: { value: 'ada@localhost' }
        })
        expect(screen.getByRole('button', { name: /Continue/i })).toBeDisabled()
    })

    it('supports going back from the account step', () => {
        renderFlow()
        fireEvent.click(screen.getByRole('button', { name: /Continue/i }))
        fireEvent.click(screen.getByRole('button', { name: /Back/i }))
        expect(screen.getByText(/Discover books made for you/i)).toBeInTheDocument()
    })
})

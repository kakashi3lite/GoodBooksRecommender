/**
 * ⚙️ Settings → Account — persistence status + delete-my-account
 *
 * Chain-of-Thought: the customer must be able to *see* whether the account is
 * durable (a D1 row exists for this device) and to delete it. Those two
 * affordances are the visible half of the CRUD contract.
 */

import { configureStore } from '@reduxjs/toolkit'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import SettingsModal from '../src/components/UI/SettingsModal'
import dashboardReducer from '../src/stores/dashboard/dashboardSlice'
import readingReducer from '../src/stores/reading/readingSlice'
import userReducer, { register, completeOnboarding } from '../src/stores/user/userSlice'

const deleteUserAccount = vi.fn().mockResolvedValue(true)
vi.mock('../src/lib/userRepository', () => ({
    deleteUserAccount: (...args: unknown[]) => deleteUserAccount(...args)
}))

const createStore = (email: string) => {
    const store = configureStore({
        reducer: { user: userReducer, dashboard: dashboardReducer, reading: readingReducer }
    })
    store.dispatch(register({ name: 'Ada', email }))
    store.dispatch(completeOnboarding({ favoriteGenres: ['Fiction'], readingGoal: 12 }))
    return store
}

const renderSettings = (email: string) => {
    const store = createStore(email)
    render(
        <Provider store={store}>
            <SettingsModal open onClose={() => {}} />
        </Provider>
    )
    return store
}

describe('Settings → Account', () => {
    beforeEach(() => {
        localStorage.clear()
        deleteUserAccount.mockClear()
    })

    it('says the account is local-only when this device holds no account key', () => {
        renderSettings('ada@example.com')
        expect(screen.getByTestId('account-persistence')).toHaveTextContent(/Local only/i)
    })

    it('says the account is saved to Cloudflare when the device holds a key', () => {
        localStorage.setItem(
            'goodbooks_account_key',
            JSON.stringify({ 'ada@example.com': 'a'.repeat(64) })
        )
        renderSettings('ada@example.com')
        expect(screen.getByTestId('account-persistence')).toHaveTextContent(/Saved to Cloudflare/i)
    })

    it('requires a second tap before deleting, then signs out', async () => {
        localStorage.setItem(
            'goodbooks_account_key',
            JSON.stringify({ 'ada@example.com': 'a'.repeat(64) })
        )
        const store = renderSettings('ada@example.com')

        fireEvent.click(screen.getByRole('button', { name: /Delete my account/i }))
        expect(deleteUserAccount).not.toHaveBeenCalled()
        expect(screen.getByRole('button', { name: /Tap again/i })).toBeInTheDocument()

        fireEvent.click(screen.getByRole('button', { name: /Tap again/i }))
        await waitFor(() => expect(deleteUserAccount).toHaveBeenCalledWith('ada@example.com'))
        await waitFor(() =>
            expect((store.getState().user as { isAuthenticated: boolean }).isAuthenticated).toBe(false)
        )
    })
})

/**
 * 🗄️ User Account Sync Thunk Tests
 * Chain-of-Thought: Verify syncAccountToServer only fires for authenticated
 * users and routes through the repository (mocked here, isolated from the
 * real-repository tests in userRepository.test.ts).
 */

import { configureStore } from '@reduxjs/toolkit'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import reducer, {
    completeOnboarding,
    register,
    syncAccountToServer
} from '../src/stores/user/userSlice'

// File-scoped mock: only this file uses it (hoisted, so no real imports here)
vi.mock('../src/lib/userRepository', () => ({
    syncUserAccount: vi.fn().mockResolvedValue({ synced: true, email: 'ada@example.com' })
}))

const createStore = () =>
    configureStore({
        reducer: {
            user: reducer
        }
    })

describe('syncAccountToServer thunk', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('does not sync when the user is not authenticated', async () => {
        const store = createStore()
        const result = (await store.dispatch(syncAccountToServer() as any)) as any
        expect(result.payload).toEqual({ synced: false })
    })

    it('syncs an authenticated, onboarded account through the repository', async () => {
        const store = createStore()
        store.dispatch(register({ name: 'Ada', email: 'ada@example.com' }))
        store.dispatch(completeOnboarding({ favoriteGenres: ['Science Fiction'] }))

        const result = (await store.dispatch(syncAccountToServer() as any)) as any
        expect(result.payload.synced).toBe(true)
        expect(result.payload.email).toBe('ada@example.com')
    })
})

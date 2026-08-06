/**
 * 🔐 User Auth + Onboarding Slice Tests
 * Chain-of-Thought: Verify register / login / logout / completeOnboarding
 * state transitions and localStorage persistence.
 */

import { configureStore } from '@reduxjs/toolkit'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import reducer, {
    completeOnboarding,
    login,
    logout,
    register,
    selectHasCompletedOnboarding,
    selectIsAuthenticated,
    type UserSliceState
} from '../src/stores/user/userSlice'

const STORAGE_KEY = 'goodbooks_user'

const createStore = () =>
    configureStore({
        reducer: {
            user: reducer
        }
    })

describe('user auth slice', () => {
    beforeEach(() => {
        localStorage.clear()
    })

    it('starts signed out and not onboarded', () => {
        const store = createStore()
        expect(selectIsAuthenticated(store.getState())).toBe(false)
        expect(selectHasCompletedOnboarding(store.getState())).toBe(false)
    })

    it('register creates an account and persists it', () => {
        const store = createStore()
        store.dispatch(register({ name: 'Ada Lovelace', email: 'ada@example.com' }))

        const state = store.getState().user as UserSliceState
        expect(state.isAuthenticated).toBe(true)
        expect(state.profile.name).toBe('Ada Lovelace')
        expect(state.profile.email).toBe('ada@example.com')
        expect(state.profile.id).toMatch(/^u-/)
        expect(localStorage.getItem(STORAGE_KEY)).toContain('Ada Lovelace')
    })

    it('restores a persisted user on store creation', async () => {
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify({
                profile: { id: 'u-abc', name: 'Grace', email: 'grace@example.com', readingLevel: 'novice' },
                preferences: {
                    favoriteGenres: ['Fantasy'],
                    preferredFormats: ['ebook'],
                    readingGoal: 12,
                    notifications: true,
                    privacy: 'friends'
                },
                goals: [],
                readingHistory: [],
                favorites: [],
                isAuthenticated: true,
                hasCompletedOnboarding: true
            })
        )

        // initialState is computed at module load — re-import fresh so restoreUser runs
        vi.resetModules()
        const { default: freshReducer } = await import('../src/stores/user/userSlice')
        const store = configureStore({ reducer: { user: freshReducer } })

        const state = store.getState().user as UserSliceState
        expect(state.isAuthenticated).toBe(true)
        expect(state.profile.name).toBe('Grace')
        expect(state.hasCompletedOnboarding).toBe(true)
    })

    it('completeOnboarding merges taste preferences and flags completion', () => {
        const store = createStore()
        store.dispatch(register({ name: 'Ada', email: 'ada@example.com' }))
        store.dispatch(
            completeOnboarding({
                favoriteGenres: ['Science Fiction', 'Fantasy'],
                readingGoal: 52
            })
        )
        const state = store.getState().user as UserSliceState
        expect(state.hasCompletedOnboarding).toBe(true)
        expect(state.preferences.favoriteGenres).toContain('Science Fiction')
        expect(state.preferences.readingGoal).toBe(52)
    })

    it('login restores an account by email', () => {
        const store = createStore()
        store.dispatch(register({ name: 'Ada', email: 'ada@example.com' }))
        store.dispatch(logout())
        expect(selectIsAuthenticated(store.getState())).toBe(false)

        store.dispatch(login({ email: 'ada@example.com' }))
        expect(selectIsAuthenticated(store.getState())).toBe(true)
        expect((store.getState().user as UserSliceState).profile.email).toBe('ada@example.com')
    })

    it('logout clears auth and persisted state', () => {
        const store = createStore()
        store.dispatch(register({ name: 'Ada', email: 'ada@example.com' }))
        store.dispatch(completeOnboarding({ favoriteGenres: ['Fiction'] }))
        store.dispatch(logout())

        const state = store.getState().user as UserSliceState
        expect(state.isAuthenticated).toBe(false)
        expect(state.hasCompletedOnboarding).toBe(false)
        expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
    })
})

/**
 * 👤 User Slice Tests
 * Chain-of-Thought: Verify profile, preferences, and reading goal state
 */

import { configureStore } from '@reduxjs/toolkit'
import { describe, expect, it } from 'vitest'
import reducer, {
    addGoal,
    toggleFavorite,
    updateGoalProgress,
    type UserSliceState
} from '../src/stores/user/userSlice'

const createStore = () =>
    configureStore({
        reducer: {
            user: reducer
        }
    })

describe('userSlice', () => {
    it('starts with a default reader profile', () => {
        const store = createStore()
        const state = store.getState().user as UserSliceState
        expect(state.profile.name).toBe('Reader')
        expect(state.preferences.readingGoal).toBe(24)
        expect(state.goals).toHaveLength(0)
    })

    it('adds a reading goal and tracks progress without exceeding target', () => {
        const store = createStore()
        store.dispatch(
            addGoal({
                id: 'g1',
                title: 'Read 5 Sci-Fi',
                type: 'genre',
                target: 5,
                current: 0,
                unit: 'books',
                year: 2026
            })
        )
        store.dispatch(updateGoalProgress({ id: 'g1', current: 3 }))
        expect((store.getState().user as UserSliceState).goals[0].current).toBe(3)

        // Progress clamps at target
        store.dispatch(updateGoalProgress({ id: 'g1', current: 99 }))
        expect((store.getState().user as UserSliceState).goals[0].current).toBe(5)
    })

    it('toggles favorites on and off', () => {
        const store = createStore()
        store.dispatch(toggleFavorite('book-1'))
        expect((store.getState().user as UserSliceState).favorites).toContain('book-1')
        store.dispatch(toggleFavorite('book-1'))
        expect((store.getState().user as UserSliceState).favorites).not.toContain('book-1')
    })
})

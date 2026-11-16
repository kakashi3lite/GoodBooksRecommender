/**
 * 🎚️ Reading pace — one answer, revisitable everywhere
 *
 * Defect found in the reader audit: onboarding asked for a reading pace, stored
 * it as `preferredMoods`, and no other surface could read or change it. Settings
 * offers no way back, so a reader who picked "Quick reads" once was stuck with
 * that preference ranking every recommendation, forever.
 */

import { configureStore } from '@reduxjs/toolkit'
import { fireEvent, render, screen } from '@testing-library/react'
import { Provider } from 'react-redux'
import { beforeEach, describe, expect, it } from 'vitest'
import SettingsModal from '../src/components/UI/SettingsModal'
import dashboardReducer from '../src/stores/dashboard/dashboardSlice'
import readingReducer from '../src/stores/reading/readingSlice'
import userReducer, { type UserPreferences } from '../src/stores/user/userSlice'
import { moodsForPace, paceForMoods, READING_PACE } from '../src/utils/readingPace'

const createStore = (preferredMoods: string[] = []) => {
    const store = configureStore({
        reducer: { user: userReducer, dashboard: dashboardReducer, reading: readingReducer }
    })
    store.dispatch({
        type: 'user/setPreferences',
        payload: { preferredMoods } as Partial<UserPreferences>
    })
    return store
}

describe('reading pace', () => {
    it('maps every pace to moods and back without loss', () => {
        for (const option of READING_PACE) {
            expect(paceForMoods(moodsForPace(option.id))).toBe(option.id)
        }
    })

    it('treats an unknown or empty mood set as the neutral pace', () => {
        expect(paceForMoods([])).toBe('mixed')
        expect(paceForMoods(undefined)).toBe('mixed')
        expect(paceForMoods(['slow-burn'])).toBe('mixed')
    })

    describe('Settings', () => {
        beforeEach(() => localStorage.clear())

        it('shows the pace the reader chose during onboarding', () => {
            render(
                <Provider store={createStore(['epic'])}>
                    <SettingsModal open onClose={() => {}} />
                </Provider>
            )
            expect(screen.getByRole('button', { name: /Epic tomes/i })).toHaveAttribute('aria-pressed', 'true')
            expect(screen.getByRole('button', { name: /Quick reads/i })).toHaveAttribute('aria-pressed', 'false')
        })

        it('lets the reader revise it, and persists the new answer', async () => {
            // The app store, not a bare one: persistence is wired in
            // `store.ts` (covered end-to-end by tests/userPersistence.test.ts).
            const { store } = await import('../src/stores/store')
            store.dispatch({ type: 'user/setPreferences', payload: { preferredMoods: [] } })
            render(
                <Provider store={store}>
                    <SettingsModal open onClose={() => {}} />
                </Provider>
            )

            fireEvent.click(screen.getByRole('button', { name: /Quick reads/i }))

            expect(store.getState().user.preferences.preferredMoods).toEqual(['fast-paced'])
            expect(JSON.parse(localStorage.getItem('goodbooks_user') ?? '{}').preferences.preferredMoods).toEqual([
                'fast-paced'
            ])
        })
    })
})

/**
 * 🧪 Account durability — the reader's own decisions must survive a reload
 *
 * Defect found in the live audit: only `register`, `login` and
 * `completeOnboarding` wrote the account to storage. Everything else — saving a
 * book for later, raising a reading goal, changing a setting — lived in memory
 * and silently reverted on the next load, so a wishlist could resurrect books
 * the reader had already started reading.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

const STORAGE_KEY = 'goodbooks_user'

type StoreModule = typeof import('../src/stores/store')
type UserModule = typeof import('../src/stores/user/userSlice')

const readStoredUser = () => JSON.parse(localStorage.getItem(STORAGE_KEY) ?? 'null')

describe('account persistence', () => {
    let store: StoreModule['store']
    let user: UserModule

    beforeEach(async () => {
        localStorage.clear()
        vi.resetModules()
        user = await import('../src/stores/user/userSlice')
        store = (await import('../src/stores/store')).store
        store.dispatch(user.register({ name: 'Ada Reader', email: 'ada@example.com' }))
    })

    it('persists a book saved for later', () => {
        store.dispatch(user.toggleFavorite('b-01'))
        expect(readStoredUser().favorites).toEqual(['b-01'])
    })

    it('persists the removal of a book the reader started', () => {
        store.dispatch(user.toggleFavorite('b-01'))
        store.dispatch(user.toggleFavorite('b-01'))
        expect(readStoredUser().favorites).toEqual([])
        expect(store.getState().user.favorites).toEqual([])
    })

    it('persists preference changes made outside onboarding', () => {
        store.dispatch(user.setPreferences({ readingGoal: 40, preferredMoods: ['epic'] }))
        const stored = readStoredUser()
        expect(stored.preferences.readingGoal).toBe(40)
        expect(stored.preferences.preferredMoods).toEqual(['epic'])
    })

    it('persists goals the reader adds', () => {
        store.dispatch(
            user.addGoal({ id: 'g-1', title: 'Read more', type: 'count', target: 30, current: 0, unit: 'books', year: 2026 })
        )
        expect(readStoredUser().goals).toHaveLength(1)
    })
})

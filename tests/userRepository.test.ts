/**
 * 🗄️ User Repository Tests (real module, unconfigured)
 * Chain-of-Thought: Without Supabase env vars, the repository must degrade to
 * { synced: false } / null — never throw, never touch the network.
 */

import { describe, expect, it } from 'vitest'
import { isSupabaseConfigured } from '../src/lib/supabaseClient'
import { fetchUserAccount, syncUserAccount } from '../src/lib/userRepository'

describe('userRepository (unconfigured)', () => {
    it('is not configured when env vars are absent', () => {
        expect(isSupabaseConfigured()).toBe(false)
    })

    it('syncUserAccount returns { synced: false } without throwing', async () => {
        const result = await syncUserAccount({
            email: 'a@b.co',
            name: 'Ada',
            favoriteGenres: ['Fiction'],
            readingGoal: 12,
            readingLevel: 'novice'
        })
        expect(result.synced).toBe(false)
    })

    it('fetchUserAccount returns null without throwing', async () => {
        const result = await fetchUserAccount('nobody@example.com')
        expect(result).toBeNull()
    })
})

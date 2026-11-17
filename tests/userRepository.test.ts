/**
 * 🗄️ User Repository Tests — Cloudflare D1 account persistence
 *
 * Chain-of-Thought: the repository must (1) mirror the local account into D1
 * through the same-origin `/api/accounts` function, (2) remember the account
 * key so later writes update the same row instead of duplicating it, and
 * (3) degrade to `{ synced: false }` / `null` when the network or the binding
 * is unavailable — never throw into a reducer.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { getAccountKey } from '../src/lib/accountApi'
import {
    deleteUserAccount,
    fetchUserAccount,
    syncUserAccount
} from '../src/lib/userRepository'

const jsonResponse = (body: unknown, status = 200): Response =>
    new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json' }
    })

const account = {
    id: 'acc-1',
    email: 'ada@example.com',
    name: 'Ada',
    favoriteGenres: ['Fiction'],
    preferredMoods: ['cozy'],
    readingGoal: 12,
    readingLevel: 'novice',
    createdAt: '2026-11-17T00:00:00.000Z',
    updatedAt: '2026-11-17T00:00:00.000Z'
}

const syncInput = {
    email: 'ada@example.com',
    name: 'Ada',
    favoriteGenres: ['Fiction'],
    preferredMoods: ['cozy'],
    readingGoal: 12,
    readingLevel: 'novice'
}

describe('userRepository → /api/accounts (D1)', () => {
    beforeEach(() => {
        localStorage.clear()
    })

    afterEach(() => {
        vi.unstubAllGlobals()
        vi.restoreAllMocks()
    })

    it('creates the account and remembers the returned account key', async () => {
        const fetchMock = vi
            .fn()
            .mockResolvedValue(jsonResponse({ created: true, accountKey: 'key-123', account }, 201))
        vi.stubGlobal('fetch', fetchMock)

        const result = await syncUserAccount(syncInput)

        expect(result).toMatchObject({ synced: true, email: 'ada@example.com', created: true })
        expect(fetchMock).toHaveBeenCalledTimes(1)
        const [url, init] = fetchMock.mock.calls[0]
        expect(url).toBe('/api/accounts')
        expect(init.method).toBe('POST')
        expect(JSON.parse(init.body)).toMatchObject({
            email: 'ada@example.com',
            favoriteGenres: ['Fiction'],
            preferredMoods: ['cozy'],
            readingGoal: 12
        })
        expect(getAccountKey('ada@example.com')).toBe('key-123')
    })

    it('proves ownership with the stored key when syncing again', async () => {
        const fetchMock = vi
            .fn()
            .mockResolvedValueOnce(jsonResponse({ created: true, accountKey: 'key-123', account }, 201))
            .mockResolvedValueOnce(jsonResponse({ created: false, account }))
        vi.stubGlobal('fetch', fetchMock)

        await syncUserAccount(syncInput)
        // The mount-level debounce must not hide a genuine update.
        localStorage.removeItem('goodbooks_sync_marker')
        await syncUserAccount({ ...syncInput, name: 'Ada Lovelace' })

        const [, secondInit] = fetchMock.mock.calls[1]
        expect(secondInit.headers['X-Account-Key']).toBe('key-123')
    })

    it('returns { synced: false } when the network is unreachable', async () => {
        vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))

        await expect(syncUserAccount(syncInput)).resolves.toMatchObject({ synced: false })
    })

    it('maps a stored account into the legacy snake_case profile shape', async () => {
        localStorage.setItem(
            'goodbooks_account_key',
            JSON.stringify({ 'ada@example.com': 'a'.repeat(64) })
        )
        const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ account }))
        vi.stubGlobal('fetch', fetchMock)

        await expect(fetchUserAccount('ada@example.com')).resolves.toEqual({
            email: 'ada@example.com',
            name: 'Ada',
            favorite_genres: ['Fiction'],
            reading_goal: 12,
            reading_level: 'novice',
            updated_at: account.updatedAt
        })
        const [url, init] = fetchMock.mock.calls[0]
        expect(url).toContain('/api/accounts/ada%40example.com')
        expect(init.headers['X-Account-Key']).toBe('a'.repeat(64))
    })

    it('returns null for a profile this device cannot prove ownership of', async () => {
        // No key on device → no request at all (the endpoint is owner-only).
        const fetchMock = vi.fn()
        vi.stubGlobal('fetch', fetchMock)
        await expect(fetchUserAccount('nobody@example.com')).resolves.toBeNull()
        expect(fetchMock).not.toHaveBeenCalled()

        // Key present but rejected → still null.
        localStorage.setItem(
            'goodbooks_account_key',
            JSON.stringify({ 'nobody@example.com': 'b'.repeat(64) })
        )
        vi.stubGlobal(
            'fetch',
            vi.fn().mockResolvedValue(jsonResponse({ error: 'invalid_key' }, 401))
        )
        await expect(fetchUserAccount('nobody@example.com')).resolves.toBeNull()
    })

    it('surfaces a 409 email conflict instead of pretending the account synced', async () => {
        vi.stubGlobal(
            'fetch',
            vi.fn().mockResolvedValue(jsonResponse({ error: 'email_taken' }, 409))
        )

        const result = await syncUserAccount(syncInput)

        expect(result).toMatchObject({ synced: false, error: 'email_taken' })
        // A conflict must not suppress the retry the way a success does.
        expect(localStorage.getItem('goodbooks_sync_marker')).toBeNull()
    })

    it('deletes the account, forgets the local key and clears the sync marker', async () => {
        vi.stubGlobal(
            'fetch',
            vi
                .fn()
                .mockResolvedValueOnce(jsonResponse({ created: true, accountKey: 'key-123', account }, 201))
                .mockResolvedValueOnce(jsonResponse({ deleted: true }))
        )

        await syncUserAccount(syncInput)
        expect(localStorage.getItem('goodbooks_sync_marker')).not.toBeNull()

        await expect(deleteUserAccount('ada@example.com')).resolves.toBe(true)
        expect(getAccountKey('ada@example.com')).toBeNull()
        // A re-signup with the same email must not be debounced away.
        expect(localStorage.getItem('goodbooks_sync_marker')).toBeNull()
    })
})

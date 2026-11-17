/**
 * 🗄️ User Repository — database-backed accounts on Cloudflare D1
 *
 * Chain-of-Thought
 *   - The durable store is the `accounts` table in the Pages project's D1
 *     database, reached through the same-origin `/api/accounts` function (see
 *     `functions/api/accounts/[[route]].ts` and `d1/schema.sql`).
 *   - `localStorage` stays the source of truth for instant UX; this repository
 *     mirrors the account to D1 so it survives a browser wipe or a device
 *     change. Every failure is non-fatal by design.
 *   - Supabase is no longer involved in accounts: its service-role key was
 *     never set as `SUPABASE_URL`/anon on the project, its `profiles` table
 *     contract did not match this payload, and its signup path was
 *     rate-limited. The Supabase REST layer remains for the book catalog only
 *     (`functions/api/_lib/db.ts`).
 */

import {
    deleteAccount,
    fetchAccount,
    syncAccount,
    updateAccount,
    type AccountSyncResult,
    type ServerAccount
} from './accountApi'

/** Shape kept for callers that still speak snake_case (server payload). */
export interface ServerProfile {
    email: string
    name: string
    favorite_genres: string[]
    reading_goal: number
    reading_level: string
    updated_at: string
}

export type SyncResult = AccountSyncResult

const toServerProfile = (account: ServerAccount): ServerProfile => ({
    email: account.email,
    name: account.name,
    favorite_genres: account.favoriteGenres,
    reading_goal: account.readingGoal,
    reading_level: account.readingLevel,
    updated_at: account.updatedAt
})

/**
 * Push the local account to D1 (create, or update when this device holds the
 * account key). Never throws; returns `{ synced: false }` when unreachable.
 */
export const syncUserAccount = async (
    input: {
        email: string
        name: string
        favoriteGenres: string[]
        preferredMoods?: string[]
        readingGoal: number
        readingLevel: string
    },
    options: { force?: boolean } = {}
): Promise<SyncResult> =>
    syncAccount(
        {
            email: input.email,
            name: input.name,
            favoriteGenres: input.favoriteGenres,
            preferredMoods: input.preferredMoods ?? [],
            readingGoal: input.readingGoal,
            readingLevel: input.readingLevel
        },
        options
    )

/** Update the account's persisted profile fields. Requires the account key. */
export const updateUserAccount = async (
    input: Partial<{
        name: string
        favoriteGenres: string[]
        preferredMoods: string[]
        readingGoal: number
        readingLevel: string
    }> & { email: string }
): Promise<SyncResult> => updateAccount(input)

/**
 * Fetch a user's persisted profile. Returns null when the account does not
 * exist (or the API is unreachable).
 */
export const fetchUserAccount = async (email: string): Promise<ServerProfile | null> => {
    const account = await fetchAccount(email)
    return account ? toServerProfile(account) : null
}

/** Delete the account from D1 (client-side "delete my data"). */
export const deleteUserAccount = async (email: string): Promise<boolean> =>
    deleteAccount(email)

/**
 * 🗄️ User Repository — database-backed accounts with local fallback
 * Chain-of-Thought:
 *   - Local-only (default): accounts live in localStorage (works everywhere).
 *   - Database-backed (when Supabase env vars are configured): accounts are
 *     real rows in the `profiles` table + a Supabase Auth identity.
 *
 * This keeps the app fully functional with zero config, and upgrades to real
 * DB accounts the moment `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY` are set.
 */

import { getSupabaseClient } from './supabaseClient'

export interface ServerProfile {
    email: string
    name: string
    favorite_genres: string[]
    reading_goal: number
    reading_level: string
    updated_at: string
}

export interface SyncResult {
    synced: boolean
    email?: string
    error?: string
}

// Deterministic local id generator (never shipped to the DB)
const makeLocalId = () => `u-${Date.now().toString(36)}`

// ─── Sync guard ─────────────────────────────────────────────────────────────
// Chain-of-Thought: syncAccountToServer fires on every app mount. Attempting
// `auth.signUp` on every mount (even for accounts that already exist) trips
// Supabase's signup rate limiter (HTTP 429). Persist a marker so we attempt
// the server sync at most once per hour per account — the app still works
// fully locally in between, and retries hourly so accounts catch up as soon
// as the DB schema exists.

const SYNC_MARKER_KEY = 'goodbooks_sync_marker'
const SYNC_INTERVAL_MS = 60 * 60 * 1000 // 1 hour

const wasRecentlySynced = (email: string): boolean => {
    try {
        const raw = localStorage.getItem(SYNC_MARKER_KEY)
        if (!raw) return false
        const marker = JSON.parse(raw) as { email: string; ts: number }
        return marker.email === email && Date.now() - marker.ts < SYNC_INTERVAL_MS
    } catch {
        return false
    }
}

const markSynced = (email: string): void => {
    try {
        localStorage.setItem(
            SYNC_MARKER_KEY,
            JSON.stringify({ email, ts: Date.now() })
        )
    } catch {
        // localStorage unavailable — best-effort guard only.
    }
}

/**
 * Push the local account to the database (upsert).
 * No-op (returns { synced: false }) when Supabase isn't configured or the
 * account synced within the last hour.
 */
export const syncUserAccount = async (input: {
    email: string
    name: string
    favoriteGenres: string[]
    readingGoal: number
    readingLevel: string
}): Promise<SyncResult> => {
    const supabase = getSupabaseClient()
    if (!supabase) return { synced: false }
    if (wasRecentlySynced(input.email)) return { synced: false }

    try {
        // 1) Ensure a real auth identity exists (random password — email confirm off
        //    in dev; a proper password/magic-link flow can be layered later).
        const { error: signUpError } = await supabase.auth.signUp({
            email: input.email,
            password: makeLocalId().replace('u-', '') + '!GoodBooks'
        })
        if (signUpError) {
            const message = signUpError.message.toLowerCase()
            // Account already exists → treat as synced and move on.
            if (message.includes('already registered')) {
                markSynced(input.email)
                return { synced: true, email: input.email }
            }
            // Rate-limited → back off so we stop hammering the endpoint.
            if (signUpError.status === 429 || message.includes('rate')) {
                markSynced(input.email)
                return { synced: false, email: input.email }
            }
            return { synced: false, email: input.email, error: signUpError.message }
        }

        // 2) Upsert the public profile row.
        const profile: ServerProfile = {
            email: input.email,
            name: input.name,
            favorite_genres: input.favoriteGenres,
            reading_goal: input.readingGoal,
            reading_level: input.readingLevel,
            updated_at: new Date().toISOString()
        }
        const { error: upsertError } = await supabase
            .from('profiles')
            .upsert(profile, { onConflict: 'email' })

        if (upsertError) {
            // Table may not exist yet (schema not applied) — still back off so
            // we don't spam; the hourly retry will pick it up once it exists.
            markSynced(input.email)
            return { synced: false, email: input.email, error: upsertError.message }
        }
        markSynced(input.email)
        return { synced: true, email: input.email }
    } catch (error) {
        console.warn('[User] Database sync failed (continuing locally):', error)
        return { synced: false, email: input.email }
    }
}

/**
 * Fetch a user's profile from the database.
 * Returns null when unconfigured or not found.
 */
export const fetchUserAccount = async (
    email: string
): Promise<ServerProfile | null> => {
    const supabase = getSupabaseClient()
    if (!supabase) return null

    try {
        const { data, error } = await supabase
            .from('profiles')
            .select('*')
            .eq('email', email)
            .maybeSingle()

        if (error || !data) return null
        return data as ServerProfile
    } catch (error) {
        console.warn('[User] Failed to fetch account from database:', error)
        return null
    }
}

/**
 * 🔌 Supabase Client (lazy)
 * Chain-of-Thought: Create the Supabase client only when env vars are present.
 * When unconfigured, the app gracefully runs on localStorage accounts
 * (the established resilience pattern) — no errors, no console spam.
 *
 * Configure via:
 *   VITE_SUPABASE_URL      https://<project>.supabase.co
 *   VITE_SUPABASE_ANON_KEY (anon/public key — safe for the client)
 */

import { createClient, type SupabaseClient } from '@supabase/supabase-js'

let client: SupabaseClient | null = null

export const isSupabaseConfigured = (): boolean =>
    Boolean(import.meta.env.VITE_SUPABASE_URL && import.meta.env.VITE_SUPABASE_ANON_KEY)

/**
 * Lazy singleton client. Returns null when not configured so callers can
 * degrade gracefully.
 */
export const getSupabaseClient = (): SupabaseClient | null => {
    if (!isSupabaseConfigured()) return null
    if (client) return client
    client = createClient(
        import.meta.env.VITE_SUPABASE_URL as string,
        import.meta.env.VITE_SUPABASE_ANON_KEY as string
    )
    return client
}

export type { SupabaseClient }

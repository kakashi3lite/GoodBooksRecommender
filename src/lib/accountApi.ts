/**
 * 👤 Account API client — same-origin `/api/accounts` (Cloudflare D1)
 *
 * Chain-of-Thought
 *   - The account has to survive a browser wipe, so it must live on the server.
 *   - The app is already served by Cloudflare Pages, so a relative URL hits the
 *     Pages Function that owns the D1 database: no CORS, no extra host, no key
 *     in the browser bundle.
 *   - Offline-first stays intact: every call returns a typed "not synced"
 *     result instead of throwing, so reducers keep working when the network or
 *     the binding is unavailable.
 *   - Ownership of a row is proven with an `accountKey` minted once by the
 *     server and kept in localStorage. It is the account's only secret, so it
 *     is never logged and never placed in the Redux store.
 */

export interface ServerAccount {
    id: string
    email: string
    name: string
    favoriteGenres: string[]
    preferredMoods: string[]
    readingGoal: number
    readingLevel: string
    createdAt: string
    updatedAt: string
}

export interface AccountSyncResult {
    synced: boolean
    email?: string
    created?: boolean
    error?: string
}

export interface AccountInput {
    email: string
    name: string
    favoriteGenres: string[]
    preferredMoods?: string[]
    readingGoal: number
    readingLevel: string
}

const ACCOUNT_KEY_STORAGE = 'goodbooks_account_key'
const SYNC_MARKER_KEY = 'goodbooks_sync_marker'
const SYNC_INTERVAL_MS = 5 * 60 * 1000
const REQUEST_TIMEOUT_MS = 6000

/**
 * The single email rule for the product — the onboarding form and the server
 * (`functions/api/accounts`) must agree, or a form that says "valid" produces a
 * silent `synced: false` and the reader believes their account was saved.
 */
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/

/** True when the address will be accepted by `/api/accounts`. */
export const isValidAccountEmail = (email: string): boolean =>
    EMAIL_RE.test(email.trim().toLowerCase())

type KeyMap = Record<string, string>

const readKeyMap = (): KeyMap => {
    try {
        const raw = localStorage.getItem(ACCOUNT_KEY_STORAGE)
        if (!raw) return {}
        const parsed: unknown = JSON.parse(raw)
        return parsed && typeof parsed === 'object' ? (parsed as KeyMap) : {}
    } catch {
        return {}
    }
}

/** The bearer key for this email, or null when this device never created it. */
export const getAccountKey = (email: string): string | null => {
    const key = readKeyMap()[email.trim().toLowerCase()]
    return typeof key === 'string' && key.length > 0 ? key : null
}

const saveAccountKey = (email: string, key: string): void => {
    try {
        const map = readKeyMap()
        map[email.trim().toLowerCase()] = key
        localStorage.setItem(ACCOUNT_KEY_STORAGE, JSON.stringify(map))
    } catch {
        // Storage unavailable (private mode) — the account still exists server-side.
    }
}

export const forgetAccountKey = (email: string): void => {
    try {
        const map = readKeyMap()
        delete map[email.trim().toLowerCase()]
        localStorage.setItem(ACCOUNT_KEY_STORAGE, JSON.stringify(map))
    } catch {
        // ignore
    }
}

const wasRecentlySynced = (email: string): boolean => {
    try {
        const raw = localStorage.getItem(SYNC_MARKER_KEY)
        if (!raw) return false
        const marker = JSON.parse(raw) as { email?: string; ts?: number }
        return (
            marker.email === email &&
            typeof marker.ts === 'number' &&
            Date.now() - marker.ts < SYNC_INTERVAL_MS
        )
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
        // best-effort guard only
    }
}

/** True when a same-origin account API can be reached from this runtime. */
const canReachApi = (): boolean =>
    typeof window !== 'undefined' && typeof fetch === 'function'

const request = async (
    path: string,
    init: RequestInit & { accountKey?: string } = {}
): Promise<Response> => {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
    const { accountKey, headers, ...rest } = init
    try {
        return await fetch(path, {
            ...rest,
            signal: controller.signal,
            headers: {
                ...(rest.body ? { 'Content-Type': 'application/json' } : {}),
                ...(accountKey ? { 'X-Account-Key': accountKey } : {}),
                ...(headers as Record<string, string> | undefined)
            }
        })
    } finally {
        clearTimeout(timer)
    }
}

interface AccountResponse {
    created?: boolean
    exists?: boolean
    accountKey?: string
    account?: ServerAccount
    error?: string
}

/**
 * Create the account, or update it when this device still holds the key.
 * Idempotent: safe to call on every app mount.
 */
/**
 * One in-flight sync per email. Onboarding dispatches a forced sync and the
 * App-mount effect dispatches another in the same tick — without this both
 * requests race, the loser gets `exists: true`, and the network tab shows a
 * duplicate create.
 */
const inFlightSyncs = new Map<string, Promise<AccountSyncResult>>()

const runSync = async (
    input: AccountInput,
    options: { force?: boolean } = {}
): Promise<AccountSyncResult> => {
    const email = input.email.trim().toLowerCase()
    if (!email || !canReachApi()) return { synced: false, email }
    // Reject here exactly what the server rejects — otherwise the form looks
    // valid, the request fails and the reader is told nothing.
    if (!isValidAccountEmail(email)) return { synced: false, email, error: 'invalid_email' }
    if (!options.force && wasRecentlySynced(email)) return { synced: false, email }

    try {
        const storedKey = getAccountKey(email)
        const res = await request('/api/accounts', {
            method: 'POST',
            accountKey: storedKey ?? undefined,
            body: JSON.stringify({
                email,
                name: input.name,
                favoriteGenres: input.favoriteGenres,
                preferredMoods: input.preferredMoods ?? [],
                readingGoal: input.readingGoal,
                readingLevel: input.readingLevel
            })
        })

        const payload = (await res.json().catch(() => ({}))) as AccountResponse

        // 401 → this device's key no longer matches the row (account was
        // re-created elsewhere). Drop it so the next sync creates a fresh one.
        if (res.status === 401) {
            forgetAccountKey(email)
            return { synced: false, email, error: 'invalid_key' }
        }
        if (!res.ok) {
            return { synced: false, email, error: payload.error ?? `http_${res.status}` }
        }

        if (payload.accountKey) saveAccountKey(email, payload.accountKey)
        markSynced(email)
        return { synced: true, email, created: payload.created === true }
    } catch (error) {
        console.warn('[Account] Sync failed (continuing locally):', error)
        return { synced: false, email }
    }
}

export const syncAccount = (
    input: AccountInput,
    options: { force?: boolean } = {}
): Promise<AccountSyncResult> => {
    const email = input.email.trim().toLowerCase()
    const pending = inFlightSyncs.get(email)
    if (pending) return pending

    const promise = runSync(input, options).finally(() => {
        inFlightSyncs.delete(email)
    })
    inFlightSyncs.set(email, promise)
    return promise
}

/** Read a profile from D1. Returns null when unconfigured or not found. */
export const fetchAccount = async (email: string): Promise<ServerAccount | null> => {
    const normalised = email.trim().toLowerCase()
    if (!normalised || !canReachApi()) return null
    try {
        const res = await request(`/api/accounts/${encodeURIComponent(normalised)}`)
        if (!res.ok) return null
        const payload = (await res.json()) as { account?: ServerAccount }
        return payload.account ?? null
    } catch (error) {
        console.warn('[Account] Fetch failed:', error)
        return null
    }
}

/** Update the account. Requires this device to hold the account key. */
export const updateAccount = async (
    input: Partial<AccountInput> & { email: string }
): Promise<AccountSyncResult> => {
    const email = input.email.trim().toLowerCase()
    const key = getAccountKey(email)
    if (!email || !key || !canReachApi()) return { synced: false, email }

    try {
        const res = await request(`/api/accounts/${encodeURIComponent(email)}`, {
            method: 'PATCH',
            accountKey: key,
            body: JSON.stringify(input)
        })
        if (!res.ok) {
            const payload = (await res.json().catch(() => ({}))) as AccountResponse
            return { synced: false, email, error: payload.error ?? `http_${res.status}` }
        }
        markSynced(email)
        return { synced: true, email }
    } catch (error) {
        console.warn('[Account] Update failed:', error)
        return { synced: false, email }
    }
}

/** Delete the account (and its key) — the client-side "delete my data" path. */
export const deleteAccount = async (email: string): Promise<boolean> => {
    const normalised = email.trim().toLowerCase()
    const key = getAccountKey(normalised)
    if (!normalised || !key || !canReachApi()) return false

    try {
        const res = await request(`/api/accounts/${encodeURIComponent(normalised)}`, {
            method: 'DELETE',
            accountKey: key
        })
        if (res.ok) {
            forgetAccountKey(normalised)
            try {
                localStorage.removeItem(SYNC_MARKER_KEY)
            } catch {
                // storage unavailable — nothing to clear
            }
            return true
        }
        return false
    } catch (error) {
        console.warn('[Account] Delete failed:', error)
        return false
    }
}

/** Number of accounts stored in D1 — used by health checks and the docs. */
export const fetchAccountCount = async (): Promise<number | null> => {
    if (!canReachApi()) return null
    try {
        const res = await request('/api/accounts')
        if (!res.ok) return null
        const payload = (await res.json()) as { count?: number }
        return typeof payload.count === 'number' ? payload.count : null
    } catch {
        return null
    }
}

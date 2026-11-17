/**
 * 👤 /api/accounts — customer accounts on Cloudflare D1 (edge CRUD)
 *
 *   GET    /api/accounts                → { count, database: 'd1' }  (health probe)
 *   POST   /api/accounts                → create; returns the one-time account key
 *   GET    /api/accounts/:email         → public profile (also `?email=`)
 *   PATCH  /api/accounts/:email         → update  (requires X-Account-Key)
 *   DELETE /api/accounts/:email         → delete  (requires X-Account-Key)
 *
 * Security model
 *   - Onboarding collects an email and a name only, so there is no password to
 *     verify. Instead the server mints a 256-bit bearer key at creation time
 *     and returns it exactly once. Only its SHA-256 hash is stored, so a
 *     database dump cannot be replayed as a login.
 *   - Writes (PATCH/DELETE) require that key. Reads are limited to the profile
 *     fields the reader chose to share (never the key, never the hash).
 *   - Same-origin only: the browser calls a relative `/api/accounts` URL, so no
 *     CORS grant is needed and no third-party origin can read the endpoint.
 *   - Responses are `no-store` — an account row must never be served from an
 *     intermediary cache.
 *
 * Why D1 (and not Supabase)
 *   The app is served by Cloudflare Pages; the D1 binding needs no external
 *   credentials, no pool, no cold start, and lives in the same colo as the
 *   request. See docs/DATA_LAYER.md → "Customer accounts".
 */
import { enforceRateLimit } from '../_lib/rateLimit'
import { type D1DatabaseLike, type PagesEnv, type PagesFunction } from '../_lib/types'

const json = (data: unknown, status = 200, extra: Record<string, string> = {}): Response =>
    new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Cache-Control': 'no-store',
            'X-Content-Type-Options': 'nosniff',
            ...extra
        }
    })

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const READING_LEVELS = new Set(['novice', 'intermediate', 'expert'])
const MAX_GENRES = 24

interface AccountInput {
    email?: unknown
    name?: unknown
    favoriteGenres?: unknown
    favorite_genres?: unknown
    preferredMoods?: unknown
    preferred_moods?: unknown
    readingGoal?: unknown
    reading_goal?: unknown
    readingLevel?: unknown
    reading_level?: unknown
}

interface AccountRow {
    id: string
    email: string
    name: string
    favorite_genres: string
    preferred_moods: string
    reading_goal: number
    reading_level: string
    account_key_hash: string
    created_at: string
    updated_at: string
}

/** Wire shape returned to the browser (never includes the key or its hash). */
interface PublicAccount {
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

const cleanString = (value: unknown, max: number): string =>
    typeof value === 'string' ? value.trim().slice(0, max) : ''

const normaliseEmail = (value: unknown): string | null => {
    const email = cleanString(value, 254).toLowerCase()
    return EMAIL_RE.test(email) ? email : null
}

const parseJsonArray = (value: string, max: number): string[] => {
    try {
        const parsed: unknown = JSON.parse(value)
        return Array.isArray(parsed)
            ? parsed.filter((v): v is string => typeof v === 'string').slice(0, max)
            : []
    } catch {
        return []
    }
}

const cleanList = (value: unknown): string[] => {
    if (!Array.isArray(value)) return []
    const seen = new Set<string>()
    for (const item of value) {
        const text = cleanString(item, 40)
        if (text) seen.add(text)
        if (seen.size >= MAX_GENRES) break
    }
    return [...seen]
}

const toInt = (value: unknown, fallback: number, min: number, max: number): number => {
    const n = typeof value === 'number' ? value : Number(value)
    if (!Number.isFinite(n)) return fallback
    return Math.max(min, Math.min(max, Math.round(n)))
}

const toPublic = (row: AccountRow): PublicAccount => ({
    id: row.id,
    email: row.email,
    name: row.name,
    favoriteGenres: parseJsonArray(row.favorite_genres, MAX_GENRES),
    preferredMoods: parseJsonArray(row.preferred_moods, MAX_GENRES),
    readingGoal: row.reading_goal,
    readingLevel: row.reading_level,
    createdAt: row.created_at,
    updatedAt: row.updated_at
})

/** Handles both the legacy `string` and the current `string[]` splat shapes. */
const pathSegments = (route: unknown): string[] => {
    const raw = Array.isArray(route)
        ? route.map(String)
        : typeof route === 'string'
          ? route.split('/')
          : []
    return raw
        .filter(Boolean)
        .map((segment) => {
            // The browser sends `encodeURIComponent(email)` → `%40`. Pages does
            // not always decode the splat, and a literal `%40` fails validation.
            try {
                return decodeURIComponent(segment)
            } catch {
                return segment
            }
        })
}

const randomToken = (bytes: number): string => {
    const buffer = new Uint8Array(bytes)
    crypto.getRandomValues(buffer)
    return [...buffer].map((b) => b.toString(16).padStart(2, '0')).join('')
}

const sha256 = async (value: string): Promise<string> => {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
    return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

/** Constant-time comparison — a hash check must not leak a prefix match. */
const timingSafeEqual = (a: string, b: string): boolean => {
    if (a.length !== b.length) return false
    let diff = 0
    for (let i = 0; i < a.length; i += 1) diff |= a.charCodeAt(i) ^ b.charCodeAt(i)
    return diff === 0
}

const findRow = async (db: D1DatabaseLike, email: string): Promise<AccountRow | null> =>
    db
        .prepare('select * from accounts where email = ?1 collate nocase limit 1')
        .bind(email)
        .first<AccountRow>()

const audit = async (
    db: D1DatabaseLike,
    action: 'created' | 'updated' | 'deleted',
    accountId: string,
    email: string
): Promise<void> => {
    try {
        await db
            .prepare(
                'insert into account_events (account_id, email, action, created_at) values (?1, ?2, ?3, ?4)'
            )
            .bind(accountId, email, action, new Date().toISOString())
            .run()
    } catch {
        // Audit is evidence, not correctness — never fail a write over it.
    }
}

/**
 * Build the write payload, merging onto an existing row so a partial PATCH
 * cannot wipe fields the client did not send.
 */
const previousLevel = (existing?: AccountRow): string =>
    READING_LEVELS.has(existing?.reading_level ?? '') ? (existing as AccountRow).reading_level : 'novice'

const listValue = (primary: unknown, legacy: unknown): unknown[] | undefined => {
    if (Array.isArray(primary)) return primary
    if (Array.isArray(legacy)) return legacy
    return undefined
}

const buildFields = (body: AccountInput, existing?: AccountRow) => {
    // Only an actual array may replace a stored list — a malformed value must
    // never silently wipe the reader's saved genres/moods.
    const genres = listValue(body.favoriteGenres, body.favorite_genres)
    const moods = listValue(body.preferredMoods, body.preferred_moods)
    const goal = body.readingGoal ?? body.reading_goal
    const level = body.readingLevel ?? body.reading_level
    const name = cleanString(body.name, 80)
    const nextLevel = cleanString(level, 24).toLowerCase()

    return {
        name: name || existing?.name || '',
        favoriteGenres:
            genres === undefined
                ? parseJsonArray(existing?.favorite_genres ?? '[]', MAX_GENRES)
                : cleanList(genres),
        preferredMoods:
            moods === undefined
                ? parseJsonArray(existing?.preferred_moods ?? '[]', MAX_GENRES)
                : cleanList(moods),
        readingGoal:
            goal === undefined
                ? (existing?.reading_goal ?? 24)
                : toInt(goal, existing?.reading_goal ?? 24, 1, 1000),
        readingLevel: READING_LEVELS.has(nextLevel) ? nextLevel : previousLevel(existing)
    }
}

const rowFromFields = (
    base: AccountRow,
    fields: ReturnType<typeof buildFields>,
    updatedAt: string
): AccountRow => ({
    ...base,
    name: fields.name || base.name,
    favorite_genres: JSON.stringify(fields.favoriteGenres),
    preferred_moods: JSON.stringify(fields.preferredMoods),
    reading_goal: fields.readingGoal,
    reading_level: fields.readingLevel,
    updated_at: updatedAt
})

const dbMissing = (): Response =>
    json(
        {
            error: 'database_not_configured',
            message:
                'The D1 binding "DB" is missing. Add [[d1_databases]] to wrangler.toml and redeploy.'
        },
        503
    )

const accountKeyHeader = (request: Request): string =>
    (request.headers.get('X-Account-Key') ?? '').trim()

const ownsRow = async (row: AccountRow, providedKey: string): Promise<boolean> =>
    Boolean(providedKey) && timingSafeEqual(await sha256(providedKey), row.account_key_hash)

const readJson = async (request: Request): Promise<AccountInput | null> => {
    try {
        return (await request.json()) as AccountInput
    } catch {
        return null
    }
}

// ─── POST /api/accounts (create, or idempotent update with a valid key) ─────

const createOrUpdate = async (request: Request, db: D1DatabaseLike): Promise<Response> => {
    const body = await readJson(request)
    if (!body) return json({ error: 'invalid', message: 'Expected a JSON body' }, 400)

    const email = normaliseEmail(body.email)
    if (!email) return json({ error: 'invalid_email' }, 400)

    const name = cleanString(body.name, 80)
    if (!name) return json({ error: 'invalid_name', message: 'Name is required' }, 400)

    const providedKey = accountKeyHeader(request)
    const existing = await findRow(db, email)

    if (existing) {
        if (!providedKey) {
            // The address already has an account. Returning the profile here
            // would turn a write endpoint into an unauthenticated read oracle,
            // and answering 200 would hide the conflict from the reader (their
            // profile would silently never persist).
            return json({ error: 'email_taken' }, 409)
        }
        if (!(await ownsRow(existing, providedKey))) {
            return json({ error: 'invalid_key' }, 401)
        }

        const fields = buildFields(body, existing)
        const updatedAt = new Date().toISOString()
        await db
            .prepare(
                `update accounts
                    set name = ?1, favorite_genres = ?2, preferred_moods = ?3,
                        reading_goal = ?4, reading_level = ?5, updated_at = ?6
                  where id = ?7`
            )
            .bind(
                fields.name || existing.name,
                JSON.stringify(fields.favoriteGenres),
                JSON.stringify(fields.preferredMoods),
                fields.readingGoal,
                fields.readingLevel,
                updatedAt,
                existing.id
            )
            .run()
        await audit(db, 'updated', existing.id, email)

        return json({
            created: false,
            exists: true,
            account: toPublic(rowFromFields(existing, fields, updatedAt))
        })
    }

    const fields = buildFields(body)
    const accountKey = providedKey || randomToken(32)
    const accountKeyHash = await sha256(accountKey)
    const now = new Date().toISOString()
    const id = crypto.randomUUID()

    try {
        await db
            .prepare(
                `insert into accounts
                    (id, email, name, favorite_genres, preferred_moods, reading_goal,
                     reading_level, account_key_hash, created_at, updated_at)
                 values (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)`
            )
            .bind(
                id,
                email,
                fields.name || 'Reader',
                JSON.stringify(fields.favoriteGenres),
                JSON.stringify(fields.preferredMoods),
                fields.readingGoal,
                fields.readingLevel,
                accountKeyHash,
                now,
                now
            )
            .run()
    } catch (error) {
        // Racing creates: the unique email index is the arbiter.
        const raced = await findRow(db, email)
        if (raced) {
            return json({ error: 'email_taken' }, 409)
        }
        console.error('[accounts] insert failed:', error)
        return json({ error: 'db_error' }, 500)
    }

    await audit(db, 'created', id, email)

    return json(
        {
            created: true,
            // Returned exactly once — the client stores it and proves ownership
            // of future writes with it.
            accountKey,
            account: toPublic({
                id,
                email,
                name: fields.name || 'Reader',
                favorite_genres: JSON.stringify(fields.favoriteGenres),
                preferred_moods: JSON.stringify(fields.preferredMoods),
                reading_goal: fields.readingGoal,
                reading_level: fields.readingLevel,
                account_key_hash: accountKeyHash,
                created_at: now,
                updated_at: now
            })
        },
        201
    )
}

// ─── Handlers ──────────────────────────────────────────────────────────────

const handleGet = async (
    request: Request,
    db: D1DatabaseLike,
    segments: string[]
): Promise<Response> => {
    const url = new URL(request.url)
    const rawEmail = segments[0] ?? url.searchParams.get('email') ?? ''

    // Health probe: lets the deployed app assert the binding is live without
    // exposing a single customer record.
    if (!rawEmail) {
        const row = await db
            .prepare('select count(*) as count from accounts')
            .first<{ count: number }>()
        return json({ database: 'd1', count: Number(row?.count ?? 0) })
    }

    const email = normaliseEmail(rawEmail)
    if (!email) return json({ error: 'invalid_email' }, 400)

    // Owner-only read. A missing row and a wrong key both answer 401 so the
    // endpoint cannot be used to confirm whether an address has an account.
    const providedKey = accountKeyHeader(request)
    if (!providedKey) return json({ error: 'missing_key' }, 401)

    const row = await findRow(db, email)
    if (!row || !(await ownsRow(row, providedKey))) {
        return json({ error: 'invalid_key' }, 401)
    }
    return json({ account: toPublic(row) })
}

const handlePatch = async (
    request: Request,
    db: D1DatabaseLike,
    segments: string[]
): Promise<Response> => {
    const url = new URL(request.url)
    const email = normaliseEmail(segments[0] ?? url.searchParams.get('email'))
    if (!email) return json({ error: 'invalid_email' }, 400)

    const existing = await findRow(db, email)
    const providedKey = accountKeyHeader(request)
    if (!existing || !providedKey || !(await ownsRow(existing, providedKey))) {
        // Same shape for "no such account" and "wrong key".
        return json({ error: 'invalid_key' }, 401)
    }

    const body = await readJson(request)
    if (!body) return json({ error: 'invalid', message: 'Expected a JSON body' }, 400)

    const fields = buildFields(body, existing)
    const updatedAt = new Date().toISOString()

    await db
        .prepare(
            `update accounts
                set name = ?1, favorite_genres = ?2, preferred_moods = ?3,
                    reading_goal = ?4, reading_level = ?5, updated_at = ?6
              where id = ?7`
        )
        .bind(
            fields.name || existing.name,
            JSON.stringify(fields.favoriteGenres),
            JSON.stringify(fields.preferredMoods),
            fields.readingGoal,
            fields.readingLevel,
            updatedAt,
            existing.id
        )
        .run()
    await audit(db, 'updated', existing.id, email)

    return json({ account: toPublic(rowFromFields(existing, fields, updatedAt)) })
}

const handleDelete = async (
    request: Request,
    db: D1DatabaseLike,
    segments: string[]
): Promise<Response> => {
    const url = new URL(request.url)
    const email = normaliseEmail(segments[0] ?? url.searchParams.get('email'))
    if (!email) return json({ error: 'invalid_email' }, 400)

    const existing = await findRow(db, email)
    const providedKey = accountKeyHeader(request)
    if (!existing || !providedKey || !(await ownsRow(existing, providedKey))) {
        return json({ error: 'invalid_key' }, 401)
    }

    await db.prepare('delete from accounts where id = ?1').bind(existing.id).run()
    await audit(db, 'deleted', existing.id, email)

    return json({ deleted: true, email })
}

const onRequest: PagesFunction<PagesEnv> = async (context) => {
    const { request, env, params } = context
    const db = env.DB
    if (!db) return dbMissing()

    const segments = pathSegments(params.route)

    // Preflights carry no cost and must not consume a caller's quota.
    if (request.method === 'OPTIONS') {
        return new Response(null, {
            status: 204,
            headers: { Allow: 'GET, HEAD, POST, PATCH, DELETE, OPTIONS' }
        })
    }

    const limit =
        request.method === 'POST'
            ? { scope: 'accounts-write', limit: 20, windowSeconds: 600 }
            : request.method === 'GET' || request.method === 'HEAD'
              ? { scope: 'accounts-read', limit: 60, windowSeconds: 60 }
              : { scope: 'accounts-mutate', limit: 30, windowSeconds: 60 }
    const limited = await enforceRateLimit(env, request, limit)
    if (limited) return limited

    switch (request.method) {
        case 'GET':
        // HEAD must behave like GET without a body — Cloudflare keeps the
        // status/headers and drops the payload.
        case 'HEAD':
            return handleGet(request, db, segments)
        case 'POST':
            return createOrUpdate(request, db)
        case 'PATCH':
            return handlePatch(request, db, segments)
        case 'DELETE':
            return handleDelete(request, db, segments)
        case 'OPTIONS':
            return new Response(null, {
                status: 204,
                headers: { Allow: 'GET, HEAD, POST, PATCH, DELETE, OPTIONS' }
            })
        default:
            return json({ error: 'method_not_allowed' }, 405, {
                Allow: 'GET, HEAD, POST, PATCH, DELETE, OPTIONS'
            })
    }
}

export const onRequestGet = onRequest
export const onRequestPost = onRequest
export const onRequestPatch = onRequest
export const onRequestDelete = onRequest
export const onRequestOptions = onRequest
/** HEAD mirrors GET (HTTP semantics: same status, no body). */
export const onRequestHead = onRequest
/**
 * Any other method (PUT, TRACE, …). Without this export Pages falls through to
 * the `/api/*` catch-all, which answers a misleading 404; a known route should
 * answer 405 with its `Allow` list instead.
 */
export { onRequest }

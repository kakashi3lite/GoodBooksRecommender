/**
 * 🚦 Edge rate limiting (D1 fixed window)
 *
 * Chain-of-Thought: Cloudflare's zone-level rate-limit rule exists on this
 * project but does not enforce on the current plan (verified: 80 rapid requests
 * to /api/accounts all returned 200), so the Functions keep their own counter.
 *
 * - Fixed window per (scope, client, window): one D1 upsert with RETURNING, so
 *   the check costs a single round-trip on the limited routes only.
 * - The stored key is a SHA-256 of `salt|ip` — no raw IP address is persisted.
 * - Fails **open** when D1 is unavailable: a database hiccup must not take the
 *   API down, and these limits are abuse control, not authorisation.
 */
import { type D1DatabaseLike, type PagesEnv } from './types'

export interface RateLimitOptions {
    /** Logical bucket, e.g. `accounts-write`; one bucket per scope+client+window. */
    scope: string
    /** Requests allowed per window. */
    limit: number
    /** Window length in seconds. */
    windowSeconds: number
}

const jsonError = (retryAfter: number): Response =>
    new Response(JSON.stringify({ error: 'rate_limited', retryAfter }), {
        status: 429,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Cache-Control': 'no-store',
            'Retry-After': String(retryAfter),
            'X-Content-Type-Options': 'nosniff'
        }
    })

const sha256 = async (value: string): Promise<string> => {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value))
    return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

/** Cloudflare always sets CF-Connecting-IP at the edge; fall back defensively. */
const clientIp = (request: Request): string =>
    request.headers.get('CF-Connecting-IP') ??
    request.headers.get('X-Forwarded-For')?.split(',')[0]?.trim() ??
    'unknown'

/**
 * Returns a `429` response when the caller is over the limit, otherwise null.
 * Never throws.
 */
export const enforceRateLimit = async (
    env: PagesEnv,
    request: Request,
    { scope, limit, windowSeconds }: RateLimitOptions
): Promise<Response | null> => {
    const db: D1DatabaseLike | undefined = env.DB
    if (!db) return null

    const now = Math.floor(Date.now() / 1000)
    const windowStart = now - (now % windowSeconds)
    const salt = env.RATE_LIMIT_SALT ?? 'goodbooks-rate-limit'
    const bucketKey = `${scope}:${await sha256(`${salt}|${clientIp(request)}`)}:${windowStart}`

    try {
        const row = await db
            .prepare(
                `insert into rate_limits (bucket_key, window_start, count)
                 values (?1, ?2, 1)
                 on conflict(bucket_key) do update set count = count + 1
                 returning count`
            )
            .bind(bucketKey, windowStart)
            .first<{ count: number }>()

        const count = Number(row?.count ?? 1)
        if (count <= limit) {
            // Opportunistic retention: keep the table tiny without a cron job.
            if (Math.random() < 0.01) {
                await db
                    .prepare('delete from rate_limits where window_start < ?1')
                    .bind(now - 86_400)
                    .run()
            }
            return null
        }

        return jsonError(Math.max(1, windowStart + windowSeconds - now))
    } catch {
        // Fail open — availability beats an abuse control.
        return null
    }
}

/**
 * 🚦 Edge rate limiter
 *
 * The zone-level WAF rule does not enforce on the current plan, so these limits
 * are the product's actual abuse control. They must count per client, stop at
 * the limit, never persist a raw IP, and fail open if D1 is unavailable.
 */

import { describe, expect, it } from 'vitest'
import { enforceRateLimit } from '../functions/api/_lib/rateLimit'

class RateDb {
    counts = new Map<string, number>()
    prepare(sql: string) {
        const state = this
        const stmt = {
            args: [] as unknown[],
            bind(...values: unknown[]) {
                this.args = values
                return this
            },
            async first<T>() {
                if (sql.includes('insert into rate_limits')) {
                    const key = String(this.args[0])
                    const next = (state.counts.get(key) ?? 0) + 1
                    state.counts.set(key, next)
                    return { count: next } as unknown as T
                }
                return null
            },
            async run() {
                return { success: true }
            },
            async all() {
                return { success: true, results: [] }
            }
        }
        return stmt
    }
    async batch() {
        return []
    }
    async exec() {
        return { count: 0, duration: 0 }
    }
}

const opts = { scope: 'test', limit: 3, windowSeconds: 60 }
const request = (ip: string) =>
    new Request('https://books.example/api/accounts', {
        headers: { 'CF-Connecting-IP': ip }
    })

describe('enforceRateLimit', () => {
    it('allows up to the limit and then answers 429 with Retry-After', async () => {
        const env = { DB: new RateDb(), RATE_LIMIT_SALT: 'salt' }

        for (let i = 0; i < 3; i += 1) {
            expect(await enforceRateLimit(env, request('203.0.113.7'), opts)).toBeNull()
        }

        const blocked = await enforceRateLimit(env, request('203.0.113.7'), opts)
        expect(blocked?.status).toBe(429)
        expect(Number(blocked?.headers.get('Retry-After'))).toBeGreaterThan(0)
        expect(await blocked?.json()).toMatchObject({ error: 'rate_limited' })
    })

    it('buckets per client', async () => {
        const env = { DB: new RateDb(), RATE_LIMIT_SALT: 'salt' }
        for (let i = 0; i < 3; i += 1) {
            await enforceRateLimit(env, request('198.51.100.1'), opts)
        }
        expect(await enforceRateLimit(env, request('198.51.100.2'), opts)).toBeNull()
    })

    it('never stores the raw client IP', async () => {
        const db = new RateDb()
        await enforceRateLimit({ DB: db, RATE_LIMIT_SALT: 'salt' }, request('203.0.113.7'), opts)
        for (const key of db.counts.keys()) {
            expect(key).not.toContain('203.0.113.7')
            expect(key).toMatch(/^test:[0-9a-f]{64}:\d+$/)
        }
    })

    it('fails open when the binding is missing', async () => {
        expect(await enforceRateLimit({}, request('203.0.113.7'), opts)).toBeNull()
    })
})

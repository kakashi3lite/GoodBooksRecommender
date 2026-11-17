/**
 * 👤 /api/accounts — CRUD contract tests
 *
 * Chain-of-Thought: the D1 binding cannot be reached from a unit test, so this
 * uses an in-memory stand-in that answers exactly the statements the handler
 * issues. The point is to lock the HTTP contract the browser depends on:
 * create → 201 + one-time key, read, key-guarded update, key-guarded delete.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
    onRequest,
    onRequestDelete,
    onRequestGet,
    onRequestHead,
    onRequestPatch,
    onRequestPost
} from '../functions/api/accounts/[[route]]'

interface Row {
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

class FakeStatement {
    args: unknown[] = []
    constructor(private readonly sql: string, private readonly state: FakeState) {}

    bind(...values: unknown[]): FakeStatement {
        this.args = values
        return this
    }

    async first<T>(): Promise<T | null> {
        if (this.sql.includes('count(*)')) {
            return { count: this.state.rows.size } as unknown as T
        }
        const email = String(this.args[0] ?? '').toLowerCase()
        const row = this.state.rows.get(email)
        return row ? ({ ...row } as unknown as T) : null
    }

    async all<T>(): Promise<{ results: T[]; success: boolean }> {
        return { results: [], success: true }
    }

    async run(): Promise<{ success: boolean }> {
        const state = this.state
        if (this.sql.startsWith('insert into accounts')) {
            const [id, email, name, genres, moods, goal, level, hash, created, updated] =
                this.args as string[]
            const key = String(email).toLowerCase()
            if (state.rows.has(key)) throw new Error('UNIQUE constraint failed: accounts.email')
            state.rows.set(key, {
                id,
                email: String(email),
                name: String(name),
                favorite_genres: String(genres),
                preferred_moods: String(moods),
                reading_goal: Number(goal),
                reading_level: String(level),
                account_key_hash: String(hash),
                created_at: String(created),
                updated_at: String(updated)
            })
            return { success: true }
        }

        if (this.sql.startsWith('update accounts')) {
            const [name, genres, moods, goal, level, updated, id] = this.args as string[]
            for (const row of state.rows.values()) {
                if (row.id === id) {
                    row.name = String(name)
                    row.favorite_genres = String(genres)
                    row.preferred_moods = String(moods)
                    row.reading_goal = Number(goal)
                    row.reading_level = String(level)
                    row.updated_at = String(updated)
                }
            }
            return { success: true }
        }

        if (this.sql.startsWith('delete from accounts')) {
            const id = String(this.args[0])
            for (const [key, row] of [...state.rows.entries()]) {
                if (row.id === id) state.rows.delete(key)
            }
            return { success: true }
        }

        if (this.sql.includes('insert into account_events')) {
            state.events.push(String(this.args[2]))
            return { success: true }
        }

        return { success: true }
    }
}

interface FakeState {
    rows: Map<string, Row>
    events: string[]
}

class FakeD1 {
    state: FakeState = { rows: new Map(), events: [] }
    prepare(sql: string) {
        return new FakeStatement(sql, this.state)
    }
    async batch() {
        return []
    }
    async exec() {
        return { count: 0, duration: 0 }
    }
}

const makeContext = (
    db: unknown,
    request: Request,
    route: string[] = []
): Parameters<typeof onRequestGet>[0] =>
    ({
        request,
        env: { DB: db },
        params: { route },
        waitUntil: () => undefined,
        next: async () => new Response(null)
    }) as unknown as Parameters<typeof onRequestGet>[0]

const post = (body: unknown, key?: string) =>
    new Request('https://books.example/api/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(key ? { 'X-Account-Key': key } : {}) },
        body: JSON.stringify(body)
    })

const newAccount = {
    email: 'Ada@Example.com',
    name: 'Ada Lovelace',
    favoriteGenres: ['Science Fiction', 'Fiction'],
    preferredMoods: ['thought-provoking'],
    readingGoal: 36,
    readingLevel: 'intermediate'
}

let db: FakeD1

beforeEach(() => {
    db = new FakeD1()
})

afterEach(() => {
    vi.restoreAllMocks()
})

describe('/api/accounts (D1 CRUD)', () => {
    it('creates an account, returns a one-time key, and normalises the email', async () => {
        const res = await onRequestPost(makeContext(db, post(newAccount)))
        const body = (await res.json()) as {
            created: boolean
            accountKey: string
            account: { email: string; favoriteGenres: string[] }
        }

        expect(res.status).toBe(201)
        expect(body.created).toBe(true)
        expect(body.accountKey).toHaveLength(64)
        expect(body.account.email).toBe('ada@example.com')
        expect(body.account.favoriteGenres).toEqual(['Science Fiction', 'Fiction'])
        expect(db.state.events).toEqual(['created'])
    })

    it('reads the account back by email for the key holder (case-insensitive)', async () => {
        const created = (await (
            await onRequestPost(makeContext(db, post(newAccount)))
        ).json()) as { accountKey: string }

        const res = await onRequestGet(
            makeContext(
                db,
                new Request('https://books.example/api/accounts', {
                    headers: { 'X-Account-Key': created.accountKey }
                }),
                ['ADA@example.com']
            )
        )
        const body = (await res.json()) as { account: { name: string; readingGoal: number } }

        expect(res.status).toBe(200)
        expect(body.account.name).toBe('Ada Lovelace')
        expect(body.account.readingGoal).toBe(36)
    })

    it('refuses an unauthenticated profile read (and does not reveal existence)', async () => {
        const created = (await (
            await onRequestPost(makeContext(db, post(newAccount)))
        ).json()) as { accountKey: string }

        const noKey = await onRequestGet(
            makeContext(db, new Request('https://books.example/api/accounts'), ['ada@example.com'])
        )
        expect(noKey.status).toBe(401)
        expect((await noKey.json()).error).toBe('missing_key')

        const wrongKey = await onRequestGet(
            makeContext(
                db,
                new Request('https://books.example/api/accounts', {
                    headers: { 'X-Account-Key': 'wrong' }
                }),
                ['ada@example.com']
            )
        )
        expect(wrongKey.status).toBe(401)
        expect((await wrongKey.json()).error).toBe('invalid_key')

        // Unknown address + wrong key answers exactly like a real one.
        const unknown = await onRequestGet(
            makeContext(
                db,
                new Request('https://books.example/api/accounts', {
                    headers: { 'X-Account-Key': created.accountKey }
                }),
                ['nobody@example.com']
            )
        )
        expect(unknown.status).toBe(401)
        expect((await unknown.json()).error).toBe('invalid_key')
    })

    it('rejects a key-less create for an existing email with 409 (no profile leak)', async () => {
        await onRequestPost(makeContext(db, post(newAccount)))

        const res = await onRequestPost(makeContext(db, post(newAccount)))
        const body = (await res.json()) as { error?: string; account?: unknown }

        expect(res.status).toBe(409)
        expect(body.error).toBe('email_taken')
        expect(body.account).toBeUndefined()
        expect(db.state.rows.size).toBe(1)
    })

    it('rejects an update without the account key', async () => {
        await onRequestPost(makeContext(db, post(newAccount)))

        const res = await onRequestPatch(
            makeContext(
                db,
                new Request('https://books.example/api/accounts/ada@example.com', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: 'Mallory' })
                }),
                ['ada@example.com']
            )
        )

        expect(res.status).toBe(401)
        expect((await res.json()).error).toBe('invalid_key')
    })

    it('rejects an update with the wrong account key', async () => {
        await onRequestPost(makeContext(db, post(newAccount)))

        const res = await onRequestPatch(
            makeContext(
                db,
                new Request('https://books.example/api/accounts/ada@example.com', {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', 'X-Account-Key': 'wrong' },
                    body: JSON.stringify({ name: 'Mallory' })
                }),
                ['ada@example.com']
            )
        )

        expect(res.status).toBe(401)
        expect((await res.json()).error).toBe('invalid_key')
    })

    it('updates the profile when the key is valid, keeping untouched fields', async () => {
        const created = (await (
            await onRequestPost(makeContext(db, post(newAccount)))
        ).json()) as { accountKey: string }

        const res = await onRequestPatch(
            makeContext(
                db,
                new Request('https://books.example/api/accounts/ada@example.com', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Account-Key': created.accountKey
                    },
                    body: JSON.stringify({ name: 'Ada L.', readingGoal: 50 })
                }),
                ['ada@example.com']
            )
        )
        const body = (await res.json()) as {
            account: { name: string; readingGoal: number; favoriteGenres: string[] }
        }

        expect(res.status).toBe(200)
        expect(body.account.name).toBe('Ada L.')
        expect(body.account.readingGoal).toBe(50)
        expect(body.account.favoriteGenres).toEqual(['Science Fiction', 'Fiction'])
    })

    it('never wipes stored fields when a malformed patch arrives', async () => {
        const created = (await (
            await onRequestPost(makeContext(db, post(newAccount)))
        ).json()) as { accountKey: string }

        const res = await onRequestPatch(
            makeContext(
                db,
                new Request('https://books.example/api/accounts/ada@example.com', {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Account-Key': created.accountKey
                    },
                    body: JSON.stringify({ favoriteGenres: 'Fantasy', readingGoal: 'lots' })
                }),
                ['ada@example.com']
            )
        )
        const body = (await res.json()) as {
            account: { favoriteGenres: string[]; readingGoal: number; name: string }
        }

        expect(res.status).toBe(200)
        expect(body.account.favoriteGenres).toEqual(['Science Fiction', 'Fiction'])
        expect(body.account.readingGoal).toBe(36)
        expect(body.account.name).toBe('Ada Lovelace')
    })

    it('deletes only with a valid key, and the row is gone afterwards', async () => {
        const created = (await (
            await onRequestPost(makeContext(db, post(newAccount)))
        ).json()) as { accountKey: string }

        const url = 'https://books.example/api/accounts/ada@example.com'
        const unauthorised = await onRequestDelete(
            makeContext(db, new Request(url, { method: 'DELETE' }), ['ada@example.com'])
        )
        expect(unauthorised.status).toBe(401)

        const deleted = await onRequestDelete(
            makeContext(
                db,
                new Request(url, { method: 'DELETE', headers: { 'X-Account-Key': created.accountKey } }),
                ['ada@example.com']
            )
        )
        expect(deleted.status).toBe(200)
        expect(db.state.rows.size).toBe(0)

        const after = await onRequestGet(makeContext(db, new Request(url), ['ada@example.com']))
        expect(after.status).toBe(401)
    })

    it('answers 401 (not 404) when the account does not exist', async () => {
        const url = 'https://books.example/api/accounts/ghost@example.com'
        const patch = await onRequestPatch(
            makeContext(
                db,
                new Request(url, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', 'X-Account-Key': 'k' },
                    body: JSON.stringify({ name: 'x' })
                }),
                ['ghost@example.com']
            )
        )
        expect(patch.status).toBe(401)

        const del = await onRequestDelete(
            makeContext(db, new Request(url, { method: 'DELETE', headers: { 'X-Account-Key': 'k' } }), [
                'ghost@example.com'
            ])
        )
        expect(del.status).toBe(401)
    })

    it('decodes a percent-encoded email in the path (what the browser sends)', async () => {
        const created = (await (
            await onRequestPost(makeContext(db, post(newAccount)))
        ).json()) as { accountKey: string }

        const res = await onRequestGet(
            makeContext(
                db,
                new Request('https://books.example/api/accounts', {
                    headers: { 'X-Account-Key': created.accountKey }
                }),
                ['ada%40example.com']
            )
        )
        const body = (await res.json()) as { account: { email: string } }

        expect(res.status).toBe(200)
        expect(body.account.email).toBe('ada@example.com')
    })

    it('rejects a malformed email with 400', async () => {
        const res = await onRequestPost(
            makeContext(db, post({ ...newAccount, email: 'not-an-email' }))
        )
        expect(res.status).toBe(400)
        expect((await res.json()).error).toBe('invalid_email')
    })

    it('answers 405 with an Allow list for unsupported methods', async () => {
        const res = await onRequest(
            makeContext(
                db,
                new Request('https://books.example/api/accounts', { method: 'PUT', body: '{}' })
            )
        )
        expect(res.status).toBe(405)
        expect(res.headers.get('Allow')).toContain('GET')
        expect(res.headers.get('Allow')).toContain('HEAD')
    })

    it('answers HEAD like GET so uptime checks work', async () => {
        const res = await onRequestHead(
            makeContext(db, new Request('https://books.example/api/accounts', { method: 'HEAD' }))
        )
        expect(res.status).toBe(200)
        expect(await res.json()).toMatchObject({ database: 'd1' })
    })

    it('answers 503 when the D1 binding is missing', async () => {
        const res = await onRequestGet({
            ...makeContext(undefined, new Request('https://books.example/api/accounts')),
            env: {}
        } as Parameters<typeof onRequestGet>[0])
        expect(res.status).toBe(503)
    })
})

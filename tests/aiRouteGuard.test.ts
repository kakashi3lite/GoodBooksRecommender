/**
 * 🛡️ /api/ai/* — abuse guards
 *
 * Chain-of-Thought: the chat endpoint is a proxy to a paid provider. CORS stops
 * other origins from *reading* a reply but not from spending the key, so the
 * route must reject cross-site callers, non-JSON bodies and oversized input
 * before any model call happens.
 */

import { describe, expect, it } from 'vitest'
import { onRequestPost } from '../functions/api/ai/[[route]]'

const ctx = (request: Request) =>
    ({
        request,
        env: {},
        params: { route: ['chat'] },
        waitUntil: () => undefined,
        next: async () => new Response(null)
    }) as unknown as Parameters<typeof onRequestPost>[0]

const post = (body: string | undefined, headers: Record<string, string> = {}) =>
    new Request('https://books.example/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...headers },
        body
    })

describe('/api/ai/chat abuse guards', () => {
    it('rejects a cross-origin caller before spending a provider token', async () => {
        const res = await onRequestPost(
            ctx(post(JSON.stringify({ message: 'hi' }), { Origin: 'https://evil.example' }))
        )
        expect(res.status).toBe(403)
        expect((await res.json()).error).toBe('forbidden_origin')
    })

    it('allows the same origin', async () => {
        const res = await onRequestPost(
            ctx(post(JSON.stringify({ message: '' }), { Origin: 'https://books.example' }))
        )
        // Reaches validation (empty message), i.e. the origin check passed.
        expect(res.status).toBe(400)
        expect((await res.json()).error).toBe('message_required')
    })

    it('rejects a non-JSON content type (blocks CORS-simple cross-site POSTs)', async () => {
        const res = await onRequestPost(
            ctx(post(JSON.stringify({ message: 'hi' }), { 'Content-Type': 'text/plain' }))
        )
        expect(res.status).toBe(415)
        expect((await res.json()).error).toBe('unsupported_media_type')
    })

    it('rejects an oversized body', async () => {
        const huge = JSON.stringify({ message: 'x', pad: 'y'.repeat(70 * 1024) })
        const res = await onRequestPost(ctx(post(huge)))
        expect(res.status).toBe(413)
        expect((await res.json()).error).toBe('payload_too_large')
    })

    it('rejects an over-long message', async () => {
        const res = await onRequestPost(ctx(post(JSON.stringify({ message: 'x'.repeat(3000) }))))
        expect(res.status).toBe(413)
        expect((await res.json())).toMatchObject({ error: 'message_too_long', maxChars: 2000 })
    })
})

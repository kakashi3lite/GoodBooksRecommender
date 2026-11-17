/**
 * 🤖 /api/ai/* — conversational AI endpoint (edge)
 *
 *   POST /api/ai/chat     body: { message, prefs?, context?, history?, shown? }
 *   POST /api/ai/insight  body: { context: { stats, persona, ... } }
 *
 * `context` carries the reader's REAL profile (genres, goal, pace, streak,
 * current book) from the client's localStorage log — used to personalize
 * the LLM reply. `history` carries the recent conversational turns and
 * `shown` the book ids already suggested this conversation, so the engine
 * rotates picks instead of returning the same titles every turn. Falls back
 * to the local hybrid engine when the LLM is unavailable — always real picks
 * and honest numbers, never fabricated.
 */
import {
    generateReadingInsight,
    handleChat,
    type ChatContext,
    type ChatTurn
} from '../_lib/ai'
import { enforceRateLimit } from '../_lib/rateLimit'
import { type PagesFunction } from '../_lib/types'

const MAX_BODY_BYTES = 64 * 1024
const MAX_MESSAGE_CHARS = 2000
const MAX_HISTORY_TURNS = 6
const MAX_TURN_CHARS = 1000
const MAX_SHOWN = 50

/** Host of an absolute URL, or null when absent/malformed. */
const hostOf = (value: string | null): string | null => {
    if (!value) return null
    try {
        return new URL(value).host
    } catch {
        return null
    }
}

const json = (body: unknown, status = 200): Response => {
    // Safety net: strip any raw control characters (other than \n \t \r) from
    // the serialized body. LLM replies and web-catalog text occasionally carry
    // stray control bytes that would make the payload invalid strict JSON and
    // break the client's response.json().
    const serialized = JSON.stringify(body).replace(
        /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g,
        ' '
    )
    return new Response(serialized, {
        status,
        headers: { 'Content-Type': 'application/json; charset=utf-8' }
    })
}

export const onRequestPost: PagesFunction = async (context) => {
    const { request, env, params } = context
    const route = Array.isArray(params.route) ? params.route[0] : params.route

    // This is a proxy to a paid provider. CORS blocks other origins from
    // *reading* a reply, but it does not stop them from spending the key — so
    // reject cross-site callers outright.
    const host = new URL(request.url).host
    const caller = hostOf(request.headers.get('Origin')) ?? hostOf(request.headers.get('Referer'))
    if (caller && caller !== host) {
        return json({ error: 'forbidden_origin' }, 403)
    }

    // JSON only: `text/plain` is a CORS-"simple" request and would let any page
    // drive the endpoint from a visitor's browser without a preflight.
    const contentType = (request.headers.get('Content-Type') ?? '').toLowerCase()
    if (!contentType.includes('application/json')) {
        return json(
            { error: 'unsupported_media_type', message: 'Content-Type must be application/json' },
            415
        )
    }

    // Paid-provider protection: 10 turns/minute per client is generous for a
    // human and ruinous for a script.
    const limited = await enforceRateLimit(env, request, {
        scope: 'ai',
        limit: 10,
        windowSeconds: 60
    })
    if (limited) return limited

    // Read once and measure: `Content-Length` is absent for chunked bodies, so
    // the header alone is not a reliable cap.
    const raw = await request.text()
    if (raw.length > MAX_BODY_BYTES) {
        return json({ error: 'payload_too_large', maxBytes: MAX_BODY_BYTES }, 413)
    }

    let body: Record<string, unknown> = {}
    try {
        body = JSON.parse(raw) as Record<string, unknown>
    } catch {
        return json({ error: 'invalid_json' }, 400)
    }

    const chatContext = (body.context ?? undefined) as ChatContext | undefined

    if (route === 'insight') {
        const result = await generateReadingInsight(env, chatContext)
        return json(result)
    }

    // Default route: /api/ai/chat
    const message = typeof body.message === 'string' ? body.message.trim() : ''
    if (!message) return json({ error: 'message_required' }, 400)
    if (message.length > MAX_MESSAGE_CHARS) {
        return json({ error: 'message_too_long', maxChars: MAX_MESSAGE_CHARS }, 413)
    }

    const prefs = (body.prefs ?? undefined) as
        | { favoriteGenres?: string[]; readingGoal?: number }
        | undefined
    // Conversation memory: prior turns (role + content) and the ids of every
    // book already suggested this conversation, so picks rotate and never
    // repeat the same titles turn after turn.
    // Bounded conversation memory: input length is billed as prompt tokens.
    const history = (Array.isArray(body.history) ? body.history : [])
        .slice(-MAX_HISTORY_TURNS)
        .map((turn) => ({
            role: (turn as ChatTurn).role,
            content: String((turn as ChatTurn).content ?? '').slice(0, MAX_TURN_CHARS)
        })) as ChatTurn[]
    const shown = (
        Array.isArray(body.shown) ? body.shown.filter((s) => typeof s === 'string') : []
    ).slice(0, MAX_SHOWN) as string[]
    const result = await handleChat(env, message, prefs, chatContext, history, shown)
    return json(result)
}

export const onRequestGet: PagesFunction = async () =>
    json(
        {
            error: 'method_not_allowed',
            message: 'Use POST /api/ai/chat or POST /api/ai/insight'
        },
        405
    )

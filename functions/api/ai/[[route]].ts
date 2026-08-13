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
import { type PagesFunction } from '../_lib/types'

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

    let body: Record<string, unknown> = {}
    try {
        body = (await request.json()) as Record<string, unknown>
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

    const prefs = (body.prefs ?? undefined) as
        | { favoriteGenres?: string[]; readingGoal?: number }
        | undefined
    // Conversation memory: prior turns (role + content) and the ids of every
    // book already suggested this conversation, so picks rotate and never
    // repeat the same titles turn after turn.
    const history = (Array.isArray(body.history) ? body.history : []) as ChatTurn[]
    const shown = (
        Array.isArray(body.shown) ? body.shown.filter((s) => typeof s === 'string') : []
    ) as string[]
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

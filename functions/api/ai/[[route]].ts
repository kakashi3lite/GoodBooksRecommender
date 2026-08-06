/**
 * 🤖 /api/ai/* — conversational AI endpoint (edge)
 *
 *   POST /api/ai/chat     body: { message: string, prefs?, context? }
 *   POST /api/ai/insight  body: { context: { stats, persona, ... } }
 *
 * `context` carries the reader's REAL profile (genres, goal, pace, streak,
 * current book) from the client's localStorage log — used to personalize
 * the LLM reply. Falls back to the local hybrid engine when the LLM is
 * unavailable — always real picks and honest numbers, never fabricated.
 */
import { generateReadingInsight, handleChat, type ChatContext } from '../_lib/ai'
import { type PagesFunction } from '../_lib/types'

const json = (body: unknown, status = 200): Response =>
    new Response(JSON.stringify(body), {
        status,
        headers: { 'Content-Type': 'application/json; charset=utf-8' }
    })

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
    const result = await handleChat(env, message, prefs, chatContext)
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

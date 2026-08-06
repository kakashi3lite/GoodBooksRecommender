/**
 * 🤖 /api/ai/* — conversational AI endpoint (edge)
 *
 *   POST /api/ai/chat   body: { message: string, prefs?: { favoriteGenres,
 *                        readingGoal } }
 *
 * Response: { reply, bookSuggestions?: [{id,title,authors,cover_url?,rating?}],
 *             model }
 *
 * Uses the LLM when configured (AI_PROVIDER/AI_API_KEY/AI_MODEL) and falls
 * back to the local hybrid engine otherwise — always returns real picks.
 */
import { handleChat } from '../_lib/ai'
import { type PagesFunction } from '../_lib/types'

export const onRequestPost: PagesFunction = async (context) => {
    const { request, env } = context
    let body: { message?: string; prefs?: { favoriteGenres?: string[]; readingGoal?: number } } = {}
    try {
        body = (await request.json()) as typeof body
    } catch {
        return new Response(JSON.stringify({ error: 'invalid_json' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' }
        })
    }

    const message = (body.message ?? '').trim()
    if (!message) {
        return new Response(JSON.stringify({ error: 'message_required' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' }
        })
    }

    const result = await handleChat(env, message, body.prefs)
    return new Response(JSON.stringify(result), {
        status: 200,
        headers: { 'Content-Type': 'application/json; charset=utf-8' }
    })
}

export const onRequestGet: PagesFunction = async () =>
    new Response(
        JSON.stringify({
            error: 'method_not_allowed',
            message: 'Use POST /api/ai/chat'
        }),
        { status: 405, headers: { 'Content-Type': 'application/json' } }
    )

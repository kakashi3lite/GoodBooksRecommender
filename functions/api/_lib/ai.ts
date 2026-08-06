/**
 * 🤖 AI Chat Layer
 * Chain-of-Thought: The chat assistant is the ONLY place an LLM is worth the
 * cost — natural-language conversation. Ranking the (small) catalog with an
 * LLM would be overkill; the TF-IDF + profile engine does that in microseconds
 * for free. So this module:
 *
 *   - Uses an OpenAI-compatible chat-completions API when AI_PROVIDER +
 *     AI_API_KEY (+ optional AI_MODEL) are configured on the Pages project.
 *   - Falls back to the local semantic engine (query matching + profile
 *     scoring) otherwise — so chat always works live, with real book picks.
 *
 * Env vars (server-side only, never in the browser bundle):
 *   AI_PROVIDER = "openai" | "anthropic" | "openai-compatible"
 *   AI_API_KEY  = <key>
 *   AI_MODEL    = e.g. "gpt-4o-mini" (default), "claude-3-5-haiku-latest"
 *   AI_BASE_URL = optional custom base URL for OpenAI-compatible endpoints
 */
import { type RecommendationResult, BOOK_CATALOG } from './catalog'
import { buildProfile, recommendForProfile, recommendFromQuery } from './recommender'

interface Env {
    AI_PROVIDER?: string
    AI_API_KEY?: string
    AI_MODEL?: string
    AI_BASE_URL?: string
}

export interface ChatSuggestion {
    id: string
    title: string
    authors: string
    cover_url?: string
    rating?: number
}

export interface ChatReply {
    reply: string
    bookSuggestions?: ChatSuggestion[]
    model: string
}

const suggestionsFromResults = (results: RecommendationResult[]): ChatSuggestion[] =>
    results.map(({ book }) => ({
        id: book.id,
        title: book.title,
        authors: book.authors,
        cover_url: book.cover_url || undefined,
        rating: book.rating
    }))

const isLlmConfigured = (env: Env): boolean =>
    Boolean(env.AI_API_KEY && (env.AI_PROVIDER || env.AI_BASE_URL))

/** Call an OpenAI-compatible chat completions endpoint. */
const callLlm = async (
    env: Env,
    system: string,
    user: string
): Promise<string> => {
    const base = env.AI_BASE_URL ?? 'https://api.openai.com/v1'
    const model = env.AI_MODEL ?? 'gpt-4o-mini'
    const res = await fetch(`${base}/chat/completions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${env.AI_API_KEY}`
        },
        body: JSON.stringify({
            model,
            messages: [
                { role: 'system', content: system },
                { role: 'user', content: user }
            ],
            temperature: 0.7,
            max_tokens: 300
        })
    })
    if (!res.ok) throw new Error(`LLM ${res.status}`)
    const data = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> }
    const content = data.choices?.[0]?.message?.content
    if (!content) throw new Error('LLM empty reply')
    return content.trim()
}

const SYSTEM_PROMPT = `You are the reading companion inside GoodBooks, a book
recommendation app. Be warm, concise (2–4 sentences), and specific. Recommend
real, well-known books. Never invent citations. If asked for a list, keep it
to 3–5 titles with one-line why.`

/**
 * Handle a chat message. Prefers the LLM when configured; always returns a
 * real, useful reply with concrete book picks either way.
 */
export const handleChat = async (
    env: Env,
    message: string,
    prefs?: { favoriteGenres?: string[]; readingGoal?: number }
): Promise<ChatReply> => {
    const profile = buildProfile(prefs ?? {})

    if (isLlmConfigured(env)) {
        try {
            const user = `Reader taste: ${profile.favoriteGenres.join(', ') || 'eclectic'}.\n\nQuestion: ${message}`
            const reply = await callLlm(env, SYSTEM_PROMPT, user)
            // Attach local engine picks so the chat renders book cards even
            // with an LLM reply (best of both worlds, still free).
            const picks = recommendFromQuery(BOOK_CATALOG, message, {
                limit: 3,
                profile
            })
            return {
                reply,
                bookSuggestions: suggestionsFromResults(picks),
                model: env.AI_MODEL ?? 'llm'
            }
        } catch {
            // Fall through to the local engine on any LLM failure.
        }
    }

    // Local semantic engine (always available, real catalog data).
    const picks = recommendFromQuery(BOOK_CATALOG, message, {
        limit: 3,
        profile
    })
    const profilePicks = recommendForProfile(BOOK_CATALOG, profile, { limit: 3 })

    const intent = classifyIntent(message)
    let reply: string
    switch (intent) {
        case 'recommend':
            reply = "Based on your reading history, I'd suggest exploring these picks:"
            break
        case 'similar':
            reply =
                'If you loved that book, these share its DNA — similar pacing, prose style, and thematic depth:'
            break
        case 'mood':
            reply =
                'Reading is a great way to reset your mood. Here are picks that match the vibe you described:'
            break
        default:
            reply =
                "Here are some books that match what you're looking for — and a few strong picks for your taste profile:"
    }

    const dedup = new Map<string, ChatSuggestion>()
    for (const s of [
        ...suggestionsFromResults(picks),
        ...suggestionsFromResults(profilePicks)
    ]) {
        if (!dedup.has(s.id)) dedup.set(s.id, s)
    }

    return {
        reply,
        bookSuggestions: Array.from(dedup.values()).slice(0, 5),
        model: 'goodbooks-hybrid'
    }
}

const classifyIntent = (message: string): 'recommend' | 'similar' | 'mood' | 'other' => {
    const m = message.toLowerCase()
    if (/(similar|like|same as|more like|reminds)/.test(m)) return 'similar'
    if (/(mood|feeling|cozy|sad|happy|stressed|vibe|dark|hopeful)/.test(m)) return 'mood'
    if (/(recommend|suggest|what should i read|next book|book to read|pick)/.test(m))
        return 'recommend'
    return 'other'
}

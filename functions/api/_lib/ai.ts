/**
 * 🤖 AI Chat Layer
 * Chain-of-Thought: The chat assistant is the ONLY place an LLM is worth the
 * cost — natural-language conversation. Ranking the (small) catalog with an
 * LLM would be overkill; the TF-IDF + profile engine does that in microseconds
 * for free. So this module:
 *
 *   - Uses an OpenAI-compatible chat-completions API when a provider key is
 *     configured: MINIMAX_API_KEY (MiniMax — live provider) or OPENAI_API_KEY
 *     (+ optional AI_MODEL).
 *   - Falls back to the local semantic engine (query matching + profile
 *     scoring) otherwise — so chat always works live, with real book picks.
 *
 * Any OpenAI-compatible provider works. MiniMax is auto-selected when
 * MINIMAX_API_KEY is present (base URL defaults to https://api.minimax.io/v1,
 * model to MiniMax-M2 — overridable via AI_BASE_URL / AI_MODEL).
 *
 * Env vars (server-side only, never in the browser bundle):
 *   MINIMAX_API_KEY = MiniMax subscription key (takes priority)
 *   OPENAI_API_KEY  = OpenAI key (sk-...) — legacy AI_API_KEY also accepted
 *   AI_PROVIDER     = optional "openai" (default) | any OpenAI-compatible
 *   AI_MODEL        = e.g. "gpt-4o-mini" (default), "MiniMax-M2"
 *   AI_BASE_URL     = optional custom base URL for OpenAI-compatible endpoints
 */
import { type RecommendationResult, BOOK_CATALOG } from './catalog'
import { buildProfile, recommendForProfile, recommendFromQuery } from './recommender'

interface Env {
    MINIMAX_API_KEY?: string
    OPENAI_API_KEY?: string
    /** @deprecated legacy alias — prefer OPENAI_API_KEY */
    AI_API_KEY?: string
    AI_PROVIDER?: string
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

export interface ReaderStats {
    streak: number
    booksFinished: number
    pagesThisMonth: number
    avgPagesPerSession: number
    distinctDays: number
}

/** Real reading context sent by the client — every number comes from the
 * reader's own localStorage log (never fabricated server-side). */
export interface ChatContext {
    favoriteGenres?: string[]
    readingGoal?: number
    persona?: string
    currentBook?: {
        title: string
        authors: string
        progressPct: number
        pageCount?: number
    }
    stats?: ReaderStats
    recentlyFinished?: Array<{ title: string; authors: string; genres?: string[] }>
}

export interface InsightReply {
    insight: string
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

interface ProviderConfig {
    key: string
    baseUrl: string
    defaultModel: string
}

/** Resolve which LLM provider is configured, if any. MiniMax wins when its
 * key is present; otherwise OpenAI (or a custom OpenAI-compatible endpoint). */
const resolveProvider = (env: Env): ProviderConfig | null => {
    if (env.MINIMAX_API_KEY) {
        return {
            key: env.MINIMAX_API_KEY,
            baseUrl: env.AI_BASE_URL ?? 'https://api.minimax.io/v1',
            defaultModel: 'MiniMax-M2'
        }
    }
    const key = env.OPENAI_API_KEY ?? env.AI_API_KEY
    if (!key) return null
    // OpenAI keys start with "sk-" → a bare key is treated as OpenAI.
    if (!(env.AI_PROVIDER || env.AI_BASE_URL || key.startsWith('sk-'))) return null
    return {
        key,
        baseUrl: env.AI_BASE_URL ?? 'https://api.openai.com/v1',
        defaultModel: 'gpt-4o-mini'
    }
}

const sleep = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms))

/** Strip a model's reasoning block (e.g. MiniMax-M2 `<think>…</think>`) so
 * users only see the actual answer. */
const stripThinkBlocks = (text: string): string =>
    text.replace(/<think>[\s\S]*?<\/think>/g, '').trim()

/** Call an OpenAI-compatible chat completions endpoint. Bounded retry with
 * backoff so a transient 429/5xx doesn't drop the LLM reply. */
const callLlm = async (
    env: Env,
    provider: ProviderConfig,
    system: string,
    user: string
): Promise<string> => {
    const base = provider.baseUrl
    const model = env.AI_MODEL ?? provider.defaultModel
    const key = provider.key
    let last: Error | null = null
    const retryDelays = [1000, 2500, 4000]
    for (let attempt = 0; attempt < 4; attempt++) {
        if (attempt > 0) await sleep(retryDelays[attempt - 1])
        const res = await fetch(`${base}/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${key}`
            },
            body: JSON.stringify({
                model,
                messages: [
                    { role: 'system', content: system },
                    { role: 'user', content: user }
                ],
                temperature: 0.7,
                max_tokens: 400
            })
        })
        if (!res.ok) {
            let detail = ''
            try {
                const err = (await res.json()) as { error?: { message?: string } }
                detail = err.error?.message ?? ''
            } catch {
                /* non-JSON error body — ignore */
            }
            last = new Error(`LLM ${res.status}${detail ? `: ${detail}` : ''}`)
            // Retry rate limits / server errors; other 4xx are fatal.
            const retryable = res.status === 429 || (res.status >= 500 && res.status <= 599)
            if (retryable && attempt < 3) {
                // Honor Retry-After when the provider sends it (capped at 5s).
                if (res.status === 429) {
                    const ra = Number(res.headers.get('retry-after'))
                    if (Number.isFinite(ra) && ra > 0) {
                        await sleep(Math.min(ra * 1000, 5000))
                    }
                }
                continue
            }
            break
        }
        const data = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> }
        const content = data.choices?.[0]?.message?.content
        if (!content) {
            last = new Error('LLM empty reply')
            break
        }
        const cleaned = stripThinkBlocks(content)
        if (!cleaned) {
            last = new Error('LLM empty reply')
            break
        }
        return cleaned
    }
    throw last ?? new Error('LLM failed')
}

/** Build a plain-text reader profile from REAL client data — only the
 * sections that exist are emitted; nothing is ever invented. */
const buildReaderContextText = (context?: ChatContext): string => {
    if (!context) return ''
    const lines: string[] = []
    const genres = context.favoriteGenres?.filter(Boolean)
    if (genres?.length) lines.push(`Favorite genres: ${genres.join(', ')}`)
    if (typeof context.readingGoal === 'number' && context.readingGoal > 0)
        lines.push(`Reading goal: ${context.readingGoal} books this year`)
    if (context.persona) lines.push(`Reader persona: ${context.persona}`)
    if (context.currentBook?.title) {
        const pct = Math.max(0, Math.min(100, Math.round(context.currentBook.progressPct)))
        lines.push(
            `Currently reading: "${context.currentBook.title}" by ${context.currentBook.authors || 'unknown'} (${pct}% done${context.currentBook.pageCount ? `, ${context.currentBook.pageCount} pages` : ''})`
        )
    }
    const s = context.stats
    if (s) {
        const bits: string[] = []
        if (s.streak > 0) bits.push(`${s.streak}-day streak`)
        if (s.booksFinished > 0) bits.push(`${s.booksFinished} books finished`)
        if (s.pagesThisMonth > 0) bits.push(`${s.pagesThisMonth} pages this month`)
        if (s.avgPagesPerSession > 0) bits.push(`~${s.avgPagesPerSession} pages per session`)
        if (bits.length) lines.push(`Reading stats: ${bits.join(' · ')}`)
    }
    if (context.recentlyFinished?.length) {
        lines.push(
            `Recently finished: ${context.recentlyFinished.map((b) => `"${b.title}"`).join(', ')}`
        )
    }
    return lines.join('\n')
}

/** Companion persona. The reader profile travels in the USER message (not the
 * system prompt) — MiniMax rejects large structured system blocks, while the
 * user-message profile pattern is proven to work (see generateReadingInsight). */
const COMPANION_SYSTEM_PROMPT = `You are the reading companion inside GoodBooks, a book recommendation app. Be warm, concise (2–4 sentences), and specific. Recommend real, well-known books. Never invent citations. If asked for a list, keep it to 3–5 titles with one-line why. When the user message contains a READER PROFILE: ground every answer in it — reference the current book, pace, streak, goal and recently-finished titles; avoid re-recommending books they just finished; when a pace is known, estimate in sessions ("at your pace, ~2 sessions") instead of vague time.`

const INSIGHT_SYSTEM_PROMPT = `You are the reflective reading companion inside GoodBooks. Write ONE warm, specific paragraph (2–4 sentences) celebrating or coaching the reader using ONLY the real numbers in the READER PROFILE. Never invent statistics, dates, or books. Mention the streak, pace, finished books, goal progress and current book if present; end with one concrete, encouraging suggestion.`

/** Honest template insight built from the SAME real numbers (never
 * fabricated) — used when the LLM is unavailable. */
const buildInsightFallback = (context?: ChatContext): string => {
    const s = context?.stats
    const goal = context?.readingGoal
    const goalProgress =
        goal && s && s.booksFinished >= 0
            ? s.booksFinished >= goal
                ? ' — you have already hit your yearly goal 🎉'
                : ` — ${goal - s.booksFinished} more to reach your goal of ${goal}`
            : ''
    const current = context?.currentBook
    const currentBit = current?.title
        ? ` Keep going with "${current.title}" (${Math.round(current.progressPct)}% done) to keep the momentum.`
        : ''
    if (s && (s.streak > 0 || s.booksFinished > 0 || s.pagesThisMonth > 0)) {
        const bits: string[] = []
        if (s.streak > 0) bits.push(`a ${s.streak}-day streak`)
        if (s.booksFinished > 0) bits.push(`${s.booksFinished} books finished`)
        if (s.pagesThisMonth > 0) bits.push(`${s.pagesThisMonth} pages this month`)
        return `You're building real momentum — ${bits.join(', ')}${goalProgress}.${currentBit}`
    }
    return 'Log a few reading sessions and this space will light up with a reflection about your real pace, streak, and goals.'
}

/**
 * Generate a short, warm reading reflection from the reader's REAL stats.
 * Prefers the LLM; falls back to an honest template of the same numbers.
 */
export const generateReadingInsight = async (
    env: Env,
    context?: ChatContext
): Promise<InsightReply> => {
    const readerContext = buildReaderContextText(context)
    const provider = resolveProvider(env)
    if (provider && readerContext) {
        try {
            const insight = await callLlm(
                env,
                provider,
                INSIGHT_SYSTEM_PROMPT,
                `READER PROFILE:\n${readerContext}`
            )
            return { insight, model: env.AI_MODEL ?? provider.defaultModel }
        } catch {
            // Fall through to the honest template below.
        }
    }
    return { insight: buildInsightFallback(context), model: 'goodbooks-hybrid' }
}

/**
 * Handle a chat message. Prefers the LLM when configured; always returns a
 * real, useful reply with concrete book picks either way. `context` carries
 * the reader's real profile so replies are genuinely personalized.
 */
export const handleChat = async (
    env: Env,
    message: string,
    prefs?: { favoriteGenres?: string[]; readingGoal?: number },
    context?: ChatContext
): Promise<ChatReply> => {
    const profile = buildProfile(prefs ?? {})
    const readerContext = buildReaderContextText(context)

    const provider = resolveProvider(env)
    if (provider) {
        try {
            // Reader profile rides in the user message (MiniMax-safe), so the
            // LLM personalizes without the system block rejection seen earlier.
            const user = readerContext
                ? `READER PROFILE (real data — personalize your answer, never contradict it):\n${readerContext}\n\nQuestion: ${message}`
                : `Question: ${message}`
            const reply = await callLlm(env, provider, COMPANION_SYSTEM_PROMPT, user)
            // Attach local engine picks so the chat renders book cards even
            // with an LLM reply (best of both worlds, still free).
            const picks = recommendFromQuery(BOOK_CATALOG, message, {
                limit: 3,
                profile
            })
            return {
                reply,
                bookSuggestions: suggestionsFromResults(picks),
                model: env.AI_MODEL ?? provider.defaultModel
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
    const contextHints: string[] = []
    if (context?.stats?.streak && context.stats.streak > 1)
        contextHints.push(`a ${context.stats.streak}-day streak`)
    if (context?.currentBook?.title)
        contextHints.push(`you're ${Math.round(context.currentBook.progressPct)}% through "${context.currentBook.title}"`)
    const hint = contextHints.length
        ? ` I can see ${contextHints.join(' and ')} — nice work.`
        : ''

    let reply: string
    switch (intent) {
        case 'recommend':
            reply = `Based on your reading history, I'd suggest exploring these picks:${hint}`
            break
        case 'similar':
            reply = `If you loved that book, these share its DNA — similar pacing, prose style, and thematic depth:${hint}`
            break
        case 'mood':
            reply = `Reading is a great way to reset your mood. Here are picks that match the vibe you described:${hint}`
            break
        default:
            reply = `Here are some books that match what you're looking for — and a few strong picks for your taste profile:${hint}`
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

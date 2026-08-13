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
import { BOOK_CATALOG, type Book, type RecommendationResult } from './catalog'
import { buildProfile, recommendForProfile, recommendFromQuery } from './recommender'
import { searchWebBooks } from './webCatalog'

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
    /** Why this book was suggested (personalization explanation). */
    reason?: string
}

/** One prior conversational turn sent by the client so the companion can
 * follow the thread and avoid re-recommending what it already suggested. */
export interface ChatTurn {
    role: 'user' | 'assistant'
    content: string
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

const suggestionsFromResults = (results: RecommendationResult[]): ChatSuggestion[] =>
    results.map(({ book, reason }) => ({
        id: book.id,
        title: book.title,
        authors: book.authors,
        cover_url: book.cover_url || undefined,
        rating: book.rating,
        reason
    }))

// ─── Conversation-aware personalization ─────────────────────────────────────
// Chain-of-Thought: the "same books every time" bug happened because chat was
// stateless — every request ran the same deterministic query against the same
// tiny catalog. The fix is three-fold:
//   1. EXCLUDE every book already suggested in this conversation (`shown`),
//      plus the reader's current book and recently-finished titles → the
//      engine is forced to rotate instead of re-serving the top of the list.
//   2. Derive genre affinity from the READER CONTEXT (recently finished +
//      current book) when no explicit prefs exist → generic questions get
//      personalized, not just highest-rated, picks.
//   3. When the LLM is up, ask it for a structured list of real books and use
//      those as the cards — so the suggestions match the reply, not a
//      hard-coded ranking.

/** Normalize a title for fuzzy matching ("The Name of the Wind" vs "name of
 * the wind"). Strips articles, punctuation and case. */
export const normalizeTitle = (title: string): string =>
    title
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, ' ')
        .replace(/\b(the|a|an)\b/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()

/** True when `titles` (LLM output) refers to the same book as `candidate`. */
export const titleMatches = (titles: string[], candidate: Book): boolean => {
    const norm = normalizeTitle(candidate.title)
    return titles.some((t) => {
        const n = normalizeTitle(t)
        return n.length > 0 && (n === norm || n.includes(norm) || norm.includes(n))
    })
}

/** Union of ids to exclude this turn: already-shown suggestions + the current
 * book + anything the reader just finished (they asked for something NEW). */
export const excludeSetFor = (shown: string[], context?: ChatContext): Set<string> => {
    const excluded = new Set<string>(shown.filter(Boolean))
    if (context?.currentBook?.title) {
        const hit = BOOK_CATALOG.find((b) => titleMatches([context.currentBook!.title], b))
        if (hit) excluded.add(hit.id)
    }
    for (const finished of context?.recentlyFinished ?? []) {
        if (!finished.title) continue
        const hit = BOOK_CATALOG.find((b) => titleMatches([finished.title], b))
        if (hit) excluded.add(hit.id)
    }
    return excluded
}

/** Build a taste profile from explicit prefs, falling back to genre affinity
 * inferred from the reader's real shelf (recently finished + current book)
 * when the user never picked genres — so even a generic "recommend me a book"
 * is grounded in what they actually read. */
export const profileFromContext = (
    prefs: { favoriteGenres?: string[]; readingGoal?: number },
    context?: ChatContext
): ReturnType<typeof buildProfile> => {
    let favoriteGenres = prefs.favoriteGenres?.filter(Boolean)
    if (!favoriteGenres?.length && context) {
        const genreCount = new Map<string, number>()
        for (const book of [
            ...(context.recentlyFinished ?? []),
            ...(context.currentBook ? [context.currentBook] : [])
        ]) {
            for (const g of book.genres ?? []) {
                genreCount.set(g, (genreCount.get(g) ?? 0) + 1)
            }
        }
        favoriteGenres = Array.from(genreCount.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3)
            .map(([g]) => g)
    }
    return buildProfile({ favoriteGenres, readingGoal: prefs.readingGoal })
}

/** Leniently extract a `{ "books": [{ title, author, reason }] }` JSON block
 * from an LLM reply — handles fenced code blocks, trailing prose and typos. */
export const parseLlmBookPicks = (
    reply: string
): Array<{ title: string; author?: string; reason?: string }> => {
    const fences = reply.match(/```(?:json)?\s*([\s\S]*?)```/g)
    const candidates = fences ?? [reply]
    for (const block of candidates) {
        const cleaned = block.replace(/```(?:json)?/g, '').replace(/```/g, '')
        const open = cleaned.indexOf('{')
        const close = cleaned.lastIndexOf('}')
        if (open === -1 || close <= open) continue
        try {
            const parsed = JSON.parse(cleaned.slice(open, close + 1)) as {
                books?: Array<{ title?: string; author?: string; reason?: string }>
            }
            const books = (parsed.books ?? [])
                .map((b) => ({
                    title: (b.title ?? '').trim(),
                    author: (b.author ?? '').trim(),
                    reason: (b.reason ?? '').trim()
                }))
                .filter((b) => b.title.length > 1)
            if (books.length > 0) return books.slice(0, 6)
        } catch {
            // try the next block
        }
    }
    return []
}

/** Match the LLM's book list against the curated catalog; return any catalog
 * hits (with the LLM's reason) plus the titles that missed, for web top-up. */
export const matchLlmBooksToCatalog = (
    picks: Array<{ title: string; author?: string; reason?: string }>
): {
    catalog: ChatSuggestion[]
    missing: Array<{ title: string; author?: string; reason?: string }>
} => {
    const catalog: ChatSuggestion[] = []
    const missing: Array<{ title: string; author?: string; reason?: string }> = []
    const used = new Set<string>()
    for (const pick of picks) {
        const hit = BOOK_CATALOG.find(
            (b) =>
                titleMatches([pick.title], b) &&
                (!pick.author ||
                    b.authors.toLowerCase().includes(pick.author.toLowerCase().slice(0, 12)))
        )
        if (hit && !used.has(hit.id)) {
            used.add(hit.id)
            catalog.push({
                id: hit.id,
                title: hit.title,
                authors: hit.authors,
                cover_url: hit.cover_url || undefined,
                rating: hit.rating,
                reason: pick.reason || `Matches your request for "${pick.title}"`
            })
        } else if (!hit) {
            missing.push(pick)
        }
    }
    return { catalog, missing }
}

/** True when `book` is (nearly) the same title as an existing suggestion.
 * Exact normalized-title match wins; a longer title that CONTAINS an existing
 * one is treated as the same work ("1984 (adaptation)" vs "1984", "Workbook on
 * House in the Cerulean Sea" vs "The House in the Cerulean Sea"); for the same
 * author we also drop anthology/omnibus editions that embed the title so web
 * top-up never floods the chat with the same book 4× under different edition
 * titles. */
export const isNearDuplicate = (existing: ChatSuggestion[], book: Book): boolean => {
    const norm = normalizeTitle(book.title)
    return existing.some((s) => {
        const other = normalizeTitle(s.title)
        if (norm === other) return true
        // Title-containment: e.g. "1984" inside "1984 (adaptation)", or
        // "pride and prejudice" inside "pride and prejudice and zombies".
        if (norm.length >= 4 && (norm.includes(other) || other.includes(norm))) {
            return true
        }
        if (!book.authors || !s.authors) return false
        if (normalizeTitle(book.authors) !== normalizeTitle(s.authors)) return false
        const a = new Set(norm.split(' ').filter((t) => t.length > 3))
        const b = new Set(other.split(' ').filter((t) => t.length > 3))
        if (a.size === 0 || b.size === 0) return false
        let shared = 0
        for (const t of a) if (b.has(t)) shared++
        return shared / Math.min(a.size, b.size) >= 0.5
    })
}

/** Convert a web-searched Book into a chat suggestion with a reason. */
const suggestionFromBook = (
    book: Book,
    reason: string | undefined,
    existing: ChatSuggestion[]
): ChatSuggestion | null => {
    if (isNearDuplicate(existing, book)) return null
    return {
        id: book.id,
        title: book.title,
        authors: book.authors,
        cover_url: book.cover_url || undefined,
        rating: book.rating,
        reason: reason || 'A real, well-loved book that matches your request'
    }
}

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

/** Remove control characters (other than \n \t \r) from an LLM reply. Some
 * providers occasionally emit raw control bytes that would otherwise break
 * the strict JSON we ship to the client ("Invalid control character"). */
export const sanitizeControlChars = (text: string): string =>
    text.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, ' ')

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
                max_tokens: 700
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
        return sanitizeControlChars(cleaned)
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
 * user-message profile pattern is proven to work (see generateReadingInsight).
 *
 * The assistant is asked to END its reply with a machine-readable JSON block
 * of real book picks so the chat can render suggestion cards that match the
 * answer instead of a static ranking (the root cause of "same books every
 * time"). Parsing is lenient and falls back to the local engine. */
const COMPANION_SYSTEM_PROMPT = `You are the reading companion inside GoodBooks, a book recommendation app. Be warm, concise (2–4 sentences), and specific. Recommend real, well-known books. Never invent citations or books that do not exist. Never recommend books the user says they already read or that are listed as ALREADY SUGGESTED.

END YOUR REPLY with a JSON block on its own lines, listing 3–4 recommended books in this exact shape (no other JSON, no markdown table):
{"books":[{"title":"The Name of the Wind","author":"Patrick Rothfuss","reason":"Epic fantasy with lyrical prose"},{"title":"...","author":"...","reason":"..."}]}

Ground every pick in the READER PROFILE and the CONVERSATION SO FAR: reference the current book, pace, streak, goal and recently-finished titles; prefer the reader's favorite genres; when a pace is known, estimate in sessions ("at your pace, ~2 sessions") instead of vague time. If the user asks for a mood, match the mood. If they ask "similar to X", pick books that genuinely share DNA with X. If they just say "recommend me a book", pick from their favorite genres or a high-quality classic — NOT the same titles as ALREADY SUGGESTED.`

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

/** Summarize the conversation so far for the LLM (last 6 turns, compact). */
const buildHistoryText = (history: ChatTurn[]): string => {
    const turns = history.slice(-6)
    if (turns.length === 0) return ''
    return turns
        .map((t) => `${t.role === 'user' ? 'Reader' : 'Companion'}: ${t.content}`)
        .join('\n')
}

/** Deduplicate suggestions (by id, then normalized title for web books). */
const dedupSuggestions = (suggestions: ChatSuggestion[]): ChatSuggestion[] => {
    const seenIds = new Set<string>()
    const seenTitles = new Set<string>()
    const out: ChatSuggestion[] = []
    for (const s of suggestions) {
        const titleKey = normalizeTitle(s.title)
        if ((s.id && seenIds.has(s.id)) || seenTitles.has(titleKey)) continue
        if (s.id) seenIds.add(s.id)
        seenTitles.add(titleKey)
        out.push(s)
    }
    return out
}

/** Top up with web-searched real books for LLM titles the catalog lacks.
 * Bounded (max 2 searches, limit 4 each) so a slow provider never stalls the
 * chat. */
const webTopUp = async (
    missing: Array<{ title: string; author?: string; reason?: string }>,
    existing: ChatSuggestion[],
    limit: number
): Promise<ChatSuggestion[]> => {
    const out: ChatSuggestion[] = []
    for (const pick of missing.slice(0, 2)) {
        if (out.length + existing.length >= limit) break
        try {
            const books = await searchWebBooks(pick.title, 4)
            for (const book of books) {
                const suggestion = suggestionFromBook(book, pick.reason, [...existing, ...out])
                if (suggestion) out.push(suggestion)
                if (out.length + existing.length >= limit) break
            }
        } catch {
            // continue with the next missing title
        }
    }
    return out
}

/** Run the local semantic engine with conversation-aware exclusions. */
const localPicks = (
    message: string,
    profile: ReturnType<typeof buildProfile>,
    excluded: Set<string>
): ChatSuggestion[] => {
    const excludes = Array.from(excluded)
    const queryPicks = recommendFromQuery(BOOK_CATALOG, message, {
        limit: 3,
        profile,
        excludeIds: excludes
    })
    const profilePicks = recommendForProfile(BOOK_CATALOG, profile, {
        limit: 3,
        excludeIds: [...excludes, ...queryPicks.map((r) => r.book.id)]
    })
    return dedupSuggestions(
        [...suggestionsFromResults(queryPicks), ...suggestionsFromResults(profilePicks)]
    ).slice(0, 5)
}

/**
 * Handle a chat message. Prefers the LLM when configured; always returns a
 * real, useful reply with concrete book picks either way.
 *
 * Personalization (this is the anti-"same books" core):
 *   - `history` — prior turns, so the companion follows the thread.
 *   - `shown`   — every book id already suggested this conversation, so the
 *     picks ROTATE and never repeat the same titles turn after turn.
 *   - `context` — the reader's real profile (genres, goal, pace, streak,
 *     current book, recently finished) so picks are grounded in their taste.
 *   - When the LLM is up it returns structured JSON book picks that match the
 *     reply; the local engine fills any gaps (and takes over entirely if the
 *     LLM is unavailable or misbehaves).
 */
export const handleChat = async (
    env: Env,
    message: string,
    prefs?: { favoriteGenres?: string[]; readingGoal?: number },
    context?: ChatContext,
    history?: ChatTurn[],
    shown?: string[]
): Promise<ChatReply> => {
    const profile = profileFromContext(prefs ?? {}, context)
    const excluded = excludeSetFor(shown ?? [], context)
    const readerContext = buildReaderContextText(context)

    const provider = resolveProvider(env)
    if (provider) {
        try {
            // Reader profile + thread + already-shown titles ride in the USER
            // message (MiniMax-safe), so the LLM personalizes and avoids
            // repeating suggestions.
            const parts: string[] = []
            if (readerContext)
                parts.push(
                    `READER PROFILE (real data — personalize your answer, never contradict it):\n${readerContext}`
                )
            const historyText = buildHistoryText(history ?? [])
            if (historyText) parts.push(`CONVERSATION SO FAR:\n${historyText}`)
            const shownTitles = BOOK_CATALOG.filter((b) => excluded.has(b.id))
                .map((b) => `"${b.title}"`)
                .join(', ')
            if (shownTitles)
                parts.push(
                    `ALREADY SUGGESTED (do NOT recommend these again): ${shownTitles}`
                )
            parts.push(`Question: ${message}`)
            const reply = await callLlm(env, provider, COMPANION_SYSTEM_PROMPT, parts.join('\n\n'))

            // Turn the LLM's structured picks into the suggestion cards so the
            // cards match the answer (the core personalization win). Cap the
            // LLM/web contribution at 3 — the LLM can occasionally pick
            // off-topic titles, so the semantic engine always contributes the
            // remaining 2 grounded picks.
            const llmPicks = parseLlmBookPicks(reply)
            let suggestions: ChatSuggestion[] = []
            if (llmPicks.length > 0) {
                const { catalog, missing } = matchLlmBooksToCatalog(llmPicks)
                suggestions = dedupSuggestions(
                    catalog.filter((s) => !excluded.has(s.id))
                )
                if (suggestions.length < 3 && missing.length > 0) {
                    const web = await webTopUp(missing, suggestions, 3)
                    suggestions = dedupSuggestions([...suggestions, ...web])
                }
                suggestions = suggestions.slice(0, 3)
            }
            // Whatever the LLM produced, top up with local picks (excluding
            // shown) so the chat ALWAYS renders real, relevant cards.
            const local = localPicks(message, profile, excluded)
            suggestions = dedupSuggestions([...suggestions, ...local]).slice(0, 5)

            return {
                reply,
                bookSuggestions: suggestions.length > 0 ? suggestions : undefined,
                model: env.AI_MODEL ?? provider.defaultModel
            }
        } catch {
            // Fall through to the local engine on any LLM failure.
        }
    }

    // Local semantic engine (always available, real catalog data, rotation).
    const suggestions = localPicks(message, profile, excluded)

    const intent = classifyIntent(message)
    const contextHints: string[] = []
    if (context?.stats?.streak && context.stats.streak > 1)
        contextHints.push(`a ${context.stats.streak}-day streak`)
    if (context?.currentBook?.title)
        contextHints.push(
            `you're ${Math.round(context.currentBook.progressPct)}% through "${context.currentBook.title}"`
        )
    const hint = contextHints.length
        ? ` I can see ${contextHints.join(' and ')} — nice work.`
        : ''
    const fresh = shown && shown.length > 0 ? ' Here are some fresh picks you haven\u2019t seen yet.' : ''

    let reply: string
    switch (intent) {
        case 'recommend':
            reply = `Based on your reading history, I'd suggest exploring these picks:${hint}${fresh}`
            break
        case 'similar':
            reply = `If you loved that book, these share its DNA — similar pacing, prose style, and thematic depth:${hint}${fresh}`
            break
        case 'mood':
            reply = `Reading is a great way to reset your mood. Here are picks that match the vibe you described:${hint}${fresh}`
            break
        default:
            reply = `Here are some books that match what you're looking for — and a few strong picks for your taste profile:${hint}${fresh}`
    }

    return {
        reply,
        bookSuggestions: suggestions.length > 0 ? suggestions : undefined,
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

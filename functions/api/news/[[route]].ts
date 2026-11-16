/**
 * 📰 /api/news/* — real book news from publisher RSS (server-side, edge)
 *
 * Chain-of-Thought: this never invents stories. If every feed is unreachable the
 * response is an empty array and the frontend shows its honest offline state.
 *
 * The feed list used to point at Google News RSS, which now replies with a
 * ~1 KB stub containing no `<item>` elements — a silent outage that made the
 * News dashboard look permanently empty. It now reads four publisher-owned
 * feeds in parallel, merges, de-duplicates and sorts newest-first, and reports
 * how many feeds answered in `X-News-Feeds` so this cannot fail silently again.
 */

import { type PagesFunction } from '../_lib/types'
import { FEEDS, mergeStories, parseRss, type RssItem } from '../_lib/rss'

const TIMEOUT_MS = 8000

const fetchFeed = async (feed: { url: string; name: string }): Promise<RssItem[]> => {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
    try {
        const response = await fetch(feed.url, {
            headers: { 'User-Agent': 'GoodBooks-News/1.0 (+https://books.dalecabra.com)' },
            signal: controller.signal
        })
        if (!response.ok) return []
        return parseRss(await response.text(), feed.name)
    } finally {
        clearTimeout(timer)
    }
}

const json = (
    data: unknown,
    status = 200,
    cacheSeconds = 900,
    extraHeaders: Record<string, string> = {}
): Response =>
    new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Cache-Control': `public, max-age=${cacheSeconds}`,
            ...extraHeaders
        }
    })

export const onRequestGet: PagesFunction = async (context) => {
    const { request } = context
    const url = new URL(request.url)
    const limit = Math.min(30, Math.max(1, parseInt(url.searchParams.get('limit') ?? '10', 10) || 10))

    const settled = await Promise.allSettled(FEEDS.map((feed) => fetchFeed(feed)))
    const answered = settled.filter((result) => result.status === 'fulfilled').length
    const items = settled.flatMap((result) => (result.status === 'fulfilled' ? result.value : []))

    const stories = mergeStories(items, limit)
    // An empty result is usually a transient upstream failure, so do not let it
    // stick at the edge for the full success window.
    return json(stories, 200, stories.length > 0 ? 900 : 60, {
        'X-News-Feeds': `${answered}/${FEEDS.length}`
    })
}

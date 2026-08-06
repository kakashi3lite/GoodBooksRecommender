/**
 * 📰 /api/news/* — real book news from RSS (server-side, edge)
 * Chain-of-Thought: the previous "news" was five fabricated stories with fake
 * credibility scores served as a fallback. This endpoint fetches REAL book /
 * literature headlines from Google News RSS, parses them, and returns a
 * structured feed. If the feed is unreachable it returns an empty array — the
 * frontend shows a clean "offline" state instead of invented news.
 */

import { type PagesFunction } from '../_lib/types'

interface RssItem {
    title: string
    link: string
    pubDate: string
    source: string
    description: string
}

const FEEDS = [
    'https://news.google.com/rss/search?q=books%20literature%20reading&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q=book%20release%20author%20bestseller&hl=en-US&gl=US&ceid=US:en'
]

const decodeXml = (s: string): string =>
    s
        .replace(/<!\[CDATA\[|\]\]>/g, '')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&apos;/g, "'")

const stripHtml = (s: string): string => s.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()

/** Minimal RSS <item> parser (Google News feed) — no external deps. */
const parseRss = (xml: string): RssItem[] => {
    const items: RssItem[] = []
    const itemRe = /<item>([\s\S]*?)<\/item>/g
    let m: RegExpExecArray | null
    while ((m = itemRe.exec(xml)) !== null) {
        const block = m[1]
        const title = decodeXml(block.match(/<title>([\s\S]*?)<\/title>/)?.[1] ?? '').trim()
        const link = decodeXml(block.match(/<link>([\s\S]*?)<\/link>/)?.[1] ?? '').trim()
        const pubDate = decodeXml(block.match(/<pubDate>([\s\S]*?)<\/pubDate>/)?.[1] ?? '').trim()
        const source = decodeXml(block.match(/<source[^>]*>([\s\S]*?)<\/source>/)?.[1] ?? '').trim()
        const description = decodeXml(block.match(/<description>([\s\S]*?)<\/description>/)?.[1] ?? '')
        if (title && link) {
            items.push({ title, link, pubDate, source: source || 'News', description })
        }
    }
    return items
}

const json = (data: unknown, status = 200, cacheSeconds = 900): Response =>
    new Response(JSON.stringify(data), {
        status,
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            // Cache at the edge so we don't hammer the RSS feed on every view.
            'Cache-Control': `public, max-age=${cacheSeconds}`
        }
    })

export const onRequestGet: PagesFunction = async (context) => {
    const { request } = context
    const url = new URL(request.url)
    const limit = Math.min(30, Math.max(1, parseInt(url.searchParams.get('limit') ?? '10', 10) || 10))

    // Try feeds in order until one returns items.
    let items: RssItem[] = []
    for (const feed of FEEDS) {
        try {
            const res = await fetch(feed, {
                headers: { 'User-Agent': 'GoodBooks-News/1.0' },
                cf: { cacheTtl: 900 } as unknown as RequestInit
            })
            if (!res.ok) continue
            const xml = await res.text()
            items = parseRss(xml)
            if (items.length > 0) break
        } catch {
            continue
        }
    }

    if (items.length === 0) {
        return json([])
    }

    // Dedupe by title, map to the frontend contract.
    const seen = new Set<string>()
    const stories = items
        .filter((item) => {
            const key = item.title.toLowerCase()
            if (seen.has(key)) return false
            seen.add(key)
            return true
        })
        .slice(0, limit)
        .map((item, i) => ({
            article_id: `news-${i}`,
            title: item.title.slice(0, 200),
            source: item.source,
            published_at: item.pubDate
                ? new Date(item.pubDate).toISOString()
                : new Date().toISOString(),
            summary: stripHtml(item.description).slice(0, 300),
            link: item.link,
            credibility_score: undefined,
            topics: ['books']
        }))

    return json(stories)
}

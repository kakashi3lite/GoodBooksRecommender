/**
 * 📰 RSS helpers for the news edge function.
 *
 * Chain-of-Thought: the original feed list pointed at Google News RSS, which now
 * answers with a ~1 KB stub containing **zero `<item>` elements** — so the
 * endpoint correctly returned `[]` and the News dashboard looked broken. The
 * parsing/merging logic lives here, pure and dependency-free, so it can be
 * unit-tested without a network or a Worker runtime.
 */

export interface RssItem {
    title: string
    link: string
    pubDate: string
    source: string
    description: string
}

export interface NewsFeed {
    url: string
    name: string
}

export interface NewsStory {
    article_id: string
    title: string
    source: string
    published_at: string
    summary: string
    link: string
    topics: string[]
}

/**
 * Real, publisher-owned book feeds. Ordered by reliability, all fetched in
 * parallel — one dead feed must never empty the page.
 */
export const FEEDS: NewsFeed[] = [
    { url: 'https://www.theguardian.com/books/rss', name: 'The Guardian' },
    { url: 'https://rss.nytimes.com/services/xml/rss/nyt/Books.xml', name: 'The New York Times' },
    { url: 'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml', name: 'BBC News' },
    { url: 'https://lithub.com/feed/', name: 'Literary Hub' }
]

export const decodeXml = (s: string): string =>
    s
        .replace(/<!\[CDATA\[|\]\]>/g, '')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/&apos;/g, "'")

export const stripHtml = (s: string): string => s.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()

/**
 * Minimal RSS 2.0 `<item>` parser.
 *
 * @param xml            raw feed body
 * @param fallbackSource feed name, used when an item carries no `<source>`
 */
export const parseRss = (xml: string, fallbackSource = 'News'): RssItem[] => {
    const items: RssItem[] = []
    const itemRe = /<item>([\s\S]*?)<\/item>/g
    let match: RegExpExecArray | null

    while ((match = itemRe.exec(xml)) !== null) {
        const block = match[1]
        const title = decodeXml(block.match(/<title>([\s\S]*?)<\/title>/)?.[1] ?? '').trim()
        const link = decodeXml(block.match(/<link>([\s\S]*?)<\/link>/)?.[1] ?? '').trim()
        if (!title || !link) continue

        items.push({
            title,
            link,
            pubDate: decodeXml(block.match(/<pubDate>([\s\S]*?)<\/pubDate>/)?.[1] ?? '').trim(),
            source: decodeXml(block.match(/<source[^>]*>([\s\S]*?)<\/source>/)?.[1] ?? '').trim() || fallbackSource,
            description: decodeXml(block.match(/<description>([\s\S]*?)<\/description>/)?.[1] ?? '')
        })
    }

    return items
}

const publishedTime = (item: RssItem): number => {
    const time = new Date(item.pubDate).getTime()
    return Number.isFinite(time) ? time : 0
}

/**
 * Merge feeds into one newest-first, de-duplicated list.
 *
 * Chain-of-Thought: publishers syndicate the same story, so the same headline
 * can arrive twice. Sorting by date (rather than trusting each feed's order)
 * means the reader always sees the freshest story first regardless of which
 * feed answered.
 */
export const mergeStories = (items: RssItem[], limit: number, now = new Date()): NewsStory[] => {
    const seen = new Set<string>()
    return [...items]
        .sort((a, b) => publishedTime(b) - publishedTime(a))
        .filter((item) => {
            const key = item.title.toLowerCase().replace(/\s+/g, ' ').trim()
            if (seen.has(key)) return false
            seen.add(key)
            return true
        })
        .slice(0, limit)
        .map((item, index) => ({
            article_id: `news-${index}`,
            title: item.title.slice(0, 200),
            source: item.source,
            published_at: publishedTime(item) ? new Date(publishedTime(item)).toISOString() : now.toISOString(),
            summary: stripHtml(item.description).slice(0, 300),
            link: item.link,
            topics: ['books']
        }))
}

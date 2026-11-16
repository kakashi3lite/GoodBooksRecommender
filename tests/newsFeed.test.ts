/**
 * 🧪 News feed — parsing, merging and the outage that hid itself
 *
 * The News dashboard was empty in production because the feed list pointed at
 * Google News RSS, which now returns a stub with zero `<item>` elements. The
 * endpoint was *honest* (it returned `[]`), but nothing surfaced that the source
 * had died. These tests pin the parsing/merge rules that replaced it.
 */

import { describe, expect, it } from 'vitest'
import { FEEDS, decodeXml, mergeStories, parseRss, stripHtml } from '../functions/api/_lib/rss'

const feed = (items: string) => `<rss><channel>${items}</channel></rss>`

const item = (title: string, pubDate: string, extra = '') => `
  <item>
    <title>${title}</title>
    <link>https://example.com/${encodeURIComponent(title)}</link>
    <pubDate>${pubDate}</pubDate>
    ${extra}
  </item>`

describe('news feed', () => {
    it('reads real publishers, not a search-engine redirect', () => {
        expect(FEEDS.length).toBeGreaterThan(1)
        expect(FEEDS.every((entry) => entry.url.startsWith('https://'))).toBe(true)
        expect(FEEDS.map((entry) => entry.url).join(' ')).not.toContain('news.google.com')
    })

    it('parses RSS items including CDATA and entities', () => {
        const xml = feed(
            item('<![CDATA[Publishers &amp; prizes]]>', 'Tue, 17 Nov 2026 10:00:00 GMT', '<description><![CDATA[<p>A <b>story</b></p>]]></description>')
        )
        const [parsed] = parseRss(xml, 'The Guardian')

        expect(parsed.title).toBe('Publishers & prizes')
        expect(parsed.source).toBe('The Guardian')
        expect(stripHtml(parsed.description)).toBe('A story')
    })

    it('drops items with no title or link instead of rendering blanks', () => {
        const xml = feed(`
            <item><title>No link here</title></item>
            <item><title>Has both</title><link>https://example.com/a</link></item>`)
        expect(parseRss(xml).map((entry) => entry.title)).toEqual(['Has both'])
    })

    it('returns an empty list for the dead feed shape (zero <item> elements)', () => {
        expect(parseRss('<html><body>Google News stub</body></html>')).toEqual([])
    })

    it('merges feeds newest-first and de-duplicates syndicated headlines', () => {
        const older = parseRss(feed(item('Older story', 'Mon, 16 Nov 2026 09:00:00 GMT')), 'Guardian')
        const newer = parseRss(feed(item('Newest story', 'Tue, 17 Nov 2026 12:00:00 GMT')), 'BBC News')
        const duplicate = parseRss(feed(item('older story', 'Mon, 16 Nov 2026 09:00:00 GMT')), 'NYT')

        const stories = mergeStories([...older, ...newer, ...duplicate], 10)

        expect(stories.map((story) => story.title)).toEqual(['Newest story', 'Older story'])
        expect(stories[0].source).toBe('BBC News')
        expect(stories[0].published_at).toBe('2026-11-17T12:00:00.000Z')
    })

    it('respects the limit and survives undated items', () => {
        const now = new Date('2026-11-17T00:00:00Z')
        const undated = parseRss(feed(item('Undated story', '')), 'Literary Hub')
        const stories = mergeStories([...undated, ...parseRss(feed(item('Dated', 'Tue, 17 Nov 2026 12:00:00 GMT')))], 1, now)

        expect(stories).toHaveLength(1)
        expect(stories[0].title).toBe('Dated')
        expect(mergeStories(undated, 5, now)[0].published_at).toBe('2026-11-17T00:00:00.000Z')
    })

    it('decodes the entity set publishers actually emit', () => {
        expect(decodeXml('a &amp; b &lt;c&gt; &quot;d&quot; &#39;e&#39;')).toBe('a & b <c> "d" \'e\'')
    })
})

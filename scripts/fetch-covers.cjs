/**
 * 📚 Fetch real book cover URLs.
 *
 * Source: Open Library (free, no API key, real cover scans from the Internet
 * Archive). Google Books API was considered but its anonymous daily quota is
 * frequently exhausted (HTTP 429) — Open Library is reliable for this size of
 * catalog and needs no credentials.
 *
 * Output: scripts/.covers.json  (gitignored) — map of book id -> cover URL.
 * The URLs are then baked into src/data/bookCatalog.ts + shared/book-catalog.json
 * and (when the DB schema exists) upserted into Supabase `books.cover_url`.
 *
 * Usage: node scripts/fetch-covers.cjs
 */
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const CATALOG = path.join(ROOT, 'shared/book-catalog.json')
const OUT = path.join(ROOT, 'scripts/.covers.json')

const books = JSON.parse(fs.readFileSync(CATALOG, 'utf8'))
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

/** Size suffix for covers.openlibrary.org — M = medium (~20-40KB). */
const SIZE = 'M'

async function fetchCover(book) {
    const q = `${book.title} ${book.authors.split(',')[0].trim()}`
    const url = `https://openlibrary.org/search.json?q=${encodeURIComponent(q)}&limit=1&fields=title,author_name,cover_i,first_publish_year`
    const res = await fetch(url, {
        headers: { 'User-Agent': 'GoodBooks-CoverFetcher/1.0 (contact: goodbooks)' }
    })
    if (!res.ok) {
        console.warn(`  ⚠ ${book.id} ${book.title}: search HTTP ${res.status}`)
        return ''
    }
    const data = await res.json()
    const doc = data.docs && data.docs[0]
    if (!doc || !doc.cover_i) {
        console.warn(`  ⚠ ${book.id} ${book.title}: no cover in search results`)
        return ''
    }
    return `https://covers.openlibrary.org/b/id/${doc.cover_i}-${SIZE}.jpg`
}

async function main() {
    console.log(`Fetching covers for ${books.length} books from Open Library...`)
    const covers = {}
    for (let i = 0; i < books.length; i++) {
        const b = books[i]
        covers[b.id] = await fetchCover(b)
        if (covers[b.id]) console.log(`  ✓ ${b.id} ${b.title}`)
        await sleep(400)
    }
    const found = Object.values(covers).filter(Boolean).length
    fs.mkdirSync(path.dirname(OUT), { recursive: true })
    fs.writeFileSync(OUT, JSON.stringify(covers, null, 2) + '\n')
    console.log(`\n✅ ${found}/${books.length} covers found -> scripts/.covers.json`)
}

main().catch((e) => {
    console.error('❌', e.message)
    process.exit(1)
})

/**
 * 🌱 Seed the GoodBooks catalog into Supabase.
 * Prereqs: run docs/supabase/schema.sql in the Supabase SQL editor first, then:
 *   SUPABASE_URL=https://<ref>.supabase.co \
 *   SUPABASE_SERVICE_ROLE_KEY=<service key> \
 *   node scripts/seed-supabase.cjs
 *
 * Upserts shared/book-catalog.json into public.books via the REST API
 * (idempotent — safe to re-run after regenerating the catalog).
 */
const fs = require('fs')
const path = require('path')

const URL = process.env.SUPABASE_URL
const KEY = process.env.SUPABASE_SERVICE_ROLE_KEY

if (!URL || !KEY) {
    console.error('❌ Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.')
    process.exit(1)
}

const catalogPath = path.resolve(__dirname, '../shared/book-catalog.json')
const books = JSON.parse(fs.readFileSync(catalogPath, 'utf8'))

const rows = books.map((b) => ({
    id: b.id,
    title: b.title,
    authors: b.authors,
    cover_url: b.cover_url || '',
    rating: b.rating,
    ratings_count: b.ratingsCount,
    description: b.description || '',
    genres: b.genres || [],
    moods: b.moods || [],
    published_year: b.published_year,
    page_count: b.page_count,
    isbn: b.isbn || null
}))

async function main() {
    console.log(`🌱 Seeding ${rows.length} books -> ${URL}/rest/v1/books`)

    const res = await fetch(`${URL}/rest/v1/books`, {
        method: 'POST',
        headers: {
            apikey: KEY,
            Authorization: `Bearer ${KEY}`,
            'Content-Type': 'application/json',
            Prefer: 'resolution=merge-duplicates,return=minimal'
        },
        body: JSON.stringify(rows)
    })

    if (!res.ok) {
        const text = await res.text()
        console.error(`❌ Seed failed (${res.status}): ${text.slice(0, 400)}`)
        process.exit(1)
    }

    console.log(`✅ Seeded ${rows.length} books (upsert).`)
    console.log('Now set env vars on the Pages project:')
    console.log('  SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY')
}

main().catch((e) => {
    console.error('❌', e.message)
    process.exit(1)
})

/**
 * Export the curated book catalog to a shared JSON file.
 * Usage: node scripts/export-catalog.cjs
 * Output: shared/book-catalog.json — consumed by the Cloudflare Pages
 * Function data layer (functions/api/_lib/catalog.ts) so the server and the
 * frontend catalog never drift.
 */
const { execSync } = require('child_process')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const OUT = path.join(ROOT, 'shared/book-catalog.json')

// Evaluate the TypeScript catalog module via vite-node (project has it).
const script = `
import { BOOK_CATALOG } from './src/data/bookCatalog.ts'
console.log(JSON.stringify(BOOK_CATALOG))
`

try {
    const tmp = path.join(ROOT, '.catalog-export.mjs')
    fs.writeFileSync(tmp, script)
    const out = execSync(`npx vite-node "${tmp}"`, {
        cwd: ROOT,
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'pipe']
    })
    fs.unlinkSync(tmp)
    const trimmed = out.trim()
    const parsed = JSON.parse(trimmed)
    fs.mkdirSync(path.dirname(OUT), { recursive: true })
    fs.writeFileSync(OUT, JSON.stringify(parsed, null, 2) + '\n')
    console.log(`✅ Exported ${parsed.length} books -> shared/book-catalog.json`)
} catch (err) {
    console.error('Export failed:', err.stderr || err.message)
    process.exit(1)
}

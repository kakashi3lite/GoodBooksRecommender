#!/usr/bin/env node
/**
 * 🔗 Documentation link checker
 *
 * Verifies that every relative link in every Markdown file resolves to a real
 * path. External URLs, anchors and mail links are ignored (they are not ours to
 * guarantee). Run after adding, moving or renaming documentation:
 *
 *   npm run docs:check
 *
 * Exits 1 when a link is broken so it can gate CI.
 */
const fs = require('node:fs')
const path = require('node:path')

const ROOT = path.resolve(__dirname, '..')
const SKIP_DIRS = new Set(['node_modules', '.git', 'dist', 'venv', '.wrangler', 'mlruns', '__pycache__', 'data'])
const LINK_RE = /\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g

/** @returns {string[]} absolute paths of every Markdown file worth checking */
function collectMarkdown(dir, out = []) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (entry.name.startsWith('._') || entry.name === '.DS_Store') continue
        if (entry.isDirectory()) {
            if (SKIP_DIRS.has(entry.name)) continue
            collectMarkdown(path.join(dir, entry.name), out)
        } else if (entry.isFile() && entry.name.endsWith('.md')) {
            out.push(path.join(dir, entry.name))
        }
    }
    return out
}

const isExternal = (target) =>
    /^(https?:|mailto:|tel:|data:|ftp:)/i.test(target) || target.startsWith('#')

function checkLink(file, target) {
    const clean = decodeURIComponent(target.split('#')[0].split('?')[0])
    if (!clean) return null // pure anchor
    const resolved = clean.startsWith('/')
        ? path.join(ROOT, clean)
        : path.resolve(path.dirname(file), clean)
    return fs.existsSync(resolved) ? null : clean
}

const files = collectMarkdown(ROOT)
const broken = []
let checked = 0

for (const file of files) {
    const text = fs.readFileSync(file, 'utf8')
    for (const match of text.matchAll(LINK_RE)) {
        const target = match[1].trim()
        if (!target || isExternal(target)) continue
        checked += 1
        const missing = checkLink(file, target)
        if (missing) {
            broken.push({
                file: path.relative(ROOT, file),
                target,
                resolved: path.relative(ROOT, path.resolve(path.dirname(file), missing))
            })
        }
    }
}

console.log(`docs:check — ${files.length} markdown files, ${checked} relative links`)

if (broken.length > 0) {
    console.error(`\n❌ ${broken.length} broken link(s):\n`)
    for (const { file, target, resolved } of broken) {
        console.error(`  ${file}\n    → ${target}  (resolved: ${resolved})`)
    }
    process.exit(1)
}

console.log('✅ all relative links resolve')

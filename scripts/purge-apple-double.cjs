#!/usr/bin/env node
/**
 * 🍎 purge-apple-double.cjs — strip macOS Apple Double files before deploy
 *
 * Chain-of-Thought:
 *   macOS (especially on external / exFAT volumes like /Volumes/T9) writes a
 *   `._name` sidecar next to many files. Those sidecars are not valid
 *   JavaScript/TypeScript, so `wrangler pages deploy` fails to bundle the
 *   Functions directory when they are present — a documented pitfall in
 *   docs/PROJECT_STATUS.md and docs/LIVE_ARCHITECTURE_RUNBOOK.md §18.
 *
 *   CI runs on Linux and never sees them, so this only ever bites a local
 *   deploy. Running this as part of `npm run deploy` makes local and CI
 *   deploys behave identically.
 *
 * Scope: `dist/` and `functions/` only — the two trees wrangler uploads.
 * Safe to run repeatedly; exits 0 when nothing matches.
 */

const fs = require('node:fs')
const path = require('node:path')

const ROOT = path.resolve(__dirname, '..')
const TARGETS = ['dist', 'functions']

const isAppleDouble = (name) => name.startsWith('._') || name === '.DS_Store'

/** Recursively delete Apple Double files; returns the removed paths. */
const purge = (dir, removed = []) => {
  if (!fs.existsSync(dir)) return removed

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (isAppleDouble(entry.name)) {
      fs.rmSync(full, { recursive: true, force: true })
      removed.push(path.relative(ROOT, full))
      continue
    }
    if (entry.isDirectory()) purge(full, removed)
  }
  return removed
}

const removed = TARGETS.flatMap((target) => purge(path.join(ROOT, target)))

if (removed.length > 0) {
  console.log(`🧹 Removed ${removed.length} Apple Double / .DS_Store file(s)`)
} else {
  console.log('🧹 No Apple Double files — bundle is clean')
}

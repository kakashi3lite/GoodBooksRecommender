/**
 * 🧪 Production posture — the headers and CSP the live site actually ships
 *
 * Two defects were found only by loading the deployed site in a real browser:
 *
 *   1. Cloudflare injects its Web Analytics beacon at the edge, but the CSP's
 *      `script-src` did not allow `static.cloudflareinsights.com`, so every page
 *      load logged a violation and no analytics were collected.
 *   2. `public/_headers` served no `Strict-Transport-Security`, leaving the first
 *      request of a session open to downgrade.
 *
 * These are one-line values that nothing else exercises, so they are asserted here.
 */

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const root = resolve(__dirname, '..')
const html = readFileSync(resolve(root, 'index.html'), 'utf8')
const headers = readFileSync(resolve(root, 'public/_headers'), 'utf8')

const cspDirective = (name: string): string[] => {
    const match = html.match(/Content-Security-Policy" content="([\s\S]*?)"/)
    const policy = match?.[1] ?? ''
    const line = policy.split(';').map((part) => part.trim()).find((part) => part.startsWith(name))
    return (line ?? '').split(/\s+/).slice(1)
}

describe('production posture', () => {
    it('allows the edge-injected Cloudflare analytics beacon in script-src', () => {
        expect(cspDirective('script-src')).toContain('https://static.cloudflareinsights.com')
    })

    it('keeps a default-src and forbids plugins', () => {
        expect(cspDirective('default-src')).toEqual(["'self'"])
        expect(cspDirective('object-src')).toEqual(["'none'"])
    })

    it('serves HSTS so the first request of a session cannot be downgraded', () => {
        expect(headers).toMatch(/Strict-Transport-Security:\s*max-age=\d{7,};\s*includeSubDomains/)
    })

    it('still forbids framing and MIME sniffing', () => {
        expect(headers).toMatch(/X-Frame-Options:\s*DENY/)
        expect(headers).toMatch(/X-Content-Type-Options:\s*nosniff/)
    })
})

/**
 * 🛡️ /assets/* guard — never let the SPA fallback poison the asset cache.
 *
 * Chain-of-Thought: `_headers` marks /assets/* as `immutable` (great for
 * hashed files). But during a deploy the browser can fetch a NEW index.html
 * that references a hashed asset which hasn't propagated yet — that request
 * falls through to the `/* → /index.html` SPA rewrite and the browser caches
 * the HTML (200 text/html) under the asset URL for a YEAR. Every load then
 * fails with "Failed to load module script ... MIME type text/html".
 *
 * This function passes real assets through unchanged (headers preserved), but
 * turns the SPA-fallback HTML for a missing asset into a clean, non-cacheable
 * 404 — so a stale index.html fails fast with a normal error instead of
 * poisoning the cache, and the next (correct) index.html works.
 */
import { type PagesFunction } from '../_lib/types'

export const onRequestGet: PagesFunction = async (context) => {
    // Try the real static file (next() → static assets, then _redirects).
    const response = await context.next()
    const contentType = response.headers.get('content-type') ?? ''

    // A real hashed asset is never HTML — if we got HTML, it's the SPA
    // fallback for a missing file. Return a proper non-cacheable 404.
    if (contentType.includes('text/html')) {
        return new Response('Not Found', {
            status: 404,
            headers: { 'Cache-Control': 'no-store' }
        })
    }
    return response
}

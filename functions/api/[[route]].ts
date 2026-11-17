/**
 * 🚫 API catch-all (Cloudflare Pages Function)
 * Chain-of-Thought: Handles every /api/* path not claimed by a more specific
 * route (books, ai, ...). Returns a clean 404 JSON so frontend API clients get
 * a proper HTTP error instead of the SPA index.html fallback.
 *
 * Pages Functions take precedence over `_redirects` and static assets, so this
 * rule is guaranteed to apply even for unknown /api/* sub-paths.
 */
import { type PagesFunction } from './_lib/types'

export const onRequest: PagesFunction = async () =>
    new Response(
        JSON.stringify({
            error: 'not_found',
            message:
                'This endpoint does not exist. Known API groups: /api/books, /api/accounts, /api/ai, /api/reading.'
        }),
        {
            status: 404,
            headers: { 'Content-Type': 'application/json' }
        }
    )

/**
 * 🚫 Static API Interceptor (Cloudflare Pages Function)
 * Chain-of-Thought: This deployment is a static site — there is no backend.
 * Intercept every /api/* request and answer with a clean 404 JSON so frontend
 * API clients (axios / fetch) get a proper HTTP error instead of the SPA
 * index.html fallback, and can fall back to curated/local data gracefully.
 *
 * Pages Functions take precedence over `_redirects` and static assets, so this
 * rule is guaranteed to apply even for unknown /api/* sub-paths.
 */
export async function onRequest(): Promise<Response> {
    return new Response(
        JSON.stringify({
            error: 'not_found',
            message:
                'This static deployment does not serve API endpoints. The backend API is not part of the Cloudflare Pages deployment.'
        }),
        {
            status: 404,
            headers: { 'Content-Type': 'application/json' }
        }
    )
}

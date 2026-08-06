/**
 * Minimal Pages Function types (self-contained — avoids a dependency on
 * @cloudflare/workers-types). Matches the runtime shape Cloudflare provides.
 */

/** Env vars this project's functions read (server-side only). */
export interface PagesEnv {
    SUPABASE_URL?: string
    SUPABASE_SERVICE_ROLE_KEY?: string
    AI_PROVIDER?: string
    AI_API_KEY?: string
    AI_MODEL?: string
    AI_BASE_URL?: string
}

export interface PagesContext<Env = PagesEnv> {
    request: Request
    env: Env
    params: Record<string, string | string[]>
    waitUntil: (p: Promise<unknown>) => void
    next: (input?: Request | string, init?: RequestInit) => Promise<Response>
}

export type PagesFunction<Env = PagesEnv> = (
    context: PagesContext<Env>
) => Promise<Response>

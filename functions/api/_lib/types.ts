/**
 * Minimal Pages Function types (self-contained — avoids a dependency on
 * @cloudflare/workers-types). Matches the runtime shape Cloudflare provides.
 */

/** The subset of the D1 API these functions use. */
export interface D1Result<T = unknown> {
    results?: T[]
    success: boolean
    meta?: Record<string, unknown>
}

export interface D1PreparedStatementLike {
    bind(...values: unknown[]): D1PreparedStatementLike
    first<T = unknown>(column?: string): Promise<T | null>
    all<T = unknown>(): Promise<D1Result<T>>
    run(): Promise<D1Result>
}

export interface D1DatabaseLike {
    prepare(query: string): D1PreparedStatementLike
    batch<T = unknown>(statements: D1PreparedStatementLike[]): Promise<D1Result<T>[]>
    exec(query: string): Promise<{ count: number; duration: number }>
}

/** Env vars this project's functions read (server-side only). */
export interface PagesEnv {
    /** D1 database binding (customer accounts). Configured in wrangler.toml. */
    DB?: D1DatabaseLike
    /** One-time token for the temporary Supabase audit endpoint. */
    AUDIT_TOKEN?: string
    /** Salt for hashed rate-limit keys (set as a Pages secret). */
    RATE_LIMIT_SALT?: string
    SUPABASE_URL?: string
    SUPABASE_SERVICE_ROLE_KEY?: string
    SUPABASE_ANON_KEY?: string
    MINIMAX_API_KEY?: string
    OPENAI_API_KEY?: string
    /** @deprecated legacy alias — prefer OPENAI_API_KEY */
    AI_API_KEY?: string
    AI_PROVIDER?: string
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

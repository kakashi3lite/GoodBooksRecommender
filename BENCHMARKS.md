# Benchmarks & Performance Targets

The live system is a static SPA plus stateless edge functions. "Performance" here
means: page load, edge response time, and D1 query cost.

## Targets

| Area | Target | How it is measured |
|---|---|---|
| App shell (first contentful paint) | < 1.5 s on a warm CDN edge | Lighthouse / browser devtools against `https://books.dalecabra.com` |
| API response (catalog, search, recommend) | < 200 ms p50 at the edge | `curl -w '%{time_total}'`, Cloudflare analytics |
| `GET /api/accounts` (D1 point read) | < 20 ms server time | D1 query `meta.duration`; the lookup uses `accounts_email_uidx` |
| `POST /api/accounts` (create) | < 40 ms server time | includes SHA-256 + insert + audit write |
| AI chat | 1–6 s | dominated by the provider; the UI streams a fallback reply from the local engine if the LLM is unavailable |

## Measuring

```bash
# Warm + measure three endpoints
for p in /api/books "/api/books/search?q=cozy" /api/accounts; do
  curl -s -o /dev/null -w "%{http_code} %{time_total}s  $p\n" "https://books.dalecabra.com$p"
done

# D1 statement timings (server-side, excludes network)
npx wrangler d1 execute goodbooks-accounts --remote \
  --command "select count(*) from accounts;" | grep -E "sql_duration_ms|rows_read"
```

Frontend bundle budget lives in the Vite build output (`npm run build`); the
account client is a separate lazy chunk (`userRepository-*.js`, ~2 kB gzip) so it
never blocks first paint.

## Known bottlenecks

- **AI chat** is provider-bound; ranking never depends on it (the local engine
  answers instantly when the LLM is slow or unconfigured).
- **Web search / trending** depend on third-party catalogs (Open Library, Google
  Books) and are TTL-cached at the edge.
- **Legacy ML stack** (`src/models/`) warms models on cold start — irrelevant to
  production because it is not deployed.

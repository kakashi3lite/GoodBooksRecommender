-- ═══════════════════════════════════════════════════════════════════════════
-- GoodBooks — Reader data + recommendation audit (additive migration)
--
-- Why this migration exists
--   1. `recommendations_log` was already written to by
--      functions/api/_lib/db.ts (fire-and-forget audit) but was never created
--      in the schema — every audit write silently 404'd. This adds the table
--      the code has always expected.
--   2. Reading progress is the product's north-star data. `reading_events`
--      mirrors the reader's real sessions (started / progress / finished) from
--      the browser into Postgres so progress can outlive one device and the
--      recommender has interaction history to learn from later.
--
-- Privacy model
--   Both tables are write-only from the server's perspective:
--     * RLS is enabled
--     * NO policies are granted to `anon` / `authenticated`
--     * only the service-role key (used exclusively inside Pages Functions)
--       can read or write
--   The browser never receives another reader's data, and there is no public
--   read path. Restoring data onto a new device must be an explicit, opt-in
--   flow added later — never automatic.
--
-- Safe to run more than once (idempotent).
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Recommendation audit (referenced by functions/api/_lib/db.ts) ─────────
create table if not exists public.recommendations_log (
  id         bigint generated always as identity primary key,
  user_id    text,
  strategy   text not null,
  book_ids   text[] not null default '{}',
  context    text,
  created_at timestamptz not null default now()
);

comment on table public.recommendations_log is
  'Server-side audit of recommendation requests. Evaluation data for the next recommender.';

alter table public.recommendations_log enable row level security;

create index if not exists recommendations_log_created_at_idx
  on public.recommendations_log (created_at desc);
create index if not exists recommendations_log_strategy_idx
  on public.recommendations_log (strategy);

-- ─── Reading events (the reader's real sessions, mirrored from the client) ─
create table if not exists public.reading_events (
  id           bigint generated always as identity primary key,
  -- Anonymous device id (UUID v4 generated in the browser, kept in localStorage).
  client_id    text not null,
  book_id      text not null,
  event_type   text not null check (event_type in ('started','progress','finished','wishlisted')),
  -- Session delta in pages (progress events).
  pages        integer not null default 0,
  -- Absolute position, when the reader used the "I'm on page N" check-in.
  page         integer,
  progress     integer not null default 0 check (progress between 0 and 100),
  -- The reader's LOCAL calendar day (not UTC) so streaks stay truthful.
  session_date date,
  created_at   timestamptz not null default now()
);

comment on table public.reading_events is
  'Write-only mirror of client-side reading activity (started/progress/finished).';

alter table public.reading_events enable row level security;

create index if not exists reading_events_client_idx
  on public.reading_events (client_id, created_at desc);
create index if not exists reading_events_book_idx
  on public.reading_events (book_id);

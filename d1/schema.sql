-- ═══════════════════════════════════════════════════════════════════════════
-- GoodBooks — Cloudflare D1 schema (customer accounts)
--
-- Apply (remote, the live database used by Pages Functions):
--   npx wrangler d1 execute goodbooks-accounts --remote --file=d1/schema.sql
-- Apply (local, for `wrangler pages dev`):
--   npx wrangler d1 execute goodbooks-accounts --local --file=d1/schema.sql
--
-- Idempotent: safe to run more than once.
--
-- Why D1: accounts must survive a browser wipe and a device change, and the
-- app is already served from Cloudflare Pages — the D1 binding needs no
-- external credentials, no connection pool, and adds a single-digit-ms read
-- on the same edge that renders the page.
-- ═══════════════════════════════════════════════════════════════════════════

create table if not exists accounts (
  id               text primary key,
  -- Case-insensitive uniqueness: Ada@x.com and ada@x.com are one account.
  email            text not null collate nocase,
  name             text not null,
  favorite_genres  text not null default '[]',
  preferred_moods  text not null default '[]',
  reading_goal     integer not null default 24,
  reading_level    text not null default 'novice',
  -- SHA-256 of the bearer key handed to the client at creation. The raw key
  -- is never stored, so a database dump cannot be replayed as a login.
  account_key_hash text not null,
  created_at       text not null,
  updated_at       text not null
);

create unique index if not exists accounts_email_uidx on accounts (email collate nocase);
create index if not exists accounts_updated_at_idx on accounts (updated_at desc);

-- Audit trail — every write is recorded so CRUD can be proven after the fact
-- (and so a future "restore my account" flow has an ordered history).
create table if not exists account_events (
  id         integer primary key autoincrement,
  account_id text,
  email      text,
  action     text not null check (action in ('created', 'updated', 'deleted')),
  created_at text not null
);

create index if not exists account_events_created_at_idx
  on account_events (created_at desc);

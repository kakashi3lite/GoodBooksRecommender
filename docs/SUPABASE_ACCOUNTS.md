# 🗄️ Database-Backed User Accounts (Supabase)

User accounts currently persist in the browser (localStorage) — fully functional with zero
config. To make accounts **database-backed** (so testers and real users have durable accounts
across devices), wire in a free Supabase project. ~10 minutes, no credit card.

---

## 1. Create the project

1. Go to https://supabase.com → **New project** (free tier).
2. Note your **Project URL** (`https://<project>.supabase.co`) and the **anon public key**
   (Dashboard → Settings → API).

## 2. Create the `profiles` table

Open **SQL Editor** → **New query** → paste:

```sql
-- Profiles for GoodBooks accounts (one row per registered email)
create table if not exists public.profiles (
  email           text primary key,
  name            text not null,
  favorite_genres jsonb not null default '[]',
  reading_goal    integer not null default 24,
  reading_level   text not null default 'novice',
  updated_at      timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- RLS: anyone can read a profile by email; owners can update their own
create policy "Profiles are readable" on public.profiles
  for select using (true);

create policy "Owners update their profile" on public.profiles
  for update using (auth.jwt() ->> 'email' = email);
```

> The app uses the **anon key** and upserts by email. If you prefer stricter RLS, gate
> inserts behind auth and use a service role in a Cloudflare Worker instead.

## 3. Configure the frontend

Copy `.env.example` → `.env` (or set these in Cloudflare Pages → **Settings → Environment
variables**):

```
VITE_SUPABASE_URL=https://<project>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon-public-key>
```

Then rebuild/deploy. When these are set:

- **Onboarding** → `register` + `completeOnboarding` run locally (instant UX) **and** the
  account is upserted into `profiles` via `src/lib/userRepository.ts`.
- **Returning users** → on app start, `syncAccountToServer` re-syncs the restored account.
- **Not configured** → everything still works on localStorage (the graceful fallback).

## 4. Verify

After onboarding, in Supabase → **Table Editor → profiles**, you should see a row per tester:
`email`, `name`, `favorite_genres` (JSON array), `reading_goal`.

## Files

| File | Purpose |
|---|---|
| `src/lib/supabaseClient.ts` | Lazy client — `null` when unconfigured |
| `src/lib/userRepository.ts` | `syncUserAccount` / `fetchUserAccount` (upsert + read) |
| `src/stores/user/userSlice.ts` | `syncAccountToServer` thunk (best-effort, non-fatal) |
| `.env.example` | `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` |

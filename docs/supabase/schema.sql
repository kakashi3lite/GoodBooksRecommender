-- ═══════════════════════════════════════════════════════════════════════════
-- GoodBooks — Supabase schema (run ONCE in the Supabase SQL editor)
-- Real-time data layer for the Cloudflare Pages Functions + frontend.
--
-- How to activate the live database:
--   1. Create a free project at https://supabase.com
--   2. Open SQL Editor → paste this file → Run
--   3. Set env vars on the Cloudflare Pages project:
--        SUPABASE_URL  = https://<project-ref>.supabase.co
--        SUPABASE_SERVICE_ROLE_KEY = <Service role key (Settings → API)>
--      and for the frontend accounts:
--        VITE_SUPABASE_URL = same URL
--        VITE_SUPABASE_ANON_KEY = <anon key>
--   4. Redeploy (CI or `npm run deploy`) — the API now reads live DB rows.
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── Books catalog ─────────────────────────────────────────────────────────
create table if not exists public.books (
  id            text primary key,
  title         text not null,
  authors       text not null,
  cover_url     text not null default '',
  rating        numeric not null default 0,
  ratings_count integer not null default 0,
  description   text not null default '',
  genres        text[] not null default '{}',
  moods         text[] not null default '{}',
  published_year integer,
  page_count    integer,
  isbn          text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

alter table public.books enable row level security;
create policy "books are publicly readable"
  on public.books for select using (true);

-- ─── User profiles (auth.users → profiles) ─────────────────────────────────
create table if not exists public.profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  display_name  text,
  email         text,
  reading_level text default 'novice',
  created_at    timestamptz not null default now()
);

alter table public.profiles enable row level security;
create policy "profiles are owner-only"
  on public.profiles for all using (auth.uid() = id);

-- ─── Reading preferences (taste profile) ───────────────────────────────────
create table if not exists public.user_preferences (
  id             uuid primary key references auth.users(id) on delete cascade,
  favorite_genres text[] not null default '{}',
  preferred_moods text[] not null default '{}',
  reading_goal   integer not null default 24,
  reading_pace   text,
  updated_at     timestamptz not null default now()
);

alter table public.user_preferences enable row level security;
create policy "preferences are owner-only"
  on public.user_preferences for all using (auth.uid() = id);

-- ─── Reading activity (real-time feed) ─────────────────────────────────────
create table if not exists public.reading_activity (
  id         bigint generated always as identity primary key,
  user_id    uuid references auth.users(id) on delete cascade,
  book_id    text references public.books(id) on delete cascade,
  event_type text not null check (event_type in ('started','progress','finished','wishlisted')),
  progress   integer not null default 0,
  created_at timestamptz not null default now()
);

alter table public.reading_activity enable row level security;
create policy "reading activity is readable by all"
  on public.reading_activity for select using (true);
create policy "users insert their own activity"
  on public.reading_activity for insert with check (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- Seed: 24 curated books (idempotent upsert)
-- Generated from shared/book-catalog.json — regenerate with
-- `node scripts/export-catalog.cjs` then `node scripts/seed-supabase.cjs`
-- ═══════════════════════════════════════════════════════════════════════════
-- Seed books (generated from shared/book-catalog.json)
insert into public.books (id, title, authors, cover_url, rating, ratings_count, description, genres, moods, published_year, page_count, isbn)
values
  ('b-01', 'The Midnight Library', 'Matt Haig', '', 4.3, 120000, 'Between life and death there is a library, and within that library, the shelves go on forever.', ARRAY['Fiction','Literary Fiction'], ARRAY['thought-provoking','emotional','uplifting'], 2020, 288, NULL),
  ('b-02', 'Project Hail Mary', 'Andy Weir', '', 4.7, 98000, 'A lone astronaut must save humanity in this near-perfect sci-fi thriller packed with hard science and heart.', ARRAY['Science Fiction','Adventure'], ARRAY['adventurous','funny','fast-paced','uplifting'], 2021, 496, NULL),
  ('b-03', 'Tomorrow, and Tomorrow, and Tomorrow', 'Gabrielle Zevin', '', 4.5, 85000, 'A decade-spanning story about friendship, creativity, and the worlds we build together.', ARRAY['Fiction','Literary Fiction'], ARRAY['emotional','thought-provoking','quiet'], 2022, 416, NULL),
  ('b-04', 'The House in the Cerulean Sea', 'T.J. Klune', '', 4.6, 76000, 'A caseworker journeys to a remote island orphanage for magical children in this cozy, heartwarming tale.', ARRAY['Fantasy','Fiction'], ARRAY['cozy','uplifting','funny','emotional'], 2020, 400, NULL),
  ('b-05', 'Piranesi', 'Susanna Clarke', '', 4.4, 42000, 'A man lives in an endless house of halls and statues, and the mystery of his world slowly unfolds.', ARRAY['Fantasy','Mystery'], ARRAY['mysterious','thought-provoking','quiet','dark'], 2020, 272, NULL),
  ('b-06', 'A Psalm for the Wild-Built', 'Becky Chambers', '', 4.4, 31000, 'A tea monk and a robot explore what it means to be alive in a gentle, hopeful novella.', ARRAY['Science Fiction','Fantasy'], ARRAY['cozy','quiet','uplifting','thought-provoking'], 2021, 160, NULL),
  ('b-07', 'The Silent Patient', 'Alex Michaelides', '', 4.6, 150000, 'A woman''s act of violence against her husband, and her refusal to speak a single word about it.', ARRAY['Mystery','Thriller'], ARRAY['mysterious','fast-paced','dark'], 2019, 336, NULL),
  ('b-08', 'Educated', 'Tara Westover', '', 4.8, 200000, 'A memoir about education, family, and the struggle for self-invention.', ARRAY['Biography','Nonfiction'], ARRAY['emotional','thought-provoking','uplifting'], 2018, 352, NULL),
  ('b-09', 'Where the Crawdads Sing', 'Delia Owens', '', 4.5, 180000, 'A coming-of-age mystery set in the marshlands of North Carolina.', ARRAY['Fiction','Mystery','Historical Fiction'], ARRAY['emotional','mysterious','quiet'], 2018, 384, NULL),
  ('b-10', 'The Seven Husbands of Evelyn Hugo', 'Taylor Jenkins Reid', '', 4.8, 160000, 'Hollywood''s golden age, and the secrets of a reclusive icon, told to an unknown journalist.', ARRAY['Fiction','Historical Fiction','Romance'], ARRAY['emotional','romantic','thought-provoking'], 2017, 400, NULL),
  ('b-11', 'Dune', 'Frank Herbert', '', 4.3, 250000, 'The epic desert planet saga of politics, religion, and survival.', ARRAY['Science Fiction','Fantasy'], ARRAY['epic','dark','thought-provoking','adventurous'], 1965, 688, NULL),
  ('b-12', 'The Name of the Wind', 'Patrick Rothfuss', '', 4.6, 180000, 'The riveting first-person narrative of Kvothe, a magically gifted young man.', ARRAY['Fantasy','Adventure'], ARRAY['epic','adventurous','emotional'], 2007, 662, NULL),
  ('b-13', 'Gone Girl', 'Gillian Flynn', '', 4.2, 220000, 'On their fifth wedding anniversary, Nick''s wife disappears.', ARRAY['Thriller','Mystery'], ARRAY['dark','fast-paced','mysterious'], 2012, 432, NULL),
  ('b-14', 'The Thursday Murder Club', 'Richard Osman', '', 4.3, 90000, 'Four unlikely retirees meet weekly to solve cold cases — and stumble onto a real murder.', ARRAY['Mystery','Fiction'], ARRAY['cozy','funny','mysterious'], 2020, 400, NULL),
  ('b-15', 'The Song of Achilles', 'Madeline Miller', '', 4.6, 140000, 'A beautiful retelling of the Iliad, centered on the bond between Achilles and Patroclus.', ARRAY['Historical Fiction','Romance','Fantasy'], ARRAY['emotional','romantic','epic','dark'], 2011, 416, NULL),
  ('b-16', 'Atomic Habits', 'James Clear', '', 4.9, 300000, 'Tiny changes, remarkable results — the definitive guide to habit formation.', ARRAY['Self-Help','Nonfiction'], ARRAY['uplifting','thought-provoking'], 2018, 320, NULL),
  ('b-17', 'The Invisible Life of Addie LaRue', 'V.E. Schwab', '', 4.4, 110000, 'A girl who makes a deal to live forever — but is cursed to be forgotten by everyone she meets.', ARRAY['Fantasy','Historical Fiction','Romance'], ARRAY['emotional','romantic','thought-provoking','dark'], 2020, 448, NULL),
  ('b-18', 'The Martian', 'Andy Weir', '', 4.6, 240000, 'Stranded on Mars, Mark Watney must science his way back to survival.', ARRAY['Science Fiction','Adventure'], ARRAY['funny','fast-paced','adventurous','uplifting'], 2014, 384, NULL),
  ('b-19', 'Normal People', 'Sally Rooney', '', 4, 130000, 'The tender, complicated relationship between two people who keep finding their way back to each other.', ARRAY['Literary Fiction','Romance','Fiction'], ARRAY['emotional','romantic','quiet','thought-provoking'], 2018, 288, NULL),
  ('b-20', 'The Southern Book Club''s Guide to Slaying Vampires', 'Grady Hendrix', '', 4.1, 45000, 'A book club of Southern housewives discovers a vampire in their neighborhood — and decides to fight back.', ARRAY['Horror','Fiction'], ARRAY['dark','funny','fast-paced'], 2020, 416, NULL),
  ('b-21', 'Circe', 'Madeline Miller', '', 4.5, 150000, 'The story of the mythological witch Circe, from exile to self-discovery.', ARRAY['Fantasy','Historical Fiction','Literary Fiction'], ARRAY['epic','emotional','thought-provoking'], 2018, 416, NULL),
  ('b-22', 'Sapiens', 'Yuval Noah Harari', '', 4.4, 280000, 'A sweeping history of humankind — how we got here and where we might go.', ARRAY['Nonfiction','Self-Help'], ARRAY['thought-provoking'], 2011, 464, NULL),
  ('b-23', 'The Guest List', 'Lucy Foley', '', 4.1, 60000, 'A wedding on a remote island turns deadly — and everyone has a secret.', ARRAY['Mystery','Thriller'], ARRAY['mysterious','fast-paced','dark'], 2020, 336, NULL),
  ('b-24', 'Beach Read', 'Emily Henry', '', 4.2, 80000, 'Two rival writers swap genres for the summer — and fall for each other.', ARRAY['Romance','Fiction'], ARRAY['cozy','romantic','funny','uplifting'], 2020, 384, NULL)
on conflict (id) do update set
  title = excluded.title,
  authors = excluded.authors,
  cover_url = excluded.cover_url,
  rating = excluded.rating,
  ratings_count = excluded.ratings_count,
  description = excluded.description,
  genres = excluded.genres,
  moods = excluded.moods,
  published_year = excluded.published_year,
  page_count = excluded.page_count,
  updated_at = now();

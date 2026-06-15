-- ============================================================
-- Mycroft — Agent 3: Media Narrative Tracker (Groq edition)
-- Supabase / PostgreSQL setup
-- ============================================================
-- Run this in the Supabase SQL editor before the first
-- pipeline execution. Creates the raw signal table, the report
-- store, supporting indexes, and the novel_signals view.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Primary signal table
-- ------------------------------------------------------------
create table if not exists media_narratives_raw (
  id                    uuid default gen_random_uuid() primary key,
  created_at            timestamptz default now(),
  processed_at          timestamptz,
  agent_run_id          uuid,
  article_url           text unique not null,   -- dedup key (upsert conflict target)
  headline              text,
  summary               text,
  source                text,
  published_at          timestamptz,
  core_claim            text,
  claim_type            text,
  narrative_label       text,
  information_age_score integer,
  is_recycled           boolean,
  first_appearance_date timestamptz,
  appearance_count      integer default 1,
  companies_mentioned   jsonb default '[]'::jsonb
);

-- ------------------------------------------------------------
-- 2. Report store — full markdown report per run
-- ------------------------------------------------------------
create table if not exists narrative_reports (
  id                 uuid default gen_random_uuid() primary key,
  created_at         timestamptz default now(),
  run_id             uuid,
  report_markdown    text,
  articles_processed integer,
  novel_count        integer,
  recycled_count     integer
);

-- ------------------------------------------------------------
-- 3. Indexes on media_narratives_raw
-- ------------------------------------------------------------
create index if not exists idx_mnr_information_age_score
  on media_narratives_raw (information_age_score);

create index if not exists idx_mnr_is_recycled
  on media_narratives_raw (is_recycled);

create index if not exists idx_mnr_narrative_label
  on media_narratives_raw (narrative_label);

create index if not exists idx_mnr_created_at
  on media_narratives_raw (created_at);

create index if not exists idx_mnr_source
  on media_narratives_raw (source);

-- GIN index for jsonb company-mention containment queries
create index if not exists idx_mnr_companies_mentioned
  on media_narratives_raw using gin (companies_mentioned);

-- ------------------------------------------------------------
-- 4. Dashboard / downstream view — novel signals only
--    (score >= 60, last 48h). Read by Agent 5.
-- ------------------------------------------------------------
create or replace view novel_signals as
select
  article_url,
  headline,
  source,
  published_at,
  core_claim,
  narrative_label,
  information_age_score,
  companies_mentioned,
  created_at
from media_narratives_raw
where information_age_score >= 60
  and created_at >= now() - interval '48 hours'
order by information_age_score desc;

-- ============================================================
-- Mycroft full schema across all agents
-- ------------------------------------------------------------
--   anxiety_runs          -- Agent 1: Reddit Anxiety Index        (built)
--   patent_runs           -- Agent 2: Patent Velocity Tracker      (built)
--   media_narratives_raw  -- Agent 3: Media Narrative Tracker      (this file)
--   narrative_reports     -- Agent 3: report store                 (this file)
--   story_consistency     -- Agent 4: Story Consistency            (not yet built)
--   blindspot_reports     -- Agent 5: Four-Layer Blindspot Detector (not yet built)
-- ============================================================

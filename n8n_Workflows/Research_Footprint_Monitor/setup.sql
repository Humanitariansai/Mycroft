-- =====================================================================
-- Mycroft — Agent 5: Research Footprint Monitor
-- Supabase / PostgreSQL schema
-- Tables: mindshare_signals, research_reports
-- =====================================================================

create table if not exists mindshare_signals (
  id                       uuid default gen_random_uuid() primary key,
  created_at               timestamptz default now(),
  run_timestamp            timestamptz,
  run_week                 text,
  agent_run_id             uuid,
  ticker                   text not null,
  company                  text,
  paper_count              integer,
  top_venues               jsonb default '[]'::jsonb,
  total_citations          integer,
  avg_citations            numeric,
  conference_presence      jsonb default '[]'::jsonb,
  has_neurips              boolean default false,
  has_icml                 boolean default false,
  has_cvpr                 boolean default false,
  has_iclr                 boolean default false,
  edit_count_7d            integer,
  unique_editors           integer,
  last_edit_timestamp      timestamptz,
  edit_velocity            numeric,
  is_spike                 boolean default false,
  research_footprint_score integer,
  footprint_tier           text,
  research_narrative       text,
  academic_signal          text,
  wikipedia_signal         text,
  combined_insight         text,
  watch_flag               boolean default false,
  unique (ticker, run_week)
);

create table if not exists research_reports (
  id                uuid default gen_random_uuid() primary key,
  created_at        timestamptz default now(),
  run_id            uuid,
  report_markdown   text,
  companies_tracked integer,
  dominant_count    integer,
  watch_flag_count  integer,
  wiki_spike_count  integer
);

create index if not exists idx_ms_ticker
  on mindshare_signals (ticker);
create index if not exists idx_ms_run_week
  on mindshare_signals (run_week);
create index if not exists idx_ms_footprint_score
  on mindshare_signals (research_footprint_score);
create index if not exists idx_ms_watch_flag
  on mindshare_signals (watch_flag);
create index if not exists idx_ms_is_spike
  on mindshare_signals (is_spike);

alter table mindshare_signals disable row level security;
alter table research_reports  disable row level security;

-- =====================================================================
-- MYCROFT FRAMEWORK — FULL SCHEMA MAP
-- ---------------------------------------------------------------------
-- AI-sector investment intelligence. Each agent writes an independent
-- signal table; downstream pattern agents read across them.
--
--   Agent 1 — Reddit Anxiety Index       -> anxiety_runs
--   Agent 2 — Patent Velocity Tracker     -> patent_runs
--   Agent 3 — Media Narrative Tracker     -> media_narratives_raw
--   Agent 4 — GitHub Commit Velocity      -> github_signals
--   Agent 5 — Research Footprint Monitor  -> mindshare_signals   (THIS AGENT)
--                                          -> research_reports    (report archive)
--   Agent 6 — Mindshare Gap / Pattern     -> reads mindshare_signals
--             (Wikipedia spike + no Reddit activity
--              => INFORMATION_ASYMMETRY_WINDOW)
--
-- Agent 5 measures research footprint across two time horizons:
--   Layer A  Semantic Scholar  (academic presence, 6-12 month lag)
--   Layer B  Wikipedia edits   (public knowledge activity, 24-72 hr lead)
-- combined into research_footprint_score (0-100) per company per week.
-- =====================================================================

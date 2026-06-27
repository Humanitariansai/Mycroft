-- =====================================================================
-- Mycroft — Workflow 6 / Agent 6: Signal Contradiction Detector
-- setup.sql
-- Creates the two tables this agent writes to, plus indexes.
-- This agent ONLY reads from the 5 upstream tables; it owns the two
-- contradiction_* tables below.
-- =====================================================================

create table if not exists contradiction_reports (
  id                       uuid default gen_random_uuid() primary key,
  created_at               timestamptz default now(),
  run_timestamp            timestamptz,
  run_week                 text,
  agent_run_id             uuid,
  ticker                   text not null,
  company                  text,
  contradiction_score      integer,
  contradiction_level      text,
  total_patterns           integer,
  highest_severity         text,
  patterns_detected        jsonb default '[]'::jsonb,
  signal_directions        jsonb default '{}'::jsonb,
  contradiction_narrative  text,
  most_significant_pattern text,
  investor_implication     text,
  confidence               text,
  data_gaps                jsonb default '[]'::jsonb,
  unique (ticker, run_week)
);

create table if not exists contradiction_run_reports (
  id                       uuid default gen_random_uuid() primary key,
  created_at               timestamptz default now(),
  run_id                   uuid,
  report_markdown          text,
  companies_analyzed       integer,
  critical_count           integer,
  elevated_count           integer,
  clean_count              integer,
  total_patterns_detected  integer,
  signal_availability      jsonb default '{}'::jsonb
);

create index if not exists idx_cr_ticker
  on contradiction_reports (ticker);
create index if not exists idx_cr_run_week
  on contradiction_reports (run_week);
create index if not exists idx_cr_contradiction_level
  on contradiction_reports (contradiction_level);
create index if not exists idx_cr_contradiction_score
  on contradiction_reports (contradiction_score);

alter table contradiction_reports      disable row level security;
alter table contradiction_run_reports  disable row level security;

-- =====================================================================
-- FULL MYCROFT SCHEMA — all 8 tables across the framework.
-- (For reference. Upstream tables are created by their own agents;
--  do NOT recreate them here. Only the two contradiction_* tables
--  above are owned by Agent 6.)
-- =====================================================================
--
--  TABLE                      | OWNER    | PURPOSE
--  ---------------------------+----------+--------------------------------
--  1. anxiety_runs            | Agent 1  | Crowd behavioral psychology;
--                             |          | anxiety_score, herd_detection.
--  2. patent_runs             | Agent 2  | Technology acceleration;
--                             |          | leaderboard (trend, velocityScore,
--                             |          | investmentSignal).
--  3. media_narratives_raw    | Agent 3  | Information-age scoring;
--                             |          | information_age_score,
--                             |          | companies_mentioned, is_recycled.
--  4. github_signals          | Agent 4  | Engineering velocity;
--                             |          | velocity_direction, delta_pct,
--                             |          | risk_flag, momentum_signal.
--  5. mindshare_signals       | Agent 5  | Research footprint;
--                             |          | research_footprint_score,
--                             |          | footprint_tier, is_spike,
--                             |          | academic_signal, wikipedia_signal.
--  6. contradiction_reports   | Agent 6  | Per-company contradiction record
--                             |          | (this file).
--  7. contradiction_run_reports| Agent 6 | Full markdown report per run
--                             |          | (this file).
--  8. (reserved)              |   —      | Future synthesis / alerting layer.
--
-- =====================================================================
-- Reference DDL for upstream tables (illustrative — owned elsewhere).
-- Provided only so Agent 6's reads are understandable in isolation.
-- =====================================================================
--
-- create table if not exists anxiety_runs (
--   id              uuid default gen_random_uuid() primary key,
--   created_at      timestamptz default now(),
--   anxiety_score   numeric,
--   herd_detection  jsonb default '[]'::jsonb
-- );
--
-- create table if not exists patent_runs (
--   id              uuid default gen_random_uuid() primary key,
--   created_at      timestamptz default now(),
--   leaderboard     jsonb default '[]'::jsonb
-- );
--
-- create table if not exists media_narratives_raw (
--   id                     uuid default gen_random_uuid() primary key,
--   created_at             timestamptz default now(),
--   information_age_score  numeric,
--   companies_mentioned    jsonb default '[]'::jsonb,
--   is_recycled            boolean default false
-- );
--
-- create table if not exists github_signals (
--   id                  uuid default gen_random_uuid() primary key,
--   run_timestamp       timestamptz default now(),
--   ticker              text,
--   company             text,
--   velocity_direction  text,
--   delta_pct           numeric,
--   risk_flag           text,
--   momentum_signal     text
-- );
--
-- create table if not exists mindshare_signals (
--   id                       uuid default gen_random_uuid() primary key,
--   run_timestamp            timestamptz default now(),
--   ticker                   text,
--   company                  text,
--   research_footprint_score numeric,
--   footprint_tier           text,
--   is_spike                 boolean default false,
--   watch_flag               text,
--   academic_signal          text,
--   wikipedia_signal         text
-- );
-- =====================================================================

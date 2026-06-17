-- ============================================================================
-- Mycroft Investment Intelligence Framework
-- Agent 4 — GitHub Commit Velocity Tracker
-- Supabase schema: github_signals + github_reports
-- ============================================================================

create table if not exists github_signals (
  id                      uuid default gen_random_uuid() primary key,
  created_at              timestamptz default now(),
  run_timestamp           timestamptz,
  run_week                text,
  agent_run_id            uuid,
  ticker                  text not null,
  company                 text,
  total_repos_active      integer,
  total_stars             integer,
  top_repo                text,
  languages               jsonb default '[]'::jsonb,
  repo_names              jsonb default '[]'::jsonb,
  velocity_direction      text,
  delta_pct               numeric,
  repos_delta             integer,
  stars_delta             integer,
  activity_classification text,
  momentum_signal         text,
  key_observation         text,
  notable_repos           jsonb default '[]'::jsonb,
  risk_flag               boolean default false,
  is_first_run            boolean default false,
  unique (ticker, run_week)
);

create table if not exists github_reports (
  id                  uuid default gen_random_uuid() primary key,
  created_at          timestamptz default now(),
  run_id              uuid,
  report_markdown     text,
  companies_tracked   integer,
  accelerating_count  integer,
  decelerating_count  integer,
  risk_flag_count     integer
);

create index if not exists idx_gs_ticker
  on github_signals (ticker);
create index if not exists idx_gs_velocity_direction
  on github_signals (velocity_direction);
create index if not exists idx_gs_risk_flag
  on github_signals (risk_flag);
create index if not exists idx_gs_run_timestamp
  on github_signals (run_timestamp);

alter table github_signals disable row level security;
alter table github_reports disable row level security;

-- Mycroft full schema:
-- anxiety_runs         — Agent 1
-- patent_runs          — Agent 2
-- media_narratives_raw — Agent 3
-- github_signals       — Agent 4 (this file)
-- github_reports       — Agent 4 (this file)
-- mindshare_signals    — Agent 5
-- contradiction_reports — Agent 6

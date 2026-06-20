-- Patent Filing Velocity Tracker — Supabase schema
-- Run this in the Supabase SQL editor before activating the n8n workflow.

create table patent_runs (
  id uuid default gen_random_uuid() primary key,
  created_at timestamptz default now(),
  date text,
  timestamp text,
  leaderboard jsonb,
  convergence jsonb,
  quarterly_stats jsonb,
  total_patents_analyzed integer
);

alter table patent_runs disable row level security;

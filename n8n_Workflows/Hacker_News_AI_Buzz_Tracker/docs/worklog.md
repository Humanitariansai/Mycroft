# Worklog — Hacker News AI Buzz Tracker

A running, timestamped record of effort. Newest entries at the top.

---

## Week 2 — 2026-06-20 — Core fetch pipeline (~20 hrs)

**Skeleton (~2 hrs)**
- Built the workflow spine: a `Schedule Trigger` for the daily cron and a `Manual Trigger` for
  testing. Added `Get Day Ago Unix Time`, a Code node that computes the trailing-window
  `sinceUnix` at runtime so the lookback is never hardcoded.

**Watchlist + multi-term queries (~2.5 hrs)**
- Loaded the 12 v1 entities into a `WatchList` node. Since HN Algolia does loose token matching
  (not boolean OR), built `Entity Term Pair` to fan each entity out into one `(entity, term)`
  item — one HTTP call per term, merged back later.

**Looping over entities (~5 hrs)**
- The time sink. Driving the per-term fetch required an inner loop inside the entity loop, and
  getting nested `Split In Batches` to behave correctly in n8n took a lot of trial and error — the
  loop kept short-circuiting or over-iterating until I worked out the right reset/merge wiring.
  Most of the debugging this week lived here.

**HTTP fetch (~1 hr)**
- Wired the `HTTP Request` to `search_by_date` with `tags=story`, the `numericFilters` window
  filter, and `hitsPerPage`/`page`. Confirmed live: busy entities return rich data, zero-hit
  entities produce a real record instead of erroring.

**Parse, dedupe, normalize (~5 hrs)**
- The other big chunk. Writing the `Get Metrics` logic was slow going — parsing hits down to the
  needed fields, deduping by `objectID` so a story matching two terms counts once, and rolling
  multi-term/alias hits up to the canonical entity. Factored the fetch into a sub-workflow
  (`Call 'HackerNews'`) to keep it modular.

**Docker build failure (~4 hrs, unplanned)**
- `docker compose up --build` died with exit 127 on `apk add` — because `n8n:latest` is now a
  Docker Hardened Image with the package manager stripped out. First fix exposed a version-pinning
  conflict (`libssl3`). Final fix: a multi-stage build installing python3/pip in a version-matched
  `alpine:3.22` builder, then copying the closure into the final image. Verified Python 3.12.13 /
  pip 25.1.1 in-container. Written up in `prompts_and_problems.md`.

**Housekeeping (~0.5 hr)**
- Committed Dockerfile, compose, and task-runner config alongside the workflow; updated the worklog.

**Decisions**
- Query strategy: one request per `queryTerm`, then merge + dedupe by `objectID` (per design.md §3).
- Watchlist loaded inline in a Code node for now; file-based config deferred to Week 11.

**Next (Week 3)**
- Implement the Buzz Score components (volume, engagement, front page, acceleration) with log
  normalization, the sparse-entity floor, and cold-start behavior; add golden fixtures and write
  `scoring_logic.md`.

---

## Week 1 — 2026-06-09 — Setup, API research, design

**Done**
- Stood up n8n locally via Docker; http://localhost:5678 loads and a workflow can be saved.
- Explored the HN Algolia `search_by_date` API by hand (query `Apple Intelligence`, trailing
  window). Confirmed response shape, the trailing-window `numericFilters` filter, and pagination
  fields. Recorded the sample request/response and findings in `design.md` §2.
- Scaffolded the folder: `README.md` (skeleton with the six sections), `.env.example`,
  `watchlist.json` (12 AI entities, v1), `design.md` (data model + Buzz Score spec), `.gitignore`.
- Wrote the Buzz Score formula spec and data model in `design.md`.

**Decisions**
- n8n runtime: Docker image + mounted volume.
- Supabase + Groq signup deferred to Weeks 4/5 (not needed until persistence + LLM land).
- `plan.md` is kept local only (gitignored), not pushed.

**Blockers**
- None.

**Next (Week 2)**
- Build the Schedule Trigger, Watchlist Set node, Split In Batches loop, and the HTTP Request to
  the HN Algolia search with the trailing-window filter.
- Parse hits, dedupe by `objectID`, normalize company names; handle zero-hit entities.

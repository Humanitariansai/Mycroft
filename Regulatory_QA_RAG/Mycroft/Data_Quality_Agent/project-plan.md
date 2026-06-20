# Data Contract Project: Build Plan

Living document. Captures thesis, architecture, build order, and the reasoning behind the sequencing.

---

## Thesis

The data contract problem has two halves:

- **Structural** (renames, drops, type changes) — well served by the existing deterministic stack: dbt manifest, dbt-checkpoint, Great Expectations, re_data, data diff, Gable.
- **Semantic** (unit changes, formula shifts, enum expansions, backfill drift) — underserved, because it requires reading the PR's intent, not just diffing the schema.

An LLM is the right tool for the semantic half **when used surgically**: confined to the reading-comprehension step, sitting on top of a deterministic lineage layer, not replacing it.

This project tests that thesis.

Companion Substack post: `the-breaks-that-compile-v2.md` (publish before building; follow up with build writeup).

---

## Falsifiable success criterion

Hand-labeled evaluation set of 50 PRs, each containing zero or one seeded semantic break. **F1 on binary "does this PR contain a semantic break" classification, bar at 0.8.** Eval set, labels, and per-PR outputs published with the build writeup.

If F1 drops below 0.8, or if real production incidents (collected from war stories in Substack comments) turn out to be predominantly structural, the thesis is wrong.

---

## System architecture

### Two repos

- **`mock-app-service`.** FastAPI, SQLAlchemy, Alembic migrations, Postgres. Tables: `users`, `accounts`, `subscriptions`, `transactions`, `events`. The "engineering" repo where schema and code changes originate. Domain-neutral SaaS framing.
- **`mock-analytics`.** dbt project (DuckDB for portability, Postgres optional) consuming the operational schema. Staging models mirror source tables. Mart models compute exec-level metrics: `fct_mrr`, `fct_revenue`, `dim_users`, `fct_engagement`.

The separation of repos is the whole reason the bug class exists in production. The demo must show it.

### Six components, in order of data flow

1. **GitHub App.** Registered against both repos. Listens for `pull_request` events on the app-service repo. Webhook receiver on Lambda or small ECS. Deploy via Terraform.
2. **Migration parser (deterministic).** AST parsing of Alembic migration files. Extracts: columns added, dropped, renamed, retyped; constraints changed; enum modifications; raw SQL via `op.execute`. Pure mechanical layer, no LLM.
3. **Lineage indexer (deterministic).** Pulls dbt `manifest.json` from analytics repo's main branch. Builds column-level dependency map using sqlglot for SQL parsing. Cached in S3 or a metadata branch on the analytics repo, refreshed by a GitHub Action on every merge to main.
4. **Deterministic impact analyzer.** Joins parsed migration against lineage map. Outputs precise list of structurally affected models. High-precision layer, produces useful output even if the LLM call fails.
5. **Semantic risk analyzer (LLM).** Anthropic API, Claude. Inputs: migration code, PR title and description, downstream model SQL for affected columns, column dictionary. Output: structured JSON with risk category, affected model, reasoning, confidence score. Temperature zero. Tight system prompt with few-shot examples per risk category.
6. **Action layer.** Posts structured comment on the source PR, separating deterministic findings from semantic risks. Optionally drafts a PR in the analytics repo with proposed model edits. Does not block merge.

---

## Demo scenarios

The build must exercise all three. Each tests a different capability.

### Scenario 1: structural break (baseline)

Alembic migration renames `users.signup_date` to `users.created_at`. dbt staging model breaks at compile time. Pure manifest traversal catches this. Agent confirms impact and drafts the rename in the analytics repo.

### Scenario 2: semantic unit break (highest-value)

Migration changes `subscriptions.amount_cents` to `subscriptions.amount` with backfill dividing by 100. PR description says "standardize amount column for new pricing tables." Type unchanged, constraints intact, every model still compiles. Downstream `fct_mrr` is now wrong by 100x. Manifest traversal cannot catch this. LLM reading migration + PR description + downstream model can flag it.

### Scenario 3: enum expansion

Migration adds `'paused'` to the `subscription_status` enum. Downstream `fct_mrr` filters on `status IN ('active', 'trialing')`. Paused subscriptions silently drop out of MRR. Model still runs. Sits between deterministic (pattern-match the `IN (...)` clause) and semantic (decide whether the new value belongs in the filter).

---

## Build phases

### Phase 0: design lock

Finalize repo names, table schemas, mart model definitions. Decide DuckDB vs Postgres for analytics layer. Sketch the three demo scenarios as a sequence of commits in the app-service repo. **Output:** one-page system diagram and a decision log.

### Phase 0.5: LLM spike (added based on risk analysis)

Before building infrastructure, validate that the LLM layer can actually do the job. Hand-write three migration files (one per scenario) plus 1–2 downstream SQL models per scenario. Write the semantic analyzer prompt. Run against the Anthropic API at temperature zero with structured JSON output. Expand to ~15 hand-crafted cases including null cases. Eyeball outputs.

**Decision gate:** does Scenario 2 work at all? At what false-positive rate? Does the LLM need the column dictionary, or do migration + PR description + downstream SQL suffice?

If the spike fails, the thesis is wrong and there's no point building the rest. If it succeeds, its outputs become the first 15 entries in the eval set.

Realistic time: a weekend.

### Phase 1: mock repos

Build `mock-app-service` and `mock-analytics`. Get the dbt project producing a non-trivial manifest with real column-level lineage across staging and marts. Seed the operational DB with synthetic data. Verify analytics models produce sensible metrics. No agent yet.

See `phase-1-plan.md` for the detailed plan.

### Phase 2: deterministic layer

Alembic migration parser. sqlglot-based column-level lineage extractor over the dbt manifest. Impact analyzer that joins the two. Runs as a local CLI against a PR diff. **Output:** list of affected models with precision.

### Phase 3: LLM layer

Build the semantic risk analyzer against the Anthropic API. Reuse and expand the hand-crafted test cases from Phase 0.5. Tune the prompt. Set up structured JSON output with confidence scores. Local CLI only.

### Phase 4: GitHub App

Webhook receiver, auth, comment posting. Deploy via Terraform. Wire phases 2 and 3 into the webhook handler. Test end-to-end with hand-pushed PRs.

### Phase 5: remediation PR generation

LLM drafts the dbt model edits needed and opens a draft PR in the analytics repo. Optional for first public release.

### Phase 6: evaluation

Build out the 50-PR labeled set (continuously accumulated since Phase 0.5, not from scratch). Compute F1. Publish results, eval set, and writeup.

---

## Key technical decisions made

- **Cross-repo, not single repo.** Reflects production reality.
- **Domain-neutral framing in the post; SaaS demo scenarios.** Broader applicability for job search.
- **Anthropic API for the LLM layer.** Small interview signal; fits the Mycroft and broader portfolio narrative.
- **Temperature zero on the semantic analyzer.** Determinism matters more than creativity here.
- **No merge blocking.** Advance warning plus draft PR only. Bots that block get disabled in week two.
- **Manifest fetched from analytics repo's main branch via GitHub Action, cached.** Do not compile dbt inside the webhook handler.
- **Validate the LLM before building infrastructure.** The thesis lives or dies on Scenario 2; test it cheaply first.
- **Start the eval set early, not at Phase 6.** Every hand-crafted case from Phase 0.5 and every test case from Phases 2–3 is an eval data point.

---

## Open decisions

- **DuckDB vs Postgres for the analytics layer.** DuckDB is faster to demo locally; Postgres is closer to production reality. Probably DuckDB for MVP.
- **Lambda vs small ECS for the webhook receiver.** Lambda is cheaper and fits the demo; ECS is closer to what most companies actually run.
- **Whether Phase 5 (auto-remediation PR) is in the first public release** or a follow-up.
- **Whether to add a Slack notification path** in addition to the GitHub comment. Probably yes, but only after the core agent is solid.

---

## Resume framing

Draft bullet, refine after the build:

> Built a cross-repo data contract agent that detects semantic schema breaks at the operational-to-analytical boundary, using deterministic dbt manifest analysis for structural impact and a focused LLM layer for semantic risk inference. Achieved F1 of [X] on a 50-PR labeled evaluation set. Deployed as a GitHub App via Terraform; written up on Substack.

What this signals: cross-repo system design, understanding of dbt internals, deliberate split between deterministic and LLM work (taste), public evaluation (rigor), production thinking (advance warning over blocking).

---

## Build-in-public plan

- Publish `the-breaks-that-compile-v2.md` on Substack **before** writing code. Drives war-story replies that become test cases.
- Build the system over four to six weeks alongside the job search, not as a replacement for it.
- Publish the build writeup with eval results, repo links, and a short demo video.
- Cross-post both essays on LinkedIn with a short framing line each.
- Use the project as the opening anecdote in "tell me about a project you are proud of" interview answers.

---

## Files

- `the-breaks-that-compile-v2.md` — the pre-build thesis essay, ready to publish.
- `project-plan.md` — this file.
- `phase-1-plan.md` — detailed plan for Phase 1.
- TBD: system diagram, decision log, eval set spec.

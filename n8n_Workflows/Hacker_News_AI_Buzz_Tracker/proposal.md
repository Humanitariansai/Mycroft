# Hacker News AI Buzz Tracker: Proposal

This proposal describes a technical-community attention signal for the AI sector and how it will be built over three months. The work is phased: the first month delivers a smaller but complete working version, and the next two months improve and extend it. This document explains what gets built, the problem it addresses, the technical approach, the scope for each phase, and where it is likely to struggle.

## What is being built

A Hacker News AI Buzz Tracker: an n8n agent that watches a list of AI companies and products on Hacker News, scores how much attention each one is getting, and reports the daily movers. In one line, it is a technical-community attention detector for the AI sector. Hacker News is not exclusively a developer forum; researchers, founders, investors, and journalists participate too, so the signal is best understood as a technical-practitioner mindshare signal rather than a pure developer one.

## The real problem it addresses

Financial signals about AI companies arrive late. Patents, filings, and earnings describe what a company has already done, and mainstream coverage tends to follow the price rather than lead it. The technical community talks first. When a model ships, an API breaks, a team is laid off, or a launch disappoints, it surfaces and gets argued over on Hacker News before it shows up in financial reporting.

The problem is that this early attention is invisible and unmeasured. A spike of developer interest, or a sudden wave of negative reception around an outage, is a leading indicator of mindshare that no structured signal currently captures. This agent turns that scattered, noisy conversation into a clean, comparable number so the shift is visible while it is still early.

The financial thesis behind the tracker is a **hypothesis to be tested, not a premise to be operationalized**: that mindshare leads price in the AI sector, and that the technical community is where mindshare forms first. This is plausible and sometimes demonstrably true (product launches, viral negative reception), but it is also contestable: Hacker News discusses AI infrastructure constantly without any price movement, some of the most-discussed entities are private with no ticker at all, and as Hacker News is itself more widely monitored the edge may decay over time. No backtest yet establishes that Hacker News activity has historically preceded price moves in AI equities, so the proposal does not assert it as fact.

Accordingly, the Buzz Score is positioned first as a legitimate **attention-tracking instrument**, and only conditionally as an investment signal. The leap from "attention" to "leading indicator for investment" is exactly what the signal validation backtest must establish, which is why that backtest is pulled forward to **early Phase 2** (rather than late Phase 2–3): it is the work that justifies treating the score as investment-actionable at all. Until the backtest produces evidence, a sustained buzz breakout is a candidate signal for the analytical and portfolio agents to *investigate* — prompting a research report, sharpening a comparative analysis within an AI subsector, or surfacing a name for risk review — not a validated predictor. The watchlist is organized around AI entities with optional ticker mappings precisely so the signal can be joined to downstream financial analysis once validated. Importantly, the score measures attention, not direction, which keeps it honest as one disciplined, unproven input among many rather than a standalone trade trigger.

## How it fits Mycroft

Mycroft's mission is "Using AI to Invest in AI": an ecosystem of specialized agents that analyze the AI sector and feed a coordination layer that turns signals into disciplined investment decisions. This agent is a concrete piece of that ecosystem, sitting squarely in Mycroft's **Intelligence Agents** division.

* **It is a Social Sentiment Agent.** Mycroft's Social Sentiment Agents are meant to analyze "discussions across social media platforms, developer forums, and industry communities" and contextualize them within broader technical and industry frameworks, rather than running simplistic sentiment scoring. The Buzz Tracker does exactly this for Hacker News, the most influential developer forum for the AI sector, producing a structured, comparable attention signal per entity instead of raw chatter.
* **It contributes a leading indicator.** Where Mycroft's structured sources describe what a company has already reported or formally disclosed, the Buzz Tracker captures developer attention *before* it reaches financial reporting, giving the framework a genuine leading signal to pair with its lagging structured data.
* **It feeds the Mycroft orchestration layer.** The deterministic Buzz Score and velocity are emitted as clean per entity signals that the Mycroft layer can ingest for **Cross-Agent Validation** (testing whether a developer attention spike confirms or contradicts other signals on the same entity), **Pattern Recognition** (connecting a buzz breakout to broader developments), and **Dynamic Task Allocation** (a breakout alert can redirect analytical capacity toward an entity worth a closer look). Coordination layer integration is an explicit deliverable in the later phase.

## Technical approach

The pipeline is intentionally simple and reads from a single free source.

* **Trailing window: 14 days (parameterized).** Every reference to a "trailing window" in this proposal resolves to **14 days**, exposed as a single configuration parameter (`TRAILING_WINDOW_DAYS`) so it can be retuned without code changes. The choice is a deliberate opinion: 7 days is too short to establish a stable per-entity baseline for the acceleration component (a single quiet weekend distorts it) and shortens cold-start to the point that velocity is unreliable; 30 days dilutes the very breakouts the signal exists to catch, smoothing a 3-day surge into the average. 14 days is the compromise — long enough that the trailing average is stable and the cold-start period (no usable velocity until ~3 daily runs accumulate, full window after 14) is bounded, short enough that a genuine breakout still moves the score against its own baseline. The acceleration component compares the current run against the trailing 14-day average; collection volume, velocity sensitivity, and cold-start duration are all downstream of this number, and it is revisited against Phase 1 data alongside the score weights.
* **Collection.** A scheduled run queries the Hacker News Search API (Algolia) for each watchlist entity over the trailing 14-day window. The endpoint needs no key and returns each story's title, url, points, comment count, and timestamp.
* **Normalization.** A Code node parses the hits, dedupes by `objectID`, and normalizes company and product names so that aliases (for example a company and its flagship model) roll up to one entity.
* **Scoring.** A deterministic Buzz Score from 0 to 100 is computed from four components, each capped at a fixed maximum:

  | Component | Max points | Initial weight rationale |
  | --- | --- | --- |
  | Volume (story count) | 30 | Breadth of attention; weighted highest because story count is the most stable, least gameable signal. |
  | Engagement (points + comments) | 30 | Depth of attention; equal to volume so a few heavily-discussed stories count as much as many quiet ones. |
  | Front page impact (stories ≥ points threshold) | 20 | Reach beyond the niche; capped lower because a single viral story should not dominate. |
  | Acceleration (growth vs. trailing average) | 20 | The breakout signal; capped lowest because it is the noisiest and history-dependent component. |

  Scores are normalized across entities on a log scale so a few viral stories do not dominate. These weights are explicitly **initial choices, not validated parameters**; the plan to validate them is to (a) hold them fixed through Phase 1 so the score series is internally comparable, then (b) tune them against the Phase 2 backtest, with "trustworthy" defined as weights whose resulting score correlates with the validation outcome better than uniform weighting. Until then the weights are documented as a parameterized opinion, not an instrument.

  Two normalization edge cases are specified up front. **Sparse entities:** because log normalization compresses large values but does not stabilize sparse distributions, an entity below a minimum activity floor (for example fewer than 3 stories in the window) is scored against an absolute floor rather than the cross-entity log scale, and flagged as low-confidence in the output so a slow-week score is not compared against a busy-week score as if they were equivalent. **Cold-start acceleration:** with no prior snapshot the acceleration component reads as a hard zero for every entity uniformly (not a variable per-entity distortion), so early runs are deterministically conservative and comparable to each other, and this is surfaced explicitly in the digest until enough history accumulates.
* **Velocity.** Each run reads the previous snapshot from Supabase Postgres and computes the change versus the trailing 14-day average, which is the part that actually flags a breakout.
* **Breakout thresholds (provisional).** An entity fires a breakout alert when **both** conditions hold in the same run: (a) its current Buzz Score is **≥ +40% above its trailing 14-day average**, and (b) its current absolute Buzz Score is **≥ 50/100**. The first condition catches acceleration; the second is a noise gate that prevents a sparse, low-confidence entity from triggering on a jump from 2 to 5 stories. As a separate, simpler tripwire, any entity whose score gains **≥ 25 absolute points day-over-day** also fires regardless of the percentage rule, to catch sudden spikes off a non-trivial base. These three numbers (`+40%`, `≥ 50`, `+25 pts`) are **provisional heuristics and will be wrong**: they are set now for the discipline of having a defined, testable rule, held fixed through Phase 1 so alert behavior is comparable, and recalibrated against accumulated data before Phase 3. Low-confidence (sub-floor) entities are excluded from breakout alerting entirely until they clear the activity floor. They are stored per-entity in the watchlist `breakout threshold` field so individual entities can be tuned without touching code.
* **Output.** The run snapshot is stored, and a ranked HTML email digest is sent, with an alert when an entity crosses a threshold.

The deterministic score is the foundation and is what the first month delivers. A free LLM narrative layer that explains why an entity is trending, with a theme and a reception tone, is added in the second and third months after the first piece works. "Free LLM" is currently a constraint, not a resolved choice, and is flagged as an **open design decision** for Phase 2: the specific model, its rate limits, whether it runs locally or via API, and how narrative quality is assessed are not yet fixed. The decision must confirm that the chosen free option is actually capable enough for reception-tone analysis on financial-adjacent content; "free" and "capable enough" may not be compatible, and the choice will be made before Phase 2 begins rather than assumed.

## Time constraint and scope

The work is phased across three months. In the first month the goal is not to build everything, so the scope is a smaller but complete version: the working core agent. By the end of the first month it will collect from Hacker News, normalize entities, compute the Buzz Score and velocity, store snapshots in Supabase, and send a simple daily ranked digest, verified end to end on a watchlist of 10 to 15 AI entities. 
The second and third months improve and extend that working version: a free LLM narrative and reception tone, comment level analysis, a Chart.js dashboard, a historical backfill, coordination layer integration, and — pulled forward to **early Phase 2** because it is what justifies the investment framing — a lightweight signal validation backtest. Building the smaller version first means there is a usable, testable deliverable early, rather than several half finished features.

**Phase 1 exit criteria.** Phase 1 ends on a deliverable, not a calendar date. It is complete when the workflow has run end to end without manual intervention for at least 10 consecutive daily runs over a two-week window, every watchlist entity produces a Buzz Score and velocity (with zero-hit and cold-start cases handled as specified rather than failing), at least two consecutive runs demonstrate a correctly computed non-zero velocity, and the stored snapshot, daily digest, and breakout alert are all verified against live data.

## Watchlist governance

The watchlist is not merely a configuration detail; it is the universe against which cross-entity log normalization occurs, so changes to it can contaminate longitudinal comparisons. It is therefore governed explicitly:

* **Selection criteria.** Entities are AI companies or products with a material public profile on Hacker News, prioritizing those with a public ticker so the signal can be joined to financial analysis; a small number of private comparables (for example leading model labs without tickers) may be included for context and are clearly marked as non-investable.
* **Static within a phase.** The watchlist is held fixed for the duration of Phase 1 so the score series is internally comparable. It is versioned (v1, v2, …); any change creates a new version rather than mutating the existing one.
* **Update protocol.** Additions and removals occur only at version boundaries. When the watchlist changes, the normalization baseline is treated as discontinuous: historical scores remain valid within their version but are not directly compared across a version change, and charts mark the boundary. This prevents a viral entity added mid-series from silently resetting every other entity's baseline.
* **Ownership.** A single named maintainer owns the watchlist file; changes are reviewed in the pull request that introduces the new version.

### Watchlist v1 composition

The initial universe is **13 entities**, chosen for material AI relevance to Mycroft's investment thesis and a meaningful Hacker News footprint. Public-ticker names are prioritized so the signal can be joined to financial analysis; three private model labs are included as non-investable context. Query terms are deliberately specific to suppress name ambiguity (the highest-risk failure mode): generic single words (for example "Meta", "Gemini", "Claude" alone) are avoided or qualified, and aliases roll up to one entity during normalization. Terms are matched against story titles/URLs and refined after Phase 1 noise review.

| # | Entity | Ticker | Query terms (OR-matched) | Aliases rolled up | Investable |
| --- | --- | --- | --- | --- | --- |
| 1 | NVIDIA | NVDA | `NVIDIA`, `CUDA`, `Blackwell GPU`, `H100`, `GB200` | NVIDIA Corp | Yes |
| 2 | Microsoft AI | MSFT | `Microsoft Copilot`, `Azure OpenAI`, `Microsoft AI` | Copilot, Azure AI | Yes |
| 3 | Alphabet / Google DeepMind | GOOGL | `Google DeepMind`, `Gemini model`, `Google AI`, `Vertex AI` | DeepMind, Gemini | Yes |
| 4 | Meta AI | META | `Meta AI`, `Llama model`, `Llama 3`, `Llama 4`, `PyTorch` | Llama, FAIR | Yes |
| 5 | Amazon AI | AMZN | `Amazon Bedrock`, `AWS Trainium`, `Amazon Q`, `SageMaker` | Bedrock, AWS AI | Yes |
| 6 | AMD | AMD | `AMD MI300`, `AMD Instinct`, `ROCm`, `AMD AI` | Instinct, ROCm | Yes |
| 7 | Broadcom | AVGO | `Broadcom AI`, `Broadcom custom silicon`, `Broadcom accelerator` | — | Yes |
| 8 | Oracle Cloud AI | ORCL | `Oracle Cloud Infrastructure AI`, `OCI GPU`, `Oracle AI` | OCI | Yes |
| 9 | Palantir | PLTR | `Palantir AIP`, `Palantir Foundry`, `Palantir AI` | AIP, Foundry | Yes |
| 10 | CoreWeave | CRWV | `CoreWeave`, `CoreWeave GPU cloud` | — | Yes |
| 11 | OpenAI | — | `OpenAI`, `ChatGPT`, `GPT-4`, `GPT-5`, `o1 model`, `Sora` | ChatGPT, GPT, Sora | No (private) |
| 12 | Anthropic | — | `Anthropic`, `Claude model`, `Claude Code`, `Claude API` | Claude | No (private) |
| 13 | Mistral AI | — | `Mistral AI`, `Mistral model`, `Mixtral`, `Le Chat` | Mixtral | No (private) |

This list is **v1** and frozen for the duration of Phase 1 per the static-within-a-phase rule above. The named maintainer for v1 is the project owner (`mali.om@northeastern.edu`); query-term ambiguity findings from Phase 1 feed the v2 revision.

## Implementation approach

The first month builds a single n8n workflow that runs end to end, with no LLM and no dashboard. The nodes are assembled in this order:

* **Schedule Trigger.** Fires the workflow on a daily cadence.
* **Watchlist (Set node).** Holds the configurable list of 10 to 15 AI entities, each with its query terms, optional ticker, and a breakout threshold.
* **Loop (Split In Batches).** Iterates over the watchlist so each entity is queried independently.
* **HTTP Request.** Calls the Hacker News Search API (Algolia) for each entity over the trailing 14-day window, with no key required.
* **Aggregate and score (Code node).** Parses the hits, dedupes by `objectID`, normalizes company and product names, computes the four Buzz Score components, and outputs a  deterministic Buzz Score from 0 to 100.
* **Read previous snapshot (Postgres).** Loads the prior run from Supabase so the current run can be compared against it.
* **Compute velocity (Code node).** Calculates the change versus the trailing average and flags any entity that crosses its threshold.
* **Store snapshot (Postgres).** Writes the run, the ranked leaderboard, and the raw metrics back to Supabase.
* **Digest and alert (Code node and Send Email).** Builds a simple ranked daily email of the top movers and sends a breakout alert when a threshold is crossed.

**Email delivery mechanism (Phase 1).** Delivery uses n8n's native **Send Email (SMTP)** node configured against **SendGrid SMTP** (`smtp.sendgrid.net`, port 587, STARTTLS), chosen because its free tier (100 emails/day) comfortably covers one daily digest plus occasional breakout alerts, it requires no self-hosted mail server, and its SMTP relay drops into the existing node without a custom integration. Credentials are stored as an n8n SMTP credential (username `apikey`, password = a SendGrid API key scoped to mail-send only), never inline in the workflow JSON, and the API key is held as an environment-level secret. The **from** address is a verified sender on the project domain (`buzz-tracker@<project-domain>`, falling back to a SendGrid single-sender verified address during setup); the **to** address for Phase 1 is the project maintainer (`mali.om@northeastern.edu`). Both digest and the distinct maintainer/pipeline-failure alert route through the same SMTP credential but use different subject prefixes (`[HN Buzz]` vs `[HN Buzz ALERT]`) so they are filterable. If SendGrid sender verification is not complete at build time, Gmail SMTP with an app password is the documented fallback for the single Phase 1 recipient.

Error handling wraps the request and storage steps so that a rate limit, an empty response, or a first run with no prior snapshot degrades gracefully rather than failing the whole run. Rather than leaving "graceful degradation" undefined, the first month makes three handling decisions explicit (the deeper design is a flagged open item, but the defaults are fixed now):

* **Zero results for an entity.** Treated as a valid data point, not an error: stored as a real zero (not null), which yields a floored low-confidence score rather than suppressing or skipping the entity.
* **Partial run failure.** If a run fails after only some entities are updated, the run is marked incomplete and velocity is computed only for entities present in both the current and prior *complete* snapshots; partial snapshots are not used as the baseline for the next run, so a half-finished run cannot corrupt the velocity series.
* **Pipeline-failure alerting.** Operational failure (API down, storage write failure, response-shape change) raises a separate maintainer alert, distinct from the entity breakout alert, so a silent pipeline outage is never mistaken for a quiet news day.

## Expected output

By the end of the first month the workflow produces three concrete artifacts on every run:

* **A stored snapshot.** One row per run in the `hn_buzz_runs` table, holding the ranked leaderboard, per entity metrics, and the run timestamp, which builds up the history that later velocity depends on.
* **A daily ranked digest (human-readable).** A simple HTML email, addressed to a project maintainer as the Phase 1 recipient, listing the watchlist entities ordered by Buzz Score, each with its score from 0 to 100, its velocity versus the previous run, and its top story title and link. This output is for human review only.
* **A machine-ingestible signal (separate output).** The same run also emits a structured JSON payload — the stored snapshot's leaderboard, scores, velocity, and confidence flags — as the canonical output for the Mycroft coordination layer. The human digest and the machine signal are deliberately distinct artifacts: HTML email is the wrong format for agent ingestion, so the coordination layer consumes the JSON (via the stored snapshot in Phase 1, and a pull endpoint in the later coordination-integration phase), never the email.
* **A breakout alert.** A notification fired only when an entity crosses its configured threshold, so the digest stays low noise.


## Where it might break or struggle

* **Name ambiguity.** Generic query terms pull in unrelated stories (for example a common word that is also a product name). The normalization step needs careful query terms and filtering, and this is the most likely source of noisy scores.
* **Thin or empty windows.** Smaller or private entities may produce few or zero hits in a window, which makes the score jumpy. The agent has to treat zero hit entities as a valid baseline rather than an error.
* **Cold start velocity.** Velocity needs a history. The first runs have no prior snapshot, so the acceleration component reads as zero until enough runs accumulate. A historical backfill in a later month is the eventual fix, but in the first month the early numbers will be conservative.
* **Score calibration.** The weights and the points threshold are judgment calls. A single viral front page story can swing a score, so the log normalization and thresholds will need tuning against real data before the numbers feel trustworthy.
* **Buzz is not direction.** A high score means attention, not good news. Heavy discussion around an outage looks similar in volume to a celebrated launch. Distinguishing the two is exactly what the reception tone layer added in a later month is for, so in the first month the score should be read as attention only.
* **Source limits.** The pipeline depends on one public API. If it rate limits or changes its response shape, collection stops, so the run needs basic error handling and a graceful failure.

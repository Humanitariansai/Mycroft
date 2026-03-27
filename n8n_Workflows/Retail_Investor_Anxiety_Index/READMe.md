# Retail Investor Anxiety Index

A behavioral intelligence dashboard that analyzes Reddit crowd sentiment across r/wallstreetbets, r/investing, and r/stocks to produce a multi-signal view of retail investor psychology — going far beyond simple fear/greed scoring.

---

## Project Overview

Traditional sentiment tools reduce investor mood to a single number. This project takes a different approach — it treats Reddit as a behavioral data source and extracts six distinct signals that together paint a picture of where retail investor psychology currently sits, what narratives are accelerating, which assets are drawing coordinated attention, and whether the crowd is acting with conviction or uncertainty.

The workflow runs automatically every 6 hours using n8n, processes up to 75 Reddit posts per run, applies a hybrid scoring pipeline, and outputs a live dashboard via Grafana.

---

## Architecture

```
Reddit API (r/wallstreetbets, r/investing, r/stocks)
        ↓
n8n Workflow (automated pipeline)
        ↓
Layer 1 — Hybrid Sentiment Scoring
        ↓
Layer 2 — Behavioral Signal Extraction (4 Claude API calls)
        ↓
Signal Aggregator + Quickchart URL Generation
        ↓
Grafana Dashboard (live, auto-refreshing)
```

---

## Tech Stack

| Component | Tool |
|---|---|
| Workflow automation | n8n (local) |
| Data source | Reddit public JSON API |
| LLM scoring | Claude Sonnet (Anthropic API) |
| Chart generation | Quickchart.io |
| Dashboard | Grafana (localhost:3000) |
| Storage | n8n static data + local JSON files |

---

## Layer 1 — Hybrid Sentiment Scoring

Layer 1 is the data ingestion and scoring foundation. Every post passes through a two-stage pipeline before any Claude API call is made.

### Stage 1A — Raw Merge and Structural Clean
All three subreddit feeds are fetched in parallel and merged into a single flat array. This stage extracts only the fields needed for analysis (id, title, subreddit, score, upvoteRatio, numComments) and drops duplicates and empty posts.

### Stage 1B — Linguistic and Relevance Filter
Each post title is cleaned for analysis. This stage lowercases text, strips URLs, emojis, and special characters, extracts ticker symbols ($AAPL format and standalone uppercase) into a separate field, removes posts under 4 words, and flags posts that are questions (isQuestion). The cleaned title is stored separately as cleanTitle while the original title is preserved.

### Stage 2 — Keyword Pre-Scorer
A weighted keyword scoring system runs against every cleanTitle before any Claude API call. Posts are scored 0–100 based on fear and greed keyword hits:

**Fear keywords (high weight):** crash, collapse, margin call, panic, bankrupt, recession, going to lose, lose it all, losing everything, worst quarter, obliterated, devastating, rekt, wiped out, capitulation

**Fear keywords (mid weight):** dump, sell, down, loss, scared, bubble, warn, fear, correction, pullback, volatile, selloff, bleeding, tariff, war, conflict, crisis, inflation, layoffs, bearish, bear, puts

**Greed keywords (high weight):** moon, all in, yolo, lambo, tendies, to the moon, diamond hands, short squeeze, ape

**Greed keywords (mid weight):** buy, bull, pump, gain, profit, green, rally, bounce, buy the dip, bullish, calls, upside, growth, opportunity

**Neutral amplifiers (1.2x multiplier):** huge, massive, insane, breaking, historic, unprecedented, extreme, critical, urgent, serious

Each post is tagged with a zone:
- `CLEAR_FEAR` — score 61–100
- `AMBIGUOUS` — score 40–60
- `CLEAR_GREED` — score 0–39

### Stage 3 — Claude Anxiety Scoring (Layer 1 Claude call)
Posts in the AMBIGUOUS zone are escalated to Claude for precise 0–100 scoring. Claude is instructed to be decisive and avoid clustering around 50, using explicit rules:
- Large losses → score 75+
- Market crashes or worst-ever language → score 70+
- Strong bullish conviction → score 25 or below
- Neutral factual questions → score 45–55
- War, geopolitical risk, economic crisis → score 65+

Claude scores are merged back, replacing keyword scores for ambiguous posts only. Clear fear and clear greed posts retain their keyword scores. The final per-post field is `finalScore`.

**Output of Layer 1:**
- `anxietyScore` — average finalScore across all posts (0–100)
- `subredditScores` — per-subreddit averages (wallstreetbets, investing, stocks)
- `top3FearfulPosts` — top 3 posts by finalScore with title and score

---

## Layer 2 — Behavioral Signal Extraction

Rather than stopping at a single fear/greed number, Layer 2 extracts four deeper behavioral signals from the same Reddit data using dedicated Claude API calls. Narrative Velocity tracks how fast emerging topics are rising in conversation — identifying what the crowd is suddenly fixating on before it becomes mainstream news. Herd Detection identifies when the same ticker or theme appears simultaneously across all three subreddits, flagging coordinated crowd behavior. Conviction vs Uncertainty measures the ratio of assertive, decisive language against hedging and questioning language — revealing whether investors are acting with confidence or doubt. Finally, Crowd Cycle Stage classifies the overall narrative into one of six psychological stages (Euphoria, Complacency, Anxiety, Denial, Panic, Hope), giving a human-readable label to where retail investor psychology currently sits on the market emotion cycle.

### Signal 1 — Narrative Velocity
**What it measures:** How fast a topic is rising in conversation compared to the previous run.

**How it works:** Claude receives all post titles plus the top topics from the previous run stored in anxiety_log.json. It extracts the top 10 current topics, counts their frequency, and compares to previous counts to produce a velocityScore (0–100) representing rate of change — not raw frequency.

**Why it matters:** A topic with a velocityScore of 85 is not necessarily the most-discussed topic — it is the fastest-accelerating one. This catches emerging narratives before they peak.

**Output:** `[{ topic, currentCount, previousCount, velocityScore }]`

### Signal 2 — Herd Detection
**What it measures:** Tickers or themes appearing simultaneously across all three subreddits.

**How it works:** Claude receives post titles grouped by subreddit and identifies any stock, company name, ETF, or macro theme that appears in two or more communities in the same run. It counts per-subreddit mentions and flags `isHerd: true` for cross-subreddit overlap.

**Why it matters:** When the same topic spikes across r/wallstreetbets, r/investing, and r/stocks simultaneously, it signals coordinated crowd attention — a behavioral pattern that often precedes significant price action or narrative shifts.

**Output:** `[{ ticker, mentions: { wallstreetbets, investing, stocks }, isHerd }]`

### Signal 3 — Conviction vs Uncertainty
**What it measures:** The ratio of assertive, decisive language versus hedging and uncertain language.

**How it works:** Claude analyzes all post titles with their isQuestion flags. It scores the batch for assertive language (bold claims, definitive statements, strong calls to action) versus uncertain language (questions, hedging, maybe/should I/not sure). The two scores sum to 100.

**Why it matters:** A high conviction score with high anxiety means investors are fearful but decisive — they are acting on their fear. A high uncertainty score with high anxiety means investors are paralyzed — they are worried but not sure what to do. These are meaningfully different crowd states.

**Output:** `{ convictionScore, uncertaintyScore, ratio, dominantPostTitles: [top 3] }`

### Signal 4 — Crowd Cycle Stage
**What it measures:** The current psychological stage of the retail investor crowd.

**How it works:** Claude receives all post titles as an aggregated batch and classifies the overall narrative into one of six stages based on the dominant language patterns:

| Stage | Characteristics |
|---|---|
| Euphoria | Extreme optimism, FOMO, everyone is winning |
| Complacency | Calm, passive, low urgency |
| Anxiety | Worried but not panicking, lots of questions |
| Denial | Ignoring bad signs, rationalizing losses |
| Panic | Extreme fear, selling everything, catastrophic language |
| Hope | Cautious optimism after a down period |

Claude returns the stage, a confidence score (0–1), and a two-sentence reasoning grounded in specific language patterns observed in the posts.

**Why it matters:** The cycle stage gives a single human-readable label to crowd psychology that contextualizes all other signals. An anxietyScore of 65 means different things depending on whether the crowd is in Denial (hasn't accepted it yet) or Hope (recovering from worse).

**Output:** `{ stage, confidence, reasoning }`

---

## Data Storage

Each workflow run appends an entry to `anxiety_log.json`:

```json
{
  "date": "2026-03-27",
  "timestamp": "2026-03-27T14:00:00Z",
  "postCount": 71,
  "anxietyScore": 53,
  "subredditScores": { "wallstreetbets": 53, "investing": 51, "stocks": 55 },
  "top3FearfulPosts": [{ "title": "...", "score": 90 }],
  "narrativeVelocity": [{ "topic": "...", "currentCount": 8, "previousCount": 1, "velocityScore": 85 }],
  "herdDetection": [{ "ticker": "AI", "mentions": { "wallstreetbets": 2, "investing": 1, "stocks": 2 }, "isHerd": true }],
  "conviction": { "convictionScore": 75, "uncertaintyScore": 25, "ratio": 3.0 },
  "cycleStage": { "stage": "Anxiety", "confidence": 0.85, "reasoning": "..." }
}
```

The log retains the last 7 days of entries. Older entries are pruned on each run.

---

## Frontend Dashboard (Grafana)

The dashboard is built in Grafana and receives a fully configured dashboard JSON pushed by n8n after every pipeline run. No manual panel configuration is required — n8n programmatically creates and updates the dashboard via the Grafana API.

### Panels

| Panel | Type | Signal |
|---|---|---|
| Anxiety Score | Stat (color-coded) | Layer 1 — anxietyScore |
| Subreddit Breakdown | Bar gauge | Layer 1 — subredditScores |
| Crowd Cycle Stage | Stat | Layer 2 — cycleStage |
| Narrative Velocity | Horizontal bar chart | Layer 2 — narrativeVelocity |
| Herd Detection | Grouped bar chart | Layer 2 — herdDetection |
| Conviction vs Uncertainty | Pie chart | Layer 2 — conviction |
| Top Fearful Posts | Table | Layer 1 — top3FearfulPosts |
| Cycle Stage Reasoning | Text (markdown) | Layer 2 — cycleReasoning |

### Color Coding
- Anxiety score 0–33 → green (Greed)
- Anxiety score 34–66 → yellow (Neutral)
- Anxiety score 67–100 → red (Fear)

---

## Setup Instructions

### Prerequisites
- n8n installed (`npx n8n`)
- Anthropic API key
- Grafana installed (`brew install grafana`)

### Running the Workflow
```bash
# Start n8n
npx n8n

# Start Grafana
brew services start grafana
```

1. Import `workflow.json` into n8n via Settings → Import Workflow
2. Add Anthropic API key as n8n credential (Header Auth, key: x-api-key)
3. Add Grafana API key as n8n credential
4. Click Execute Workflow to run manually
5. Open http://localhost:3000 to view dashboard

### Automated Runs
The workflow runs automatically every 6 hours once activated. Toggle the Active switch in n8n to enable.

---

## File Structure

```
Retail_Investor_Anxiety_Index/
├── workflow.json        # n8n workflow (import into n8n)
├── index.html           # Standalone HTML dashboard (optional)
├── anxiety_log.json     # Auto-generated — 7-day rolling log
└── output.json          # Auto-generated — latest run output
```

---

## Known Limitations

- Anxiety score tends toward neutral (50) on low-news days — this is accurate but can feel flat
- Herd detection works best when tickers are mentioned explicitly — implicit references may be missed
- Conviction score can be stable across runs when post language patterns are similar
- All data is sourced from public Reddit posts — not representative of all retail investors
- 7-day rolling window means the line chart requires multiple runs to show meaningful trends

---

## Author
Sahiti Nallamolu — Humanitarians Project
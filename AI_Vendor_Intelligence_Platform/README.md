# AI Vendor Intelligence Platform

> Automated competitive intelligence briefs on 50 AI companies, refreshed daily and delivered via API.

## Architecture Overview

```
collector/          — Data ingestion layer
  edgar_collector   — SEC filings (10-K, 10-Q, 8-K) for public companies
  github_collector  — GitHub activity: stars, commits, contributors, releases
  arxiv_collector   — Research paper indexing by company affiliation
  news_collector    — News articles and press releases via RSS/scraping
  db.py             — Shared PostgreSQL helpers (psycopg2)

agents/             — LLM analysis layer (Groq-backed, Langfuse-traced)
  financial/        — Revenue signals, funding rounds, burn indicators
  technology/       — Model releases, benchmark results, OSS activity
  news/             — Sentiment, key events, reputational signals
  personnel/        — Executive hires/departures, headcount trends
  competitive/      — Positioning shifts, partnership announcements
  supervisor/       — Orchestrates sub-agents, merges into final brief

infrastructure/     — Terraform (AWS Lambda + IAM)
api/                — Lambda handler + brief formatter
frontend/           — Single-page brief viewer
evaluation/         — Labeled ground-truth briefs + eval runner
prompts/            — Shared prompt fragments
```

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd AI-Vendor-Intelligence-Platform

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and GROQ_API_KEY

# 3. Install collector dependencies
pip install -r collector/requirements.txt

# 4. (Optional) Provision infrastructure
cd infrastructure
terraform init
terraform apply
```

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GITHUB_TOKEN` | GitHub PAT for higher rate limits |
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `LANGFUSE_PUBLIC_KEY` | Langfuse observability (public) |
| `LANGFUSE_SECRET_KEY` | Langfuse observability (secret) |
| `LANGFUSE_HOST` | Langfuse host (default: cloud) |
| `NEO4J_URI` | Neo4j URI for graph relationships |
| `NEO4J_USER` | Neo4j username |
| `NEO4J_PASSWORD` | Neo4j password |
| `AWS_REGION` | AWS region for Lambda deployment |

## Week 1 Status

- [x] Project scaffold created (50-company seed list, all collector stubs, agent directory structure)
- [ ] `edgar_collector.py` — fetch and parse 10-K/10-Q filings
- [ ] `github_collector.py` — pull repo metrics via PyGithub
- [ ] `arxiv_collector.py` — index papers by company affiliation
- [ ] `news_collector.py` — ingest RSS feeds and normalise articles
- [ ] `db.py` — schema migrations and upsert helpers
- [ ] Agent instructions and schemas (financial, technology, news, personnel, competitive)
- [ ] Supervisor orchestration logic
- [ ] API handler and brief formatter
- [ ] Evaluation baseline on labeled briefs

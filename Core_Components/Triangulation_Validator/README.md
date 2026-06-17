# Triangulation Validator

> **Consensus-based signal validation using multi-agent triangulation heuristic**

A component that validates signals from multiple Mycroft agents using the triangulation heuristic from the Computational Finance textbook. When 2+ agents agree on a signal about an AI company, confidence increases; when they disagree, it flags for manual review.

## The Problem

Mycroft agents independently analyze AI companies:
- **Talent Flow Agent**: "OpenAI strong" (confidence: 85%)
- **Patent Agent**: "OpenAI weak" (confidence: 60%)
- **News Agent**: "OpenAI strong" (confidence: 90%)

Which signal is right? The Triangulation Validator answers: **"2/3 agents agree it's strong; overall confidence: 87%"**

## How It Works

### The Math (Triangulation Heuristic)

From *Computational Finance with Excel, Python, and LLMs*:

If each agent is ~85% accurate independently:
- **All 3 agree** → Combined confidence: ~89% (up from 85%)
- **2/3 agree** → Combined confidence: ~78% (conflict detected)
- **1/3 agrees** → Combined confidence: ~60% (weak signal)

**Result:** Better decisions through consensus validation.

## Architecture

```
Talent Agent      Patent Agent      News Agent
    (LLM)            (LLM)            (LLM)
      │                │                │
      └────────────────┼────────────────┘
                       │
              ┌────────▼────────┐
              │ Signal Aggregator│
              └────────┬────────┘
                       │
              ┌────────▼────────────┐
              │ Triangulation Engine│
              │  (consensus logic)  │
              └────────┬────────────┘
                       │
              ┌────────▼──────────────┐
              │ Triangulation Result  │
              │ (confidence + flag)   │
              └──────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Spring Boot 3.2 + Java 21 |
| **Database** | PostgreSQL |
| **Frontend** | React + Vite + Tailwind |
| **Testing** | JUnit 5 + Mockito |
| **Deployment** | Docker |

## API Overview

```
POST   /api/v1/triangulation/analyze/{company}
       → Trigger analysis for a company

GET    /api/v1/triangulation/{company}/latest
       → Get latest triangulation result

GET    /api/v1/triangulation/{company}/history?days=30
       → Historical trend (detect erosion)

GET    /api/v1/triangulation/compare?companies=OpenAI,Anthropic
       → Compare multiple companies

GET    /api/v1/health
       → Service health
```

## Database Schema

### `signals` Table
```sql
CREATE TABLE signals (
  id BIGSERIAL PRIMARY KEY,
  company_name VARCHAR(255) NOT NULL,
  agent_name VARCHAR(255) NOT NULL,      -- "Talent Flow Agent", "Patent Agent", etc.
  signal_text TEXT NOT NULL,              -- "Hired 3 senior researchers"
  confidence INT CHECK (confidence >= 0 AND confidence <= 100),
  signal_type VARCHAR(50),                -- "talent", "patent", "news", "market", etc.
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_company_date (company_name, created_at)
);
```

### `triangulation_results` Table
```sql
CREATE TABLE triangulation_results (
  id BIGSERIAL PRIMARY KEY,
  company_name VARCHAR(255) NOT NULL,
  consensus_level VARCHAR(50),            -- "HIGH", "MEDIUM", "LOW"
  agents_agreeing INT,                    -- 3/4, 2/3, etc.
  total_agents_reporting INT,
  average_confidence INT,
  triangulated_confidence INT,            -- Boosted confidence
  signal_direction VARCHAR(20),           -- "POSITIVE", "NEGATIVE", "NEUTRAL"
  recommendation VARCHAR(50),             -- "TRUST_SIGNAL", "CONFLICTING", "WEAK"
  risk_level VARCHAR(20),                 -- "LOW", "MEDIUM", "HIGH"
  signal_summary TEXT,                    -- JSON array of individual signals
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_company_latest (company_name, created_at DESC)
);
```

### `signal_agreements` Table (Audit Log)
```sql
CREATE TABLE signal_agreements (
  id BIGSERIAL PRIMARY KEY,
  company_name VARCHAR(255) NOT NULL,
  signals_analyzed INT,
  agreement_count INT,
  conflict_flags INT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Installation

```bash
# 1. Create directory
mkdir -p Core_Components/Triangulation_Validator
cd Core_Components/Triangulation_Validator

# 2. Backend setup
cd backend
./mvnw clean install

# 3. Set environment
cp .env.example .env
# Edit .env with DATABASE_URL, etc.

# 4. Start backend
./mvnw spring-boot:run

# 5. Frontend setup (separate terminal)
cd ../frontend
npm install
npm run dev
```

**Backend:** http://localhost:8080  
**Frontend:** http://localhost:5173  
**API Docs:** http://localhost:8080/swagger-ui.html

## Development Workflow

```
Week 1:
  Day 1-2: Setup & Database Schema
  Day 3-4: Core Triangulation Algorithm
  Day 5: Signal Fetching & Integration

Week 2:
  Day 6-7: REST API Endpoints
  Day 8-9: React Dashboard
  Day 10: Testing & Docker
  Day 11-12: Documentation & Integration
```

## Current Status

- [ ] Week 1: Backend Foundation
  - [ ] Day 1-2: Project setup + schema
  - [ ] Day 3-4: Algorithm + unit tests
  - [ ] Day 5: Signal integration
- [ ] Week 2: API & Frontend
  - [ ] Day 6-7: REST endpoints
  - [ ] Day 8-9: React dashboard
  - [ ] Day 10: Testing
  - [ ] Day 11-12: Docs

## Integration with Mycroft

This component:
- ✅ Consumes signals from other agents (Talent Flow, Patent, News, etc.)
- ✅ Outputs consensus validation for Portfolio & Risk Management components
- ✅ Feeds into Investment Decision layer
- ✅ Provides audit trail (traceable reasoning)

## References

- **Textbook**: *Computational Finance with Excel, Python, and LLMs* — Chapter 19: Advanced LLM Applications
- **Triangulation Math**: Introduction.md (trilateral approach + accuracy improvement)
- **Mycroft Framework**: README.md (orchestration layer philosophy)

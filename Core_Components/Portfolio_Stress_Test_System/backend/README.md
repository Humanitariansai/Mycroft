# Portfolio Stress Testing System — Layers 1 & 2

FastAPI + Streamlit system that analyzes portfolio risk through two analytical lenses: regime-dependent diversification and historical crash simulation.

---

## Layers Overview

- **Layer 1** ✓ — Regime-Dependent Diversification
- **Layer 2** ✓ — Historical Crash Simulation
- **Layer 3** — Factor Exposure Decomposition *(planned)*
- **Layer 4** — Regime-Specific Performance Analysis *(planned)*

---

## Installation

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Start the API (serves both layers)
python -m app.main

# Start the Streamlit UI (separate terminal)
streamlit run streamlit_app.py
```

- API: `http://localhost:8001`
- Streamlit: `http://localhost:8501`
- Swagger docs: `http://localhost:8001/docs`

---

## Layer 1: Regime-Dependent Diversification

Analyzes how portfolio correlation structure changes across three market volatility regimes and quantifies how much diversification degrades under stress.

### Regimes
- **Low VIX (<15)**: Calm markets
- **Medium VIX (15–25)**: Normal volatility
- **High VIX (>25)**: Stress periods

### How It Works

**1. Data Collection** — `app/services/data_fetcher.py`
- Fetches historical prices from Yahoo Finance via `yfinance`
- Fetches VIX data for the same period
- Applies 5-day rolling average to VIX to reduce noise

**2. Regime Classification** — `app/services/regime_classifier.py`
- Classifies each trading day into low/medium/high regime
- Filters out short regime periods (< 20 days) to avoid single-day spikes

**3. Returns Calculation** — `app/services/returns_calculator.py`
- Converts prices to log returns: `r_t = ln(P_t / P_{t-1})`

**4. Correlation Analysis** — `app/services/correlation_analyzer.py`
- Calculates Pearson correlation matrix per regime
- Strips timezone info from both indexes before alignment to prevent pandas misalignment errors
- Metrics per regime:
  - Average pairwise correlation (portfolio-weighted)
  - Max/min correlation
  - Effective number of assets: `N_eff = 1 / Σ(w_i × w_j × ρ_ij)`

**5. Risk Analysis** — `app/services/risk_analyzer.py`
- Compares low vs high VIX metrics to calculate degradation
- Risk flags: `SEVERE_CORRELATION_SPIKE`, `MAJOR_DIVERSIFICATION_LOSS`, `EXTREME_STRESS_CORRELATION`, `ILLUSION_OF_DIVERSIFICATION`

**6. Visualization** — `app/services/visualization.py`
- Side-by-side correlation heatmaps for each regime
- Degradation bar chart
- Returns base64-encoded PNG images

### API

**Endpoint:** `POST /api/v1/analyze`

```bash
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [
      {"ticker": "AAPL", "shares": 100, "weight": 0.4},
      {"ticker": "MSFT", "shares": 75,  "weight": 0.3},
      {"ticker": "GOOGL","shares": 50,  "weight": 0.3}
    ],
    "params": {
      "lookback_days": 756,
      "vix_low_threshold": 15.0,
      "vix_high_threshold": 25.0
    }
  }'
```

**Response includes:** correlation metrics per regime, degradation analysis, risk flags, recommendations, base64 visualizations.

### Example Output

```json
{
  "regime_metrics": {
    "low_vix":  { "avg_pairwise_correlation": 0.45, "effective_n_assets": 2.8 },
    "high_vix": { "avg_pairwise_correlation": 0.78, "effective_n_assets": 1.6 }
  },
  "degradation_analysis": {
    "avg_corr_pct_increase": 73.3,
    "eff_assets_pct_decrease": 42.9
  },
  "risk_flags": ["SEVERE_CORRELATION_SPIKE"]
}
```

---

## Layer 2: Historical Crash Simulation

Time-travels current portfolio holdings through past market crashes to reveal structural vulnerabilities before they appear in live performance.

### Key Insight
A portfolio that held up "relatively well" means it tracked the crash — not that it avoided loss. Flags fire on both **relative** underperformance vs benchmark and **absolute** drawdown severity.

### Predefined Crash Periods

| Key | Name | Period | Benchmark | Context |
|---|---|---|---|---|
| `covid_2020` | COVID Crash | Feb 19 – Mar 23, 2020 | SPY | S&P fell ~34% in 33 days |
| `tech_selloff_2022` | Tech Selloff 2022 | Jan 3 – Oct 12, 2022 | QQQ | NASDAQ fell ~33% over 9 months |
| `q4_selloff_2018` | Q4 Selloff 2018 | Sep 20 – Dec 24, 2018 | SPY | Fed tightening + trade war fears |
| `flash_crash_2015` | Flash Crash 2015 | Aug 1 – Aug 24, 2015 | SPY | China slowdown, S&P fell ~12% |

Custom date ranges are also supported via the UI or API.

### How It Works

**1. Data Fetching** — `app/services/data_fetcher.py`
- Fetches crash window prices with a 5-day pre-period buffer (for day-1 return calculation)
- Fetches up to 2 years of post-crash data for recovery measurement

**2. Simulation** — `app/services/crash_simulator.py`
- Computes portfolio daily log returns, weighted by position sizes
- Calculates cumulative return: `exp(Σ log_returns) - 1`
- Computes drawdown series: `(wealth - running_max) / running_max`
- Measures recovery: first day post-crash where portfolio recoups full loss
- Non-fatal: individual crash periods are skipped (with a warning) if data is unavailable, rather than failing the whole request

**3. Loss Attribution** — `app/services/loss_analyzer.py`
- Decomposes portfolio loss by holding: `contribution_i = weight_i × return_i`
- Calculates each holding's share of total portfolio loss
- Generates per-crash and cross-crash risk flags

**4. Visualization** — `app/services/crash_visualization.py`
- **Drawdown Paths**: portfolio vs benchmark drawdown curves per crash
- **Loss Attribution**: horizontal bar chart of per-holding contributions
- **Summary Heatmap**: holdings × crashes matrix showing return (%) per cell

### Risk Flags

| Flag | Condition |
|---|---|
| `SEVERE_DRAWDOWN` | Max drawdown < -20% |
| `SIGNIFICANT_UNDERPERFORMANCE` | Portfolio > 5% worse than benchmark |
| `SLOW_RECOVERY` | Recovery took > 120 trading days |
| `NOT_YET_RECOVERED` | Not recovered within 2-year observation window |
| `CONCENTRATED_LOSS_DRIVER:<TICKER>` | Single holding drove > 15% of total loss |
| `CONSISTENTLY_SEVERE_DRAWDOWNS` | Severe drawdown in 2+ crashes |
| `CONSISTENT_UNDERPERFORMANCE_VS_BENCHMARK` | Underperformed benchmark in 2+ crashes |
| `REPEAT_LOSS_CONCENTRATION` | Same ticker was a concentrated driver in 2+ crashes |

### API

**Endpoint:** `POST /api/v1/crash-simulation`

```bash
curl -X POST "http://localhost:8001/api/v1/crash-simulation" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [
      {"ticker": "AAPL", "shares": 100, "weight": 0.25},
      {"ticker": "MSFT", "shares": 75,  "weight": 0.25},
      {"ticker": "GOOGL","shares": 50,  "weight": 0.20},
      {"ticker": "TSLA", "shares": 30,  "weight": 0.15},
      {"ticker": "NVDA", "shares": 20,  "weight": 0.15}
    ],
    "selected_crashes": ["covid_2020", "tech_selloff_2022"],
    "custom_crash": {
      "key": "svb_2023",
      "name": "SVB Crisis",
      "start": "2023-03-01",
      "end": "2023-05-04",
      "benchmark_ticker": "SPY",
      "description": "Regional banking crisis triggered by SVB collapse"
    }
  }'
```

- `selected_crashes`: list of predefined keys to run; omit or pass `null` to run all four
- `custom_crash`: optional additional window appended to the selected set

**Response includes:** per-crash metrics, drawdown series, loss drivers, recovery days, risk flags, cross-crash summary, recommendations, base64 visualizations.

---
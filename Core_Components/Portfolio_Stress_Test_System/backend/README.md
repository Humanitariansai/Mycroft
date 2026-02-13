# Portfolio Stress Testing - Layer 1 Backend

FastAPI service that analyzes how portfolio diversification changes across market volatility regimes.

## What It Does

Analyzes portfolio correlation structure in three different market conditions:
- **Low VIX (<15)**: Calm markets
- **Medium VIX (15-25)**: Normal volatility  
- **High VIX (>25)**: Stress periods

The key insight: portfolios that look diversified in calm markets often behave like a single concentrated bet during stress.

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
python -m app.main
```

Service runs on `http://localhost:8001`

## How It Works

### 1. Data Collection
**DataFetcher** (`app/services/data_fetcher.py`)
- Fetches historical prices from Yahoo Finance using `yfinance`
- Gets VIX data for the same period
- Applies 5-day rolling average to VIX to reduce noise

### 2. Regime Classification
**RegimeClassifier** (`app/services/regime_classifier.py`)
- Takes VIX data and classifies each trading day into low/medium/high regime
- Filters out short regime periods (< 20 days) to avoid single-day spikes
- Returns mapping of date → regime label

### 3. Returns Calculation
**ReturnsCalculator** (`app/services/returns_calculator.py`)
- Converts prices to log returns: `r_t = ln(P_t / P_{t-1})`
- Creates DataFrame with returns for all tickers

### 4. Correlation Analysis
**CorrelationAnalyzer** (`app/services/correlation_analyzer.py`)
- Filters returns by regime (low/medium/high VIX periods)
- Calculates Pearson correlation matrix for each regime separately
- Computes three key metrics per regime:
  - **Average pairwise correlation**: Portfolio-weighted mean of all correlations
  - **Max correlation**: Highest correlation between any two holdings
  - **Effective number of assets**: `N_eff = 1 / Σ(w_i × w_j × ρ_ij)` - accounts for both weights and correlations

### 5. Risk Analysis
**RiskAnalyzer** (`app/services/risk_analyzer.py`)
- Compares low VIX vs high VIX metrics to calculate degradation:
  - How much does correlation increase?
  - How much does effective diversification decrease?
- Generates risk flags based on thresholds:
  - `SEVERE_CORRELATION_SPIKE`: >50% correlation increase
  - `MAJOR_DIVERSIFICATION_LOSS`: >40% effective asset decrease
  - `EXTREME_STRESS_CORRELATION`: Max correlation >0.85 during stress
  - `ILLUSION_OF_DIVERSIFICATION`: Effective assets <3 despite many holdings
- Creates natural language recommendations

### 6. Visualization
**Visualizer** (`app/services/visualization.py`)
- Generates correlation heatmaps (3 side-by-side for each regime)
- Creates degradation bar chart showing percentage changes
- Returns base64-encoded PNG images

## API Usage

**Main Endpoint:** `POST /api/v1/analyze`

```bash
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio": [
      {"ticker": "AAPL", "shares": 100, "weight": 0.4},
      {"ticker": "MSFT", "shares": 75, "weight": 0.3},
      {"ticker": "GOOGL", "shares": 50, "weight": 0.3}
    ],
    "params": {
      "lookback_days": 756,
      "vix_low_threshold": 15.0,
      "vix_high_threshold": 25.0
    }
  }'
```

**Response includes:**
- Correlation metrics for each regime
- Degradation analysis (how much diversification breaks down)
- Risk flags
- Recommendations
- Base64-encoded visualizations

## Configuration

Edit `.env` file to customize defaults:

```bash
DEFAULT_LOOKBACK_DAYS=756        # 3 years historical data
DEFAULT_ROLLING_WINDOW=252       # 1 year rolling window
VIX_LOW_THRESHOLD=15.0
VIX_HIGH_THRESHOLD=25.0
MIN_REGIME_DAYS=20               # Filter out short regime periods
```

## Example Output

```json
{
  "regime_metrics": {
    "low_vix": {
      "avg_pairwise_correlation": 0.45,
      "max_correlation": 0.72,
      "effective_n_assets": 2.8
    },
    "high_vix": {
      "avg_pairwise_correlation": 0.78,
      "max_correlation": 0.91,
      "effective_n_assets": 1.6
    }
  },
  "degradation_analysis": {
    "avg_corr_pct_increase": 73.3,
    "eff_assets_pct_decrease": 42.9
  },
  "risk_flags": ["SEVERE_CORRELATION_SPIKE"],
  "recommendations": [
    "Portfolio correlation increases by 73.3% during stress. Consider adding assets with low correlation to market factors."
  ]
}
```

## Implementation Details

### Why Log Returns?
- Time-additive: multi-period returns = sum of single-period returns
- Approximately normal distribution (better for correlation analysis)
- Standard in financial analysis

### Why 5-Day VIX Average?
- Daily VIX is noisy with frequent spikes
- 5-day average smooths out single-day volatility events
- Still responsive enough to capture regime changes

### Why Minimum Regime Days?
- Avoids classifying single-day VIX spikes as regime changes
- 20-day minimum ensures we're capturing sustained volatility periods
- Reduces noise in correlation calculations

### Effective Number of Assets Formula
Standard diversification metric that accounts for:
- Portfolio weights (concentration)
- Correlations between assets
- Result: "Your 10-stock portfolio behaves like 2.3 independent assets under stress"

## Common Issues

**"No data found for ticker"**
- Ticker might be invalid or delisted
- Yahoo Finance API might be down
- Check ticker on finance.yahoo.com first

**"Analysis takes too long"**
- Reduce `lookback_days` from 756 to 504
- Check internet connection
- Yahoo Finance sometimes rate-limits

**"Weights must sum to 1.0"**
- Portfolio weights need to add up to exactly 1.0
- Use 0.25, 0.25, 0.25, 0.25 not 25, 25, 25, 25

## Next Steps

This is Layer 1 of 4 layers:
- **Layer 1** (this): Regime-dependent diversification ✓
- **Layer 2** (next): Historical crash simulation
- **Layer 3**: Factor exposure decomposition  
- **Layer 4**: Regime-specific performance analysis

## Development

```bash
# Run with auto-reload
python -m app.main

# Access API docs
http://localhost:8001/docs

# Run with Streamlit dashboard
streamlit run streamlit_app.py
```
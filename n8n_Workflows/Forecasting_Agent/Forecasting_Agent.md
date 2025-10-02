# Forecasting Agent Workflow

An advanced **n8n workflow** that generates stock price forecasts by combining **market data (Alpha Vantage)** with **FinBERT-based sentiment analysis**. The agent computes optimistic, realistic, and pessimistic scenarios, applies risk scoring, and stores results in PostgreSQL for downstream dashboards and reporting.

---

## 🚀 Features
- **Market Data Integration** – Uses Alpha Vantage API to fetch OHLC price data  
- **Sentiment Analysis** – Integrates FinBERT for domain-specific sentiment scoring  
- **Scenario Forecasting** – Produces optimistic, realistic, and pessimistic values  
- **Volatility Analysis** – Detects risk levels (low, medium, high) from price fluctuations  
- **Backtesting** – Tracks error metrics (MAPE, RMSE, MAE) for forecast validation  
- **Database Storage** – Persists results into PostgreSQL for historical analysis  
- **Alerting (Optional)** – Email/Slack notifications for low-confidence predictions  

---

## 🎯 System Architecture

```
Alpha Vantage (Market Data) → Historical Data Processing → FinBERT Sentiment → Feature Engineering → Forecast Engine → PostgreSQL Storage → Alerts/Reports
```

---

## 📊 Workflow Design (n8n)

1. **Configuration Node** – Input for company symbol and runtime parameters  
2. **Alpha Vantage Node** – Fetches OHLC data (`TIME_SERIES_DAILY`)  
3. **Historical Data Node** – Cleans and formats market data  
4. **FinBERT Node** – Generates sentiment scores (positive, neutral, negative)  
5. **Merge Node** – Combines sentiment and historical data  
6. **Code Node (Feature Engineering)** – Calculates volatility, momentum, and trends  
7. **Code Node (Forecast Engine)** – Generates scenarios and assigns confidence  
8. **If Node** – Applies thresholds for alerts  
9. **PostgreSQL Insert** – Persists forecasts in database  
10. **Optional Notifications** – Email/Slack alerts for high-risk cases  

---

## ⚙️ Setup Instructions

### 1. Database Setup
Run PostgreSQL (example with Docker):

Create results table:

```sql
CREATE TABLE forecasting_results (
    id SERIAL PRIMARY KEY,
    timestamp timestamptz NOT NULL,
    symbol text NOT NULL,
    optimistic_value numeric,
    realistic_value numeric,
    pessimistic_value numeric,
    overall_confidence numeric,
    volatility_level text,
    mape numeric,
    rmse numeric,
    created_at timestamptz DEFAULT now()
);
```

---

### 2. API Configuration

Update `Configuration` node with your Alpha Vantage key:

```json
{
  "alpha_vantage_key": "your_api_key_here",
  "company_symbol": "AAPL"
}
```

⚠️ **Note**: Alpha Vantage free tier allows only 5 calls/minute. For larger workloads, consider **Polygon.io** or **TwelveData**.

---

### 3. Workflow Import
1. Import the `Forecasting_Agent.json` file into n8n  
2. Configure environment variables (API keys, DB credentials)  
3. Run manually or schedule via cron  

---

## 📈 Example Output

```json
{
  "timestamp": "2025-10-02T18:46:01.449Z",
  "symbol": "AAPL",
  "optimistic_value": 1162.26,
  "realistic_value": 993.38,
  "pessimistic_value": 825.40,
  "overall_confidence": 0.785,
  "volatility_level": "medium",
  "mape": 6.02,
  "rmse": 48.56
}
```

---

## 📝 Notes
- **API Limitations**: Alpha Vantage free tier is restricted to 5 calls/minute  
- **Current Scope**: Supports only one stock per execution run (batch mode can be added later)  
- **Customizable Assumptions**: Risk thresholds and sentiment weights can be tuned per industry  

---

## 🔮 Future Extensions
- Multi-symbol batch forecasting with Polygon.io  
- Real-time dashboards in Grafana/Power BI  
- Include **R²** and **MAE** scoring for stronger validation  
- Expand sentiment feeds (Reddit, Twitter, SEC filings)  
- Integrate reinforcement learning for adaptive forecasts  

---

##  Acknowledgments
- **n8n** – Workflow automation platform  
- **Alpha Vantage** – Market data provider  
- **Hugging Face (FinBERT)** – Sentiment model  
- **PostgreSQL** – Storage backend  



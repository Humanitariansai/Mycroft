
## AI News Sentiment Workflow
Daily workflow that monitors AI news and alerts on negative sentiment. Uses NewsAPI to fetch headlines, applies keyword-based sentiment analysis with embedded Python, stores results in Airtable, and sends email notifications for negative articles only. Simple yet effective implementation showing n8n's ability to combine visual workflow design with custom code.

## Financial Metrics Analysis Workflow
Tool that analyzes SEC financial filings for publicly traded companies. Executes a Python script to retrieve official financial data, calculates key metrics and ratios, and generates comprehensive reports with both structured JSON output and human-readable summaries. Currently manual but designed for future automation as part of a larger financial intelligence orchestration system.
> ⚠️ Note: This version is a starting point and **not yet production-grade**. We're currently working on a more robust implementation using advanced sentiment models and real-time triggers.

➡️ For full technical documentation, check out the [n8n-news-sentiment-agent.md](./n8n-news-sentiment-agent.md) file.

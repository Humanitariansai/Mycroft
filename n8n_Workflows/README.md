# n8n workflows 

## AI News Sentiment Workflow
Daily workflow that monitors AI news and alerts on negative sentiment. Uses NewsAPI to fetch headlines, applies keyword-based sentiment analysis with embedded Python, stores results in Airtable, and sends email notifications for negative articles only. Simple yet effective implementation showing n8n's ability to combine visual workflow design with custom code.

> ⚠️ Note: This version is a starting point.

➡️ For full technical documentation, check out the [README.md](./AI_NEWS_SENTIMENT/README.md) file.

➡️ A more advanced Phase 2 version is also available, which uses FinBERT-based sentiment analysis, multi-factor risk scoring, PostgreSQL storage, and real-time alerts. 
For full technical documentation, check out the [Mycroft News Intelligence Agent.md](./AI_NEWS_SENTIMENT/Mycroft%20News%20Intelligence%20Agent.md) file.

## Financial Metrics Analysis Workflow
Tool that analyzes SEC financial filings for publicly traded companies. Executes a Python script to retrieve official financial data, calculates key metrics and ratios, and generates comprehensive reports with both structured JSON output and human-readable summaries. Currently manual but designed for future automation as part of a larger financial intelligence orchestration system.

➡️ For full technical documentation, check out the [README.md](./SEC_FINANCIAL_METRICS/README.md) file.


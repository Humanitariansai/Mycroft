# n8n workflows 

## AI News Sentiment Workflow
Daily workflow that monitors AI news and alerts on negative sentiment. Uses NewsAPI to fetch headlines, applies keyword-based sentiment analysis with embedded Python, stores results in Airtable, and sends email notifications for negative articles only. Simple yet effective implementation showing n8n's ability to combine visual workflow design with custom code.

> ⚠️ Note: This version is a starting point.

➡️ For full technical documentation, check out the [AI News Sentiment.md](./AI_NEWS_SENTIMENT/AI%20News%20Sentiment.md) file.

➡️ A more advanced Phase 2 version is also available, which uses FinBERT-based sentiment analysis, multi-factor risk scoring, PostgreSQL storage, and real-time alerts. 
For full technical documentation, check out the [Mycroft News Intelligence Agent.md](./AI_NEWS_SENTIMENT/Mycroft%20News%20Intelligence%20Agent.md) file.

## Financial Metrics Analysis Workflow
Tool that analyzes SEC financial filings for publicly traded companies. Executes a Python script to retrieve official financial data, calculates key metrics and ratios, and generates comprehensive reports with both structured JSON output and human-readable summaries. Currently manual but designed for future automation as part of a larger financial intelligence orchestration system.

➡️ For full technical documentation, check out the [README.md](./SEC_FINANCIAL_METRICS/README.md) file.

## Patent Intelligence System Workflow
Automated patent monitoring and AI classification system that tracks recent USPTO patent filings. Extracts patent metadata from PatentsView API using cursor-based pagination, processes records to identify AI-related innovations through keyword matching and CPC code analysis, normalizes company names, and generates intelligence reports with confidence scoring. Delivers CSV data and metrics JSON via email for competitive intelligence and technology scouting.

➡️ For full technical documentation, check out the [README.md](./Patent_Intelligence_Agent/README.md) file.
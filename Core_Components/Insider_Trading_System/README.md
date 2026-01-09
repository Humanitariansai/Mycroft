# Capitol Trades Scraper

Automated web scraper for tracking U.S. congressional stock trades from [Capitol Trades](https://www.capitoltrades.com).

> **Developed by:** Darshan Rajopadhye (rajopadhye.d@northeastern.edu)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/darshanrr)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/therrshan)


## Overview

Congressional stock trades are disclosed via SEC Form 4 filings, which are difficult to parse. Capitol Trades aggregates these filings but has no public API and uses JavaScript to load content dynamically. This scraper handles the dynamic content and filters trades based on customizable criteria.

## Features

- Handles JavaScript-rendered content using Selenium
- Filters trades by filing delay, size, and ticker availability
- Automatic pagination with rate limiting
- Deduplication to prevent reprocessing trades
- Clean, structured output

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install ChromeDriver
pip install webdriver-manager
```

## Usage

```bash
python scraper.py
```

**Output:**
- `filtered_trades_YYYYMMDD_HHMMSS.txt` - Matching trades
- `trades_checked.txt` - Processed trade IDs
- `capitol_trades.log` - Execution logs

## Configuration

Edit the `Config` class to customize:

```python
class Config:
    RECENT_DAYS = 45          # Max filing delay (days)
    MIN_TRADE_SIZE = 5000     # Minimum trade size ($)
    PAGES_TO_SCRAPE = 5       # Number of pages to scrape
```

## Architecture

```
Config → TradeExtractor → TradeChecker → CapitolTradesScraper
```

- **Config**: Centralized settings
- **TradeExtractor**: Parses trade data (size, dates, tickers)
- **TradeChecker**: Tracks processed trades for deduplication
- **CapitolTradesScraper**: Main scraping orchestration

## Requirements

```txt
selenium==4.15.0
beautifulsoup4==4.12.2
requests==2.31.0
```

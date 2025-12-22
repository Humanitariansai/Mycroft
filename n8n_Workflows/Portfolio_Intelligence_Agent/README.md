# Portfolio Intelligence Agent – Documentation

## 📊 Overview

The **Portfolio Intelligence Agent** is an automated **n8n workflow** that tracks an AI-focused investment portfolio, calculates performance metrics, and generates daily AI-powered insights. Built as part of the **Mycroft Investment Intelligence Framework**, this agent embodies the philosophy of **“Using AI to Invest in AI”** while serving as an educational tool for learning portfolio management principles.

---

## 🎯 What It Does

The Portfolio Intelligence Agent automatically:

- Fetches **live stock prices** from Yahoo Finance API  
- Calculates **portfolio value** and position weights  
- Computes **daily returns** using historical comparisons  
- Generates **AI-powered analysis** using Claude Sonnet 4  
- Stores **historical data** in CSV files  
- Sends **daily HTML email reports**

**Schedule:** Runs Monday–Friday at **5:00 PM (market close)**

---

## 🏗️ Architecture

### Technology Stack

| Component | Technology | Purpose |
|---------|------------|---------|
| Workflow Engine | n8n | Automation orchestration |
| Data Storage | CSV files | Historical portfolio data |
| Market Data | Yahoo Finance API | Live stock prices |
| AI Analysis | Claude Sonnet 4 | Portfolio insights |
| Notifications | Gmail / SMTP | Daily email reports |

---

### Data Flow

```

[Schedule Trigger] → [Read Holdings] → [Fetch Prices] → [Calculate Metrics]
↓
[Read Previous Data] → [Calculate Returns] → [Generate AI Summary]
↓
[Save to CSV] → [Send Email Report]

```

---

## 📁 Project Structure

```

mycroft-portfolio/
├── data/
│   ├── holdings.json
│   ├── portfolio_history.csv
│   └── daily_summaries.csv
└── reports/   # (optional)

````

---

## 🚀 Quick Start Guide

### Prerequisites

- n8n (Docker or npm)
- Terminal access
- Anthropic API key
- Gmail / SMTP email account

---

### Installation Steps

#### 1️⃣ Create Project Directory

```bash
mkdir -p ~/mycroft-portfolio/data
cd ~/mycroft-portfolio
````

---

#### 2️⃣ Create Data Files

**`data/holdings.json`**

```json
[
  { "ticker": "NVDA", "quantity": 10, "sector": "Semiconductors" },
  { "ticker": "MSFT", "quantity": 15, "sector": "Cloud Infrastructure" },
  { "ticker": "GOOGL", "quantity": 8, "sector": "ML Infrastructure" },
  { "ticker": "AMD", "quantity": 12, "sector": "Semiconductors" },
  { "ticker": "META", "quantity": 6, "sector": "Foundation Models" }
]
```

**`data/portfolio_history.csv`**

```csv
date,ticker,quantity,price,value,weight,sector
```

**`data/daily_summaries.csv`**

```csv
date,total_value,daily_return,top_holding,top_holding_weight,ai_summary
```

---

#### 3️⃣ Import n8n Workflow

1. Open `http://localhost:5678`
2. Click **Import from File**
3. Select `portfolio-intelligence-agent.json`
4. Workflow loads automatically

---

#### 4️⃣ Configure Workflow

Update file paths:

| Node           | Parameter | Path                                                                |
| -------------- | --------- | ------------------------------------------------------------------- |
| Read Holdings  | File Path | `/Users/YOUR_USERNAME/mycroft-portfolio/data/holdings.json`         |
| Read Summaries | File Path | `/Users/YOUR_USERNAME/mycroft-portfolio/data/daily_summaries.csv`   |
| Append History | File Name | `/Users/YOUR_USERNAME/mycroft-portfolio/data/portfolio_history.csv` |
| Append Summary | File Name | `/Users/YOUR_USERNAME/mycroft-portfolio/data/daily_summaries.csv`   |

Add **Anthropic API key** in the `Generate AI Summary` node (`x-api-key`).

Configure **email credentials** in `Send Email Report`.

---

#### 5️⃣ Test the Workflow

* Click **Execute Workflow**
* Verify:

  * CSV files update
  * Email report arrives

---

## 📊 Data Schema

### `holdings.json`

```json
{
  "ticker": "string",
  "quantity": number,
  "sector": "string"
}
```

---

### `portfolio_history.csv`

| Column   | Description      |
| -------- | ---------------- |
| date     | Trading date     |
| ticker   | Stock symbol     |
| quantity | Shares           |
| price    | Daily price      |
| value    | Position value   |
| weight   | Portfolio weight |
| sector   | AI sector        |

---

### `daily_summaries.csv`

| Column             | Description      |
| ------------------ | ---------------- |
| date               | Trading date     |
| total_value        | Portfolio value  |
| daily_return       | Daily return     |
| top_holding        | Largest position |
| top_holding_weight | Weight           |
| ai_summary         | Claude analysis  |

---

## 📧 Email Report Contents

* Portfolio value
* Daily return (color-coded)
* Top holding
* AI-generated insights (3–4 bullets)
* Mycroft branding footer

---

## 🎓 Current Portfolio

| Ticker | Shares | Sector            |
| ------ | ------ | ----------------- |
| NVDA   | 10     | Semiconductors    |
| MSFT   | 15     | Cloud             |
| GOOGL  | 8      | ML Infra          |
| AMD    | 12     | Semiconductors    |
| META   | 6      | Foundation Models |

**Total Value:** ~$15k–16k

---

## 📈 Metrics Tracked

### Current

* Portfolio value
* Daily return
* Position weights
* Sector exposure

### Planned

* Rolling returns
* Volatility
* Max drawdown
* Risk alerts

---

## 🛠️ Customization

### Change Schedule

Edit cron in **Schedule Trigger**:

```
0 17 * * 1-5
```

### Modify AI Prompt

Edit prompt in **Generate AI Summary** node.

### Change Email Styling

Edit HTML inside **Send Email Report**.

---

## 🐛 Troubleshooting

| Issue            | Fix                    |
| ---------------- | ---------------------- |
| File not found   | Verify file paths      |
| Yahoo 404        | Check ticker           |
| API error        | Validate Anthropic key |
| Email fails      | Use App Password       |
| Daily return = 0 | First run only         |



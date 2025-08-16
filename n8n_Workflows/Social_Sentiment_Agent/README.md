# 🧠 Mycroft Social Sentiment Agent

> An AI-powered sentiment analysis agent for the Mycroft Framework — *Using AI to Invest in AI*

---

## 📄 Overview
The **Mycroft Social Sentiment Agent** is an open-source educational experiment in AI-powered investment intelligence.  
Named after Sherlock Holmes's analytical elder brother, this agent processes social media discussions about artificial intelligence to generate actionable investment signals.

---

## 🚀 Features

### **Core Capabilities**
- **Contextual Sentiment Analysis** — Advanced LLM-powered sentiment scoring with confidence metrics  
- **Technical Discussion Interpretation** — Distinguishes technical vs general AI discussions  
- **Topic Clustering & Trend Identification** — Categorizes content into 6 investment-relevant areas  
- **Developer Community Sentiment Tracking** — Monitors engagement, problem-solving, and innovation indicators  
- **Signal-to-Noise Ratio Optimization** — Multi-dimensional quality filtering for actionable intelligence  

### **Data Sources**
- **StackOverflow** — AI technical discussions and Q&A  
- **GitHub** — AI repository activity and developer sentiment  
- **Reddit r/MachineLearning** — ML community discussions  
- **Reddit r/investing** — Investment sentiment and market discussions  

### **AI Technology**
- **Groq API** with Llama 3.1-8B model for sentiment analysis  
- **Custom prompt engineering** for investment-focused classification  
- **Real-time processing** of social media content  
- **Automated quality scoring** and signal filtering  

---

## 🛠 Architecture

```
Data Collection → AI Analysis → Topic Classification → Quality Filtering → Intelligence Output
      ↓               ↓              ↓                   ↓                    ↓
  4 Platforms    Groq/Llama3.1   6 Categories      Signal Scoring      Google Sheets
```

---

## 🔄 Workflow Pipeline
1. **Multi-Platform Collection** — Simultaneous API calls to StackOverflow, GitHub, Reddit  
2. **Data Harmonization** — Unified format across different platform structures  
3. **LLM Sentiment Analysis** — Groq API processing with confidence scoring  
4. **Topic Classification** — AI-powered categorization into investment themes  
5. **Technical Analysis** — Keyword-based technical vs general content detection  
6. **Quality Scoring** — 20-point scoring system across multiple dimensions  
7. **Signal Filtering** — High/Medium/Low quality classification  
8. **Intelligence Export** — Executive summary and detailed signal data  
9. **Persistent Storage** — Automated Google Sheets integration  

---

## ⚙️ Installation & Setup

### **Prerequisites**
- n8n workflow automation platform  
- Groq API account (free tier available)  
- Google Cloud Console project with Sheets API enabled  
- Google Sheets for data storage  

### **Quick Start**
1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/mycroft-social-sentiment-agent
   ```
2. **Import n8n workflow**
   - Open n8n interface  
   - Import the `mycroft-social-sentiment-workflow.json` file  
   - Configure credentials (Groq API, Google Sheets OAuth2)  

3. **Set up Google Sheets**
   - Create new Google Sheet with column headers  
   - Configure OAuth2 authentication  
   - Update sheet ID in workflow  

4. **Configure API credentials**
   - Add Groq API key to n8n credentials  
   - Set up Google Sheets OAuth2 connection  
   - Test all API connections  

**Configuration Files**
- `mycroft-social-sentiment-workflow.json` — Complete n8n workflow  
- `google-sheets-schema.md` — Required column structure  
- `groq-api-setup.md` — API configuration guide  

---

## ▶️ Usage

### **Running the Agent**
1. **Manual Execution** — Trigger workflow manually in n8n  
2. **Scheduled Runs** — Set up cron schedule for automated execution  
3. **Webhook Triggers** — External trigger via HTTP requests  

### **Data Output**
- **Executive Summary** — High-level market intelligence and trending topics  
- **Detailed Signals** — Individual high-quality investment signals with scoring  

**Sample Output**
```json
{
  "mycroft_run_id": "1755043893067",
  "agent_type": "Social_Sentiment_Agent",
  "intelligence_insights": {
    "market_sentiment_direction": "bullish",
    "technical_community_activity": "high",
    "investment_signals": [...]
  },
  "high_quality_signals": [...]
}
```

---

## 🔗 Framework Integration
Part of the **Mycroft Framework** ecosystem:
- **Research Agents** — Utilize sentiment signals for company analysis  
- **Portfolio Agents** — Incorporate sentiment data into allocation decisions  
- **Mycroft Orchestration Layer** — Coordinates multiple agent insights  

---

## 🎓 Educational Philosophy
Following the Mycroft principle of *“building to learn”*, this agent is:
- A **Learning Platform** — Hands-on AI data pipeline experience  
- A **Research Tool** — Test sentiment analysis approaches for investment  
- An **Open Source Contribution** — Encourage collaboration and improvement  
- An **Experimental Framework** — Explore practical, working solutions  

---

## 📊 Performance Metrics

### **Current Benchmarks**
- **Processing Volume** — ~14 items per execution  
- **Signal Quality** — 25%+ high-signal retention after filtering  
- **Platform Coverage** — 4 major AI discussion platforms  
- **Response Time** — 2–3 minutes per analysis cycle  

### **Quality Scoring**
- **Signal Score Range** — 1–20 points  
- **Quality Tiers** — High (8+), Medium (5–7), Low (<5)  
- **Filtering Efficiency** — Noise reduction while preserving investment relevance  

---

## 🤝 Contributing
We welcome contributions:
1. Fork the repo  
2. Create a feature branch  
3. Test modifications  
4. Submit a pull request with documentation  
5. Join learning discussions  

**Areas for Enhancement**
- More data sources  
- Advanced sentiment techniques  
- Improved signal validation  
- Integration with other Mycroft agents  
- Performance optimization  

---

## 📜 License
Open-source educational project — MIT License  

---

## 🙏 Acknowledgments
- **Mycroft Framework** — Architecture and vision  
- **n8n Community** — Workflow automation platform  
- **Groq** — AI API infrastructure  
- **Professor Nik Bear Brown** — Educational guidance and framework design  

---

> *"Using AI to Invest in AI"* — An educational experiment to understand the AI revolution reshaping our world.

## **📈 SEC Financial Metrics Analyzer with n8n**

# 🏦 Financial Analysis Workflow Summary

This n8n workflow automatically executes a Python-based financial analyzer to pull SEC filing data and generate comprehensive financial reports for any publicly traded company. Perfect for investment research and financial analysis automation!

---

### **🔄 Workflow Overview**

This production-ready n8n workflow transforms raw SEC data into actionable financial insights through intelligent automation:

1. **🎯 Manual Trigger** – initiates the analysis process
2. **⚙️ Set Variables** – configures ticker symbol, script path, and user agent  
3. **🐍 Execute Python Script** – runs the financial analyzer with SEC data retrieval
4. **🔍 Process Results** – parses JSON output and handles errors gracefully
5. **📊 Format Analysis** – creates structured summaries and readable reports
6. **✅ Success Check** – routes to appropriate response handler
7. **📤 Response Handler** – returns formatted financial insights or error details

🟢 **Current Status**: Manual execution | **Future**: Full orchestration automation

---

### **💰 What You Get**

#### **Company Intelligence**
- 🏢 Company name & industry classification  
- 📈 Latest annual financial highlights
- 💵 Revenue, Net Income, Assets, Cash positions
- 📊 Key financial ratios & health metrics

#### **Example Output Structure**
```json
{
  "success": true,
  "ticker": "AAPL",
  "summary": {
    "company_name": "Apple Inc.",
    "financial_highlights": {
      "revenue": {
        "formatted": "$394,328.00M",
        "fiscal_year": "2023"
      },
      "net_income": {
        "formatted": "$96,995.00M"
      }
    },
    "key_ratios": {
      "profit_margin": 24.6,
      "return_on_assets": 22.4
    }
  }
}
```

---

### **🎛️ Quick Configuration**

**Default Setup:**
```javascript
// Set Variables Node Configuration
{
  "script_path": "/mnt/data/gitrepos/Mycroft/Core_Components/Financial-Metrics-Agent/financial_analyzer.py",
  "user_agent": "'Financial Analyzer your.email@example.com'",
  "ticker": "AAPL"  // 🍎 Change me!
}
```

**🚀 Want to analyze Tesla?** Just update:
```javascript
"ticker": "TSLA"  // ⚡ Electric!
```

**⚠️ Important**: Update the user agent with your actual email for SEC EDGAR compliance!

---

### **🧠 Smart Processing Logic**

The workflow includes intelligent error handling and data formatting:

```javascript
// Error Detection
if (exitCode !== 0) {
  return [{
    json: {
      success: false,
      error: `Script failed with exit code ${exitCode}: ${stderr}`,
      ticker: ticker,
      timestamp: new Date().toISOString()
    }
  }];
}

// Financial Formatting  
revenue: {
  value: annual.revenue?.value || 0,
  formatted: `$${(annual.revenue.value / 1000000).toFixed(2)}M`,
  fiscal_year: annual.revenue?.fiscal_year
}
```

---

### **Future Vision**🔮 

This is a **production-ready component** of a larger financial intelligence system that will be Mycroft:

📍 **Current State**: Manual execution for on-demand analysis  
🚀 **Future State**: Full automation as part of orchestration layer

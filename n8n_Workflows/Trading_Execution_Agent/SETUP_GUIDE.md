# Trading Execution Agent - Manual Setup Guide

## Prerequisites

### Required Software
1. **n8n** - Workflow automation platform
   ```bash
   npm install -g n8n
   # or use Docker
   docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
   ```

2. **Market Signal System** - Must be running on localhost:8001
   ```bash
   cd Core_Components/Market_Signal_System/backend
   python3 -m uvicorn main:app --reload --port 8001 --host 0.0.0.0
   ```

3. **Google Sheets** - For portfolio data and logging
4. **Alpaca Paper Trading Account** - For order execution

### Required Accounts
1. **Alpaca Markets** (Free Paper Trading)
   - Sign up at https://alpaca.markets
   - Generate API keys in dashboard
   - Note: Paper trading only - no real money

2. **Google Account** 
   - Create Google Sheets for portfolio data
   - Enable Google Sheets API access in n8n

## Step 1: Import Workflow

1. **Start n8n**
   ```bash
   n8n start
   ```
   Access at http://localhost:5678

2. **Import Workflow**
   - In n8n, click "Import from File"
   - Select `trading-execution-workflow.json`
   - Workflow will appear with all nodes

3. **Verify Node Structure**
   You should see 9 connected nodes:
   - Manual Trigger
   - Get Portfolio from Sheets
   - Process Portfolio Positions
   - Get Market Signals
   - Risk Assessment
   - Trading Decision Logic
   - Place Order (Alpaca)
   - Log Trade to Sheets
   - Send Email Notification

## Step 2: Configure Google Sheets

### Create Portfolio Spreadsheet

1. **Create new Google Sheet** named "Trading Portfolio"

2. **Create "Portfolio_Positions" tab** with columns:
   ```
   A: Ticker
   B: Shares
   C: Cost_Basis
   D: Current_Value
   E: Target_Allocation
   ```

3. **Create "Trade_Execution_Log" tab** with columns:
   ```
   A: Timestamp
   B: Ticker
   C: Action
   D: Shares
   E: Price
   F: Total_Value
   G: Risk_Score
   H: Signal_Confidence
   I: Order_ID
   J: Status
   ```

4. **Add sample data** to Portfolio_Positions:
   ```
   AAPL    50    150.00    8750     15.0
   NVDA    25    280.00    7020     20.0
   MSFT    30    365.00    10956    15.0
   TSLA    20    195.00    3916     10.0
   SPY     100   425.00    42530    30.0
   ```

### Configure n8n Google Sheets Integration

1. **In n8n, go to Credentials**
2. **Add Google Sheets API credential**
3. **Authenticate with your Google account**
4. **Copy your spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
   ```

## Step 3: Set Environment Variables

1. **In n8n Settings → Variables**
   ```
   ALPACA_API_KEY=your_alpaca_api_key
   ALPACA_SECRET_KEY=your_alpaca_secret_key
   PORTFOLIO_SHEET_ID=your_google_sheets_id
   ```

2. **Get Alpaca API Keys**
   - Log into Alpaca dashboard
   - Go to "Your API Keys"
   - Generate new paper trading keys
   - Copy Key ID and Secret Key

## Step 4: Configure Workflow Nodes

### 1. Google Sheets Nodes
- **Get Portfolio from Sheets**: Set spreadsheet ID and range "Portfolio_Positions!A:E"
- **Log Trade to Sheets**: Set spreadsheet ID and range "Trade_Execution_Log!A:J"

### 2. HTTP Request Nodes
- **Market Signal System**: Verify URL is http://localhost:8001/api/analyze
- **Alpaca API**: Verify URL is https://paper-api.alpaca.markets/v2/orders

### 3. Email Notification Node
- Configure SMTP settings or use n8n email service
- Set recipient email address

## Step 5: Test Individual Components

### Test Market Signal System
```bash
curl -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

### Test Google Sheets Access
1. Execute "Get Portfolio from Sheets" node
2. Verify data is retrieved correctly

### Test Alpaca Connection
1. Execute "Place Order (Alpaca)" node manually
2. Check for authentication success

## Step 6: Run Complete Workflow

1. **Start Market Signal System**
   ```bash
   cd Core_Components/Market_Signal_System/backend
   python3 -m uvicorn main:app --reload --port 8001
   ```

2. **Execute Workflow**
   - Click "Manual Trigger" node
   - Click "Execute Node"
   - Monitor execution progress

3. **Verify Results**
   - Check Trade_Execution_Log sheet for new entries
   - Check email for notifications
   - Review Alpaca dashboard for paper trades

## Troubleshooting

### Common Issues

1. **Market Signal System Not Running**
   ```
   Error: ECONNREFUSED localhost:8001
   Solution: Start the Market Signal System backend
   ```

2. **Google Sheets Permission Denied**
   ```
   Error: 403 Forbidden
   Solution: Re-authenticate Google Sheets credentials
   ```

3. **Alpaca API Authentication Failed**
   ```
   Error: 401 Unauthorized  
   Solution: Verify API keys are correct and for paper trading
   ```

4. **Node Execution Timeout**
   ```
   Error: Request timeout
   Solution: Increase timeout in HTTP Request nodes to 30 seconds
   ```

### Testing Workflow Components

Run the included test script:
```bash
cd Trading_Execution_Agent
python3 test_integration.py
```

This will test:
- Market Signal System API calls
- Risk assessment logic
- Trading decision making
- Order simulation

## Security Notes

1. **API Keys**: Store in n8n environment variables, never in workflow JSON
2. **Paper Trading Only**: This system is configured for paper trading only
3. **No Real Money**: Alpaca paper trading uses virtual money
4. **Audit Trail**: All trades logged to Google Sheets for transparency

## Production Deployment

### Recommended Setup
1. **VPS/Cloud Instance** running n8n
2. **Scheduled Execution** instead of manual trigger
3. **Error Monitoring** with email alerts
4. **Backup Strategy** for Google Sheets data
5. **API Rate Limiting** for external services

### Scaling Considerations
1. **Multiple Portfolios**: Create separate workflows
2. **Advanced Risk Management**: Integrate with Risk Management Agent webhook
3. **Real Broker Integration**: Replace Alpaca with production broker
4. **Machine Learning**: Add ML-based position sizing

## Support

For issues with:
- **n8n**: Check n8n documentation and community forum
- **Market Signal System**: Review Core_Components documentation
- **Alpaca API**: Check Alpaca API documentation
- **Google Sheets**: Verify API quotas and permissions

---

**Remember**: This is an educational system using paper trading only. Never risk real money without proper testing and risk management.
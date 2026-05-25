# Mycroft Trading Execution Agent

An automated AI-powered trading execution system built with n8n that bridges the gap between Mycroft's investment intelligence and actual trade execution using paper trading through Alpaca Markets.

## Overview

The Mycroft Trading Execution Agent is the first execution component of the Mycroft Framework - an open-source educational project exploring practical AI applications in investment intelligence. This agent orchestrates existing Mycroft intelligence agents to make automated trading decisions while maintaining strict risk controls and comprehensive logging.

### Key Features

- **Multi-Agent Orchestration**: Integrates Market Signal System, Risk Management Agent, and Portfolio Intelligence
- **Paper Trading Execution**: Safe execution through Alpaca Markets paper trading API
- **Comprehensive Risk Management**: Position limits, risk scoring, and stop-loss automation
- **Real-Time Decision Making**: Combines technical analysis, sentiment, and risk assessment
- **Audit Trail**: Complete logging of all decisions and executions to Google Sheets
- **Safety First**: Multiple validation layers and paper trading only

## Architecture

The Trading Execution Agent operates as an orchestrator that coordinates multiple existing Mycroft components:

### Existing Agent Integration
```
Portfolio Data (Sheets) → Market Signal System → Risk Management Agent → Execution Decision → Alpaca API → Trade Logging
```

### Component Mapping
1. **Market Signal System** (Core_Components) - Multi-agent investment analysis with conflict resolution
2. **Risk Management Agent** (n8n_Workflows) - Portfolio risk monitoring and position sizing
3. **Portfolio Intelligence Agent** (n8n_Workflows) - Performance tracking and allocation analysis
4. **NEW: Execution Layer** - Alpaca API integration for order placement

## Workflow Architecture

The n8n workflow consists of 9 connected nodes:

1. **Manual Trigger** - Initiates trading analysis and execution cycle
2. **Get Portfolio from Sheets** - Reads current positions and target allocations
3. **Process Portfolio Positions** - Normalizes and validates portfolio data
4. **Get Market Signals** - Calls Market Signal System API for BUY/SELL/HOLD recommendations
5. **Risk Assessment** - Calls Risk Management Agent for position sizing and risk validation
6. **Trading Decision Logic** - Combines signals and risk to make final execution decision
7. **Place Order (Alpaca)** - Executes trades through Alpaca paper trading API
8. **Log Trade to Sheets** - Records all trade details for audit trail
9. **Send Email Notification** - Alerts on trade execution and results

### Data Flow
```
Google Sheets Portfolio → Market Analysis → Risk Validation → Order Execution → Results Logging → Email Alerts
```

## Trading Logic

### Decision Criteria
The agent will only execute trades when ALL conditions are met:

**BUY Conditions:**
- Market Signal System recommends BUY
- Signal confidence ≥ 0.6
- Risk score ≤ 0.7  
- Position size within limits (≤5% of portfolio)
- Sufficient buying power
- Current position < target allocation

**SELL Conditions:**
- Market Signal System recommends SELL
- Signal confidence ≥ 0.6
- Risk score indicates elevated risk
- Current position > 0 shares
- Stop-loss triggered OR target reached

**HOLD Conditions:**
- Any safety check fails
- Low signal confidence
- High risk score
- Position limits exceeded
- Market hours closed

### Risk Management Integration

The agent leverages the existing Risk Management Agent's capabilities:

- **Position Sizing**: Maximum 5% of portfolio per position
- **Stop-Loss Management**: 8% trailing stop-loss with volatility adjustment
- **Risk Scoring**: Multi-factor risk analysis (0.0-1.0 scale)
- **Portfolio Limits**: Maximum risk exposure controls
- **Volatility Adjustment**: Position sizing based on asset volatility

## Setup Requirements

### Prerequisites
- n8n instance running
- Google Sheets access configured in n8n
- Alpaca Markets paper trading account
- Market Signal System running (localhost:8001)
- Risk Management Agent workflow deployed

### Environment Variables
```bash
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key  
PORTFOLIO_SHEET_ID=your_google_sheets_id
```

### Google Sheets Structure

#### Portfolio_Positions Sheet
| Ticker | Shares | Cost_Basis | Current_Value | Target_Allocation |
|--------|--------|------------|---------------|-------------------|
| AAPL   | 50     | 150.00     | 175.50        | 15.0             |
| NVDA   | 25     | 220.00     | 280.75        | 20.0             |

#### Trade_Execution_Log Sheet  
| Timestamp | Ticker | Action | Shares | Price | Total_Value | Risk_Score | Signal_Confidence | Order_ID | Status |
|-----------|--------|---------|--------|-------|-------------|------------|-------------------|----------|---------|

## Integration with Existing Agents

### Market Signal System Integration
```http
POST http://localhost:8001/api/analyze
Content-Type: application/json

{
  \"ticker\": \"AAPL\"
}
```

**Response Used:**
- `final_recommendation.decision` (BUY/SELL/HOLD)
- `final_recommendation.score` (confidence level)
- `conflict_analysis.has_conflicts` (decision uncertainty)

### Risk Management Agent Integration
```http  
POST http://localhost:5678/webhook/risk-assessment
Content-Type: application/json

{
  \"ticker\": \"AAPL\",
  \"currentPosition\": 50,
  \"costBasis\": 150.00
}
```

**Response Used:**
- `risk_score` (overall risk assessment)
- `position_size_recommendation` (shares to trade)
- `stop_loss_level` (exit price)

## Safety Features

### Multi-Layer Validation
1. **Signal Confidence**: Minimum 0.6 confidence required
2. **Risk Scoring**: Maximum 0.7 risk score allowed
3. **Position Limits**: 5% maximum position size
4. **Account Validation**: Sufficient buying power check
5. **Market Hours**: Trading only during market hours
6. **Paper Trading**: No real money at risk

### Error Handling
- API connection failures logged and alerted
- Invalid orders rejected with detailed logging
- Risk limit violations prevent execution
- All errors trigger email notifications
- Complete audit trail maintained

## Performance Monitoring

### Metrics Tracked
- Trade success rate
- Average holding period
- Risk-adjusted returns
- Signal accuracy
- Risk management effectiveness

### Logging and Alerts
- Real-time trade execution logging
- Daily performance summaries
- Risk threshold breach alerts
- System error notifications
- Weekly portfolio rebalancing reports

## Example Usage

### Basic Execution Cycle
1. Trigger workflow manually or via schedule
2. Agent reads current portfolio from Google Sheets
3. For each position, calls Market Signal System
4. Validates signals with Risk Management Agent
5. Executes qualifying trades through Alpaca
6. Logs all results and sends notifications

### Sample Execution Decision
```javascript
// Example decision logic output
{
  \"ticker\": \"AAPL\",
  \"action\": \"BUY\",
  \"quantity\": 25,
  \"reason\": \"Strong buy signal with acceptable risk\",
  \"confidence\": 0.75,
  \"riskScore\": 0.45,
  \"timestamp\": \"2024-01-15T14:30:00Z\"
}
```

## Educational Value

This agent demonstrates:
- **Multi-agent coordination** using existing AI systems
- **Production trading workflows** with real broker integration  
- **Risk management automation** with quantitative controls
- **API orchestration** across multiple financial services
- **Audit trails** and regulatory compliance considerations

## Limitations and Disclaimers

⚠️ **Important Disclaimers:**
- This system is for EDUCATIONAL PURPOSES ONLY
- Uses paper trading - no real money at risk
- NOT financial advice or investment recommendations
- Past performance does not guarantee future results
- Always consult licensed financial advisors for investment decisions

### Technical Limitations
- Dependent on external API availability
- Market data delays (15-20 minutes for free sources)
- Paper trading may not reflect real market conditions
- Limited to US equity markets through Alpaca

## Future Enhancements

### Planned Features (Phase 2)
- **Options trading** integration for advanced strategies
- **Crypto trading** through additional broker APIs
- **Tax optimization** with wash sale rule compliance
- **Portfolio rebalancing** automation with drift detection
- **Machine learning** for signal confidence calibration

### Advanced Risk Management
- **Value at Risk (VaR)** calculations
- **Stress testing** integration with Portfolio Stress Test System
- **Correlation analysis** for position concentration risk
- **Dynamic position sizing** based on market volatility

## Contributing

This agent follows Mycroft Framework contribution guidelines:
1. No modifications to existing components
2. Educational focus with comprehensive documentation  
3. Open-source collaboration and knowledge sharing
4. Safety-first approach with paper trading only

## Technical Specifications

### Dependencies
- n8n workflow automation platform
- Google Sheets API integration
- Alpaca Markets API (paper trading)
- Existing Mycroft agents (Market Signals, Risk Management)

### Performance Requirements
- Workflow execution: < 30 seconds per portfolio
- API response times: < 5 seconds per call
- Error recovery: Automatic retry with exponential backoff
- Logging latency: < 1 second to Google Sheets

### Security Considerations
- API keys stored as environment variables
- No sensitive data in workflow JSON
- HTTPS only for all external API calls
- Audit logging for compliance

---

## Version Information
**Current Version:** 1.0  
**Status:** Educational/Paper Trading Only  
**Last Updated:** January 2024  
**Compatibility:** n8n v1.0+, Mycroft Framework v2.0+

---

**Note:** This Trading Execution Agent represents the culmination of Mycroft's intelligence gathering capabilities, bridging analysis to action while maintaining educational focus and safety through paper trading only.
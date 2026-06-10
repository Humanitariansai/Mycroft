# Alpaca Paper Trading Setup

## 1. Create Alpaca Paper Trading Account

1. Go to [Alpaca Markets](https://alpaca.markets)
2. Sign up for a free paper trading account
3. Navigate to "Your API Keys" in the dashboard
4. Generate new API credentials

## 2. Environment Variables

Add these to your n8n environment or .env file:

```bash
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
PORTFOLIO_SHEET_ID=your_google_sheets_id
```

## 3. API Endpoints Used

### Account Information
- `GET /v2/account` - Get account details and buying power

### Orders
- `POST /v2/orders` - Place new orders
- `GET /v2/orders` - List orders
- `GET /v2/orders/{order_id}` - Get specific order

### Positions  
- `GET /v2/positions` - List all positions
- `GET /v2/positions/{symbol}` - Get position for specific symbol

## 4. Order Types Supported

- **Market**: Executes immediately at current market price
- **Limit**: Executes only at specified price or better
- **Stop**: Converts to market order when price reached
- **Stop Limit**: Converts to limit order when price reached

## 5. Safety Features

- **Paper Trading Only**: No real money at risk
- **Position Limits**: Maximum 5% of portfolio per position
- **Risk Score Validation**: No trades above 0.7 risk score
- **Confidence Threshold**: Minimum 0.6 signal confidence
- **Daily Trade Limits**: Maximum 10 trades per day

## 6. Error Handling

The workflow includes comprehensive error handling:
- API connection failures
- Invalid order parameters  
- Insufficient buying power
- Market hours validation
- Risk limit violations

All errors are logged to Google Sheets and email notifications sent.
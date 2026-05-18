# Market Signal Analysis System

A sophisticated multi-agent investment analysis system implementing advanced conflict resolution algorithms for real-time market signals. This system addresses the critical challenge of agent disagreement in automated investment decisions, moving beyond simple averaging to intelligent consensus building.

## 🎯 Purpose & Problem Solved

Traditional multi-agent investment systems suffer from a fundamental flaw: when agents disagree, they typically use naive averaging methods that dilute valuable insights. This system implements research-backed conflict resolution algorithms that:

- **Detect meaningful disagreements** between agents
- **Preserve minority opinions** when they have high confidence
- **Weight decisions** based on agent expertise and data quality
- **Provide transparency** into the decision-making process

## 🏗️ Architecture Overview

```
Market_Signal_System/
├── backend/                    # FastAPI + LangGraph Backend
│   ├── main.py                # API server with CORS
│   ├── agents.py              # Core agent implementations
│   ├── conflict_resolution.py # Conflict resolution engine
│   ├── models.py              # Pydantic data models
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React + Tailwind Frontend
│   ├── src/
│   │   ├── App.jsx           # Main application
│   │   └── pages/
│   │       └── MarketSignals.jsx # Market analysis UI
│   └── package.json          # Node.js dependencies
└── README.md                 # This file
```

## 🤖 Agent Architecture

### Three Specialized Agents

1. **Technical Analysis Agent**
   - Analyzes price trends, volume, momentum indicators
   - Uses Yahoo Finance API for real-time market data
   - Provides technical scoring based on multiple indicators

2. **News Sentiment Agent** 
   - Integrates Yahoo Finance analyst recommendations
   - Processes recent news sentiment via NewsAPI
   - Combines analyst data (80% weight) with news sentiment (20% weight)

3. **Market Fear/Greed Agent**
   - Analyzes VIX volatility index as fear indicator
   - Calculates market sentiment based on volatility levels
   - Provides contrarian signals during extreme fear/greed

### Agent Execution Flow

```python
# LangGraph orchestrates parallel agent execution
graph = StateGraph(MarketState)
graph.add_node("technical", technical_analysis_agent)
graph.add_node("sentiment", news_sentiment_agent) 
graph.add_node("fear_greed", market_fear_greed_agent)
graph.add_node("resolver", conflict_resolution_node)

# Agents run in parallel, then conflict resolution
graph.add_edge("technical", "resolver")
graph.add_edge("sentiment", "resolver")
graph.add_edge("fear_greed", "resolver")
```

## ⚔️ Conflict Resolution Engine

### Detection Algorithms

The system detects three types of conflicts:

1. **Analytical Disagreement**: When agent scores vary significantly
   ```python
   score_std = np.std([agent.edge_score for agent in findings])
   analytical_disagreement = score_std > 0.2
   ```

2. **Source Quality Mismatch**: When data sources have varying reliability
   ```python
   confidence_std = np.std([agent.confidence for agent in findings])
   quality_mismatch = confidence_std > 0.15
   ```

3. **Temporal Lag**: When agents use data from different time periods
   ```python
   timestamps = [agent.data_timestamp for agent in findings]
   temporal_lag = max(timestamps) - min(timestamps) > threshold
   ```

### Resolution Methods

1. **Simple Average**: Baseline averaging method
   ```python
   simple_avg = sum(scores) / len(scores)
   ```

2. **Confidence Weighted**: Weights decisions by agent confidence
   ```python
   weighted_score = sum(score * confidence) / sum(confidence)
   ```

3. **Ensemble Voting**: Categorical voting with confidence thresholds
   ```python
   votes = {"BUY": [], "HOLD": [], "SELL": []}
   for agent in agents:
       decision = get_decision(agent.score)
       votes[decision].append(agent.confidence)
   ```

### Resolution Selection Logic

```python
def select_resolution_method(conflict_analysis):
    if conflict_analysis.disagreement_score > 0.5:
        return "ensemble_voting"  # High disagreement -> democratic voting
    elif any("quality" in t for t in conflict_analysis.conflict_types):
        return "confidence_weighted"  # Quality issues -> weight by confidence  
    else:
        return "simple_average"  # Low conflict -> simple averaging
```

## 📊 Data Integration

### Real-World Data Sources

1. **Yahoo Finance API**
   - Real-time stock prices and technical indicators
   - Professional analyst recommendations and target prices
   - Historical price data for technical analysis
   - No API key required

2. **NewsAPI** 
   - Recent news articles for sentiment analysis
   - Requires API key (95e39812-bb59-44d6-bbc0-93717e0a9aa9)
   - Filters for financial news relevance

3. **VIX Data (via Yahoo Finance)**
   - Chicago Board Options Exchange Volatility Index
   - Real-time fear/greed sentiment indicator
   - Historical context for volatility analysis

### Data Flow

```
User Input (Ticker) → Parallel Agent Execution → Conflict Detection → Resolution → Final Recommendation
     ↓                        ↓                        ↓              ↓              ↓
   "AAPL"            Technical + Sentiment + VIX    Algorithm     Weighted      BUY/SELL/HOLD
                         Analysis                   Selection     Decision
```

## 🚀 Installation & Setup

### Backend Setup

```bash
cd Market_Signal_System/backend

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your_groq_api_key_here"
export NEWS_API_KEY="95e39812-bb59-44d6-bbc0-93717e0a9aa9"

# Run the FastAPI server
uvicorn main:app --reload --port 8001 --host 0.0.0.0
```

### Frontend Setup

```bash
cd Market_Signal_System/frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev  # Runs on http://localhost:5174
```

## 🔧 Configuration

### Environment Variables

- `GROQ_API_KEY`: Required for LLM-based analysis
- `NEWS_API_KEY`: Required for news sentiment analysis
- `PORT`: Backend port (default: 8001)

### Tunable Parameters

```python
# In agents.py - adjust these thresholds as needed
BUY_THRESHOLD = 0.55   # Lower = more BUY signals
SELL_THRESHOLD = 0.45  # Higher = more SELL signals

# In conflict_resolution.py
DISAGREEMENT_THRESHOLD = 0.2  # Sensitivity to agent disagreement
CONFIDENCE_THRESHOLD = 0.15   # Confidence variation tolerance
```

## 📈 Usage Examples

### Basic Analysis

```bash
curl -X POST "http://localhost:8001/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

### Understanding Output

```json
{
  "success": true,
  "data": {
    "final_recommendation": {
      "decision": "BUY",
      "score": 0.652,
      "method": "confidence_weighted",
      "rationale": "Strong analyst consensus with moderate news sentiment"
    },
    "conflict_analysis": {
      "has_conflicts": true,
      "disagreement_score": 0.234,
      "conflict_types": ["analytical_disagreement"]
    },
    "agent_findings": [
      {
        "agent_name": "technical_analysis_agent",
        "edge_score": 0.723,
        "confidence": 0.85,
        "insights": ["Strong upward momentum", "High trading volume"]
      }
      // ... other agents
    ]
  }
}
```

## 🔍 Monitoring & Debugging

### Key Metrics to Watch

1. **Disagreement Score**: Higher values indicate agent conflicts
2. **Confidence Levels**: Lower values suggest data quality issues  
3. **Resolution Method**: Shows which algorithm was used
4. **Agent Performance**: Individual agent accuracy over time

### Common Issues

1. **"Fear Greed Index Unavailable"**: VIX data temporarily inaccessible
   - Solution: System falls back to neutral sentiment (0.5)

2. **All Recommendations Show HOLD**: Thresholds too conservative
   - Solution: Lower BUY_THRESHOLD or raise SELL_THRESHOLD

3. **API Rate Limiting**: Too many requests to external services
   - Solution: Implement caching or request throttling

## 🧪 Testing

### Test Different Scenarios

```bash
# Test high-volatility stock
curl -X POST "http://localhost:8001/api/analyze" -d '{"ticker": "NVDA"}'

# Test stable dividend stock  
curl -X POST "http://localhost:8001/api/analyze" -d '{"ticker": "JNJ"}'

# Test market index
curl -X POST "http://localhost:8001/api/analyze" -d '{"ticker": "SPY"}'
```

## 🔮 Future Enhancements

### Planned Features

1. **Additional Agents**
   - Options flow analysis
   - Institutional sentiment tracking
   - Macroeconomic indicators

2. **Advanced Conflict Resolution**
   - Machine learning-based agent weighting
   - Historical performance tracking
   - Dynamic threshold adjustment

3. **Enhanced UI**
   - Real-time updates
   - Historical analysis charts
   - Agent performance metrics

### Research Integration

This system implements concepts from "When the Agents Disagree, Who Decides?" research paper, focusing on:

- Multi-agent consensus mechanisms
- Confidence-based decision weighting
- Transparent conflict resolution
- Preservation of minority expert opinions

## 📝 API Documentation

### Endpoints

- `POST /api/analyze`: Analyze market signals for a ticker
  - Request: `{"ticker": "AAPL"}`
  - Response: Complete analysis with conflict resolution

### Data Models

```python
class AgentFindings(BaseModel):
    agent_name: str
    edge_score: float
    confidence: float
    insights: List[str]
    metrics: Dict[str, Any]

class ConflictAnalysis(BaseModel):
    has_conflicts: bool
    disagreement_score: float
    conflict_types: List[str]
    conflicting_agents: List[Dict]

class FinalRecommendation(BaseModel):
    decision: str  # "BUY", "SELL", "HOLD"
    score: float
    method: str
    rationale: str
```

## 🤝 Contributing

### Development Guidelines

1. **Agent Development**: Follow the AgentFindings model structure
2. **Conflict Resolution**: Add new methods to ConflictResolver class
3. **Testing**: Validate with multiple tickers and market conditions
4. **Documentation**: Update README for new features

### Code Style

- Use type hints for all functions
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for complex functions

## 📄 License

This project is part of the Mycroft Core Components system. See main repository for license details.

---

**Note**: This system is for educational and research purposes. Do not use for actual investment decisions without proper risk assessment and professional advice.
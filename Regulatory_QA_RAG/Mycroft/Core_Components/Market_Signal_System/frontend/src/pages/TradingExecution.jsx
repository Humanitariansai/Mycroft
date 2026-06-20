import { useState } from 'react'

const PortfolioCard = ({ position, onTrade }) => {
  const [loading, setLoading] = useState(false)
  
  const handleTrade = async (action) => {
    setLoading(true)
    try {
      await onTrade(position.ticker, action)
    } finally {
      setLoading(false)
    }
  }
  
  const getPositionColor = (value, target) => {
    const diff = ((value - target) / target) * 100
    if (Math.abs(diff) < 5) return 'text-green-600'
    if (Math.abs(diff) < 15) return 'text-yellow-600'
    return 'text-red-600'
  }
  
  return (
    <div className="bg-white rounded-xl border-2 border-gray-200 p-6 shadow-lg hover:shadow-xl transition-all">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-black">{position.ticker}</h3>
          <p className="text-black">Current: {position.shares} shares</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-black">${position.currentValue.toLocaleString()}</div>
          <div className={`text-sm font-semibold ${getPositionColor(position.currentValue, position.targetValue)}`}>
            Target: ${position.targetValue.toLocaleString()} ({position.targetAllocation}%)
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-black">Cost Basis:</span>
          <span className="font-semibold ml-2">${position.costBasis}</span>
        </div>
        <div className="bg-gray-50 p-2 rounded">
          <span className="text-black">P&L:</span>
          <span className={`font-semibold ml-2 ${position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${position.pnl > 0 ? '+' : ''}{position.pnl.toLocaleString()}
          </span>
        </div>
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={() => handleTrade('BUY')}
          disabled={loading}
          className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 font-semibold"
        >
          {loading ? 'Processing...' : '📈 BUY'}
        </button>
        <button
          onClick={() => handleTrade('SELL')}
          disabled={loading}
          className="flex-1 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 disabled:opacity-50 font-semibold"
        >
          {loading ? 'Processing...' : '📉 SELL'}
        </button>
        <button
          onClick={() => handleTrade('ANALYZE')}
          disabled={loading}
          className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-semibold"
        >
          {loading ? 'Processing...' : '🔍 ANALYZE'}
        </button>
      </div>
    </div>
  )
}

const TradeExecutionCard = ({ trade }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'FILLED': return 'bg-green-100 text-green-800 border-green-300'
      case 'PENDING': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'REJECTED': return 'bg-red-100 text-red-800 border-red-300'
      default: return 'bg-gray-100 text-black border-gray-300'
    }
  }
  
  const getActionColor = (action) => {
    switch (action) {
      case 'BUY': return 'text-green-600'
      case 'SELL': return 'text-red-600'
      default: return 'text-black'
    }
  }
  
  return (
    <div className="bg-white rounded-lg border p-4 shadow hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-bold text-lg">{trade.ticker}</h4>
          <p className={`font-semibold ${getActionColor(trade.action)}`}>
            {trade.action} {trade.quantity} shares
          </p>
        </div>
        <div className="text-right">
          <div className={`px-2 py-1 rounded border text-xs font-semibold ${getStatusColor(trade.status)}`}>
            {trade.status}
          </div>
          <p className="text-xs text-black mt-1">{trade.timestamp}</p>
        </div>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-black">Price:</span>
          <span className="font-semibold">${trade.price}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-black">Total:</span>
          <span className="font-semibold">${(trade.price * trade.quantity).toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-black">Risk Score:</span>
          <span className="font-semibold">{(trade.riskScore * 100).toFixed(0)}%</span>
        </div>
        <div className="bg-gray-50 p-2 rounded text-xs">
          <strong>Reason:</strong> {trade.reason}
        </div>
      </div>
    </div>
  )
}

export default function TradingExecution() {
  const [portfolio, setPortfolio] = useState([
    {
      ticker: "AAPL",
      shares: 50,
      costBasis: 150.00,
      currentValue: 15441,
      targetValue: 15000,
      targetAllocation: 15.0,
      pnl: 2941
    },
    {
      ticker: "NVDA", 
      shares: 25,
      costBasis: 280.00,
      currentValue: 8020,
      targetValue: 20000,
      targetAllocation: 20.0,
      pnl: 1020
    },
    {
      ticker: "MSFT",
      shares: 30,
      costBasis: 365.00,
      currentValue: 12156,
      targetValue: 15000,
      targetAllocation: 15.0,
      pnl: 1206
    },
    {
      ticker: "TSLA",
      shares: 20,
      costBasis: 195.00,
      currentValue: 4316,
      targetValue: 10000,
      targetAllocation: 10.0,
      pnl: 416
    },
    {
      ticker: "SPY",
      shares: 100,
      costBasis: 425.00,
      currentValue: 43030,
      targetValue: 30000,
      targetAllocation: 30.0,
      pnl: 530
    }
  ])
  
  const [tradeHistory, setTradeHistory] = useState([
    {
      id: 1,
      ticker: "NVDA",
      action: "BUY",
      quantity: 4,
      price: 285.50,
      status: "FILLED",
      riskScore: 0.45,
      reason: "Strong buy signal with acceptable risk",
      timestamp: "2024-01-15 14:30:22"
    },
    {
      id: 2, 
      ticker: "TSLA",
      action: "BUY",
      quantity: 10,
      price: 195.80,
      status: "FILLED", 
      riskScore: 0.35,
      reason: "Underweight position, bullish signals",
      timestamp: "2024-01-15 11:15:18"
    },
    {
      id: 3,
      ticker: "AAPL", 
      action: "SELL",
      quantity: 15,
      status: "REJECTED",
      price: 308.20,
      riskScore: 0.85,
      reason: "Risk limits exceeded - position too large",
      timestamp: "2024-01-15 09:45:12"
    }
  ])
  
  const [executing, setExecuting] = useState(false)
  const [executionResults, setExecutionResults] = useState(null)
  
  const portfolioValue = portfolio.reduce((sum, pos) => sum + pos.currentValue, 0)
  const totalPnL = portfolio.reduce((sum, pos) => sum + pos.pnl, 0)
  
  const handleTrade = async (ticker, action) => {
    setExecuting(true)
    setExecutionResults(null)
    
    try {
      // Simulate market signal analysis + risk assessment + execution
      const response = await fetch('http://localhost:8001/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker })
      })
      
      if (response.ok) {
        const signalData = await response.json()
        const signal = signalData.data.final_recommendation
        
        // Simulate trading logic
        const mockExecution = {
          ticker,
          requestedAction: action,
          signalRecommendation: signal.score >= 0.55 ? 'BUY' : signal.score <= 0.45 ? 'SELL' : 'HOLD',
          signalConfidence: signal.score,
          riskScore: Math.random() * 0.5 + 0.2,
          executedAction: 'HOLD',
          quantity: 0,
          price: Math.random() * 50 + 200,
          reason: 'Demo execution - paper trading simulation'
        }
        
        // Apply trading logic
        if (action === 'BUY' && mockExecution.signalRecommendation === 'BUY' && mockExecution.riskScore < 0.6) {
          mockExecution.executedAction = 'BUY'
          mockExecution.quantity = Math.floor(Math.random() * 20) + 5
          mockExecution.reason = 'Strong buy signal with acceptable risk'
        } else if (action === 'SELL' && portfolio.find(p => p.ticker === ticker)?.shares > 0) {
          mockExecution.executedAction = 'SELL'
          mockExecution.quantity = Math.floor(Math.random() * 10) + 5
          mockExecution.reason = 'Position reduction based on risk/signal analysis'
        } else {
          mockExecution.reason = `Risk too high (${(mockExecution.riskScore * 100).toFixed(0)}%) or insufficient signal confidence`
        }
        
        setExecutionResults(mockExecution)
        
        // Add to trade history and update portfolio if executed
        if (mockExecution.quantity > 0) {
          const newTrade = {
            id: tradeHistory.length + 1,
            ticker: mockExecution.ticker,
            action: mockExecution.executedAction,
            quantity: mockExecution.quantity,
            price: mockExecution.price,
            status: "FILLED",
            riskScore: mockExecution.riskScore,
            reason: mockExecution.reason,
            timestamp: new Date().toLocaleString()
          }
          setTradeHistory([newTrade, ...tradeHistory])
          
          // Update portfolio positions
          setPortfolio(prevPortfolio => 
            prevPortfolio.map(position => {
              if (position.ticker === ticker) {
                const newShares = mockExecution.executedAction === 'BUY' 
                  ? position.shares + mockExecution.quantity
                  : Math.max(0, position.shares - mockExecution.quantity)
                
                const newCostBasis = mockExecution.executedAction === 'BUY'
                  ? ((position.shares * position.costBasis) + (mockExecution.quantity * mockExecution.price)) / newShares
                  : position.costBasis
                
                const newCurrentValue = newShares * mockExecution.price
                const totalCost = newShares * newCostBasis
                const newPnL = newCurrentValue - totalCost
                
                return {
                  ...position,
                  shares: newShares,
                  costBasis: parseFloat(newCostBasis.toFixed(2)),
                  currentValue: parseFloat(newCurrentValue.toFixed(0)),
                  pnl: parseFloat(newPnL.toFixed(0))
                }
              }
              return position
            })
          )
        }
      }
    } catch (error) {
      console.error('Trade execution failed:', error)
    } finally {
      setExecuting(false)
    }
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-black mb-4 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            ⚡ Trading Execution Engine
          </h1>
          <p className="text-xl text-black font-medium">
            AI-Powered Multi-Agent Trading System with Real-Time Execution
          </p>
        </div>
        
        {/* Portfolio Overview */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-2xl border-2 border-gray-200 p-6 shadow-xl">
            <h3 className="text-lg font-bold text-black mb-2">💰 Portfolio Value</h3>
            <div className="text-3xl font-bold text-black">${portfolioValue.toLocaleString()}</div>
          </div>
          <div className="bg-white rounded-2xl border-2 border-gray-200 p-6 shadow-xl">
            <h3 className="text-lg font-bold text-black mb-2">📈 Total P&L</h3>
            <div className={`text-3xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${totalPnL > 0 ? '+' : ''}{totalPnL.toLocaleString()}
            </div>
          </div>
          <div className="bg-white rounded-2xl border-2 border-gray-200 p-6 shadow-xl">
            <h3 className="text-lg font-bold text-black mb-2">🔄 Active Positions</h3>
            <div className="text-3xl font-bold text-black">{portfolio.length}</div>
          </div>
        </div>
        
        {/* Execution Results */}
        {executing && (
          <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 mb-8">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-4"></div>
              <span className="text-lg font-semibold text-blue-800">🤖 Executing Multi-Agent Trading Analysis...</span>
            </div>
          </div>
        )}
        
        {executionResults && (
          <div className="bg-white rounded-2xl border-2 border-gray-200 p-6 mb-8 shadow-xl">
            <h3 className="text-xl font-bold text-black mb-4">⚡ Execution Results</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="font-semibold">Ticker:</span>
                  <span className="font-bold text-lg">{executionResults.ticker}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Requested:</span>
                  <span className={`font-bold ${executionResults.requestedAction === 'BUY' ? 'text-green-600' : executionResults.requestedAction === 'SELL' ? 'text-red-600' : 'text-blue-600'}`}>
                    {executionResults.requestedAction}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Signal:</span>
                  <span className="font-bold">{executionResults.signalRecommendation} ({(executionResults.signalConfidence * 100).toFixed(0)}%)</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Risk Score:</span>
                  <span className={`font-bold ${executionResults.riskScore > 0.6 ? 'text-red-600' : 'text-green-600'}`}>
                    {(executionResults.riskScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="font-semibold">Executed:</span>
                  <span className={`font-bold text-lg ${executionResults.executedAction === 'BUY' ? 'text-green-600' : executionResults.executedAction === 'SELL' ? 'text-red-600' : 'text-black'}`}>
                    {executionResults.executedAction} {executionResults.quantity} shares
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Price:</span>
                  <span className="font-bold">${executionResults.price.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold">Total Value:</span>
                  <span className="font-bold">${(executionResults.price * executionResults.quantity).toLocaleString()}</span>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                  <span className="text-sm font-semibold">Reason:</span>
                  <p className="text-sm mt-1">{executionResults.reason}</p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Portfolio Positions */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-black mb-6">📊 Portfolio Positions</h2>
          <div className="grid lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {portfolio.map((position, idx) => (
              <PortfolioCard 
                key={idx}
                position={position}
                onTrade={handleTrade}
              />
            ))}
          </div>
        </div>
        
        {/* Trade History */}
        <div>
          <h2 className="text-2xl font-bold text-black mb-6">📜 Recent Trade Executions</h2>
          <div className="grid lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {tradeHistory.slice(0, 6).map((trade) => (
              <TradeExecutionCard key={trade.id} trade={trade} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
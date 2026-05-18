import { useState } from 'react'

const ConflictBadge = ({ level, score }) => {
  const getBadgeColor = (level) => {
    switch (level) {
      case 'high': return 'bg-gradient-to-r from-red-100 to-red-50 text-red-700 border border-red-200 shadow-sm'
      case 'medium': return 'bg-gradient-to-r from-yellow-100 to-yellow-50 text-yellow-700 border border-yellow-200 shadow-sm' 
      case 'low': return 'bg-gradient-to-r from-green-100 to-green-50 text-green-700 border border-green-200 shadow-sm'
      default: return 'bg-gradient-to-r from-gray-100 to-gray-50 text-gray-700 border border-gray-200 shadow-sm'
    }
  }
  
  return (
    <div className="flex items-center gap-2">
      <div className={`w-3 h-3 rounded-full ${level === 'high' ? 'bg-red-400' : level === 'medium' ? 'bg-yellow-400' : 'bg-green-400'}`}></div>
      <span className={`px-3 py-1.5 rounded-full text-sm font-semibold ${getBadgeColor(level)}`}>
        {level.toUpperCase()} ({score})
      </span>
    </div>
  )
}

const SignalStrengthMeter = ({ score, label }) => {
  const getColor = (score) => {
    if (score >= 0.7) return 'bg-green-500'
    if (score >= 0.55) return 'bg-green-400' 
    if (score >= 0.45) return 'bg-yellow-400'
    if (score >= 0.3) return 'bg-orange-400'
    return 'bg-red-400'
  }

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span>{label}</span>
        <span>{(score * 100).toFixed(0)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div 
          className={`h-2.5 rounded-full transition-all duration-500 ${getColor(score)}`}
          style={{ width: `${score * 100}%` }}
        ></div>
      </div>
    </div>
  )
}

const AgentCard = ({ finding, isConflicting }) => {
  const [expanded, setExpanded] = useState(false)
  
  const getScoreColor = (score) => {
    if (score >= 0.7) return 'text-green-700 bg-gradient-to-br from-green-50 to-green-100 border border-green-200 shadow-lg'
    if (score >= 0.55) return 'text-green-600 bg-gradient-to-br from-green-50 to-white border border-green-200 shadow-md'  
    if (score >= 0.45) return 'text-yellow-600 bg-gradient-to-br from-yellow-50 to-white border border-yellow-200 shadow-md'  
    return 'text-red-600 bg-gradient-to-br from-red-50 to-white border border-red-200 shadow-md'
  }

  const getSignalText = (score) => {
    if (score >= 0.55) return { text: 'BUY', icon: '📈' }
    if (score >= 0.45) return { text: 'HOLD', icon: '⏸️' }
    return { text: 'SELL', icon: '📉' }
  }

  const getAgentIcon = (agentName) => {
    switch (agentName) {
      case 'technical_analysis': return '📊'
      case 'news_sentiment': return '📰'
      case 'market_fear_greed': return '😰'
      default: return '🤖'
    }
  }

  const signal = getSignalText(finding.edge_score || 0)

  return (
    <div className={`bg-white rounded-xl border-2 transition-all duration-300 hover:shadow-xl ${
      isConflicting 
        ? 'border-red-200 bg-gradient-to-br from-red-50/50 to-white shadow-lg ring-1 ring-red-100' 
        : 'border-gray-200 hover:border-gray-300 shadow-md'
    }`}>
      
      {/* Header */}
      <div className="p-6 pb-4">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <div className="text-2xl">{getAgentIcon(finding.agent_name)}</div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">
                {finding.agent_name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </h3>
              {isConflicting && (
                <span className="text-xs text-red-600 font-medium">⚠️ Conflicting Signal</span>
              )}
            </div>
          </div>
          
          {finding.edge_score !== null && (
            <div className="text-right">
              <div className={`px-4 py-2 rounded-lg text-lg font-bold flex items-center gap-2 ${getScoreColor(finding.edge_score)}`}>
                <span>{signal.icon}</span>
                <span>{signal.text}</span>
              </div>
              <div className="text-xs text-gray-600 mt-1">
                Confidence: {(finding.edge_score * 100).toFixed(0)}%
              </div>
            </div>
          )}
        </div>

        {/* Signal Strength Meter */}
        {finding.edge_score !== null && (
          <div className="mb-4">
            <SignalStrengthMeter score={finding.edge_score} label="Signal Strength" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="px-6 pb-4">
        {/* Key Insights */}
        <div className="space-y-2 mb-4">
          {finding.insights.slice(0, expanded ? finding.insights.length : 2).map((insight, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
              <p className="text-sm text-gray-800 leading-relaxed">{insight}</p>
            </div>
          ))}
          
          {finding.insights.length > 2 && (
            <button 
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              {expanded ? '▲ Show less' : '▼ Show more insights'}
            </button>
          )}
        </div>
      </div>

      {/* Metrics Footer */}
      {Object.keys(finding.metrics).length > 0 && (
        <div className="border-t bg-gray-50/50 px-6 py-3 rounded-b-xl">
          <div className="grid grid-cols-2 gap-3 text-xs">
            {Object.entries(finding.metrics).slice(0, 4).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-600 font-medium">{key.replace('_', ' ')}:</span>
                <span className="font-bold text-gray-900">
                  {typeof value === 'number' 
                    ? (key.includes('price') || key.includes('target')) 
                      ? `$${value.toLocaleString()}` 
                      : value.toLocaleString() 
                    : value
                  }
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const ConflictAnalysis = ({ analysis, resolution }) => {
  const getConflictLevel = (score) => {
    if (score >= 0.5) return 'high'
    if (score >= 0.3) return 'medium'
    return 'low'
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b">
        <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
          <span>⚖️</span>
          Conflict Resolution Analysis
        </h3>
      </div>
      
      <div className="p-6">
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>🔍</span>
              Conflict Detection
            </h4>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-700 font-medium">Conflicts Present:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  analysis.has_conflicts 
                    ? 'bg-red-100 text-red-700 border border-red-200' 
                    : 'bg-green-100 text-green-700 border border-green-200'
                }`}>
                  {analysis.has_conflicts ? '⚠️ YES' : '✅ NO'}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-700 font-medium">Disagreement Level:</span>
                <ConflictBadge 
                  level={getConflictLevel(analysis.disagreement_score)} 
                  score={analysis.disagreement_score?.toFixed(3)} 
                />
              </div>
              
              {analysis.conflict_types?.length > 0 && (
                <div>
                  <span className="text-sm text-gray-700 font-medium mb-2 block">Conflict Types:</span>
                  <div className="flex flex-wrap gap-2">
                    {analysis.conflict_types.map((type, idx) => (
                      <span key={idx} className="inline-block bg-blue-100 text-blue-800 text-xs px-3 py-1 rounded-full font-medium border border-blue-200">
                        {type.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>🧮</span>
              Resolution Methods
            </h4>
            <div className="space-y-3">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-700 font-medium">Simple Average:</span>
                  <span className="font-bold text-gray-900 font-mono">{resolution.simple_average?.toFixed(3)}</span>
                </div>
              </div>
              
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="flex justify-between items-center">
                  <span className="text-blue-700 font-medium">Confidence Weighted:</span>
                  <span className="font-bold text-blue-900 font-mono">{resolution.confidence_weighted?.resolved_score?.toFixed(3)}</span>
                </div>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <div className="flex justify-between items-center">
                  <span className="text-purple-700 font-medium">Ensemble Voting:</span>
                  <span className="font-bold text-purple-900 uppercase">{resolution.ensemble_voting?.decision}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const FinalRecommendation = ({ recommendation, resolution }) => {
  const getRecommendationColor = (method) => {
    if (method.includes('warning')) return 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-200 text-yellow-800'
    if (method.includes('voting')) return 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 text-blue-800' 
    return 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200 text-green-800'
  }

  const getScoreDisplay = () => {
    if (recommendation.score) {
      const score = recommendation.score
      if (score >= 0.55) return { 
        text: 'BUY', 
        color: 'text-green-700 bg-gradient-to-br from-green-100 to-green-200 border border-green-300 shadow-lg', 
        icon: '🚀' 
      }
      if (score >= 0.45) return { 
        text: 'HOLD', 
        color: 'text-yellow-700 bg-gradient-to-br from-yellow-100 to-yellow-200 border border-yellow-300 shadow-lg', 
        icon: '⏸️' 
      }
      return { 
        text: 'SELL', 
        color: 'text-red-700 bg-gradient-to-br from-red-100 to-red-200 border border-red-300 shadow-lg', 
        icon: '📉' 
      }
    }
    
    if (recommendation.decision) {
      const decision = recommendation.decision.toUpperCase()
      if (decision === 'BUY') return { text: 'BUY', color: 'text-green-700 bg-gradient-to-br from-green-100 to-green-200 border border-green-300 shadow-lg', icon: '🚀' }
      if (decision === 'HOLD') return { text: 'HOLD', color: 'text-yellow-700 bg-gradient-to-br from-yellow-100 to-yellow-200 border border-yellow-300 shadow-lg', icon: '⏸️' }
      return { text: 'SELL', color: 'text-red-700 bg-gradient-to-br from-red-100 to-red-200 border border-red-300 shadow-lg', icon: '📉' }
    }
    
    return { text: 'HOLD', color: 'text-gray-600 bg-gray-100', icon: '⏸️' }
  }

  const scoreDisplay = getScoreDisplay()

  return (
    <div className={`rounded-xl border-2 p-6 shadow-lg ${getRecommendationColor(recommendation.method)}`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <span>🎯</span>
          Final Recommendation
        </h3>
        <div className={`px-6 py-3 rounded-xl font-bold text-2xl flex items-center gap-2 ${scoreDisplay.color}`}>
          <span>{scoreDisplay.icon}</span>
          <span>{scoreDisplay.text}</span>
        </div>
      </div>
      
      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <span className="font-semibold text-gray-800">Resolution Method:</span>
            <div className="mt-1 px-3 py-1 bg-white rounded-lg border text-sm font-mono">
              {recommendation.method.replace('_', ' ')}
            </div>
          </div>
          
          {recommendation.score && (
            <div>
              <span className="font-semibold text-gray-800">Confidence Score:</span>
              <div className="mt-2">
                <SignalStrengthMeter score={recommendation.score} label="Overall Confidence" />
                <span className="text-xs text-gray-600 mt-1 block">
                  System Confidence: {resolution.confidence_weighted?.confidence?.toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>
        
        <div>
          <span className="font-semibold text-gray-800 block mb-2">Analysis Summary:</span>
          <div className="bg-white rounded-lg p-4 border text-sm leading-relaxed">
            {recommendation.rationale}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function MarketSignalsEnhanced() {
  const [ticker, setTicker] = useState('SPY')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const analyzeSignals = async () => {
    if (!ticker.trim()) return

    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch('http://localhost:8001/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker: ticker.trim().toUpperCase() })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const data = await response.json()
      setResults(data.data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const conflictingAgents = results?.conflict_analysis?.conflicting_agents?.map(a => a.agent) || []

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4 flex items-center justify-center gap-3">
            <span className="text-5xl">📈</span>
            Enhanced Market Signal Analysis
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Premium UI for AI-powered multi-agent system with sophisticated conflict resolution
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-xl p-8 mb-8">
          <div className="max-w-md mx-auto">
            <label htmlFor="ticker" className="block text-lg font-semibold text-gray-800 mb-4 text-center">
              Enter Stock Ticker Symbol
            </label>
            <div className="flex gap-4">
              <input
                type="text"
                id="ticker"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                className="flex-1 px-6 py-4 text-lg font-mono border-2 border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                placeholder="e.g., AAPL, TSLA, SPY"
                maxLength={5}
                onKeyPress={(e) => e.key === 'Enter' && analyzeSignals()}
              />
              <button
                onClick={analyzeSignals}
                disabled={loading || !ticker.trim()}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-lg font-semibold rounded-xl hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                    Analyzing...
                  </div>
                ) : (
                  'Analyze 🚀'
                )}
              </button>
            </div>
          </div>
          
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl max-w-md mx-auto">
              <p className="text-red-700 text-center font-medium">{error}</p>
            </div>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-16">
            <div className="inline-block">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mb-4"></div>
              <p className="text-lg text-gray-600">Running 3 market signal agents...</p>
              <p className="text-sm text-gray-500 mt-2">Technical Analysis • News Sentiment • Market Psychology</p>
            </div>
          </div>
        )}

        {/* Results */}
        {results && !loading && (
          <div className="space-y-8">
            {/* Final Recommendation */}
            <FinalRecommendation 
              recommendation={results.final_recommendation}
              resolution={results.resolution_summary}
            />

            {/* Agent Analysis Grid */}
            <div>
              <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <span>🤖</span>
                Agent Analysis Results
              </h3>
              <div className="grid lg:grid-cols-3 gap-6">
                {results.agent_findings.map((finding, idx) => (
                  <AgentCard 
                    key={idx} 
                    finding={finding} 
                    isConflicting={conflictingAgents.includes(finding.agent_name)}
                  />
                ))}
              </div>
            </div>

            {/* Conflict Analysis */}
            <ConflictAnalysis 
              analysis={results.conflict_analysis}
              resolution={results.resolution_summary}
            />

            {/* Technical Details */}
            <div className="bg-white rounded-xl border border-gray-200 shadow-lg overflow-hidden">
              <details className="cursor-pointer">
                <summary className="px-6 py-4 bg-gray-50 border-b font-semibold text-gray-900 hover:bg-gray-100 transition-colors">
                  <span className="flex items-center gap-2">
                    <span>🔧</span>
                    Technical Details & Resolution Methods
                    <span className="text-xs text-gray-500 ml-auto">Click to expand</span>
                  </span>
                </summary>
                <div className="p-6">
                  <pre className="text-xs bg-gray-50 p-4 rounded-lg overflow-auto text-gray-700 border">
                    {JSON.stringify(results.resolution_summary, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
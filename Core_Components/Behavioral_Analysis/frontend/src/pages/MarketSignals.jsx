import { useState } from 'react'

const ConflictBadge = ({ level, score }) => {
  const getBadgeColor = (level) => {
    switch (level) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200' 
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }
  
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getBadgeColor(level)}`}>
      {level.toUpperCase()} ({score})
    </span>
  )
}

const AgentCard = ({ finding, isConflicting }) => {
  const getScoreColor = (score) => {
    if (score >= 0.7) return 'text-green-600 bg-green-50'
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  const getSignalText = (score) => {
    if (score >= 0.6) return 'BUY'
    if (score >= 0.4) return 'HOLD'
    return 'SELL'
  }

  return (
    <div className={`bg-white rounded-lg border p-6 ${isConflicting ? 'border-red-200 bg-red-50/30' : 'border-gray-200'}`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {finding.agent_name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </h3>
        {finding.edge_score !== null && (
          <div className="text-right">
            <div className={`px-3 py-1 rounded-md text-sm font-bold ${getScoreColor(finding.edge_score)}`}>
              {getSignalText(finding.edge_score)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Score: {finding.edge_score.toFixed(3)}
            </div>
          </div>
        )}
      </div>
      
      <div className="space-y-2 mb-4">
        {finding.insights.map((insight, idx) => (
          <p key={idx} className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
            {insight}
          </p>
        ))}
      </div>
      
      {Object.keys(finding.metrics).length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Metrics:</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(finding.metrics).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-500">{key.replace('_', ' ')}:</span>
                <span className="font-medium">{typeof value === 'number' ? value.toLocaleString() : value}</span>
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
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Conflict Resolution Analysis</h3>
      
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h4 className="font-medium text-gray-700 mb-3">Conflict Detection:</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Conflicts Present:</span>
              <span className={analysis.has_conflicts ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
                {analysis.has_conflicts ? 'YES' : 'NO'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Disagreement Level:</span>
              <ConflictBadge 
                level={getConflictLevel(analysis.disagreement_score)} 
                score={analysis.disagreement_score?.toFixed(3)} 
              />
            </div>
            {analysis.conflict_types?.length > 0 && (
              <div>
                <span className="text-sm text-gray-600">Conflict Types:</span>
                <div className="mt-1">
                  {analysis.conflict_types.map((type, idx) => (
                    <span key={idx} className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1">
                      {type.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div>
          <h4 className="font-medium text-gray-700 mb-3">Resolution Methods:</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Simple Average:</span>
              <span className="font-mono">{resolution.simple_average?.toFixed(3)}</span>
            </div>
            <div className="flex justify-between">
              <span>Confidence Weighted:</span>
              <span className="font-mono">{resolution.confidence_weighted?.resolved_score?.toFixed(3)}</span>
            </div>
            <div className="flex justify-between">
              <span>Ensemble Voting:</span>
              <span className="font-mono">{resolution.ensemble_voting?.decision?.toUpperCase()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const FinalRecommendation = ({ recommendation, resolution }) => {
  const getRecommendationColor = (method) => {
    if (method.includes('warning')) return 'bg-yellow-50 border-yellow-200 text-yellow-800'
    if (method.includes('voting')) return 'bg-blue-50 border-blue-200 text-blue-800' 
    return 'bg-green-50 border-green-200 text-green-800'
  }

  const getScoreDisplay = () => {
    if (recommendation.score) {
      const score = recommendation.score
      if (score >= 0.6) return { text: 'BUY', color: 'text-green-600 bg-green-100' }
      if (score >= 0.4) return { text: 'HOLD', color: 'text-yellow-600 bg-yellow-100' }
      return { text: 'SELL', color: 'text-red-600 bg-red-100' }
    }
    
    if (recommendation.decision) {
      const decision = recommendation.decision.toUpperCase()
      if (decision === 'BUY') return { text: 'BUY', color: 'text-green-600 bg-green-100' }
      if (decision === 'HOLD') return { text: 'HOLD', color: 'text-yellow-600 bg-yellow-100' }
      return { text: 'SELL', color: 'text-red-600 bg-red-100' }
    }
    
    return { text: 'HOLD', color: 'text-gray-600 bg-gray-100' }
  }

  const scoreDisplay = getScoreDisplay()

  return (
    <div className={`rounded-lg border p-6 ${getRecommendationColor(recommendation.method)}`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold">Final Recommendation</h3>
        <div className={`px-4 py-2 rounded-md font-bold text-lg ${scoreDisplay.color}`}>
          {scoreDisplay.text}
        </div>
      </div>
      
      <div className="space-y-3">
        <div>
          <span className="font-medium">Method Used: </span>
          <span className="font-mono text-sm">{recommendation.method.replace('_', ' ')}</span>
        </div>
        
        {recommendation.score && (
          <div>
            <span className="font-medium">Confidence Score: </span>
            <span className="font-mono">{recommendation.score.toFixed(3)}</span>
            <span className="text-sm text-gray-600 ml-2">
              (Confidence: {resolution.confidence_weighted?.confidence?.toFixed(3)})
            </span>
          </div>
        )}
        
        <div>
          <span className="font-medium">Rationale: </span>
          <span className="text-sm">{recommendation.rationale}</span>
        </div>
      </div>
    </div>
  )
}

export default function MarketSignals() {
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
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Market Signal Analysis</h1>
        <p className="text-gray-600">Multi-agent conflict resolution for investment decisions</p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label htmlFor="ticker" className="block text-sm font-medium text-gray-700 mb-2">
              Stock Ticker
            </label>
            <input
              type="text"
              id="ticker"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              placeholder="Enter ticker (e.g., AAPL, TSLA, SPY)"
              maxLength={5}
            />
          </div>
          <button
            onClick={analyzeSignals}
            disabled={loading || !ticker.trim()}
            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Analyze Signals'}
          </button>
        </div>
        
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mb-4"></div>
          <p className="text-gray-600">Running 3 market signal agents...</p>
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

          {/* Conflict Analysis */}
          <ConflictAnalysis 
            analysis={results.conflict_analysis}
            resolution={results.resolution_summary}
          />

          {/* Agent Findings */}
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-6">Agent Analysis Results</h3>
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

          {/* Technical Details */}
          <div className="bg-gray-50 rounded-lg p-6">
            <details className="cursor-pointer">
              <summary className="font-medium text-gray-900 mb-4">
                Technical Details & Resolution Methods
              </summary>
              <pre className="text-xs bg-white p-4 rounded border overflow-auto text-gray-700">
                {JSON.stringify(results.resolution_summary, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}
    </div>
  )
}
import { useState } from 'react'

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

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">Market Signal Analysis</h1>
      
      <div className="mb-8">
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Enter ticker (e.g., AAPL, TSLA, SPY)"
            className="border rounded px-3 py-2 flex-1"
            maxLength={5}
          />
          <button
            onClick={analyzeSignals}
            disabled={loading || !ticker.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
      </div>

      {results && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Final Recommendation</h2>
            <div className="text-lg">
              <strong>{results.final_recommendation.decision || 'HOLD'}</strong>
            </div>
            <p className="text-gray-600 mt-2">{results.final_recommendation.rationale}</p>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Agent Findings</h2>
            {results.agent_findings.map((finding, idx) => (
              <div key={idx} className="mb-4 p-4 border rounded">
                <h3 className="font-medium">{finding.agent_name.replace('_', ' ').toUpperCase()}</h3>
                <div className="mt-2">
                  {finding.insights.map((insight, i) => (
                    <p key={i} className="text-sm text-gray-700">{insight}</p>
                  ))}
                </div>
                {finding.edge_score && (
                  <p className="mt-2 text-sm">Score: {finding.edge_score.toFixed(3)}</p>
                )}
              </div>
            ))}
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Conflict Analysis</h2>
            <p>Conflicts Present: {results.conflict_analysis.has_conflicts ? 'YES' : 'NO'}</p>
            <p>Disagreement Level: {results.conflict_analysis.disagreement_score?.toFixed(3)}</p>
          </div>
        </div>
      )}
    </div>
  )
}
import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface Statistics {
  total_analyses: number
  average_confidence: number
  consensus_distribution: Record<string, number>
  high_risk_count: number
}

function Dashboard() {
  const [stats, setStats] = useState<Statistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStatistics()
  }, [])

  const fetchStatistics = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/v1/history/statistics?days=7')
      setStats(response.data)
      setError(null)
    } catch (err) {
      setError('Failed to load statistics')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">System-wide signal consensus analysis</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-500 text-sm font-medium">Total Analyses</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {stats?.total_analyses || 0}
          </p>
          <p className="text-gray-500 text-sm mt-2">Last 7 days</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-500 text-sm font-medium">Average Confidence</h3>
          <p className="text-3xl font-bold text-blue-600 mt-2">
            {Math.round(stats?.average_confidence || 0)}%
          </p>
          <p className="text-gray-500 text-sm mt-2">Triangulated score</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-500 text-sm font-medium">High Risk Signals</h3>
          <p className="text-3xl font-bold text-red-600 mt-2">
            {stats?.high_risk_count || 0}
          </p>
          <p className="text-gray-500 text-sm mt-2">Require investigation</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-500 text-sm font-medium">Consensus Level</h3>
          <p className="text-3xl font-bold text-green-600 mt-2">
            {stats?.consensus_distribution?.UNANIMOUS || 0}
          </p>
          <p className="text-gray-500 text-sm mt-2">Unanimous agreements</p>
        </div>
      </div>

      {/* Consensus Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Consensus Distribution</h2>
        <div className="space-y-4">
          {stats?.consensus_distribution && Object.entries(stats.consensus_distribution).map(([level, count]) => (
            <div key={level}>
              <div className="flex justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">{level}</span>
                <span className="text-sm font-medium text-gray-900">{count}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    level === 'UNANIMOUS' ? 'bg-green-600' :
                    level === 'HIGH' ? 'bg-blue-600' :
                    level === 'MEDIUM' ? 'bg-yellow-600' :
                    level === 'CONFLICTING' ? 'bg-orange-600' :
                    'bg-red-600'
                  }`}
                  style={{
                    width: `${((count / (stats.total_analyses || 1)) * 100)}%`
                  }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">System Status</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="border-l-4 border-green-600 pl-4 py-2">
            <p className="text-sm text-gray-600">Backend Status</p>
            <p className="text-lg font-semibold text-green-600">🟢 Operational</p>
          </div>
          <div className="border-l-4 border-blue-600 pl-4 py-2">
            <p className="text-sm text-gray-600">Database Status</p>
            <p className="text-lg font-semibold text-blue-600">🟢 Connected</p>
          </div>
          <div className="border-l-4 border-purple-600 pl-4 py-2">
            <p className="text-sm text-gray-600">Signal Agents</p>
            <p className="text-lg font-semibold text-purple-600">🟢 Available</p>
          </div>
          <div className="border-l-4 border-indigo-600 pl-4 py-2">
            <p className="text-sm text-gray-600">API Version</p>
            <p className="text-lg font-semibold text-indigo-600">v0.1.0</p>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchStatistics}
        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
      >
        Refresh Data
      </button>
    </div>
  )
}

export default Dashboard

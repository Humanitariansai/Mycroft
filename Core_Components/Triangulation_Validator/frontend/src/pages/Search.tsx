import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface Signal {
  id: number
  companyName: string
  agentName: string
  signalText: string
  confidence: number
  signalType: string
}

interface SearchResults {
  total_results: number
  signals: Signal[]
  page: number
  size: number
  total_pages: number
}

function Search() {
  const [filters, setFilters] = useState({
    company: '',
    agent: '',
    type: '',
    minConfidence: '',
    maxConfidence: ''
  })

  const [companies, setCompanies] = useState<string[]>([])
  const [agents, setAgents] = useState<string[]>([])
  const [types, setTypes] = useState<string[]>([])
  const [results, setResults] = useState<SearchResults | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadFilterOptions()
  }, [])

  const loadFilterOptions = async () => {
    try {
      const [companiesRes, agentsRes, typesRes] = await Promise.all([
        axios.get('/api/v1/search/companies'),
        axios.get('/api/v1/search/agents'),
        axios.get('/api/v1/search/types')
      ])

      setCompanies(companiesRes.data.companies)
      setAgents(agentsRes.data.agents)
      setTypes(typesRes.data.types)
    } catch (err) {
      setError('Failed to load filter options')
    }
  }

  const handleSearch = async (page = 0) => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      if (filters.company) params.append('company', filters.company)
      if (filters.agent) params.append('agentName', filters.agent)
      if (filters.type) params.append('signalType', filters.type)
      if (filters.minConfidence) params.append('minConfidence', filters.minConfidence)
      if (filters.maxConfidence) params.append('maxConfidence', filters.maxConfidence)
      params.append('page', page.toString())
      params.append('size', '20')

      const response = await axios.post(`/api/v1/search/signals?${params}`)
      setResults(response.data)
    } catch (err) {
      setError('Failed to search signals')
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-gray-900">Signal Search</h1>
        <p className="text-gray-600 mt-2">Advanced search and filtering for investment signals</p>
      </div>

      {/* Search Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Search Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
            <select
              value={filters.company}
              onChange={(e) => handleFilterChange('company', e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">All Companies</option>
              {companies.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Agent</label>
            <select
              value={filters.agent}
              onChange={(e) => handleFilterChange('agent', e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">All Agents</option>
              {agents.map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Signal Type</label>
            <select
              value={filters.type}
              onChange={(e) => handleFilterChange('type', e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">All Types</option>
              {types.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Confidence</label>
            <input
              type="number"
              min="0"
              max="100"
              value={filters.minConfidence}
              onChange={(e) => handleFilterChange('minConfidence', e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
              placeholder="0"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Confidence</label>
            <input
              type="number"
              min="0"
              max="100"
              value={filters.maxConfidence}
              onChange={(e) => handleFilterChange('maxConfidence', e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2"
              placeholder="100"
            />
          </div>
        </div>

        <button
          onClick={() => handleSearch(0)}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : results ? (
        <div className="space-y-6">
          <div className="bg-gray-100 rounded-lg p-4">
            <p className="text-gray-700">
              Found <span className="font-bold">{results.total_results}</span> signals
              ({results.page + 1} of {results.total_pages} pages)
            </p>
          </div>

          {/* Results Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {results.signals.length > 0 ? (
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Company</th>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Agent</th>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Signal</th>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Type</th>
                    <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {results.signals.map((signal) => (
                    <tr key={signal.id} className="border-b hover:bg-gray-50">
                      <td className="px-6 py-4 font-semibold text-gray-900">{signal.companyName}</td>
                      <td className="px-6 py-4 text-gray-700">{signal.agentName}</td>
                      <td className="px-6 py-4 text-gray-700">{signal.signalText}</td>
                      <td className="px-6 py-4">
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                          {signal.signalType}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="h-2 rounded-full bg-blue-600"
                              style={{ width: `${signal.confidence}%` }}
                            ></div>
                          </div>
                          <span className="font-semibold text-gray-900">{signal.confidence}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-gray-600">
                No signals found matching your criteria
              </div>
            )}
          </div>

          {/* Pagination */}
          {results.total_pages > 1 && (
            <div className="flex justify-center space-x-2">
              {Array.from({ length: results.total_pages }, (_, i) => (
                <button
                  key={i}
                  onClick={() => handleSearch(i)}
                  className={`px-4 py-2 rounded transition-colors ${
                    results.page === i
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}

export default Search

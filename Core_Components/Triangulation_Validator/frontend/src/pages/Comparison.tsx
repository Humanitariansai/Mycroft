import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface CompanyComparison {
  [key: string]: {
    consensusLevel: string
    triangulatedConfidence: number
    riskLevel: string
    recommendation: string
    lastUpdated: string
  }
}

function Comparison() {
  const [companies, setCompanies] = useState<string[]>([])
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([])
  const [comparisonData, setComparisonData] = useState<CompanyComparison | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCompanies()
  }, [])

  const fetchCompanies = async () => {
    try {
      const response = await axios.get('/api/v1/search/companies')
      setCompanies(response.data.companies)
    } catch (err) {
      setError('Failed to load companies')
    }
  }

  const toggleCompany = (company: string) => {
    setSelectedCompanies(prev =>
      prev.includes(company)
        ? prev.filter(c => c !== company)
        : [...prev, company]
    )
  }

  const compareCompanies = async () => {
    if (selectedCompanies.length === 0) {
      setError('Please select at least one company')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await axios.post('/api/v1/history/compare', selectedCompanies)
      setComparisonData(response.data.comparison_data)
    } catch (err) {
      setError('Failed to compare companies')
    } finally {
      setLoading(false)
    }
  }

  const getConsensusScore = (level: string) => {
    const scores: Record<string, number> = {
      'UNANIMOUS': 5,
      'HIGH': 4,
      'MEDIUM': 3,
      'CONFLICTING': 2,
      'WEAK': 1,
      'NO_DATA': 0
    }
    return scores[level] || 0
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-gray-900">Company Comparison</h1>
        <p className="text-gray-600 mt-2">Compare triangulation results across multiple companies</p>
      </div>

      {/* Company Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Select Companies to Compare</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {companies.map((company) => (
            <label key={company} className="flex items-center">
              <input
                type="checkbox"
                checked={selectedCompanies.includes(company)}
                onChange={() => toggleCompany(company)}
                className="rounded"
              />
              <span className="ml-2 text-gray-700">{company}</span>
            </label>
          ))}
        </div>
        <button
          onClick={compareCompanies}
          disabled={loading || selectedCompanies.length === 0}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
        >
          {loading ? 'Comparing...' : 'Compare'}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Comparison Results */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : comparisonData ? (
        <div className="space-y-6">
          {/* Comparison Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Company</th>
                  <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Consensus</th>
                  <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Confidence</th>
                  <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Risk</th>
                  <th className="px-6 py-3 text-left text-sm font-bold text-gray-900">Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparisonData).map(([company, data]) => (
                  <tr key={company} className="border-b hover:bg-gray-50">
                    <td className="px-6 py-4 font-semibold text-gray-900">{company}</td>
                    <td className="px-6 py-4">
                      <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                        {data.consensusLevel}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-bold text-blue-600">{data.triangulatedConfidence}%</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        data.riskLevel === 'LOW' ? 'bg-green-100 text-green-800' :
                        data.riskLevel === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {data.riskLevel}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-700">{data.recommendation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Ranking */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Consensus Ranking</h3>
            <div className="space-y-3">
              {Object.entries(comparisonData)
                .sort((a, b) =>
                  getConsensusScore(b[1].consensusLevel) - getConsensusScore(a[1].consensusLevel)
                )
                .map(([company, data], index) => (
                  <div key={company} className="flex items-center space-x-4">
                    <div className="text-2xl font-bold text-gray-400 w-8 text-center">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-gray-900">{company}</p>
                      <p className="text-sm text-gray-600">{data.consensusLevel}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-blue-600">{data.triangulatedConfidence}%</p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default Comparison

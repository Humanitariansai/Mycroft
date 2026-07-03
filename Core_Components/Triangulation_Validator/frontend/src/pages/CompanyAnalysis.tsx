import React, { useState, useEffect } from 'react'
import axios from 'axios'

interface Company {
  company: string
  consensusLevel: string
  triangulatedConfidence: number
  recommendation: string
  riskLevel: string
}

function CompanyAnalysis() {
  const [companies, setCompanies] = useState<string[]>([])
  const [selectedCompany, setSelectedCompany] = useState<string>('')
  const [analysis, setAnalysis] = useState<Company | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCompanies()
  }, [])

  const fetchCompanies = async () => {
    try {
      const response = await axios.get('/api/v1/search/companies')
      setCompanies(response.data.companies)
      if (response.data.companies.length > 0) {
        setSelectedCompany(response.data.companies[0])
      }
    } catch (err) {
      setError('Failed to load companies')
    }
  }

  const analyzeCompany = async (company: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.post(`/api/v1/analyze/${company}`)
      setAnalysis(response.data)
    } catch (err) {
      setError('Failed to analyze company')
    } finally {
      setLoading(false)
    }
  }

  const handleCompanySelect = (company: string) => {
    setSelectedCompany(company)
    analyzeCompany(company)
  }

  const getConsensusColor = (level: string) => {
    switch (level) {
      case 'UNANIMOUS': return 'bg-green-100 text-green-800'
      case 'HIGH': return 'bg-blue-100 text-blue-800'
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800'
      case 'CONFLICTING': return 'bg-orange-100 text-orange-800'
      default: return 'bg-red-100 text-red-800'
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'bg-green-100 text-green-800'
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800'
      case 'HIGH': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-gray-900">Company Analysis</h1>
        <p className="text-gray-600 mt-2">Detailed triangulation analysis for individual companies</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Company List */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Companies</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {companies.map((company) => (
              <button
                key={company}
                onClick={() => handleCompanySelect(company)}
                className={`w-full text-left px-4 py-2 rounded transition-colors ${
                  selectedCompany === company
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}
              >
                {company}
              </button>
            ))}
          </div>
        </div>

        {/* Analysis Results */}
        <div className="lg:col-span-3">
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800">{error}</p>
            </div>
          ) : analysis ? (
            <div className="space-y-6">
              {/* Company Header */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-3xl font-bold text-gray-900">{analysis.company}</h2>
                <p className="text-gray-600 mt-2">Latest triangulation analysis</p>
              </div>

              {/* Key Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-gray-500 text-sm font-medium">Consensus Level</h3>
                  <span className={`inline-block mt-2 px-4 py-2 rounded-full font-bold ${getConsensusColor(analysis.consensusLevel)}`}>
                    {analysis.consensusLevel}
                  </span>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-gray-500 text-sm font-medium">Confidence Score</h3>
                  <p className="text-3xl font-bold text-blue-600 mt-2">
                    {analysis.triangulatedConfidence}%
                  </p>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-gray-500 text-sm font-medium">Risk Level</h3>
                  <span className={`inline-block mt-2 px-4 py-2 rounded-full font-bold ${getRiskColor(analysis.riskLevel)}`}>
                    {analysis.riskLevel}
                  </span>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-gray-500 text-sm font-medium">Recommendation</h3>
                  <p className="text-lg font-bold text-gray-900 mt-2">
                    {analysis.recommendation}
                  </p>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Confidence Level</h3>
                <div className="w-full bg-gray-200 rounded-full h-8">
                  <div
                    className="h-8 rounded-full bg-gradient-to-r from-blue-400 to-blue-600 flex items-center justify-end pr-2 transition-all"
                    style={{ width: `${analysis.triangulatedConfidence}%` }}
                  >
                    <span className="text-white font-bold text-sm">
                      {analysis.triangulatedConfidence}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Signal Summary */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Analysis Summary</h3>
                <p className="text-gray-700">
                  Based on consensus from multiple Mycroft agents, {analysis.company} shows{' '}
                  <span className="font-semibold">{analysis.consensusLevel}</span> consensus with a{' '}
                  <span className="font-semibold">{analysis.triangulatedConfidence}%</span> confidence score.
                  {' '}
                  <span className="font-semibold">{analysis.recommendation}</span> is recommended.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <p className="text-gray-600">Select a company to view analysis</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CompanyAnalysis

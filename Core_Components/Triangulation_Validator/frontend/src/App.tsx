import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import CompanyAnalysis from './pages/CompanyAnalysis'
import Comparison from './pages/Comparison'
import Search from './pages/Search'
import './App.css'

function App() {
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Check backend connection
    fetch('/api/v1/health')
      .then(() => setIsConnected(true))
      .catch(() => setIsConnected(false))
  }, [])

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link to="/" className="text-2xl font-bold text-blue-600">
                  Triangulation Validator
                </Link>
              </div>
              <div className="flex items-center space-x-4">
                <Link to="/" className="px-3 py-2 text-gray-700 hover:text-blue-600">
                  Dashboard
                </Link>
                <Link to="/companies" className="px-3 py-2 text-gray-700 hover:text-blue-600">
                  Analysis
                </Link>
                <Link to="/comparison" className="px-3 py-2 text-gray-700 hover:text-blue-600">
                  Compare
                </Link>
                <Link to="/search" className="px-3 py-2 text-gray-700 hover:text-blue-600">
                  Search
                </Link>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  isConnected
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {isConnected ? '🟢 Connected' : '🔴 Offline'}
                </span>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/companies" element={<CompanyAnalysis />} />
            <Route path="/comparison" element={<Comparison />} />
            <Route path="/search" element={<Search />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-gray-800 text-white mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="grid grid-cols-3 gap-8">
              <div>
                <h3 className="text-lg font-bold mb-2">Triangulation Validator</h3>
                <p className="text-gray-400">Signal consensus validation for Mycroft Framework</p>
              </div>
              <div>
                <h4 className="text-lg font-bold mb-2">Features</h4>
                <ul className="text-gray-400 space-y-1">
                  <li>Consensus Validation</li>
                  <li>Signal Analysis</li>
                  <li>Risk Assessment</li>
                </ul>
              </div>
              <div>
                <h4 className="text-lg font-bold mb-2">Documentation</h4>
                <ul className="text-gray-400 space-y-1">
                  <li>API Docs</li>
                  <li>User Guide</li>
                  <li>Architecture</li>
                </ul>
              </div>
            </div>
            <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
              <p>&copy; 2026 Mycroft Framework. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  )
}

export default App

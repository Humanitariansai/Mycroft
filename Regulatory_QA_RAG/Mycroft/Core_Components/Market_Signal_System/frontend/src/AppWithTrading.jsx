import { useState } from 'react'
import MarketSignals from './pages/MarketSignals'
import TradingExecution from './pages/TradingExecution'

export default function AppWithTrading() {
  const [activeTab, setActiveTab] = useState('signals')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-lg border-b-2 border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('signals')}
              className={`py-4 px-6 border-b-4 font-bold text-lg transition-all ${
                activeTab === 'signals'
                  ? 'border-blue-500 text-blue-600 bg-blue-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              🔍 Market Signal Analysis
            </button>
            <button
              onClick={() => setActiveTab('execution')}
              className={`py-4 px-6 border-b-4 font-bold text-lg transition-all ${
                activeTab === 'execution'
                  ? 'border-purple-500 text-purple-600 bg-purple-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              ⚡ Trading Execution
            </button>
          </div>
        </div>
      </nav>

      {/* Tab Content */}
      <main>
        {activeTab === 'signals' && <MarketSignals />}
        {activeTab === 'execution' && <TradingExecution />}
      </main>
    </div>
  )
}
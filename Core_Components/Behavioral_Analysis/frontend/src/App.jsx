import { useState } from 'react'
import Upload from './pages/Upload'
import Results from './pages/Results'
import MarketSignals from './pages/MarketSignals'

export default function App() {
  const [report, setReport] = useState(null)
  const [currentView, setCurrentView] = useState('behavioral') // 'behavioral' or 'signals'

  const NavBar = () => (
    <div className="bg-gray-100 border-b border-gray-200 p-4 mb-6">
      <div className="flex space-x-4">
        <button 
          onClick={() => setCurrentView('behavioral')}
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            currentView === 'behavioral' 
              ? 'bg-blue-600 text-white' 
              : 'bg-white text-gray-700 hover:bg-gray-50 border'
          }`}
        >
          Behavioral Analysis
        </button>
        <button 
          onClick={() => setCurrentView('signals')}
          className={`px-4 py-2 rounded-md font-medium transition-colors ${
            currentView === 'signals' 
              ? 'bg-green-600 text-white' 
              : 'bg-white text-gray-700 hover:bg-gray-50 border'
          }`}
        >
          Market Signals
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      {currentView === 'behavioral' ? (
        report
          ? <Results report={report} onReset={() => setReport(null)} />
          : <Upload onReport={setReport} />
      ) : (
        <MarketSignals />
      )}
    </div>
  )
}
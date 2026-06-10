import React, { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import { talentAPI } from './services/api';
import { AlertCircle, Wifi, WifiOff } from 'lucide-react';

function App() {
  const [apiStatus, setApiStatus] = useState('checking');
  const [error, setError] = useState(null);

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await talentAPI.getHealth();
      if (response.data.status === 'healthy') {
        setApiStatus('connected');
        setError(null);
      } else {
        setApiStatus('error');
        setError('API returned unhealthy status');
      }
    } catch (err) {
      setApiStatus('disconnected');
      setError('Cannot connect to AI Talent Flow Intelligence API. Make sure the backend is running on port 8004.');
    }
  };

  if (apiStatus === 'checking') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-talent-primary mx-auto mb-4"></div>
          <p className="text-black">Connecting to AI Talent Flow Intelligence...</p>
        </div>
      </div>
    );
  }

  if (apiStatus === 'disconnected' || apiStatus === 'error') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center">
          <div className="bg-white rounded-xl border border-gray-200 shadow-lg p-8">
            <div className="flex justify-center mb-4">
              <div className="p-3 bg-red-100 rounded-full">
                <WifiOff className="w-8 h-8 text-red-600" />
              </div>
            </div>
            
            <h2 className="text-2xl font-bold text-black mb-2">Connection Error</h2>
            <p className="text-black opacity-75 mb-6">{error}</p>
            
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
                <h3 className="font-semibold text-blue-800 mb-2">To start the backend:</h3>
                <div className="text-sm text-blue-700 font-mono bg-blue-100 p-2 rounded">
                  cd Core_Components/AI_Talent_Flow_Intelligence/backend<br/>
                  python3 simple_main.py
                </div>
              </div>
              
              <button
                onClick={checkApiHealth}
                className="w-full bg-talent-primary text-white py-2 px-4 rounded-lg font-medium hover:bg-talent-secondary transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      {/* Connection Status Bar */}
      <div className="bg-green-50 border-b border-green-200 px-4 py-2">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2 text-green-800">
            <Wifi className="w-4 h-4" />
            <span className="text-sm font-medium">Connected to AI Talent Flow Intelligence API</span>
          </div>
          
          <div className="flex items-center space-x-4 text-xs text-green-700">
            <span>Backend: localhost:8002</span>
            <span>Frontend: localhost:5174</span>
          </div>
        </div>
      </div>

      {/* Main Dashboard */}
      <Dashboard />
    </div>
  );
}

export default App;
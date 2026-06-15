import React, { useState, useEffect } from 'react';
import { RefreshCw, Users, TrendingUp, AlertCircle, Zap, Activity, Eye } from 'lucide-react';
import TalentCard from '../components/TalentCard';
import MovementCard from '../components/MovementCard';
import SignalCard from '../components/SignalCard';
import { talentAPI } from '../services/api';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    talents: [],
    movements: [],
    signals: [],
    summary: {},
    trends: {}
  });
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [talents, movements, signals, summary, trends] = await Promise.all([
        talentAPI.getTalentProfiles(),
        talentAPI.getTalentMovements(),
        talentAPI.getRecentSignals(),
        talentAPI.getMovementSummary(),
        talentAPI.getMovementTrends(),
      ]);

      setData({
        talents: talents.data || [],
        movements: movements.data || [],
        signals: signals.data || [],
        summary: summary.data || {},
        trends: trends.data || {}
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const handleGenerateDemo = async () => {
    try {
      await talentAPI.generateDemoMovement();
      await loadDashboardData(); // Refresh to show new data
    } catch (error) {
      console.error('Failed to generate demo movement:', error);
    }
  };

  const handleExecuteTrade = (signal) => {
    // This would integrate with the Trading Execution Agent
    console.log('Executing trade for signal:', signal);
    alert(`Trade execution initiated for ${signal.ticker_symbol}: ${signal.recommended_action}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-talent-primary mx-auto mb-4"></div>
          <p className="text-black">Loading Talent Intelligence...</p>
        </div>
      </div>
    );
  }

  const StatCard = ({ title, value, icon: Icon, subtitle, color = "talent-primary" }) => (
    <div className="metric-card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-white opacity-90 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-white opacity-75 text-xs mt-1">{subtitle}</p>}
        </div>
        <Icon className="h-8 w-8 text-white opacity-75" />
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-black">AI Talent Flow Intelligence</h1>
              <p className="text-black opacity-75 mt-1">Track talent movements to predict market shifts</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={handleGenerateDemo}
                className="px-4 py-2 bg-talent-secondary text-white rounded-lg font-medium hover:bg-opacity-90 transition-colors"
              >
                Generate Demo Movement
              </button>
              
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center space-x-2 px-4 py-2 bg-talent-primary text-white rounded-lg font-medium hover:bg-opacity-90 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8">
              {[
                { id: 'overview', label: 'Overview', icon: Activity },
                { id: 'talents', label: 'Talent Profiles', icon: Users },
                { id: 'movements', label: 'Recent Movements', icon: TrendingUp },
                { id: 'signals', label: 'Investment Signals', icon: AlertCircle },
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === id
                      ? 'border-talent-primary text-talent-primary'
                      : 'border-transparent text-black hover:text-talent-primary hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title="Tracked Talents"
                value={data.talents.length}
                icon={Users}
                subtitle="AI professionals monitored"
              />
              <StatCard
                title="Recent Movements"
                value={data.summary.total_movements || 0}
                icon={TrendingUp}
                subtitle="Last 30 days"
              />
              <StatCard
                title="Investment Signals"
                value={data.signals.length}
                icon={AlertCircle}
                subtitle="Active recommendations"
              />
              <StatCard
                title="Avg Confidence"
                value={`${((data.summary.average_confidence || 0) * 100).toFixed(0)}%`}
                icon={Zap}
                subtitle="Signal reliability"
              />
            </div>

            {/* Quick Overview Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Top Signals */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-xl font-bold text-black flex items-center">
                    <AlertCircle className="w-5 h-5 mr-2 text-talent-primary" />
                    Latest Investment Signals
                  </h3>
                </div>
                <div className="card-content space-y-4">
                  {data.signals.slice(0, 3).map((signal, index) => (
                    <SignalCard 
                      key={index} 
                      signal={signal} 
                      onExecute={handleExecuteTrade}
                    />
                  ))}
                  {data.signals.length === 0 && (
                    <p className="text-black opacity-75 text-center py-8">No active signals</p>
                  )}
                </div>
              </div>

              {/* Recent Movements */}
              <div className="card">
                <div className="card-header">
                  <h3 className="text-xl font-bold text-black flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2 text-talent-primary" />
                    Recent Talent Movements
                  </h3>
                </div>
                <div className="card-content space-y-4">
                  {data.movements.slice(0, 2).map((movement, index) => (
                    <MovementCard key={index} movement={movement} />
                  ))}
                  {data.movements.length === 0 && (
                    <p className="text-black opacity-75 text-center py-8">No recent movements</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Talent Profiles Tab */}
        {activeTab === 'talents' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-black">Talent Profiles</h2>
              <div className="text-sm text-black opacity-75">
                {data.talents.length} profiles tracked
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {data.talents.map((talent) => (
                <TalentCard 
                  key={talent.id} 
                  talent={talent}
                  onClick={(talent) => console.log('View talent details:', talent)}
                />
              ))}
            </div>
            
            {data.talents.length === 0 && (
              <div className="text-center py-12">
                <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-black opacity-75">No talent profiles available</p>
              </div>
            )}
          </div>
        )}

        {/* Movements Tab */}
        {activeTab === 'movements' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-black">Recent Talent Movements</h2>
              <div className="text-sm text-black opacity-75">
                {data.movements.length} movements detected
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {data.movements.map((movement, index) => (
                <MovementCard key={index} movement={movement} />
              ))}
            </div>
            
            {data.movements.length === 0 && (
              <div className="text-center py-12">
                <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-black opacity-75">No recent movements detected</p>
              </div>
            )}
          </div>
        )}

        {/* Signals Tab */}
        {activeTab === 'signals' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-black">Investment Signals</h2>
              <div className="text-sm text-black opacity-75">
                {data.signals.length} active signals
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {data.signals.map((signal, index) => (
                <SignalCard 
                  key={index} 
                  signal={signal} 
                  onExecute={handleExecuteTrade}
                />
              ))}
            </div>
            
            {data.signals.length === 0 && (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-black opacity-75">No investment signals available</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
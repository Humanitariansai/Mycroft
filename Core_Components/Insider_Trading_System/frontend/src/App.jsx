import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  DollarSign, 
  Activity,
  Search,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  BarChart3,
  PieChart,
  ChevronDown,
  ExternalLink,
  X,
  Settings as SettingsIcon
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from 'recharts';

const API_BASE = 'http://localhost:8000';
const N8N_WEBHOOK = 'http://localhost:5678/webhook/capitol-trades-scan'; // Configure this

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [trades, setTrades] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState(N8N_WEBHOOK);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    party: '',
    transaction_type: '',
  });

  useEffect(() => {
    loadStats();
    loadTrades();
    
    // Load webhook URL from localStorage if available
    const savedWebhook = localStorage.getItem('n8n_webhook_url');
    if (savedWebhook) {
      setWebhookUrl(savedWebhook);
    }
  }, []);

  const loadStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      const data = await res.json();
      console.log('Stats data:', data); // Debug log
      setStats(data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const loadTrades = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/trades`);
      const data = await res.json();
      console.log('Trades data:', data); // Debug log
      setTrades(data.trades || []);
    } catch (err) {
      console.error('Error loading trades:', err);
    }
  };

  const startScrape = async () => {
    if (!webhookUrl) {
      alert('Please configure n8n webhook URL first');
      return;
    }
    
    try {
      setLoading(true);
      
      // Call n8n webhook to trigger the workflow
      const res = await fetch(webhookUrl, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trigger: 'scan',
          timestamp: new Date().toISOString()
        })
      });
      
      if (!res.ok) {
        throw new Error('Failed to trigger workflow');
      }
      
      alert('Scan started! The workflow will scrape and analyze trades. Refresh the page in a few minutes to see results.');
      
      // Reload data after a delay
      setTimeout(() => {
        loadStats();
        loadTrades();
      }, 5000);
      
    } catch (err) {
      console.error('Error starting scrape:', err);
      alert('Failed to start scraping. Make sure n8n webhook URL is correct.');
    } finally {
      setLoading(false);
    }
  };

  const filteredTrades = trades.filter(trade => {
    const matchesSearch = !searchTerm || 
      trade.politician?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trade.ticker?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesParty = !filters.party || trade.party === filters.party;
    const matchesType = !filters.transaction_type || 
      trade.transaction_type?.toLowerCase().includes(filters.transaction_type.toLowerCase());
    
    return matchesSearch && matchesParty && matchesType;
  });

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f1419', color: '#e4e6eb' }}>
      {/* Sidebar */}
      <aside style={{ width: '200px', background: '#1a1f2e', borderRight: '1px solid #2d3748', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px 16px', borderBottom: '1px solid #2d3748' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} style={{ color: '#3b82f6' }} />
            <div>
              <h1 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '2px' }}>Capitol Trades</h1>
              <p style={{ fontSize: '11px', color: '#6b7280' }}>Analytics</p>
            </div>
          </div>
        </div>
        
        <nav style={{ flex: 1, padding: '12px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <NavItem 
            icon={BarChart3} 
            label="Dashboard" 
            active={activeTab === 'dashboard'}
            onClick={() => setActiveTab('dashboard')}
          />
          <NavItem 
            icon={Activity} 
            label="Trades" 
            active={activeTab === 'trades'}
            onClick={() => setActiveTab('trades')}
          />
          <NavItem 
            icon={PieChart} 
            label="Analytics" 
            active={activeTab === 'analytics'}
            onClick={() => setActiveTab('analytics')}
          />
          <NavItem 
            icon={SettingsIcon} 
            label="Settings" 
            active={activeTab === 'settings'}
            onClick={() => setActiveTab('settings')}
          />
        </nav>

        <div style={{ padding: '12px', borderTop: '1px solid #2d3748' }}>
          <button 
            style={{ 
              width: '100%', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              gap: '6px', 
              padding: '8px 12px', 
              background: loading ? '#1e40af' : '#3b82f6', 
              color: 'white', 
              borderRadius: '6px', 
              fontWeight: 500,
              fontSize: '13px',
              border: 'none', 
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1
            }}
            onClick={startScrape} 
            disabled={loading}
          >
            <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            {loading ? 'Scanning...' : 'New Scan'}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, overflowY: 'auto', background: '#0f1419' }}>
        <header style={{ background: '#1a1f2e', borderBottom: '1px solid #2d3748', padding: '20px 32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ fontSize: '22px', fontWeight: 600, marginBottom: '4px' }}>
                {activeTab === 'dashboard' ? 'Dashboard' : activeTab === 'trades' ? 'Trades' : 'Analytics'}
              </h1>
              <p style={{ fontSize: '13px', color: '#9ca3af' }}>
                {activeTab === 'dashboard' ? 'Congressional trading overview' : 
                 activeTab === 'trades' ? 'Detailed trade analysis' : 
                 'Trading statistics'}
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 14px', background: '#0f1419', border: '1px solid #2d3748', borderRadius: '6px', width: '300px' }}>
              <Search size={16} style={{ color: '#6b7280' }} />
              <input 
                type="text" 
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ flex: 1, background: 'transparent', outline: 'none', fontSize: '13px', color: '#e4e6eb', border: 'none' }}
              />
            </div>
          </div>
        </header>

        {/* Content */}
        <div style={{ padding: '32px' }}>
          {activeTab === 'dashboard' && <Dashboard stats={stats} />}
          {activeTab === 'trades' && (
            <TradesView 
              trades={filteredTrades} 
              filters={filters}
              setFilters={setFilters}
            />
          )}
          {activeTab === 'analytics' && <Analytics stats={stats} />}
          {activeTab === 'settings' && (
            <Settings 
              webhookUrl={webhookUrl} 
              setWebhookUrl={setWebhookUrl} 
            />
          )}
        </div>
      </main>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        ::placeholder {
          color: #6b7280;
        }
        select {
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%239ca3af' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 12px center;
          padding-right: 32px;
          appearance: none;
        }
      `}</style>
    </div>
  );
}

function NavItem({ icon: Icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '8px 12px',
        borderRadius: '6px',
        fontSize: '13px',
        fontWeight: 500,
        border: 'none',
        cursor: 'pointer',
        background: active ? '#2d3748' : 'transparent',
        color: active ? '#e4e6eb' : '#9ca3af',
        transition: 'all 0.2s'
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.background = '#2d374850';
          e.currentTarget.style.color = '#e4e6eb';
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.color = '#9ca3af';
        }
      }}
    >
      <Icon size={16} />
      {label}
    </button>
  );
}

function Dashboard({ stats }) {
  if (!stats) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '256px' }}>
      <RefreshCw size={24} style={{ color: '#6b7280', animation: 'spin 1s linear infinite' }} />
    </div>
  );

  console.log('Rendering dashboard with stats:', stats); // Debug log

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
        <StatCard 
          icon={Activity}
          label="Total Trades"
          value={stats.total_trades || 0}
          color="#3b82f6"
        />
        <StatCard 
          icon={CheckCircle}
          label="Analyzed"
          value={stats.analyzed_trades || 0}
          color="#10b981"
        />
        <StatCard 
          icon={Users}
          label="Politicians"
          value={stats.top_politicians?.length || 0}
          color="#8b5cf6"
        />
        <StatCard 
          icon={DollarSign}
          label="Tickers"
          value={stats.top_tickers?.length || 0}
          color="#f59e0b"
        />
      </div>

      {/* Top Performers */}
      {stats.best_performers && stats.best_performers.length > 0 && (
        <div style={{ background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', padding: '20px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>Best Performers (30 days post-trade)</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
            {stats.best_performers.slice(0, 6).map((perf, idx) => (
              <div key={idx} style={{ background: '#0f1419', border: '1px solid #2d3748', borderRadius: '6px', padding: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600 }}>{perf.ticker}</span>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#10b981' }}>
                    +{perf.change_after_trade.toFixed(2)}%
                  </span>
                </div>
                <p style={{ fontSize: '11px', color: '#9ca3af' }}>{perf.politician}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Party Distribution */}
      {stats.parties && stats.parties.length > 0 && (
        <div style={{ background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', padding: '20px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>Party Distribution</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {stats.parties.map((party) => (
              <div key={party.party}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 500 }}>{party.party}</span>
                  <span style={{ fontSize: '13px', color: '#9ca3af' }}>{party.count} trades</span>
                </div>
                <div style={{ height: '6px', background: '#0f1419', borderRadius: '9999px', overflow: 'hidden' }}>
                  <div 
                    style={{ 
                      height: '100%', 
                      borderRadius: '9999px', 
                      transition: 'width 0.5s',
                      background: party.party === 'Republican' ? '#dc2626' : '#2563eb',
                      width: `${(party.count / stats.total_trades) * 100}%`
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No data message */}
      {stats.total_trades === 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 0', color: '#9ca3af' }}>
          <AlertCircle size={36} style={{ marginBottom: '10px', opacity: 0.5 }} />
          <p style={{ fontSize: '13px' }}>No trades analyzed yet. Click "New Scan" to start.</p>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div style={{ background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', padding: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between' }}>
        <div>
          <p style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>{label}</p>
          <p style={{ fontSize: '22px', fontWeight: 600 }}>{value.toLocaleString()}</p>
        </div>
        <Icon size={18} style={{ color }} />
      </div>
    </div>
  );
}

function TradesView({ trades, filters, setFilters }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Filters */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <select 
          value={filters.party} 
          onChange={(e) => setFilters({...filters, party: e.target.value})}
          style={{ padding: '8px 12px', background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '6px', fontSize: '13px', color: '#e4e6eb', cursor: 'pointer', outline: 'none' }}
        >
          <option value="">All Parties</option>
          <option value="Republican">Republican</option>
          <option value="Democrat">Democrat</option>
        </select>

        <select 
          value={filters.transaction_type} 
          onChange={(e) => setFilters({...filters, transaction_type: e.target.value})}
          style={{ padding: '8px 12px', background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '6px', fontSize: '13px', color: '#e4e6eb', cursor: 'pointer', outline: 'none' }}
        >
          <option value="">All Types</option>
          <option value="purchase">Buy</option>
          <option value="sale">Sell</option>
        </select>
      </div>

      {/* Trades List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {trades.map((trade, idx) => (
          <TradeCard key={idx} trade={trade} />
        ))}
        
        {trades.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 0', color: '#9ca3af' }}>
            <AlertCircle size={36} style={{ marginBottom: '10px', opacity: 0.5 }} />
            <p style={{ fontSize: '13px' }}>No trades found</p>
          </div>
        )}
      </div>
    </div>
  );
}

function TradeCard({ trade }) {
  const [expanded, setExpanded] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [stockData, setStockData] = useState(null);
  const [loadingChart, setLoadingChart] = useState(false);
  
  const metrics = trade.metrics || {};
  const changeAfter = metrics.change_after_trade || 0;

  console.log('Trade card data:', trade); // Debug log

  const loadStockData = async () => {
    if (stockData) {
      setShowChart(true);
      return;
    }
    
    setLoadingChart(true);
    try {
      const res = await fetch(`${API_BASE}/api/trades/${trade.id}/stock-data`);
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to load stock data');
      }
      const data = await res.json();
      console.log('Stock data loaded:', data); // Debug log
      setStockData(data);
      setShowChart(true);
    } catch (err) {
      console.error('Error loading stock data:', err);
      alert(`Failed to load chart data: ${err.message}`);
    } finally {
      setLoadingChart(false);
    }
  };

  return (
    <>
      <div style={{ background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', overflow: 'hidden' }}>
        <div 
          style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
          onClick={() => setExpanded(!expanded)}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ padding: '8px 14px', background: '#0f1419', borderRadius: '6px', fontSize: '14px', fontWeight: 700, letterSpacing: '0.5px' }}>
              {trade.ticker}
            </div>
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 500, marginBottom: '4px' }}>{trade.politician}</h3>
              <span style={{ 
                fontSize: '11px', 
                padding: '2px 8px', 
                borderRadius: '4px',
                background: 'transparent',
                color: trade.party === 'Republican' ? '#dc2626' : '#2563eb'
              }}>
                {trade.party}
              </span>
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ 
              fontSize: '11px', 
              padding: '4px 10px', 
              borderRadius: '4px', 
              textTransform: 'uppercase',
              fontWeight: 600,
              letterSpacing: '0.5px',
              background: 'transparent',
              color: trade.transaction_type?.toLowerCase().includes('purchase') ? '#10b981' : '#ef4444'
            }}>
              {trade.transaction_type}
            </span>
            {trade.is_analyzed ? (
              <span style={{ fontSize: '14px', fontWeight: 600, color: changeAfter > 0 ? '#10b981' : '#ef4444', minWidth: '80px', textAlign: 'right' }}>
                {changeAfter > 0 ? '+' : ''}{changeAfter.toFixed(2)}%
              </span>
            ) : (
              <span style={{ fontSize: '12px', color: '#6b7280', minWidth: '80px', textAlign: 'right' }}>
                Not analyzed
              </span>
            )}
            <ChevronDown 
              size={14} 
              style={{ color: '#6b7280', transition: 'transform 0.2s', transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}
            />
          </div>
        </div>

        {expanded && (
          <div style={{ borderTop: '1px solid #2d3748', padding: '20px', background: '#0f1419' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '16px', marginBottom: '16px' }}>
              <DetailItem label="Trade Date" value={new Date(trade.trade_date).toLocaleDateString()} />
              <DetailItem label="Filed After" value={`${trade.filed_after_days} days`} />
              <DetailItem 
                label="Trade Size" 
                value={`${trade.size_min?.toLocaleString()} - ${trade.size_max?.toLocaleString()}`} 
              />
              {metrics.trade_price && <DetailItem label="Price" value={`${metrics.trade_price}`} />}
              {metrics.change_to_trade && (
                <DetailItem 
                  label="30d Before" 
                  value={`${metrics.change_to_trade > 0 ? '+' : ''}${metrics.change_to_trade.toFixed(2)}%`} 
                />
              )}
              {metrics.volatility && (
                <DetailItem label="Volatility" value={`${metrics.volatility.toFixed(2)}%`} />
              )}
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
              {trade.is_analyzed && (
                <button
                  onClick={loadStockData}
                  disabled={loadingChart}
                  style={{ 
                    display: 'inline-flex', 
                    alignItems: 'center', 
                    gap: '6px', 
                    padding: '8px 14px', 
                    background: '#8b5cf6', 
                    color: 'white', 
                    borderRadius: '6px', 
                    fontSize: '13px', 
                    fontWeight: 500,
                    border: 'none',
                    cursor: loadingChart ? 'not-allowed' : 'pointer',
                    opacity: loadingChart ? 0.5 : 1,
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => !loadingChart && (e.currentTarget.style.background = '#7c3aed')}
                  onMouseLeave={(e) => !loadingChart && (e.currentTarget.style.background = '#8b5cf6')}
                >
                  <BarChart3 size={14} />
                  {loadingChart ? 'Loading...' : 'View Chart'}
                </button>
              )}

              <a 
                href={trade.trade_link} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ 
                  display: 'inline-flex', 
                  alignItems: 'center', 
                  gap: '6px', 
                  padding: '8px 14px', 
                  background: '#3b82f6', 
                  color: 'white', 
                  borderRadius: '6px', 
                  fontSize: '13px', 
                  fontWeight: 500, 
                  textDecoration: 'none',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#2563eb'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#3b82f6'}
              >
                View Details
                <ExternalLink size={12} />
              </a>
            </div>

            {!trade.is_analyzed && trade.analysis_error && (
              <div style={{ marginTop: '12px', padding: '10px', background: '#7f1d1d', border: '1px solid #991b1b', borderRadius: '6px', fontSize: '12px', color: '#fca5a5' }}>
                Analysis Error: {trade.analysis_error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chart Modal */}
      {showChart && stockData && (
        <ChartModal 
          stockData={stockData} 
          trade={trade}
          onClose={() => setShowChart(false)} 
        />
      )}
    </>
  );
}

function ChartModal({ stockData, trade, onClose }) {
  const tradeDate = new Date(stockData.trade_date).toISOString().split('T')[0];
  
  // Prepare data for charts
  const priceData = stockData.data_points.map(point => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    fullDate: point.date,
    close: point.close,
    open: point.open,
    high: point.high,
    low: point.low
  }));

  const volumeData = stockData.data_points.map(point => ({
    date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    fullDate: point.date,
    volume: point.volume,
    color: point.close >= point.open ? '#10b981' : '#ef4444'
  }));

  // Find trade date index
  const tradeDateIndex = stockData.data_points.findIndex(
    point => point.date.split('T')[0] === tradeDate
  );

  return (
    <div 
      style={{ 
        position: 'fixed', 
        inset: 0, 
        background: 'rgba(0, 0, 0, 0.8)', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        zIndex: 1000,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div 
        style={{ 
          background: '#1a1f2e', 
          borderRadius: '12px', 
          width: '100%', 
          maxWidth: '1200px',
          maxHeight: '90vh',
          overflow: 'auto',
          border: '1px solid #2d3748'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #2d3748', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '4px' }}>
              {stockData.ticker} - {trade.politician}
            </h2>
            <p style={{ fontSize: '13px', color: '#9ca3af' }}>
              {trade.transaction_type} • {new Date(trade.trade_date).toLocaleDateString()}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{ 
              padding: '8px', 
              background: '#0f1419', 
              border: '1px solid #2d3748', 
              borderRadius: '6px', 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              color: '#9ca3af'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Charts */}
        <div style={{ padding: '24px' }}>
          {/* Price Chart */}
          <div style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Price Movement</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12, fill: '#9ca3af' }}
                  stroke="#2d3748"
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: '#9ca3af' }}
                  domain={['auto', 'auto']}
                  stroke="#2d3748"
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f1419',
                    border: '1px solid #2d3748',
                    borderRadius: '6px',
                    fontSize: '12px'
                  }}
                  formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
                  labelStyle={{ color: '#e4e6eb' }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: '12px' }}
                  iconType="line"
                />
                
                {/* Shade before trade */}
                {tradeDateIndex > 0 && (
                  <ReferenceArea
                    x1={priceData[0].date}
                    x2={priceData[tradeDateIndex].date}
                    fill="#3b82f6"
                    fillOpacity={0.1}
                  />
                )}
                
                {/* Shade after trade */}
                {tradeDateIndex >= 0 && tradeDateIndex < priceData.length - 1 && (
                  <ReferenceArea
                    x1={priceData[tradeDateIndex].date}
                    x2={priceData[priceData.length - 1].date}
                    fill="#10b981"
                    fillOpacity={0.1}
                  />
                )}
                
                {/* Trade date line */}
                {tradeDateIndex >= 0 && (
                  <ReferenceLine
                    x={priceData[tradeDateIndex].date}
                    stroke="#ef4444"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    label={{
                      value: 'Trade Date',
                      position: 'top',
                      fill: '#ef4444',
                      fontWeight: 'bold',
                      fontSize: 12
                    }}
                  />
                )}
                
                <Line
                  type="monotone"
                  dataKey="close"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 6, fill: '#3b82f6' }}
                  name="Close Price"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Volume Chart */}
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Trading Volume</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12, fill: '#9ca3af' }}
                  stroke="#2d3748"
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: '#9ca3af' }}
                  stroke="#2d3748"
                  tickFormatter={(value) => {
                    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
                    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
                    return value.toString();
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f1419',
                    border: '1px solid #2d3748',
                    borderRadius: '6px',
                    fontSize: '12px'
                  }}
                  formatter={(value) => [value.toLocaleString(), 'Volume']}
                  labelStyle={{ color: '#e4e6eb' }}
                />
                
                {/* Trade date line */}
                {tradeDateIndex >= 0 && (
                  <ReferenceLine
                    x={volumeData[tradeDateIndex].date}
                    stroke="#ef4444"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                )}
                
                <Bar dataKey="volume" name="Volume">
                  {volumeData.map((entry, index) => (
                    <rect key={`bar-${index}`} fill={entry.color} opacity={0.6} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Metrics Summary */}
          {trade.metrics && (
            <div style={{ marginTop: '24px', padding: '16px', background: '#0f1419', border: '1px solid #2d3748', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Performance Metrics</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px' }}>
                <MetricItem label="Trade Price" value={`$${trade.metrics.trade_price}`} />
                {trade.metrics.change_to_trade && (
                  <MetricItem 
                    label="30d Before Trade" 
                    value={`${trade.metrics.change_to_trade > 0 ? '+' : ''}${trade.metrics.change_to_trade.toFixed(2)}%`}
                    valueColor={trade.metrics.change_to_trade > 0 ? '#10b981' : '#ef4444'}
                  />
                )}
                {trade.metrics.change_after_trade && (
                  <MetricItem 
                    label="30d After Trade" 
                    value={`${trade.metrics.change_after_trade > 0 ? '+' : ''}${trade.metrics.change_after_trade.toFixed(2)}%`}
                    valueColor={trade.metrics.change_after_trade > 0 ? '#10b981' : '#ef4444'}
                  />
                )}
                {trade.metrics.volatility && (
                  <MetricItem label="Volatility" value={`${trade.metrics.volatility.toFixed(2)}%`} />
                )}
                {trade.metrics.volume_ratio && (
                  <MetricItem label="Volume Ratio" value={`${trade.metrics.volume_ratio.toFixed(2)}x`} />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricItem({ label, value, valueColor }) {
  return (
    <div>
      <p style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>{label}</p>
      <p style={{ fontSize: '14px', fontWeight: 600, color: valueColor || '#e4e6eb' }}>{value}</p>
    </div>
  );
}

function DetailItem({ label, value }) {
  return (
    <div>
      <p style={{ fontSize: '11px', color: '#6b7280', marginBottom: '4px' }}>{label}</p>
      <p style={{ fontSize: '13px', fontWeight: 500 }}>{value}</p>
    </div>
  );
}

function Analytics({ stats }) {
  if (!stats) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '256px' }}>
      <RefreshCw size={24} style={{ color: '#6b7280', animation: 'spin 1s linear infinite' }} />
    </div>
  );

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '20px' }}>
      {/* Most Active Politicians */}
      <div style={{ background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', padding: '20px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>Most Active Politicians</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {stats.top_politicians.map((pol, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: '#0f1419', borderRadius: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#6b7280', width: '20px' }}>
                #{idx + 1}
              </span>
              <span style={{ flex: 1, fontSize: '13px', fontWeight: 500 }}>{pol.name}</span>
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                {pol.trade_count} trades
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Most Traded Tickers */}
      <div style={{ background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', padding: '20px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>Most Traded Tickers</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {stats.top_tickers.map((ticker, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px', background: '#0f1419', borderRadius: '6px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#6b7280', width: '20px' }}>
                #{idx + 1}
              </span>
              <span style={{ fontSize: '13px', fontWeight: 600 }}>{ticker.ticker}</span>
              <span style={{ flex: 1 }} />
              <span style={{ fontSize: '11px', color: '#9ca3af' }}>
                {ticker.trade_count} trades
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Settings({ webhookUrl, setWebhookUrl }) {
  const [tempUrl, setTempUrl] = useState(webhookUrl);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setWebhookUrl(tempUrl);
    localStorage.setItem('n8n_webhook_url', tempUrl);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div style={{ maxWidth: '600px' }}>
      <div style={{ background: '#1a1f2e', border: '1px solid #2d3748', borderRadius: '8px', padding: '24px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>n8n Configuration</h2>
        <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '20px' }}>
          Configure your n8n webhook URL that handles scraping and analysis
        </p>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>
            Webhook URL
          </label>
          <input
            type="text"
            value={tempUrl}
            onChange={(e) => setTempUrl(e.target.value)}
            placeholder="http://localhost:5678/webhook/capitol-trades-scan"
            style={{
              width: '100%',
              padding: '10px 12px',
              background: '#0f1419',
              border: '1px solid #2d3748',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#e4e6eb',
              outline: 'none'
            }}
          />
        </div>

        <button
          onClick={handleSave}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 16px',
            background: '#3b82f6',
            color: 'white',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 500,
            border: 'none',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#2563eb'}
          onMouseLeave={(e) => e.currentTarget.style.background = '#3b82f6'}
        >
          {saved ? <CheckCircle size={16} /> : null}
          {saved ? 'Saved!' : 'Save Configuration'}
        </button>

        <div style={{ marginTop: '24px', padding: '16px', background: '#0f1419', border: '1px solid #2d3748', borderRadius: '6px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>How it works</h3>
          <ol style={{ fontSize: '12px', color: '#9ca3af', paddingLeft: '20px', margin: 0, lineHeight: '1.8' }}>
            <li>Set up n8n workflow with a webhook trigger</li>
            <li>Workflow scrapes Capitol Trades website</li>
            <li>Workflow analyzes stock data with yfinance</li>
            <li>Workflow writes results directly to database</li>
            <li>This frontend reads from the same database</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default App;
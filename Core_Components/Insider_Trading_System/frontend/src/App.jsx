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
  Clock,
  BarChart3,
  PieChart,
  ChevronDown,
  ExternalLink
} from 'lucide-react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [trades, setTrades] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentJob, setCurrentJob] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    party: '',
    transaction_type: '',
  });

  useEffect(() => {
    loadStats();
    loadTrades();
  }, []);

  useEffect(() => {
    if (currentJob && currentJob.status !== 'completed' && currentJob.status !== 'failed') {
      const interval = setInterval(() => {
        checkJobStatus(currentJob.job_id);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [currentJob]);

  const loadStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/stats`);
      setStats(res.data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const loadTrades = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/trades`);
      setTrades(res.data.trades);
    } catch (err) {
      console.error('Error loading trades:', err);
    }
  };

  const startScrape = async () => {
    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE}/api/scrape`);
      setCurrentJob({ job_id: res.data.job_id, status: 'pending' });
    } catch (err) {
      console.error('Error starting scrape:', err);
      alert('Failed to start scraping');
    } finally {
      setLoading(false);
    }
  };

  const checkJobStatus = async (jobId) => {
    try {
      const res = await axios.get(`${API_BASE}/api/jobs/${jobId}`);
      setCurrentJob(res.data);
      
      if (res.data.status === 'completed') {
        loadStats();
        loadTrades();
      }
    } catch (err) {
      console.error('Error checking job:', err);
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
    <div className="flex min-h-screen bg-[var(--color-bg-primary)] text-[var(--color-text-primary)]">
      {/* Sidebar */}
      <aside className="w-64 bg-[var(--color-bg-secondary)] border-r border-[var(--color-border)] flex flex-col">
        <div className="p-6 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-3">
            <TrendingUp size={24} className="text-[var(--color-accent-blue)]" />
            <div>
              <h1 className="text-base font-semibold">Capitol Trades</h1>
              <p className="text-xs text-[var(--color-text-tertiary)]">Analytics</p>
            </div>
          </div>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
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
        </nav>

        <div className="p-4 border-t border-[var(--color-border)]">
          <button 
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-[var(--color-accent-blue)] text-white rounded-lg font-medium hover:bg-[var(--color-accent-blue)]/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={startScrape} 
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin-slow' : ''} />
            {loading ? 'Scanning...' : 'New Scan'}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <header className="bg-[var(--color-bg-secondary)] border-b border-[var(--color-border)] px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-semibold">
                {activeTab === 'dashboard' ? 'Dashboard' : activeTab === 'trades' ? 'Trades' : 'Analytics'}
              </h1>
              <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                {activeTab === 'dashboard' ? 'Congressional trading overview' : 
                 activeTab === 'trades' ? 'Detailed trade analysis' : 
                 'Trading statistics'}
              </p>
            </div>
            <div className="flex items-center gap-3 px-4 py-2 bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg min-w-[320px]">
              <Search size={18} className="text-[var(--color-text-tertiary)]" />
              <input 
                type="text" 
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 bg-transparent outline-none text-sm placeholder:text-[var(--color-text-tertiary)]"
              />
            </div>
          </div>
        </header>

        {/* Job Progress */}
        {currentJob && currentJob.status !== 'completed' && currentJob.status !== 'failed' && (
          <div className="mx-8 mt-6 p-4 bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg animate-slide-in">
            <div className="flex items-center gap-4">
              <Clock size={18} className="text-[var(--color-accent-blue)]" />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{currentJob.message}</span>
                  <span className="text-xs text-[var(--color-text-secondary)]">{currentJob.progress.toFixed(0)}%</span>
                </div>
                <div className="h-1 bg-[var(--color-bg-tertiary)] rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-[var(--color-accent-blue)] transition-all duration-300"
                    style={{ width: `${currentJob.progress}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-8">
          {activeTab === 'dashboard' && <Dashboard stats={stats} />}
          {activeTab === 'trades' && (
            <TradesView 
              trades={filteredTrades} 
              filters={filters}
              setFilters={setFilters}
            />
          )}
          {activeTab === 'analytics' && <Analytics stats={stats} />}
        </div>
      </main>
    </div>
  );
}

function NavItem({ icon: Icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        active 
          ? 'bg-[var(--color-bg-tertiary)] text-white' 
          : 'text-[var(--color-text-secondary)] hover:text-white hover:bg-[var(--color-bg-tertiary)]/50'
      }`}
    >
      <Icon size={18} />
      {label}
    </button>
  );
}

function Dashboard({ stats }) {
  if (!stats) return (
    <div className="flex items-center justify-center h-64">
      <RefreshCw size={24} className="animate-spin-slow text-[var(--color-text-tertiary)]" />
    </div>
  );

  return (
    <div className="space-y-6 animate-slide-in">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          icon={Activity}
          label="Total Trades"
          value={stats.total_trades}
          color="blue"
        />
        <StatCard 
          icon={CheckCircle}
          label="Analyzed"
          value={stats.successful_analyses}
          color="green"
        />
        <StatCard 
          icon={Users}
          label="Politicians"
          value={stats.top_politicians.length}
          color="purple"
        />
        <StatCard 
          icon={DollarSign}
          label="Tickers"
          value={stats.top_tickers.length}
          color="orange"
        />
      </div>

      {/* Top Performers */}
      <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Top Price Movements</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {stats.top_performers?.slice(0, 6).map((perf, idx) => (
            <div key={idx} className="bg-[var(--color-bg-tertiary)] border border-[var(--color-border)] rounded-lg p-4 hover:border-[var(--color-bg-hover)] transition-colors">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold">{perf.ticker}</span>
                <span className={`text-sm font-semibold ${
                  perf.change > 0 ? 'text-[var(--color-accent-green)]' : 'text-[var(--color-accent-red)]'
                }`}>
                  {perf.change > 0 ? '+' : ''}{perf.change.toFixed(2)}%
                </span>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)]">{perf.politician}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Party Distribution */}
      <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Party Distribution</h2>
        <div className="space-y-4">
          {Object.entries(stats.parties).map(([party, count]) => (
            <div key={party}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">{party}</span>
                <span className="text-sm text-[var(--color-text-secondary)]">{count}</span>
              </div>
              <div className="h-2 bg-[var(--color-bg-tertiary)] rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    party === 'Republican' ? 'bg-[var(--color-republican)]' : 'bg-[var(--color-democrat)]'
                  }`}
                  style={{ width: `${(count / stats.total_trades) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colorClasses = {
    blue: 'text-[var(--color-accent-blue)]',
    green: 'text-[var(--color-accent-green)]',
    purple: 'text-[var(--color-accent-purple)]',
    orange: 'text-[var(--color-accent-orange)]',
  };

  return (
    <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-[var(--color-text-secondary)] mb-1">{label}</p>
          <p className="text-2xl font-semibold">{value.toLocaleString()}</p>
        </div>
        <Icon size={20} className={colorClasses[color]} />
      </div>
    </div>
  );
}

function TradesView({ trades, filters, setFilters }) {
  return (
    <div className="space-y-4 animate-slide-in">
      {/* Filters */}
      <div className="flex gap-3">
        <select 
          value={filters.party} 
          onChange={(e) => setFilters({...filters, party: e.target.value})}
          className="px-4 py-2 bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg text-sm outline-none cursor-pointer hover:border-[var(--color-bg-hover)] transition-colors"
        >
          <option value="">All Parties</option>
          <option value="Republican">Republican</option>
          <option value="Democrat">Democrat</option>
        </select>

        <select 
          value={filters.transaction_type} 
          onChange={(e) => setFilters({...filters, transaction_type: e.target.value})}
          className="px-4 py-2 bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg text-sm outline-none cursor-pointer hover:border-[var(--color-bg-hover)] transition-colors"
        >
          <option value="">All Types</option>
          <option value="purchase">Purchase</option>
          <option value="sale">Sale</option>
        </select>
      </div>

      {/* Trades List */}
      <div className="space-y-3">
        {trades.map((trade, idx) => (
          <TradeCard key={idx} trade={trade} />
        ))}
        
        {trades.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-[var(--color-text-secondary)]">
            <AlertCircle size={40} className="mb-3 opacity-50" />
            <p className="text-sm">No trades found</p>
          </div>
        )}
      </div>
    </div>
  );
}

function TradeCard({ trade }) {
  const [expanded, setExpanded] = useState(false);
  const metrics = trade.metrics || {};
  const changeAfter = metrics.change_after_trade || 0;

  return (
    <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg overflow-hidden hover:border-[var(--color-bg-hover)] transition-colors">
      <div 
        className="p-4 flex justify-between items-center cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-4">
          <span className="px-3 py-1 bg-[var(--color-bg-tertiary)] rounded text-sm font-semibold">
            {trade.ticker}
          </span>
          <div>
            <h3 className="text-sm font-medium mb-1">{trade.politician}</h3>
            <span className={`text-xs px-2 py-0.5 rounded ${
              trade.party === 'Republican' 
                ? 'bg-[var(--color-republican)]/10 text-[var(--color-republican)]'
                : 'bg-[var(--color-democrat)]/10 text-[var(--color-democrat)]'
            }`}>
              {trade.party}
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <span className={`text-xs px-2 py-1 rounded uppercase ${
            trade.transaction_type?.toLowerCase().includes('purchase')
              ? 'bg-[var(--color-accent-green)]/10 text-[var(--color-accent-green)]'
              : 'bg-[var(--color-accent-red)]/10 text-[var(--color-accent-red)]'
          }`}>
            {trade.transaction_type}
          </span>
          <span className={`text-sm font-semibold ${
            changeAfter > 0 ? 'text-[var(--color-accent-green)]' : 'text-[var(--color-accent-red)]'
          }`}>
            {changeAfter > 0 ? '+' : ''}{changeAfter.toFixed(2)}%
          </span>
          <ChevronDown 
            size={16} 
            className={`text-[var(--color-text-tertiary)] transition-transform ${expanded ? 'rotate-180' : ''}`}
          />
        </div>
      </div>

      {expanded && (
        <div className="border-t border-[var(--color-border)] p-4 animate-slide-in">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <DetailItem label="Trade Date" value={trade.trade_date} />
            <DetailItem label="Filed After" value={`${trade.filed_after} days`} />
            <DetailItem 
              label="Trade Size" 
              value={`$${trade.trade_size_range?.[0]?.toLocaleString()} - $${trade.trade_size_range?.[1]?.toLocaleString()}`} 
            />
            <DetailItem label="Price" value={`$${metrics.trade_price}`} />
          </div>

          {trade.chart_path && (
            <div className="rounded-lg overflow-hidden border border-[var(--color-border)] mb-4">
              <img 
                src={`${API_BASE}/api/charts/${trade.chart_path.split('/').pop()}`} 
                alt="Price chart"
                className="w-full h-auto"
              />
            </div>
          )}

          <a 
            href={trade.trade_link} 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--color-accent-blue)] text-white rounded-lg text-sm font-medium hover:bg-[var(--color-accent-blue)]/90 transition-colors"
          >
            View Details
            <ExternalLink size={14} />
          </a>
        </div>
      )}
    </div>
  );
}

function DetailItem({ label, value }) {
  return (
    <div>
      <p className="text-xs text-[var(--color-text-tertiary)] mb-1">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}

function Analytics({ stats }) {
  if (!stats) return (
    <div className="flex items-center justify-center h-64">
      <RefreshCw size={24} className="animate-spin-slow text-[var(--color-text-tertiary)]" />
    </div>
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-slide-in">
      {/* Most Active Politicians */}
      <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Most Active Politicians</h2>
        <div className="space-y-2">
          {stats.top_politicians.map((pol, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-[var(--color-bg-tertiary)] rounded-lg">
              <span className="text-sm font-semibold text-[var(--color-text-secondary)] w-6">
                #{idx + 1}
              </span>
              <span className="flex-1 text-sm font-medium">{pol.name}</span>
              <span className="text-xs text-[var(--color-text-secondary)]">
                {pol.count} trades
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Most Traded Tickers */}
      <div className="bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Most Traded Tickers</h2>
        <div className="space-y-2">
          {stats.top_tickers.map((ticker, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-[var(--color-bg-tertiary)] rounded-lg">
              <span className="text-sm font-semibold text-[var(--color-text-secondary)] w-6">
                #{idx + 1}
              </span>
              <span className="text-sm font-semibold">{ticker.ticker}</span>
              <span className="flex-1" />
              <span className="text-xs text-[var(--color-text-secondary)]">
                {ticker.count} trades
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
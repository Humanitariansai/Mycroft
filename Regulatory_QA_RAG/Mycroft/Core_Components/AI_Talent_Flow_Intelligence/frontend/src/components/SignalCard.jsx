import React from 'react';
import { TrendingUp, TrendingDown, Target, Clock, DollarSign } from 'lucide-react';

const SignalCard = ({ signal, onExecute }) => {
  const getActionIcon = (action) => {
    switch (action) {
      case 'buy':
      case 'strong_buy':
        return <TrendingUp className="w-5 h-5 text-green-600" />;
      case 'sell':
      case 'reduce_position':
        return <TrendingDown className="w-5 h-5 text-red-600" />;
      default:
        return <Target className="w-5 h-5 text-blue-600" />;
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'buy':
      case 'strong_buy':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'sell':
      case 'reduce_position':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'critical':
        return 'signal-critical';
      case 'strong':
        return 'signal-strong';
      case 'moderate':
        return 'signal-moderate';
      default:
        return 'signal-weak';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="card hover:shadow-xl transition-all duration-300 border-l-4 border-talent-primary">
      <div className="card-content">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            {getActionIcon(signal.recommended_action)}
            <div>
              <h3 className="font-bold text-lg text-black">
                {signal.ticker_symbol || 'N/A'} 
                <span className="text-sm font-normal text-black opacity-75 ml-2">
                  {signal.signal_type.replace('_', ' ').toUpperCase()}
                </span>
              </h3>
              <p className="text-black text-sm">{signal.predicted_impact.toUpperCase()} Impact</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className={`signal-badge ${getStrengthColor(signal.signal_strength)}`}>
              {signal.signal_strength.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Action Recommendation */}
        <div className={`p-4 rounded-lg border-2 mb-4 ${getActionColor(signal.recommended_action)}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="font-bold text-lg">
                {signal.recommended_action.replace('_', ' ').toUpperCase()}
              </div>
              <div className="text-sm">
                Confidence: {(signal.confidence_score * 100).toFixed(0)}%
              </div>
            </div>
            
            <div className="text-right">
              <div className="text-xs opacity-75">Time Horizon</div>
              <div className="font-medium">{signal.time_horizon?.toUpperCase() || 'MEDIUM'}</div>
            </div>
          </div>
        </div>

        {/* Reasoning */}
        <div className="mb-4">
          <h4 className="font-semibold text-black mb-2">Analysis</h4>
          <p className="text-sm text-black bg-gray-50 p-3 rounded-lg">
            {signal.reasoning}
          </p>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg">
            <div className="text-lg font-bold text-purple-800">
              {(signal.confidence_score * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-purple-700">Confidence Score</div>
          </div>
          
          <div className="text-center p-3 bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-lg">
            <div className="text-lg font-bold text-indigo-800">
              {signal.time_horizon?.toUpperCase() || 'MEDIUM'}
            </div>
            <div className="text-xs text-indigo-700">Time Horizon</div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-black opacity-75">
          <span className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            {formatDate(signal.signal_generated_at)}
          </span>
          
          {onExecute && (
            <button
              onClick={() => onExecute(signal)}
              className="px-3 py-1 bg-talent-primary text-white rounded-full text-xs font-medium hover:bg-talent-secondary transition-colors"
            >
              Execute Trade
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default SignalCard;
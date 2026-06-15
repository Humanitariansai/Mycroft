import React from 'react';
import { ArrowRight, Clock, TrendingUp, AlertTriangle } from 'lucide-react';

const MovementCard = ({ movement }) => {
  const getMovementTypeIcon = (type) => {
    switch (type) {
      case 'job_change':
        return <ArrowRight className="w-5 h-5" />;
      case 'promotion':
        return <TrendingUp className="w-5 h-5" />;
      default:
        return <ArrowRight className="w-5 h-5" />;
    }
  };

  const getImpactColor = (impact) => {
    switch (impact) {
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
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="card hover:shadow-xl transition-all duration-300">
      <div className="card-content">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-talent-primary bg-opacity-10 rounded-lg text-talent-primary">
              {getMovementTypeIcon(movement.movement_type)}
            </div>
            <div>
              <h3 className="font-bold text-lg text-black">{movement.talent_name}</h3>
              <p className="text-black text-sm">{movement.movement_type.replace('_', ' ').toUpperCase()}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className={`signal-badge ${getImpactColor(movement.expected_impact)}`}>
              {movement.expected_impact.toUpperCase()}
            </span>
            <span className="text-xs text-black opacity-75 flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              {formatDate(movement.movement_date)}
            </span>
          </div>
        </div>

        {/* Movement Details */}
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-center space-x-4">
            <div className="text-center">
              <div className="text-sm font-medium text-black">{movement.from_company || 'Unknown'}</div>
              <div className="text-xs text-black opacity-75">{movement.from_role || 'Previous Role'}</div>
            </div>
            
            <div className="flex items-center text-talent-primary">
              <ArrowRight className="w-6 h-6" />
            </div>
            
            <div className="text-center">
              <div className="text-sm font-medium text-black">{movement.to_company}</div>
              <div className="text-xs text-black opacity-75">{movement.to_role}</div>
            </div>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 bg-gradient-to-r from-green-50 to-green-100 rounded-lg">
            <div className="text-lg font-bold text-green-800">
              {(movement.confidence_score * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-green-700">Confidence</div>
          </div>
          
          <div className="text-center p-3 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg">
            <div className="text-lg font-bold text-blue-800">
              {(movement.strategic_importance * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-blue-700">Strategic Impact</div>
          </div>
        </div>

        {/* Detection Info */}
        <div className="flex items-center justify-between text-xs text-black opacity-75">
          <span className="flex items-center">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Source: {movement.detection_source}
          </span>
          <span>
            Detection: {(movement.detection_confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  );
};

export default MovementCard;
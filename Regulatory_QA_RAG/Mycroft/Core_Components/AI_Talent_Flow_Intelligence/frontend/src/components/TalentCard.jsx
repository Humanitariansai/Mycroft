import React from 'react';
import { User, GitBranch, Award, Zap } from 'lucide-react';

const TalentCard = ({ talent, onClick }) => {
  const getInfluenceColor = (score) => {
    if (score >= 0.8) return 'from-green-400 to-green-600';
    if (score >= 0.6) return 'from-yellow-400 to-yellow-600';
    if (score >= 0.4) return 'from-orange-400 to-orange-600';
    return 'from-red-400 to-red-600';
  };

  const getInitials = (name) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div
      onClick={() => onClick && onClick(talent)}
      className="card hover:shadow-xl transition-all duration-300 cursor-pointer hover:scale-105"
    >
      <div className="card-content">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="talent-avatar">
              {getInitials(talent.name)}
            </div>
            <div>
              <h3 className="font-bold text-lg text-black">{talent.name}</h3>
              <p className="text-black text-sm">{talent.current_role}</p>
              <p className="text-black text-xs opacity-75">{talent.current_company}</p>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-black">
              {(talent.influence_score * 100).toFixed(0)}
            </div>
            <div className="text-xs text-black opacity-75">Influence</div>
          </div>
        </div>

        {/* Influence Breakdown */}
        <div className="space-y-2 mb-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-black flex items-center">
              <Zap className="w-4 h-4 mr-1" />
              Technical
            </span>
            <span className="text-sm font-medium text-black">
              {(talent.technical_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="influence-bar">
            <div
              className={`influence-fill bg-gradient-to-r ${getInfluenceColor(talent.technical_score)}`}
              style={{ width: `${talent.technical_score * 100}%` }}
            />
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-black flex items-center">
              <Award className="w-4 h-4 mr-1" />
              Leadership
            </span>
            <span className="text-sm font-medium text-black">
              {(talent.leadership_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="influence-bar">
            <div
              className={`influence-fill bg-gradient-to-r ${getInfluenceColor(talent.leadership_score)}`}
              style={{ width: `${talent.leadership_score * 100}%` }}
            />
          </div>

          <div className="flex justify-between items-center">
            <span className="text-sm text-black flex items-center">
              <GitBranch className="w-4 h-4 mr-1" />
              Network
            </span>
            <span className="text-sm font-medium text-black">
              {(talent.network_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="influence-bar">
            <div
              className={`influence-fill bg-gradient-to-r ${getInfluenceColor(talent.network_score)}`}
              style={{ width: `${talent.network_score * 100}%` }}
            />
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="font-bold text-black">{talent.research_papers || 0}</div>
            <div className="text-black opacity-75">Papers</div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="font-bold text-black">{talent.patents_filed || 0}</div>
            <div className="text-black opacity-75">Patents</div>
          </div>
          <div className="text-center p-2 bg-gray-50 rounded">
            <div className="font-bold text-black">{talent.github_contributions || 0}</div>
            <div className="text-black opacity-75">Commits</div>
          </div>
        </div>

        {/* Skills */}
        <div className="mt-3">
          <div className="flex flex-wrap gap-1">
            {talent.technical_skills?.slice(0, 3).map((skill, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-talent-primary text-white text-xs rounded-full"
              >
                {skill}
              </span>
            ))}
            {talent.technical_skills?.length > 3 && (
              <span className="px-2 py-1 bg-gray-200 text-black text-xs rounded-full">
                +{talent.technical_skills.length - 3} more
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TalentCard;
"""
Advanced talent movement detection algorithms.
Implements machine learning and pattern recognition for identifying talent flows.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict

# ML imports (simplified for testing without heavy dependencies)
# from sklearn.ensemble import RandomForestClassifier, IsolationForest
# from sklearn.preprocessing import StandardScaler
# from sklearn.cluster import DBSCAN
# import networkx as nx

# Internal imports
from models.schemas import (
    TalentProfile, TalentMovement, TalentMovementType, 
    CompanyProfile, CollaborationNetwork, SignalStrength
)

logger = logging.getLogger(__name__)


class MovementConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


@dataclass
class MovementSignal:
    """Represents a potential talent movement signal"""
    talent_id: str
    signal_type: str
    confidence: float
    evidence: Dict[str, Any]
    timestamp: datetime
    source: str


class TalentInfluenceCalculator:
    """Calculates multi-dimensional influence scores for talent"""
    
    def __init__(self):
        self.weights = {
            'technical_expertise': 0.35,
            'leadership_impact': 0.25,
            'network_centrality': 0.20,
            'innovation_potential': 0.20
        }
    
    def calculate_influence_score(self, profile: TalentProfile, 
                                github_data: Dict[str, Any] = None,
                                academic_data: Dict[str, Any] = None,
                                network_data: Dict[str, Any] = None) -> Dict[str, float]:
        """Calculate comprehensive influence scores"""
        
        scores = {
            'technical_score': self._calculate_technical_score(profile, github_data),
            'leadership_score': self._calculate_leadership_score(profile),
            'network_score': self._calculate_network_score(profile, network_data),
            'innovation_score': self._calculate_innovation_score(profile, academic_data),
        }
        
        # Calculate weighted overall influence
        overall_score = sum(
            scores[score_type.replace('_score', '') + '_score'] * weight 
            for score_type, weight in self.weights.items()
            if score_type.replace('_', '') + '_score' in scores
        )
        
        scores['overall_influence'] = min(overall_score, 1.0)
        
        return scores
    
    def _calculate_technical_score(self, profile: TalentProfile, 
                                 github_data: Dict[str, Any] = None) -> float:
        """Calculate technical expertise score"""
        score_components = []
        
        # Years of experience
        exp_score = min(profile.ai_experience_years / 10.0, 1.0)  # Cap at 10 years
        score_components.append(exp_score * 0.3)
        
        # GitHub activity (if available)
        if github_data:
            repo_score = min(github_data.get('public_repos', 0) / 50.0, 1.0)
            contrib_score = min(profile.github_contributions / 1000.0, 1.0)
            score_components.extend([repo_score * 0.2, contrib_score * 0.2])
        
        # Patents and research
        patent_score = min(profile.patents_filed / 10.0, 1.0)
        research_score = min(profile.research_papers / 20.0, 1.0)
        score_components.extend([patent_score * 0.15, research_score * 0.15])
        
        return sum(score_components) if score_components else 0.5
    
    def _calculate_leadership_score(self, profile: TalentProfile) -> float:
        """Calculate leadership impact score"""
        score_components = []
        
        # Leadership roles
        leadership_count = len(profile.leadership_roles)
        leadership_score = min(leadership_count / 5.0, 1.0)
        score_components.append(leadership_score * 0.4)
        
        # Conference talks and visibility
        talks_score = min(profile.conference_talks / 20.0, 1.0)
        score_components.append(talks_score * 0.3)
        
        # Career progression (companies worked)
        progression_score = min(len(profile.companies_worked) / 5.0, 1.0)
        score_components.append(progression_score * 0.3)
        
        return sum(score_components) if score_components else 0.3
    
    def _calculate_network_score(self, profile: TalentProfile, 
                               network_data: Dict[str, Any] = None) -> float:
        """Calculate network centrality and connection quality score"""
        if not network_data:
            # Fallback estimation
            companies_score = min(len(profile.companies_worked) / 5.0, 1.0)
            return companies_score * 0.5
        
        # Would use actual network analysis
        centrality_score = network_data.get('betweenness_centrality', 0.3)
        connection_quality = network_data.get('high_influence_connections', 0.2)
        
        return (centrality_score * 0.6 + connection_quality * 0.4)
    
    def _calculate_innovation_score(self, profile: TalentProfile, 
                                  academic_data: Dict[str, Any] = None) -> float:
        """Calculate innovation and cutting-edge work potential"""
        score_components = []
        
        # Research output
        if academic_data:
            recent_papers = academic_data.get('recent_publications', 0)
            citations = academic_data.get('total_citations', 0)
            
            research_score = min(recent_papers / 10.0, 1.0)
            impact_score = min(citations / 100.0, 1.0)
            
            score_components.extend([research_score * 0.3, impact_score * 0.2])
        
        # Technology adoption (cutting-edge skills)
        emerging_skills = ['transformer', 'gpt', 'diffusion', 'quantum', 'neuromorphic']
        skill_innovation = sum(1 for skill in profile.technical_skills 
                             if any(emerging in skill.lower() for emerging in emerging_skills))
        innovation_score = min(skill_innovation / 3.0, 1.0)
        score_components.append(innovation_score * 0.3)
        
        # Patents in emerging areas
        patent_score = min(profile.patents_filed / 5.0, 1.0)
        score_components.append(patent_score * 0.2)
        
        return sum(score_components) if score_components else 0.4


class MovementPatternAnalyzer:
    """Analyzes patterns in talent movements for early detection"""
    
    def __init__(self):
        self.movement_history: List[TalentMovement] = []
        self.pattern_models = {}
        
    def analyze_movement_patterns(self, company_id: str, 
                                historical_movements: List[TalentMovement]) -> Dict[str, Any]:
        """Analyze talent movement patterns for a company"""
        
        self.movement_history = historical_movements
        
        analysis = {
            'hiring_patterns': self._analyze_hiring_patterns(company_id),
            'exit_patterns': self._analyze_exit_patterns(company_id),
            'seasonal_trends': self._analyze_seasonal_trends(company_id),
            'competitive_dynamics': self._analyze_competitive_movements(company_id),
            'team_movements': self._detect_team_movements(company_id),
        }
        
        return analysis
    
    def _analyze_hiring_patterns(self, company_id: str) -> Dict[str, Any]:
        """Analyze hiring patterns and sources"""
        hires = [m for m in self.movement_history 
                if m.to_company == company_id and m.movement_type == TalentMovementType.JOB_CHANGE]
        
        if not hires:
            return {'total_hires': 0}
        
        # Source company analysis
        source_companies = defaultdict(int)
        for hire in hires:
            if hire.from_company:
                source_companies[hire.from_company] += 1
        
        # Role pattern analysis
        role_patterns = defaultdict(int)
        for hire in hires:
            role_patterns[hire.to_role] += 1
        
        # Timing analysis
        recent_hires = [h for h in hires 
                       if h.movement_date > datetime.now() - timedelta(days=90)]
        
        return {
            'total_hires': len(hires),
            'recent_hires': len(recent_hires),
            'top_source_companies': dict(sorted(source_companies.items(), 
                                              key=lambda x: x[1], reverse=True)[:5]),
            'common_roles': dict(sorted(role_patterns.items(), 
                                      key=lambda x: x[1], reverse=True)[:5]),
            'hiring_velocity': len(recent_hires) / 3,  # per month
        }
    
    def _analyze_exit_patterns(self, company_id: str) -> Dict[str, Any]:
        """Analyze departure patterns and destinations"""
        exits = [m for m in self.movement_history 
                if m.from_company == company_id and m.movement_type == TalentMovementType.JOB_CHANGE]
        
        if not exits:
            return {'total_exits': 0}
        
        # Destination analysis
        destinations = defaultdict(int)
        for exit in exits:
            destinations[exit.to_company] += 1
        
        # Exit role analysis
        exit_roles = defaultdict(int)
        for exit in exits:
            if exit.from_role:
                exit_roles[exit.from_role] += 1
        
        # Recent exits
        recent_exits = [e for e in exits 
                       if e.movement_date > datetime.now() - timedelta(days=90)]
        
        return {
            'total_exits': len(exits),
            'recent_exits': len(recent_exits),
            'top_destinations': dict(sorted(destinations.items(), 
                                          key=lambda x: x[1], reverse=True)[:5]),
            'roles_at_risk': dict(sorted(exit_roles.items(), 
                                       key=lambda x: x[1], reverse=True)[:5]),
            'attrition_rate': len(recent_exits) / max(len(exits), 1),
        }
    
    def _analyze_seasonal_trends(self, company_id: str) -> Dict[str, Any]:
        """Identify seasonal patterns in talent movements"""
        company_movements = [m for m in self.movement_history 
                           if m.to_company == company_id or m.from_company == company_id]
        
        if not company_movements:
            return {}
        
        # Group by month
        monthly_counts = defaultdict(int)
        for movement in company_movements:
            month = movement.movement_date.month
            monthly_counts[month] += 1
        
        # Find peak months
        peak_month = max(monthly_counts.items(), key=lambda x: x[1], default=(1, 0))
        
        return {
            'monthly_distribution': dict(monthly_counts),
            'peak_movement_month': peak_month[0],
            'peak_movement_count': peak_month[1],
            'seasonal_variance': np.std(list(monthly_counts.values())) if monthly_counts else 0,
        }
    
    def _analyze_competitive_movements(self, company_id: str) -> Dict[str, Any]:
        """Analyze movements between competitors"""
        # Identify competitors based on movement patterns
        company_movements = [m for m in self.movement_history 
                           if m.to_company == company_id or m.from_company == company_id]
        
        competitor_interactions = defaultdict(lambda: {'to_us': 0, 'from_us': 0})
        
        for movement in company_movements:
            if movement.to_company == company_id and movement.from_company:
                competitor_interactions[movement.from_company]['to_us'] += 1
            elif movement.from_company == company_id:
                competitor_interactions[movement.to_company]['from_us'] += 1
        
        # Calculate net talent flow
        net_flows = {}
        for competitor, flows in competitor_interactions.items():
            net_flows[competitor] = flows['to_us'] - flows['from_us']
        
        return {
            'competitor_interactions': dict(competitor_interactions),
            'net_talent_flows': net_flows,
            'talent_winners': [k for k, v in net_flows.items() if v < 0][:3],  # Companies we lose to
            'talent_sources': [k for k, v in net_flows.items() if v > 0][:3],  # Companies we gain from
        }
    
    def _detect_team_movements(self, company_id: str) -> Dict[str, Any]:
        """Detect coordinated team movements"""
        company_movements = [m for m in self.movement_history 
                           if m.to_company == company_id or m.from_company == company_id]
        
        # Group movements by time windows
        time_windows = []
        sorted_movements = sorted(company_movements, key=lambda m: m.movement_date)
        
        current_window = []
        window_size = timedelta(days=30)  # 30-day window
        
        for movement in sorted_movements:
            if not current_window or (movement.movement_date - current_window[0].movement_date) <= window_size:
                current_window.append(movement)
            else:
                if len(current_window) > 1:
                    time_windows.append(current_window)
                current_window = [movement]
        
        # Add final window
        if len(current_window) > 1:
            time_windows.append(current_window)
        
        team_movements = []
        for window in time_windows:
            if len(window) >= 3:  # Potential team movement
                team_movements.append({
                    'date_range': (window[0].movement_date, window[-1].movement_date),
                    'movement_count': len(window),
                    'companies_involved': list(set([m.from_company for m in window if m.from_company] + 
                                                 [m.to_company for m in window])),
                    'movements': [m.id for m in window]
                })
        
        return {
            'team_movements_detected': len(team_movements),
            'team_movements': team_movements[:5],  # Top 5
            'largest_team_movement': max(team_movements, key=lambda x: x['movement_count']) if team_movements else None,
        }


class InvestmentSignalGenerator:
    """Generates investment signals from talent intelligence"""
    
    def __init__(self):
        self.influence_calculator = TalentInfluenceCalculator()
        self.pattern_analyzer = MovementPatternAnalyzer()
        
    def generate_signals_from_movement(self, movement: TalentMovement,
                                     talent_profile: TalentProfile,
                                     company_profiles: Dict[str, CompanyProfile]) -> List[Dict[str, Any]]:
        """Generate investment signals from a talent movement"""
        
        signals = []
        
        # Calculate talent influence impact
        influence_scores = self.influence_calculator.calculate_influence_score(talent_profile)
        
        # Generate signal for destination company
        if movement.to_company in company_profiles:
            destination_signal = self._generate_positive_signal(
                movement, talent_profile, company_profiles[movement.to_company], influence_scores
            )
            signals.append(destination_signal)
        
        # Generate signal for source company (if applicable)
        if movement.from_company and movement.from_company in company_profiles:
            source_signal = self._generate_negative_signal(
                movement, talent_profile, company_profiles[movement.from_company], influence_scores
            )
            signals.append(source_signal)
        
        return signals
    
    def _generate_positive_signal(self, movement: TalentMovement, talent: TalentProfile,
                                company: CompanyProfile, influence_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate positive investment signal for talent acquisition"""
        
        # Calculate signal strength based on talent influence and company size
        base_strength = influence_scores['overall_influence']
        
        # Adjust for company size (bigger impact on smaller companies)
        size_multiplier = {
            'startup': 2.0,
            'small': 1.5,
            'medium': 1.2,
            'large': 1.0,
            'enterprise': 0.8
        }.get(company.company_size.value, 1.0)
        
        adjusted_strength = min(base_strength * size_multiplier, 1.0)
        
        # Determine signal classification
        if adjusted_strength >= 0.8:
            signal_strength = SignalStrength.CRITICAL
            recommended_action = "strong_buy"
        elif adjusted_strength >= 0.6:
            signal_strength = SignalStrength.STRONG
            recommended_action = "buy"
        elif adjusted_strength >= 0.4:
            signal_strength = SignalStrength.MODERATE
            recommended_action = "watch"
        else:
            signal_strength = SignalStrength.WEAK
            recommended_action = "neutral"
        
        return {
            'signal_id': f"talent_hire_{movement.id}",
            'company_id': company.id,
            'ticker_symbol': company.ticker_symbol,
            'signal_type': 'talent_acquisition',
            'signal_strength': signal_strength,
            'confidence_score': movement.confidence_score * 0.9,  # Slight discount for uncertainty
            'predicted_impact': 'positive',
            'recommended_action': recommended_action,
            'reasoning': f"High-influence talent acquisition: {talent.name} joining {company.name}",
            'key_factors': [
                f"Talent influence score: {influence_scores['overall_influence']:.2f}",
                f"Technical expertise: {influence_scores['technical_score']:.2f}",
                f"Leadership impact: {influence_scores['leadership_score']:.2f}",
                f"Company size amplification: {size_multiplier}x"
            ],
            'time_horizon': self._estimate_impact_timeline(movement, talent, company),
            'risk_factors': self._identify_risk_factors(movement, talent, company),
            'generated_at': datetime.now().isoformat()
        }
    
    def _generate_negative_signal(self, movement: TalentMovement, talent: TalentProfile,
                                company: CompanyProfile, influence_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate negative investment signal for talent departure"""
        
        # Calculate negative impact
        base_impact = influence_scores['overall_influence']
        
        # Adjust for leadership vs individual contributor
        role_multiplier = 2.0 if any(keyword in movement.from_role.lower() 
                                   for keyword in ['cto', 'vp', 'director', 'head', 'chief']) else 1.0
        
        adjusted_impact = min(base_impact * role_multiplier, 1.0)
        
        # Determine signal classification
        if adjusted_impact >= 0.8:
            signal_strength = SignalStrength.CRITICAL
            recommended_action = "sell"
        elif adjusted_impact >= 0.6:
            signal_strength = SignalStrength.STRONG
            recommended_action = "reduce_position"
        elif adjusted_impact >= 0.4:
            signal_strength = SignalStrength.MODERATE
            recommended_action = "watch"
        else:
            signal_strength = SignalStrength.WEAK
            recommended_action = "neutral"
        
        return {
            'signal_id': f"talent_exit_{movement.id}",
            'company_id': company.id,
            'ticker_symbol': company.ticker_symbol,
            'signal_type': 'talent_departure',
            'signal_strength': signal_strength,
            'confidence_score': movement.confidence_score * 0.8,
            'predicted_impact': 'negative',
            'recommended_action': recommended_action,
            'reasoning': f"High-influence talent departure: {talent.name} leaving {company.name}",
            'key_factors': [
                f"Departing talent influence: {influence_scores['overall_influence']:.2f}",
                f"Role importance multiplier: {role_multiplier}x",
                f"Leadership impact: {influence_scores['leadership_score']:.2f}",
                f"Technical expertise loss: {influence_scores['technical_score']:.2f}"
            ],
            'time_horizon': 'short',  # Negative impacts often more immediate
            'risk_factors': [
                'Knowledge transfer risk',
                'Team morale impact',
                'Competitive intelligence loss',
                'Potential talent cascade'
            ],
            'generated_at': datetime.now().isoformat()
        }
    
    def _estimate_impact_timeline(self, movement: TalentMovement, 
                                talent: TalentProfile, company: CompanyProfile) -> str:
        """Estimate when talent impact will be reflected in stock performance"""
        
        # Factors affecting timeline
        role_seniority = 1.0 if any(keyword in movement.to_role.lower() 
                                  for keyword in ['senior', 'principal', 'staff', 'lead']) else 0.5
        
        leadership_role = 2.0 if any(keyword in movement.to_role.lower() 
                                   for keyword in ['director', 'vp', 'head', 'chief']) else 1.0
        
        company_size_factor = {
            'startup': 0.5,  # Faster impact
            'small': 1.0,
            'medium': 1.5,
            'large': 2.0,
            'enterprise': 3.0  # Slower impact
        }.get(company.company_size.value, 1.5)
        
        # Calculate months to impact
        base_months = 6
        adjusted_months = base_months * company_size_factor / (role_seniority + leadership_role)
        
        if adjusted_months <= 3:
            return 'short'  # 1-3 months
        elif adjusted_months <= 12:
            return 'medium'  # 3-12 months
        else:
            return 'long'  # 12+ months
    
    def _identify_risk_factors(self, movement: TalentMovement, 
                             talent: TalentProfile, company: CompanyProfile) -> List[str]:
        """Identify potential risk factors for the investment signal"""
        
        risks = []
        
        # Integration risks
        if len(talent.companies_worked) > 5:
            risks.append("High job mobility - retention risk")
        
        # Company-specific risks
        if company.company_size.value == 'startup':
            risks.append("Startup execution risk")
        
        # Role-specific risks
        if 'research' in movement.to_role.lower():
            risks.append("Research impact timeline uncertainty")
        
        # Market risks
        risks.extend([
            "Market volatility impact",
            "Competitor talent response",
            "Technology evolution risk"
        ])
        
        return risks


# Example usage and testing
def test_movement_detection():
    """Test the movement detection algorithms"""
    print("Testing AI Talent Movement Detection")
    
    # Create sample data
    sample_profile = TalentProfile(
        id="test_001",
        name="Dr. Sarah Chen",
        current_company="TechCorp",
        current_role="Senior ML Engineer",
        ai_experience_years=8,
        technical_skills=["Python", "TensorFlow", "Computer Vision", "Transformers"],
        leadership_roles=["Tech Lead", "Research Lead"],
        research_papers=12,
        patents_filed=3,
        github_contributions=150,
        conference_talks=8
    )
    
    # Test influence calculation
    influence_calc = TalentInfluenceCalculator()
    scores = influence_calc.calculate_influence_score(sample_profile)
    print(f"Influence Scores: {json.dumps(scores, indent=2)}")
    
    # Test signal generation
    signal_gen = InvestmentSignalGenerator()
    sample_movement = TalentMovement(
        id="move_001",
        talent_id="test_001",
        talent_name="Dr. Sarah Chen",
        movement_type=TalentMovementType.JOB_CHANGE,
        from_company="TechCorp",
        to_company="AI Innovations Inc",
        from_role="Senior ML Engineer",
        to_role="Principal AI Scientist",
        movement_date=datetime.now(),
        expected_impact='strong',
        confidence_score=0.85,
        strategic_importance=0.8,
        detection_source='automated',
        detection_confidence=0.9
    )
    
    sample_company = CompanyProfile(
        id="company_001",
        name="AI Innovations Inc",
        ticker_symbol="AIIV",
        sector="Artificial Intelligence",
        company_size="medium"
    )
    
    signals = signal_gen.generate_signals_from_movement(
        sample_movement, sample_profile, {"AI Innovations Inc": sample_company}
    )
    
    print(f"Generated Signals: {json.dumps(signals, indent=2, default=str)}")


if __name__ == "__main__":
    test_movement_detection()
"""
Predictive models for talent flow impact on stock prices and company performance.
Uses simplified ML approaches for educational demonstration.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Result of a talent flow impact prediction"""
    ticker: str
    prediction_type: str
    predicted_impact: float  # -1 to +1 scale
    confidence: float  # 0 to 1 scale
    time_horizon: str  # short, medium, long
    contributing_factors: List[str]
    model_version: str
    prediction_date: datetime

class TalentImpactPredictor:
    """Predicts stock price impact from talent movements"""
    
    def __init__(self):
        self.model_weights = {
            'influence_score': 0.35,
            'role_seniority': 0.25, 
            'company_size_factor': 0.15,
            'industry_momentum': 0.10,
            'team_effect': 0.10,
            'market_conditions': 0.05
        }
        self.model_version = "1.0.0-demo"
    
    def predict_stock_impact(self, talent_movement: Dict, talent_profile: Dict, 
                           company_profile: Dict, market_context: Dict = None) -> PredictionResult:
        """Predict stock price impact from a talent movement"""
        
        try:
            # Extract features
            features = self._extract_features(talent_movement, talent_profile, company_profile, market_context)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(features)
            
            # Determine confidence
            confidence = self._calculate_confidence(features)
            
            # Determine time horizon
            time_horizon = self._determine_time_horizon(features)
            
            # Generate contributing factors explanation
            contributing_factors = self._identify_contributing_factors(features)
            
            return PredictionResult(
                ticker=company_profile.get('ticker_symbol', 'UNKNOWN'),
                prediction_type='talent_movement_impact',
                predicted_impact=impact_score,
                confidence=confidence,
                time_horizon=time_horizon,
                contributing_factors=contributing_factors,
                model_version=self.model_version,
                prediction_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return PredictionResult(
                ticker=company_profile.get('ticker_symbol', 'UNKNOWN'),
                prediction_type='error',
                predicted_impact=0.0,
                confidence=0.0,
                time_horizon='unknown',
                contributing_factors=[f"Prediction error: {str(e)}"],
                model_version=self.model_version,
                prediction_date=datetime.now()
            )
    
    def _extract_features(self, movement: Dict, talent: Dict, company: Dict, market: Dict = None) -> Dict:
        """Extract numerical features for prediction"""
        
        features = {}
        
        # Talent influence features
        features['influence_score'] = talent.get('influence_score', 0.5)
        features['technical_score'] = talent.get('technical_score', 0.5)
        features['leadership_score'] = talent.get('leadership_score', 0.5)
        features['network_score'] = talent.get('network_score', 0.5)
        
        # Role seniority
        role = movement.get('to_role', '').lower()
        features['role_seniority'] = self._calculate_role_seniority(role)
        
        # Company size factor
        company_size = company.get('company_size', 'medium')
        features['company_size_factor'] = self._get_company_size_factor(company_size)
        
        # Movement type impact
        movement_type = movement.get('movement_type', 'job_change')
        features['movement_type_factor'] = self._get_movement_type_factor(movement_type)
        
        # Experience factor
        features['experience_factor'] = min(talent.get('ai_experience_years', 0) / 15.0, 1.0)
        
        # Research/innovation factor
        papers = talent.get('research_papers', 0)
        patents = talent.get('patents_filed', 0)
        features['innovation_factor'] = min((papers * 0.02) + (patents * 0.1), 1.0)
        
        # Market timing factor (simplified)
        features['market_timing'] = 0.6 if market else 0.5
        
        return features
    
    def _calculate_role_seniority(self, role: str) -> float:
        """Calculate role seniority score"""
        role = role.lower()
        
        if any(title in role for title in ['ceo', 'cto', 'chief', 'founder']):
            return 1.0
        elif any(title in role for title in ['vp', 'vice president', 'head of', 'director']):
            return 0.8
        elif any(title in role for title in ['principal', 'staff', 'lead', 'manager']):
            return 0.6
        elif any(title in role for title in ['senior', 'sr']):
            return 0.4
        else:
            return 0.2
    
    def _get_company_size_factor(self, company_size: str) -> float:
        """Get impact multiplier based on company size"""
        size_factors = {
            'startup': 2.0,      # High impact on small companies
            'small': 1.5,
            'medium': 1.0,       # Baseline
            'large': 0.7,
            'enterprise': 0.5    # Lower impact on large companies
        }
        return size_factors.get(company_size, 1.0)
    
    def _get_movement_type_factor(self, movement_type: str) -> float:
        """Get impact factor based on movement type"""
        type_factors = {
            'job_change': 1.0,
            'promotion': 0.7,
            'company_exit': -0.8,
            'startup_join': 1.2
        }
        return type_factors.get(movement_type, 1.0)
    
    def _calculate_impact_score(self, features: Dict) -> float:
        """Calculate overall impact score using weighted features"""
        
        # Base impact from talent influence
        base_impact = features['influence_score']
        
        # Adjust for role seniority
        role_adjustment = features['role_seniority'] * 0.3
        
        # Company size multiplier
        size_multiplier = features['company_size_factor']
        
        # Movement type factor
        movement_factor = features['movement_type_factor']
        
        # Experience bonus
        experience_bonus = features['experience_factor'] * 0.2
        
        # Innovation bonus
        innovation_bonus = features['innovation_factor'] * 0.15
        
        # Calculate combined impact
        impact = (base_impact + role_adjustment + experience_bonus + innovation_bonus) * size_multiplier * movement_factor
        
        # Normalize to [-1, 1] range
        impact = max(-1.0, min(1.0, (impact - 0.5) * 2))
        
        return impact
    
    def _calculate_confidence(self, features: Dict) -> float:
        """Calculate prediction confidence based on feature quality"""
        
        confidence_factors = []
        
        # High influence increases confidence
        if features['influence_score'] > 0.7:
            confidence_factors.append(0.8)
        elif features['influence_score'] > 0.5:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.4)
        
        # Senior roles increase confidence
        if features['role_seniority'] > 0.7:
            confidence_factors.append(0.8)
        elif features['role_seniority'] > 0.4:
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(0.5)
        
        # Experience increases confidence
        if features['experience_factor'] > 0.6:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)
        
        # Average confidence
        confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Add some randomness for realism
        confidence += np.random.normal(0, 0.05)
        
        return max(0.1, min(0.95, confidence))
    
    def _determine_time_horizon(self, features: Dict) -> str:
        """Determine impact time horizon"""
        
        # Senior roles have faster impact
        if features['role_seniority'] > 0.8:
            return 'short'  # 1-3 months
        
        # High influence tech roles
        elif features['influence_score'] > 0.8 and features['technical_score'] > 0.8:
            return 'short'
        
        # Medium impact cases
        elif features['role_seniority'] > 0.4 or features['influence_score'] > 0.6:
            return 'medium'  # 3-12 months
        
        # Lower impact takes longer to materialize
        else:
            return 'long'  # 12+ months
    
    def _identify_contributing_factors(self, features: Dict) -> List[str]:
        """Identify key factors contributing to the prediction"""
        
        factors = []
        
        if features['influence_score'] > 0.7:
            factors.append(f"High talent influence score ({features['influence_score']:.2f})")
        
        if features['role_seniority'] > 0.7:
            factors.append("Senior leadership role")
        
        if features['company_size_factor'] > 1.2:
            factors.append("High impact on smaller company")
        
        if features['innovation_factor'] > 0.3:
            factors.append("Strong research/innovation background")
        
        if features['experience_factor'] > 0.6:
            factors.append("Extensive AI experience")
        
        if features['technical_score'] > 0.8:
            factors.append("High technical expertise")
        
        if features['leadership_score'] > 0.7:
            factors.append("Proven leadership capabilities")
        
        return factors if factors else ["Standard talent movement impact"]


class TeamMovementPredictor:
    """Predicts impact when multiple talents move together"""
    
    def __init__(self):
        self.team_multiplier = 1.5  # Team movements have amplified effect
    
    def predict_team_movement_impact(self, movements: List[Dict], talent_profiles: List[Dict], 
                                   company_profile: Dict) -> PredictionResult:
        """Predict impact of coordinated team movement"""
        
        try:
            individual_predictor = TalentImpactPredictor()
            individual_predictions = []
            
            # Get individual predictions
            for movement, talent in zip(movements, talent_profiles):
                pred = individual_predictor.predict_stock_impact(movement, talent, company_profile)
                individual_predictions.append(pred)
            
            # Aggregate team impact
            avg_impact = sum(p.predicted_impact for p in individual_predictions) / len(individual_predictions)
            team_impact = avg_impact * self.team_multiplier
            
            # Higher confidence for team movements
            avg_confidence = sum(p.confidence for p in individual_predictions) / len(individual_predictions)
            team_confidence = min(0.95, avg_confidence * 1.2)
            
            # Team movements typically have faster impact
            time_horizon = 'short' if len(movements) >= 3 else 'medium'
            
            contributing_factors = [
                f"Team movement of {len(movements)} high-value talents",
                f"Coordinated departure suggests strategic shift",
                f"Amplified impact factor: {self.team_multiplier}x"
            ]
            
            return PredictionResult(
                ticker=company_profile.get('ticker_symbol', 'UNKNOWN'),
                prediction_type='team_movement_impact',
                predicted_impact=max(-1.0, min(1.0, team_impact)),
                confidence=team_confidence,
                time_horizon=time_horizon,
                contributing_factors=contributing_factors,
                model_version="1.0.0-team",
                prediction_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Team prediction failed: {e}")
            return PredictionResult(
                ticker=company_profile.get('ticker_symbol', 'UNKNOWN'),
                prediction_type='error',
                predicted_impact=0.0,
                confidence=0.0,
                time_horizon='unknown',
                contributing_factors=[f"Team prediction error: {str(e)}"],
                model_version="1.0.0-team",
                prediction_date=datetime.now()
            )


class MarketTimingPredictor:
    """Predicts optimal timing for trading based on talent signals"""
    
    def __init__(self):
        self.timing_factors = {
            'earnings_proximity': 0.3,
            'market_volatility': 0.25,
            'sector_momentum': 0.25,
            'news_cycle': 0.2
        }
    
    def predict_optimal_timing(self, prediction: PredictionResult, 
                             market_context: Dict = None) -> Dict[str, any]:
        """Predict optimal timing for acting on talent-based signals"""
        
        try:
            timing_score = 0.5  # Baseline
            timing_factors = []
            
            # Adjust based on prediction confidence
            if prediction.confidence > 0.8:
                timing_score += 0.2
                timing_factors.append("High prediction confidence favors immediate action")
            
            # Adjust based on time horizon
            if prediction.time_horizon == 'short':
                timing_score += 0.15
                timing_factors.append("Short time horizon suggests urgent timing")
            
            # Adjust based on impact magnitude
            if abs(prediction.predicted_impact) > 0.6:
                timing_score += 0.1
                timing_factors.append("High impact magnitude supports immediate positioning")
            
            # Market context adjustments (if available)
            if market_context:
                if market_context.get('volatility', 0.5) < 0.3:
                    timing_score += 0.1
                    timing_factors.append("Low market volatility favorable for position changes")
                
                if market_context.get('sector_momentum', 0) > 0.1:
                    timing_score += 0.05
                    timing_factors.append("Positive sector momentum")
            
            # Normalize timing score
            timing_score = max(0.1, min(0.9, timing_score))
            
            # Determine timing recommendation
            if timing_score > 0.7:
                timing_rec = "immediate"
                timing_window = "0-2 days"
            elif timing_score > 0.5:
                timing_rec = "near_term"
                timing_window = "3-7 days"
            else:
                timing_rec = "wait"
                timing_window = "1-2 weeks"
            
            return {
                "timing_score": timing_score,
                "timing_recommendation": timing_rec,
                "timing_window": timing_window,
                "reasoning": timing_factors,
                "optimal_entry_confidence": min(0.9, timing_score + prediction.confidence) / 2
            }
            
        except Exception as e:
            logger.error(f"Timing prediction failed: {e}")
            return {
                "timing_score": 0.5,
                "timing_recommendation": "hold",
                "timing_window": "unknown",
                "reasoning": ["Timing analysis failed"],
                "optimal_entry_confidence": 0.3
            }


# Example usage and testing
def test_predictive_models():
    """Test the predictive models with sample data"""
    print("Testing AI Talent Flow Predictive Models")
    
    # Sample data
    sample_movement = {
        "id": "movement_001",
        "talent_id": "talent_001", 
        "talent_name": "Dr. Sarah Chen",
        "movement_type": "job_change",
        "from_company": "Google",
        "to_company": "OpenAI",
        "to_role": "VP of Research",
        "movement_date": datetime.now().isoformat(),
        "confidence_score": 0.9
    }
    
    sample_talent = {
        "id": "talent_001",
        "name": "Dr. Sarah Chen",
        "influence_score": 0.85,
        "technical_score": 0.90,
        "leadership_score": 0.80,
        "network_score": 0.85,
        "ai_experience_years": 8,
        "research_papers": 25,
        "patents_filed": 4
    }
    
    sample_company = {
        "id": "company_001",
        "name": "OpenAI",
        "ticker_symbol": "OPENAI",
        "company_size": "large"
    }
    
    # Test individual movement prediction
    predictor = TalentImpactPredictor()
    prediction = predictor.predict_stock_impact(sample_movement, sample_talent, sample_company)
    
    print(f"\nIndividual Movement Prediction:")
    print(f"Ticker: {prediction.ticker}")
    print(f"Predicted Impact: {prediction.predicted_impact:.3f}")
    print(f"Confidence: {prediction.confidence:.3f}")
    print(f"Time Horizon: {prediction.time_horizon}")
    print(f"Contributing Factors: {prediction.contributing_factors}")
    
    # Test timing prediction
    timing_predictor = MarketTimingPredictor()
    timing = timing_predictor.predict_optimal_timing(prediction)
    
    print(f"\nTiming Prediction:")
    print(f"Timing Score: {timing['timing_score']:.3f}")
    print(f"Recommendation: {timing['timing_recommendation']}")
    print(f"Window: {timing['timing_window']}")
    print(f"Entry Confidence: {timing['optimal_entry_confidence']:.3f}")


if __name__ == "__main__":
    test_predictive_models()
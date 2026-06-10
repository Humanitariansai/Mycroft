"""
AI Talent Flow Intelligence - Enhanced with Predictive Models
Complete integrated system with advanced prediction capabilities
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
import json

# Import integration and prediction services
from services.mycroft_integration import mycroft_integrator, signal_aggregator
from models.predictive_models import TalentImpactPredictor, TeamMovementPredictor, MarketTimingPredictor
from services.real_time_monitor import real_time_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize predictive models
impact_predictor = TalentImpactPredictor()
team_predictor = TeamMovementPredictor()
timing_predictor = MarketTimingPredictor()

# Initialize FastAPI app
app = FastAPI(
    title="AI Talent Flow Intelligence API - Enhanced Predictive",
    description="Advanced talent intelligence with predictive modeling and Mycroft integration",
    version="1.0.0-predictive",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data (enhanced version)
sample_data = {
    "talent_profiles": [
        {
            "id": "talent_001",
            "name": "Dr. Emma Rodriguez",
            "current_company": "OpenAI",
            "current_role": "Senior Research Scientist",
            "github_username": "emma_ai",
            "ai_experience_years": 6,
            "technical_skills": ["Python", "PyTorch", "Transformers", "Computer Vision"],
            "leadership_roles": ["Research Lead"],
            "influence_score": 0.85,
            "technical_score": 0.90,
            "leadership_score": 0.75,
            "network_score": 0.80,
            "research_papers": 15,
            "patents_filed": 2,
            "github_contributions": 250,
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "talent_002",
            "name": "Alex Chen",
            "current_company": "Google DeepMind", 
            "current_role": "Principal Engineer",
            "github_username": "alexchen_ml",
            "ai_experience_years": 10,
            "technical_skills": ["TensorFlow", "JAX", "Reinforcement Learning", "NLP"],
            "leadership_roles": ["Tech Lead", "Mentor"],
            "influence_score": 0.92,
            "technical_score": 0.95,
            "leadership_score": 0.85,
            "network_score": 0.90,
            "research_papers": 28,
            "patents_filed": 7,
            "github_contributions": 420,
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "talent_003",
            "name": "Dr. Lisa Wang",
            "current_company": "Anthropic",
            "current_role": "VP of Safety Research",
            "ai_experience_years": 12,
            "technical_skills": ["AI Safety", "Constitutional AI", "Python", "Research"],
            "leadership_roles": ["VP", "Research Director"],
            "influence_score": 0.88,
            "technical_score": 0.85,
            "leadership_score": 0.95,
            "network_score": 0.87,
            "research_papers": 35,
            "patents_filed": 5,
            "github_contributions": 180,
            "last_updated": datetime.now().isoformat()
        }
    ],
    "company_profiles": [
        {
            "id": "company_001",
            "name": "OpenAI",
            "ticker_symbol": "OPENAI",
            "sector": "Artificial Intelligence",
            "company_size": "large",
            "ai_specializations": ["Large Language Models", "AGI Research"],
            "total_ai_talent": 150,
            "recent_hires": 12,
            "recent_exits": 3,
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "company_002",
            "name": "Anthropic",
            "ticker_symbol": "ANTHR",
            "sector": "AI Safety",
            "company_size": "medium", 
            "ai_specializations": ["Constitutional AI", "Safety Research"],
            "total_ai_talent": 80,
            "recent_hires": 15,
            "recent_exits": 2,
            "last_updated": datetime.now().isoformat()
        },
        {
            "id": "company_003",
            "name": "Google DeepMind",
            "ticker_symbol": "GOOGL",
            "sector": "AI Research",
            "company_size": "enterprise",
            "ai_specializations": ["Research", "AGI", "Robotics"],
            "total_ai_talent": 2000,
            "recent_hires": 50,
            "recent_exits": 15,
            "last_updated": datetime.now().isoformat()
        }
    ],
    "talent_movements": [],
    "investment_signals": []
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-predictive",
        "services": {
            "api": "operational",
            "data": "demo_mode",
            "mycroft_integration": "enabled",
            "predictive_models": "operational"
        }
    }

# Core endpoints (inherited from previous version)
@app.get("/api/talent/profiles")
async def list_talent_profiles():
    return sample_data["talent_profiles"]

@app.get("/api/companies/profiles")
async def list_company_profiles():
    return sample_data["company_profiles"]

@app.get("/api/movements")
async def get_talent_movements():
    return sample_data["talent_movements"]

@app.get("/api/signals/recent")
async def get_recent_signals():
    return sample_data["investment_signals"]

# NEW PREDICTIVE MODEL ENDPOINTS

@app.post("/api/predictions/movement-impact")
async def predict_movement_impact(movement_data: Dict[str, Any]):
    """Predict stock price impact from a talent movement"""
    try:
        # Find talent and company profiles
        talent_profile = None
        company_profile = None
        
        for talent in sample_data["talent_profiles"]:
            if talent["name"] == movement_data.get("talent_name"):
                talent_profile = talent
                break
        
        for company in sample_data["company_profiles"]:
            if company["name"] == movement_data.get("to_company"):
                company_profile = company
                break
        
        if not talent_profile or not company_profile:
            raise HTTPException(status_code=400, detail="Talent or company not found")
        
        # Generate prediction
        prediction = impact_predictor.predict_stock_impact(
            movement_data, talent_profile, company_profile
        )
        
        # Get timing recommendation
        timing = timing_predictor.predict_optimal_timing(prediction)
        
        return {
            "status": "success",
            "prediction": {
                "ticker": prediction.ticker,
                "predicted_impact": prediction.predicted_impact,
                "confidence": prediction.confidence,
                "time_horizon": prediction.time_horizon,
                "contributing_factors": prediction.contributing_factors,
                "model_version": prediction.model_version
            },
            "timing": timing,
            "investment_recommendation": {
                "action": "buy" if prediction.predicted_impact > 0.3 else "hold" if prediction.predicted_impact > -0.3 else "sell",
                "position_size": min(0.1, abs(prediction.predicted_impact) * prediction.confidence),
                "urgency": timing["timing_recommendation"]
            }
        }
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predictions/team-movement")
async def predict_team_movement_impact(team_data: Dict[str, Any]):
    """Predict impact of coordinated team movement"""
    try:
        movements = team_data.get("movements", [])
        if len(movements) < 2:
            raise HTTPException(status_code=400, detail="Team movement requires at least 2 people")
        
        # Find talent profiles for team members
        talent_profiles = []
        for movement in movements:
            for talent in sample_data["talent_profiles"]:
                if talent["name"] == movement.get("talent_name"):
                    talent_profiles.append(talent)
                    break
        
        # Find company profile
        company_profile = None
        target_company = movements[0].get("to_company")  # Assume same destination
        for company in sample_data["company_profiles"]:
            if company["name"] == target_company:
                company_profile = company
                break
        
        if len(talent_profiles) != len(movements) or not company_profile:
            raise HTTPException(status_code=400, detail="Could not find all required profiles")
        
        # Generate team movement prediction
        team_prediction = team_predictor.predict_team_movement_impact(
            movements, talent_profiles, company_profile
        )
        
        return {
            "status": "success",
            "team_prediction": {
                "ticker": team_prediction.ticker,
                "predicted_impact": team_prediction.predicted_impact,
                "confidence": team_prediction.confidence,
                "time_horizon": team_prediction.time_horizon,
                "contributing_factors": team_prediction.contributing_factors,
                "team_size": len(movements)
            },
            "individual_impacts": [
                impact_predictor.predict_stock_impact(mov, tal, company_profile).predicted_impact
                for mov, tal in zip(movements, talent_profiles)
            ],
            "amplification_factor": team_predictor.team_multiplier
        }
        
    except Exception as e:
        logger.error(f"Team prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predictions/market-timing/{ticker}")
async def get_market_timing_analysis(ticker: str):
    """Get market timing analysis for a ticker"""
    try:
        # Find recent signals for this ticker
        recent_prediction = None
        for signal in sample_data["investment_signals"]:
            if signal.get("ticker_symbol") == ticker.upper():
                # Convert signal to prediction format
                from models.predictive_models import PredictionResult
                recent_prediction = PredictionResult(
                    ticker=ticker.upper(),
                    prediction_type="signal_based",
                    predicted_impact=0.6 if signal.get("predicted_impact") == "positive" else -0.6,
                    confidence=signal.get("confidence_score", 0.7),
                    time_horizon=signal.get("time_horizon", "medium"),
                    contributing_factors=[signal.get("reasoning", "")],
                    model_version="signal_conversion",
                    prediction_date=datetime.now()
                )
                break
        
        if not recent_prediction:
            # Create default prediction
            from models.predictive_models import PredictionResult
            recent_prediction = PredictionResult(
                ticker=ticker.upper(),
                prediction_type="default",
                predicted_impact=0.0,
                confidence=0.5,
                time_horizon="medium",
                contributing_factors=["No recent talent signals"],
                model_version="default",
                prediction_date=datetime.now()
            )
        
        # Get timing analysis
        timing = timing_predictor.predict_optimal_timing(recent_prediction)
        
        # Add market context
        market_context = {
            "sector_momentum": 0.15,  # Positive AI sector momentum
            "volatility": 0.25,       # Moderate volatility
            "liquidity": 0.8,         # Good liquidity
            "news_sentiment": 0.6     # Positive news sentiment
        }
        
        return {
            "status": "success",
            "ticker": ticker.upper(),
            "timing_analysis": timing,
            "market_context": market_context,
            "recommendation_summary": {
                "primary_action": timing["timing_recommendation"],
                "confidence_level": timing["optimal_entry_confidence"],
                "time_window": timing["timing_window"],
                "risk_assessment": "moderate" if timing["timing_score"] > 0.5 else "high"
            }
        }
        
    except Exception as e:
        logger.error(f"Timing analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predictions/scenario-analysis")
async def run_scenario_analysis(scenario_data: Dict[str, Any]):
    """Run scenario analysis for multiple what-if talent movements"""
    try:
        scenarios = scenario_data.get("scenarios", [])
        results = []
        
        for i, scenario in enumerate(scenarios):
            # Find profiles
            talent_profile = None
            company_profile = None
            
            for talent in sample_data["talent_profiles"]:
                if talent["name"] == scenario.get("talent_name"):
                    talent_profile = talent
                    break
            
            for company in sample_data["company_profiles"]:
                if company["name"] == scenario.get("to_company"):
                    company_profile = company
                    break
            
            if talent_profile and company_profile:
                prediction = impact_predictor.predict_stock_impact(
                    scenario, talent_profile, company_profile
                )
                
                results.append({
                    "scenario_id": i + 1,
                    "scenario_name": scenario.get("name", f"Scenario {i + 1}"),
                    "ticker": company_profile["ticker_symbol"],
                    "predicted_impact": prediction.predicted_impact,
                    "confidence": prediction.confidence,
                    "time_horizon": prediction.time_horizon,
                    "roi_estimate": prediction.predicted_impact * prediction.confidence * 100,  # Rough ROI %
                })
        
        # Rank scenarios by potential ROI
        results.sort(key=lambda x: x["roi_estimate"], reverse=True)
        
        return {
            "status": "success",
            "scenario_analysis": {
                "total_scenarios": len(results),
                "best_opportunity": results[0] if results else None,
                "worst_scenario": results[-1] if results else None,
                "average_impact": sum(r["predicted_impact"] for r in results) / len(results) if results else 0,
                "high_confidence_scenarios": [r for r in results if r["confidence"] > 0.7],
                "scenarios": results
            }
        }
        
    except Exception as e:
        logger.error(f"Scenario analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/demo/generate-predictive-movement")
async def generate_predictive_demo():
    """Generate a demo movement with full predictive analysis"""
    try:
        # Create realistic demo movement
        demo_movement = {
            "id": f"movement_predictive_{len(sample_data['talent_movements']) + 1}",
            "talent_name": "Dr. Lisa Wang",
            "movement_type": "job_change",
            "from_company": "Anthropic",
            "to_company": "OpenAI",
            "from_role": "VP of Safety Research",
            "to_role": "Chief Safety Officer",
            "movement_date": datetime.now().isoformat(),
            "expected_impact": "critical",
            "confidence_score": 0.92,
            "strategic_importance": 0.95
        }
        
        # Add to movements
        sample_data["talent_movements"].append(demo_movement)
        
        # Get talent and company profiles
        talent_profile = None
        company_profile = None
        
        for talent in sample_data["talent_profiles"]:
            if talent["name"] == "Dr. Lisa Wang":
                talent_profile = talent
                break
        
        for company in sample_data["company_profiles"]:
            if company["name"] == "OpenAI":
                company_profile = company
                break
        
        # Generate full predictive analysis
        prediction = impact_predictor.predict_stock_impact(
            demo_movement, talent_profile, company_profile
        )
        
        timing = timing_predictor.predict_optimal_timing(prediction)
        
        # Process through Mycroft integration
        company_profiles = {comp["id"]: comp for comp in sample_data["company_profiles"]}
        integration_result = await mycroft_integrator.process_talent_movement_end_to_end(
            demo_movement, company_profiles
        )
        
        # Create enhanced investment signal
        enhanced_signal = {
            "id": f"signal_predictive_{len(sample_data['investment_signals']) + 1}",
            "signal_type": "talent_acquisition_predictive",
            "company_id": "company_001",
            "ticker_symbol": "OPENAI",
            "signal_strength": "critical",
            "confidence_score": prediction.confidence,
            "predicted_impact": "positive",
            "predicted_price_impact": prediction.predicted_impact,
            "recommended_action": "strong_buy" if prediction.predicted_impact > 0.5 else "buy",
            "reasoning": f"Critical leadership acquisition: {demo_movement['talent_name']} as Chief Safety Officer",
            "time_horizon": prediction.time_horizon,
            "contributing_factors": prediction.contributing_factors,
            "timing_recommendation": timing,
            "signal_generated_at": datetime.now().isoformat()
        }
        
        sample_data["investment_signals"].append(enhanced_signal)
        
        return {
            "status": "success",
            "demo_movement": demo_movement,
            "predictive_analysis": {
                "impact_prediction": {
                    "predicted_impact": prediction.predicted_impact,
                    "confidence": prediction.confidence,
                    "time_horizon": prediction.time_horizon,
                    "contributing_factors": prediction.contributing_factors
                },
                "timing_analysis": timing,
                "investment_recommendation": {
                    "action": enhanced_signal["recommended_action"],
                    "position_size": min(0.15, abs(prediction.predicted_impact) * prediction.confidence),
                    "expected_return": f"{prediction.predicted_impact * 100:.1f}%",
                    "risk_level": "moderate" if prediction.confidence > 0.7 else "high"
                }
            },
            "enhanced_signal": enhanced_signal,
            "mycroft_integration": integration_result
        }
        
    except Exception as e:
        logger.error(f"Predictive demo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# REAL-TIME MONITORING ENDPOINTS

@app.get("/api/monitoring/status")
async def get_monitoring_status():
    """Get real-time monitoring system status"""
    try:
        stats = real_time_monitor.get_current_stats()
        return {
            "status": "success",
            "monitoring": stats,
            "websocket_url": "ws://localhost:8005"
        }
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/monitoring/events")
async def get_monitoring_events(count: int = 50):
    """Get recent monitoring events"""
    try:
        events = real_time_monitor.get_recent_events(count)
        return {
            "status": "success",
            "events": events,
            "total_events": len(events)
        }
    except Exception as e:
        logger.error(f"Error getting monitoring events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/trigger-alert")
async def trigger_monitoring_alert(alert_data: Dict[str, Any]):
    """Trigger a custom monitoring alert"""
    try:
        from services.real_time_monitor import MonitoringEvent, MonitoringLevel
        
        level_map = {
            "info": MonitoringLevel.INFO,
            "warning": MonitoringLevel.WARNING,
            "critical": MonitoringLevel.CRITICAL
        }
        
        event = MonitoringEvent(
            event_type=alert_data.get("event_type", "custom_alert"),
            level=level_map.get(alert_data.get("level", "info"), MonitoringLevel.INFO),
            message=alert_data.get("message", "Custom monitoring alert"),
            timestamp=datetime.now(),
            data=alert_data.get("data", {}),
            source="api_trigger"
        )
        
        await real_time_monitor._emit_event(event)
        
        return {
            "status": "success",
            "message": "Alert triggered successfully",
            "event": {
                "event_type": event.event_type,
                "level": event.level.value,
                "message": event.message
            }
        }
    except Exception as e:
        logger.error(f"Error triggering alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Note: For production deployment, run monitoring service separately
    # python3 start_monitoring.py
    
    # Start main API server  
    uvicorn.run(app, host="0.0.0.0", port=8004)  # Different port for enhanced version
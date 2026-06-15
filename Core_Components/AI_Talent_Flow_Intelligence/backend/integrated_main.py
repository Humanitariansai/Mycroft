"""
AI Talent Flow Intelligence FastAPI Backend - Integrated with Mycroft Ecosystem
Enhanced version with full Mycroft integration capabilities
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
import json

# Import integration services
from services.mycroft_integration import mycroft_integrator, signal_aggregator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Talent Flow Intelligence API - Integrated",
    description="Advanced talent intelligence system integrated with Mycroft ecosystem",
    version="1.0.0-integrated",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data (same as simple_main.py but with enhanced processing)
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
    "talent_movements": [
        {
            "id": "movement_001",
            "talent_id": "talent_001",
            "talent_name": "Dr. Emma Rodriguez",
            "movement_type": "job_change",
            "from_company": "Google DeepMind",
            "to_company": "OpenAI",
            "from_role": "Research Scientist",
            "to_role": "Senior Research Scientist",
            "movement_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "expected_impact": "strong",
            "confidence_score": 0.85,
            "strategic_importance": 0.8,
            "detection_source": "automated",
            "detection_confidence": 0.9
        }
    ],
    "investment_signals": [
        {
            "id": "signal_001",
            "signal_type": "talent_acquisition",
            "company_id": "company_001",
            "ticker_symbol": "OPENAI",
            "signal_strength": "strong",
            "confidence_score": 0.85,
            "predicted_impact": "positive",
            "recommended_action": "buy",
            "reasoning": "High-influence talent acquisition: Dr. Emma Rodriguez joining OpenAI",
            "time_horizon": "medium",
            "signal_generated_at": datetime.now().isoformat()
        }
    ]
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-integrated",
        "services": {
            "api": "operational",
            "data": "demo_mode",
            "mycroft_integration": "enabled"
        }
    }

# Original endpoints (same as simple_main.py)
@app.get("/api/talent/profiles")
async def list_talent_profiles():
    """List all tracked talent profiles"""
    return sample_data["talent_profiles"]

@app.get("/api/talent/profiles/{profile_id}")
async def get_talent_profile(profile_id: str):
    """Get talent profile by ID"""
    for profile in sample_data["talent_profiles"]:
        if profile["id"] == profile_id:
            return profile
    raise HTTPException(status_code=404, detail="Talent profile not found")

@app.get("/api/companies/profiles")
async def list_company_profiles():
    """List all tracked company profiles"""
    return sample_data["company_profiles"]

@app.get("/api/movements")
async def get_talent_movements():
    """Get recent talent movements"""
    return sample_data["talent_movements"]

@app.get("/api/movements/summary")
async def get_movement_summary():
    """Get talent movement summary"""
    movements = sample_data["talent_movements"]
    return {
        "total_movements": len(movements),
        "high_impact_movements": len([m for m in movements if m["expected_impact"] in ["strong", "critical"]]),
        "companies_affected": 3,  # OpenAI, Google, Anthropic
        "investment_signals_generated": len(sample_data["investment_signals"]),
        "average_confidence": 0.85,
        "top_movements": movements
    }

@app.get("/api/signals/recent")
async def get_recent_signals():
    """Get recent high-confidence investment signals"""
    return sample_data["investment_signals"]

# NEW INTEGRATION ENDPOINTS

@app.post("/api/integration/process-movement")
async def process_movement_with_integration(movement_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Process a talent movement through the entire Mycroft ecosystem"""
    try:
        # Convert company profiles to dict format expected by integrator
        company_profiles = {
            company["id"]: company for company in sample_data["company_profiles"]
        }
        
        # Process through Mycroft ecosystem
        result = await mycroft_integrator.process_talent_movement_end_to_end(
            movement_data, company_profiles
        )
        
        return {
            "status": "success",
            "integration_result": result,
            "message": "Movement processed through Mycroft ecosystem"
        }
        
    except Exception as e:
        logger.error(f"Error processing movement integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integration/enhanced-analysis/{ticker}")
async def get_enhanced_analysis(ticker: str):
    """Get market analysis enhanced with talent intelligence"""
    try:
        # Find talent context for this ticker
        talent_context = {}
        for signal in sample_data["investment_signals"]:
            if signal.get("ticker_symbol") == ticker.upper():
                talent_context = signal
                break
        
        if not talent_context:
            talent_context = {
                "confidence_score": 0.5,
                "predicted_impact": "neutral",
                "reasoning": "No recent talent signals available"
            }
        
        # Get enhanced analysis
        enhanced_analysis = await mycroft_integrator.trigger_market_analysis_with_talent_context(
            ticker.upper(), talent_context
        )
        
        return {
            "status": "success",
            "enhanced_analysis": enhanced_analysis,
            "ticker": ticker.upper()
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integration/aggregated-signals/{ticker}")
async def get_aggregated_signals(ticker: str, hours_back: int = 24):
    """Get aggregated talent signals for a ticker"""
    try:
        # Add sample signals to aggregator
        for signal in sample_data["investment_signals"]:
            if signal.get("ticker_symbol") == ticker.upper():
                signal_aggregator.add_signal(signal)
        
        aggregated = signal_aggregator.get_aggregated_signals_for_ticker(ticker.upper(), hours_back)
        
        return {
            "status": "success",
            "aggregated_signals": aggregated,
            "ticker": ticker.upper()
        }
        
    except Exception as e:
        logger.error(f"Error getting aggregated signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integration/send-to-trading")
async def send_signal_to_trading(signal_data: Dict[str, Any]):
    """Send investment signal to Trading Execution Agent"""
    try:
        result = await mycroft_integrator.send_to_trading_execution(signal_data)
        
        return {
            "status": "success",
            "trading_result": result,
            "message": "Signal sent to Trading Execution Agent"
        }
        
    except Exception as e:
        logger.error(f"Error sending to trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/demo/generate-integrated-movement")
async def generate_integrated_demo_movement(background_tasks: BackgroundTasks):
    """Generate a demo talent movement and process it through entire Mycroft ecosystem"""
    try:
        # Create demo movement
        new_movement = {
            "id": f"movement_integrated_{len(sample_data['talent_movements']) + 1}",
            "talent_id": "talent_002",
            "talent_name": "Alex Chen",
            "movement_type": "job_change",
            "from_company": "Google DeepMind",
            "to_company": "Anthropic",
            "from_role": "Principal Engineer",
            "to_role": "VP of Engineering",
            "movement_date": datetime.now().isoformat(),
            "expected_impact": "critical",
            "confidence_score": 0.95,
            "strategic_importance": 0.9,
            "detection_source": "demo_integrated",
            "detection_confidence": 1.0
        }
        
        # Add to sample data
        sample_data["talent_movements"].append(new_movement)
        
        # Process through Mycroft ecosystem
        company_profiles = {
            company["id"]: company for company in sample_data["company_profiles"]
        }
        
        integration_result = await mycroft_integrator.process_talent_movement_end_to_end(
            new_movement, company_profiles
        )
        
        # Generate corresponding investment signal
        new_signal = {
            "id": f"signal_integrated_{len(sample_data['investment_signals']) + 1}",
            "signal_type": "talent_acquisition",
            "company_id": "company_002",  # Anthropic
            "ticker_symbol": "ANTHR",
            "signal_strength": "critical",
            "confidence_score": 0.95,
            "predicted_impact": "positive",
            "recommended_action": "strong_buy",
            "reasoning": "Critical talent acquisition: Alex Chen (VP Engineering) joining Anthropic from Google DeepMind",
            "time_horizon": "short",
            "signal_generated_at": datetime.now().isoformat()
        }
        
        sample_data["investment_signals"].append(new_signal)
        
        return {
            "status": "success",
            "movement": new_movement,
            "signal": new_signal,
            "integration_result": integration_result,
            "message": "Demo talent movement processed through entire Mycroft ecosystem"
        }
        
    except Exception as e:
        logger.error(f"Error generating integrated demo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integration/ecosystem-status")
async def get_ecosystem_status():
    """Get status of Mycroft ecosystem integration"""
    try:
        # Test connectivity to other services
        ecosystem_status = {
            "talent_intelligence": "operational",
            "market_signal_system": "checking",
            "trading_execution": "checking",
            "integration_layer": "operational"
        }
        
        # Test Market Signal System
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/health", timeout=5.0)
                if response.status_code == 200:
                    ecosystem_status["market_signal_system"] = "operational"
                else:
                    ecosystem_status["market_signal_system"] = "error"
        except:
            ecosystem_status["market_signal_system"] = "disconnected"
        
        # Trading execution would be on different port in production
        ecosystem_status["trading_execution"] = "simulated"
        
        return {
            "status": "success",
            "ecosystem_status": ecosystem_status,
            "timestamp": datetime.now().isoformat(),
            "integration_features": [
                "talent_signal_generation",
                "market_analysis_enhancement",
                "trading_execution_integration",
                "signal_aggregation",
                "end_to_end_processing"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting ecosystem status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)  # Different port to avoid conflicts
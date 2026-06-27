"""
AI Talent Flow Intelligence FastAPI Backend - Simplified Version
Demonstrates core functionality without heavy ML dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Talent Flow Intelligence API",
    description="Advanced talent intelligence system for AI investment decision making",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simplified in-memory storage
talent_profiles = {}
company_profiles = {}
talent_movements = []
investment_signals = []

# Sample data for demonstration
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
        }
    ],
    "talent_movements": [
        {
            "id": "movement_001",
            "talent_id": "talent_001",
            "talent_name": "Dr. Emma Rodriguez",
            "movement_type": "job_change",
            "from_company": "Google",
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
        "version": "1.0.0-simplified",
        "services": {
            "api": "operational",
            "data": "demo_mode"
        }
    }

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

@app.get("/api/companies/profiles/{company_id}")
async def get_company_profile(company_id: str):
    """Get company profile by ID"""
    for company in sample_data["company_profiles"]:
        if company["id"] == company_id:
            return company
    raise HTTPException(status_code=404, detail="Company profile not found")

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
        "companies_affected": 2,  # OpenAI, Google
        "investment_signals_generated": len(sample_data["investment_signals"]),
        "average_confidence": 0.85,
        "top_movements": movements
    }

@app.get("/api/signals/recent")
async def get_recent_signals():
    """Get recent high-confidence investment signals"""
    return sample_data["investment_signals"]

@app.get("/api/companies/{company_id}/talent-metrics")
async def get_company_talent_metrics(company_id: str):
    """Get comprehensive talent metrics for a company"""
    # Find company
    company = None
    for comp in sample_data["company_profiles"]:
        if comp["id"] == company_id:
            company = comp
            break
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "company_id": company_id,
        "company_name": company["name"],
        "talent_flow_score": 0.78,
        "hiring_momentum": 0.85,
        "retention_risk": 0.15,
        "competitive_threat_level": 0.3,
        "investment_recommendation": "buy",
        "key_talent_moves": sample_data["talent_movements"]
    }

@app.get("/api/analytics/influence-leaders")
async def get_influence_leaders():
    """Get top talent by influence score"""
    return sorted(
        sample_data["talent_profiles"],
        key=lambda x: x["influence_score"],
        reverse=True
    )

@app.get("/api/analytics/movement-trends")
async def get_movement_trends():
    """Analyze talent movement trends"""
    return {
        "monthly_trends": {
            "2024-01": {"total": 5, "high_impact": 2},
            "2024-02": {"total": 8, "high_impact": 3},
            "2024-03": {"total": 12, "high_impact": 4}
        },
        "total_movements": 25,
        "trend_analysis": "Increasing talent mobility in AI sector"
    }

@app.get("/api/demo/generate-movement")
async def generate_demo_movement():
    """Generate a demo talent movement for testing"""
    new_movement = {
        "id": f"movement_{len(sample_data['talent_movements']) + 1}",
        "talent_id": "talent_002",
        "talent_name": "Alex Chen",
        "movement_type": "job_change",
        "from_company": "Google DeepMind",
        "to_company": "OpenAI",
        "from_role": "Principal Engineer",
        "to_role": "VP of Engineering",
        "movement_date": datetime.now().isoformat(),
        "expected_impact": "critical",
        "confidence_score": 0.95,
        "strategic_importance": 0.9,
        "detection_source": "demo_generated",
        "detection_confidence": 1.0
    }
    
    sample_data["talent_movements"].append(new_movement)
    
    # Generate corresponding investment signal
    new_signal = {
        "id": f"signal_{len(sample_data['investment_signals']) + 1}",
        "signal_type": "talent_acquisition",
        "company_id": "company_001",
        "ticker_symbol": "OPENAI",
        "signal_strength": "critical",
        "confidence_score": 0.95,
        "predicted_impact": "positive",
        "recommended_action": "strong_buy",
        "reasoning": "Critical talent acquisition: Alex Chen (VP Engineering) joining OpenAI from Google DeepMind",
        "time_horizon": "short",
        "signal_generated_at": datetime.now().isoformat()
    }
    
    sample_data["investment_signals"].append(new_signal)
    
    return {
        "status": "success",
        "movement": new_movement,
        "signal": new_signal,
        "message": "Demo talent movement and investment signal generated"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
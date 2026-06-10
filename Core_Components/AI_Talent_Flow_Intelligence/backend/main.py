"""
AI Talent Flow Intelligence FastAPI Backend
Main application entry point with comprehensive talent intelligence APIs
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
import asyncio
import json
import os

# Internal imports
from models.schemas import (
    TalentProfile, CompanyProfile, TalentMovement, InvestmentSignal,
    TalentFlowSummary, CompanyTalentMetrics, TalentTrackingRequest,
    CompanyTrackingRequest, InvestmentSignalQuery, TalentIntelligenceReport
)
from services.data_collectors import (
    GitHubTalentCollector, LinkedInTalentCollector, AcademicDataCollector,
    TalentMovementDetector, CompanyTalentTracker
)
from services.movement_detection import (
    TalentInfluenceCalculator, MovementPatternAnalyzer, InvestmentSignalGenerator
)

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
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
github_collector = GitHubTalentCollector()
linkedin_collector = LinkedInTalentCollector()
academic_collector = AcademicDataCollector()
movement_detector = TalentMovementDetector()
company_tracker = CompanyTalentTracker()
influence_calculator = TalentInfluenceCalculator()
pattern_analyzer = MovementPatternAnalyzer()
signal_generator = InvestmentSignalGenerator()

# In-memory storage for demonstration (would be replaced with proper database)
talent_profiles: Dict[str, TalentProfile] = {}
company_profiles: Dict[str, CompanyProfile] = {}
talent_movements: List[TalentMovement] = []
investment_signals: List[InvestmentSignal] = []

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "data_collection": "operational",
            "movement_detection": "operational",
            "signal_generation": "operational"
        }
    }

# Talent Profile Management Endpoints
@app.post("/api/talent/profiles", response_model=Dict[str, str])
async def create_talent_profile(request: TalentTrackingRequest, background_tasks: BackgroundTasks):
    """Start tracking a new talent profile"""
    try:
        # Generate profile ID
        profile_id = f"talent_{len(talent_profiles) + 1}_{int(datetime.now().timestamp())}"
        
        # Create initial profile
        profile = TalentProfile(
            id=profile_id,
            name=request.name or "Unknown",
            current_company=request.current_company,
            current_role="Unknown",
            linkedin_url=request.linkedin_url,
            github_username=request.github_username
        )
        
        # Store profile
        talent_profiles[profile_id] = profile
        
        # Schedule background data collection
        background_tasks.add_task(collect_talent_data, profile_id)
        
        return {
            "status": "success",
            "profile_id": profile_id,
            "message": "Talent profile created and data collection initiated"
        }
        
    except Exception as e:
        logger.error(f"Error creating talent profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/talent/profiles/{profile_id}", response_model=TalentProfile)
async def get_talent_profile(profile_id: str):
    """Get talent profile by ID"""
    if profile_id not in talent_profiles:
        raise HTTPException(status_code=404, detail="Talent profile not found")
    
    return talent_profiles[profile_id]

@app.get("/api/talent/profiles", response_model=List[TalentProfile])
async def list_talent_profiles(limit: int = 50, offset: int = 0):
    """List all tracked talent profiles"""
    profiles_list = list(talent_profiles.values())[offset:offset + limit]
    return profiles_list

@app.put("/api/talent/profiles/{profile_id}", response_model=Dict[str, str])
async def update_talent_profile(profile_id: str, profile_update: Dict[str, Any]):
    """Update talent profile information"""
    if profile_id not in talent_profiles:
        raise HTTPException(status_code=404, detail="Talent profile not found")
    
    try:
        profile = talent_profiles[profile_id]
        
        # Update allowed fields
        for field, value in profile_update.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        profile.last_updated = datetime.now()
        talent_profiles[profile_id] = profile
        
        return {"status": "success", "message": "Profile updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Company Profile Management Endpoints
@app.post("/api/companies/profiles", response_model=Dict[str, str])
async def create_company_profile(request: CompanyTrackingRequest, background_tasks: BackgroundTasks):
    """Start tracking a company's talent"""
    try:
        company_id = f"company_{len(company_profiles) + 1}_{int(datetime.now().timestamp())}"
        
        profile = CompanyProfile(
            id=company_id,
            name=request.company_name,
            ticker_symbol=request.ticker_symbol,
            sector="Artificial Intelligence",  # Default
            company_size="medium"  # Default
        )
        
        company_profiles[company_id] = profile
        
        # Schedule background talent analysis
        background_tasks.add_task(analyze_company_talent, company_id)
        
        return {
            "status": "success",
            "company_id": company_id,
            "message": "Company profile created and talent analysis initiated"
        }
        
    except Exception as e:
        logger.error(f"Error creating company profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/companies/profiles/{company_id}", response_model=CompanyProfile)
async def get_company_profile(company_id: str):
    """Get company profile by ID"""
    if company_id not in company_profiles:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    return company_profiles[company_id]

@app.get("/api/companies/profiles", response_model=List[CompanyProfile])
async def list_company_profiles(limit: int = 50):
    """List all tracked company profiles"""
    return list(company_profiles.values())[:limit]

# Talent Movement Endpoints
@app.get("/api/movements", response_model=List[TalentMovement])
async def get_talent_movements(
    company_id: Optional[str] = None,
    limit: int = 100,
    days_back: int = 90
):
    """Get recent talent movements"""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    filtered_movements = [
        movement for movement in talent_movements
        if movement.movement_date >= cutoff_date
        and (not company_id or movement.to_company == company_id or movement.from_company == company_id)
    ]
    
    return sorted(filtered_movements, key=lambda x: x.movement_date, reverse=True)[:limit]

@app.get("/api/movements/summary", response_model=TalentFlowSummary)
async def get_movement_summary(days_back: int = 30):
    """Get talent movement summary"""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    recent_movements = [
        movement for movement in talent_movements
        if movement.movement_date >= cutoff_date
    ]
    
    high_impact_movements = [
        movement for movement in recent_movements
        if movement.expected_impact in ['strong', 'critical']
    ]
    
    companies_affected = set()
    for movement in recent_movements:
        if movement.to_company:
            companies_affected.add(movement.to_company)
        if movement.from_company:
            companies_affected.add(movement.from_company)
    
    return TalentFlowSummary(
        total_movements=len(recent_movements),
        high_impact_movements=len(high_impact_movements),
        companies_affected=len(companies_affected),
        investment_signals_generated=len([s for s in investment_signals 
                                        if s.signal_generated_at >= cutoff_date]),
        average_confidence=sum(m.confidence_score for m in recent_movements) / len(recent_movements) if recent_movements else 0,
        top_movements=high_impact_movements[:5]
    )

# Investment Signals Endpoints
@app.post("/api/signals/query", response_model=List[InvestmentSignal])
async def query_investment_signals(query: InvestmentSignalQuery):
    """Query investment signals with filters"""
    filtered_signals = investment_signals
    
    # Apply filters
    if query.companies:
        filtered_signals = [s for s in filtered_signals if s.company_id in query.companies]
    
    if query.signal_types:
        filtered_signals = [s for s in filtered_signals if s.signal_type in query.signal_types]
    
    if query.min_confidence:
        filtered_signals = [s for s in filtered_signals if s.confidence_score >= query.min_confidence]
    
    if query.time_horizon:
        filtered_signals = [s for s in filtered_signals if s.time_horizon == query.time_horizon]
    
    # Sort by confidence and limit results
    filtered_signals.sort(key=lambda x: x.confidence_score, reverse=True)
    return filtered_signals[:query.max_results]

@app.get("/api/signals/recent", response_model=List[InvestmentSignal])
async def get_recent_signals(limit: int = 20, min_confidence: float = 0.5):
    """Get recent high-confidence investment signals"""
    recent_signals = [
        signal for signal in investment_signals
        if signal.confidence_score >= min_confidence
        and signal.signal_generated_at >= datetime.now() - timedelta(days=7)
    ]
    
    return sorted(recent_signals, key=lambda x: x.signal_generated_at, reverse=True)[:limit]

# Company Intelligence Endpoints
@app.get("/api/companies/{company_id}/talent-metrics", response_model=CompanyTalentMetrics)
async def get_company_talent_metrics(company_id: str):
    """Get comprehensive talent metrics for a company"""
    if company_id not in company_profiles:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company = company_profiles[company_id]
    
    # Calculate metrics from movements
    company_movements = [
        movement for movement in talent_movements
        if movement.to_company == company.name or movement.from_company == company.name
    ]
    
    recent_movements = [
        movement for movement in company_movements
        if movement.movement_date >= datetime.now() - timedelta(days=90)
    ]
    
    hires = [m for m in recent_movements if m.to_company == company.name]
    exits = [m for m in recent_movements if m.from_company == company.name]
    
    # Calculate scores (simplified for demo)
    talent_flow_score = min((len(hires) - len(exits)) / 10.0 + 0.5, 1.0)
    hiring_momentum = len(hires) / max(len(recent_movements), 1)
    retention_risk = len(exits) / max(len(company_movements), 1)
    
    return CompanyTalentMetrics(
        company_id=company_id,
        company_name=company.name,
        talent_flow_score=talent_flow_score,
        hiring_momentum=hiring_momentum,
        retention_risk=retention_risk,
        competitive_threat_level=0.3,  # Placeholder
        investment_recommendation="neutral",  # Would be calculated
        key_talent_moves=recent_movements[:5]
    )

@app.get("/api/companies/{company_id}/intelligence-report", response_model=TalentIntelligenceReport)
async def get_company_intelligence_report(company_id: str):
    """Generate comprehensive talent intelligence report for a company"""
    if company_id not in company_profiles:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company = company_profiles[company_id]
    
    # Generate comprehensive report (simplified for demo)
    report = TalentIntelligenceReport(
        id=f"report_{company_id}_{int(datetime.now().timestamp())}",
        company_id=company_id,
        talent_health_score=0.75,
        competitive_position="strong",
        key_risks=["Talent war in AI sector", "Remote work competition"],
        key_opportunities=["Emerging AI talent pool", "Research partnerships"],
        top_talent_retention=0.88,
        hiring_velocity=1.2,
        talent_quality_score=0.82,
        skill_diversity_index=0.65,
        recent_hires=[],  # Would be populated
        recent_exits=[],
        leadership_changes=[],
        investment_signals=[],
        risk_assessment={"retention": 0.2, "competition": 0.4},
        opportunity_analysis={"innovation": 0.8, "growth": 0.7},
        competitor_analysis={"talent_acquisition": 0.6},
        industry_benchmarks={"retention_rate": 0.85},
        report_confidence=0.78,
        data_freshness="24 hours",
        next_update=datetime.now() + timedelta(days=7)
    )
    
    return report

# Analytics Endpoints
@app.get("/api/analytics/influence-leaders")
async def get_influence_leaders(limit: int = 20):
    """Get top talent by influence score"""
    sorted_profiles = sorted(
        talent_profiles.values(),
        key=lambda x: x.influence_score,
        reverse=True
    )
    
    return [
        {
            "name": profile.name,
            "company": profile.current_company,
            "role": profile.current_role,
            "influence_score": profile.influence_score,
            "technical_score": profile.technical_score,
            "leadership_score": profile.leadership_score
        }
        for profile in sorted_profiles[:limit]
    ]

@app.get("/api/analytics/movement-trends")
async def get_movement_trends(days_back: int = 180):
    """Analyze talent movement trends"""
    cutoff_date = datetime.now() - timedelta(days=days_back)
    recent_movements = [
        movement for movement in talent_movements
        if movement.movement_date >= cutoff_date
    ]
    
    # Group by month
    monthly_trends = {}
    for movement in recent_movements:
        month_key = movement.movement_date.strftime("%Y-%m")
        if month_key not in monthly_trends:
            monthly_trends[month_key] = {"total": 0, "high_impact": 0}
        
        monthly_trends[month_key]["total"] += 1
        if movement.expected_impact in ['strong', 'critical']:
            monthly_trends[month_key]["high_impact"] += 1
    
    return {
        "monthly_trends": monthly_trends,
        "total_movements": len(recent_movements),
        "trend_analysis": "Increasing talent mobility in AI sector"
    }

# Background Tasks
async def collect_talent_data(profile_id: str):
    """Background task to collect comprehensive talent data"""
    try:
        if profile_id not in talent_profiles:
            return
        
        profile = talent_profiles[profile_id]
        logger.info(f"Collecting data for talent profile: {profile.name}")
        
        # Collect GitHub data
        if profile.github_username:
            github_data = await github_collector.get_user_profile(profile.github_username)
            if github_data:
                # Update profile with GitHub data
                profile.github_contributions = github_data.get('public_repos', 0)
                # Additional field updates...
        
        # Collect academic data
        if profile.name:
            academic_data = await academic_collector.get_researcher_publications(profile.name)
            if academic_data:
                profile.research_papers = academic_data.get('total_papers', 0)
        
        # Calculate influence scores
        influence_scores = influence_calculator.calculate_influence_score(profile)
        profile.influence_score = influence_scores.get('overall_influence', 0.5)
        profile.technical_score = influence_scores.get('technical_score', 0.5)
        profile.leadership_score = influence_scores.get('leadership_score', 0.5)
        profile.network_score = influence_scores.get('network_score', 0.5)
        
        profile.last_updated = datetime.now()
        talent_profiles[profile_id] = profile
        
        logger.info(f"Completed data collection for {profile.name}")
        
    except Exception as e:
        logger.error(f"Error in background data collection: {e}")

async def analyze_company_talent(company_id: str):
    """Background task to analyze company talent patterns"""
    try:
        if company_id not in company_profiles:
            return
        
        company = company_profiles[company_id]
        logger.info(f"Analyzing talent for company: {company.name}")
        
        # Perform talent flow analysis
        analysis = await company_tracker.analyze_company_talent_flow(company)
        
        # Update company profile with metrics
        if 'talent_flow_metrics' in analysis:
            metrics = analysis['talent_flow_metrics']
            company.recent_hires = metrics.get('hiring_velocity', 0)
            company.talent_retention_rate = metrics.get('retention_rate', 0.0)
        
        company.last_updated = datetime.now()
        company_profiles[company_id] = company
        
        logger.info(f"Completed talent analysis for {company.name}")
        
    except Exception as e:
        logger.error(f"Error in company talent analysis: {e}")

# Initialize with sample data for demonstration
@app.on_event("startup")
async def startup_event():
    """Initialize the application with sample data"""
    logger.info("Starting AI Talent Flow Intelligence API")
    
    # Load sample data if available
    await load_sample_data()

async def load_sample_data():
    """Load sample data for demonstration"""
    try:
        # Sample talent profiles
        sample_talents = [
            TalentProfile(
                id="talent_001",
                name="Dr. Emma Rodriguez",
                current_company="OpenAI",
                current_role="Senior Research Scientist",
                github_username="emma_ai",
                ai_experience_years=6,
                technical_skills=["Python", "PyTorch", "Transformers", "Computer Vision"],
                leadership_roles=["Research Lead"],
                influence_score=0.85,
                technical_score=0.90,
                leadership_score=0.75,
                network_score=0.80,
                research_papers=15,
                patents_filed=2,
                github_contributions=250
            ),
            TalentProfile(
                id="talent_002", 
                name="Alex Chen",
                current_company="Google DeepMind",
                current_role="Principal Engineer",
                github_username="alexchen_ml",
                ai_experience_years=10,
                technical_skills=["TensorFlow", "JAX", "Reinforcement Learning", "NLP"],
                leadership_roles=["Tech Lead", "Mentor"],
                influence_score=0.92,
                technical_score=0.95,
                leadership_score=0.85,
                network_score=0.90,
                research_papers=28,
                patents_filed=7,
                github_contributions=420
            )
        ]
        
        for talent in sample_talents:
            talent_profiles[talent.id] = talent
        
        # Sample companies
        sample_companies = [
            CompanyProfile(
                id="company_001",
                name="OpenAI",
                ticker_symbol="OPENAI",
                sector="Artificial Intelligence",
                company_size="large",
                ai_specializations=["Large Language Models", "AGI Research"],
                total_ai_talent=150,
                recent_hires=12,
                recent_exits=3
            ),
            CompanyProfile(
                id="company_002",
                name="Anthropic",
                ticker_symbol="ANTHR",
                sector="AI Safety",
                company_size="medium",
                ai_specializations=["Constitutional AI", "Safety Research"],
                total_ai_talent=80,
                recent_hires=15,
                recent_exits=2
            )
        ]
        
        for company in sample_companies:
            company_profiles[company.id] = company
        
        logger.info("Sample data loaded successfully")
        
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
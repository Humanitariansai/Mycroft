from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TalentMovementType(str, Enum):
    JOB_CHANGE = "job_change"
    PROMOTION = "promotion"
    ROLE_SHIFT = "role_shift"
    COMPANY_EXIT = "company_exit"
    STARTUP_JOIN = "startup_join"


class SignalStrength(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    CRITICAL = "critical"


class CompanySize(str, Enum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class TalentProfile(BaseModel):
    """Core talent profile data model"""
    id: str
    name: str
    current_company: str
    current_role: str
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    email: Optional[str] = None
    
    # Skills and expertise
    technical_skills: List[str] = []
    leadership_roles: List[str] = []
    specializations: List[str] = []
    certifications: List[str] = []
    
    # Influence metrics
    influence_score: float = Field(ge=0.0, le=1.0, description="Overall influence score")
    technical_score: float = Field(ge=0.0, le=1.0, description="Technical expertise score")
    leadership_score: float = Field(ge=0.0, le=1.0, description="Leadership impact score")
    network_score: float = Field(ge=0.0, le=1.0, description="Network centrality score")
    
    # Career history
    total_experience_years: int = 0
    ai_experience_years: int = 0
    companies_worked: List[str] = []
    
    # External presence
    github_contributions: int = 0
    research_papers: int = 0
    patents_filed: int = 0
    conference_talks: int = 0
    
    # Tracking metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    first_tracked: datetime = Field(default_factory=datetime.now)
    tracking_confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class CompanyProfile(BaseModel):
    """AI company profile for talent tracking"""
    id: str
    name: str
    ticker_symbol: Optional[str] = None
    
    # Company characteristics
    sector: str
    company_size: CompanySize
    market_cap: Optional[float] = None
    employee_count: Optional[int] = None
    founded_year: Optional[int] = None
    headquarters: Optional[str] = None
    
    # AI focus areas
    ai_specializations: List[str] = []
    tech_stack: List[str] = []
    research_areas: List[str] = []
    
    # Talent metrics
    total_ai_talent: int = 0
    senior_talent_count: int = 0
    recent_hires: int = 0
    recent_exits: int = 0
    talent_retention_rate: float = 0.0
    
    # Financial data
    revenue: Optional[float] = None
    funding_stage: Optional[str] = None
    last_funding_amount: Optional[float] = None
    
    # Tracking metadata
    last_updated: datetime = Field(default_factory=datetime.now)
    tracking_active: bool = True


class TalentMovement(BaseModel):
    """Talent movement event tracking"""
    id: str
    talent_id: str
    talent_name: str
    
    # Movement details
    movement_type: TalentMovementType
    from_company: Optional[str] = None
    to_company: str
    from_role: Optional[str] = None
    to_role: str
    movement_date: datetime
    
    # Impact assessment
    expected_impact: SignalStrength
    confidence_score: float = Field(ge=0.0, le=1.0)
    strategic_importance: float = Field(ge=0.0, le=1.0)
    
    # Context
    movement_reason: Optional[str] = None
    compensation_change: Optional[float] = None
    team_size_change: Optional[int] = None
    
    # Investment implications
    stock_impact_prediction: Optional[float] = None
    time_to_impact_months: Optional[int] = None
    related_opportunities: List[str] = []
    
    # Detection metadata
    detection_source: str
    detection_confidence: float = Field(ge=0.0, le=1.0)
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class CollaborationNetwork(BaseModel):
    """Professional collaboration relationships"""
    id: str
    talent_a_id: str
    talent_b_id: str
    
    # Relationship strength
    collaboration_strength: float = Field(ge=0.0, le=1.0)
    interaction_frequency: str  # daily, weekly, monthly, occasional
    relationship_type: str  # colleague, manager, collaborator, mentor
    
    # Collaboration context
    shared_projects: List[str] = []
    shared_companies: List[str] = []
    collaboration_duration_months: int = 0
    
    # Network analysis
    influence_transfer: float = Field(ge=0.0, le=1.0)
    knowledge_overlap: float = Field(ge=0.0, le=1.0)
    
    # Tracking
    first_detected: datetime = Field(default_factory=datetime.now)
    last_interaction: datetime = Field(default_factory=datetime.now)
    active: bool = True


class InvestmentSignal(BaseModel):
    """Investment signal generated from talent intelligence"""
    id: str
    signal_type: str
    company_id: str
    ticker_symbol: Optional[str] = None
    
    # Signal characteristics
    signal_strength: SignalStrength
    confidence_score: float = Field(ge=0.0, le=1.0)
    predicted_impact: str  # positive, negative, neutral
    
    # Investment recommendation
    recommended_action: str  # buy, sell, hold, watch
    position_size_recommendation: float = Field(ge=0.0, le=1.0)
    time_horizon: str  # short, medium, long
    
    # Supporting evidence
    triggering_events: List[str] = []
    supporting_talent_moves: List[str] = []
    risk_factors: List[str] = []
    
    # Predictions
    price_target_change: Optional[float] = None
    probability_of_success: float = Field(ge=0.0, le=1.0)
    expected_timeline_months: Optional[int] = None
    
    # Performance tracking
    signal_generated_at: datetime = Field(default_factory=datetime.now)
    signal_expires_at: Optional[datetime] = None
    actual_outcome: Optional[str] = None
    accuracy_score: Optional[float] = None


class TalentIntelligenceReport(BaseModel):
    """Comprehensive talent intelligence report"""
    id: str
    company_id: str
    report_date: datetime = Field(default_factory=datetime.now)
    
    # Executive summary
    talent_health_score: float = Field(ge=0.0, le=1.0)
    competitive_position: str
    key_risks: List[str] = []
    key_opportunities: List[str] = []
    
    # Talent metrics
    top_talent_retention: float
    hiring_velocity: float
    talent_quality_score: float
    skill_diversity_index: float
    
    # Recent movements
    recent_hires: List[TalentMovement] = []
    recent_exits: List[TalentMovement] = []
    leadership_changes: List[TalentMovement] = []
    
    # Investment implications
    investment_signals: List[InvestmentSignal] = []
    risk_assessment: Dict[str, float] = {}
    opportunity_analysis: Dict[str, float] = {}
    
    # Market context
    competitor_analysis: Dict[str, float] = {}
    industry_benchmarks: Dict[str, float] = {}
    
    # Confidence and metadata
    report_confidence: float = Field(ge=0.0, le=1.0)
    data_freshness: str
    next_update: datetime


# API Response Models
class TalentFlowSummary(BaseModel):
    """Summary response for talent flow analysis"""
    total_movements: int
    high_impact_movements: int
    companies_affected: int
    investment_signals_generated: int
    average_confidence: float
    top_movements: List[TalentMovement] = []


class CompanyTalentMetrics(BaseModel):
    """Company-specific talent metrics response"""
    company_id: str
    company_name: str
    talent_flow_score: float
    hiring_momentum: float
    retention_risk: float
    competitive_threat_level: float
    investment_recommendation: str
    key_talent_moves: List[TalentMovement] = []


# Request Models
class TalentTrackingRequest(BaseModel):
    """Request to start tracking a talent profile"""
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    name: Optional[str] = None
    current_company: str
    tracking_priority: str = "normal"  # low, normal, high, critical


class CompanyTrackingRequest(BaseModel):
    """Request to start tracking a company's talent"""
    company_name: str
    ticker_symbol: Optional[str] = None
    tracking_depth: str = "standard"  # basic, standard, comprehensive
    focus_areas: List[str] = []


class InvestmentSignalQuery(BaseModel):
    """Query parameters for investment signals"""
    companies: Optional[List[str]] = None
    signal_types: Optional[List[str]] = None
    min_confidence: float = 0.5
    time_horizon: Optional[str] = None
    max_results: int = 100
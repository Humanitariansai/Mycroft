from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime

class PortfolioHolding(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    shares: float = Field(..., gt=0, description="Number of shares")
    weight: float = Field(..., ge=0, le=1, description="Portfolio weight (0-1)")
    
    @validator('ticker')
    def ticker_uppercase(cls, v):
        return v.upper().strip()

class AnalysisParameters(BaseModel):
    lookback_days: int = Field(default=756, ge=252, le=2520, description="Historical lookback period")
    rolling_window: int = Field(default=252, ge=20, le=504, description="Rolling correlation window")
    vix_low_threshold: float = Field(default=15.0, ge=10, le=20, description="VIX low regime threshold")
    vix_high_threshold: float = Field(default=25.0, ge=20, le=40, description="VIX high regime threshold")
    min_regime_days: int = Field(default=20, ge=5, le=60, description="Minimum days in regime")
    use_5day_vix: bool = Field(default=True, description="Use 5-day rolling VIX average")

class AnalysisRequest(BaseModel):
    portfolio: List[PortfolioHolding] = Field(..., min_items=2, max_items=50)
    params: Optional[AnalysisParameters] = Field(default_factory=AnalysisParameters)
    
    @validator('portfolio')
    def validate_weights(cls, holdings):
        total_weight = sum(h.weight for h in holdings)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Portfolio weights must sum to 1.0, got {total_weight}")
        return holdings

class CorrelationMetrics(BaseModel):
    avg_pairwise_correlation: float
    max_correlation: float
    min_correlation: float
    effective_n_assets: float
    
class RegimeMetrics(BaseModel):
    low_vix: CorrelationMetrics
    medium_vix: CorrelationMetrics
    high_vix: CorrelationMetrics

class DegradationAnalysis(BaseModel):
    avg_corr_increase: float
    avg_corr_pct_increase: float
    max_corr_increase: float
    eff_assets_decrease: float
    eff_assets_pct_decrease: float

class AnalysisResponse(BaseModel):
    analysis_id: str
    timestamp: datetime
    portfolio_summary: Dict
    regime_metrics: RegimeMetrics
    degradation_analysis: DegradationAnalysis
    risk_flags: List[str]
    recommendations: List[str]
    visualizations: Dict
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime, date

class PortfolioHolding(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    shares: float = Field(..., gt=0, description="Number of shares")
    weight: float = Field(..., ge=0, le=1, description="Portfolio weight (0-1)")

    @validator('ticker')
    def ticker_uppercase(cls, v):
        return v.upper().strip()

class AnalysisParameters(BaseModel):
    lookback_days: int = Field(default=756, ge=252, le=2520)
    rolling_window: int = Field(default=252, ge=20, le=504)
    vix_low_threshold: float = Field(default=15.0, ge=10, le=20)
    vix_high_threshold: float = Field(default=25.0, ge=20, le=40)
    min_regime_days: int = Field(default=20, ge=5, le=60)
    use_5day_vix: bool = Field(default=True)

class AnalysisRequest(BaseModel):
    portfolio: List[PortfolioHolding] = Field(..., min_items=2, max_items=50)
    params: Optional[AnalysisParameters] = Field(default_factory=AnalysisParameters)

    @validator('portfolio')
    def validate_weights(cls, holdings):
        total = sum(h.weight for h in holdings)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Portfolio weights must sum to 1.0, got {total}")
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


class CrashPeriod(BaseModel):
    """A single crash window to simulate — predefined or custom"""
    key: str = Field(..., description="Unique identifier e.g. 'covid_2020'")
    name: str = Field(..., description="Human-readable label")
    start: str = Field(..., description="Start date YYYY-MM-DD")
    end: str = Field(..., description="End date YYYY-MM-DD")
    benchmark_ticker: str = Field(default="SPY")
    description: Optional[str] = None

    @validator('start', 'end')
    def valid_date(cls, v):
        datetime.strptime(v, "%Y-%m-%d")
        return v

class CrashSimulationRequest(BaseModel):
    portfolio: List[PortfolioHolding] = Field(..., min_items=2, max_items=50)
    # Which predefined crashes to include (empty = all four)
    selected_crashes: Optional[List[str]] = Field(
        default=None,
        description="Keys from PREDEFINED_CRASHES; None = run all"
    )
    # Optional custom window appended to the run
    custom_crash: Optional[CrashPeriod] = None

    @validator('portfolio')
    def validate_weights(cls, holdings):
        total = sum(h.weight for h in holdings)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")
        return holdings


class LossDriver(BaseModel):
    ticker: str
    weight: float
    period_return: float          # raw return during crash
    contribution_to_loss: float   # weight * return
    contribution_pct: float       # share of total portfolio loss


class DrawdownPoint(BaseModel):
    date: str
    portfolio_dd: float
    benchmark_dd: float


class CrashResult(BaseModel):
    key: str
    name: str
    description: str
    start: str
    end: str
    trading_days: int
    benchmark_ticker: str
    # Core metrics
    portfolio_total_return: float
    benchmark_total_return: float
    relative_performance: float       # portfolio - benchmark
    max_drawdown: float               # worst intra-period drawdown
    benchmark_max_drawdown: float
    recovery_days: Optional[int]      # None = not yet recovered
    # Decomposition
    loss_drivers: List[LossDriver]
    # Risk flags for this crash
    risk_flags: List[str]
    # Drawdown time-series for chart
    drawdown_series: List[DrawdownPoint]


class CrashSimulationResponse(BaseModel):
    simulation_id: str
    timestamp: datetime
    portfolio_summary: Dict
    crash_results: List[CrashResult]
    # Cross-crash summary
    worst_crash: str                  # key of worst crash by max_drawdown
    avg_max_drawdown: float
    avg_relative_performance: float
    overall_risk_flags: List[str]
    recommendations: List[str]
    # Visualizations
    visualizations: Dict              # base64 PNG values
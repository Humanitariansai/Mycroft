from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
from datetime import datetime, date

# ============================================================
# LAYER 1 — unchanged
# ============================================================

class PortfolioHolding(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    shares: float = Field(..., gt=0)
    weight: float = Field(..., ge=0, le=1)

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
            raise ValueError(f"Weights must sum to 1.0, got {total}")
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


# ============================================================
# LAYER 2 — unchanged
# ============================================================

class CrashPeriod(BaseModel):
    key: str
    name: str
    start: str
    end: str
    benchmark_ticker: str = Field(default="SPY")
    description: Optional[str] = None

    @validator('start', 'end')
    def valid_date(cls, v):
        datetime.strptime(v, "%Y-%m-%d")
        return v

class CrashSimulationRequest(BaseModel):
    portfolio: List[PortfolioHolding] = Field(..., min_items=2, max_items=50)
    selected_crashes: Optional[List[str]] = None
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
    period_return: float
    contribution_to_loss: float
    contribution_pct: float

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
    portfolio_total_return: float
    benchmark_total_return: float
    relative_performance: float
    max_drawdown: float
    benchmark_max_drawdown: float
    recovery_days: Optional[int]
    loss_drivers: List[LossDriver]
    risk_flags: List[str]
    drawdown_series: List[DrawdownPoint]

class CrashSimulationResponse(BaseModel):
    simulation_id: str
    timestamp: datetime
    portfolio_summary: Dict
    crash_results: List[CrashResult]
    worst_crash: str
    avg_max_drawdown: float
    avg_relative_performance: float
    overall_risk_flags: List[str]
    recommendations: List[str]
    visualizations: Dict


# ============================================================
# LAYER 3 — Factor Exposure Decomposition
# ============================================================

class FactorExposureParameters(BaseModel):
    lookback_days: int = Field(default=756, ge=252, le=2520,
                               description="Historical window for regression")
    rolling_window: int = Field(default=252, ge=60, le=504,
                                description="Window for rolling regression")
    vix_low_threshold: float = Field(default=15.0, ge=10, le=20)
    vix_high_threshold: float = Field(default=25.0, ge=20, le=40)
    min_regime_days: int = Field(default=20, ge=5, le=60)
    use_5day_vix: bool = Field(default=True)
    significance_level: float = Field(default=0.05, ge=0.01, le=0.10,
                                      description="p-value threshold for significance flags")

class FactorExposureRequest(BaseModel):
    portfolio: List[PortfolioHolding] = Field(..., min_items=2, max_items=50)
    params: Optional[FactorExposureParameters] = Field(
        default_factory=FactorExposureParameters
    )

    @validator('portfolio')
    def validate_weights(cls, holdings):
        total = sum(h.weight for h in holdings)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")
        return holdings


# ── Static regression output ─────────────────────────────────

class FactorLoading(BaseModel):
    factor: str                  # MKT, SMB, HML, RMW, CMA, UMD
    beta: float                  # regression coefficient
    t_stat: float
    p_value: float
    significant: bool            # p_value < significance_level
    contribution_to_variance: float   # β²·Var(F) / Var(R_p)  as fraction


class StaticRegressionResult(BaseModel):
    alpha: float                 # annualised Jensen's alpha
    alpha_t_stat: float
    alpha_p_value: float
    r_squared: float
    adj_r_squared: float
    unexplained_variance_pct: float   # (1 - R²) × 100
    factor_loadings: List[FactorLoading]
    dominant_factor: str         # factor with highest contribution_to_variance
    observations: int


# ── Rolling regression output ────────────────────────────────

class RollingLoadingPoint(BaseModel):
    date: str
    beta: float
    r_squared: float


class RollingFactorSeries(BaseModel):
    factor: str
    series: List[RollingLoadingPoint]
    drift_flag: bool             # True if range > DRIFT_THRESHOLD
    drift_magnitude: float       # max_beta - min_beta over window


# ── Regime-conditional loadings ──────────────────────────────

class RegimeFactorLoadings(BaseModel):
    regime: str                  # low / medium / high
    observations: int
    factor_loadings: List[FactorLoading]
    r_squared: float
    alpha: float


# ── Top-level response ────────────────────────────────────────

class FactorExposureResponse(BaseModel):
    exposure_id: str
    timestamp: datetime
    portfolio_summary: Dict
    # Full-period regression
    static_regression: StaticRegressionResult
    # 252-day rolling betas per factor
    rolling_regressions: List[RollingFactorSeries]
    # Regression split by VIX regime
    regime_regressions: List[RegimeFactorLoadings]
    # Risk flags
    risk_flags: List[str]
    recommendations: List[str]
    # base64 PNGs
    visualizations: Dict
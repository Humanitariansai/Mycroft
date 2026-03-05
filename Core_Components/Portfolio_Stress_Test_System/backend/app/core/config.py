from pydantic_settings import BaseSettings
from typing import Optional, Dict
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Portfolio Stress Testing - Layers 1, 2 & 3"
    VERSION: str = "3.0.0"

    # ── Layer 1 ──────────────────────────────────────────────
    DEFAULT_LOOKBACK_DAYS: int = 756
    DEFAULT_ROLLING_WINDOW: int = 252
    VIX_LOW_THRESHOLD: float = 15.0
    VIX_HIGH_THRESHOLD: float = 25.0
    MIN_REGIME_DAYS: int = 20

    # ── Shared ───────────────────────────────────────────────
    YFINANCE_MAX_RETRIES: int = 3
    YFINANCE_TIMEOUT: int = 30
    DATABASE_URL: Optional[str] = None

    # ── Layer 2 ──────────────────────────────────────────────
    PREDEFINED_CRASHES: Dict[str, Dict] = {
        "covid_2020": {
            "key": "covid_2020",
            "name": "COVID Crash",
            "start": "2020-02-19",
            "end": "2020-03-23",
            "benchmark_ticker": "SPY",
            "description": "Fastest bear market in history — S&P fell ~34% in 33 days"
        },
        "tech_selloff_2022": {
            "key": "tech_selloff_2022",
            "name": "Tech Selloff 2022",
            "start": "2022-01-03",
            "end": "2022-10-12",
            "benchmark_ticker": "QQQ",
            "description": "Rate-hike driven bear market — NASDAQ dropped ~33% over 9 months"
        },
        "q4_selloff_2018": {
            "key": "q4_selloff_2018",
            "name": "Q4 Selloff 2018",
            "start": "2018-09-20",
            "end": "2018-12-24",
            "benchmark_ticker": "SPY",
            "description": "Fed tightening + trade war fears — S&P fell ~19% in 3 months"
        },
        "flash_crash_2015": {
            "key": "flash_crash_2015",
            "name": "Flash Crash 2015",
            "start": "2015-08-01",
            "end": "2015-08-24",
            "benchmark_ticker": "SPY",
            "description": "China slowdown fears triggered rapid global selloff — S&P fell ~12%"
        }
    }

    SEVERE_DRAWDOWN_THRESHOLD: float = -0.20
    UNDERPERFORM_THRESHOLD: float = -0.05
    SLOW_RECOVERY_DAYS: int = 120
    CONCENTRATION_DRIVER_PCT: float = 0.15

    # ── Layer 3 ──────────────────────────────────────────────

    # Fama-French daily factor data URLs (Kenneth French Data Library)
    FF5_URL: str = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
        "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
    )
    MOMENTUM_URL: str = (
        "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
        "F-F_Momentum_Factor_daily_CSV.zip"
    )

    # Disk cache — store next to this file under data/
    FACTOR_CACHE_DIR: Path = Path(__file__).parent.parent / "data" / "factor_cache"
    FF5_CACHE_FILE: str = "ff5_daily.parquet"
    MOM_CACHE_FILE: str = "momentum_daily.parquet"
    FACTOR_CACHE_MAX_AGE_DAYS: int = 7      # refresh weekly

    # Risk flag thresholds
    HIGH_BETA_THRESHOLD: float = 1.3        # MKT beta flag
    SIGNIFICANT_TILT_THRESHOLD: float = 0.3 # |β| > 0.3 for non-MKT factors
    LOW_R2_THRESHOLD: float = 0.60          # unexplained variance flag
    HIGH_ALPHA_THRESHOLD: float = 0.05      # |annualised alpha| > 5%
    DRIFT_THRESHOLD: float = 0.0           # rolling beta range triggers drift flag
    CONCENTRATED_FACTOR_PCT: float = 0.50   # single factor > 50% of variance

    class Config:
        env_file = ".env"

settings = Settings()
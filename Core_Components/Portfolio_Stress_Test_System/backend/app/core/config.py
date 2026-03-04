from pydantic_settings import BaseSettings
from typing import Optional, Dict

class Settings(BaseSettings):
    APP_NAME: str = "Portfolio Stress Testing"
    VERSION: str = "2.0.0"

    DEFAULT_LOOKBACK_DAYS: int = 756
    DEFAULT_ROLLING_WINDOW: int = 252
    VIX_LOW_THRESHOLD: float = 15.0
    VIX_HIGH_THRESHOLD: float = 25.0
    MIN_REGIME_DAYS: int = 20

    YFINANCE_MAX_RETRIES: int = 3
    YFINANCE_TIMEOUT: int = 30
    DATABASE_URL: Optional[str] = None

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

    # ── Layer 2: risk thresholds ─────────────────────────────
    SEVERE_DRAWDOWN_THRESHOLD: float = -0.20        # flag if max_dd < -20%
    UNDERPERFORM_THRESHOLD: float = -0.05           # flag if rel_perf < -5%
    SLOW_RECOVERY_DAYS: int = 120                   # flag if recovery > 120 days
    CONCENTRATION_DRIVER_PCT: float = 0.15          # flag if single stock > 15% of loss

    class Config:
        env_file = ".env"

settings = Settings()
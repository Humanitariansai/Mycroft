from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Portfolio Stress Testing - Layer 1"
    VERSION: str = "1.0.0"
    
    # Analysis parameters
    DEFAULT_LOOKBACK_DAYS: int = 756  # 3 years
    DEFAULT_ROLLING_WINDOW: int = 252  # 1 year
    VIX_LOW_THRESHOLD: float = 15.0
    VIX_HIGH_THRESHOLD: float = 25.0
    MIN_REGIME_DAYS: int = 20
    
    # Data settings
    YFINANCE_MAX_RETRIES: int = 3
    YFINANCE_TIMEOUT: int = 30
    
    # Database (optional for future use)
    DATABASE_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()


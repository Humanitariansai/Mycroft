from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import JobStatus

# Configuration schemas
class ScraperConfig(BaseModel):
    recent_days: int = Field(default=45, ge=1, le=180)
    min_trade_size: int = Field(default=5000, ge=0)
    pages_to_scrape: int = Field(default=7, ge=1, le=20)

# Job schemas
class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    trades_count: int
    analyzed_count: int
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class JobCreate(BaseModel):
    config: Optional[ScraperConfig] = None

# Trade schemas
class TradeMetricsResponse(BaseModel):
    trade_price: Optional[float]
    price_before_start: Optional[float]
    price_after_end: Optional[float]
    change_to_trade: Optional[float]
    change_after_trade: Optional[float]
    avg_volume_before: Optional[int]
    trade_day_volume: Optional[int]
    volume_ratio: Optional[float]
    volatility: Optional[float]
    analyzed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TradeResponse(BaseModel):
    id: str
    politician: str
    party: str
    ticker: str
    company: str
    transaction_type: str
    trade_date: datetime
    published_date: datetime
    filed_after_days: int
    size_min: int
    size_max: int
    price: Optional[str]
    trade_link: str
    is_analyzed: bool
    metrics: Optional[TradeMetricsResponse] = None
    
    class Config:
        from_attributes = True

class TradeListResponse(BaseModel):
    trades: List[TradeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# Filter schemas
class TradeFilters(BaseModel):
    politician: Optional[str] = None
    party: Optional[str] = None
    transaction_type: Optional[str] = None
    ticker: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

# Statistics schemas
class PartyStats(BaseModel):
    party: str
    count: int
    avg_change_after: Optional[float]

class PoliticianStats(BaseModel):
    name: str
    party: str
    trade_count: int
    avg_change_after: Optional[float]

class TickerStats(BaseModel):
    ticker: str
    trade_count: int
    avg_change_after: Optional[float]

class PerformanceEntry(BaseModel):
    ticker: str
    politician: str
    party: str
    change_after_trade: float
    trade_date: datetime

class StatsResponse(BaseModel):
    total_trades: int
    analyzed_trades: int
    failed_analyses: int
    parties: List[PartyStats]
    top_politicians: List[PoliticianStats]
    top_tickers: List[TickerStats]
    best_performers: List[PerformanceEntry]
    worst_performers: List[PerformanceEntry]

# Stock data schemas
class StockDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class StockDataResponse(BaseModel):
    ticker: str
    trade_date: datetime
    data_points: List[StockDataPoint]
    days_before: int
    days_after: int
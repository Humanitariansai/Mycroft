from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    EXCHANGE = "exchange"

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    progress = Column(Float, default=0.0)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    trades_count = Column(Integer, default=0)
    analyzed_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    
    trades = relationship("Trade", back_populates="job", cascade="all, delete-orphan")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(String, primary_key=True)  # trade_id from scraper
    job_id = Column(String, ForeignKey("jobs.id"), index=True)
    
    # Politician info
    politician = Column(String, index=True)
    party = Column(String, index=True)
    
    # Trade info
    ticker = Column(String, index=True)
    company = Column(String)
    transaction_type = Column(String, index=True)
    trade_date = Column(DateTime, index=True)
    published_date = Column(DateTime)
    filed_after_days = Column(Integer)
    
    # Size info
    size_min = Column(Integer)
    size_max = Column(Integer)
    price = Column(String, nullable=True)
    
    # Links
    trade_link = Column(String)
    
    # Analysis results
    is_analyzed = Column(Integer, default=0, index=True)  # Boolean as int for SQLite
    analysis_error = Column(String, nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="trades")
    metrics = relationship("TradeMetrics", back_populates="trade", uselist=False, cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_ticker_date', 'ticker', 'trade_date'),
        Index('idx_politician_party', 'politician', 'party'),
    )

class TradeMetrics(Base):
    __tablename__ = "trade_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String, ForeignKey("trades.id"), unique=True, index=True)
    
    # Price metrics
    trade_price = Column(Float)
    price_before_start = Column(Float, nullable=True)
    price_after_end = Column(Float, nullable=True)
    change_to_trade = Column(Float, nullable=True)  # Percentage
    change_after_trade = Column(Float, nullable=True)  # Percentage
    
    # Volume metrics
    avg_volume_before = Column(Integer, nullable=True)
    trade_day_volume = Column(Integer, nullable=True)
    volume_ratio = Column(Float, nullable=True)
    
    # Volatility
    volatility = Column(Float, nullable=True)
    
    # Timestamps
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    trade = relationship("Trade", back_populates="metrics")

class StockDataCache(Base):
    __tablename__ = "stock_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True)
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
    price_data = Column(JSON)  # OHLCV data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_ticker_dates', 'ticker', 'start_date', 'end_date'),
    )
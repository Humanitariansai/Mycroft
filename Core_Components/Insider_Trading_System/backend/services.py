from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

from models import Job, Trade, TradeMetrics, StockDataCache, JobStatus
from schemas import TradeFilters, TradeResponse

logger = logging.getLogger(__name__)

class JobService:
    """Service for managing analysis jobs."""
    
    @staticmethod
    def create_job(db: Session, job_id: str) -> Job:
        """Create a new job."""
        job = Job(
            id=job_id,
            status=JobStatus.PENDING,
            progress=0.0,
            message="Job queued",
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def update_job(
        db: Session, 
        job_id: str, 
        status: Optional[JobStatus] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        trades_count: Optional[int] = None,
        analyzed_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[Job]:
        """Update job status and progress."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None
        
        if status:
            job.status = status
        if progress is not None:
            job.progress = progress
        if message:
            job.message = message
        if trades_count is not None:
            job.trades_count = trades_count
        if analyzed_count is not None:
            job.analyzed_count = analyzed_count
        if error_message:
            job.error_message = error_message
        
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return db.query(Job).filter(Job.id == job_id).first()
    
    @staticmethod
    def list_jobs(db: Session, limit: int = 50, offset: int = 0) -> Tuple[List[Job], int]:
        """List all jobs with pagination."""
        total = db.query(func.count(Job.id)).scalar()
        jobs = db.query(Job).order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
        return jobs, total

class TradeService:
    """Service for managing trades."""
    
    @staticmethod
    def create_trades(db: Session, job_id: str, trades_data: List[Dict]) -> List[Trade]:
        """Bulk create trades from scraper data."""
        trades = []
        for data in trades_data:
            trade = Trade(
                id=data['trade_id'],
                job_id=job_id,
                politician=data['politician'],
                party=data['party'],
                ticker=data['trade_ticker'],
                company=data['trade_issue'],
                transaction_type=data['transaction_type'],
                trade_date=data['trade_date_parsed'],
                published_date=data['published_date_parsed'],
                filed_after_days=data['filed_after'],
                size_min=data['trade_size'][0],
                size_max=data['trade_size'][1],
                price=data.get('price'),
                trade_link=data['trade_link'],
                is_analyzed=0
            )
            trades.append(trade)
        
        db.bulk_save_objects(trades, return_defaults=True)
        db.commit()
        return trades
    
    @staticmethod
    def get_trade(db: Session, trade_id: str) -> Optional[Trade]:
        """Get single trade with metrics."""
        return db.query(Trade).filter(Trade.id == trade_id).first()
    
    @staticmethod
    def list_trades(
        db: Session,
        filters: Optional[TradeFilters] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Trade], int]:
        """List trades with optional filters and pagination."""
        query = db.query(Trade).filter(Trade.is_analyzed == 1)
        
        if filters:
            if filters.politician:
                query = query.filter(Trade.politician.ilike(f"%{filters.politician}%"))
            if filters.party:
                query = query.filter(Trade.party == filters.party)
            if filters.transaction_type:
                query = query.filter(Trade.transaction_type.ilike(f"%{filters.transaction_type}%"))
            if filters.ticker:
                query = query.filter(Trade.ticker == filters.ticker.upper())
            if filters.min_size:
                query = query.filter(Trade.size_max >= filters.min_size)
            if filters.max_size:
                query = query.filter(Trade.size_min <= filters.max_size)
            if filters.date_from:
                query = query.filter(Trade.trade_date >= filters.date_from)
            if filters.date_to:
                query = query.filter(Trade.trade_date <= filters.date_to)
        
        total = query.count()
        offset = (page - 1) * page_size
        trades = query.order_by(Trade.trade_date.desc()).offset(offset).limit(page_size).all()
        
        return trades, total
    
    @staticmethod
    def update_trade_analysis(
        db: Session,
        trade_id: str,
        metrics: Dict,
        error: Optional[str] = None
    ) -> Optional[Trade]:
        """Update trade with analysis results."""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            return None
        
        if error:
            trade.is_analyzed = 0
            trade.analysis_error = error
        else:
            trade.is_analyzed = 1
            trade.analysis_error = None
            
            # Create or update metrics
            trade_metrics = db.query(TradeMetrics).filter(TradeMetrics.trade_id == trade_id).first()
            if not trade_metrics:
                trade_metrics = TradeMetrics(trade_id=trade_id)
                db.add(trade_metrics)
            
            trade_metrics.trade_price = metrics.get('trade_price')
            trade_metrics.price_before_start = metrics.get('price_before_start')
            trade_metrics.price_after_end = metrics.get('price_after_end')
            trade_metrics.change_to_trade = metrics.get('change_to_trade')
            trade_metrics.change_after_trade = metrics.get('change_after_trade')
            trade_metrics.avg_volume_before = metrics.get('avg_volume_before')
            trade_metrics.trade_day_volume = metrics.get('trade_day_volume')
            trade_metrics.volume_ratio = metrics.get('volume_ratio')
            trade_metrics.volatility = metrics.get('volatility')
            trade_metrics.analyzed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(trade)
        return trade

class StatsService:
    """Service for generating statistics."""
    
    @staticmethod
    def get_comprehensive_stats(db: Session) -> Dict:
        """Generate comprehensive statistics."""
        # Basic counts
        total_trades = db.query(func.count(Trade.id)).scalar()
        analyzed_trades = db.query(func.count(Trade.id)).filter(Trade.is_analyzed == 1).scalar()
        failed_trades = total_trades - analyzed_trades
        
        # Party distribution with performance
        party_stats = db.query(
            Trade.party,
            func.count(Trade.id).label('count'),
            func.avg(TradeMetrics.change_after_trade).label('avg_change')
        ).join(TradeMetrics, Trade.id == TradeMetrics.trade_id, isouter=True)\
         .group_by(Trade.party)\
         .all()
        
        # Top politicians
        politician_stats = db.query(
            Trade.politician,
            Trade.party,
            func.count(Trade.id).label('trade_count'),
            func.avg(TradeMetrics.change_after_trade).label('avg_change')
        ).join(TradeMetrics, Trade.id == TradeMetrics.trade_id, isouter=True)\
         .group_by(Trade.politician, Trade.party)\
         .order_by(func.count(Trade.id).desc())\
         .limit(10)\
         .all()
        
        # Top tickers
        ticker_stats = db.query(
            Trade.ticker,
            func.count(Trade.id).label('trade_count'),
            func.avg(TradeMetrics.change_after_trade).label('avg_change')
        ).join(TradeMetrics, Trade.id == TradeMetrics.trade_id, isouter=True)\
         .group_by(Trade.ticker)\
         .order_by(func.count(Trade.id).desc())\
         .limit(10)\
         .all()
        
        # Best and worst performers
        best_performers = db.query(Trade, TradeMetrics)\
            .join(TradeMetrics, Trade.id == TradeMetrics.trade_id)\
            .filter(TradeMetrics.change_after_trade.isnot(None))\
            .order_by(TradeMetrics.change_after_trade.desc())\
            .limit(10)\
            .all()
        
        worst_performers = db.query(Trade, TradeMetrics)\
            .join(TradeMetrics, Trade.id == TradeMetrics.trade_id)\
            .filter(TradeMetrics.change_after_trade.isnot(None))\
            .order_by(TradeMetrics.change_after_trade.asc())\
            .limit(10)\
            .all()
        
        return {
            'total_trades': total_trades,
            'analyzed_trades': analyzed_trades,
            'failed_analyses': failed_trades,
            'parties': [
                {
                    'party': p[0],
                    'count': p[1],
                    'avg_change_after': round(p[2], 2) if p[2] else None
                }
                for p in party_stats
            ],
            'top_politicians': [
                {
                    'name': p[0],
                    'party': p[1],
                    'trade_count': p[2],
                    'avg_change_after': round(p[3], 2) if p[3] else None
                }
                for p in politician_stats
            ],
            'top_tickers': [
                {
                    'ticker': t[0],
                    'trade_count': t[1],
                    'avg_change_after': round(t[2], 2) if t[2] else None
                }
                for t in ticker_stats
            ],
            'best_performers': [
                {
                    'ticker': trade.ticker,
                    'politician': trade.politician,
                    'party': trade.party,
                    'change_after_trade': round(metrics.change_after_trade, 2),
                    'trade_date': trade.trade_date
                }
                for trade, metrics in best_performers
            ],
            'worst_performers': [
                {
                    'ticker': trade.ticker,
                    'politician': trade.politician,
                    'party': trade.party,
                    'change_after_trade': round(metrics.change_after_trade, 2),
                    'trade_date': trade.trade_date
                }
                for trade, metrics in worst_performers
            ]
        }

class CacheService:
    """Service for stock data caching."""
    
    @staticmethod
    def get_cached_data(
        db: Session,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict]:
        """Retrieve cached stock data."""
        cache_entry = db.query(StockDataCache).filter(
            StockDataCache.ticker == ticker,
            StockDataCache.start_date == start_date,
            StockDataCache.end_date == end_date
        ).first()
        
        if cache_entry:
            # Check if cache is recent (within 24 hours)
            if datetime.utcnow() - cache_entry.created_at < timedelta(days=1):
                return cache_entry.price_data
        
        return None
    
    @staticmethod
    def save_cached_data(
        db: Session,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        data: Dict
    ):
        """Save stock data to cache."""
        # Delete old cache entry if exists
        db.query(StockDataCache).filter(
            StockDataCache.ticker == ticker,
            StockDataCache.start_date == start_date,
            StockDataCache.end_date == end_date
        ).delete()
        
        cache_entry = StockDataCache(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            price_data=data,
            created_at=datetime.utcnow()
        )
        db.add(cache_entry)
        db.commit()
    
    @staticmethod
    def get_stock_data_for_trade(
        db: Session,
        trade_id: str
    ) -> Optional[Dict]:
        """Get cached stock data for a specific trade."""
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            return None
        
        # Calculate date range (30 days before/after)
        start_date = trade.trade_date - timedelta(days=30)
        end_date = trade.trade_date + timedelta(days=30)
        
        return CacheService.get_cached_data(db, trade.ticker, start_date, end_date)
    
    @staticmethod
    def clear_cache(db: Session, older_than_days: Optional[int] = None) -> int:
        """Clear cached stock data."""
        query = db.query(StockDataCache)
        
        if older_than_days:
            cutoff = datetime.utcnow() - timedelta(days=older_than_days)
            query = query.filter(StockDataCache.created_at < cutoff)
        
        count = query.delete()
        db.commit()
        return count
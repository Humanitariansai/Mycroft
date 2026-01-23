import logging
from datetime import datetime
from typing import Dict

from database import get_db_context
from models import JobStatus
from services import JobService, TradeService
from analyzer_service import StockAnalyzer
from scraper import CapitolTradesScraperSelenium, Config as ScraperConfig

logger = logging.getLogger(__name__)

def run_analysis_job(job_id: str, config: Dict):
    """
    Background task to run scraping and analysis.
    
    This function runs in a background thread and manages the entire
    scraping and analysis pipeline.
    """
    logger.info(f"Starting job {job_id}")
    
    try:
        with get_db_context() as db:
            # Update job to scraping status
            JobService.update_job(
                db, job_id,
                status=JobStatus.SCRAPING,
                progress=10.0,
                message="Scraping Capitol Trades..."
            )
        
        # Configure and run scraper
        scraper_config = ScraperConfig()
        scraper_config.RECENT_DAYS = config.get('recent_days', 45)
        scraper_config.MIN_TRADE_SIZE = config.get('min_trade_size', 5000)
        scraper_config.PAGES_TO_SCRAPE = config.get('pages_to_scrape', 7)
        
        scraper = CapitolTradesScraperSelenium(scraper_config)
        raw_trades = scraper.run()
        
        if not raw_trades:
            with get_db_context() as db:
                JobService.update_job(
                    db, job_id,
                    status=JobStatus.COMPLETED,
                    progress=100.0,
                    message="No trades found"
                )
            return
        
        # Parse dates and prepare for database
        trades_for_db = []
        for trade in raw_trades:
            try:
                # Parse dates
                analyzer = StockAnalyzer()
                trade_date = analyzer.parse_trade_date(trade['traded_date'])
                published_date = analyzer.parse_trade_date(trade['published'])
                
                if not trade_date:
                    logger.warning(f"Could not parse trade date: {trade['traded_date']}")
                    continue
                
                trade['trade_date_parsed'] = trade_date
                trade['published_date_parsed'] = published_date or trade_date
                trades_for_db.append(trade)
            except Exception as e:
                logger.error(f"Error preparing trade {trade.get('trade_id')}: {e}")
        
        # Save trades to database
        with get_db_context() as db:
            JobService.update_job(
                db, job_id,
                progress=40.0,
                trades_count=len(trades_for_db),
                message=f"Found {len(trades_for_db)} trades, saving to database..."
            )
            
            TradeService.create_trades(db, job_id, trades_for_db)
        
        # Analysis phase
        with get_db_context() as db:
            JobService.update_job(
                db, job_id,
                status=JobStatus.ANALYZING,
                progress=50.0,
                message="Analyzing stock trends..."
            )
        
        analyzer = StockAnalyzer(days_before=30, days_after=30)
        
        for i, trade in enumerate(trades_for_db):
            try:
                with get_db_context() as db:
                    # Analyze trade
                    metrics, chart_filename, error = analyzer.analyze_trade(db, {
                        'ticker': trade['trade_ticker'],
                        'trade_date': trade['trade_date_parsed'],
                        'politician': trade['politician'],
                        'transaction_type': trade['transaction_type']
                    })
                    
                    # Update trade with results
                    TradeService.update_trade_analysis(
                        db,
                        trade['trade_id'],
                        metrics=metrics or {},
                        chart_filename=chart_filename,
                        error=error
                    )
                    
                    # Update job progress
                    progress = 50.0 + (50.0 * (i + 1) / len(trades_for_db))
                    JobService.update_job(
                        db, job_id,
                        progress=progress,
                        analyzed_count=i + 1,
                        message=f"Analyzing {i + 1}/{len(trades_for_db)}"
                    )
            
            except Exception as e:
                logger.error(f"Error analyzing trade {trade['trade_id']}: {e}")
                with get_db_context() as db:
                    TradeService.update_trade_analysis(
                        db,
                        trade['trade_id'],
                        metrics={},
                        error=str(e)
                    )
        
        # Mark job as complete
        with get_db_context() as db:
            JobService.update_job(
                db, job_id,
                status=JobStatus.COMPLETED,
                progress=100.0,
                message="Analysis complete"
            )
        
        logger.info(f"Job {job_id} completed successfully")
    
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        with get_db_context() as db:
            JobService.update_job(
                db, job_id,
                status=JobStatus.FAILED,
                message=f"Job failed: {str(e)}",
                error_message=str(e)
            )

def parse_trade_date(date_str: str) -> datetime:
    """Parse various date formats."""
    import re
    
    if not date_str:
        raise ValueError("Empty date string")
    
    date_str = date_str.strip()
    date_str = re.sub(r'([A-Za-z])(\d{4})', r'\1 \2', date_str)
    
    date_formats = [
        "%d %b %Y",
        "%d %B %Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%m/%d/%y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse date: {date_str}")
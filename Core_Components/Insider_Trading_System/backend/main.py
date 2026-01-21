from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uvicorn
import json
from pathlib import Path
import asyncio
from enum import Enum

from scraper import CapitolTradesScraperSelenium, Config as ScraperConfig
from analyzer import StockPriceAnalyzer, load_trades_from_file

app = FastAPI(title="Capitol Trades Analyzer", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CHARTS_DIR = Path("charts")
CHARTS_DIR.mkdir(exist_ok=True)

# In-memory job tracking
jobs = {}

class JobStatus(str, Enum):
    PENDING = "pending"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(BaseModel):
    job_id: str
    status: JobStatus
    progress: float
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    trades_count: int = 0
    analyzed_count: int = 0
    results: Optional[List[Dict]] = None

class ScraperConfigUpdate(BaseModel):
    recent_days: Optional[int] = 45
    min_trade_size: Optional[int] = 5000
    pages_to_scrape: Optional[int] = 7

class TradeFilter(BaseModel):
    politician: Optional[str] = None
    party: Optional[str] = None
    transaction_type: Optional[str] = None
    ticker: Optional[str] = None
    min_size: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "Capitol Trades Analyzer API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "scrape": "/api/scrape",
            "trades": "/api/trades",
            "jobs": "/api/jobs/{job_id}",
            "charts": "/api/charts/{filename}"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/config")
async def get_config():
    """Get current scraper configuration."""
    config = ScraperConfig()
    return {
        "recent_days": config.RECENT_DAYS,
        "min_trade_size": config.MIN_TRADE_SIZE,
        "pages_to_scrape": config.PAGES_TO_SCRAPE
    }

@app.post("/api/scrape")
async def start_scrape(
    background_tasks: BackgroundTasks,
    config: Optional[ScraperConfigUpdate] = None
):
    """Start a new scraping and analysis job."""
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    job = Job(
        job_id=job_id,
        status=JobStatus.PENDING,
        progress=0.0,
        message="Job queued",
        created_at=datetime.now()
    )
    jobs[job_id] = job
    
    background_tasks.add_task(run_scrape_job, job_id, config)
    
    return {"job_id": job_id, "status": "started"}

async def run_scrape_job(job_id: str, config: Optional[ScraperConfigUpdate]):
    """Background task to run scraping and analysis."""
    try:
        job = jobs[job_id]
        
        # Setup config
        scraper_config = ScraperConfig()
        if config:
            if config.recent_days:
                scraper_config.RECENT_DAYS = config.recent_days
            if config.min_trade_size:
                scraper_config.MIN_TRADE_SIZE = config.min_trade_size
            if config.pages_to_scrape:
                scraper_config.PAGES_TO_SCRAPE = config.pages_to_scrape
        
        # Scraping phase
        job.status = JobStatus.SCRAPING
        job.message = "Scraping Capitol Trades..."
        job.progress = 10.0
        
        scraper = CapitolTradesScraperSelenium(scraper_config)
        trades = scraper.run()
        
        job.trades_count = len(trades)
        job.progress = 40.0
        job.message = f"Found {len(trades)} trades"
        
        if not trades:
            job.status = JobStatus.COMPLETED
            job.message = "No trades found"
            job.completed_at = datetime.now()
            return
        
        # Analysis phase
        job.status = JobStatus.ANALYZING
        job.message = "Analyzing stock trends..."
        job.progress = 50.0
        
        analyzer = StockPriceAnalyzer(days_before=30, days_after=30)
        results = []
        
        for i, trade in enumerate(trades):
            result = analyzer.analyze_trade(trade)
            results.append(result)
            
            job.analyzed_count = i + 1
            job.progress = 50.0 + (50.0 * (i + 1) / len(trades))
            job.message = f"Analyzing {i + 1}/{len(trades)}"
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = DATA_DIR / f"results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        job.status = JobStatus.COMPLETED
        job.progress = 100.0
        job.message = "Analysis complete"
        job.completed_at = datetime.now()
        job.results = results
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.message = f"Error: {str(e)}"
        job.completed_at = datetime.now()

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status and results."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return job.dict()

@app.get("/api/jobs")
async def list_jobs():
    """List all jobs."""
    return {
        "jobs": [job.dict() for job in jobs.values()],
        "total": len(jobs)
    }

@app.get("/api/trades")
async def get_trades(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0
):
    """Get latest analyzed trades from most recent results file."""
    result_files = sorted(DATA_DIR.glob("results_*.json"), reverse=True)
    
    if not result_files:
        return {"trades": [], "total": 0}
    
    with open(result_files[0], 'r') as f:
        results = json.load(f)
    
    # Filter out errors
    trades = [r for r in results if 'error' not in r]
    
    total = len(trades)
    trades = trades[offset:offset + limit]
    
    return {
        "trades": trades,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.post("/api/trades/filter")
async def filter_trades(filters: TradeFilter):
    """Filter trades based on criteria."""
    result_files = sorted(DATA_DIR.glob("results_*.json"), reverse=True)
    
    if not result_files:
        return {"trades": [], "total": 0}
    
    with open(result_files[0], 'r') as f:
        results = json.load(f)
    
    trades = [r for r in results if 'error' not in r]
    
    # Apply filters
    if filters.politician:
        trades = [t for t in trades if filters.politician.lower() in t.get('politician', '').lower()]
    
    if filters.party:
        trades = [t for t in trades if t.get('party', '').lower() == filters.party.lower()]
    
    if filters.transaction_type:
        trades = [t for t in trades if filters.transaction_type.lower() in t.get('transaction_type', '').lower()]
    
    if filters.ticker:
        trades = [t for t in trades if filters.ticker.upper() == t.get('ticker', '').upper()]
    
    if filters.min_size:
        trades = [t for t in trades if t.get('trade_size_range') and t['trade_size_range'][1] >= filters.min_size]
    
    return {
        "trades": trades,
        "total": len(trades),
        "filters_applied": filters.dict(exclude_none=True)
    }

@app.get("/api/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get specific trade details."""
    result_files = sorted(DATA_DIR.glob("results_*.json"), reverse=True)
    
    if not result_files:
        raise HTTPException(status_code=404, detail="No results found")
    
    with open(result_files[0], 'r') as f:
        results = json.load(f)
    
    # Find trade by various IDs
    for trade in results:
        if (trade.get('ticker') == trade_id or 
            trade.get('politician', '').replace(' ', '_') == trade_id):
            return trade
    
    raise HTTPException(status_code=404, detail="Trade not found")

@app.get("/api/charts/{filename}")
async def get_chart(filename: str):
    """Serve chart images."""
    chart_path = CHARTS_DIR / filename
    
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail="Chart not found")
    
    return FileResponse(chart_path)

@app.get("/api/stats")
async def get_stats():
    """Get summary statistics."""
    result_files = sorted(DATA_DIR.glob("results_*.json"), reverse=True)
    
    if not result_files:
        return {
            "total_trades": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "parties": {},
            "top_politicians": [],
            "top_tickers": []
        }
    
    with open(result_files[0], 'r') as f:
        results = json.load(f)
    
    successful = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    # Party distribution
    parties = {}
    for trade in successful:
        party = trade.get('party', 'Unknown')
        parties[party] = parties.get(party, 0) + 1
    
    # Top politicians
    politicians = {}
    for trade in successful:
        pol = trade.get('politician', 'Unknown')
        politicians[pol] = politicians.get(pol, 0) + 1
    
    top_politicians = sorted(politicians.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Top tickers
    tickers = {}
    for trade in successful:
        ticker = trade.get('ticker', 'Unknown')
        tickers[ticker] = tickers.get(ticker, 0) + 1
    
    top_tickers = sorted(tickers.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Performance metrics
    performance = []
    for trade in successful:
        metrics = trade.get('metrics', {})
        if 'change_after_trade' in metrics:
            performance.append({
                'ticker': trade.get('ticker'),
                'politician': trade.get('politician'),
                'change': metrics['change_after_trade']
            })
    
    performance.sort(key=lambda x: abs(x['change']), reverse=True)
    
    return {
        "total_trades": len(results),
        "successful_analyses": len(successful),
        "failed_analyses": len(failed),
        "parties": parties,
        "top_politicians": [{"name": p[0], "count": p[1]} for p in top_politicians],
        "top_tickers": [{"ticker": t[0], "count": t[1]} for t in top_tickers],
        "top_performers": performance[:10]
    }

@app.delete("/api/cache")
async def clear_cache():
    """Clear stock data cache."""
    cache_dir = Path("stock_data_cache")
    count = 0
    
    if cache_dir.exists():
        for file in cache_dir.glob("*.json"):
            file.unlink()
            count += 1
    
    return {"message": f"Cleared {count} cache files"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
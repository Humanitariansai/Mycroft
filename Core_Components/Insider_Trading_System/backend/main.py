from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging
import math

from database import get_db, init_db
from schemas import (
    TradeResponse, TradeListResponse, TradeFilters,
    StatsResponse
)
import schemas
from services import TradeService, StatsService, CacheService, JobService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Capitol Trades Analyzer API",
    version="2.0.0",
    description="Read-only API for congressional stock trades analysis"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")

# Health check
@app.get("/")
async def root():
    return {
        "name": "Capitol Trades Analyzer API",
        "version": "2.0.0",
        "status": "operational",
        "note": "Data is populated by n8n workflow"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/jobs/{job_id}", response_model=schemas.JobResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get job status and progress."""
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/jobs", response_model=dict)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all jobs with pagination."""
    offset = (page - 1) * page_size
    jobs, total = JobService.list_jobs(db, limit=page_size, offset=offset)
    
    return {
        "jobs": [schemas.JobResponse.from_orm(job) for job in jobs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size)
    }

# Trade endpoints
@app.get("/api/trades", response_model=TradeListResponse)
async def list_trades(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get analyzed trades with pagination."""
    trades, total = TradeService.list_trades(
        db, filters=None, page=page, page_size=page_size
    )
    
    return TradeListResponse(
        trades=[TradeResponse.from_orm(trade) for trade in trades],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size)
    )

@app.post("/api/trades/filter", response_model=TradeListResponse)
async def filter_trades(
    filters: TradeFilters,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Filter trades based on criteria."""
    trades, total = TradeService.list_trades(
        db, filters=filters, page=page, page_size=page_size
    )
    
    return TradeListResponse(
        trades=[TradeResponse.from_orm(trade) for trade in trades],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size)
    )

@app.get("/api/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: str, db: Session = Depends(get_db)):
    """Get specific trade with full details."""
    trade = TradeService.get_trade(db, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return TradeResponse.from_orm(trade)

# Chart endpoints - now returns raw data instead of images
@app.get("/api/trades/{trade_id}/stock-data", response_model=schemas.StockDataResponse)
async def get_trade_stock_data(trade_id: str, db: Session = Depends(get_db)):
    """Get raw stock data for charting on frontend."""
    stock_data = CacheService.get_stock_data_for_trade(db, trade_id)
    
    if not stock_data:
        raise HTTPException(status_code=404, detail="Stock data not found")
    
    trade = TradeService.get_trade(db, trade_id)
    
    # Convert to response format
    data_points = []
    for date_str, values in sorted(stock_data.items()):
        data_points.append(schemas.StockDataPoint(
            date=date_str,
            open=values['Open'],
            high=values['High'],
            low=values['Low'],
            close=values['Close'],
            volume=values['Volume']
        ))
    
    return schemas.StockDataResponse(
        ticker=trade.ticker,
        trade_date=trade.trade_date,
        data_points=data_points,
        days_before=30,
        days_after=30
    )

# Statistics endpoints
@app.get("/api/stats", response_model=StatsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """Get comprehensive trading statistics."""
    stats = StatsService.get_comprehensive_stats(db)
    return StatsResponse(**stats)

# Cache management
@app.get("/api/config")
async def get_config():
    """Get current scraper configuration."""
    return {
        "message": "Scraping is handled by n8n workflow",
        "n8n_webhook": "Configure your n8n webhook URL in frontend"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
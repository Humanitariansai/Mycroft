from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import analyze_market_signals
import uvicorn

app = FastAPI(title="Market Signal System API")

# Add CORS middleware to allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    ticker: str

class HealthResponse(BaseModel):
    status: str
    message: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", message="Market Signal System is running")

@app.post("/api/analyze")
async def analyze_signals(request: AnalysisRequest):
    """
    Analyze market signals for a given ticker
    """
    try:
        if not request.ticker:
            raise HTTPException(status_code=400, detail="Ticker is required")
        
        # Convert to uppercase for consistency
        ticker = request.ticker.upper().strip()
        
        # Validate ticker format (1-5 letters)
        if not ticker.isalpha() or len(ticker) < 1 or len(ticker) > 5:
            raise HTTPException(status_code=400, detail="Invalid ticker format")
        
        # Run market signal analysis
        report = analyze_market_signals(ticker)
        
        return {
            "success": True,
            "data": report.model_dump()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analyze/{ticker}")
async def analyze_signals_get(ticker: str):
    """
    Alternative GET endpoint for analysis
    """
    request = AnalysisRequest(ticker=ticker)
    return await analyze_signals(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
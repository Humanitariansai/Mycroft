"""
Market Data Fetcher using yfinance
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from app.core.config import settings
from app.schemas.simulation import PortfolioAllocation

logger = logging.getLogger(__name__)

class MarketDataFetcher:
    """Fetch and process market data from free sources"""
    
    TICKERS = {
        "stocks": settings.STOCK_TICKER,
        "bonds": settings.BOND_TICKER,
        "cash": settings.CASH_TICKER
    }
    
    # Fallback historical parameters
    FALLBACK_PARAMS = {
        "stocks": {"mean": 0.007, "std": 0.04},   # ~9% annual, 15% vol
        "bonds": {"mean": 0.003, "std": 0.015},   # ~4% annual, 5% vol
        "cash": {"mean": 0.002, "std": 0.001}     # ~2.5% annual, minimal vol
    }
    
    @classmethod
    def fetch_historical_returns(
        cls,
        asset_class: str,
        years: int = None
    ) -> pd.Series:
        """Fetch historical returns for an asset class"""
        years = years or settings.MARKET_DATA_YEARS
        
        try:
            ticker = cls.TICKERS.get(asset_class, cls.TICKERS["stocks"])
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years*365)
            
            logger.info(f"Fetching {asset_class} data: {ticker}")
            
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if data.empty:
                logger.warning(f"No data retrieved for {ticker}, using fallback")
                return cls._get_fallback_returns(asset_class, years)
            
            # Calculate monthly returns
            monthly_data = data['Adj Close'].resample('M').last()
            returns = monthly_data.pct_change().dropna()
            
            logger.info(f"Retrieved {len(returns)} months of data for {asset_class}")
            return returns
            
        except Exception as e:
            logger.error(f"Error fetching {asset_class} data: {str(e)}")
            if settings.USE_FALLBACK_DATA:
                logger.info(f"Using fallback data for {asset_class}")
                return cls._get_fallback_returns(asset_class, years)
            raise
    
    @classmethod
    def _get_fallback_returns(cls, asset_class: str, years: int) -> pd.Series:
        """Generate synthetic returns based on historical averages"""
        param = cls.FALLBACK_PARAMS.get(asset_class, cls.FALLBACK_PARAMS["stocks"])
        num_months = years * 12
        
        returns = np.random.normal(
            param["mean"],
            param["std"],
            num_months
        )
        
        dates = pd.date_range(
            end=datetime.now(),
            periods=num_months,
            freq='M'
        )
        
        return pd.Series(returns, index=dates)
    
    @classmethod
    def get_portfolio_statistics(
        cls,
        allocation: PortfolioAllocation,
        years: int = None
    ) -> Dict[str, float]:
        """Calculate historical portfolio statistics"""
        years = years or settings.MARKET_DATA_YEARS
        
        # Fetch returns for each asset class
        stocks_returns = cls.fetch_historical_returns("stocks", years)
        bonds_returns = cls.fetch_historical_returns("bonds", years)
        cash_returns = cls.fetch_historical_returns("cash", years)
        
        # Align all series to same dates
        all_returns = pd.DataFrame({
            'stocks': stocks_returns,
            'bonds': bonds_returns,
            'cash': cash_returns
        }).dropna()
        
        # Calculate portfolio returns
        portfolio_returns = (
            all_returns['stocks'] * (allocation.stocks / 100) +
            all_returns['bonds'] * (allocation.bonds / 100) +
            all_returns['cash'] * (allocation.cash / 100)
        )
        
        # Calculate statistics
        annual_return = (1 + portfolio_returns.mean()) ** 12 - 1
        annual_vol = portfolio_returns.std() * np.sqrt(12)
        sharpe = (annual_return - 0.025) / annual_vol if annual_vol > 0 else 0
        
        return {
            "annual_return": round(annual_return, 4),
            "annual_volatility": round(annual_vol, 4),
            "sharpe_ratio": round(sharpe, 4),
            "monthly_mean": round(portfolio_returns.mean(), 6),
            "monthly_std": round(portfolio_returns.std(), 6),
            "max_drawdown": round(cls._calculate_max_drawdown(portfolio_returns), 4)
        }
    
    @staticmethod
    def _calculate_max_drawdown(returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

# Global instance
market_data_fetcher = MarketDataFetcher()
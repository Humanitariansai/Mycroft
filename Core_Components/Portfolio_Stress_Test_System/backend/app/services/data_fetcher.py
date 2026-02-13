import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger("portfolio_analysis.data_fetcher")

class DataFetchError(Exception):
    """Custom exception for data fetching errors"""
    pass

class DataFetcher:
    """Service for fetching market data from Yahoo Finance"""
    
    @staticmethod
    def fetch_price_data(
        tickers: List[str], 
        lookback_days: int
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical price data for given tickers
        
        Returns:
            Dict mapping ticker -> DataFrame with Date index and Close column
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        logger.info(f"Fetching price data for {len(tickers)} tickers from {start_date.date()} to {end_date.date()}")
        
        price_data = {}
        failed_tickers = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(start=start_date, end=end_date)
                
                if hist.empty:
                    failed_tickers.append(ticker)
                    logger.warning(f"No data found for {ticker}")
                    continue
                
                # Store only Close prices with Date index
                price_data[ticker] = hist[['Close']].copy()
                logger.info(f"Fetched {len(hist)} days of data for {ticker}")
                
            except Exception as e:
                failed_tickers.append(ticker)
                logger.error(f"Error fetching {ticker}: {str(e)}")
        
        if len(price_data) < 2:
            raise DataFetchError(
                f"Insufficient data. Successfully fetched {len(price_data)} tickers. "
                f"Failed: {failed_tickers}"
            )
        
        return price_data
    
    @staticmethod
    def fetch_vix_data(
        lookback_days: int, 
        use_5day_avg: bool = True
    ) -> pd.Series:
        """
        Fetch VIX historical data
        
        Returns:
            Series with Date index and VIX levels
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        logger.info(f"Fetching VIX data from {start_date.date()} to {end_date.date()}")
        
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise DataFetchError("No VIX data found")
            
            vix_series = hist['Close']
            
            # Apply 5-day rolling average to reduce noise
            if use_5day_avg:
                vix_series = vix_series.rolling(window=5, min_periods=1).mean()
                logger.info("Applied 5-day rolling average to VIX")
            
            logger.info(f"Fetched {len(vix_series)} days of VIX data")
            return vix_series
            
        except Exception as e:
            raise DataFetchError(f"Error fetching VIX: {str(e)}")

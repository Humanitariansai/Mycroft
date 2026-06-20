import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from models import AgentFindings
import requests
import os
from groq import Groq


# ── Agent 1: Technical Analysis Agent ────────────────────────────────────────

def technical_analysis_agent(ticker: str = "SPY") -> AgentFindings:
    """Technical Analysis Agent using Yahoo Finance for RSI, SMA signals"""
    insights = []
    metrics = {}
    
    try:
        # Get 50 days of data for technical indicators
        stock = yf.Ticker(ticker)
        hist = stock.history(period="50d")
        
        if hist.empty:
            return AgentFindings(
                agent_name="technical_analysis",
                insights=["Could not fetch price data"],
                metrics={},
                edge_score=None
            )
        
        current_price = hist['Close'].iloc[-1]
        sma_20 = hist['Close'].rolling(20).mean().iloc[-1]
        sma_50 = hist['Close'].rolling(50).mean().iloc[-1]
        
        # Simple RSI calculation
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        metrics["current_price"] = round(current_price, 2)
        metrics["sma_20"] = round(sma_20, 2)
        metrics["sma_50"] = round(sma_50, 2)
        metrics["rsi"] = round(current_rsi, 1)
        
        # Technical signals
        signal_score = 0.0
        
        # Price vs SMA signals
        if current_price > sma_20 and sma_20 > sma_50:
            insights.append(f"Bullish: Price ${current_price} above 20-day SMA ${sma_20:.2f} and 50-day SMA")
            signal_score += 0.3
        elif current_price < sma_20:
            insights.append(f"Bearish: Price ${current_price} below 20-day SMA ${sma_20:.2f}")
            signal_score -= 0.3
            
        # RSI signals  
        if current_rsi > 70:
            insights.append(f"RSI overbought at {current_rsi:.1f} - potential sell signal")
            signal_score -= 0.4
        elif current_rsi < 30:
            insights.append(f"RSI oversold at {current_rsi:.1f} - potential buy signal")
            signal_score += 0.4
        else:
            insights.append(f"RSI neutral at {current_rsi:.1f}")
            
        # Normalize signal_score to 0-1 range for edge_score
        edge_score = max(0, min(1, (signal_score + 1) / 2))
        
    except Exception as e:
        return AgentFindings(
            agent_name="technical_analysis",
            insights=[f"Error fetching technical data: {str(e)}"],
            metrics={},
            edge_score=None
        )
    
    return AgentFindings(
        agent_name="technical_analysis",
        insights=insights,
        metrics=metrics,
        edge_score=round(edge_score, 3)
    )


# ── Agent 2: News Sentiment Agent ────────────────────────────────────────────

def news_sentiment_agent(ticker: str = "SPY") -> AgentFindings:
    """Enhanced News Sentiment Agent with Analyst Data Integration"""
    insights = []
    metrics = {}
    
    try:
        # Get analyst data from Yahoo Finance
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Analyst recommendations
        recommendation_key = info.get('recommendationKey', 'hold')
        recommendation_mean = info.get('recommendationMean', 3.0)  # 1=Strong Buy, 5=Strong Sell
        target_price = info.get('targetMeanPrice', None)
        current_price = info.get('currentPrice', None)
        num_analysts = info.get('numberOfAnalystOpinions', 0)
        
        # Calculate analyst-based score
        analyst_score = 0.5  # Default neutral
        
        if recommendation_mean and recommendation_mean <= 2.0:  # Strong Buy/Buy
            analyst_score = 0.8
            if recommendation_mean <= 1.5:  # Strong Buy
                analyst_score = 0.9
        elif recommendation_mean <= 2.5:  # Moderate Buy
            analyst_score = 0.65
        elif recommendation_mean <= 3.5:  # Hold
            analyst_score = 0.5
        else:  # Sell/Strong Sell
            analyst_score = 0.3
        
        # Add target price analysis
        upside_potential = 0
        if target_price and current_price:
            upside_potential = ((target_price - current_price) / current_price) * 100
            
            if upside_potential > 25:
                analyst_score = min(analyst_score + 0.1, 1.0)  # Boost for high upside
            elif upside_potential < -10:
                analyst_score = max(analyst_score - 0.1, 0.0)  # Reduce for downside
        
        # Generate insights based on analyst data
        if recommendation_key == 'strong_buy':
            insights.append(f"Analyst Consensus: STRONG BUY ({num_analysts} analysts)")
        elif recommendation_key == 'buy':
            insights.append(f"Analyst Consensus: BUY ({num_analysts} analysts)")
        elif recommendation_key == 'hold':
            insights.append(f"Analyst Consensus: HOLD ({num_analysts} analysts)")
        else:
            insights.append(f"Analyst Consensus: {recommendation_key.upper().replace('_', ' ')} ({num_analysts} analysts)")
        
        if target_price and current_price:
            insights.append(f"Price target: ${target_price:.2f} ({upside_potential:+.1f}% potential)")
        
        # Try to get news headlines as secondary signal
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        news_url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&sortBy=publishedAt&pageSize=3&apiKey={os.getenv('NEWS_API_KEY')}"
        
        news_sentiment = 0
        try:
            news_response = requests.get(news_url, timeout=10)
            if news_response.status_code == 200:
                news_data = news_response.json()
                if news_data.get('articles'):
                    headlines = [article['title'] for article in news_data['articles'][:2]]
                    
                    for headline in headlines:
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{
                                "role": "user", 
                                "content": f"Analyze the sentiment of this text and respond with only: positive, negative, or neutral. Text: {headline}"
                            }],
                            max_tokens=10
                        )
                        
                        sentiment = response.choices[0].message.content.strip().lower()
                        if sentiment == "positive":
                            news_sentiment += 0.1
                        elif sentiment == "negative":
                            news_sentiment -= 0.1
        except Exception:
            pass  # News is secondary, don't fail on this
        
        # Combine analyst data (80% weight) with news sentiment (20% weight)
        final_score = (analyst_score * 0.8) + ((0.5 + news_sentiment) * 0.2)
        
        # Store metrics
        metrics["analyst_rating"] = recommendation_key
        metrics["analyst_score"] = round(recommendation_mean, 2) if recommendation_mean else None
        metrics["num_analysts"] = num_analysts
        metrics["target_price"] = round(target_price, 2) if target_price else None
        metrics["upside_potential"] = round(upside_potential, 1) if upside_potential else None
        
        edge_score = max(0.0, min(1.0, final_score))  # Ensure 0-1 range
        
    except Exception as e:
        return AgentFindings(
            agent_name="news_sentiment",
            insights=[f"Error fetching analyst data: {str(e)}"],
            metrics={},
            edge_score=None
        )
    
    return AgentFindings(
        agent_name="news_sentiment", 
        insights=insights,
        metrics=metrics,
        edge_score=round(edge_score, 3)
    )


# ── Agent 3: Market Fear/Greed Agent ──────────────────────────────────────────

def market_fear_greed_agent() -> AgentFindings:
    """Market Fear/Greed Index Agent with VIX-based sentiment"""
    insights = []
    metrics = {}
    
    try:
        # Use VIX (Volatility Index) as Fear/Greed proxy - more reliable than CNN
        vix_ticker = yf.Ticker("^VIX")
        vix_data = vix_ticker.history(period="1d")
        
        if not vix_data.empty:
            current_vix = vix_data['Close'].iloc[-1]
            
            # Convert VIX to Fear/Greed scale 
            # Higher VIX = More Fear = Lower score (contrarian opportunity)
            if current_vix > 30:  # High fear (VIX > 30)
                fear_greed_score = 25  
                rating = "Fear"
                edge_score = 0.7  # Contrarian buy opportunity
                insights.append(f"VIX at {current_vix:.1f} indicates high market fear")
                insights.append("High volatility suggests contrarian buying opportunity")
            elif current_vix > 20:  # Elevated concern
                fear_greed_score = 40  
                rating = "Fear" 
                edge_score = 0.6  # Moderate buy opportunity
                insights.append(f"VIX at {current_vix:.1f} shows elevated market concern")
                insights.append("Moderate fear levels suggest cautious buying opportunity")
            elif current_vix < 12:  # Low fear/complacency
                fear_greed_score = 75  
                rating = "Greed"
                edge_score = 0.3  # Caution - potential correction ahead
                insights.append(f"VIX at {current_vix:.1f} indicates market complacency")
                insights.append("Low volatility suggests potential for correction - consider profit taking")
            else:  # Normal range (12-20)
                fear_greed_score = 50  
                rating = "Neutral"
                edge_score = 0.5  
                insights.append(f"VIX at {current_vix:.1f} in normal range")
                insights.append("Balanced market sentiment - neutral positioning")
            
            metrics["vix_level"] = round(current_vix, 2)
            metrics["fear_greed_score"] = fear_greed_score
            metrics["fear_greed_rating"] = rating
            
        else:
            # Fallback if VIX data unavailable
            edge_score = 0.5
            insights.append("Market sentiment data temporarily unavailable")
            metrics["fear_greed_score"] = 50
            metrics["fear_greed_rating"] = "Neutral"
            
    except Exception as e:
        edge_score = 0.5
        insights.append("Market sentiment analysis unavailable")
        metrics["fear_greed_score"] = 50
        metrics["fear_greed_rating"] = "Neutral"
    
    return AgentFindings(
        agent_name="market_fear_greed",
        insights=insights,
        metrics=metrics,
        edge_score=round(edge_score, 3)
    )
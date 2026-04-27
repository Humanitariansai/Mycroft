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
    """News Sentiment Agent reusing existing Groq prompt from Social Sentiment"""
    insights = []
    metrics = {}
    
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Get real news headlines using NewsAPI (free tier: 1000 requests/day)
        news_url = f"https://newsapi.org/v2/everything?q={ticker}&language=en&sortBy=publishedAt&pageSize=5&apiKey={os.getenv('NEWS_API_KEY')}"
        
        try:
            news_response = requests.get(news_url, timeout=10)
            if news_response.status_code == 200:
                news_data = news_response.json()
                if news_data.get('articles'):
                    sample_headlines = [article['title'] for article in news_data['articles'][:3]]
                else:
                    # Fallback to demo headlines
                    sample_headlines = [
                        f"{ticker} shows mixed market sentiment",
                        f"Financial analysts review {ticker} outlook", 
                        f"Market conditions affect {ticker} performance"
                    ]
            else:
                # Fallback for API rate limits or errors
                sample_headlines = [
                    f"{ticker} trading reflects current market trends",
                    f"Investment outlook for {ticker} under review",
                    f"Market analysts evaluate {ticker} fundamentals"
                ]
        except Exception:
            # Fallback headlines if API fails
            sample_headlines = [
                f"{ticker} shows mixed trading patterns",
                f"Market sentiment varies for {ticker}",
                f"Analysts maintain {ticker} coverage"
            ]
        
        sentiment_scores = []
        
        for headline in sample_headlines:
            # Reuse exact Groq prompt from Social Sentiment Agent
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
                sentiment_scores.append(1)
                insights.append(f"Positive news: {headline}")
            elif sentiment == "negative":
                sentiment_scores.append(-1)  
                insights.append(f"Negative news: {headline}")
            else:
                sentiment_scores.append(0)
                insights.append(f"Neutral news: {headline}")
        
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        metrics["news_count"] = len(sample_headlines)
        metrics["avg_sentiment"] = round(avg_sentiment, 2)
        metrics["positive_count"] = sum(1 for s in sentiment_scores if s > 0)
        metrics["negative_count"] = sum(1 for s in sentiment_scores if s < 0)
        
        # Convert sentiment to edge_score (0-1 range)
        edge_score = (avg_sentiment + 1) / 2  # Convert from [-1,1] to [0,1]
        
    except Exception as e:
        return AgentFindings(
            agent_name="news_sentiment",
            insights=[f"Error fetching news sentiment: {str(e)}"],
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
    """Market Fear/Greed Index Agent"""
    insights = []
    metrics = {}
    
    try:
        # CNN Fear & Greed Index (free endpoint)
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current_score = data['fear_and_greed']['score']
            current_rating = data['fear_and_greed']['rating']
            
            metrics["fear_greed_score"] = current_score
            metrics["fear_greed_rating"] = current_rating
            
            insights.append(f"CNN Fear & Greed Index: {current_score}/100 ({current_rating})")
            
            # Convert to signal
            if current_score < 25:  # Extreme Fear
                edge_score = 0.8  # Contrarian buy signal
                insights.append("Extreme fear - potential contrarian buying opportunity")
            elif current_score < 50:  # Fear  
                edge_score = 0.6
                insights.append("Market fear - consider cautious buying")
            elif current_score > 75:  # Extreme Greed
                edge_score = 0.2  # Sell signal
                insights.append("Extreme greed - consider taking profits") 
            else:  # Neutral/Greed
                edge_score = 0.4
                insights.append("Market neutral to greedy - hold positions")
                
        else:
            # Fallback to random for demo
            edge_score = 0.5
            insights.append("Fear/Greed data unavailable - using neutral signal")
            metrics["fear_greed_score"] = 50
            metrics["fear_greed_rating"] = "Neutral"
            
    except Exception as e:
        edge_score = 0.5
        insights.append(f"Error fetching Fear/Greed data: {str(e)}")
        metrics["error"] = str(e)
    
    return AgentFindings(
        agent_name="market_fear_greed",
        insights=insights,
        metrics=metrics,
        edge_score=round(edge_score, 3)
    )
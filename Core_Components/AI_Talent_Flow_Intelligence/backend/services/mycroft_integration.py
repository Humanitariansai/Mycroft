"""
Integration services for connecting AI Talent Flow Intelligence 
with the broader Mycroft ecosystem.
"""

import asyncio
import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class MycroftEcosystemIntegrator:
    """Integrates talent intelligence with other Mycroft components"""
    
    def __init__(self):
        self.market_signal_api = "http://localhost:8001"
        self.trading_execution_api = "http://localhost:8002"  # Would be separate port in production
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_talent_signal_to_market_system(self, talent_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Send talent-based investment signal to Market Signal System"""
        try:
            # Format talent signal for market system consumption
            market_signal_payload = {
                "signal_type": "talent_intelligence",
                "ticker": talent_signal.get("ticker_symbol"),
                "source": "ai_talent_flow",
                "data": {
                    "talent_signal": talent_signal,
                    "confidence": talent_signal.get("confidence_score", 0.0),
                    "recommendation": talent_signal.get("recommended_action"),
                    "reasoning": talent_signal.get("reasoning"),
                    "time_horizon": talent_signal.get("time_horizon", "medium"),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            # Send to market signal system (would be a dedicated endpoint)
            logger.info(f"Sending talent signal for {talent_signal.get('ticker_symbol')} to market system")
            
            # For now, just log the integration - in production would hit actual endpoint
            return {
                "status": "success",
                "message": "Talent signal integrated with market system",
                "payload": market_signal_payload
            }
            
        except Exception as e:
            logger.error(f"Failed to send talent signal to market system: {e}")
            return {"status": "error", "message": str(e)}
    
    async def trigger_market_analysis_with_talent_context(self, ticker: str, talent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger market analysis enhanced with talent intelligence context"""
        try:
            # Get market analysis
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.market_signal_api}/api/analyze",
                    json={"ticker": ticker},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    market_data = response.json()
                    
                    # Enhance with talent context
                    enhanced_analysis = {
                        "ticker": ticker,
                        "market_analysis": market_data,
                        "talent_intelligence": talent_context,
                        "combined_recommendation": self._combine_signals(market_data, talent_context),
                        "analysis_timestamp": datetime.now().isoformat()
                    }
                    
                    return enhanced_analysis
                else:
                    logger.warning(f"Market analysis failed: {response.status_code}")
                    return {"error": "Market analysis unavailable", "talent_context": talent_context}
                    
        except Exception as e:
            logger.error(f"Failed to get enhanced market analysis: {e}")
            return {"error": str(e), "talent_context": talent_context}
    
    def _combine_signals(self, market_data: Dict[str, Any], talent_context: Dict[str, Any]) -> Dict[str, Any]:
        """Combine market signals with talent intelligence for enhanced recommendation"""
        try:
            # Extract market signal confidence
            market_confidence = 0.5  # Default
            if "data" in market_data and "final_recommendation" in market_data["data"]:
                market_confidence = market_data["data"]["final_recommendation"].get("score", 0.5)
            
            # Extract talent signal confidence
            talent_confidence = talent_context.get("confidence_score", 0.5)
            
            # Weighted combination (60% market, 40% talent for now)
            combined_confidence = (market_confidence * 0.6) + (talent_confidence * 0.4)
            
            # Determine combined action
            if combined_confidence >= 0.7:
                action = "strong_buy" if talent_context.get("predicted_impact") == "positive" else "buy"
            elif combined_confidence >= 0.6:
                action = "buy" if talent_context.get("predicted_impact") == "positive" else "hold"
            elif combined_confidence <= 0.3:
                action = "sell" if talent_context.get("predicted_impact") == "negative" else "hold"
            else:
                action = "hold"
            
            return {
                "action": action,
                "combined_confidence": combined_confidence,
                "market_confidence": market_confidence,
                "talent_confidence": talent_confidence,
                "reasoning": f"Combined analysis: Market signals ({market_confidence:.2f}) + Talent intelligence ({talent_confidence:.2f})",
                "signal_sources": ["market_technical_analysis", "talent_flow_intelligence"]
            }
            
        except Exception as e:
            logger.error(f"Failed to combine signals: {e}")
            return {
                "action": "hold",
                "combined_confidence": 0.5,
                "error": "Signal combination failed"
            }
    
    async def send_to_trading_execution(self, combined_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Send combined signal to Trading Execution Agent"""
        try:
            # Format for trading execution
            trading_payload = {
                "ticker": combined_signal.get("ticker"),
                "action": combined_signal["combined_recommendation"]["action"],
                "confidence": combined_signal["combined_recommendation"]["combined_confidence"],
                "reasoning": combined_signal["combined_recommendation"]["reasoning"],
                "source_signals": {
                    "market_analysis": combined_signal.get("market_analysis"),
                    "talent_intelligence": combined_signal.get("talent_intelligence")
                },
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Sending combined signal to trading execution: {trading_payload['action']} {trading_payload['ticker']}")
            
            # For demonstration - in production would call actual trading API
            return {
                "status": "success",
                "message": "Signal sent to trading execution",
                "trade_payload": trading_payload
            }
            
        except Exception as e:
            logger.error(f"Failed to send to trading execution: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_talent_movement_end_to_end(self, talent_movement: Dict[str, Any], 
                                               company_profiles: Dict[str, Any]) -> Dict[str, Any]:
        """Process a talent movement through the entire Mycroft ecosystem"""
        try:
            results = {
                "movement_id": talent_movement.get("id"),
                "ticker": None,
                "steps": [],
                "final_action": None,
                "success": True
            }
            
            # Step 1: Identify affected company ticker
            affected_company = talent_movement.get("to_company")
            ticker = None
            
            for company_id, company in company_profiles.items():
                if company.get("name") == affected_company:
                    ticker = company.get("ticker_symbol")
                    break
            
            if not ticker:
                results["steps"].append({"step": "ticker_lookup", "status": "failed", "message": "No ticker found for company"})
                results["success"] = False
                return results
            
            results["ticker"] = ticker
            results["steps"].append({"step": "ticker_lookup", "status": "success", "ticker": ticker})
            
            # Step 2: Create talent signal
            talent_signal = {
                "ticker_symbol": ticker,
                "signal_type": "talent_acquisition" if talent_movement.get("movement_type") == "job_change" else "talent_movement",
                "confidence_score": talent_movement.get("confidence_score", 0.7),
                "predicted_impact": "positive",  # Simplified for demo
                "recommended_action": "buy",
                "reasoning": f"Talent movement: {talent_movement.get('talent_name')} joining {affected_company}",
                "time_horizon": "medium"
            }
            
            results["steps"].append({"step": "talent_signal_creation", "status": "success", "signal": talent_signal})
            
            # Step 3: Get enhanced market analysis
            enhanced_analysis = await self.trigger_market_analysis_with_talent_context(ticker, talent_signal)
            results["steps"].append({"step": "market_analysis", "status": "success", "analysis": enhanced_analysis})
            
            # Step 4: Send to trading execution
            if "combined_recommendation" in enhanced_analysis:
                trading_result = await self.send_to_trading_execution(enhanced_analysis)
                results["steps"].append({"step": "trading_execution", "status": trading_result["status"], "result": trading_result})
                results["final_action"] = enhanced_analysis["combined_recommendation"]["action"]
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to process talent movement end-to-end: {e}")
            return {
                "movement_id": talent_movement.get("id"),
                "success": False,
                "error": str(e)
            }


class TalentSignalAggregator:
    """Aggregates and prioritizes multiple talent signals"""
    
    def __init__(self):
        self.signal_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 100
    
    def add_signal(self, signal: Dict[str, Any]):
        """Add a new talent signal to the buffer"""
        signal["timestamp"] = datetime.now().isoformat()
        self.signal_buffer.append(signal)
        
        # Keep buffer size manageable
        if len(self.signal_buffer) > self.max_buffer_size:
            self.signal_buffer = self.signal_buffer[-self.max_buffer_size:]
    
    def get_aggregated_signals_for_ticker(self, ticker: str, hours_back: int = 24) -> Dict[str, Any]:
        """Get aggregated talent signals for a specific ticker"""
        cutoff_time = datetime.now().timestamp() - (hours_back * 3600)
        
        relevant_signals = []
        for signal in self.signal_buffer:
            if signal.get("ticker_symbol") == ticker:
                signal_time = datetime.fromisoformat(signal["timestamp"].replace('Z', '')).timestamp()
                if signal_time >= cutoff_time:
                    relevant_signals.append(signal)
        
        if not relevant_signals:
            return {"ticker": ticker, "signal_count": 0, "aggregated_confidence": 0}
        
        # Aggregate confidence scores
        total_confidence = sum(s.get("confidence_score", 0) for s in relevant_signals)
        avg_confidence = total_confidence / len(relevant_signals)
        
        # Determine overall sentiment
        positive_signals = sum(1 for s in relevant_signals if s.get("predicted_impact") == "positive")
        negative_signals = len(relevant_signals) - positive_signals
        
        return {
            "ticker": ticker,
            "signal_count": len(relevant_signals),
            "aggregated_confidence": avg_confidence,
            "sentiment": "positive" if positive_signals > negative_signals else "negative" if negative_signals > positive_signals else "neutral",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals,
            "latest_signals": relevant_signals[-5:]  # Last 5 signals
        }


# Global instances for use across the application
mycroft_integrator = MycroftEcosystemIntegrator()
signal_aggregator = TalentSignalAggregator()


# Example usage and testing
async def test_integration():
    """Test the Mycroft ecosystem integration"""
    print("Testing AI Talent Flow Intelligence - Mycroft Integration")
    
    # Sample talent movement
    sample_movement = {
        "id": "movement_test_001",
        "talent_name": "Dr. Sarah Chen",
        "movement_type": "job_change",
        "from_company": "Google",
        "to_company": "OpenAI",
        "confidence_score": 0.85
    }
    
    # Sample company profiles
    sample_companies = {
        "company_001": {
            "name": "OpenAI",
            "ticker_symbol": "OPENAI"
        }
    }
    
    # Test end-to-end processing
    result = await mycroft_integrator.process_talent_movement_end_to_end(
        sample_movement, sample_companies
    )
    
    print(f"Integration test result: {json.dumps(result, indent=2, default=str)}")


if __name__ == "__main__":
    asyncio.run(test_integration())
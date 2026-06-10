#!/usr/bin/env python3
"""
Trading Execution Agent - Integration Testing Script
Tests all components of the trading workflow independently
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class TradingExecutionTester:
    def __init__(self):
        self.market_signals_url = "http://localhost:8001/api/analyze"
        self.results = []
        
    def test_market_signals(self, ticker: str) -> Dict[str, Any]:
        """Test Market Signal System integration"""
        print(f"\n🔍 Testing Market Signals for {ticker}...")
        
        try:
            response = requests.post(
                self.market_signals_url,
                json={"ticker": ticker},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                final_rec = data["data"]["final_recommendation"]
                ensemble_vote = data["data"]["resolution_summary"]["ensemble_voting"]
                
                # Convert score to decision based on thresholds
                score = final_rec.get("score", 0.5)
                if score >= 0.55:
                    decision = "BUY"
                elif score <= 0.45:
                    decision = "SELL"
                else:
                    decision = "HOLD"
                    
                result = {
                    "ticker": ticker,
                    "recommendation": decision,
                    "score": score,
                    "conflicts": data["data"]["conflict_analysis"]["has_conflicts"],
                    "ensemble_decision": ensemble_vote.get("decision", "hold").upper(),
                    "agent_scores": {
                        finding["agent_name"]: finding["edge_score"] 
                        for finding in data["data"]["agent_findings"]
                    }
                }
                
                print(f"✅ {ticker}: {result['recommendation']} (Score: {result['score']:.3f})")
                return result
                
            else:
                print(f"❌ API Error: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"❌ Connection Error: {str(e)}")
            return {"error": str(e)}
    
    def simulate_risk_assessment(self, ticker: str, position_data: Dict) -> Dict[str, Any]:
        """Simulate Risk Management Agent (since we don't have webhook setup)"""
        print(f"\n⚖️ Simulating Risk Assessment for {ticker}...")
        
        # Simulate risk scoring logic
        current_value = position_data.get("current_value", 10000)
        position_percent = (current_value / 100000) * 100  # Assume $100k portfolio
        
        # Risk factors
        risk_score = 0.0
        if position_percent > 5.0:
            risk_score += 0.2  # Oversized position
        if position_percent > 10.0:
            risk_score += 0.3  # Severely oversized
            
        # Add some market-based risk
        risk_score += min(0.2, position_percent / 30.0)
        
        # Calculate max additional shares (allow some flexibility)
        target_position_value = min(8000, current_value + 2000)  # Allow up to $8K or current + $2K
        max_additional = max(0, int((target_position_value - current_value) / 200))  # Assume $200/share avg
        result = {
            "ticker": ticker,
            "risk_score": min(1.0, risk_score),
            "position_percent": position_percent,
            "max_additional_shares": max_additional,
            "recommendation": "APPROVE" if risk_score < 0.7 else "REJECT"
        }
        
        print(f"✅ Risk Score: {result['risk_score']:.3f} ({result['recommendation']})")
        return result
    
    def simulate_trading_decision(self, market_signal: Dict, risk_assessment: Dict) -> Dict[str, Any]:
        """Combine market signals and risk assessment to make trading decision"""
        print(f"\n🎯 Making Trading Decision...")
        
        ticker = market_signal.get("ticker")
        signal = market_signal.get("recommendation", "HOLD")
        confidence = market_signal.get("score", 0.5)
        risk_score = risk_assessment.get("risk_score", 0.5)
        
        # Decision logic (matches n8n workflow)
        action = "HOLD"
        quantity = 0
        reason = ""
        
        if risk_score > 0.7:
            action = "HOLD"
            reason = f"Risk score too high: {risk_score:.3f}"
        elif confidence < 0.55:  # Match the BUY threshold
            action = "HOLD"
            reason = f"Signal confidence too low: {confidence:.3f}"
        elif signal == "BUY" and risk_assessment.get("recommendation") == "APPROVE":
            action = "BUY"
            quantity = min(50, risk_assessment.get("max_additional_shares", 0))
            reason = "Strong buy signal with acceptable risk"
        elif signal == "SELL":
            action = "SELL"
            quantity = 25  # Assume some position to sell
            reason = "Sell signal triggered"
        else:
            reason = "Conditions not met for trade execution"
        
        result = {
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "reason": reason,
            "confidence": confidence,
            "risk_score": risk_score,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"✅ Decision: {action} {quantity} shares - {reason}")
        return result
    
    def simulate_alpaca_order(self, trade_decision: Dict) -> Dict[str, Any]:
        """Simulate Alpaca API order placement (since we don't have real credentials)"""
        print(f"\n📈 Simulating Order Placement...")
        
        if trade_decision["quantity"] == 0:
            result = {
                "status": "SKIPPED",
                "reason": "No quantity to trade"
            }
            print("⏭️ Order skipped - no quantity")
            return result
        
        # Simulate API call delay
        time.sleep(1)
        
        # Simulate successful order
        result = {
            "id": f"ORDER_{int(time.time())}",
            "symbol": trade_decision["ticker"],
            "qty": trade_decision["quantity"],
            "side": trade_decision["action"].lower(),
            "type": "market",
            "status": "filled",
            "filled_avg_price": 200.00,  # Mock price
            "filled_at": datetime.now().isoformat()
        }
        
        print(f"✅ Order Filled: {result['side'].upper()} {result['qty']} {result['symbol']} @ ${result['filled_avg_price']}")
        return result
    
    def run_full_workflow_test(self, test_portfolio: List[Dict]) -> List[Dict]:
        """Run complete trading workflow for test portfolio"""
        print("=" * 60)
        print("🚀 TRADING EXECUTION WORKFLOW TEST")
        print("=" * 60)
        
        workflow_results = []
        
        for position in test_portfolio:
            ticker = position["ticker"]
            print(f"\n📊 Processing {ticker}...")
            
            # Step 1: Get market signals
            market_signal = self.test_market_signals(ticker)
            
            # Step 2: Risk assessment
            risk_assessment = self.simulate_risk_assessment(ticker, position)
            
            # Step 3: Trading decision
            trade_decision = self.simulate_trading_decision(market_signal, risk_assessment)
            
            # Step 4: Order execution
            order_result = self.simulate_alpaca_order(trade_decision)
            
            # Combine results
            workflow_result = {
                "ticker": ticker,
                "market_signal": market_signal,
                "risk_assessment": risk_assessment,
                "trade_decision": trade_decision,
                "order_result": order_result,
                "timestamp": datetime.now().isoformat()
            }
            
            workflow_results.append(workflow_result)
            
            print(f"✅ {ticker} workflow completed")
            print("-" * 40)
        
        return workflow_results
    
    def generate_test_report(self, results: List[Dict]) -> None:
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 TRADING EXECUTION TEST REPORT")
        print("=" * 60)
        
        total_tests = len(results)
        successful_signals = sum(1 for r in results if "error" not in r["market_signal"])
        trades_executed = sum(1 for r in results if r["trade_decision"]["quantity"] > 0)
        
        print(f"\n📊 Test Summary:")
        print(f"   Total Positions Tested: {total_tests}")
        print(f"   Successful API Calls: {successful_signals}/{total_tests}")
        print(f"   Trades Executed: {trades_executed}/{total_tests}")
        print(f"   Success Rate: {(successful_signals/total_tests)*100:.1f}%")
        
        print(f"\n📈 Trade Decisions:")
        actions = {}
        for result in results:
            action = result["trade_decision"]["action"]
            actions[action] = actions.get(action, 0) + 1
        
        for action, count in actions.items():
            print(f"   {action}: {count}")
        
        print(f"\n⚠️ Risk Assessment:")
        high_risk = sum(1 for r in results if r["risk_assessment"]["risk_score"] > 0.7)
        print(f"   High Risk Positions: {high_risk}/{total_tests}")
        
        print(f"\n🎯 Signal Quality:")
        avg_confidence = sum(r["market_signal"].get("score", 0) for r in results if "error" not in r["market_signal"]) / max(successful_signals, 1)
        print(f"   Average Signal Confidence: {avg_confidence:.3f}")
        
        print(f"\n🔍 Detailed Results:")
        for result in results:
            ticker = result["ticker"]
            signal = result["market_signal"].get("recommendation", "ERROR")
            confidence = result["market_signal"].get("score", 0)
            action = result["trade_decision"]["action"]
            quantity = result["trade_decision"]["quantity"]
            
            print(f"   {ticker}: {signal} ({confidence:.2f}) → {action} {quantity}")

def main():
    """Main testing function"""
    tester = TradingExecutionTester()
    
    # Test portfolio
    test_portfolio = [
        {"ticker": "AAPL", "current_value": 8750, "target_allocation": 15.0},
        {"ticker": "NVDA", "current_value": 7020, "target_allocation": 20.0}, 
        {"ticker": "MSFT", "current_value": 10956, "target_allocation": 15.0},
        {"ticker": "TSLA", "current_value": 3916, "target_allocation": 10.0},
        {"ticker": "SPY", "current_value": 42530, "target_allocation": 30.0}
    ]
    
    # Run complete workflow test
    results = tester.run_full_workflow_test(test_portfolio)
    
    # Generate report
    tester.generate_test_report(results)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trading_test_results_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: {filename}")
    print(f"\n🎉 Trading Execution Agent testing completed!")

if __name__ == "__main__":
    main()
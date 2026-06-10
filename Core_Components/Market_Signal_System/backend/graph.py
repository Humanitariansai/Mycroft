import os
import json
from datetime import datetime
from typing import TypedDict, Annotated
import operator
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from models import AgentFindings, MarketSignalReport
from agents import (
    technical_analysis_agent,
    news_sentiment_agent,
    market_fear_greed_agent,
)
from conflict_resolution import ConflictResolver

load_dotenv()


# ── Graph state ──────────────────────────────────────────────────────────────

class MarketSignalState(TypedDict):
    ticker: str
    findings: Annotated[list[AgentFindings], operator.add]
    conflict_analysis: dict
    resolution_summary: dict
    final_recommendation: dict
    error: str | None


# ── Agent Nodes ──────────────────────────────────────────────────────────────

def technical_node(state: MarketSignalState) -> dict:
    ticker = state.get("ticker", "SPY")
    findings = technical_analysis_agent(ticker)
    return {"findings": [findings]}


def news_node(state: MarketSignalState) -> dict:
    ticker = state.get("ticker", "SPY") 
    findings = news_sentiment_agent(ticker)
    return {"findings": [findings]}


def fear_greed_node(state: MarketSignalState) -> dict:
    findings = market_fear_greed_agent()
    return {"findings": [findings]}


# ── Conflict Resolution Node ─────────────────────────────────────────────────

def conflict_resolution_node(state: MarketSignalState) -> dict:
    findings = state["findings"]
    resolver = ConflictResolver()
    
    # Generate comprehensive conflict report
    conflict_report = resolver.generate_conflict_report(findings)
    
    return {
        "conflict_analysis": conflict_report["conflict_analysis"],
        "resolution_summary": conflict_report["resolution_methods"],
        "final_recommendation": conflict_report["recommendation"]
    }


# ── Graph Construction ────────────────────────────────────────────────────────

def create_market_signal_graph():
    g = StateGraph(MarketSignalState)
    
    # Add nodes
    g.add_node("technical", technical_node)
    g.add_node("news", news_node)
    g.add_node("fear_greed", fear_greed_node)
    g.add_node("resolve_conflicts", conflict_resolution_node)
    
    # Set entry point
    g.set_entry_point("technical")
    
    # All agents run in parallel then converge to conflict resolution
    g.add_edge("technical", "news")
    g.add_edge("technical", "fear_greed")
    g.add_edge("news", "resolve_conflicts")
    g.add_edge("fear_greed", "resolve_conflicts")
    g.add_edge("resolve_conflicts", END)
    
    return g.compile()


# ── Main Analysis Function ────────────────────────────────────────────────────

def analyze_market_signals(ticker: str = "SPY") -> MarketSignalReport:
    """
    Run 3-agent market signal analysis with conflict resolution
    """
    graph = create_market_signal_graph()
    
    initial_state = {
        "ticker": ticker,
        "findings": [],
        "conflict_analysis": {},
        "resolution_summary": {},
        "final_recommendation": {},
        "error": None
    }
    
    try:
        # Execute the graph
        final_state = graph.invoke(initial_state)
        
        return MarketSignalReport(
            ticker=ticker,
            agent_findings=final_state["findings"],
            conflict_analysis=final_state["conflict_analysis"],
            resolution_summary=final_state["resolution_summary"],
            final_recommendation=final_state["final_recommendation"],
            generated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        # Return error state
        return MarketSignalReport(
            ticker=ticker,
            agent_findings=[],
            conflict_analysis={"error": str(e)},
            resolution_summary={},
            final_recommendation={"error": str(e)},
            generated_at=datetime.now().isoformat()
        )


if __name__ == "__main__":
    # Test the system
    report = analyze_market_signals("SPY")
    print(json.dumps(report.model_dump(), indent=2, default=str))
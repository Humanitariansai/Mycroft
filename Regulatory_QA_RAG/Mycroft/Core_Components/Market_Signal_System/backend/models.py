from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgentFindings(BaseModel):
    agent_name: str
    insights: list[str]
    metrics: dict
    edge_score: Optional[float] = None    # 0 to 1, where 1 = strong buy signal


class MarketSignalReport(BaseModel):
    ticker: str
    agent_findings: list[AgentFindings]
    conflict_analysis: dict
    resolution_summary: dict
    final_recommendation: dict
    generated_at: str
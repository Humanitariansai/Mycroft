"""
Conflict Resolution Layer for Multi-Agent Investment Systems
Implementation of research paper: "When the Agents Disagree, Who Decides?"

Handles 3 types of conflicts:
1. Temporal Lag - agents working with different data freshness
2. Source Quality Mismatch - different confidence levels in data sources  
3. Analytical Disagreement - fundamentally different analysis conclusions
"""

import numpy as np
from typing import List, Dict, Any
from models import AgentFindings
from datetime import datetime
import pandas as pd


class ConflictResolver:
    """
    Implements sophisticated conflict resolution beyond simple averaging
    Based on confidence weighting, disagreement detection, and ensemble methods
    """
    
    def __init__(self):
        self.agent_weights = {
            "technical_analysis": 0.4,   # Higher weight for quantitative signals
            "news_sentiment": 0.3,       # Medium weight for sentiment
            "market_fear_greed": 0.3     # Medium weight for market psychology
        }
        
        self.confidence_threshold = 0.7  # Threshold for high-confidence decisions
        self.disagreement_threshold = 0.3  # Threshold for significant disagreement
    
    def detect_conflicts(self, findings: List[AgentFindings]) -> Dict[str, Any]:
        """
        Detect different types of conflicts between agents
        """
        conflicts = {
            "has_conflicts": False,
            "conflict_types": [],
            "disagreement_score": 0.0,
            "conflicting_agents": []
        }
        
        # Get edge scores
        edge_scores = []
        agent_names = []
        
        for finding in findings:
            if finding.edge_score is not None:
                edge_scores.append(finding.edge_score)
                agent_names.append(finding.agent_name)
        
        if len(edge_scores) < 2:
            return conflicts
            
        # Calculate disagreement metrics
        edge_scores = np.array(edge_scores)
        std_dev = np.std(edge_scores)
        max_diff = np.max(edge_scores) - np.min(edge_scores)
        
        conflicts["disagreement_score"] = round(max_diff, 3)
        
        # Detect significant disagreement
        if max_diff > self.disagreement_threshold:
            conflicts["has_conflicts"] = True
            conflicts["conflict_types"].append("analytical_disagreement")
            
            # Find conflicting agents
            mean_score = np.mean(edge_scores)
            for i, (score, agent) in enumerate(zip(edge_scores, agent_names)):
                if abs(score - mean_score) > self.disagreement_threshold/2:
                    conflicts["conflicting_agents"].append({
                        "agent": agent,
                        "score": score,
                        "deviation": round(score - mean_score, 3)
                    })
        
        # Detect source quality issues (missing data)
        missing_data_agents = []
        for finding in findings:
            if finding.edge_score is None or len(finding.insights) == 0:
                missing_data_agents.append(finding.agent_name)
                conflicts["has_conflicts"] = True
                if "source_quality_mismatch" not in conflicts["conflict_types"]:
                    conflicts["conflict_types"].append("source_quality_mismatch")
        
        conflicts["missing_data_agents"] = missing_data_agents
        
        return conflicts
    
    def resolve_with_confidence_weighting(self, findings: List[AgentFindings]) -> Dict[str, Any]:
        """
        Resolve conflicts using confidence-weighted consensus
        """
        weighted_scores = []
        total_weight = 0
        agent_contributions = {}
        
        for finding in findings:
            if finding.edge_score is not None:
                agent_weight = self.agent_weights.get(finding.agent_name, 0.33)
                
                # Calculate confidence based on data quality
                confidence = self._calculate_confidence(finding)
                
                # Adjust weight by confidence
                effective_weight = agent_weight * confidence
                
                weighted_score = finding.edge_score * effective_weight
                weighted_scores.append(weighted_score)
                total_weight += effective_weight
                
                agent_contributions[finding.agent_name] = {
                    "raw_score": finding.edge_score,
                    "base_weight": agent_weight,
                    "confidence": round(confidence, 3),
                    "effective_weight": round(effective_weight, 3),
                    "contribution": round(weighted_score, 3)
                }
        
        if total_weight == 0:
            return {
                "resolved_score": 0.5,
                "method": "default",
                "confidence": 0.0,
                "agent_contributions": {}
            }
        
        resolved_score = sum(weighted_scores) / total_weight
        overall_confidence = min(1.0, total_weight / sum(self.agent_weights.values()))
        
        return {
            "resolved_score": round(resolved_score, 3),
            "method": "confidence_weighted_consensus",
            "confidence": round(overall_confidence, 3),
            "agent_contributions": agent_contributions
        }
    
    def resolve_with_ensemble_voting(self, findings: List[AgentFindings]) -> Dict[str, Any]:
        """
        Alternative: Ensemble voting approach
        """
        buy_votes = 0
        sell_votes = 0
        hold_votes = 0
        
        agent_votes = {}
        
        for finding in findings:
            if finding.edge_score is not None:
                if finding.edge_score > 0.55:  # Lowered from 0.6 to 0.55
                    vote = "buy"
                    buy_votes += 1
                elif finding.edge_score < 0.45:  # Raised from 0.4 to 0.45
                    vote = "sell" 
                    sell_votes += 1
                else:
                    vote = "hold"
                    hold_votes += 1
                    
                agent_votes[finding.agent_name] = {
                    "vote": vote,
                    "score": finding.edge_score
                }
        
        # Determine majority
        if buy_votes > sell_votes and buy_votes > hold_votes:
            decision = "buy"
            confidence = buy_votes / len([f for f in findings if f.edge_score is not None])
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            decision = "sell"
            confidence = sell_votes / len([f for f in findings if f.edge_score is not None])
        else:
            decision = "hold"
            confidence = hold_votes / len([f for f in findings if f.edge_score is not None])
        
        return {
            "decision": decision,
            "method": "ensemble_voting",
            "confidence": round(confidence, 3),
            "vote_breakdown": {
                "buy": buy_votes,
                "sell": sell_votes, 
                "hold": hold_votes
            },
            "agent_votes": agent_votes
        }
    
    def _calculate_confidence(self, finding: AgentFindings) -> float:
        """
        Calculate confidence score for an agent's finding based on data quality
        """
        confidence = 1.0
        
        # Reduce confidence if missing data
        if finding.edge_score is None:
            return 0.0
            
        # Reduce confidence if few insights
        if len(finding.insights) < 2:
            confidence *= 0.8
            
        # Reduce confidence if error messages present
        error_indicators = ["error", "could not", "unavailable", "failed"]
        for insight in finding.insights:
            if any(indicator in insight.lower() for indicator in error_indicators):
                confidence *= 0.6
                break
        
        # Boost confidence for data-rich findings
        if len(finding.metrics) > 3:
            confidence *= 1.1
            
        return min(1.0, confidence)
    
    def generate_conflict_report(self, findings: List[AgentFindings]) -> Dict[str, Any]:
        """
        Generate comprehensive conflict analysis report
        """
        conflicts = self.detect_conflicts(findings)
        confidence_resolution = self.resolve_with_confidence_weighting(findings)
        voting_resolution = self.resolve_with_ensemble_voting(findings)
        
        # Simple average for comparison
        valid_scores = [f.edge_score for f in findings if f.edge_score is not None]
        simple_average = np.mean(valid_scores) if valid_scores else 0.5
        
        return {
            "timestamp": datetime.now().isoformat(),
            "conflict_analysis": conflicts,
            "resolution_methods": {
                "simple_average": round(simple_average, 3),
                "confidence_weighted": confidence_resolution,
                "ensemble_voting": voting_resolution
            },
            "recommendation": self._generate_recommendation(
                confidence_resolution, voting_resolution, conflicts
            )
        }
    
    def _generate_recommendation(self, confidence_res: Dict, voting_res: Dict, conflicts: Dict) -> Dict[str, Any]:
        """
        Generate final recommendation based on conflict resolution analysis
        """
        if not conflicts["has_conflicts"]:
            # No conflicts - use confidence weighted
            return {
                "method": "confidence_weighted",
                "score": confidence_res["resolved_score"],
                "rationale": "No significant conflicts detected, using confidence-weighted consensus"
            }
        
        if conflicts["disagreement_score"] > 0.5:
            # High disagreement - use voting
            return {
                "method": "ensemble_voting", 
                "decision": voting_res["decision"],
                "rationale": f"High disagreement ({conflicts['disagreement_score']:.2f}) detected, using ensemble voting"
            }
        
        # Medium conflicts - use confidence weighted but flag uncertainty
        return {
            "method": "confidence_weighted_with_warning",
            "score": confidence_res["resolved_score"],
            "rationale": f"Moderate conflicts detected, confidence-weighted result with {conflicts['disagreement_score']:.2f} disagreement"
        }
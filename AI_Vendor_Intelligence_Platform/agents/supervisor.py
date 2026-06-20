"""Supervisor agent using LangGraph StateGraph for orchestration."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from agents.llm import get_llm
from agents.specialists import (
    run_financial_agent,
    run_technology_agent,
    run_news_agent,
    run_personnel_agent,
    run_competitive_agent,
)

load_dotenv()


# ---------------------------------------------------------------------------
# Define Graph State
# ---------------------------------------------------------------------------


class BriefState(TypedDict):
    """State for the vendor intelligence brief generation graph."""

    company_name: str
    messages: Annotated[list, add_messages]
    financial_output: str
    technology_output: str
    news_output: str
    personnel_output: str
    competitive_output: str
    next_agent: str
    brief: str


# ---------------------------------------------------------------------------
# Supervisor Node
# ---------------------------------------------------------------------------


def supervisor_node(state: BriefState) -> BriefState:
    """Route to the next agent based on what's been collected."""
    llm = get_llm()

    # Track what's been collected
    collected = []
    if state.get("financial_output"):
        collected.append("financial")
    if state.get("technology_output"):
        collected.append("technology")
    if state.get("news_output"):
        collected.append("news")
    if state.get("personnel_output"):
        collected.append("personnel")
    if state.get("competitive_output"):
        collected.append("competitive")

    all_agents = ["financial", "technology", "news", "personnel", "competitive"]
    remaining = [a for a in all_agents if a not in collected]

    # If all agents have run, move to synthesis
    if not remaining:
        return {**state, "next_agent": "synthesize"}

    # Ask LLM which agent to run next
    system = """You are orchestrating a vendor intelligence analysis.
Choose the next specialist agent to run based on what's already been collected.
Return ONLY one word from the available options."""

    user = f"""Analyzing: {state["company_name"]}
Already collected: {", ".join(collected) if collected else "nothing yet"}
Still needed: {", ".join(remaining)}

Which agent should run next?
Choose from: {", ".join(remaining)}
Return only the agent name, nothing else."""

    response = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)]
    )

    next_agent = response.content.strip().lower()

    # Validate and fallback
    if next_agent not in remaining:
        next_agent = remaining[0]

    print(f"  Supervisor → routing to: {next_agent}")
    return {**state, "next_agent": next_agent}


# ---------------------------------------------------------------------------
# Agent Nodes
# ---------------------------------------------------------------------------


def financial_node(state: BriefState) -> BriefState:
    """Run financial specialist agent."""
    print("  Running Financial agent...")
    output = run_financial_agent(state["company_name"])
    return {**state, "financial_output": output}


def technology_node(state: BriefState) -> BriefState:
    """Run technology specialist agent."""
    print("  Running Technology agent...")
    output = run_technology_agent(state["company_name"])
    return {**state, "technology_output": output}


def news_node(state: BriefState) -> BriefState:
    """Run news specialist agent."""
    print("  Running News agent...")
    output = run_news_agent(state["company_name"])
    return {**state, "news_output": output}


def personnel_node(state: BriefState) -> BriefState:
    """Run personnel specialist agent."""
    print("  Running Personnel agent...")
    output = run_personnel_agent(state["company_name"])
    return {**state, "personnel_output": output}


def competitive_node(state: BriefState) -> BriefState:
    """Run competitive specialist agent."""
    print("  Running Competitive agent...")
    output = run_competitive_agent(state["company_name"])
    return {**state, "competitive_output": output}


# ---------------------------------------------------------------------------
# Synthesis Node
# ---------------------------------------------------------------------------


def synthesis_node(state: BriefState) -> BriefState:
    """Synthesize all agent outputs into final brief."""
    print("  Synthesizing final brief...")
    llm = get_llm(temperature=0.3)

    prompt = f"""Synthesize this vendor intelligence brief from specialist agent analyses.

Company: {state["company_name"]}

FINANCIAL ANALYSIS:
{state.get("financial_output", "No data")}

TECHNOLOGY ANALYSIS:
{state.get("technology_output", "No data")}

NEWS ANALYSIS:
{state.get("news_output", "No data")}

PERSONNEL ANALYSIS:
{state.get("personnel_output", "No data")}

COMPETITIVE ANALYSIS:
{state.get("competitive_output", "No data")}

Produce a structured brief with these exact sections:

VENDOR INTELLIGENCE BRIEF: {state["company_name"]}

FINANCIAL HEALTH: [score/100]
[2-3 sentences from financial data]

TECHNOLOGY MOMENTUM: [score/100]
[2-3 sentences from technology data]

NEWS & SENTIMENT: [positive/neutral/negative]
[2-3 sentences from news data]

PERSONNEL STABILITY: [score/100]
[2-3 sentences from personnel data]

COMPETITIVE POSITION:
[2-3 sentences from competitive data]

EXECUTIVE SUMMARY:
[3-4 sentences synthesizing everything into a procurement recommendation]

DATA SOURCES: SEC EDGAR, GitHub, ArXiv, Google News, Neo4j competitive graph"""

    response = llm.invoke(prompt)
    brief = response.content if hasattr(response, "content") else str(response)
    return {**state, "brief": brief}


# ---------------------------------------------------------------------------
# Router Function
# ---------------------------------------------------------------------------


def route_next(state: BriefState) -> Literal[
    "financial", "technology", "news", "personnel", "competitive", "synthesize"
]:
    """Route to the next node based on supervisor decision."""
    return state["next_agent"]


# ---------------------------------------------------------------------------
# Build the Graph
# ---------------------------------------------------------------------------


def build_graph():
    """Build and compile the LangGraph StateGraph."""
    graph = StateGraph(BriefState)

    # Add all nodes
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("financial", financial_node)
    graph.add_node("technology", technology_node)
    graph.add_node("news", news_node)
    graph.add_node("personnel", personnel_node)
    graph.add_node("competitive", competitive_node)
    graph.add_node("synthesize", synthesis_node)

    # Entry point
    graph.add_edge(START, "supervisor")

    # Supervisor routes to agents or synthesis
    graph.add_conditional_edges(
        "supervisor",
        route_next,
        {
            "financial": "financial",
            "technology": "technology",
            "news": "news",
            "personnel": "personnel",
            "competitive": "competitive",
            "synthesize": "synthesize",
        },
    )

    # All agents return to supervisor for next decision
    graph.add_edge("financial", "supervisor")
    graph.add_edge("technology", "supervisor")
    graph.add_edge("news", "supervisor")
    graph.add_edge("personnel", "supervisor")
    graph.add_edge("competitive", "supervisor")

    # Synthesis ends the graph
    graph.add_edge("synthesize", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------


def generate_brief(company_name: str) -> str:
    """Generate a vendor intelligence brief using LangGraph."""
    print(f"\n{'='*70}")
    print(f"Generating intelligence brief: {company_name}")
    print(f"{'='*70}\n")

    graph = build_graph()
    wall_start = time.monotonic()

    # Initialize state
    initial_state = BriefState(
        company_name=company_name,
        messages=[],
        financial_output="",
        technology_output="",
        news_output="",
        personnel_output="",
        competitive_output="",
        next_agent="",
        brief="",
    )

    # Execute the graph
    final_state = graph.invoke(initial_state)

    elapsed = time.monotonic() - wall_start
    minutes, seconds = divmod(int(elapsed), 60)
    time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"

    # Print final brief
    print(f"\n{'='*70}")
    print(final_state["brief"])
    print(f"{'='*70}")
    print(f"\nTotal time: {time_str}\n")

    return final_state["brief"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    company = sys.argv[1] if len(sys.argv) > 1 else "Cohere"
    generate_brief(company)

"""Five specialist agents for intelligence analysis."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langgraph.prebuilt import create_react_agent
from agents.llm import get_llm
from agents.tools import (
    query_funding_signals,
    query_executive_changes,
    query_github_signals,
    query_arxiv_signals,
    query_news_signals,
    query_negative_signals,
    query_annual_filings,
    get_signal_summary,
    query_neo4j_competitors,
    query_neo4j_investors,
    query_neo4j_company_info,
    query_all_signals_count,
)

# ---------------------------------------------------------------------------
# Financial Agent
# ---------------------------------------------------------------------------

FINANCIAL_PROMPT = """You are a financial analyst evaluating AI vendors for \
enterprise procurement decisions. Given a company name, use your tools to \
gather financial signals then provide:
1. FINANCIAL HEALTH SCORE: 0-100
2. KEY FINDINGS: 3 bullet points with dates
3. RISK FLAGS: any concerning signals
4. SOURCES: cite signal dates and headlines
Be concise. If no data found, say so honestly."""

financial_agent = create_react_agent(
    model=get_llm(),
    tools=[
        query_funding_signals,
        query_annual_filings,
        query_executive_changes,
        get_signal_summary,
    ],
    prompt=FINANCIAL_PROMPT,
)


def run_financial_agent(company_name: str) -> str:
    """Run financial agent on a company."""
    try:
        result = financial_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze {company_name}",
                    }
                ]
            }
        )
        return result["messages"][-1].content
    except Exception as exc:
        return f"Error running financial agent: {exc}"


# ---------------------------------------------------------------------------
# Technology Agent
# ---------------------------------------------------------------------------

TECHNOLOGY_PROMPT = """You are a technology analyst evaluating AI vendors. \
Given a company name, use your tools to gather technology signals then provide:
1. TECHNOLOGY MOMENTUM SCORE: 0-100
2. RECENT RELEASES: list with dates
3. RESEARCH OUTPUT: paper count and topics
4. GITHUB ACTIVITY: release velocity assessment
Be concise. If no data found, say so honestly."""

technology_agent = create_react_agent(
    model=get_llm(),
    tools=[
        query_github_signals,
        query_arxiv_signals,
        get_signal_summary,
        query_all_signals_count,
    ],
    prompt=TECHNOLOGY_PROMPT,
)


def run_technology_agent(company_name: str) -> str:
    """Run technology agent on a company."""
    try:
        result = technology_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze {company_name}",
                    }
                ]
            }
        )
        return result["messages"][-1].content
    except Exception as exc:
        return f"Error running technology agent: {exc}"


# ---------------------------------------------------------------------------
# News Agent
# ---------------------------------------------------------------------------

NEWS_PROMPT = """You are a news and sentiment analyst evaluating AI vendors. \
Given a company name, use your tools to gather news signals then provide:
1. SENTIMENT: positive/neutral/negative with reasoning
2. KEY EVENTS: top 3 most important recent events
3. NEGATIVE FLAGS: any concerning news
4. PARTNERSHIPS: notable announcements
Be concise. If no data found, say so honestly."""

news_agent = create_react_agent(
    model=get_llm(),
    tools=[
        query_news_signals,
        query_negative_signals,
        get_signal_summary,
    ],
    prompt=NEWS_PROMPT,
)


def run_news_agent(company_name: str) -> str:
    """Run news agent on a company."""
    try:
        result = news_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze {company_name}",
                    }
                ]
            }
        )
        return result["messages"][-1].content
    except Exception as exc:
        return f"Error running news agent: {exc}"


# ---------------------------------------------------------------------------
# Personnel Agent
# ---------------------------------------------------------------------------

PERSONNEL_PROMPT = """You are a personnel analyst evaluating AI vendor \
leadership stability. Given a company name, use your tools to gather \
personnel signals then provide:
1. PERSONNEL STABILITY SCORE: 0-100
2. EXECUTIVE CHANGES: list any with dates and roles
3. STABILITY ASSESSMENT: one paragraph
Be concise. If no data found, say so honestly."""

personnel_agent = create_react_agent(
    model=get_llm(),
    tools=[
        query_executive_changes,
        query_annual_filings,
        get_signal_summary,
    ],
    prompt=PERSONNEL_PROMPT,
)


def run_personnel_agent(company_name: str) -> str:
    """Run personnel agent on a company."""
    try:
        result = personnel_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze {company_name}",
                    }
                ]
            }
        )
        return result["messages"][-1].content
    except Exception as exc:
        return f"Error running personnel agent: {exc}"


# ---------------------------------------------------------------------------
# Competitive Agent
# ---------------------------------------------------------------------------

COMPETITIVE_PROMPT = """You are a competitive intelligence analyst evaluating \
AI vendors. Given a company name, use your tools to gather competitive signals \
then provide:
1. MARKET POSITION: one paragraph
2. DIRECT COMPETITORS: list with stages
3. KEY INVESTORS: list
4. COMPETITIVE RISKS: any concerning signals
Be concise. If no data found, say so honestly."""

competitive_agent = create_react_agent(
    model=get_llm(),
    tools=[
        query_neo4j_competitors,
        query_neo4j_investors,
        query_neo4j_company_info,
        query_news_signals,
    ],
    prompt=COMPETITIVE_PROMPT,
)


def run_competitive_agent(company_name: str) -> str:
    """Run competitive agent on a company."""
    try:
        result = competitive_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze {company_name}",
                    }
                ]
            }
        )
        return result["messages"][-1].content
    except Exception as exc:
        return f"Error running competitive agent: {exc}"


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    company = "Cohere"
    print(f"Running all 5 specialist agents for {company}\n")

    print("=" * 70)
    print("FINANCIAL AGENT")
    print("=" * 70)
    print(run_financial_agent(company))
    print()

    print("=" * 70)
    print("TECHNOLOGY AGENT")
    print("=" * 70)
    print(run_technology_agent(company))
    print()

    print("=" * 70)
    print("NEWS AGENT")
    print("=" * 70)
    print(run_news_agent(company))
    print()

    print("=" * 70)
    print("PERSONNEL AGENT")
    print("=" * 70)
    print(run_personnel_agent(company))
    print()

    print("=" * 70)
    print("COMPETITIVE AGENT")
    print("=" * 70)
    print(run_competitive_agent(company))
    print()

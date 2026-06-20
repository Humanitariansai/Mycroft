"""Tool functions for agents to query signals and graph data."""

import sys
import os
from datetime import datetime

from langchain_core.tools import tool
from dotenv import load_dotenv
from neo4j import GraphDatabase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import collector.db as db

load_dotenv()


# ---------------------------------------------------------------------------
# Postgres Signal Query Tools
# ---------------------------------------------------------------------------


@tool
def query_funding_signals(company_name: str) -> str:
    """Get funding round signals for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT headline, summary, signal_date, importance_score
                FROM ai_company_signals
                WHERE company_name = %s AND signal_type = 'funding'
                ORDER BY signal_date DESC
                LIMIT 5
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No funding signals found for {company_name}"

        result = f"Funding signals for {company_name}:\n"
        for headline, summary, date, score in rows:
            result += f"  • {date}: {headline} (score: {score})\n"
            result += f"    {summary}\n"
        return result
    except Exception as exc:
        return f"Error querying funding signals: {exc}"


@tool
def query_executive_changes(company_name: str) -> str:
    """Get executive change signals for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT headline, summary, signal_date, importance_score
                FROM ai_company_signals
                WHERE company_name = %s AND signal_type = 'executive_change'
                ORDER BY signal_date DESC
                LIMIT 5
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No executive change signals found for {company_name}"

        result = f"Executive changes for {company_name}:\n"
        for headline, summary, date, score in rows:
            result += f"  • {date}: {headline} (score: {score})\n"
            result += f"    {summary}\n"
        return result
    except Exception as exc:
        return f"Error querying executive changes: {exc}"


@tool
def query_github_signals(company_name: str) -> str:
    """Get GitHub activity and release signals for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT headline, summary, signal_date, signal_type
                FROM ai_company_signals
                WHERE company_name = %s
                  AND signal_type IN ('github_release', 'github_activity')
                ORDER BY signal_date DESC
                LIMIT 10
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No GitHub signals found for {company_name}"

        result = f"GitHub signals for {company_name}:\n"
        for headline, summary, date, sig_type in rows:
            result += f"  • {date} [{sig_type}]: {headline}\n"
            result += f"    {summary}\n"
        return result
    except Exception as exc:
        return f"Error querying GitHub signals: {exc}"


@tool
def query_arxiv_signals(company_name: str) -> str:
    """Get research paper signals for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT headline, summary, signal_date, importance_score
                FROM ai_company_signals
                WHERE company_name = %s AND signal_type = 'research_paper'
                ORDER BY signal_date DESC
                LIMIT 10
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No research papers found for {company_name}"

        result = f"Research papers by {company_name}:\n"
        for headline, summary, date, score in rows:
            result += f"  • {date}: {headline} (relevance: {score})\n"
            result += f"    {summary}\n"
        return result
    except Exception as exc:
        return f"Error querying ArXiv signals: {exc}"


@tool
def query_news_signals(company_name: str) -> str:
    """Get recent news signals for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT headline, summary, signal_date, signal_type, importance_score
                FROM ai_company_signals
                WHERE company_name = %s
                  AND signal_type IN (
                    'product_launch', 'partnership', 'negative',
                    'regulatory', 'other', 'acquisition'
                  )
                ORDER BY signal_date DESC
                LIMIT 15
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No news signals found for {company_name}"

        result = f"News signals for {company_name}:\n"
        for headline, summary, date, sig_type, score in rows:
            result += f"  • {date} [{sig_type}]: {headline} (score: {score})\n"
            result += f"    {summary}\n"
        return result
    except Exception as exc:
        return f"Error querying news signals: {exc}"


@tool
def query_negative_signals(company_name: str) -> str:
    """Get negative news signals for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT headline, summary, signal_date, importance_score
                FROM ai_company_signals
                WHERE company_name = %s AND signal_type = 'negative'
                ORDER BY signal_date DESC
                LIMIT 5
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No negative signals found for {company_name}"

        result = f"Negative signals for {company_name}:\n"
        for headline, summary, date, score in rows:
            result += f"  • {date}: {headline} (severity: {score})\n"
            result += f"    {summary}\n"
        return result
    except Exception as exc:
        return f"Error querying negative signals: {exc}"


@tool
def query_annual_filings(company_name: str) -> str:
    """Get SEC annual filing signals for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT headline, summary, signal_date
                FROM ai_company_signals
                WHERE company_name = %s AND signal_type = 'annual_filing'
                ORDER BY signal_date DESC
                LIMIT 3
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No SEC filings found for {company_name}"

        result = f"SEC filings for {company_name}:\n"
        for headline, summary, date in rows:
            result += f"  • {date}: {headline}\n"
            result += f"    {summary}\n"
        return result
    except Exception as exc:
        return f"Error querying SEC filings: {exc}"


@tool
def get_signal_summary(company_name: str) -> str:
    """Get a count summary of all signal types for a company."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT signal_type, COUNT(*) as count
                FROM ai_company_signals
                WHERE company_name = %s
                GROUP BY signal_type
                ORDER BY count DESC
                """,
                (company_name,),
            )
            rows = cur.fetchall()
        conn.close()

        if not rows:
            return f"No signals found for {company_name}"

        result = f"Signal summary for {company_name}:\n"
        total = 0
        for sig_type, count in rows:
            result += f"  {sig_type}: {count}\n"
            total += count
        result += f"  Total: {total}\n"
        return result
    except Exception as exc:
        return f"Error querying signal summary: {exc}"


# ---------------------------------------------------------------------------
# Neo4j Graph Query Tools
# ---------------------------------------------------------------------------


def _get_neo4j_driver():
    """Get Neo4j driver from environment."""
    uri = os.getenv("NEO4J_URI", "").strip()
    user = os.getenv("NEO4J_USER", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()

    if not all([uri, user, password]):
        raise EnvironmentError(
            "NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set"
        )

    return GraphDatabase.driver(uri, auth=(user, password))


@tool
def query_neo4j_competitors(company_name: str) -> str:
    """Get direct competitors of a company from the graph."""
    try:
        driver = _get_neo4j_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company {name: $name})-[:COMPETES_WITH]-(r:Company)
                RETURN r.name, r.stage
                ORDER BY r.name
                """,
                name=company_name,
            )
            rows = result.data()
        driver.close()

        if not rows:
            return f"No competitors found for {company_name} in the graph"

        competitors_str = f"Direct competitors of {company_name}:\n"
        for record in rows:
            name = record.get("r.name", "Unknown")
            stage = record.get("r.stage", "Unknown")
            competitors_str += f"  • {name} ({stage})\n"
        return competitors_str
    except Exception as exc:
        return f"Error querying competitors: {exc}"


@tool
def query_neo4j_investors(company_name: str) -> str:
    """Get investors backing a company from the graph."""
    try:
        driver = _get_neo4j_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company {name: $name})-[:BACKED_BY]->(i:Investor)
                RETURN i.name
                ORDER BY i.name
                """,
                name=company_name,
            )
            rows = result.data()
        driver.close()

        if not rows:
            return f"No investor data found for {company_name}"

        investors_str = f"Investors backing {company_name}:\n"
        for record in rows:
            investor = record.get("i.name", "Unknown")
            investors_str += f"  • {investor}\n"
        return investors_str
    except Exception as exc:
        return f"Error querying investors: {exc}"


@tool
def query_neo4j_company_info(company_name: str) -> str:
    """Get basic company info from the graph."""
    try:
        driver = _get_neo4j_driver()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (c:Company {name: $name})
                RETURN c.name, c.stage, c.ticker, c.founded_year, c.github_org
                """,
                name=company_name,
            )
            row = result.single()
        driver.close()

        if not row:
            return f"Company {company_name} not found in graph"

        name = row.get("c.name", "Unknown")
        stage = row.get("c.stage", "Unknown")
        ticker = row.get("c.ticker", "N/A")
        founded = row.get("c.founded_year", "N/A")
        github_org = row.get("c.github_org", "N/A")

        info_str = f"Company info for {name}:\n"
        info_str += f"  Stage: {stage}\n"
        info_str += f"  Ticker: {ticker}\n"
        info_str += f"  Founded: {founded}\n"
        info_str += f"  GitHub Org: {github_org}\n"
        return info_str
    except Exception as exc:
        return f"Error querying company info: {exc}"


@tool
def query_all_signals_count(company_name: str) -> str:
    """Get total signal count for a company across all types."""
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM ai_company_signals
                WHERE company_name = %s
                """,
                (company_name,),
            )
            row = cur.fetchone()
        conn.close()

        if row and row[0] > 0:
            return f"Total signals for {company_name}: {row[0]}"
        else:
            return f"No data found for {company_name}"
    except Exception as exc:
        return f"Error querying signal count: {exc}"


# ---------------------------------------------------------------------------
# Test Tools
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    company = "Anthropic"
    print(f"Testing all tools with company: {company}\n")

    tools = [
        ("1. Funding Signals", query_funding_signals),
        ("2. Executive Changes", query_executive_changes),
        ("3. GitHub Signals", query_github_signals),
        ("4. ArXiv Signals", query_arxiv_signals),
        ("5. News Signals", query_news_signals),
        ("6. Negative Signals", query_negative_signals),
        ("7. Annual Filings", query_annual_filings),
        ("8. Signal Summary", get_signal_summary),
        ("9. Neo4j Competitors", query_neo4j_competitors),
        ("10. Neo4j Investors", query_neo4j_investors),
        ("11. Neo4j Company Info", query_neo4j_company_info),
        ("12. Total Signals Count", query_all_signals_count),
    ]

    for label, tool_func in tools:
        print(f"\n{label}:")
        print("-" * 60)
        result = tool_func.invoke({"company_name": company})
        print(result)
        print()

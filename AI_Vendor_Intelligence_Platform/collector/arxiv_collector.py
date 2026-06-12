"""Fetches and indexes arXiv papers authored by or citing tracked AI companies."""

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
import db

load_dotenv()

SEED_FILE = Path(__file__).parent / "seed_companies.json"
RATE_LIMIT_SLEEP = 3  # seconds between companies; ArXiv is strict
LOOKBACK_DAYS = 90


# ---------------------------------------------------------------------------
# ArXiv API interaction
# ---------------------------------------------------------------------------

def search_arxiv(company_name: str, max_results: int = 20) -> str:
    """Query the arXiv API and return raw XML response."""
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f'all:"{company_name}"',
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.text


def parse_arxiv_response(xml_text: str) -> list[dict]:
    """Parse arXiv XML response and extract paper metadata."""
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    root = ET.fromstring(xml_text)
    papers = []

    for entry in root.findall("atom:entry", ns):
        title_elem = entry.find("atom:title", ns)
        summary_elem = entry.find("atom:summary", ns)
        published_elem = entry.find("atom:published", ns)
        id_elem = entry.find("atom:id", ns)
        author_elems = entry.findall("atom:author", ns)

        title = title_elem.text.strip() if title_elem is not None else ""
        summary = summary_elem.text.strip() if summary_elem is not None else ""
        published = published_elem.text.strip() if published_elem is not None else ""
        entry_id = id_elem.text.strip() if id_elem is not None else ""

        authors = []
        for author in author_elems:
            name_elem = author.find("atom:name", ns)
            if name_elem is not None:
                authors.append(name_elem.text)

        papers.append({
            "title": title,
            "summary": summary,
            "published": published,
            "entry_id": entry_id,
            "authors": authors[:5],
        })

    return papers


# ---------------------------------------------------------------------------
# Paper filtering
# ---------------------------------------------------------------------------

def _is_recent(published_str: str) -> bool:
    """Check if a paper was published within the lookback window."""
    if not published_str:
        return False
    try:
        pub_date = datetime.fromisoformat(
            published_str.replace("Z", "+00:00")
        )
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=LOOKBACK_DAYS)
        return pub_date >= cutoff
    except ValueError:
        return False


def _parse_published_date(published_str: str):
    """Parse arXiv ISO date string to a Python date object."""
    return datetime.fromisoformat(
        published_str.replace("Z", "+00:00")
    ).date()


# ---------------------------------------------------------------------------
# Per-company processing
# ---------------------------------------------------------------------------

def _process_company(company: dict) -> tuple[int, int]:
    """Search arXiv for papers mentioning a company. Returns (signals_added, errors)."""
    name = company["name"]
    ticker = company.get("ticker")
    signals_added = 0
    errors = 0

    try:
        xml_response = search_arxiv(name, max_results=20)
        papers = parse_arxiv_response(xml_response)
    except Exception as exc:
        print(f"  ArXiv search failed for {name}: {exc}")
        return 0, 1

    for paper in papers:
        if not _is_recent(paper["published"]):
            continue

        headline = paper["title"][:200]
        summary = paper["summary"][:300]
        pub_date = _parse_published_date(paper["published"])

        try:
            inserted = db.insert_signal(
                company_name=name,
                ticker=ticker,
                signal_type="research_paper",
                signal_date=pub_date,
                headline=headline,
                summary=summary,
                source_url=paper["entry_id"],
                importance_score=60,
                raw_data={
                    "arxiv_id": paper["entry_id"],
                    "authors": paper["authors"],
                },
            )
            if inserted:
                signals_added += 1
        except Exception as exc:
            print(f"    [insert error] {headline}: {exc}")
            errors += 1

    return signals_added, errors

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    with open(SEED_FILE) as f:
        all_companies = json.load(f)

    # ArXiv search works on company names, not specific to public/private
    companies = all_companies
    total = len(companies)
    total_signals = 0
    total_errors = 0
    started_at = datetime.now(tz=timezone.utc)

    print(f"ArXiv collector starting — {total} companies to process.\n")

    for i, company in enumerate(companies, start=1):
        name = company["name"]
        print(f"Processing {name} ({i}/{total})...")

        try:
            signals, errors = _process_company(company)
            total_signals += signals
            total_errors += errors
            print(f"  -> {signals} signal(s) added, {errors} error(s).")
        except Exception as exc:
            print(f"  ERROR processing {name}: {exc}")
            total_errors += 1

        if i < total:
            time.sleep(RATE_LIMIT_SLEEP)

    db.log_run(
        collector_name="arxiv_collector",
        companies_processed=total,
        signals_added=total_signals,
        errors=total_errors,
        started_at=started_at,
    )

    print(f"\nDone. {total_signals} signals added, {total_errors} errors.")


if __name__ == "__main__":
    run()

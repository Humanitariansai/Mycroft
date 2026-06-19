"""Fetches and parses SEC EDGAR filings (10-K, 8-K) for tracked public companies."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import edgar
from dotenv import load_dotenv
from groq import Groq

import db
import langfuse_helper

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEED_FILE = Path(__file__).parent / "seed_companies.json"
GROQ_MODEL = "llama-3.3-70b-versatile"
RATE_LIMIT_SLEEP = 1  # seconds between companies

SUMMARY_PROMPT = (
    "In one sentence, explain why this SEC filing signal matters to an "
    "enterprise evaluating this AI vendor as a potential partner: {headline}"
)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def _set_edgar_identity() -> None:
    name = os.getenv("EDGAR_NAME", "").strip()
    email = os.getenv("EDGAR_EMAIL", "").strip()
    if not name or not email:
        raise EnvironmentError(
            "EDGAR_NAME and EDGAR_EMAIL must be set in .env.\n"
            "  The SEC requires a User-Agent string for all EDGAR requests.\n"
            "  Example:\n"
            "    EDGAR_NAME=Jane Smith\n"
            "    EDGAR_EMAIL=jane@example.com"
        )
    edgar.set_identity(f"{name} {email}")


def _groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set in .env. Cannot generate summaries."
        )
    return Groq(api_key=api_key)


# ---------------------------------------------------------------------------
# Filing helpers
# ---------------------------------------------------------------------------

def _business_description(filing) -> str:
    """Extract the first 300 chars of a 10-K's business section, or a fallback."""
    try:
        tenk = filing.obj()
        # edgartools exposes the business section via the TenK object
        business = getattr(tenk, "business", None)
        if business:
            text = str(business).strip()
            return text[:300] if text else "No description available"
    except Exception:
        pass

    try:
        text = filing.text()
        # Rough heuristic: find "ITEM 1." and grab the next 300 chars
        upper = text.upper()
        idx = upper.find("ITEM 1.")
        if idx != -1:
            snippet = text[idx + 7 : idx + 307].strip()
            return snippet if snippet else "No description available"
    except Exception:
        pass

    return "No description available"


def _eightk_items(filing) -> list[str]:
    """Return the list of item strings from an 8-K filing object."""
    try:
        eightk = filing.obj()
        items = getattr(eightk, "items", [])
        return list(items) if items else []
    except Exception:
        return []


def _has_item_502(items: list[str]) -> bool:
    return any("5.02" in item for item in items)


# ---------------------------------------------------------------------------
# LLM summary
# ---------------------------------------------------------------------------

def _generate_summary(groq: Groq, headline: str, company_name: str, signal_type: str, importance_score: int) -> tuple[str, str | None]:
    """Call Groq to summarise the signal. Returns (summary, trace_id)."""
    prompt = SUMMARY_PROMPT.format(headline=headline)
    response = groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.3,
    )
    summary = response.choices[0].message.content.strip()

    trace_id = langfuse_helper.trace_signal_classification(
        company_name=company_name,
        headline=headline,
        signal_type=signal_type,
        importance_score=importance_score,
        model_name=GROQ_MODEL,
    )

    return summary, trace_id


# ---------------------------------------------------------------------------
# Per-company processing
# ---------------------------------------------------------------------------

def _process_company(company: dict, groq: Groq) -> tuple[int, int]:
    """Process one company. Returns (signals_added, errors)."""
    name = company["name"]
    ticker = company["ticker"]
    signals_added = 0
    errors = 0

    edgar_company = edgar.Company(ticker)

    # --- 10-K ---
    try:
        tenk_filings = edgar_company.get_filings(form="10-K")
        latest_tenk = tenk_filings.latest()
        if latest_tenk:
            filing_date = latest_tenk.filing_date
            description = _business_description(latest_tenk)
            headline = (
                f"{name} filed 10-K for fiscal year ending {filing_date}"
            )
            summary, trace_id = _generate_summary(
                groq, headline, name, "annual_filing", 40
            )
            inserted = db.insert_signal(
                company_name=name,
                ticker=ticker,
                signal_type="annual_filing",
                signal_date=filing_date,
                headline=headline,
                summary=summary,
                source_url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K",
                importance_score=40,
                raw_data={"description": description},
                langfuse_trace_id=trace_id,
            )
            if inserted:
                signals_added += 1
    except Exception as exc:
        print(f"    [10-K error] {name}: {exc}")
        errors += 1

    # --- 8-K (most recent 3) ---
    try:
        eightk_filings = edgar_company.get_filings(form="8-K")
        recent_3 = eightk_filings.latest(3)
        # latest(n>1) returns a Filings collection; iterate it
        filing_list = list(recent_3) if hasattr(recent_3, "__iter__") else [recent_3]
        for filing in filing_list:
            try:
                filing_date = filing.filing_date
                items = _eightk_items(filing)
                items_str = ", ".join(items) if items else "unknown"

                if not _has_item_502(items):
                    continue  # only create signals for executive changes

                headline = (
                    f"{name}: officer change disclosed in 8-K ({filing_date})"
                )
                summary, trace_id = _generate_summary(
                    groq, headline, name, "executive_change", 75
                )
                inserted = db.insert_signal(
                    company_name=name,
                    ticker=ticker,
                    signal_type="executive_change",
                    signal_date=filing_date,
                    headline=headline,
                    summary=summary,
                    source_url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=8-K",
                    importance_score=75,
                    raw_data={"items": items_str},
                    langfuse_trace_id=trace_id,
                )
                if inserted:
                    signals_added += 1

            except Exception as exc:
                print(f"    [8-K filing error] {name}: {exc}")
                errors += 1

    except Exception as exc:
        print(f"    [8-K error] {name}: {exc}")
        errors += 1

    return signals_added, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    _set_edgar_identity()
    groq = _groq_client()

    with open(SEED_FILE) as f:
        all_companies = json.load(f)

    public_companies = [c for c in all_companies if c.get("ticker")]
    total = len(public_companies)
    total_signals = 0
    total_errors = 0
    started_at = datetime.now(tz=timezone.utc)

    print(f"EDGAR collector starting — {total} public companies to process.\n")

    for i, company in enumerate(public_companies, start=1):
        name = company["name"]
        ticker = company["ticker"]
        print(f"Processing {name} ({i}/{total})...")

        try:
            signals, errors = _process_company(company, groq)
            total_signals += signals
            total_errors += errors
            print(f"  -> {signals} signal(s) added, {errors} error(s).")
        except Exception as exc:
            print(f"  ERROR processing {name} ({ticker}): {exc}")
            total_errors += 1

        if i < total:
            time.sleep(RATE_LIMIT_SLEEP)

    db.log_run(
        collector_name="edgar_collector",
        companies_processed=total,
        signals_added=total_signals,
        errors=total_errors,
        started_at=started_at,
    )

    print(
        f"\nDone. {total_signals} signals added, {total_errors} errors."
    )


if __name__ == "__main__":
    run()

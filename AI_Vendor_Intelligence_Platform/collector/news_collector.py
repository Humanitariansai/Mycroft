"""Scrapes and normalises news articles and press releases for tracked AI vendors."""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import feedparser
from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, os.path.dirname(__file__))
import db
import langfuse_helper

load_dotenv()

SEED_FILE = Path(__file__).parent / "seed_companies.json"
RATE_LIMIT_SLEEP = 1  # seconds between companies
GROQ_MODEL = "llama-3.3-70b-versatile"

CLASSIFICATION_PROMPT = """Classify this news headline about the AI company {company_name}.
Headline: '{title}'

Return only valid JSON with these exact fields:
{{
  "signal_type": one of [funding, executive_change, product_launch, partnership, negative, regulatory, other],
  "importance_score": integer 0-100,
  "one_line_summary": string under 150 chars
}}

Scoring guide:
- funding rounds: 85
- executive changes: 75
- product launches: 70
- partnerships: 60
- negative news (layoffs, outages, lawsuits): 80
- regulatory: 65
- other: 30"""


# ---------------------------------------------------------------------------
# Groq classification
# ---------------------------------------------------------------------------

def classify_article(groq: Groq, company_name: str, title: str) -> dict:
    """Call Groq to classify a news article. Returns dict with classification."""
    prompt = CLASSIFICATION_PROMPT.format(company_name=company_name, title=title)
    attempts = 0
    max_attempts = 2

    while attempts < max_attempts:
        attempts += 1
        try:
            response = groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=200,
                temperature=0,
            )
            json_text = response.choices[0].message.content.strip()
            classification = json.loads(json_text)
            return classification
        except Exception as exc:
            error_message = str(exc)
            # Check for 429 rate limit error
            if "429" in error_message or "rate_limit" in error_message.lower():
                if attempts < max_attempts:
                    # Parse wait time from error message
                    match = re.search(r'try again in (\d+)m([\d.]+)s', error_message)
                    if match:
                        wait = int(match.group(1)) * 60 + float(match.group(2)) + 5
                    else:
                        wait = 180  # default 3 minutes
                    print(f"  [rate limit] Daily token limit reached. Waiting {wait:.0f}s before retrying...")
                    time.sleep(wait)
                    continue
                else:
                    # Second attempt failed, fall back to defaults
                    return {
                        "signal_type": "other",
                        "importance_score": 30,
                        "one_line_summary": title[:150],
                    }
            # Non-rate-limit errors: return defaults immediately
            elif isinstance(exc, (json.JSONDecodeError, KeyError, AttributeError)):
                return {
                    "signal_type": "other",
                    "importance_score": 30,
                    "one_line_summary": title[:150],
                }
            else:
                # Other exceptions: return defaults
                return {
                    "signal_type": "other",
                    "importance_score": 30,
                    "one_line_summary": title[:150],
                }


# ---------------------------------------------------------------------------
# Per-company processing
# ---------------------------------------------------------------------------

def _process_company(company: dict, groq: Groq) -> tuple[int, int]:
    """Fetch and classify news for a company. Returns (signals_added, errors)."""
    name = company["name"]
    ticker = company.get("ticker")
    signals_added = 0
    errors = 0

    # Fetch Google News RSS
    url = (
        f"https://news.google.com/rss/search"
        f"?q={name.replace(' ', '+')}+AI&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        feed = feedparser.parse(url)
        if not feed.entries:
            return 0, 0
    except Exception as exc:
        print(f"  News feed fetch failed for {name}: {exc}")
        return 0, 1

    now = datetime.now(tz=timezone.utc)

    for entry in feed.entries:
        try:
            pub_date = parsedate_to_datetime(entry.published)
        except (TypeError, AttributeError, ValueError):
            continue

        # Filter to last 7 days
        days_old = (now - pub_date).days
        if days_old > 7:
            continue

        title = entry.get("title", "Untitled")[:300]
        link = entry.get("link", "")

        # Classify with Groq
        classification = classify_article(groq, name, entry.get("title", ""))
        signal_type = classification.get("signal_type", "other")
        importance_score = classification.get("importance_score", 30)
        one_line_summary = classification.get("one_line_summary", title[:150])

        # Log to Langfuse
        trace_id = langfuse_helper.trace_signal_classification(
            company_name=name,
            headline=entry.get("title", ""),
            signal_type=signal_type,
            importance_score=importance_score,
            model_name=GROQ_MODEL,
        )

        # Insert signal
        try:
            inserted = db.insert_signal(
                company_name=name,
                ticker=ticker,
                signal_type=signal_type,
                signal_date=pub_date.date(),
                headline=title,
                summary=one_line_summary,
                source_url=link,
                importance_score=importance_score,
                raw_data={
                    "feed_title": feed.feed.get("title", ""),
                    "original_title": entry.get("title", ""),
                },
                langfuse_trace_id=trace_id,
            )
            if inserted:
                signals_added += 1
        except Exception as exc:
            print(f"    [insert error] {title}: {exc}")
            errors += 1

    return signals_added, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set in .env. Cannot classify articles."
        )

    groq = Groq(api_key=api_key)

    with open(SEED_FILE) as f:
        all_companies = json.load(f)

    total = len(all_companies)
    total_signals = 0
    total_errors = 0
    started_at = datetime.now(tz=timezone.utc)

    print(f"News collector starting — {total} companies to process.\n")

    for i, company in enumerate(all_companies, start=1):
        name = company["name"]
        print(f"Processing {name} ({i}/{total})...")

        try:
            signals, errors = _process_company(company, groq)
            total_signals += signals
            total_errors += errors
            print(f"  -> {signals} signal(s) added, {errors} error(s).")
        except Exception as exc:
            print(f"  ERROR processing {name}: {exc}")
            total_errors += 1

        if i < total:
            time.sleep(RATE_LIMIT_SLEEP)

    db.log_run(
        collector_name="news_collector",
        companies_processed=total,
        signals_added=total_signals,
        errors=total_errors,
        started_at=started_at,
    )

    print(f"\nDone. {total_signals} signals added, {total_errors} errors.")


if __name__ == "__main__":
    run()

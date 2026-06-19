"""Collects GitHub activity metrics (stars, commits, contributors, releases) for tracked orgs."""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from github import Auth, Github, UnknownObjectException
import os

import db

load_dotenv()

SEED_FILE = Path(__file__).parent / "seed_companies.json"
RATE_LIMIT_SLEEP = 0.5  # seconds between companies
RATE_LIMIT_BUFFER = 100  # pause if remaining requests fall below this


# ---------------------------------------------------------------------------
# Importance scoring
# ---------------------------------------------------------------------------

def _release_importance(stars: int) -> int:
    if stars >= 10_000:
        return 85
    if stars >= 1_000:
        return 65
    if stars >= 100:
        return 45
    return 30


def _activity_importance(velocity_score: int) -> int:
    return min(90, 30 + velocity_score * 5)


# ---------------------------------------------------------------------------
# Rate-limit guard
# ---------------------------------------------------------------------------

def _wait_for_rate_limit(g: Github) -> None:
    rate = g.get_rate_limit()
    if rate.resources.core.remaining < RATE_LIMIT_BUFFER:
        reset_time = rate.resources.core.reset.replace(tzinfo=timezone.utc)
        now = datetime.now(tz=timezone.utc)
        wait_seconds = max(0, (reset_time - now).total_seconds()) + 5
        print(
            f"  [rate limit] Only {rate.resources.core.remaining} requests remaining. "
            f"Sleeping {wait_seconds:.0f}s until reset..."
        )
        time.sleep(wait_seconds)


# ---------------------------------------------------------------------------
# Per-company processing
# ---------------------------------------------------------------------------

def _process_company(company: dict, g: Github) -> tuple[int, int]:
    """Process one company. Returns (signals_added, errors)."""
    name = company["name"]
    ticker = company.get("ticker")
    github_org = company["github_org"]
    signals_added = 0
    errors = 0

    now = datetime.now(tz=timezone.utc)
    cutoff_7d = now - timedelta(days=7)
    cutoff_90d = now - timedelta(days=90)

    # --- Fetch org and top repos ---
    try:
        org = g.get_organization(github_org)
    except UnknownObjectException:
        print(f"  GitHub org not found for {name} (org: {github_org})")
        return 0, 0

    all_repos = list(org.get_repos(type="public", sort="stargazers"))
    top_repos = sorted(all_repos, key=lambda r: r.stargazers_count, reverse=True)[:5]

    if not top_repos:
        return 0, 0

    top_repo = top_repos[0]
    top_stars = top_repo.stargazers_count
    top_repo_name = top_repo.name

    # --- Releases: velocity (90d) and recent (7d) signals ---
    velocity_score = 0

    for repo in top_repos:
        stars = repo.stargazers_count
        try:
            releases = list(repo.get_releases())
        except Exception as exc:
            print(f"    [releases error] {github_org}/{repo.name}: {exc}")
            errors += 1
            continue

        for release in releases:
            published = release.published_at
            if published is None:
                continue
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)

            if published >= cutoff_90d:
                velocity_score += 1

            if published >= cutoff_7d:
                tag = release.tag_name or "unknown"
                headline = f"{github_org}/{repo.name} released {tag}"
                raw = {
                    "repo": repo.name,
                    "tag": tag,
                    "stars": stars,
                    "published_at": published.isoformat(),
                    "release_url": release.html_url,
                }
                try:
                    inserted = db.insert_signal(
                        company_name=name,
                        ticker=ticker,
                        signal_type="github_release",
                        signal_date=published.date(),
                        headline=headline,
                        summary=(
                            f"{github_org} published {tag} for {repo.name} "
                            f"({stars:,} stars) on {published.strftime('%Y-%m-%d')}."
                        ),
                        source_url=release.html_url,
                        importance_score=_release_importance(stars),
                        raw_data=raw,
                    )
                    if inserted:
                        signals_added += 1
                except Exception as exc:
                    print(f"    [insert error] {headline}: {exc}")
                    errors += 1

    # --- Monthly activity summary (one per company per run) ---
    repo_details = [
        {
            "name": r.name,
            "stars": r.stargazers_count,
            "open_issues": r.open_issues_count,
            "last_push": r.pushed_at.isoformat() if r.pushed_at else None,
        }
        for r in top_repos
    ]
    activity_headline = (
        f"{name} GitHub: {velocity_score} releases in 90 days, "
        f"top repo {top_repo_name} has {top_stars:,} stars"
    )
    try:
        inserted = db.insert_signal(
            company_name=name,
            ticker=ticker,
            signal_type="github_activity",
            signal_date=now.date(),
            headline=activity_headline,
            summary=(
                f"{name}'s top GitHub repo ({top_repo_name}) has {top_stars:,} stars. "
                f"{velocity_score} releases across top repos in the last 90 days."
            ),
            source_url=f"https://github.com/{github_org}",
            importance_score=_activity_importance(velocity_score),
            raw_data={
                "github_org": github_org,
                "velocity_90d": velocity_score,
                "top_repos": repo_details,
            },
        )
        if inserted:
            signals_added += 1
    except Exception as exc:
        print(f"    [insert error] activity summary for {name}: {exc}")
        errors += 1

    return signals_added, errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise EnvironmentError(
            "GITHUB_TOKEN is not set in .env.\n"
            "  Create a GitHub personal access token (read-only, public repos) and add it."
        )

    g = Github(auth=Auth.Token(token))

    with open(SEED_FILE) as f:
        all_companies = json.load(f)

    companies = [c for c in all_companies if c.get("github_org")]
    total = len(companies)
    total_signals = 0
    total_errors = 0
    started_at = datetime.now(tz=timezone.utc)

    print(f"GitHub collector starting — {total} companies to process.\n")

    for i, company in enumerate(companies, start=1):
        name = company["name"]
        print(f"Processing {name} ({i}/{total})...")

        _wait_for_rate_limit(g)

        try:
            signals, errors = _process_company(company, g)
            total_signals += signals
            total_errors += errors
            print(f"  -> {signals} signal(s) added, {errors} error(s).")
        except Exception as exc:
            print(f"  ERROR processing {name}: {exc}")
            total_errors += 1

        if i < total:
            time.sleep(RATE_LIMIT_SLEEP)

    db.log_run(
        collector_name="github_collector",
        companies_processed=total,
        signals_added=total_signals,
        errors=total_errors,
        started_at=started_at,
    )

    print(f"\nDone. {total_signals} signals added, {total_errors} errors.")


if __name__ == "__main__":
    run()

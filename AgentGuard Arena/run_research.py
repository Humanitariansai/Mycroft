"""
Standalone runner for the Research Agent.

Lets you exercise the offensive-research agent in isolation — independently of the
Streamlit app and the rest of the swarm — so you can see exactly what gets scraped
and what brief DeepSeek synthesizes from it.

Examples
--------
# List the available target profiles:
    python3 run_research.py --list

# Scrape-only — show the RAW web hits per query (no LLM, no W&B key needed):
    python3 run_research.py --profile "FinTech Wealth Assistant" --scrape-only

# Scrape ONE custom query and show raw hits:
    python3 run_research.py --query "latest LLM jailbreak techniques 2026" --scrape-only

# Full run — scrape + DeepSeek synthesis (needs WANDB_API_KEY exported):
    python3 run_research.py --profile "HealthTech Triage Bot"
"""

import argparse
import sys

from profiles import TARGET_PROFILES


def _print_hits(query: str, hits: list) -> None:
    print(f"\n  QUERY: {query}")
    if not hits:
        print("    (no results — ddgs not installed, rate-limited, or no network)")
        return
    for i, h in enumerate(hits, 1):
        print(f"    [{i}] {h['title']}")
        print(f"        url: {h['url']}")
        snippet = (h["snippet"] or "").replace("\n", " ")
        print(f"        snippet: {snippet[:200]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AgentGuard research agent standalone.")
    parser.add_argument("--profile", help="Target profile name (see --list). Default: first profile.")
    parser.add_argument("--query", help="Scrape a single custom query instead of the profile's queries.")
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Only show raw scraped web hits — skip the DeepSeek synthesis (no W&B key needed).",
    )
    parser.add_argument("--list", action="store_true", help="List available target profiles and exit.")
    parser.add_argument(
        "--frameworks",
        action="store_true",
        help="Scrape the authoritative frameworks (OWASP / MITRE ATLAS) and exit. No W&B key needed.",
    )
    args = parser.parse_args()

    if args.list:
        print("Available target profiles:")
        for name in TARGET_PROFILES:
            print(f"  - {name}  ({TARGET_PROFILES[name].get('domain', 'n/a')})")
        return

    if args.frameworks:
        from web_search import frameworks_brief

        print("=" * 78)
        print("AUTHORITATIVE SECURITY FRAMEWORKS · live scrape")
        print("=" * 78)
        brief = frameworks_brief()
        print(brief or "(all framework scrapes failed — check network)")
        return

    # Scraper lives in its own dependency-free module, so --scrape-only works
    # without weave / openai / a W&B key installed.
    from web_search import web_search as _web_search

    # ── Single custom query path ──────────────────────────────────────────────────
    if args.query:
        print("=" * 78)
        print("RESEARCH AGENT · single-query scrape")
        print("=" * 78)
        _print_hits(args.query, _web_search(args.query, max_results=5))
        return

    # ── Profile-driven path ───────────────────────────────────────────────────────
    profile_name = args.profile or next(iter(TARGET_PROFILES))
    if profile_name not in TARGET_PROFILES:
        print(f"Unknown profile: {profile_name!r}")
        print("Use --list to see valid names.")
        sys.exit(1)

    profile = TARGET_PROFILES[profile_name]
    queries = profile.get("research_queries", [])

    print("=" * 78)
    print(f"RESEARCH AGENT · profile: {profile_name}")
    print(f"domain : {profile.get('domain', 'n/a')}")
    print(f"target : {profile['role']}")
    print("=" * 78)

    print("\n── STEP 1/2 · SCRAPING WEB (ddgs / DuckDuckGo, keyless) " + "─" * 22)
    for q in queries[:4]:
        _print_hits(q, _web_search(q, max_results=3))

    if args.scrape_only:
        print("\n[scrape-only] Skipping DeepSeek synthesis. Drop --scrape-only for the full brief.")
        return

    print("\n── STEP 2/2 · SYNTHESIZING BRIEF (DeepSeek via W&B) " + "─" * 25)
    from core_swarm import run_researcher

    intel = run_researcher(profile, history=[], profile_name=profile_name)
    print(f"\nLive sources scraped: {len(intel['sources'])}")
    print("\n" + "=" * 78)
    print("ATTACK INTELLIGENCE BRIEF")
    print("=" * 78)
    print(intel["brief"])
    print("=" * 78)


if __name__ == "__main__":
    main()

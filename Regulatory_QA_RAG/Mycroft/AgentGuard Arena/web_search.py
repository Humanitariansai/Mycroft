"""
Web-intelligence helpers for the research agent.

Two layers:
  1. Curated AUTHORITATIVE FRAMEWORKS — scraped from OWASP and MITRE ATLAS.
     These give the research agent a credible, recognizable vulnerability taxonomy
     (the names every security judge knows) to anchor and label its attack ideas.
  2. Open-web search via DuckDuckGo (keyless) for the freshest in-the-wild tradecraft.

Kept isolated from the swarm's heavy imports (weave / openai) so the scraping layer
can run standalone — e.g. `run_research.py --scrape-only` with no W&B key.
Every fetch is best-effort: it never raises, returning empty results on failure so
the research agent degrades gracefully to model knowledge.
"""

import os
import re

# Pre-scraped knowledge base produced by build_research_kb.py (lives next to this file).
KB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_kb.md")

# Authoritative source endpoints (resolved to stable, scrape-friendly URLs).
OWASP_LLM_URL = "https://owasp.org/www-project-top-10-for-large-language-model-applications/"
MITRE_ATLAS_URL = "https://atlas.mitre.org/techniques/"
# The ATLAS site is a JS SPA; it loads its technique data from this YAML on its own
# origin (discovered in the site bundle: fetch('/atlas-data/dist/...')).
MITRE_ATLAS_DATA_URL = "https://atlas.mitre.org/atlas-data/dist/ATLAS.yaml"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# Process-level cache — these frameworks change rarely, so we fetch once per run
# rather than on every round of the adversarial loop.
_FRAMEWORK_CACHE = {}


def _get(url: str, timeout: int = 20):
    """Best-effort HTTP GET. Returns response text or None. Never raises."""
    try:
        import requests

        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


# ─── Authoritative framework scrapers ───────────────────────────────────────────────

def fetch_owasp_llm_top10() -> dict:
    """OWASP Top 10 for LLM Applications — e.g. 'LLM01: Prompt Injection'."""
    html = _get(OWASP_LLM_URL)
    items = []
    if html:
        seen = set()
        for m in re.findall(r"LLM\d{2}:\s*[A-Za-z][A-Za-z &/\-]{2,50}", html):
            label = re.sub(r"\s+", " ", m).strip()
            if label not in seen:
                seen.add(label)
                items.append(label)
    return {
        "source": "OWASP Top 10 for LLM Applications",
        "url": OWASP_LLM_URL,
        "items": items,
    }


def fetch_mitre_atlas_techniques() -> dict:
    """MITRE ATLAS adversarial-AI techniques — e.g. 'AML.T0051 - LLM Prompt Injection'."""
    raw = _get(MITRE_ATLAS_DATA_URL, timeout=30)
    items = []
    if raw:
        try:
            import yaml

            data = yaml.safe_load(raw)

            # Walk the document; collect every object tagged as a top-level technique.
            def _walk(node):
                if isinstance(node, dict):
                    obj_type = node.get("object-type")
                    tid = node.get("id", "")
                    name = node.get("name", "")
                    # Main techniques look like AML.T0051 (sub-techniques add '.000').
                    if obj_type == "technique" and re.fullmatch(r"AML\.T\d{4}", str(tid)):
                        items.append({"id": tid, "name": name})
                    for v in node.values():
                        _walk(v)
                elif isinstance(node, list):
                    for v in node:
                        _walk(v)

            _walk(data)
        except Exception:
            pass

    # De-dupe, keep stable order by technique id.
    uniq = {it["id"]: it for it in items}
    ordered = [uniq[k] for k in sorted(uniq)]
    return {
        "source": "MITRE ATLAS (Adversarial Threat Landscape for AI Systems)",
        "url": MITRE_ATLAS_URL,
        "items": ordered,  # list of {"id", "name"}
    }


def fetch_security_frameworks(use_cache: bool = True) -> dict:
    """Scrape the authoritative frameworks (cached per process)."""
    if use_cache and _FRAMEWORK_CACHE:
        return _FRAMEWORK_CACHE
    result = {
        "owasp": fetch_owasp_llm_top10(),
        "mitre_atlas": fetch_mitre_atlas_techniques(),
    }
    _FRAMEWORK_CACHE.update(result)
    return result


def frameworks_brief(use_cache: bool = True) -> str:
    """
    Render the scraped frameworks into a compact text block the research agent can
    feed to the LLM. MITRE techniques are filtered to the most attack-relevant ones
    (with the full count noted) to stay concise.
    """
    fw = fetch_security_frameworks(use_cache=use_cache)
    blocks = []

    owasp = fw["owasp"]
    if owasp["items"]:
        lines = "\n".join(f"- {x}" for x in owasp["items"])
        blocks.append(f"[{owasp['source']}] ({owasp['url']})\n{lines}")

    atlas = fw["mitre_atlas"]
    if atlas["items"]:
        kw = ("LLM", "Prompt", "Jailbreak", "Poison", "Evasion", "Exfiltrat",
              "Manipulat", "Inject", "Extraction", "Backdoor")
        relevant = [it for it in atlas["items"] if any(k.lower() in it["name"].lower() for k in kw)]
        shown = relevant or atlas["items"][:12]
        lines = "\n".join(f"- {it['id']} - {it['name']}" for it in shown)
        blocks.append(
            f"[{atlas['source']}] ({atlas['url']})\n"
            f"{lines}\n(...{len(atlas['items'])} ATLAS techniques total)"
        )

    if not blocks:
        return ""
    return "AUTHORITATIVE SECURITY FRAMEWORKS (live-scraped — cite these IDs/names):\n\n" + "\n\n".join(blocks)


# ─── Pre-scraped knowledge base loader ───────────────────────────────────────────────

def load_research_kb(profile_name: str, path: str = KB_PATH) -> dict:
    """
    Load the pre-scraped knowledge base (research_kb.md) and return the slice
    relevant to one profile: the shared authoritative-frameworks section plus that
    profile's own domain threat-intel block. Returns {"text": str, "urls": list}.
    Returns empty text if the file is missing/unreadable so callers can fall back
    to a live scrape.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            md = f.read()
    except Exception:
        return {"text": "", "urls": []}

    # Section 1 = frameworks, Section 2 = per-domain web intel.
    marker = "## 2. Domain Threat Intelligence"
    idx = md.find(marker)
    frameworks = md[:idx] if idx != -1 else md
    domain_part = md[idx:] if idx != -1 else ""

    # Keep frameworks from the "## 1." heading onward (drop the title/timestamp).
    f1 = frameworks.find("## 1.")
    if f1 != -1:
        frameworks = frameworks[f1:]

    # Pull just this profile's "### <name>" block out of the domain section.
    profile_block = ""
    if domain_part and profile_name:
        head = f"### {profile_name}"
        h = domain_part.find(head)
        if h != -1:
            rest = domain_part[h + len(head):]
            nxt = rest.find("\n### ")
            profile_block = head + (rest if nxt == -1 else rest[:nxt])

    parts = [p.strip() for p in (frameworks, profile_block) if p.strip()]
    text = "\n\n".join(parts)
    urls = re.findall(r"\((https?://[^)\s]+)\)", text)
    return {"text": text, "urls": urls}


# ─── Open-web search (keyless) ───────────────────────────────────────────────────────

def web_search(query: str, max_results: int = 4) -> list:
    """
    Best-effort keyless web search via DuckDuckGo. Returns a list of
    {title, snippet, url} dicts. Never raises — returns [] if search is
    unavailable so the research agent can fall back to model knowledge.
    """
    try:
        try:
            from ddgs import DDGS  # newer package name
        except ImportError:
            from duckduckgo_search import DDGS  # legacy package name

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", ""),
                    }
                )
        return results
    except Exception:
        return []

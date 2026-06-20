"""Smoke-test all four external services before running collectors."""

import os
import re
from dotenv import load_dotenv

load_dotenv()

results: dict[str, bool] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask_password(url: str) -> str:
    """Replace the password in a Postgres URL with ***."""
    return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", url)


def _pass(service: str, detail: str) -> None:
    print(f"  [PASS] {service}: {detail}")
    results[service] = True


def _fail(service: str, detail: str) -> None:
    print(f"  [FAIL] {service}: {detail}")
    results[service] = False


# ---------------------------------------------------------------------------
# 1. Postgres
# ---------------------------------------------------------------------------

def _ensure_sslmode(url: str) -> str:
    """Append sslmode=require if no sslmode is already present in the URL."""
    if "sslmode=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}sslmode=require"


def check_postgres() -> None:
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        _fail("Postgres", "DATABASE_URL is not set in .env")
        return

    connect_url = _ensure_sslmode(database_url)
    host_match = re.search(r"@([^:/]+)", connect_url)
    host = host_match.group(1) if host_match else _mask_password(connect_url)

    try:
        import psycopg2
        conn = psycopg2.connect(connect_url)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        _pass("Postgres", f"connected to {host}")
    except Exception as exc:
        _fail("Postgres", str(exc))
        print(
            f"         Attempted host : {host}\n"
            f"         Check: is your Supabase project paused?\n"
            f"           Go to supabase.com → your project → check if it shows\n"
            f"           'Project is paused' and resume it if so."
        )


# ---------------------------------------------------------------------------
# 2. Groq
# ---------------------------------------------------------------------------

def check_groq() -> None:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        _fail("Groq", "GROQ_API_KEY is not set in .env")
        return
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say hello in one word"}],
            max_tokens=10,
            temperature=0,
        )
        word = response.choices[0].message.content.strip()
        _pass("Groq", f'model responded: "{word}"')
    except Exception as exc:
        _fail("Groq", str(exc))


# ---------------------------------------------------------------------------
# 3. GitHub
# ---------------------------------------------------------------------------

def check_github() -> None:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        _fail("GitHub", "GITHUB_TOKEN is not set in .env")
        return
    try:
        from github import Auth, Github
        g = Github(auth=Auth.Token(token))
        rate_limit = g.get_rate_limit()
        print(f"         [debug] type : {type(rate_limit)}")
        print(f"         [debug] dir  : {[a for a in dir(rate_limit) if not a.startswith('_')]}")
        # Try known attribute paths in order; fall back to repr
        if hasattr(rate_limit, "core"):
            remaining = rate_limit.core.remaining
        elif hasattr(rate_limit, "rate"):
            remaining = rate_limit.rate.remaining
        else:
            remaining = repr(rate_limit)
        _pass("GitHub", f"{remaining} requests remaining")
    except Exception as exc:
        _fail("GitHub", str(exc))


# ---------------------------------------------------------------------------
# 4. Langfuse
# ---------------------------------------------------------------------------

def check_langfuse() -> None:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        missing = []
        if not public_key:
            missing.append("LANGFUSE_PUBLIC_KEY")
        if not secret_key:
            missing.append("LANGFUSE_SECRET_KEY")
        _fail("Langfuse", f"{', '.join(missing)} not set in .env")
        return
    try:
        from langfuse import Langfuse
        client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)
        trace = client.trace(name="setup_check")
        client.flush()
        _pass("Langfuse", f"trace created — ID: {trace.id}")
    except Exception as exc:
        _fail("Langfuse", str(exc))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n── AI Vendor Intelligence Platform — setup check ──────────────────\n")

    print("Postgres …")
    check_postgres()

    print("Groq …")
    check_groq()

    print("GitHub …")
    check_github()

    print("Langfuse …")
    check_langfuse()

    # --- Summary ---
    passed = sum(1 for ok in results.values() if ok)
    total = 4

    print(f"\n── Results ─────────────────────────────────────────────────────────\n")
    print(f"  {passed}/{total} services ready")

    core_ready = all(results.get(svc) for svc in ("Postgres", "Groq", "GitHub"))
    if core_ready:
        print("  Ready to run collectors: yes\n")
    else:
        print("  Ready to run collectors: no — fix the above before continuing\n")


if __name__ == "__main__":
    main()

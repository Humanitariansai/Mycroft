"""Run all four collectors in sequence with a consolidated summary."""

import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s" if m else f"{s}s"


def _run(label: str, module_name: str) -> bool:
    """Import *module_name*, call its run(), and return True on success."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    t0 = time.monotonic()
    try:
        import importlib
        mod = importlib.import_module(module_name)
        mod.run()
        elapsed = time.monotonic() - t0
        print(f"\n  [{label}] finished in {_fmt_elapsed(elapsed)}.")
        return True
    except Exception as exc:
        elapsed = time.monotonic() - t0
        print(f"\n  [{label}] FAILED after {_fmt_elapsed(elapsed)}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    wall_start = time.monotonic()
    started_at = datetime.now(tz=timezone.utc)
    print(f"run_all starting at {started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    collectors = [
        ("EDGAR collector",  "edgar_collector"),
        ("GitHub collector", "github_collector"),
        ("ArXiv collector",  "arxiv_collector"),
        ("News collector",   "news_collector"),
    ]

    results = {}
    for label, module in collectors:
        results[label] = _run(label, module)

    # --- Summary ---
    elapsed = time.monotonic() - wall_start
    succeeded = sum(1 for ok in results.values() if ok)
    failed    = len(results) - succeeded

    print(f"\n{'='*60}")
    print(f"  ALL COLLECTORS COMPLETE — {_fmt_elapsed(elapsed)} total")
    print(f"{'='*60}")
    for label, ok in results.items():
        status = "OK   " if ok else "FAIL "
        print(f"  [{status}] {label}")
    print(f"\n  {succeeded}/{len(results)} collectors succeeded, {failed} failed.")
    print("  Check Postgres for results  →  python verify.py")


if __name__ == "__main__":
    main()

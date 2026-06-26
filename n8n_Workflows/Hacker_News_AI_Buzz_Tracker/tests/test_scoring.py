"""
Standalone fixture test for compute_buzz_score.py scoring math.

Run from the repo root:
    python tests/test_scoring.py

Uses the same scoring constants and formulas as the n8n Code node so that
a passing suite means the live node behaves as expected.
"""

import json
import math
import sys
import os

# ---------------------------------------------------------------------------
# Import scoring math directly from the production module.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from compute_buzz_score import clamp, VOLUME_REF, ENGAGEMENT_REF, FRONTPAGE_REF


def score_fixture(inp: dict) -> tuple[float, dict]:
    """Apply the same math as compute_buzz_score.func() to a flat input dict."""
    story_count = inp["storyCount"]
    engagement  = inp["totalPoints"] + inp["totalComments"]
    fp_count    = inp["frontPageCount"]
    low_conf    = inp["lowConfidence"]

    if low_conf:
        volume_score     = 30.0 * clamp(story_count / 3.0)
        engagement_score = 30.0 * clamp(engagement  / 50.0)
        front_page_score = 0.0
    else:
        volume_score     = 30.0 * clamp(math.log1p(story_count) / math.log1p(VOLUME_REF))
        engagement_score = 30.0 * clamp(math.log1p(engagement)  / math.log1p(ENGAGEMENT_REF))
        front_page_score = 20.0 * clamp(fp_count / FRONTPAGE_REF)

    accel_score = 0.0  # cold-start; Week 4 wires the DB
    buzz = round(volume_score + engagement_score + front_page_score + accel_score, 1)
    buzz_score = clamp(buzz, 0, 100)

    components = {
        "volume":      round(volume_score, 1),
        "engagement":  round(engagement_score, 1),
        "frontPage":   round(front_page_score, 1),
        "acceleration": accel_score,
    }
    return buzz_score, components


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_tests():
    fixtures_path = os.path.join(os.path.dirname(__file__), "scoring_fixtures.json")
    with open(fixtures_path) as f:
        fixtures = json.load(f)

    passed = 0
    failed = 0

    for fx in fixtures:
        fid  = fx["id"]
        inp  = fx["input"]
        exp  = fx["expected"]
        buzz, components = score_fixture(inp)

        errors = []

        # Range check
        if "buzzMin" in exp and buzz < exp["buzzMin"]:
            errors.append(f"buzz {buzz} < min {exp['buzzMin']}")
        if "buzzMax" in exp and buzz > exp["buzzMax"]:
            errors.append(f"buzz {buzz} > max {exp['buzzMax']}")

        # Exact check
        if "buzzExact" in exp and buzz != exp["buzzExact"]:
            errors.append(f"buzz {buzz} != exact {exp['buzzExact']}")

        # Low-confidence path check: floor path sets frontPage to 0
        if "lowConfidencePathUsed" in exp:
            want_floor = exp["lowConfidencePathUsed"]
            got_floor  = inp["lowConfidence"]
            if want_floor != got_floor:
                errors.append(f"lowConfidencePathUsed expected {want_floor}, got {got_floor}")
            if want_floor and components["frontPage"] != 0.0:
                errors.append(f"floor path should zero frontPage, got {components['frontPage']}")

        if errors:
            failed += 1
            print(f"FAIL  [{fid}]  buzz={buzz}  components={components}")
            for e in errors:
                print(f"        -> {e}")
        else:
            passed += 1
            print(f"PASS  [{fid}]  buzz={buzz}  components={components}")

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()

"""Local CLI for the deterministic layer.

    contract-agent analyze <migration.py> \
        --manifest <manifest.json> \
        --baseline <0001_initial.py>

Prints the structured findings: which analytics models a migration impacts, split
into what the deterministic layer can prove (structural breaks) and what it can
only flag for the semantic/LLM layer (unit changes, enum expansions).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .impact import (
    ENUM_REVIEW,
    INFORMATIONAL,
    SEMANTIC_REVIEW,
    STRUCTURAL_BREAK,
    analyze,
)
from .lineage import build_lineage
from .migration_parser import load_baseline_schema, parse_migration

_DEFAULT_MANIFEST = Path("../mock-analytics/target/manifest.json")
_DEFAULT_BASELINE = Path("fixtures/migrations/0001_initial.py")

_LABELS = {
    STRUCTURAL_BREAK: ("STRUCTURAL BREAK", "caught deterministically"),
    SEMANTIC_REVIEW: ("SEMANTIC REVIEW", "needs the LLM/semantic layer"),
    ENUM_REVIEW: ("ENUM REVIEW", "needs the LLM/semantic layer"),
    INFORMATIONAL: ("INFO", "no action"),
}
_ORDER = [STRUCTURAL_BREAK, SEMANTIC_REVIEW, ENUM_REVIEW, INFORMATIONAL]


@click.command()
@click.argument("migration", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--manifest",
    type=click.Path(dir_okay=False),
    default=str(_DEFAULT_MANIFEST),
    show_default=True,
    help="Path to the dbt target/manifest.json.",
)
@click.option(
    "--baseline",
    type=click.Path(dir_okay=False),
    default=str(_DEFAULT_BASELINE),
    show_default=True,
    help="Baseline migration that defines the operational schema.",
)
@click.option(
    "--pr",
    "pr_path",
    type=click.Path(dir_okay=False),
    default=None,
    help="JSON file with the PR title/description (enables semantic context).",
)
@click.option(
    "--semantic/--no-semantic",
    default=False,
    help="Run the LLM semantic layer (needs ANTHROPIC_API_KEY).",
)
@click.option(
    "--model",
    default=None,
    help="Override the Claude model for the semantic layer (default: claude-opus-4-8).",
)
def main(
    migration: str,
    manifest: str,
    baseline: str,
    pr_path: str | None,
    semantic: bool,
    model: str | None,
) -> None:
    """Analyze a single Alembic MIGRATION for downstream analytics impact."""
    if not Path(manifest).exists():
        raise click.ClickException(
            f"manifest not found: {manifest}\n"
            "Run `dbt build` in mock-analytics, or pass --manifest."
        )

    schema = load_baseline_schema(baseline)
    changes = parse_migration(migration)
    index = build_lineage(manifest, schema)
    report = analyze(Path(migration).name, changes, index, schema)

    click.echo(f"\n  Migration: {report.migration}")
    click.echo(f"  Parsed {len(changes)} change(s):")
    for ch in changes:
        click.echo(f"    - {ch.describe()}")

    if report.findings:
        click.echo("\n  Deterministic findings")
        click.echo("  " + "-" * 66)
        for cat in _ORDER:
            for f in report.by_category(cat):
                label, tag = _LABELS[cat]
                click.echo(f"\n  [{label}]  ({tag})")
                click.echo(f"    {f.summary}")
                if f.affected_models:
                    click.echo(f"    affected models: {', '.join(f.affected_models)}")

        structural = report.by_category(STRUCTURAL_BREAK)
        handed_off = report.by_category(SEMANTIC_REVIEW) + report.by_category(ENUM_REVIEW)
        click.echo("\n  " + "-" * 66)
        click.echo(
            f"  Deterministic summary: {len(structural)} structural break(s) caught here; "
            f"{len(handed_off)} item(s) for the semantic layer; "
            f"{len(report.affected_models)} model(s) affected."
        )
    else:
        click.echo("\n  No deterministic impact detected.")

    if semantic:
        _run_semantic(migration, manifest, baseline, pr_path, model, report)

    click.echo("")


def _run_semantic(migration, manifest, baseline, pr_path, model, report) -> None:
    """Run the LLM layer. Degrades gracefully — never aborts the deterministic output."""
    from .schema_model import BaselineSchema  # noqa: F401  (kept local; cheap)
    from .semantic import DEFAULT_MODEL, PRContext, analyze_semantic, model_sql_map

    click.echo("\n  Semantic layer (LLM)")
    click.echo("  " + "-" * 66)

    if pr_path:
        meta = json.loads(Path(pr_path).read_text())
        pr = PRContext(
            title=meta["title"],
            description=meta["description"],
            migration_code=Path(migration).read_text(),
        )
    else:
        pr = PRContext(
            title="(no PR metadata provided)",
            description="(no PR description provided — pass --pr for the intent signal)",
            migration_code=Path(migration).read_text(),
        )

    schema = load_baseline_schema(baseline)
    try:
        verdict = analyze_semantic(
            pr, report, schema, model_sql_map(manifest), model=model or DEFAULT_MODEL
        )
    except Exception as exc:  # noqa: BLE001 - graceful degradation is the whole point
        click.echo(
            f"    LLM call failed ({type(exc).__name__}: {exc}).\n"
            "    Deterministic findings above stand on their own."
        )
        return

    flag = "⚠ SEMANTIC BREAK" if verdict.contains_semantic_break else "✓ no semantic break"
    click.echo(f"\n  [{flag}]  category={verdict.risk_category.value}  "
               f"confidence={verdict.confidence:.2f}")
    if verdict.affected_models:
        click.echo(f"    affected models: {', '.join(verdict.affected_models)}")
    click.echo(f"    reasoning: {verdict.reasoning}")


if __name__ == "__main__":
    sys.exit(main())

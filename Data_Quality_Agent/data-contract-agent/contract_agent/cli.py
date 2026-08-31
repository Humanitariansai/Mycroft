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
from .simulate import DEFAULT_ENUM_SHIFT

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
@click.option(
    "--simulate",
    "run_simulation",
    is_flag=True,
    default=False,
    help="Rebuild the marts before/after the change and diff the numbers.",
)
@click.option(
    "--sources",
    type=click.Path(file_okay=False),
    default=None,
    help=(
        "Directory of <table>.parquet for the simulation (e.g. ../mock-analytics/raw). "
        "Omit to use a deterministic synthetic seed."
    ),
)
@click.option(
    "--enum-shift",
    type=click.FloatRange(0.0, 1.0),
    default=DEFAULT_ENUM_SHIFT,
    show_default=True,
    help="Counterfactual: fraction of currently-included rows that adopt a new enum value.",
)
@click.option(
    "--auto-patch/--no-auto-patch",
    default=True,
    help="Apply the mechanical rename a reviewer would make before diffing metrics.",
)
def main(
    migration: str,
    manifest: str,
    baseline: str,
    pr_path: str | None,
    semantic: bool,
    model: str | None,
    run_simulation: bool,
    sources: str | None,
    enum_shift: float,
    auto_patch: bool,
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

    if run_simulation:
        _run_simulation(changes, manifest, schema, index, sources, enum_shift, auto_patch)

    if semantic:
        _run_semantic(migration, manifest, baseline, pr_path, model, report)

    click.echo("")


def _num(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}"


def _run_simulation(
    changes, manifest, schema, index, sources, enum_shift, auto_patch
) -> None:
    """Rebuild the warehouse before/after and print the metric diff.

    Degrades gracefully for the same reason the semantic layer does: the
    deterministic findings above are the floor, and a simulation that can't run
    (no duckdb, no usable source data) must not take them down with it.
    """
    from .simulate import SimulationUnavailable, biggest_mover, simulate

    click.echo("\n  Metric impact simulation")
    click.echo("  " + "-" * 66)

    try:
        sim = simulate(
            changes,
            manifest,
            schema,
            index,
            sources=sources,
            enum_shift=enum_shift,
            auto_patch=auto_patch,
        )
    except SimulationUnavailable as exc:
        click.echo(f"    Not run: {exc}")
        return
    except Exception as exc:  # noqa: BLE001 - graceful degradation, as above
        click.echo(f"    Simulation failed ({type(exc).__name__}: {exc}).")
        click.echo("    Deterministic findings above stand on their own.")
        return

    rows = ", ".join(f"{t}={n:,}" for t, n in sorted(sim.source_rows.items()))
    click.echo(f"    warehouse: {sim.source_mode}")
    click.echo(f"    seeded:    {rows}")
    if sim.source_mode == "synthetic":
        click.echo(
            "               (synthetic seed — absolute values are illustrative; "
            "the ratios are what matter)"
        )
    click.echo(f"    replayed:  {len(sim.applied)} statement(s) against the source tables")

    for cf in sim.counterfactuals:
        scope = f" currently in ({', '.join(cf.from_values)})" if cf.from_values else ""
        click.echo(
            f"\n    Counterfactual: '{cf.value}' does not exist in any row yet, so the "
            f"simulation moves\n    {cf.fraction:.0%} of {cf.table}.{cf.column}"
            f"{scope} into it ({cf.rows_moved:,} rows) to project the impact."
        )

    if sim.as_is_failures:
        click.echo("\n    Build as-is — the loud half, what CI would show you:")
        for m, err in sim.as_is_failures.items():
            click.echo(f"      x {m}: {err}")

    if sim.patches:
        fixes = ", ".join(sorted({f"{p.rename} in {p.model}" for p in sim.patches}))
        verdict = (
            "The numbers do not survive:"
            if sim.deltas
            else "Everything compiles and every metric is identical — loud, but safe "
            "once the rename lands."
        )
        click.echo(
            f"\n    Then applied the mechanical fix a reviewer would make ({fixes}) "
            f"and rebuilt.\n    {verdict}"
        )

    if not sim.deltas:
        if not sim.patches:
            click.echo(
                "\n    No metric drift: every model rebuilt and every metric is unchanged."
            )
    else:
        for model_name in sim.changed_models:
            click.echo(f"\n      {model_name}")
            for d in sim.deltas_for(model_name):
                if d.broke:
                    click.echo(f"        {d.metric:<32} builds no longer — cannot measure")
                    continue
                decimals = 0 if d.metric == "rows" else 2
                line = (
                    f"        {d.metric:<32} {_num(d.before, decimals):>16} -> "
                    f"{_num(d.after, decimals):>16}"
                )
                if d.scale is not None:
                    line += f"   x{d.scale:g}"
                elif d.pct_change is not None:
                    line += f"   {d.pct_change:+.1f}%"
                click.echo(line)

    for line in sim.headlines():
        click.echo(f"\n    ! {line}")

    for cf in sim.counterfactuals:
        biggest = biggest_mover(sim.deltas)
        if biggest is not None and cf.fraction:
            per_point = biggest.pct_change / (cf.fraction * 100)
            click.echo(
                f"    ! Sensitivity: every 1% of {cf.table} adopting '{cf.value}' moves "
                f"{biggest.model}.{biggest.metric[4:-1]} by {per_point:+.2f}%. "
                "Scale to your own adoption estimate."
            )

    if sim.skipped:
        click.echo("\n    Not simulated:")
        for note in sim.skipped:
            click.echo(f"      - {note}")

    for note in sim.notes:
        click.echo(f"    note: {note}")


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

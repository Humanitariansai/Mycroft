"""Join parsed migration changes against the lineage index to produce findings.

This is the high-precision deterministic verdict. It deliberately stays in its
lane: it reports what it can *prove* from the schema diff + lineage (a dropped or
renamed column that a model reads will break), and it *surfaces* the patterns that
need judgement (a unit-suffix change with an arithmetic backfill; an enum value
added that an IN-list filter doesn't cover) without pretending to adjudicate them.
Those surfaced patterns are exactly the hand-off to the LLM layer in Phase 3.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .lineage import LineageIndex
from .schema_model import BaselineSchema, ChangeKind, SchemaChange

# Categories, ordered by how much human/LLM attention they need.
STRUCTURAL_BREAK = "structural_break"  # will fail to compile; deterministic catches it
SEMANTIC_REVIEW = "semantic_review"  # compiles fine, meaning may have shifted -> LLM
ENUM_REVIEW = "enum_review"  # new enum value vs hard-coded filters -> LLM
INFORMATIONAL = "informational"  # no downstream readers / benign

_ARITHMETIC_BACKFILL = re.compile(r"[/*]\s*100(\.0+)?\b|\b100(\.0+)?\s*[/*]")


@dataclass
class Finding:
    category: str
    summary: str
    affected_models: list[str] = field(default_factory=list)
    deterministic: bool = True  # True => provable here; False => needs the LLM layer
    change: SchemaChange | None = None


@dataclass
class ImpactReport:
    migration: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def affected_models(self) -> list[str]:
        out: list[str] = []
        for f in self.findings:
            for m in f.affected_models:
                if m not in out:
                    out.append(m)
        return out

    def by_category(self, category: str) -> list[Finding]:
        return [f for f in self.findings if f.category == category]


def analyze(
    migration: str,
    changes: list[SchemaChange],
    index: LineageIndex,
    schema: BaselineSchema,
) -> ImpactReport:
    report = ImpactReport(migration=migration)

    for ch in changes:
        if ch.kind is ChangeKind.RENAME_COLUMN:
            models = index.models_reading(ch.table, ch.column)
            report.findings.append(
                Finding(
                    category=STRUCTURAL_BREAK if models else INFORMATIONAL,
                    summary=(
                        f"{ch.table}.{ch.column} renamed to {ch.new_column}. "
                        f"{len(models)} model(s) reference the old name and will fail to compile."
                    ),
                    affected_models=models,
                    deterministic=True,
                    change=ch,
                )
            )

        elif ch.kind is ChangeKind.DROP_COLUMN:
            models = index.models_reading(ch.table, ch.column)
            report.findings.append(
                Finding(
                    category=STRUCTURAL_BREAK if models else INFORMATIONAL,
                    summary=(
                        f"{ch.table}.{ch.column} dropped. "
                        + (
                            f"{len(models)} model(s) read it and will break."
                            if models
                            else "No analytics model reads it."
                        )
                    ),
                    affected_models=models,
                    deterministic=True,
                    change=ch,
                )
            )

        elif ch.kind is ChangeKind.ALTER_TYPE:
            models = index.models_reading(ch.table, ch.column)
            report.findings.append(
                Finding(
                    category=SEMANTIC_REVIEW if models else INFORMATIONAL,
                    summary=(
                        f"{ch.table}.{ch.column} retyped to {ch.new_type}. "
                        "Likely still compiles; verify the new type preserves units/precision."
                    ),
                    affected_models=models,
                    deterministic=False,
                    change=ch,
                )
            )

        elif ch.kind is ChangeKind.ENUM_ADD_VALUE:
            report.findings.append(_enum_finding(ch, index, schema))

    # Cross-change pattern: add + drop + arithmetic backfill on one table == a
    # rename that also changes units. The classic silent semantic break.
    _detect_unit_rename(changes, index, report)

    return report


def _enum_finding(
    ch: SchemaChange, index: LineageIndex, schema: BaselineSchema
) -> Finding:
    cols = schema.columns_for_enum(ch.enum_type)  # [(table, column), ...]
    affected: list[str] = []
    for t, c in cols:
        for m in index.models_reading(t, c):
            if m not in affected:
                affected.append(m)

    uncovered: list[str] = []
    for m in affected:
        for f in index.enum_filters_by_model.get(m, []):
            if (f.source_table, f.source_column) in cols and ch.enum_value not in f.values:
                uncovered.append(f"{m}: `{f.column} IN ({', '.join(f.values)})`")

    if uncovered:
        summary = (
            f"Enum {ch.enum_type} gained '{ch.enum_value}'. "
            f"Hard-coded filter(s) do NOT include it, so rows with '{ch.enum_value}' "
            f"will be silently dropped: {'; '.join(uncovered)}."
        )
    else:
        summary = (
            f"Enum {ch.enum_type} gained '{ch.enum_value}'. "
            f"{len(affected)} model(s) read this enum; verify whether the new value "
            "belongs in their logic."
        )
    return Finding(
        category=ENUM_REVIEW if affected else INFORMATIONAL,
        summary=summary,
        affected_models=affected,
        deterministic=False,
        change=ch,
    )


def _detect_unit_rename(
    changes: list[SchemaChange], index: LineageIndex, report: ImpactReport
) -> None:
    adds = [c for c in changes if c.kind is ChangeKind.ADD_COLUMN]
    drops = [c for c in changes if c.kind is ChangeKind.DROP_COLUMN]
    backfills = [
        c for c in changes if c.kind is ChangeKind.RAW_SQL and c.raw_sql
    ]
    for add in adds:
        for drop in drops:
            if add.table != drop.table:
                continue
            related = [
                b
                for b in backfills
                if add.column in (b.raw_sql or "") and drop.column in (b.raw_sql or "")
            ]
            if not related:
                continue
            arithmetic = any(_ARITHMETIC_BACKFILL.search(b.raw_sql or "") for b in related)
            models = index.models_reading(drop.table, drop.column)
            unit_hint = (
                " The backfill divides/multiplies by 100, and the dropped column's "
                "name carried a unit suffix -- a units-of-measure change (e.g. cents -> "
                "dollars) that compiles cleanly but silently rescales every downstream "
                "metric. Confirm downstream conversions are updated in lockstep."
                if arithmetic
                else " Verify downstream models are updated to the new column."
            )
            report.findings.append(
                Finding(
                    category=SEMANTIC_REVIEW,
                    summary=(
                        f"Likely rename {drop.table}.{drop.column} -> {add.column} "
                        f"with backfill `{related[0].raw_sql.strip()}`."
                        + unit_hint
                    ),
                    affected_models=models,
                    deterministic=False,
                    change=add,
                )
            )

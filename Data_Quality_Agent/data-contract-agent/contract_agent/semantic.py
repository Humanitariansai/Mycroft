"""Semantic risk analyzer — the LLM layer (Phase 3).

This sits on top of the deterministic layer. The deterministic layer proves what
it can (a dropped/renamed column a model reads will break) and *surfaces* the rest
(a unit-suffix change with an arithmetic backfill, an enum value a filter omits).
This layer reads the migration, the PR's stated intent, and the affected downstream
SQL, and decides whether a change that *compiles cleanly* will silently corrupt a
metric — the judgement the deterministic layer can't make.

Design choices (see docs/decision-log):
  * Model defaults to claude-opus-4-8. Configurable for cost (e.g. claude-sonnet-4-6).
  * Output is constrained to a Pydantic schema via `client.messages.parse()` — no
    fragile JSON-string parsing.
  * `temperature` is NOT set: Opus 4.8 removed it (400 error). Determinism is steered
    by a tight prompt + the structured-output constraint instead. Adaptive thinking is
    on, because the unit/enum judgement is genuinely reasoning-heavy.
  * The call is wrapped so a failure degrades gracefully — the deterministic findings
    remain useful on their own.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from .impact import ImpactReport
from .schema_model import BaselineSchema

DEFAULT_MODEL = "claude-opus-4-8"


class RiskCategory(StrEnum):
    none = "none"  # no semantic break (benign, or purely structural)
    unit_change = "unit_change"  # column units/scale changed (e.g. cents -> dollars)
    enum_expansion = "enum_expansion"  # new enum value a downstream filter silently drops
    other_semantic = "other_semantic"  # some other compiles-but-wrong change


class SemanticVerdict(BaseModel):
    """Structured output of the semantic analyzer."""

    contains_semantic_break: bool = Field(
        description=(
            "True only if this PR introduces a change that COMPILES AND RUNS but "
            "silently produces wrong analytics numbers. A purely structural break "
            "(a rename/drop that fails at compile time) is NOT a semantic break."
        )
    )
    risk_category: RiskCategory
    affected_models: list[str] = Field(
        description="dbt models whose output would be silently wrong."
    )
    reasoning: str = Field(
        description="2-4 sentences: the mechanism of the silent break, or why there is none."
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in contains_semantic_break, 0..1."
    )


@dataclass
class PRContext:
    title: str
    description: str
    migration_code: str

    @classmethod
    def from_files(cls, pr_json: str | Path, migrations_dir: str | Path) -> PRContext:
        meta = json.loads(Path(pr_json).read_text())
        code = (Path(migrations_dir) / meta["migration"]).read_text()
        return cls(title=meta["title"], description=meta["description"], migration_code=code)


SYSTEM_PROMPT = """\
You are a data-contract reviewer. An operational engineer has opened a pull request \
that changes a Postgres schema (via an Alembic migration). Downstream, a dbt project \
turns that schema into executive metrics. Your job is to decide whether this PR will \
SILENTLY corrupt a downstream metric — a change that compiles, runs, passes tests, and \
returns a number that is simply wrong.

A deterministic layer already runs before you. It reliably catches STRUCTURAL breaks \
(a renamed or dropped column a model references — those fail loudly at compile time). \
Do NOT count a purely structural break as a semantic break; the compiler catches it. \
Your focus is the breaks that compile.

The semantic breaks that matter:

- unit_change: a monetary/quantitative column changes units or scale while a downstream \
  transformation keeps its old conversion. Classic tell: a column named `*_cents` (cents) \
  becomes `amount` (dollars) with a backfill like `amount = amount_cents / 100.0`, while a \
  staging model still divides by 100 — the metric ends up 100x wrong. The PR description \
  often frames this as routine "standardization" and a human reviewer misses it.

- enum_expansion: a new value is added to an enum, but a downstream filter hard-codes the \
  old value set (e.g. `WHERE status IN ('active','trialing')`). Rows with the new value \
  silently drop out of the metric. Whether that's a bug depends on whether the new value \
  belongs in the metric — reason about the business meaning.

- other_semantic: any other compiles-but-wrong change (nullability/default shifts that skew \
  aggregates, a backfill that changes the meaning of existing rows, etc.).

If the PR is benign (a new unused column, a rename with no downstream readers, or a purely \
structural break the compiler will catch) then contains_semantic_break is false and \
risk_category is none.

Reason from three things together: the migration code (especially raw backfill SQL), the \
PR title/description (intent — but treat it skeptically; the whole danger is plausible-looking \
intent), and the affected downstream SQL (does it still assume the old units/values?). \
Be precise and conservative: only flag a semantic break you can explain mechanically."""


def _column_dictionary(schema: BaselineSchema, tables: set[str]) -> str:
    lines: list[str] = []
    for tname in sorted(tables):
        t = schema.tables.get(tname)
        if not t:
            continue
        for c in t.columns.values():
            enum = f"  [enum {c.enum_type}]" if c.enum_type else ""
            lines.append(f"  {tname}.{c.name}: {c.type or 'unknown'}{enum}")
    return "\n".join(lines) or "  (none)"


def model_sql_map(manifest_path: str | Path) -> dict[str, str]:
    """name -> compiled_code for every model in the manifest."""
    manifest = json.loads(Path(manifest_path).read_text())
    out: dict[str, str] = {}
    for node in manifest["nodes"].values():
        if node.get("resource_type") == "model":
            out[node["name"]] = node.get("compiled_code") or node.get("raw_code") or ""
    return out


def build_user_prompt(
    pr: PRContext,
    report: ImpactReport,
    schema: BaselineSchema,
    model_sql: dict[str, str],
) -> str:
    affected = report.affected_models
    touched_tables = {
        f.change.table for f in report.findings if f.change and f.change.table
    }
    det_lines = [f"- [{f.category}] {f.summary}" for f in report.findings] or ["- (none)"]
    sql_blocks = [
        f"### {m}\n```sql\n{(model_sql.get(m) or '(sql unavailable)').strip()}\n```"
        for m in affected
    ] or ["(no affected models)"]

    return f"""\
## PR title
{pr.title}

## PR description
{pr.description}

## Alembic migration
```python
{pr.migration_code.strip()}
```

## Deterministic layer findings
{chr(10).join(det_lines)}

## Operational column dictionary (tables touched by this PR)
{_column_dictionary(schema, touched_tables)}

## Downstream dbt models flagged as affected (compiled SQL)
{chr(10).join(sql_blocks)}

Decide whether this PR contains a SILENT semantic break per your instructions."""


def analyze_semantic(
    pr: PRContext,
    report: ImpactReport,
    schema: BaselineSchema,
    model_sql: dict[str, str],
    *,
    model: str = DEFAULT_MODEL,
    client=None,
) -> SemanticVerdict:
    """Run the LLM semantic analyzer. Raises on API/SDK error (caller decides fallback)."""
    import anthropic

    client = client or anthropic.Anthropic()
    user_prompt = build_user_prompt(pr, report, schema, model_sql)

    response = client.messages.parse(
        model=model,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
        output_format=SemanticVerdict,
    )
    return response.parsed_output

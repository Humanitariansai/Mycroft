"""Column-level lineage reconstructed from a dbt manifest.

The deterministic impact analysis needs to answer one question precisely:

    "If operational column ``T.c`` changes, which analytics models read it?"

dbt's manifest gives *model-level* lineage for free (``depends_on``). To get
*column-level* lineage we parse each model's ``compiled_code`` with sqlglot and
trace every output column back to the physical source columns that feed it,
stitching staging -> marts in topological order.

The result is a ``LineageIndex`` with:
  * ``column_footprint[(model, col)]`` -> set of (source_table, source_col)
  * ``model_footprint[model]``         -> union of the above
  * ``models_reading(table, col)``     -> models whose footprint includes it
  * ``enum_filters(model)``            -> IN-lists that look like enum guards
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.lineage import lineage as sqlglot_lineage

from .schema_model import BaselineSchema

SourceCol = tuple[str, str]  # (table, column)


@dataclass
class EnumFilter:
    """An IN-list whose members are all valid enum values -- a likely enum guard."""

    model: str
    column: str  # the column being filtered (as written in the model SQL)
    values: list[str]  # the hard-coded literal members
    source_table: str | None = None  # resolved operational table, if known
    source_column: str | None = None


@dataclass
class LineageIndex:
    column_footprint: dict[tuple[str, str], set[SourceCol]] = field(default_factory=dict)
    model_footprint: dict[str, set[SourceCol]] = field(default_factory=dict)
    model_order: list[str] = field(default_factory=list)  # topological (sources first)
    enum_filters_by_model: dict[str, list[EnumFilter]] = field(default_factory=dict)
    # depth from sources, used only to sort output (staging before marts)
    depth: dict[str, int] = field(default_factory=dict)

    def models_reading(self, table: str, column: str) -> list[str]:
        hits = [m for m, fp in self.model_footprint.items() if (table, column) in fp]
        return sorted(hits, key=lambda m: (self.depth.get(m, 0), m))

    def models_touching_table(self, table: str) -> list[str]:
        hits = [
            m for m, fp in self.model_footprint.items() if any(t == table for t, _ in fp)
        ]
        return sorted(hits, key=lambda m: (self.depth.get(m, 0), m))


def _strip_quotes(s: str) -> str:
    return s.replace('"', "").replace("`", "")


class _ManifestGraph:
    """Thin view over the dbt manifest: nodes, sources, and relation->name maps."""

    def __init__(self, manifest: dict):
        self.models: dict[str, dict] = {
            nid: n
            for nid, n in manifest["nodes"].items()
            if n.get("resource_type") == "model"
        }
        self.sources: dict[str, dict] = manifest.get("sources", {})

        # bare table name -> kind, and relation string -> bare name (for SQL rewrite)
        self.source_table_by_id: dict[str, str] = {
            sid: s["name"] for sid, s in self.sources.items()
        }
        self.model_name_by_id: dict[str, str] = {
            nid: n["name"] for nid, n in self.models.items()
        }
        self.source_names: set[str] = set(self.source_table_by_id.values())
        self.model_names: set[str] = set(self.model_name_by_id.values())

        # relation_name (as it appears in compiled SQL) -> bare name
        self.relation_to_bare: dict[str, str] = {}
        for s in self.sources.values():
            if s.get("relation_name"):
                self.relation_to_bare[s["relation_name"]] = s["name"]
        for n in self.models.values():
            if n.get("relation_name"):
                self.relation_to_bare[n["relation_name"]] = n["name"]

    def normalize_sql(self, sql: str) -> str:
        """Rewrite source/model relation strings to bare identifiers for sqlglot."""
        # Replace longest relations first so substrings don't clobber each other.
        for relation in sorted(self.relation_to_bare, key=len, reverse=True):
            sql = sql.replace(relation, self.relation_to_bare[relation])
        return sql

    def topo_models(self) -> list[str]:
        """Model bare-names ordered sources-first by depends_on depth."""
        order: list[str] = []
        seen: set[str] = set()

        def visit(node_id: str):
            if node_id in seen or node_id not in self.models:
                return
            seen.add(node_id)
            for dep in self.models[node_id].get("depends_on", {}).get("nodes", []):
                visit(dep)
            order.append(self.model_name_by_id[node_id])

        for nid in self.models:
            visit(nid)
        return order


def build_lineage(manifest_path: str | Path, schema: BaselineSchema) -> LineageIndex:
    manifest = json.loads(Path(manifest_path).read_text())
    g = _ManifestGraph(manifest)
    index = LineageIndex()

    # sqlglot schema: physical sources from the baseline, models filled in as we go.
    sg_schema: dict[str, dict[str, str]] = {}
    for tname, tdef in schema.tables.items():
        if tname in g.source_names:
            sg_schema[tname] = {c: "UNKNOWN" for c in tdef.columns}

    order = g.topo_models()
    name_to_id = {v: k for k, v in g.model_name_by_id.items()}

    for model in order:
        node = g.models[name_to_id[model]]
        raw_sql = node.get("compiled_code") or node.get("raw_code") or ""
        sql = g.normalize_sql(raw_sql)
        index.depth[model] = _depth_of(g, name_to_id[model])

        try:
            parsed = sqlglot.parse_one(sql, dialect="duckdb")
        except Exception:
            parsed = None

        out_cols = list(parsed.named_selects) if parsed else []
        # register this model's output columns so downstream models can resolve them
        sg_schema[model] = {c: "UNKNOWN" for c in out_cols}

        model_fp: set[SourceCol] = set()
        for col in out_cols:
            fp = _trace_column(model, col, sql, sg_schema, g, index)
            index.column_footprint[(model, col)] = fp
            model_fp |= fp
        index.model_footprint[model] = model_fp

        if parsed is not None:
            index.enum_filters_by_model[model] = _find_enum_filters(
                model, parsed, schema, index
            )

    return index


def _depth_of(g: _ManifestGraph, node_id: str) -> int:
    deps = [
        d
        for d in g.models[node_id].get("depends_on", {}).get("nodes", [])
        if d in g.models
    ]
    if not deps:
        return 0
    return 1 + max(_depth_of(g, d) for d in deps)


def _trace_column(
    model: str,
    col: str,
    sql: str,
    sg_schema: dict,
    g: _ManifestGraph,
    index: LineageIndex,
) -> set[SourceCol]:
    """Source-column footprint of one output column, stitched transitively."""
    try:
        root = sqlglot_lineage(col, sql, schema=sg_schema, dialect="duckdb")
    except Exception:
        return set()

    footprint: set[SourceCol] = set()
    for leaf in _leaves(root):
        ref = _leaf_ref(leaf)
        if ref is None:
            continue
        table, column = ref
        if table in g.source_names:
            footprint.add((table, column))
        elif table in g.model_names:
            # transitively resolve via the upstream model's already-computed footprint
            footprint |= index.column_footprint.get((table, column), set())
    return footprint


def _leaves(root) -> list:
    out = []
    for node in root.walk():
        if not node.downstream:
            out.append(node)
    return out


def _leaf_ref(leaf) -> SourceCol | None:
    """Parse a lineage leaf into (table, column)."""
    name = _strip_quotes(leaf.name)
    if "." in name:
        table, _, column = name.rpartition(".")
        # name may be catalog.schema.table.column; keep the last two parts
        table = table.split(".")[-1]
        return (table, column)
    # unqualified leaf: try the node's source table expression
    src = getattr(leaf, "source", None)
    if isinstance(src, exp.Table):
        return (_strip_quotes(src.name), name)
    return None


_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$", re.IGNORECASE)


def _find_enum_filters(
    model: str, parsed, schema: BaselineSchema, index: LineageIndex
) -> list[EnumFilter]:
    """IN-lists over columns whose lineage resolves to an enum-backed source column.

    We don't know an enum's value-set from the schema alone, so rather than match
    on the literals we match structurally: a string-literal IN-list on a column
    that traces back to an ENUM-typed operational column is a likely enum guard.
    """
    filters: list[EnumFilter] = []
    for in_expr in parsed.find_all(exp.In):
        col_expr = in_expr.this
        if not isinstance(col_expr, exp.Column):
            continue
        members = [
            e.this
            for e in in_expr.expressions
            if isinstance(e, exp.Literal) and e.is_string
        ]
        if not members or len(members) != len(in_expr.expressions):
            continue  # not a pure string-literal IN-list
        colname = col_expr.name
        src = _resolve_filter_column(model, colname, schema, index)
        filters.append(
            EnumFilter(
                model=model,
                column=colname,
                values=members,
                source_table=src[0] if src else None,
                source_column=src[1] if src else None,
            )
        )
    return filters


def _resolve_filter_column(
    model: str, colname: str, schema: BaselineSchema, index: LineageIndex
) -> SourceCol | None:
    """Best-effort: map a filtered column name to an enum-backed source column."""
    fp = index.column_footprint.get((model, colname))
    if fp:
        for table, column in fp:
            cdef = schema.column(table, column)
            if cdef and cdef.enum_type:
                return (table, column)
    return None

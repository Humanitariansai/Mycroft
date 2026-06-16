"""Parse Alembic migration files into structured schema changes.

This is a *static* parser: it reads the migration's source with the stdlib ``ast``
module and never imports or executes it. That matters -- the agent runs against
PRs from arbitrary authors, so executing migration code would be both unsafe and
impossible (the DB it targets isn't there).

Two entry points:

  * ``parse_migration(path)``      -> list[SchemaChange] from the upgrade() body.
  * ``load_baseline_schema(path)`` -> BaselineSchema from create_table() calls.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from .schema_model import (
    BaselineSchema,
    ChangeKind,
    ColumnDef,
    SchemaChange,
    TableDef,
)

# ALTER TYPE <name> ADD VALUE [IF NOT EXISTS] 'value'
_ENUM_ADD = re.compile(
    r"ALTER\s+TYPE\s+(\w+)\s+ADD\s+VALUE\s+(?:IF\s+NOT\s+EXISTS\s+)?'([^']+)'",
    re.IGNORECASE,
)

# Type constructor call names that are NOT the column's data type (skip when
# hunting for the type positional arg of sa.Column).
_NON_TYPE_CALLS = {"ForeignKey", "ForeignKeyConstraint", "UniqueConstraint",
                   "CheckConstraint", "PrimaryKeyConstraint", "Index"}


def _str_arg(node: ast.expr | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _func_name(call: ast.Call) -> str:
    """Return the trailing attribute of a call: op.add_column -> 'add_column'."""
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _enum_info(type_node: ast.expr | None) -> tuple[str | None, str | None]:
    """If a column type is a Postgres ENUM / sa.Enum, return (rendered, enum_name)."""
    if not isinstance(type_node, ast.Call):
        return (None, None)
    fname = _func_name(type_node)
    if not fname.upper().endswith("ENUM"):
        return (_render(type_node), None)
    enum_name = None
    for kw in type_node.keywords:
        if kw.arg == "name":
            enum_name = _str_arg(kw.value)
    return (_render(type_node), enum_name)


def _render(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - unparse is robust on real migrations
        return None


def _column_type_node(call: ast.Call) -> ast.expr | None:
    """The data-type positional arg of an sa.Column(...) call (after the name)."""
    for arg in call.args[1:]:
        if isinstance(arg, ast.Call) and _func_name(arg) in _NON_TYPE_CALLS:
            continue
        return arg
    return None


def _column_def_from_call(call: ast.Call) -> ColumnDef | None:
    """Build a ColumnDef from an sa.Column("name", <type>, ...) call."""
    name = _str_arg(call.args[0]) if call.args else None
    if name is None:
        return None
    rendered, enum_name = _enum_info(_column_type_node(call))
    return ColumnDef(name=name, type=rendered, enum_type=enum_name)


def _iter_op_calls(fn: ast.FunctionDef):
    """Yield every Call node under a function body (descends into with/if/for)."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            yield node


def parse_migration(path: str | Path) -> list[SchemaChange]:
    """Extract the structured changes from a migration's upgrade() function."""
    src = Path(path).read_text()
    tree = ast.parse(src)
    upgrade = _find_function(tree, "upgrade")
    if upgrade is None:
        return []

    changes: list[SchemaChange] = []
    for call in _iter_op_calls(upgrade):
        fname = _func_name(call)

        if fname == "add_column":
            table = _str_arg(call.args[0]) if call.args else None
            col = _column_def_from_call(call.args[1]) if len(call.args) > 1 else None
            if table and col:
                changes.append(
                    SchemaChange(
                        kind=ChangeKind.ADD_COLUMN,
                        table=table,
                        column=col.name,
                        new_type=col.type,
                        enum_type=col.enum_type,
                    )
                )

        elif fname == "drop_column":
            table = _str_arg(call.args[0]) if call.args else None
            col = _str_arg(call.args[1]) if len(call.args) > 1 else None
            if table and col:
                changes.append(
                    SchemaChange(kind=ChangeKind.DROP_COLUMN, table=table, column=col)
                )

        elif fname == "alter_column":
            table = _str_arg(call.args[0]) if call.args else None
            col = _str_arg(call.args[1]) if len(call.args) > 1 else None
            kw = {k.arg: k.value for k in call.keywords}
            if "new_column_name" in kw:
                changes.append(
                    SchemaChange(
                        kind=ChangeKind.RENAME_COLUMN,
                        table=table,
                        column=col,
                        new_column=_str_arg(kw["new_column_name"]),
                    )
                )
            if "type_" in kw:
                rendered, enum_name = _enum_info(kw["type_"])
                changes.append(
                    SchemaChange(
                        kind=ChangeKind.ALTER_TYPE,
                        table=table,
                        column=col,
                        new_type=rendered,
                        enum_type=enum_name,
                    )
                )
            if "nullable" in kw and isinstance(kw["nullable"], ast.Constant):
                changes.append(
                    SchemaChange(
                        kind=ChangeKind.ALTER_NULLABILITY,
                        table=table,
                        column=col,
                        nullable=bool(kw["nullable"].value),
                    )
                )

        elif fname == "execute":
            sql = _str_arg(call.args[0]) if call.args else None
            if not sql:
                continue
            m = _ENUM_ADD.search(sql)
            if m:
                changes.append(
                    SchemaChange(
                        kind=ChangeKind.ENUM_ADD_VALUE,
                        enum_type=m.group(1),
                        enum_value=m.group(2),
                    )
                )
            else:
                changes.append(SchemaChange(kind=ChangeKind.RAW_SQL, raw_sql=sql))

    return changes


def load_baseline_schema(path: str | Path) -> BaselineSchema:
    """Reconstruct the table/column schema from a migration's create_table calls."""
    src = Path(path).read_text()
    tree = ast.parse(src)
    upgrade = _find_function(tree, "upgrade")
    schema = BaselineSchema()
    if upgrade is None:
        return schema

    for call in _iter_op_calls(upgrade):
        if _func_name(call) != "create_table":
            continue
        table_name = _str_arg(call.args[0]) if call.args else None
        if not table_name:
            continue
        table = TableDef(name=table_name)
        for arg in call.args[1:]:
            if isinstance(arg, ast.Call) and _func_name(arg) == "Column":
                col = _column_def_from_call(arg)
                if col:
                    table.columns[col.name] = col
        schema.tables[table_name] = table

    return schema

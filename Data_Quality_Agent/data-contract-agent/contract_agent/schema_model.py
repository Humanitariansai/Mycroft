"""Shared data structures for the deterministic layer.

These are deliberately plain dataclasses with no behaviour beyond a couple of
lookups. The parser produces them; the lineage and impact layers consume them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ChangeKind(StrEnum):
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    RENAME_COLUMN = "rename_column"
    ALTER_TYPE = "alter_type"
    ALTER_NULLABILITY = "alter_nullability"
    ENUM_ADD_VALUE = "enum_add_value"
    RAW_SQL = "raw_sql"


@dataclass
class SchemaChange:
    """One structured change extracted from a migration's upgrade()."""

    kind: ChangeKind
    table: str | None = None
    column: str | None = None
    new_column: str | None = None  # rename target
    new_type: str | None = None  # add_column / alter_type
    enum_type: str | None = None  # enum_add_value
    enum_value: str | None = None  # enum_add_value
    nullable: bool | None = None  # alter_nullability / add_column
    raw_sql: str | None = None  # raw_sql (backfills etc.)

    def describe(self) -> str:
        k = self.kind
        if k is ChangeKind.RENAME_COLUMN:
            return f"rename {self.table}.{self.column} -> {self.new_column}"
        if k is ChangeKind.ADD_COLUMN:
            return f"add {self.table}.{self.column} ({self.new_type})"
        if k is ChangeKind.DROP_COLUMN:
            return f"drop {self.table}.{self.column}"
        if k is ChangeKind.ALTER_TYPE:
            return f"retype {self.table}.{self.column} -> {self.new_type}"
        if k is ChangeKind.ALTER_NULLABILITY:
            return f"set {self.table}.{self.column} nullable={self.nullable}"
        if k is ChangeKind.ENUM_ADD_VALUE:
            return f"enum {self.enum_type} += '{self.enum_value}'"
        if k is ChangeKind.RAW_SQL:
            return f"raw sql: {(self.raw_sql or '').strip()[:80]}"
        return k.value


@dataclass
class ColumnDef:
    name: str
    type: str | None = None
    enum_type: str | None = None  # set when this column is backed by a Postgres ENUM


@dataclass
class TableDef:
    name: str
    columns: dict[str, ColumnDef] = field(default_factory=dict)


@dataclass
class BaselineSchema:
    """The operational schema as of the baseline migration (0001_initial)."""

    tables: dict[str, TableDef] = field(default_factory=dict)

    def column(self, table: str, column: str) -> ColumnDef | None:
        t = self.tables.get(table)
        return t.columns.get(column) if t else None

    def columns_for_enum(self, enum_type: str) -> list[tuple[str, str]]:
        """Every (table, column) backed by the given Postgres ENUM type."""
        out: list[tuple[str, str]] = []
        for t in self.tables.values():
            for c in t.columns.values():
                if c.enum_type == enum_type:
                    out.append((t.name, c.name))
        return out

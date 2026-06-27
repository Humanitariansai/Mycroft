"""Deterministic layer of the data contract agent.

Three components, mirroring the project plan:

  * migration_parser -- AST parse of Alembic migrations into structured schema changes.
  * lineage          -- column-level lineage reconstructed from a dbt manifest via sqlglot.
  * impact           -- joins the two to report which analytics models a change affects.

No LLM, no network. Everything here is mechanical and reproducible.
"""

__version__ = "0.1.0"

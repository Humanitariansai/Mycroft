from pathlib import Path

import pytest

from contract_agent.lineage import build_lineage
from contract_agent.migration_parser import load_baseline_schema

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
MIGRATIONS = FIXTURES / "migrations"
MANIFEST = FIXTURES / "manifest.json"
BASELINE = MIGRATIONS / "0001_initial.py"


@pytest.fixture(scope="session")
def schema():
    return load_baseline_schema(BASELINE)


@pytest.fixture(scope="session")
def index(schema):
    return build_lineage(MANIFEST, schema)

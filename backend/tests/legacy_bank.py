"""Explicit historical definitions for migration and immutable-version tests."""
import json
from copy import deepcopy
from pathlib import Path
from app.benchmark import import_pack as import_current_pack
from app.config import ROOT_DIR


def import_pack(db, admin, runner, pack=None, **options):
    pack = deepcopy(pack) if pack is not None else json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    definitions = json.loads((Path(__file__).parent / "fixtures/legacy_assessment_definitions.json").read_text(encoding="utf-8"))
    key = pack.get("scope")
    if key not in definitions and any(c.get("concept_code") == "SQL-DML-KNOW" for c in pack["concepts"]):
        key = "sql_knowledge_pack.json"
    pack["assessments"] = definitions.get(key, [])
    return import_current_pack(db, admin, runner, pack, **options)

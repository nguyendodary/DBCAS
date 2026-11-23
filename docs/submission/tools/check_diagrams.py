# -*- coding: utf-8 -*-
"""Consistency checks for the generated 67-card TRD/ERD continuation pages."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_style import LEGEND_COUNTS  # noqa: E402


def check(spec_path, schema_path):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    problems = []
    expected = {"tables": 67, "columns": 561, "foreign_keys": 122, "migrations": 28,
                "pages_total": 11}
    for key, value in expected.items():
        if spec["counts"].get(key) != value:
            problems.append(f"{key}: {spec['counts'].get(key)} != {value}")
    names = [n for page in spec["original_pages"] + spec["continuation_pages"] for n in page]
    if len(names) != len(set(names)):
        problems.append("duplicate table card")
    if set(names) != {t["table"] for t in schema["tables"]}:
        problems.append("card set differs from schema")
    if spec.get("legend") != LEGEND_COUNTS:
        problems.append(f"legend mismatch: {spec.get('legend')!r}")
    if len(spec["continuation_pages"]) != 6:
        problems.append("expected six continuation pages")
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spec", default=str(Path(__file__).with_name("out") / "trd67" / "trd-spec-67.json"))
    ap.add_argument("--schema", default=str(ROOT / "docs/diagrams/schema-028/schema-introspection.json"))
    args = ap.parse_args(argv)
    problems = check(args.spec, args.schema)
    stale = ROOT / "docs/diagrams/rebuild/trd/spec.json"
    if stale.exists():
        old = json.loads(stale.read_text(encoding="utf-8"))
        if old.get("counts", {}).get("tables") == 41:
            print("NOTE: docs/diagrams/rebuild/trd/spec.json still records the frozen 41-card set; "
                  "trd67.py is the superseding generator for the 67-card continuation.")
    if problems:
        raise SystemExit("\n".join(problems))
    print("PASS: 67 tables, 561 columns, 122 FKs, 28 migrations, 11 pages, unique cards")
    return 0


if __name__ == "__main__":
    sys.exit(main())

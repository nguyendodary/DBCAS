#!/usr/bin/env python3
"""Validate and apply db/concept_metadata.json to the concept table.

Only description, keywords and learning_objectives are written. Concept ids,
codes, names, subject areas, difficulty levels, SQL features, prerequisite
edges and CLO mappings are verified unchanged and never modified.

Dry run (default):
  backend/.venv/Scripts/python.exe db/apply_concept_metadata.py

Apply:
  backend/.venv/Scripts/python.exe db/apply_concept_metadata.py --apply \
      --report _review/continuation-20261027/concept-metadata-report.json
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

import psycopg  # noqa: E402

from app.config import Settings  # noqa: E402

METADATA = ROOT / "db/concept_metadata.json"
FIELDS = ("description", "keywords", "learning_objectives")
PRESERVED = ("concept_id", "concept_code", "concept_name", "subject_area", "difficulty_level", "sql_feature")


def load_metadata():
    payload = json.loads(METADATA.read_text(encoding="utf-8"))
    concepts = payload["concepts"]
    errors = []
    objective_owner = {}
    for code, item in concepts.items():
        description = item.get("description")
        if not isinstance(description, str) or len(description.strip()) < 20:
            errors.append(f"{code}: description must be at least 20 characters")
        keywords = item.get("keywords")
        if not isinstance(keywords, list) or not 3 <= len(keywords) <= 30:
            errors.append(f"{code}: keywords must contain 3-30 entries")
        elif any(not isinstance(k, str) or not k.strip() or len(k) > 100 for k in keywords):
            errors.append(f"{code}: keyword empty, non-string or longer than 100 characters")
        elif len(set(keywords)) != len(keywords):
            errors.append(f"{code}: duplicate keyword")
        objectives = item.get("learning_objectives")
        if not isinstance(objectives, list) or not 3 <= len(objectives) <= 20:
            errors.append(f"{code}: learning objectives must contain 3-20 entries")
        elif any(not isinstance(o, str) or not o.strip() or len(o) > 1000 for o in objectives):
            errors.append(f"{code}: objective empty, non-string or longer than 1000 characters")
        else:
            for objective in objectives:
                if objective in objective_owner:
                    errors.append(f"{code}: objective duplicated from {objective_owner[objective]}")
                objective_owner[objective] = code
            if len(set(objectives)) != len(objectives):
                errors.append(f"{code}: duplicate learning objective")
        for value in (description, *keywords, *objectives):
            if isinstance(value, str) and any(ord(ch) < 32 and ch not in "\n\t" for ch in value):
                errors.append(f"{code}: control character in metadata")
    return payload, errors


def snapshot(db):
    cur = db.execute(
        "SELECT concept_id, concept_code, concept_name, subject_area, difficulty_level, "
        "sql_feature, description, keywords, learning_objectives FROM concept ORDER BY concept_id"
    )
    rows = cur.fetchall()
    concepts = [dict(zip([d.name for d in cur.description], row)) for row in rows]
    deps = db.execute("SELECT concept_id, prerequisite_concept_id FROM concept_dependency ORDER BY 1, 2").fetchall()
    clos = db.execute("SELECT clo_id, concept_id, mapping_source, status FROM clo_concept ORDER BY 1, 2").fetchall()
    refs = {}
    for table in ("question_concept", "assessment_concept", "concept_competency", "competency_gap", "question_candidate"):
        refs[table] = db.execute(f"SELECT count(*) FROM {table} WHERE concept_id IS NOT NULL").fetchone()[0]
    return {
        "concepts": concepts,
        "dependencies": [list(row) for row in deps],
        "clo_mappings": [list(row) for row in clos],
        "reference_counts": refs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    payload, errors = load_metadata()
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(" -", error)
        return 1

    settings = Settings()
    dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(dsn) as conn:
        identity = conn.execute(
            "SELECT current_database(), (pg_control_system()).system_identifier::text, "
            "current_setting('server_version')"
        ).fetchone()
        if identity[0] != "dbcas":
            print(f"REFUSED: target database is {identity[0]!r}, expected 'dbcas'")
            return 2
        before = snapshot(conn)
        by_code = {row["concept_code"]: row for row in before["concepts"]}
        expected = set(payload["concepts"])
        missing = sorted(expected - set(by_code))
        extra = sorted(set(by_code) - expected)
        if missing or extra:
            print(f"REFUSED: metadata/DB concept mismatch missing={missing} extra={extra}")
            return 2

        changes = []
        for code, item in payload["concepts"].items():
            current = by_code[code]
            change = {"concept_code": code, "concept_id": current["concept_id"]}
            for field in FIELDS:
                new_value = item[field]
                old_value = current[field]
                if field == "description":
                    new_value = new_value.strip()
                if old_value != new_value:
                    change[f"{field}_before"] = old_value
                    change[f"{field}_after"] = new_value
            if len(change) > 2:
                changes.append(change)
                if args.apply:
                    item = payload["concepts"][code]
                    conn.execute(
                        "UPDATE concept SET description = %s, keywords = %s, "
                        "learning_objectives = %s WHERE concept_code = %s",
                        (item["description"].strip(), item["keywords"],
                         item["learning_objectives"], code),
                    )
        if args.apply:
            conn.commit()
        after = snapshot(conn)

    before_by_code = {row["concept_code"]: row for row in before["concepts"]}
    after_by_code = {row["concept_code"]: row for row in after["concepts"]}
    preserved_ok = True
    for code in expected:
        for field in PRESERVED:
            if before_by_code[code][field] != after_by_code[code][field]:
                preserved_ok = False
    preserved_ok = preserved_ok and before["dependencies"] == after["dependencies"]
    preserved_ok = preserved_ok and before["clo_mappings"] == after["clo_mappings"]
    preserved_ok = preserved_ok and before["reference_counts"] == after["reference_counts"]

    effective = []
    for row in after["concepts"]:
        item = payload["concepts"][row["concept_code"]]
        effective.append({**row,
                          "description": item["description"].strip(),
                          "keywords": item["keywords"],
                          "learning_objectives": item["learning_objectives"]})
    if args.apply:
        for row in after["concepts"]:
            matches = payload["concepts"][row["concept_code"]]
            if (row["description"] != matches["description"].strip()
                    or row["keywords"] != matches["keywords"]
                    or row["learning_objectives"] != matches["learning_objectives"]):
                preserved_ok = False

    validation = {
        "concept_count": len(effective),
        "all_descriptions_present": all(
            isinstance(row["description"], str) and row["description"].strip()
            for row in effective),
        "all_keywords_present": all(row["keywords"] for row in effective),
        "all_objectives_present": all(row["learning_objectives"] for row in effective),
        "objective_global_uniqueness": True,
        "preserved_concept_identity_and_relations": preserved_ok,
    }
    seen = {}
    for row in effective:
        for objective in row["learning_objectives"]:
            if objective in seen:
                validation["objective_global_uniqueness"] = False
            seen[objective] = row["concept_code"]
    validation["objective_total"] = len(seen)
    validation["keyword_total"] = sum(len(row["keywords"]) for row in effective)
    validation["all_valid"] = all(
        validation[key] for key in (
            "all_descriptions_present", "all_keywords_present", "all_objectives_present",
            "objective_global_uniqueness", "preserved_concept_identity_and_relations"))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metadata_file": str(METADATA.relative_to(ROOT)),
        "database": {"name": identity[0], "system_identifier": identity[1], "server_version": identity[2]},
        "applied": bool(args.apply),
        "summary": {
            "concepts": len(after["concepts"]),
            "changed_records": len(changes),
            "descriptions_added": sum(1 for c in changes if "description_after" in c and c.get("description_before") in (None, "")),
            "descriptions_replaced": sum(1 for c in changes if "description_after" in c and c.get("description_before") not in (None, "")),
            "keywords_added": sum(1 for c in changes if "keywords_after" in c),
            "objectives_added": sum(1 for c in changes if "learning_objectives_after" in c),
        },
        "validation": validation,
        "preserved": {
            "concept_ids": True,
            "concept_codes": True,
            "names_subject_areas_difficulty_sql_features": preserved_ok,
            "prerequisite_edges": len(after["dependencies"]),
            "clo_mappings": len(after["clo_mappings"]),
            "reference_counts": after["reference_counts"],
        },
        "changes": changes,
        "final_records": [
            {key: row[key] for key in (*PRESERVED, *FIELDS)}
            for row in after["concepts"]
        ],
    }
    if args.report:
        destination = Path(args.report)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"report: {destination}")
    print(json.dumps(report["summary"], indent=2))
    print("validation:", json.dumps(validation))
    print("APPLIED" if args.apply else "DRY RUN — no changes written")
    return 0 if validation["all_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""Build an authoring plan from real assessment scopes.

Unlike the first coverage pass, this keeps (assessment, subject area) units
separate when two assessments reuse the same area label for different
concept sets. Units with identical concept sets are merged because one new
question can serve both.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import psycopg

BANDS = {"EASY": (1, 2), "MEDIUM": (3, 3), "HARD": (4, 5)}
CLONE_URL = "postgresql://dbcas:clone_only_pw@127.0.0.1:5547/dbcas_clone"
OUT = Path("_content/expansion-20261024/evidence/expansion_plan.json")


def main() -> None:
    with psycopg.connect(CLONE_URL) as conn:
        assessments = {
            row[0]: row
            for row in conn.execute(
                "select assessment_id, title, max_questions, target_mcq, target_sql, "
                "target_essay from assessment where assessment_id in (2,3,4,6)"
            )
        }
        targets = conn.execute(
            """
            select ac.assessment_id, ac.concept_id, c.concept_code,
                   c.concept_name, c.subject_area
            from assessment_concept ac
            join concept c on c.concept_id = ac.concept_id
            where ac.assessment_id in (2,3,4,6)
              and c.subject_area <> 'E2E Verification'
            order by ac.assessment_id, c.subject_area, c.concept_code
            """
        ).fetchall()
        rows = conn.execute(
            """
            select q.question_id, q.family_id, q.question_type, q.difficulty_level,
                   c.concept_id, c.concept_code, c.subject_area
            from question q
            join question_concept qc on qc.question_id = q.question_id and qc.confirmed
            join concept c on c.concept_id = qc.concept_id
            where q.status = 'validated' and c.subject_area <> 'E2E Verification'
            """
        ).fetchall()

    units = defaultdict(lambda: {"concepts": {}, "assessments": []})
    for aid, cid, code, name, area in targets:
        unit = units[(area, tuple(sorted(
            t[1] for t in targets if t[0] == aid and t[4] == area
        )))]
        unit["concepts"][cid] = {"code": code, "name": name}
        unit["assessments"].append(aid)

    plan = []
    merged = {}
    for (area, concept_tuple), unit in sorted(units.items()):
        concept_ids = set(concept_tuple)
        quotas = {"mcq": 0, "sql": 0, "essay": 0}
        for aid in unit["assessments"]:
            _, _, max_q, t_mcq, t_sql, t_essay = assessments[aid]
            extra = max_q - (t_mcq + t_sql + t_essay)
            quotas["mcq"] = max(quotas["mcq"], t_mcq + extra)
            quotas["sql"] = max(quotas["sql"], t_sql)
            quotas["essay"] = max(quotas["essay"], t_essay)
        bands = {}
        for band, (low, high) in BANDS.items():
            eligible = [
                r for r in rows if low <= r[3] <= high and r[4] in concept_ids
            ]
            families = defaultdict(set)
            concept_families = defaultdict(set)
            for qid, family_id, qtype, difficulty, cid, code, _ in eligible:
                family = family_id or qid
                families[qtype].add(family)
                concept_families[code].add(family)
            deficits = {k: max(0, quotas[k] - len(families[k])) for k in quotas}
            missing = sorted(
                meta["code"] for cid, meta in unit["concepts"].items()
                if not concept_families.get(meta["code"])
            )
            weak = sorted(
                (
                    {"code": meta["code"], "families": len(concept_families.get(meta["code"], ()))}
                    for meta in unit["concepts"].values()
                    if 0 < len(concept_families.get(meta["code"], ())) < 3
                ),
                key=lambda item: item["code"],
            )
            bands[band] = {
                "eligible_families": {k: len(v) for k, v in sorted(families.items())},
                "deficits": deficits,
                "missing_concepts": missing,
                "weak_concepts": weak,
            }
        signature = tuple(sorted(concept_ids))
        entry = {
            "area": area,
            "concept_codes": [unit["concepts"][cid]["code"] for cid in sorted(concept_ids)],
            "assessments": sorted(set(unit["assessments"])),
            "quotas": quotas,
            "bands": bands,
        }
        plan.append(entry)
        merged.setdefault(signature, []).append(entry)

    summary = {"units": len(plan), "bands": {}, "merged_groups": []}
    totals = {"mcq": 0, "sql": 0, "essay": 0}
    for signature, group in merged.items():
        for band in BANDS:
            need = {"mcq": 0, "sql": 0, "essay": 0}
            for entry in group:
                for kind, value in entry["bands"][band]["deficits"].items():
                    need[kind] = max(need[kind], value)
            if any(need.values()):
                totals = {k: totals[k] + need[k] for k in totals}
                summary["bands"].setdefault(band, 0)
                summary["bands"][band] += sum(need.values())
                summary["merged_groups"].append(
                    {
                        "area": group[0]["area"],
                        "concept_codes": group[0]["concept_codes"],
                        "assessments": sorted({a for e in group for a in e["assessments"]}),
                        "band": band,
                        "need": need,
                    }
                )
    summary["total_new_items_conservative"] = sum(totals.values())
    summary["by_type"] = totals
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"summary": summary, "units": plan}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

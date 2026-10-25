"""Measure expansion needs against the real assembly rules.

Two distinct readiness questions are reported:

1. Area x band FORMAL readiness: a learner selects every concept of one
   subject area offered by an assessment. The engine needs the assessment's
   exact type quotas and must cover every selected concept.
2. Concept x band PRACTICE readiness: how many distinct version families
   exist for a single skill. The UI's automatic practice length is
   min(13, max_questions, max(3, requested_concepts), families), so three
   families are needed for a full three-question practice.

Only validated questions with confirmed concept tags are counted, matching
adaptive_engine._eligible_pool.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import psycopg

BANDS = {"EASY": (1, 2), "MEDIUM": (3, 3), "HARD": (4, 5)}
CLONE_URL = os.environ.get(
    "DBCAS_COVERAGE_URL",
    "postgresql://dbcas:clone_only_pw@127.0.0.1:5547/dbcas_clone",
)


def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "_content/expansion-20261024/evidence/coverage_after_pilot.json"
    )
    with psycopg.connect(CLONE_URL) as conn:
        assessments = conn.execute(
            """
            select assessment_id, title, status, max_questions,
                   target_mcq, target_sql, target_essay
            from assessment
            where assessment_id in (2, 3, 4, 6)
            order by assessment_id
            """
        ).fetchall()
        targets = conn.execute(
            """
            select ac.assessment_id, ac.concept_id, c.concept_code,
                   c.concept_name, c.subject_area,
                   ac.min_difficulty, ac.max_difficulty
            from assessment_concept ac
            join concept c on c.concept_id = ac.concept_id
            where ac.assessment_id in (2, 3, 4, 6)
              and c.subject_area <> 'E2E Verification'
            order by ac.assessment_id, c.subject_area, c.concept_code
            """
        ).fetchall()
        blueprints = {}
        for assessment_id, area, band, mcq, sql, essay, version in conn.execute(
            """
            select assessment_id, subject_area, difficulty_band,
                   target_mcq, target_sql, target_essay, version_no
            from (
              select b.*, row_number() over (
                partition by assessment_id, subject_area, difficulty_band
                order by version_no desc) rn
              from assessment_blueprint b
              where status = 'approved'
            ) latest
            where rn = 1
            """
        ):
            blueprints[(assessment_id, area, band)] = {
                "mcq": mcq, "sql": sql, "essay": essay, "version_no": version}
        rows = conn.execute(
            """
            select q.question_id, q.family_id, q.question_type,
                   q.difficulty_level, c.concept_id, c.concept_code,
                   c.subject_area
            from question q
            join question_concept qc
              on qc.question_id = q.question_id and qc.confirmed
            join concept c on c.concept_id = qc.concept_id
            where q.status = 'validated'
              and c.subject_area <> 'E2E Verification'
            """
        ).fetchall()

    by_assessment = defaultdict(list)
    for t in targets:
        by_assessment[t[0]].append(t)

    report = {
        "assessments": {},
        "concept_practice": {},
        "totals": defaultdict(int),
    }

    for assessment_id, title, status, max_questions, t_mcq, t_sql, t_essay in assessments:
        extra_mcq = max_questions - (t_mcq + t_sql + t_essay)
        quotas = {"mcq": t_mcq + extra_mcq, "sql": t_sql, "essay": t_essay}
        scope = by_assessment[assessment_id]
        areas = defaultdict(list)
        for t in scope:
            areas[t[4]].append(t)
        assessment_report = {"title": title, "status": status,
                             "legacy_quotas": quotas, "areas": {}}
        for area, concepts in sorted(areas.items()):
            in_area = {c[1] for c in concepts}
            area_report = {}
            for band, (low, high) in BANDS.items():
                eligible = [
                    r for r in rows
                    if r[3] >= low and r[3] <= high and r[4] in in_area
                ]
                families = defaultdict(set)
                concept_families = defaultdict(set)
                for qid, family_id, qtype, difficulty, concept_id, code, area_name in eligible:
                    family = family_id or qid
                    families[qtype].add(family)
                    concept_families[code].add(family)
                blueprint = blueprints.get((assessment_id, area, band))
                cell_quotas = blueprint or quotas
                deficits = {
                    kind: max(0, cell_quotas[kind] - len(families[kind]))
                    for kind in ("mcq", "sql", "essay")
                }
                missing_concepts = sorted(
                    t[2] for t in concepts if not concept_families.get(t[2])
                )
                weak_concepts = sorted(
                    (
                        {"code": t[2], "families": len(concept_families[t[2]])}
                        for t in concepts
                        if 0 < len(concept_families.get(t[2], ())) < 3
                    ),
                    key=lambda item: item["code"],
                )
                area_report[band] = {
                    "families": {k: len(v) for k, v in sorted(families.items())},
                    "quotas": dict(cell_quotas),
                    "blueprint": blueprint,
                    "deficits": deficits,
                    "missing_concepts": missing_concepts,
                    "weak_concepts": weak_concepts,
                }
                for kind, value in deficits.items():
                    report["totals"][f"{kind}_deficit_cells"] += 1 if value else 0
                    report["totals"][f"{kind}_deficit_items"] += value
            assessment_report["areas"][area] = area_report
        report["assessments"][str(assessment_id)] = assessment_report

    concept_ids = {}
    with psycopg.connect(CLONE_URL) as conn:
        for concept_id, code, area in conn.execute(
            "select concept_id, concept_code, subject_area from concept "
            "where subject_area <> 'E2E Verification' order by concept_code"
        ):
            concept_ids[code] = (concept_id, area)
    for code, (concept_id, area) in sorted(concept_ids.items()):
        bands = {}
        for band, (low, high) in BANDS.items():
            families = {
                (r[1] or r[0])
                for r in rows
                if r[4] == concept_id and low <= r[3] <= high
            }
            bands[band] = len(families)
        report["concept_practice"][code] = {"area": area, "families": bands}

    report["totals"]["concepts_under_3_in_any_band"] = sum(
        1 for item in report["concept_practice"].values()
        if any(count < 3 for count in item["families"].values())
    )
    report["totals"] = dict(report["totals"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, default=list), encoding="utf-8")
    print(json.dumps(report["totals"], indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

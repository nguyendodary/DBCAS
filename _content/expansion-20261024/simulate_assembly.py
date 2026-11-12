"""Exercise the real assembly selectors against staged clone inventory.

No sessions are created and nothing is written: the script builds the same
eligible pool as ``start_session`` and calls ``select_questions`` /
``select_practice_questions`` directly, five times per selection to expose
random-order failures. Coverage and exact type quotas are checked on every
successful plan.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db import get_session_factory
from app.errors import AppError
from app.models import Assessment, AssessmentConcept, Concept
from app.repositories import AssessmentRepository
from app.services import adaptive_engine
from app.services.blueprints import (
    DIFFICULTY_BANDS,
    quotas_for,
    resolve_blueprint,
)
from app.services.personalized_assessment import (
    select_practice_questions,
    select_questions,
)

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    Path(__file__).resolve().parent / "evidence" / "assembly_simulation.json"
)
ASSESSMENT_IDS = (2, 3, 4, 6)
RUNS = 5


def _targets(assessment, area, band):
    low, high = DIFFICULTY_BANDS[band]
    result = []
    for target in assessment.targets:
        if target.concept.subject_area != area:
            continue
        minimum = max(low, target.min_difficulty)
        maximum = min(high, target.max_difficulty)
        if minimum <= maximum:
            result.append(SimpleNamespace(
                concept_id=target.concept_id,
                min_difficulty=minimum,
                max_difficulty=maximum,
            ))
    return result


def _families(pool):
    return {q.family_id or q.question_id for q, _ in pool}


def _check(chosen, concept_ids, quotas):
    covered = set()
    types = Counter()
    families = set()
    for q in chosen:
        types[q.question_type] += 1
        families.add(q.family_id or q.question_id)
        covered.update(
            tag.concept_id for tag in q.concept_tags
            if tag.confirmed and tag.concept_id in concept_ids
        )
    return {
        "covered": covered == set(concept_ids),
        "types": dict(types),
        "types_exact": all(types[kind] == count for kind, count in quotas.items()),
        "families_distinct": len(families) == len(chosen),
    }


def main() -> None:
    get_settings()
    db = get_session_factory()()
    try:
        assessments = db.scalars(
            select(Assessment)
            .where(Assessment.assessment_id.in_(ASSESSMENT_IDS))
            .options(
                selectinload(Assessment.targets).selectinload(AssessmentConcept.concept)
            )
            .order_by(Assessment.assessment_id)
        ).all()
        repo = AssessmentRepository(db)
        report = {"assessments": {}, "single_concept": {}}
        for assessment in assessments:
            extra = assessment.max_questions - (
                assessment.target_mcq + assessment.target_sql + assessment.target_essay
            )
            legacy_quotas = {
                "mcq": assessment.target_mcq + extra,
                "sql": assessment.target_sql,
                "essay": assessment.target_essay,
            }
            areas = {}
            for target in assessment.targets:
                areas.setdefault(target.concept.subject_area, []).append(target)
            output_areas = {}
            for area, members in sorted(areas.items()):
                if area == "E2E Verification":
                    continue
                band_results = {}
                for band in DIFFICULTY_BANDS:
                    targets = _targets(assessment, area, band)
                    if not targets:
                        continue
                    concept_ids = {t.concept_id for t in targets}
                    codes = sorted({
                        target.concept.concept_code
                        for target in members
                        if target.concept_id in concept_ids
                    })
                    pool = adaptive_engine._eligible_pool(
                        SimpleNamespace(targets=targets), set(), repo
                    )
                    families = _families(pool)
                    try:
                        blueprint, resolution = resolve_blueprint(
                            db, assessment, concept_ids, band)
                    except AppError as exc:
                        blueprint, resolution = None, {
                            "mode": "error", "code": exc.code,
                            "details": exc.details}
                    quotas = quotas_for(blueprint) if blueprint is not None else legacy_quotas
                    attempts = []
                    for _ in range(RUNS):
                        try:
                            chosen = select_questions(pool, concept_ids, quotas)
                        except AppError as exc:
                            attempts.append({"ok": False, "code": exc.code})
                            continue
                        attempts.append({"ok": True, **_check(chosen, concept_ids, quotas)})
                    practice_count = min(
                        13, assessment.max_questions, max(3, len(concept_ids)), len(families)
                    )
                    practice = {"count": practice_count, "runs": []}
                    if practice_count:
                        for _ in range(RUNS):
                            try:
                                chosen, used = select_practice_questions(
                                    pool, concept_ids, practice_count
                                )
                            except AppError as exc:
                                practice["runs"].append({"ok": False, "code": exc.code})
                                continue
                            practice["runs"].append({
                                "ok": True, "quotas": used,
                                **_check(chosen, concept_ids, used),
                            })
                    band_results[band] = {
                        "concept_codes": codes,
                        "concept_count": len(concept_ids),
                        "families": len(families),
                        "families_by_type": dict(Counter(q.question_type for q, _ in pool)),
                        "formal_quota": quotas,
                        "blueprint": resolution,
                        "blueprint_version": (
                            blueprint.version_no if blueprint is not None else None),
                        "formal_runs": attempts,
                        "formal_ready": len(attempts) == RUNS and all(
                            run.get("ok") and run.get("covered") and run.get("types_exact")
                            for run in attempts
                        ),
                        "practice": practice,
                        "practice_ready": bool(practice["runs"]) and all(
                            run.get("ok") and run.get("covered") for run in practice["runs"]
                        ),
                    }
                if band_results:
                    output_areas[area] = band_results
            report["assessments"][str(assessment.assessment_id)] = {
                "title": assessment.title,
                "legacy_quotas": legacy_quotas,
                "areas": output_areas,
            }

        concept_rows = db.execute(
            select(AssessmentConcept.assessment_id, Concept.concept_id, Concept.concept_code)
            .join(Concept, AssessmentConcept.concept_id == Concept.concept_id)
            .where(AssessmentConcept.assessment_id.in_(ASSESSMENT_IDS))
            .distinct()
        ).all()
        for assessment_id, concept_id, code in concept_rows:
            for band in DIFFICULTY_BANDS:
                low, high = DIFFICULTY_BANDS[band]
                target = SimpleNamespace(concept_id=concept_id, min_difficulty=low, max_difficulty=high)
                pool = adaptive_engine._eligible_pool(SimpleNamespace(targets=[target]), set(), repo)
                families = len(_families(pool))
                report["single_concept"].setdefault(str(assessment_id), {}).setdefault(code, {})[band] = {
                    "families": families,
                    "practice_ready": families >= 3,
                }
        OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote {OUT}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

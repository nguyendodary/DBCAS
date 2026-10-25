"""Competency-aligned, versioned formal assessment blueprints.

The published assessment configuration remains the compatibility contract for
custom, historical and mixed-area selections. A single subject-area selection
on an assessment with approved blueprints binds to the latest approved version
for that area and difficulty band. Blueprint rows are immutable; a policy
change appends a new version and never rewrites a session snapshot.
"""
from collections import Counter

from sqlalchemy import func, select

from ..errors import AppError
from ..models import AssessmentBlueprint
from ..repositories import SecurityRepository

DIFFICULTY_BANDS = {"EASY": (1, 2), "MEDIUM": (3, 3), "HARD": (4, 5)}

# Competencies whose evidence is conceptual reasoning, diagnosis and structured
# written analysis. The read-only sandbox cannot honestly execute EXPLAIN,
# index DDL, configuration, backup, transaction-control or server-programming
# statements, so no SQL practical is scheduled for them.
THEORY_AREAS = {
    "Performance",
    "PostgreSQL Administration",
    "PostgreSQL Concurrency",
    "PostgreSQL Performance",
    "PostgreSQL Security",
    "PostgreSQL Server Programming",
}

# Executable SQL here audits schema/functional-dependency facts rather than
# measuring index tuning or query-plan execution.
DESIGN_AUDIT_AREAS = {"Database Design"}

# Executable SQL here queries the observable semantics of DDL/DML application;
# the learner never executes the DDL/DML itself in the sandbox.
SEMANTICS_AREAS = {
    "SQL Foundations",
    "PostgreSQL Data Definition",
    "PostgreSQL Data Manipulation",
}

_AREA_EVIDENCE = {
    "Performance": ["mcq_conceptual", "query_plan_and_index_reasoning", "structured_written"],
    "PostgreSQL Performance": ["mcq_conceptual", "query_plan_and_index_reasoning", "structured_written"],
    "PostgreSQL Administration": ["mcq_configuration_and_risk", "backup_monitoring_case", "structured_written"],
    "PostgreSQL Concurrency": ["mcq_schedule_and_anomaly", "lock_and_deadlock_explanation", "structured_written"],
    "PostgreSQL Security": ["mcq_privilege_and_rls", "attack_prevention_scenario", "structured_written"],
    "PostgreSQL Server Programming": ["mcq_function_and_trigger_behavior", "server_program_design_analysis", "structured_written"],
}

_SCORING = {
    "aggregation": "points_weighted",
    "question_points": {"mcq": "1.00", "sql": "5.00", "essay": "5.00"},
    "normalization": "points_earned / points_possible * 100",
    "rounding": "HALF_UP",
    "scale": 100,
    "competency": "per_selected_concept",
    "grading": {
        "mcq": "deterministic",
        "sql": "sandbox_expected_result",
        "essay": "four_band_rubric_with_ai_assist_and_human_review",
    },
}


def desired_mix(assessment, subject_area):
    """System-managed competency mix for one assessment area."""
    total = int(assessment.max_questions)
    if subject_area in THEORY_AREAS:
        essay = min(3, max(2, round(total / 4)))
        return {"mcq": total - essay, "sql": 0, "essay": essay}
    sql = int(assessment.target_sql)
    essay = int(assessment.target_essay)
    mcq = total - sql - essay
    if mcq < 0:
        raise AppError(422, "invalid_blueprint_default",
                       "Assessment configuration cannot produce a non-negative MCQ quota")
    return {"mcq": mcq, "sql": sql, "essay": essay}


def evidence_types(subject_area, mix):
    if mix["sql"] == 0:
        return list(_AREA_EVIDENCE.get(subject_area, ["mcq_conceptual", "structured_written"]))
    if subject_area in DESIGN_AUDIT_AREAS:
        return ["mcq_conceptual", "schema_fd_audit_sql", "structured_written"]
    if subject_area in SEMANTICS_AREAS:
        return ["mcq_conceptual", "read_only_semantics_sql", "structured_written"]
    return ["mcq_conceptual", "executable_sql_practical", "structured_written"]


def _approval_basis(subject_area, mix):
    if mix["sql"] == 0:
        return (
            "Curriculum design: this competency is evidenced by conceptual judgement, "
            "diagnosis and rubric-scored written analysis. A read-only SELECT sandbox "
            "cannot execute the statements the competency describes, so executable SQL "
            "is deliberately not scheduled rather than mislabelled."
        )
    if subject_area in DESIGN_AUDIT_AREAS:
        return (
            "Curriculum design: schema and functional-dependency reasoning are measured "
            "by MCQ and written analysis; the scheduled read-only SQL audits constraints "
            "and dependency violations in the fixture rather than pretending to measure "
            "tuning or DDL execution."
        )
    if subject_area in SEMANTICS_AREAS:
        return (
            "Curriculum design: DDL/DML semantics are measured by MCQ and written "
            "analysis; scheduled read-only SQL inspects the resulting data and catalog "
            "state. Mutating SQL is outside the approved sandbox policy."
        )
    return (
        "Published configuration retained: conceptual MCQ, read-only executable SQL "
        "against a declared dataset, and rubric-scored written analysis. SQL quotas "
        "only apply where the sandbox can execute the measured objective."
    )


def _row(assessment_id, subject_area, band, version, mix, *, approved_by=None):
    return AssessmentBlueprint(
        assessment_id=assessment_id,
        subject_area=subject_area,
        difficulty_band=band,
        version_no=version,
        status="approved",
        max_questions=mix["mcq"] + mix["sql"] + mix["essay"],
        target_mcq=mix["mcq"],
        target_sql=mix["sql"],
        target_essay=mix["essay"],
        scoring=dict(_SCORING),
        evidence_types=evidence_types(subject_area, mix),
        approval_basis=_approval_basis(subject_area, mix),
        approved_by=approved_by,
    )


def seed_blueprints(db, assessment, *, approved_by=None):
    """Ensure a current approved version exists for every area and band.

    Existing single-area behavior is preserved by the practical mix. A changed
    assessment configuration appends a new immutable version. Retired policies
    are never silently resurrected.
    """
    SecurityRepository(db).lock(f"assessment-blueprint:{assessment.assessment_id}")
    targets = list(assessment.targets)
    if not targets:
        return []
    created = []
    for area in sorted({t.concept.subject_area for t in targets}):
        area_targets = [t for t in targets if t.concept.subject_area == area]
        for band, (low, high) in DIFFICULTY_BANDS.items():
            if not any(max(low, t.min_difficulty) <= min(high, t.max_difficulty)
                       for t in area_targets):
                continue
            latest = db.scalar(
                select(AssessmentBlueprint)
                .where(AssessmentBlueprint.assessment_id == assessment.assessment_id,
                       AssessmentBlueprint.subject_area == area,
                       AssessmentBlueprint.difficulty_band == band)
                .order_by(AssessmentBlueprint.version_no.desc())
                .limit(1)
            )
            mix = desired_mix(assessment, area)
            if latest is not None and latest.status != "approved":
                continue
            if latest is not None and (latest.target_mcq, latest.target_sql, latest.target_essay) == (
                    mix["mcq"], mix["sql"], mix["essay"]) and latest.scoring == _SCORING \
                    and latest.evidence_types == evidence_types(area, mix):
                continue
            row = _row(assessment.assessment_id, area, band,
                       1 if latest is None else latest.version_no + 1, mix,
                       approved_by=approved_by)
            db.add(row)
            created.append(row)
    db.flush()
    return created


def ensure_all_blueprints(db, *, approved_by=None):
    """Backfill published assessments after a controlled migration activation."""
    from ..models import Assessment

    created = []
    for assessment in db.scalars(select(Assessment).where(Assessment.status == "published")):
        created.extend(seed_blueprints(db, assessment, approved_by=approved_by))
    return created


def resolve_blueprint(db, assessment, concept_ids, difficulty):
    """Return (row, resolution) for a single-area selection.

    Mixed-area selections retain the published fixed mix. An assessment with no
    blueprints at all (custom or historical) also retains it. Once an assessment
    is blueprint-managed, a missing or retired version for a single area/band is
    an actionable error, never a silent substitution.
    """
    selected = set(concept_ids)
    areas = {t.concept.subject_area for t in assessment.targets if t.concept_id in selected}
    area = next(iter(areas)) if len(areas) == 1 else None
    managed = bool(db.scalar(
        select(func.count()).select_from(AssessmentBlueprint)
        .where(AssessmentBlueprint.assessment_id == assessment.assessment_id)
    ))
    if not managed:
        return None, {"mode": "legacy", "reason": "assessment_not_blueprint_managed"}
    if area is None:
        return None, {"mode": "legacy", "reason": "mixed_subject_areas"}
    latest = db.scalar(
        select(AssessmentBlueprint)
        .where(AssessmentBlueprint.assessment_id == assessment.assessment_id,
               AssessmentBlueprint.subject_area == area,
               AssessmentBlueprint.difficulty_band == difficulty)
        .order_by(AssessmentBlueprint.version_no.desc())
        .limit(1)
    )
    if latest is None:
        raise AppError(422, "blueprint_not_available",
                       "No approved assessment blueprint exists for this skill and difficulty",
                       details={"assessment_id": assessment.assessment_id,
                                "subject_area": area, "difficulty_band": difficulty})
    if latest.status != "approved":
        raise AppError(422, "blueprint_retired",
                       "The assessment blueprint for this skill and difficulty has been retired",
                       details={"assessment_id": assessment.assessment_id,
                                "subject_area": area, "difficulty_band": difficulty,
                                "version_no": latest.version_no})
    return latest, {
        "mode": "blueprint",
        "blueprint_id": latest.blueprint_id,
        "version_no": latest.version_no,
        "subject_area": area,
        "difficulty_band": difficulty,
    }


def quotas_for(row):
    return {"mcq": row.target_mcq, "sql": row.target_sql, "essay": row.target_essay}


def snapshot_policy(row):
    """Serializable blueprint evidence captured on the session."""
    approved_at = getattr(row, "approved_at", None)
    return {
        "blueprint_id": row.blueprint_id,
        "version_no": row.version_no,
        "subject_area": row.subject_area,
        "difficulty_band": row.difficulty_band,
        "max_questions": row.max_questions,
        "target_mcq": row.target_mcq,
        "target_sql": row.target_sql,
        "target_essay": row.target_essay,
        "scoring": row.scoring,
        "evidence_types": row.evidence_types,
        "approval_basis": row.approval_basis,
        "approved_at": approved_at.isoformat() if approved_at is not None else None,
    }


def verify_quotas(row):
    counts = Counter({"mcq": row.target_mcq, "sql": row.target_sql, "essay": row.target_essay})
    if sum(counts.values()) != row.max_questions:
        raise AppError(409, "invalid_blueprint",
                       "Assessment blueprint quota does not match its question count",
                       details={"blueprint_id": row.blueprint_id})

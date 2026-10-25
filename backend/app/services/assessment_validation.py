"""Formal assessment configuration and bank coverage acceptance checks."""
from collections import Counter

from ..errors import AppError
from ..repositories import AssessmentRepository, QuestionRepository
from .question_service import _validation_missing
from .bank_validation import verify_sql_fixtures


def validate_assessment_bank(db, assessment, runner=None):
    problems = []
    formal = {"duration_min": 60, "max_questions": 13, "target_mcq": 10,
              "target_sql": 2, "target_essay": 1}
    for key, required in formal.items():
        if getattr(assessment, key) != required:
            problems.append(f"{key} must be {required}")
    ranges = {t.concept_id: (t.min_difficulty, t.max_difficulty) for t in assessment.targets}
    if not ranges:
        problems.append("At least one target concept is required")
    repo = QuestionRepository(db)
    eligible = []
    coverage = set()
    families = set()
    for question in AssessmentRepository(db).eligible_questions(assessment, set()):
        fits = {t.concept_id for t in question.concept_tags if t.confirmed
                and t.concept_id in ranges
                and ranges[t.concept_id][0] <= question.difficulty_level <= ranges[t.concept_id][1]}
        if not fits:
            continue
        missing = _validation_missing(repo, question)
        if runner and not missing and question.question_type == "sql":
            missing = verify_sql_fixtures(runner, repo.datasets_for(question.question_id), question.reference_answer)
        if missing:
            problems.append(f"Question #{question.question_id}: {'; '.join(missing)}")
            continue
        family = question.family_id or question.question_id
        if family in families:
            continue
        families.add(family)
        eligible.append(question)
        coverage.update(fits)
    counts = Counter(q.question_type for q in eligible)
    for kind, required in (("mcq", 10), ("sql", 2), ("essay", 1)):
        if counts[kind] < required:
            problems.append(f"Need {required} eligible {kind.upper()} questions; available {counts[kind]}")
    basics = sum(q.question_type == "mcq" and q.difficulty_level <= 2 for q in eligible)
    if basics < 3:
        problems.append(f"Opening phase needs three distinct basic MCQs (difficulty 1–2); available {basics}")
    for concept_id in sorted(set(ranges) - coverage):
        problems.append(f"Target concept #{concept_id} has no eligible confirmed question")
    if problems:
        raise AppError(422, "assessment_bank_incomplete",
                       "Assessment cannot open until its configuration and question bank are valid",
                       details=[{"problem": problem} for problem in problems])

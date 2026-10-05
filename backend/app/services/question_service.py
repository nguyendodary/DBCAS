"""Question bank management — UC07 / Admin story 5.

The bank holds only administrator-curated items across the three formats.
Content rules enforced here:

* mcq   — at least 2 options, exactly one correct
* sql   — at least 1 test dataset (setup + expected result) and a
          reference answer
* essay — at least 1 rubric row
* all   — at least one confirmed concept tag to be serveable, otherwise
          the adaptive engine cannot place it and competency evidence
          would never attach to a concept

Editing a validated item demotes it back to ``draft`` — a changed answer
key or rubric must be re-validated before it can be served again.
AI-pending tags (tag_source='ai', confirmed=false) belong to the UC08
review flow; an explicit admin tag set confirms them in place but never
silently deletes them.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete as sql_delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import (
    Account,
    McqOption,
    Question,
    QuestionConcept,
    Rubric,
    SqlTestDataset,
)
from ..repositories import CurriculumRepository, QuestionRepository
from ..schemas import (
    McqOptionResult,
    QuestionConceptTag,
    QuestionDetail,
    QuestionListItem,
    QuestionUpsertRequest,
    RubricResult,
    SqlDatasetResult,
)


def _tags(question: Question) -> list[QuestionConceptTag]:
    return [
        QuestionConceptTag(
            concept_id=tag.concept_id,
            concept_code=tag.concept.concept_code,
            concept_name=tag.concept.concept_name,
            tag_source=tag.tag_source,
            is_required=tag.is_required,
            confirmed=tag.confirmed,
        )
        for tag in sorted(question.concept_tags, key=lambda t: t.concept_id)
    ]


def _to_list_item(q: Question) -> QuestionListItem:
    return QuestionListItem(
        question_id=q.question_id,
        question_type=q.question_type,
        prompt=q.prompt,
        difficulty_level=q.difficulty_level,
        points=q.points,
        status=q.status,
        source=q.source,
        updated_at=q.updated_at,
        concepts=_tags(q),
    )


def _to_detail(repo: QuestionRepository, q: Question) -> QuestionDetail:
    return QuestionDetail(
        **_to_list_item(q).model_dump(),
        reference_answer=q.reference_answer,
        options=[
            McqOptionResult(
                option_id=o.option_id,
                option_label=o.option_label,
                option_text=o.option_text,
                is_correct=o.is_correct,
            )
            for o in sorted(q.options, key=lambda o: o.option_id)
        ],
        datasets=[
            SqlDatasetResult(
                dataset_id=d.dataset_id,
                dataset_name=d.dataset_name,
                setup_sql=d.setup_sql,
                expected_result=d.expected_result,
                is_edge_case=d.is_edge_case,
            )
            for d in repo.datasets_for(q.question_id)
        ],
        rubrics=[
            RubricResult(
                rubric_id=r.rubric_id,
                level_name=r.level_name,
                min_score=r.min_score,
                max_score=r.max_score,
                criteria=r.criteria,
            )
            for r in repo.rubrics_for(q.question_id)
        ],
    )


def _require_question(repo: QuestionRepository, question_id: int) -> Question:
    q = repo.get_detail(question_id)
    if q is None:
        raise AppError(404, "question_not_found", "Question not found")
    return q


def _check_type_payload(payload: QuestionUpsertRequest) -> None:
    """422 on child collections that don't fit the question type."""
    qt = payload.question_type
    problems: list[str] = []
    if qt != "mcq" and payload.options:
        problems.append("options are only allowed for mcq questions")
    if qt != "sql" and payload.datasets:
        problems.append("datasets are only allowed for sql questions")
    if qt != "essay" and payload.rubrics:
        problems.append("rubrics are only allowed for essay questions")
    if qt == "mcq":
        if len(payload.options) >= 1 and len(payload.options) < 2:
            problems.append("mcq questions need at least 2 options")
        correct = sum(1 for o in payload.options if o.is_correct)
        if len(payload.options) >= 2 and correct != 1:
            problems.append("mcq questions need exactly one correct option")
    if qt == "sql" and payload.datasets:
        for i, ds in enumerate(payload.datasets):
            er = ds.expected_result
            if not isinstance(er, dict) or "rows" not in er:
                problems.append(
                    f"datasets[{i}].expected_result must contain 'rows'"
                )
    if problems:
        raise AppError(422, "invalid_question_payload", "; ".join(problems))


def _check_concepts(
    db: Session, payload: QuestionUpsertRequest
) -> set[int]:
    ids = set(payload.concept_ids)
    if len(ids) != len(payload.concept_ids):
        raise AppError(422, "duplicate_concept_ids", "Concept ids must be unique")
    required = set(payload.required_concept_ids)
    if not required.issubset(ids):
        raise AppError(
            422,
            "required_not_tagged",
            "required_concept_ids must be a subset of concept_ids",
        )
    found = {c.concept_id for c in CurriculumRepository(db).get_concepts(ids)}
    missing = ids - found
    if missing:
        raise AppError(
            404,
            "concept_not_found",
            "Unknown concept ids",
            details=[{"concept_id": i} for i in sorted(missing)],
        )
    return required


def _apply_children(
    repo: QuestionRepository,
    db: Session,
    question: Question,
    payload: QuestionUpsertRequest,
) -> None:
    """Replace the type-specific children + admin tag set from the payload."""
    repo.replace_options(question, payload.options)
    repo.replace_datasets(question, payload.datasets)
    repo.replace_rubrics(question, payload.rubrics)

    required = _check_concepts(db, payload)
    keep = set(payload.concept_ids)
    for concept_id in sorted(keep):
        repo.upsert_tag(
            question.question_id,
            concept_id,
            source="admin",
            confirmed=True,
            is_required=concept_id in required,
        )
    for tag in repo.tags_for(question.question_id):
        if tag.concept_id in keep:
            continue
        if tag.tag_source == "admin":
            repo.db.delete(tag)
        elif tag.confirmed:
            tag.confirmed = False  # previously confirmed AI suggestion
    repo.db.flush()


def search_questions(
    db: Session,
    *,
    concept_id: Optional[int] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[int] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
) -> list[QuestionListItem]:
    repo = QuestionRepository(db)
    return [
        _to_list_item(item)
        for item in repo.search(
            concept_id=concept_id,
            question_type=question_type,
            difficulty=difficulty,
            status=status,
            q=q,
        )
    ]


def get_question(db: Session, question_id: int) -> QuestionDetail:
    repo = QuestionRepository(db)
    return _to_detail(repo, _require_question(repo, question_id))


def create_question(
    db: Session, payload: QuestionUpsertRequest, admin: Account
) -> QuestionDetail:
    _check_type_payload(payload)
    repo = QuestionRepository(db)
    try:
        question = repo.create(
            question_type=payload.question_type,
            prompt=payload.prompt,
            reference_answer=payload.reference_answer,
            difficulty_level=payload.difficulty_level,
            points=payload.points,
            source="bank",
            status="draft",
            created_by=admin.account_id,
        )
        _apply_children(repo, db, question, payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(422, "invalid_question", "Question violates a constraint")
    # expire_on_commit=False — refresh so the detail reflects the new rows
    db.expire(question)
    return _to_detail(repo, repo.get_detail(question.question_id))


def replace_question(
    db: Session, question_id: int, payload: QuestionUpsertRequest
) -> QuestionDetail:
    repo = QuestionRepository(db)
    question = _require_question(repo, question_id)
    _check_type_payload(payload)
    try:
        question.question_type = payload.question_type
        question.prompt = payload.prompt
        question.reference_answer = payload.reference_answer
        question.difficulty_level = payload.difficulty_level
        question.points = payload.points
        question.updated_at = datetime.now(timezone.utc)
        if question.status == "validated":
            question.status = "draft"  # content changed — must re-validate
        _apply_children(repo, db, question, payload)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(422, "invalid_question", "Question violates a constraint")
    db.expire(question)
    return _to_detail(repo, repo.get_detail(question_id))


def _validation_missing(repo: QuestionRepository, q: Question) -> list[str]:
    """What stops this item from being served (the 'validated' checklist)."""
    missing: list[str] = []
    if not any(t.confirmed for t in q.concept_tags):
        missing.append("at least one confirmed concept tag")
    if q.question_type == "mcq":
        if len(q.options) < 2:
            missing.append("at least 2 options")
        elif sum(1 for o in q.options if o.is_correct) != 1:
            missing.append("exactly one correct option")
    elif q.question_type == "sql":
        if not repo.datasets_for(q.question_id):
            missing.append("at least one test dataset")
        if not (q.reference_answer or "").strip():
            missing.append("a reference answer")
    elif q.question_type == "essay":
        if not repo.rubrics_for(q.question_id):
            missing.append("at least one rubric row")
    return missing


def set_question_status(
    db: Session, question_id: int, status: str
) -> QuestionDetail:
    repo = QuestionRepository(db)
    question = _require_question(repo, question_id)
    if status == "validated":
        missing = _validation_missing(repo, question)
        if missing:
            raise AppError(
                422,
                "question_incomplete",
                "Question cannot be validated yet",
                details=[{"missing": m} for m in missing],
            )
    question.status = status
    question.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.expire(question)
    return _to_detail(repo, repo.get_detail(question_id))


def delete_question(db: Session, question_id: int) -> None:
    repo = QuestionRepository(db)
    question = _require_question(repo, question_id)
    refs = {k: v for k, v in repo.reference_counts(question_id).items() if v}
    if refs:
        raise AppError(
            409,
            "question_in_use",
            "Question is referenced by session history and cannot be deleted",
            details=[{"table": t, "references": n} for t, n in sorted(refs.items())],
        )
    # Bulk deletes — removing children through loaded ORM collections would
    # trip SQLAlchemy's dependency sync on the composite PKs.
    for model in (QuestionConcept, McqOption, SqlTestDataset, Rubric):
        db.execute(
            sql_delete(model).where(model.question_id == question_id)
        )
    db.expire(question)  # drop stale loaded collections before deleting parent
    repo.db.delete(question)
    db.commit()

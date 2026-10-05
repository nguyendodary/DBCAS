"""AI-assisted admin curation flows — UC06 / UC08 / UC10.

The LLM is strictly *assistive*: it proposes, the administrator decides.
Nothing the model produces can affect serving, competency, gaps, or the
question bank until an admin confirms it.

* UC06  ``suggest_clo_concepts`` — model picks concepts for a CLO; rows
        are stored as ``clo_concept(mapping_source='ai', status='pending')``
        and only take effect once an admin confirms them.
* UC08  ``suggest_question_tags`` — model proposes concept tags,
        difficulty and evaluation criteria for a question; tags land as
        ``question_concept(tag_source='ai', confirmed=false)`` and never
        satisfy the validated-question checklist until confirmed.
* UC10  candidates — model drafts questions held in
        ``question_candidate``, OUTSIDE the bank (NFR-09). Deterministic
        pre-review checks run at generation time and on demand:
        completeness per type, prompt-duplicate detection against bank
        and live candidates, and for SQL a real sandbox execution of the
        reference answer against every declared test dataset. Approval
        promotes the candidate into a ``status='validated'`` question
        with a confirmed ai tag; rejection hides it from review lists.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import (
    Account,
    McqOption,
    Question,
    QuestionCandidate,
    Rubric,
    SqlTestDataset,
)
from ..repositories import CurriculumRepository, QuestionRepository
from ..schemas import (
    CandidateGenerateRequest,
    CloAiSuggestResult,
    CloResult,
    QuestionCandidateDetail,
    QuestionCandidateItem,
    TagSuggestionResult,
)
from . import curriculum_service, question_service
from . import sql_result
from .llm.service import LLMService
from .sandbox_runner import SandboxRunner, SandboxError

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are an assessment-content assistant for a PostgreSQL competency "
    "platform. Answer with strict JSON only — no prose, no code fences."
)


def _concept_brief(repo: CurriculumRepository) -> list[dict]:
    return [
        {
            "concept_id": c.concept_id,
            "concept_code": c.concept_code,
            "concept_name": c.concept_name,
            "subject_area": c.subject_area,
            "difficulty_level": c.difficulty_level,
        }
        for c in repo.list_concepts()
    ]


def _id_list(value) -> list[int]:
    out: list[int] = []
    if not isinstance(value, list):
        return out
    for v in value:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return out


# ---------------------------------------------------------------- UC06


def suggest_clo_concepts(
    db: Session, clo_id: int, llm: LLMService
) -> CloAiSuggestResult:
    repo = CurriculumRepository(db)
    clo = repo.get_clo(clo_id)
    if clo is None:
        raise AppError(404, "clo_not_found", "Course learning outcome not found")
    concepts = _concept_brief(repo)
    if not concepts:
        raise AppError(
            409, "no_concepts", "Define concepts before requesting suggestions"
        )

    result = llm.generate_structured(
        "clo_map",
        [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": "map_clo_to_concepts",
                        "clo": {
                            "clo_code": clo.clo_code,
                            "title": clo.title,
                            "description": clo.description,
                        },
                        "concepts": concepts,
                        "return_schema": {
                            "concept_ids": ["int"],
                            "rationale": "string",
                        },
                    }
                ),
            },
        ],
    )
    wanted = set(_id_list(result.get("concept_ids")))
    existing = {c["concept_id"] for c in concepts}
    valid = sorted(wanted & existing)
    ignored = sorted(wanted - existing)
    already_linked = {l.concept_id for l in repo.links_for_clo(clo_id)}

    for concept_id in valid:
        if concept_id in already_linked:
            continue  # never downgrade an existing link
        repo.upsert_clo_link(
            clo_id, concept_id, source="ai", status="pending"
        )
    db.commit()
    db.expire(clo)  # drop the stale concept_links collection
    return CloAiSuggestResult(
        clo_id=clo_id,
        suggested_concept_ids=[c for c in valid if c not in already_linked],
        ignored_concept_ids=ignored,
        rationale=result.get("rationale"),
        clo=curriculum_service._to_clo_result(repo.get_clo(clo_id)),
    )


def delete_clo_link(db: Session, clo_id: int, concept_id: int) -> CloResult:
    """Reject a pending AI suggestion (or remove a link row entirely for
    pending rows). Confirmed mappings go through set_clo_concepts so an
    accidental click can't silently unmap a CLO."""
    repo = CurriculumRepository(db)
    if repo.get_clo(clo_id) is None:
        raise AppError(404, "clo_not_found", "Course learning outcome not found")
    link = repo.get_clo_link(clo_id, concept_id)
    if link is None:
        raise AppError(404, "mapping_not_found", "Concept mapping not found")
    if link.status == "confirmed":
        raise AppError(
            409,
            "mapping_confirmed",
            "Confirmed mappings are removed via PUT /clos/{id}/concepts",
        )
    repo.db.delete(link)
    db.commit()
    return curriculum_service._to_clo_result(repo.get_clo(clo_id))


def confirm_clo_link(db: Session, clo_id: int, concept_id: int) -> CloResult:
    """Accept one AI suggestion in place (equivalent to including it in
    the confirmed set, but keeps the 'ai' provenance)."""
    repo = CurriculumRepository(db)
    if repo.get_clo(clo_id) is None:
        raise AppError(404, "clo_not_found", "Course learning outcome not found")
    link = repo.get_clo_link(clo_id, concept_id)
    if link is None:
        raise AppError(404, "mapping_not_found", "Concept mapping not found")
    link.status = "confirmed"
    db.commit()
    return curriculum_service._to_clo_result(repo.get_clo(clo_id))


# ---------------------------------------------------------------- UC08


def suggest_question_tags(
    db: Session, question_id: int, llm: LLMService
) -> TagSuggestionResult:
    qrepo = QuestionRepository(db)
    question = qrepo.get_detail(question_id)
    if question is None:
        raise AppError(404, "question_not_found", "Question not found")
    crepo = CurriculumRepository(db)
    concepts = _concept_brief(crepo)
    if not concepts:
        raise AppError(
            409, "no_concepts", "Define concepts before requesting suggestions"
        )

    result = llm.generate_structured(
        "tag",
        [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": "suggest_question_tags",
                        "question": {
                            "question_type": question.question_type,
                            "prompt": question.prompt,
                        },
                        "concepts": concepts,
                        "return_schema": {
                            "concept_ids": ["int"],
                            "difficulty_level": "1-5",
                            "evaluation_criteria": "string",
                        },
                    }
                ),
            },
        ],
    )
    wanted = set(_id_list(result.get("concept_ids")))
    existing = {c["concept_id"] for c in concepts}
    valid = sorted(wanted & existing)
    ignored = sorted(wanted - existing)
    if not valid:
        raise AppError(
            422,
            "no_usable_tags",
            "The AI suggestion contained no known concepts",
            details=[{"ignored_concept_ids": i} for i in ignored],
        )

    for concept_id in valid:
        tag = next(
            (t for t in qrepo.tags_for(question_id)
             if t.concept_id == concept_id),
            None,
        )
        if tag is not None and tag.confirmed:
            continue  # never downgrade a confirmed tag
        qrepo.upsert_tag(
            question_id,
            concept_id,
            source="ai",
            confirmed=False,
            is_required=False,
        )
    db.commit()

    difficulty = result.get("difficulty_level")
    try:
        difficulty = int(difficulty) if difficulty is not None else None
        if difficulty is not None and not (1 <= difficulty <= 5):
            difficulty = None
    except (TypeError, ValueError):
        difficulty = None

    db.expire(question)
    return TagSuggestionResult(
        question_id=question_id,
        suggested_concept_ids=valid,
        ignored_concept_ids=ignored,
        suggested_difficulty=difficulty,
        evaluation_criteria=result.get("evaluation_criteria"),
        question=question_service.get_question(db, question_id),
    )


def confirm_question_tag(
    db: Session, question_id: int, concept_id: int
):
    qrepo = QuestionRepository(db)
    if qrepo.get_detail(question_id) is None:
        raise AppError(404, "question_not_found", "Question not found")
    tag = next(
        (t for t in qrepo.tags_for(question_id) if t.concept_id == concept_id),
        None,
    )
    if tag is None:
        raise AppError(404, "tag_not_found", "Concept tag not found")
    tag.confirmed = True
    db.commit()
    return question_service.get_question(db, question_id)


def reject_question_tag(
    db: Session, question_id: int, concept_id: int
):
    """Remove a pending/unconfirmed suggestion. Confirmed tags require the
    question PUT flow so the validated-tag rule is re-checked."""
    qrepo = QuestionRepository(db)
    question = qrepo.get_detail(question_id)
    if question is None:
        raise AppError(404, "question_not_found", "Question not found")
    tag = next(
        (t for t in qrepo.tags_for(question_id) if t.concept_id == concept_id),
        None,
    )
    if tag is None:
        raise AppError(404, "tag_not_found", "Concept tag not found")
    if tag.confirmed:
        raise AppError(
            409,
            "tag_confirmed",
            "Confirmed tags are removed by editing the question",
        )
    qrepo.db.delete(tag)
    db.commit()
    db.expire(question)
    return question_service.get_question(db, question_id)


# ---------------------------------------------------------------- UC10


def _candidate_dto(row: QuestionCandidate) -> QuestionCandidateItem:
    return QuestionCandidateItem(
        candidate_id=row.candidate_id,
        concept_id=row.concept_id,
        concept_code=row.concept.concept_code if row.concept else None,
        question_type=row.question_type,
        validation_status=row.validation_status,
        promoted_question_id=row.promoted_question_id,
        created_at=row.created_at,
    )


def _candidate_detail(row: QuestionCandidate) -> QuestionCandidateDetail:
    return QuestionCandidateDetail(
        **_candidate_dto(row).model_dump(),
        payload=row.payload or {},
        validation_detail=row.validation_detail,
    )


def list_candidates(
    db: Session, status: Optional[str] = None
) -> list[QuestionCandidateItem]:
    return [
        _candidate_dto(r)
        for r in QuestionRepository(db).list_candidates(status)
    ]


def get_candidate(db: Session, candidate_id: int) -> QuestionCandidateDetail:
    row = QuestionRepository(db).get_candidate(candidate_id)
    if row is None:
        raise AppError(404, "candidate_not_found", "Question candidate not found")
    return _candidate_detail(row)


def _completeness_problems(qtype: str, payload: dict) -> list[str]:
    """Deterministic completeness check mirroring the bank's rules."""
    problems: list[str] = []
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        problems.append("prompt is empty")
    if qtype == "mcq":
        options = payload.get("options") or []
        if len(options) < 2:
            problems.append("mcq needs at least 2 options")
        else:
            correct = [o for o in options if o.get("is_correct")]
            if len(correct) != 1:
                problems.append("mcq needs exactly one correct option")
            for i, o in enumerate(options):
                if not (o.get("option_label") and o.get("option_text")):
                    problems.append(f"options[{i}] needs label and text")
    elif qtype == "sql":
        if not (payload.get("reference_answer") or "").strip():
            problems.append("sql needs a reference answer")
        datasets = payload.get("datasets") or []
        if not datasets:
            problems.append("sql needs at least one test dataset")
        for i, d in enumerate(datasets):
            if not (d.get("setup_sql") or "").strip():
                problems.append(f"datasets[{i}] needs setup_sql")
            er = d.get("expected_result")
            if not isinstance(er, dict) or "rows" not in er:
                problems.append(
                    f"datasets[{i}].expected_result must contain 'rows'"
                )
    elif qtype == "essay":
        rubrics = payload.get("rubrics") or []
        if not rubrics:
            problems.append("essay needs at least one rubric level")
        for i, r in enumerate(rubrics):
            if not (
                r.get("level_name")
                and r.get("criteria")
                and r.get("min_score") is not None
                and r.get("max_score") is not None
            ):
                problems.append(f"rubrics[{i}] is incomplete")
    return problems


def _run_sql_checks(
    runner: SandboxRunner, payload: dict
) -> list[dict]:
    """Execute the reference answer on every declared dataset — the UC10
    'runs the task and reference answer on test datasets' check."""
    ref = (payload.get("reference_answer") or "").strip()
    results: list[dict] = []
    for ds in payload.get("datasets") or []:
        entry = {"dataset": ds.get("dataset_name") or "?"}
        expected = sql_result.parse_expected(ds.get("expected_result"))
        if expected is None:
            entry["status"] = "error"
            entry["error_type"] = "invalid_expected_result"
            results.append(entry)
            continue
        schema = None
        try:
            schema = runner.provision_dataset(ds.get("setup_sql") or "")
            outcome_result = runner.execute(ref, schema=schema)
        except SandboxError as exc:
            entry["status"] = "error"
            entry["error_type"] = getattr(exc, "code", "sandbox_error")
            results.append(entry)
            continue
        finally:
            if schema:
                try:
                    runner.drop_dataset(schema)
                except SandboxError:
                    pass
        if not outcome_result.success:
            entry["status"] = "error"
            entry["error_type"] = outcome_result.error_type
            results.append(entry)
            continue
        outcome = sql_result.compare(
            outcome_result.columns, outcome_result.rows, expected
        )
        entry["status"] = outcome.status
        results.append(entry)
    return results


def _validate_candidate(
    repo: QuestionRepository,
    row: QuestionCandidate,
    runner: Optional[SandboxRunner],
) -> dict:
    """All pre-review checks; returns the validation_detail dict."""
    payload = row.payload or {}
    detail: dict = {"checks": []}
    problems = _completeness_problems(row.question_type, payload)
    detail["checks"].append(
        {"check": "completeness", "ok": not problems, "problems": problems}
    )
    ok = not problems

    prompt = (payload.get("prompt") or "").strip()
    if prompt:
        dupes = repo.prompt_duplicates(
            prompt, exclude_candidate_id=row.candidate_id
        )
        detail["checks"].append(
            {
                "check": "duplicate",
                "ok": not dupes,
                "matches": [
                    {"question_id": i} if i > 0 else {"candidate_id": -i}
                    for i in dupes
                ],
            }
        )
        ok = ok and not dupes

    if row.question_type == "sql" and ok:
        if runner is None:
            detail["checks"].append(
                {
                    "check": "sql_execution",
                    "ok": False,
                    "error": "sandbox_unavailable",
                }
            )
            ok = False
        else:
            runs = _run_sql_checks(runner, payload)
            passed = all(r.get("status") == "passed" for r in runs)
            detail["checks"].append(
                {"check": "sql_execution", "ok": passed, "datasets": runs}
            )
            ok = ok and passed
    detail["ok"] = ok
    return detail


def generate_candidates(
    db: Session,
    payload: CandidateGenerateRequest,
    admin: Account,
    llm: LLMService,
    runner: Optional[SandboxRunner],
) -> list[QuestionCandidateDetail]:
    repo = QuestionRepository(db)
    crepo = CurriculumRepository(db)
    concept = crepo.get_concept(payload.concept_id)
    if concept is None:
        raise AppError(404, "concept_not_found", "Concept not found")

    spec = {
        "mcq": {
            "prompt": "string",
            "options": [
                {"option_label": "A", "option_text": "...", "is_correct": False}
            ],
            "difficulty_level": "1-5",
        },
        "sql": {
            "prompt": "string",
            "reference_answer": "SELECT ...",
            "datasets": [
                {
                    "dataset_name": "base",
                    "setup_sql": "CREATE TABLE ...; INSERT ...;",
                    "expected_result": {"rows": [[1]], "columns": ["c"]},
                    "is_edge_case": False,
                }
            ],
            "difficulty_level": "1-5",
        },
        "essay": {
            "prompt": "string",
            "reference_answer": "string",
            "rubrics": [
                {
                    "level_name": "Complete|Mostly Complete|Partial|Incomplete",
                    "min_score": 0,
                    "max_score": 1,
                    "criteria": "string",
                }
            ],
            "difficulty_level": "1-5",
        },
    }
    result = llm.generate_structured(
        "gen_question",
        [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": "generate_question_candidates",
                        "count": payload.count,
                        "question_type": payload.question_type,
                        "concept": {
                            "concept_id": concept.concept_id,
                            "concept_code": concept.concept_code,
                            "concept_name": concept.concept_name,
                            "subject_area": concept.subject_area,
                        },
                        "candidate_schema": spec[payload.question_type],
                        "return_schema": {
                            "questions": ["array of candidate_schema objects"]
                        },
                    }
                ),
            },
        ],
    )
    raw_items = result.get("questions")
    if not isinstance(raw_items, list):
        # tolerate a bare single-object response
        raw_items = [result] if result.get("prompt") else []

    out: list[QuestionCandidateDetail] = []
    for item in raw_items[: payload.count]:
        if not isinstance(item, dict):
            continue
        row = repo.create_candidate(
            payload.concept_id, payload.question_type, item
        )
        row.validation_detail = _validate_candidate(repo, row, runner)
        row.validation_status = (
            "validated" if row.validation_detail.get("ok") else "pending"
        )
        out.append(row)
    db.commit()
    return [
        _candidate_detail(repo.get_candidate(r.candidate_id)) for r in out
    ]


def validate_candidate(
    db: Session, candidate_id: int, runner: Optional[SandboxRunner]
) -> QuestionCandidateDetail:
    """Re-run the pre-review checks (e.g. after the bank changed)."""
    repo = QuestionRepository(db)
    row = repo.get_candidate(candidate_id)
    if row is None:
        raise AppError(404, "candidate_not_found", "Question candidate not found")
    if row.validation_status == "approved":
        raise AppError(
            409, "already_approved", "Candidate was already promoted"
        )
    row.validation_detail = _validate_candidate(repo, row, runner)
    row.validation_status = (
        "validated" if row.validation_detail.get("ok") else "pending"
    )
    db.commit()
    return _candidate_detail(repo.get_candidate(candidate_id))


def approve_candidate(
    db: Session, candidate_id: int, admin: Account
) -> QuestionCandidateDetail:
    """Promote a validated candidate into the bank as a validated question
    with a confirmed ai-sourced tag — the only way AI content reaches
    serving (NFR-09)."""
    repo = QuestionRepository(db)
    row = repo.get_candidate(candidate_id)
    if row is None:
        raise AppError(404, "candidate_not_found", "Question candidate not found")
    if row.validation_status == "approved":
        return _candidate_detail(row)  # idempotent
    if row.validation_status != "validated":
        raise AppError(
            409,
            "candidate_not_validated",
            "Candidate must pass the pre-review checks first",
        )
    payload = row.payload or {}
    problems = _completeness_problems(row.question_type, payload)
    if problems:
        raise AppError(
            422, "candidate_incomplete", "; ".join(problems)
        )
    try:
        difficulty = int(payload.get("difficulty_level") or 1)
    except (TypeError, ValueError):
        difficulty = 1
    difficulty = min(max(difficulty, 1), 5)

    question = Question(
        question_type=row.question_type,
        prompt=(payload.get("prompt") or "").strip(),
        reference_answer=(payload.get("reference_answer") or None),
        difficulty_level=difficulty,
        source="ai",
        status="validated",
        created_by=admin.account_id,
    )
    repo.db.add(question)
    repo.db.flush()

    for o in payload.get("options") or []:
        repo.db.add(
            McqOption(
                question_id=question.question_id,
                option_label=str(o.get("option_label", ""))[:10],
                option_text=str(o.get("option_text", "")),
                is_correct=bool(o.get("is_correct")),
            )
        )
    for d in payload.get("datasets") or []:
        repo.db.add(
            SqlTestDataset(
                question_id=question.question_id,
                dataset_name=str(d.get("dataset_name") or "dataset"),
                setup_sql=str(d.get("setup_sql") or ""),
                expected_result=d.get("expected_result") or {"rows": []},
                is_edge_case=bool(d.get("is_edge_case")),
            )
        )
    for r in payload.get("rubrics") or []:
        repo.db.add(
            Rubric(
                question_id=question.question_id,
                level_name=str(r.get("level_name") or "")[:30],
                min_score=r.get("min_score"),
                max_score=r.get("max_score"),
                criteria=str(r.get("criteria") or ""),
            )
        )
    repo.upsert_tag(
        question.question_id,
        row.concept_id,
        source="ai",
        confirmed=True,
        is_required=bool(payload.get("is_required_concept")),
    )
    row.validation_status = "approved"
    row.promoted_question_id = question.question_id
    db.commit()
    return _candidate_detail(repo.get_candidate(candidate_id))


def reject_candidate(
    db: Session, candidate_id: int
) -> QuestionCandidateDetail:
    repo = QuestionRepository(db)
    row = repo.get_candidate(candidate_id)
    if row is None:
        raise AppError(404, "candidate_not_found", "Question candidate not found")
    if row.validation_status == "approved":
        raise AppError(
            409, "already_approved", "Candidate was already promoted"
        )
    row.validation_status = "rejected"
    db.commit()
    return _candidate_detail(repo.get_candidate(candidate_id))

"""UC15 — four-level rubric essay scoring (Task 3.5 / FR-10).

Flow: rubric rows (administrator-configured, four levels) + question prompt +
reference answer + *sanitized* learner answer -> the LLM provider is asked
for strict-JSON grading constrained to the supplied rubric. The response is
validated and clamped into the selected level's [min_score, max_score] band
before anything is persisted — an invalid LLM payload fails safely (502) and
the attempt is left unsubmitted so a retry is possible.

The LLM output is assistive evidence: the score it returns is bounded by the
administrator's rubric bands and question points, and it never feeds back
into deterministic competency math (that pipeline reads attempt.score only).
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, Attempt, Question, Rubric
from ..repositories import AssessmentRepository
from ..schemas import AttemptResult, SubmitAnswerRequest
from .llm import ChatMessage, LLMError, LLMService, sanitize_learner_text
from .session_guard import load_owned_active_session, load_served_attempt

logger = logging.getLogger(__name__)

# Canonical four-level names from the Architecture/Proposal documents. The
# administrator's rubric rows supply the actual bands + criteria; this list
# only guards the contract when a rubric is misconfigured (e.g. fewer rows).
KNOWN_LEVELS = ("Incomplete", "Partial", "Mostly Complete", "Complete")

ESSAY_GRADE_SCHEMA = {
    "name": "essay_grade",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "rubric_level": {"type": "string"},
            "score": {"type": "number"},
            "confidence": {"type": "number"},
            "matched_criteria": {
                "type": "array",
                "items": {"type": "string"},
            },
            "missing_concepts": {
                "type": "array",
                "items": {"type": "string"},
            },
            "evidence": {"type": "array", "items": {"type": "string"}},
            "explanation": {"type": "string"},
            "feedback": {"type": "string"},
        },
        "required": ["rubric_level", "score", "explanation"],
        "additionalProperties": False,
    },
}

_SYSTEM_PROMPT = (
    "You are a strict-but-fair database course grader. Grade ONLY against the "
    "supplied rubric. Do not reward verbosity, do not assume facts the "
    "student did not state, and do not award a rubric level unless its "
    "required criteria are met. Cite short verbatim evidence from the "
    "student's answer for every matched criterion and list the concepts that "
    "are missing. Output JSON only."
)


def _rubric_block(rubrics: list[Rubric]) -> str:
    lines = []
    for r in rubrics:
        lines.append(
            f"- {r.level_name}: score {r.min_score} to {r.max_score}. "
            f"Criteria: {r.criteria}"
        )
    return "\n".join(lines)


def _match_level(rubrics: list[Rubric], name: str) -> Optional[Rubric]:
    """Case/whitespace-insensitive match of the LLM's rubric_level."""
    want = " ".join(name.strip().lower().split())
    for r in rubrics:
        if " ".join(r.level_name.strip().lower().split()) == want:
            return r
    return None


def _to_decimal(value) -> Optional[Decimal]:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def grade_essay(
    question: Question,
    rubrics: list[Rubric],
    essay_text: str,
    llm: LLMService,
    *,
    identifiers=(),
) -> dict:
    """Call the provider, validate/clamp the result, return score + evidence.

    Raises LLMError on provider/config problems and on malformed or
    rubric-inconsistent output — callers map that to a safe failure.
    """
    user_prompt = (
        "QUESTION PROMPT:\n"
        f"{question.prompt}\n\n"
        "REFERENCE ANSWER (for calibration; the student need not match it "
        "verbatim):\n"
        f"{question.reference_answer or '(none provided)'}\n\n"
        f"MAXIMUM SCORE: {question.points}\n\n"
        "RUBRIC (four levels; pick exactly one, score must fall inside its "
        "band):\n"
        f"{_rubric_block(rubrics)}\n\n"
        "STUDENT ANSWER (identifiers redacted):\n"
        f"{essay_text}\n\n"
        'Return JSON: {"rubric_level": <level name exactly as given>, '
        '"score": <number within the level band>, "confidence": <0-1>, '
        '"matched_criteria": [...], "missing_concepts": [...], '
        '"evidence": [<quoted student text>], "explanation": "...", '
        '"feedback": "<constructive guidance>"}'
    )

    result = llm.generate_structured(
        "essay_grading",
        [
            ChatMessage("system", _SYSTEM_PROMPT),
            ChatMessage("user", user_prompt),
        ],
        json_schema=ESSAY_GRADE_SCHEMA,
    )

    return _validate_result(result, question, rubrics)


def _validate_result(
    result: dict, question: Question, rubrics: list[Rubric]
) -> dict:
    """Enforce the rubric contract on the parsed provider response."""
    if not isinstance(result, dict):
        raise LLMError(
            LLMError.INVALID_RESPONSE, "Essay grading returned a malformed result"
        )
    level = _match_level(rubrics, str(result.get("rubric_level", "")))
    if level is None:
        raise LLMError(
            LLMError.INVALID_RESPONSE,
            "Essay grading returned a rubric level outside the configured rubric",
        )
    score = _to_decimal(result.get("score"))
    if score is None:
        raise LLMError(
            LLMError.INVALID_RESPONSE, "Essay grading returned a non-numeric score"
        )
    # Clamp into the level band, then into the question's range — the admin's
    # bounds win over anything the provider claims.
    score = max(level.min_score, min(score, level.max_score))
    score = max(Decimal("0"), min(score, question.points))

    confidence = _to_decimal(result.get("confidence"))
    if confidence is not None:
        confidence = max(Decimal("0"), min(confidence, Decimal("1")))

    def _str_list(key) -> list[str]:
        v = result.get(key)
        if isinstance(v, list):
            return [str(x) for x in v]
        return []

    return {
        "score": score,
        "points_possible": question.points,
        "is_correct": level.level_name.strip().lower() == "complete",
        "grading_detail": {
            "grader": "llm_rubric",
            "question_type": "essay",
            "rubric_level": level.level_name,
            "level_band": [str(level.min_score), str(level.max_score)],
            "confidence": str(confidence) if confidence is not None else None,
            "matched_criteria": _str_list("matched_criteria"),
            "missing_concepts": _str_list("missing_concepts"),
            "evidence": _str_list("evidence"),
            "explanation": str(result.get("explanation", "")),
            "feedback": str(result.get("feedback", "")),
            "points_possible": str(question.points),
            "points_earned": str(score),
        },
    }


def submit_essay_answer(
    db: Session,
    session_id: int,
    learner: Account,
    payload: SubmitAnswerRequest,
    llm: LLMService,
) -> AttemptResult:
    """Grade a served essay attempt; persists essay_answer, score, evidence."""
    repo = AssessmentRepository(db)
    load_owned_active_session(repo, session_id, learner)
    attempt = load_served_attempt(repo, session_id, payload.question_id)
    if attempt.submitted_at is not None:
        raise AppError(409, "already_submitted", "This question was already answered")

    question = attempt.question
    if question is None:
        raise AppError(404, "question_not_found", "Question not found")
    if question.question_type != "essay":
        raise AppError(
            422,
            "unsupported_question_type",
            "Only essay answers are graded by this path",
        )
    if payload.essay_answer is None or not payload.essay_answer.strip():
        raise AppError(
            422, "empty_answer", "An essay answer is required for this question"
        )

    rubrics = repo.get_rubrics_for_question(question.question_id)
    if not rubrics:
        raise AppError(
            422,
            "rubric_not_configured",
            "This essay question has no rubric configured",
        )

    identifiers = [learner.email]
    if learner.profile and learner.profile.full_name:
        identifiers.append(learner.profile.full_name)
    sanitized = sanitize_learner_text(
        payload.essay_answer, identifiers=identifiers
    )

    try:
        result = grade_essay(
            question, rubrics, sanitized, llm, identifiers=identifiers
        )
    except LLMError as exc:
        raise exc.to_app_error()

    attempt.essay_answer = payload.essay_answer  # raw text stays inside DBCAS
    attempt.score = result["score"]
    attempt.grading_detail = result["grading_detail"]
    attempt.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)

    return AttemptResult(
        attempt_id=attempt.attempt_id,
        session_id=attempt.session_id,
        question_id=attempt.question_id,
        score=attempt.score,
        points_possible=result["points_possible"],
        is_correct=result["is_correct"],
        submitted_at=attempt.submitted_at,
    )

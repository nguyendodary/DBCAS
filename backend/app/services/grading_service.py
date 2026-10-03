"""Grading service — dispatches by question type.

* ``mcq`` — rule-based scoring against the verified answer key (Task 2.3).
* ``sql`` — sandboxed execution + semantic result comparison
  (sql_grading, Task 3.3).
* ``essay`` — four-level AI rubric scoring (Task 3.5).

All paths persist score + a standardized evidence record on the Attempt row.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, McqOption, Question
from ..repositories import AssessmentRepository
from ..schemas import AttemptResult, SubmitAnswerRequest
from .sandbox_runner import SandboxRunner
from .session_guard import load_owned_active_session, load_served_attempt


def score_mcq(
    question: Question,
    options: Sequence[McqOption],
    selected_option_id: Optional[int],
) -> dict:
    """Pure rule: compare the selected option with the answer key.

    Raises AppError(422) when the selected option does not belong to the
    question. An unanswered question (selected_option_id=None) scores 0.
    """
    correct = next((o for o in options if o.is_correct), None)
    if selected_option_id is None:
        is_correct = False
    else:
        selected = next((o for o in options if o.option_id == selected_option_id), None)
        if selected is None:
            raise AppError(
                422,
                "invalid_option",
                "Selected option does not belong to this question",
            )
        is_correct = bool(selected.is_correct)

    earned = question.points if is_correct else Decimal("0")
    return {
        "is_correct": is_correct,
        "score": earned,
        "points_possible": question.points,
        "grading_detail": {
            "grader": "answer_key",
            "question_type": "mcq",
            "selected_option_id": selected_option_id,
            "correct_option_id": correct.option_id if correct else None,
            "is_correct": is_correct,
            "points_possible": str(question.points),
            "points_earned": str(earned),
        },
    }


def submit_answer(
    db: Session,
    session_id: int,
    learner: Account,
    payload: SubmitAnswerRequest,
    runner: Optional[SandboxRunner] = None,
) -> AttemptResult:
    """Submit one answer inside a session; graded per the question's format.

    Attempts are created by the serving/adaptive flow; this operation only
    grades a previously served, still-pending attempt — which also enforces
    'question belongs to this session' and 'no duplicate submissions'.
    """
    from . import sql_grading  # local import: keeps sandbox deps out of MCQ path

    attempt = (
        AssessmentRepository(db).get_attempt(session_id, payload.question_id)
    )
    if attempt is not None and attempt.question is not None:
        qtype = attempt.question.question_type
        if qtype == "sql":
            if runner is None:
                raise AppError(503, "sandbox_unavailable", "SQL grading unavailable")
            return sql_grading.submit_sql_answer(
                db, session_id, learner, payload, runner
            )

    repo = AssessmentRepository(db)
    load_owned_active_session(repo, session_id, learner)
    now = datetime.now(timezone.utc)

    attempt = load_served_attempt(repo, session_id, payload.question_id)
    if attempt.submitted_at is not None:
        raise AppError(409, "already_submitted", "This question was already answered")

    question = attempt.question
    if question is None:
        raise AppError(404, "question_not_found", "Question not found")
    if question.question_type != "mcq":
        raise AppError(
            422,
            "unsupported_question_type",
            "This question type is not graded by this endpoint",
        )

    result = score_mcq(question, question.options, payload.selected_option_id)

    attempt.selected_option_id = payload.selected_option_id
    attempt.score = result["score"]
    attempt.grading_detail = result["grading_detail"]
    attempt.submitted_at = now
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

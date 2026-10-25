"""Grading service — dispatches by question type.

* ``mcq`` — rule-based scoring against the verified answer key (Task 2.3).
* ``sql`` — sandboxed execution + semantic result comparison
  (sql_grading, Task 3.3).
* ``essay`` — four-level AI rubric scoring (Task 3.5).

All paths persist score + a standardized evidence record on the Attempt row.
"""

from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Account, McqOption, Question
from ..schemas import AttemptResult, SubmitAnswerRequest
from .sandbox_runner import SandboxRunner


def score_mcq(
    question: Question,
    options: Sequence[McqOption],
    selected_option_id: Optional[int] = None,
    selected_option_ids: Optional[list[int]] = None,
) -> dict:
    """Full credit only for an exact match with the complete answer key."""
    selected = list(selected_option_ids) if selected_option_ids is not None else ([selected_option_id] if selected_option_id is not None else [])
    selected_set = set(selected)
    valid = {option.option_id for option in options}
    if len(selected) != len(selected_set) or not selected_set.issubset(valid):
        raise AppError(422, "invalid_option", "Selected options must be unique and belong to this question")
    correct = {option.option_id for option in options if option.is_correct}
    is_correct = bool(correct) and selected_set == correct
    earned = question.points if is_correct else Decimal("0")
    return {
        "is_correct": is_correct, "score": earned, "points_possible": question.points,
        "grading_detail": {
            "grader": "answer_key", "question_type": "mcq",
            "selected_option_id": next(iter(selected_set)) if len(selected_set) == 1 else None,
            "selected_option_ids": sorted(selected_set),
            "correct_option_id": next(iter(correct)) if len(correct) == 1 else None,
            "correct_option_ids": sorted(correct),
            "is_correct": is_correct,
            "points_possible": str(question.points), "points_earned": str(earned),
        },
    }


def submit_answer(
    db: Session,
    session_id: int,
    learner: Account,
    payload: SubmitAnswerRequest,
    runner: Optional[SandboxRunner] = None,
    llm=None,
) -> AttemptResult:
    """Submit one answer inside a session; graded per the question's format.

    Attempts are created by the serving/adaptive flow; this operation only
    grades a previously served, still-pending attempt — which also enforces
    'question belongs to this session' and 'no duplicate submissions'.
    """
    from .assessment_lifecycle import submit
    result = submit(db, session_id, learner, payload, runner, llm, idempotent=False)
    db.commit()
    return result

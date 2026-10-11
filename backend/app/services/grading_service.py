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

"""Generated grading metadata must survive database persistence unchanged."""
import pytest

from app.config import get_settings
from app.models import LlmCache, QuestionCandidate
from app.services.ai_admin_service import generate_candidates
from app.services.essay_grading import grade_essay
from app.services.llm import LLMError
from app.services.sandbox_runner import SandboxRunner
from test_governed_generation import fixture
from test_llm_release import _service, _essay, _rubrics, _grade_payload


@pytest.mark.parametrize("score", [.901, 10 ** 40])
def test_generated_essay_score_cannot_silently_round_at_persistence(db_session, score):
    with pytest.raises(LLMError):
        grade_essay(_essay(), _rubrics(), "3NF", _service(db_session, _grade_payload(score=score)))
    assert db_session.query(LlmCache).count() == 0


@pytest.mark.parametrize("defect", ["point_precision", "blank_rationale", "dataset_name_length"])
def test_invalid_generation_metadata_is_rejected_before_draft_or_cache(db_session, defect):
    kind = "sql" if defect == "dataset_name_length" else "mcq"
    admin, _, payload, item = fixture(db_session, kind)
    if defect == "point_precision":
        item["points"] = .015  # PostgreSQL NUMERIC(...,2) would change this value.
    elif defect == "blank_rationale":
        item["explanation"] = "   "
    else:
        item["datasets"][0]["dataset_name"] = "x" * 101
    with pytest.raises(LLMError):
        generate_candidates(db_session, payload, admin, _service(db_session, {"questions": [item]}), SandboxRunner(get_settings()))
    assert db_session.query(QuestionCandidate).count() == 0
    assert db_session.query(LlmCache).count() == 0

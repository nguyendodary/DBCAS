"""Bounded provider configuration, usage and real database cache regression."""
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.services.essay_grading import grade_essay
from test_llm_release import _service, _grade_payload, _rubrics


@pytest.mark.parametrize("key,value", [
    ("llm_timeout_seconds", 0), ("llm_timeout_seconds", float("inf")),
    ("llm_timeout_seconds", float("nan")), ("llm_max_retries", -1),
    ("llm_max_retries", 4), ("llm_backoff_seconds", -0.1),
])
def test_provider_policy_rejects_unbounded_configuration(key, value):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{key: value})


def test_essay_has_output_ceiling_and_rubric_aware_cache(db_session):
    seen = []
    llm = _service(db_session, _grade_payload(), seen=seen)
    question = SimpleNamespace(points=Decimal("1"), prompt="Explain 3NF", reference_answer="3NF")
    rubrics = _rubrics()
    first = grade_essay(question, rubrics, "3NF", llm)
    assert grade_essay(question, rubrics, "3NF", llm) == first
    assert len(seen) == 1 and seen[0]["max_tokens"] == 2048
    rubrics[-1].criteria += "; include a dependency example"
    grade_essay(question, rubrics, "3NF", llm)
    assert len(seen) == 2

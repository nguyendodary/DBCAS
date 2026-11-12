"""Terminal credential failures must not spend a second generation request."""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.llm.errors import LLMError
from app.services.practice_generation import generate_entries
from app.services.practice_service import PracticeStart


@pytest.mark.parametrize("code", [LLMError.AUTH_FAILED, LLMError.NOT_CONFIGURED])
def test_terminal_configuration_error_uses_fallback_without_another_request(code):
    class Provider:
        calls = 0

        def is_configured(self):
            return True

        def generate_structured(self, *args, **kwargs):
            self.calls += 1
            raise LLMError(code, "Unavailable configuration")

    provider = Provider()
    diagnostics = []
    concept = SimpleNamespace(concept_id=1, concept_code="SQL-SELECT", concept_name="SELECT", description="Projection")
    payload = PracticeStart(concept_ids=[1], difficulties=["EASY"], source="ai", question_count=1, request_id=uuid4())
    result = generate_entries([concept], payload, SimpleNamespace(account_id=1), None, provider, diagnostics=diagnostics)
    assert result == []  # Existing caller recovers using reviewed bank/template content.
    assert provider.calls == 1
    assert len(diagnostics) == 1
    assert diagnostics[0]["reason"] == code

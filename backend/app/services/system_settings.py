"""Read-only operational status for the admin system page.

There is no global result-flow switch.  Every practice session is graded by
the AI pipeline and then reviewed and approved by an administrator before the
official result is published.
"""
from ..models import SystemSetting  # noqa: F401  (legacy table, kept for history)


def status(db):
    from ..config import get_settings
    from .llm import LLMService
    settings = get_settings()
    return {"evaluator_configured": LLMService(settings).is_configured(),
            "prompt_builder_configured": bool(settings.prompt_builder_model_path),
            "fallback_available": True, "mode": "local", "database": "PostgreSQL 17",
            "pipeline": "Prompt Builder → Evaluator → Admin review"}

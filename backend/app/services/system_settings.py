"""One local system policy, snapshotted at the start of each practice."""
from datetime import datetime, timezone
from ..models import SystemSetting


def result_flow(db):
    row = db.get(SystemSetting, "result_flow")
    return row.value if row else "IMMEDIATE"


def update_flow(db, value, actor):
    row = db.get(SystemSetting, "result_flow", with_for_update=True)
    if row is None:
        row = SystemSetting(setting_key="result_flow", value=value)
        db.add(row)
    row.value, row.updated_by, row.updated_at = value, actor.account_id, datetime.now(timezone.utc)
    db.commit()
    return status(db)


def status(db):
    from ..config import get_settings
    from .llm import LLMService
    settings = get_settings()
    return {"result_flow": result_flow(db), "evaluator_configured": LLMService(settings).is_configured(),
            "prompt_builder_configured": bool(settings.prompt_builder_model_path),
            "fallback_available": True, "mode": "local", "database": "PostgreSQL 17", "pipeline": "Prompt Builder → Evaluator"}

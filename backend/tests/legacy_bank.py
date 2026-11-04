"""Explicit historical definitions for migration and immutable-version tests."""
import json
from copy import deepcopy
from pathlib import Path
from app.benchmark import import_pack as import_current_pack
from app.config import ROOT_DIR


def restore_archived_question(db, admin, runner, pack, *, translation_data):
    """Reconstruct a reviewed pre-upgrade row, without republishing it today.

    An old incomplete row cannot pass the current publication API. Migration
    tests must still reproduce that exact database state and frozen history.
    This helper is test-only and accepts only a registered archived definition.
    """
    from app.models import Question
    from app.schemas import QuestionUpsertRequest
    from app.services.question_service import create_question
    assert len(pack["questions"]) == 1
    item = pack["questions"][0]
    before = json.loads((ROOT_DIR / "db/reviewed_question_before.json").read_text(encoding="utf-8"))
    assert item == before[item["key"]]["question"]
    curriculum = import_current_pack(db, admin, runner, {**pack, "questions": [], "assessments": []},
                                     translation_data=translation_data)
    ids = curriculum["concept_ids"]
    payload = QuestionUpsertRequest(**{**item,
        "concept_ids": [ids[code] for code in item["concept_codes"]],
        "required_concept_ids": [ids[code] for code in item.get("required_concept_codes", [])],
        "translations": [{"locale": "vi", **translation_data["questions"][item["key"]]}]})
    draft = create_question(db, payload, admin)
    question = db.get(Question, draft.question_id)
    question.status = item.get("status", "validated")
    db.commit()
    return question


def import_pack(db, admin, runner, pack=None, **options):
    pack = deepcopy(pack) if pack is not None else json.loads((ROOT_DIR / "db/benchmark_pack.json").read_text(encoding="utf-8"))
    definitions = json.loads((Path(__file__).parent / "fixtures/legacy_assessment_definitions.json").read_text(encoding="utf-8"))
    key = pack.get("scope")
    if key not in definitions and any(c.get("concept_code") == "SQL-DML-KNOW" for c in pack["concepts"]):
        key = "sql_knowledge_pack.json"
    pack["assessments"] = definitions.get(key, [])
    return import_current_pack(db, admin, runner, pack, **options)

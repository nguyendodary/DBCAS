"""Additive, history-safe upgrade of the versioned curated bank.

Only an exact reviewed prior definition may be replaced. Used questions get a
new version; administrator edits and all attempt snapshots stay untouched.
The identity registry makes subsequent initialization a read-only no-op.
"""
from collections import defaultdict
from decimal import Decimal
from hashlib import sha256
import json

from sqlalchemy import select

from ..config import ROOT_DIR
from ..models import (Concept, CourseLearningOutcome, CloConcept, ConceptDependency,
                      Question, QuestionConcept, McqOption, SqlTestDataset, Rubric, SystemSetting)
from ..repositories import QuestionRepository, SecurityRepository
from ..schemas import QuestionUpsertRequest
from ..validate_bank import load_corpus
from .question_validator import bank_problems
from .question_service import _apply_children, upsert_question_translations

REGISTRY_KEY = "curated-bank-identities-v1"
_FIELDS = ("question_type", "original_locale", "prompt", "reference_answer", "explanation",
           "difficulty_level", "points", "tags", "source_refs")


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def _payload(item, ids, translated=None):
    return QuestionUpsertRequest(**{**item,
        "concept_ids": [ids[c] for c in item["concept_codes"]],
        "required_concept_ids": [ids[c] for c in item.get("required_concept_codes", [])],
        "translations": [{"locale": "vi", **translated}] if translated else []})


def _normalized(payload):
    result = payload.model_dump(mode="json")
    result["points"] = str(Decimal(result["points"]).normalize())
    for rubric in result["rubrics"]:
        for field in ("min_score", "max_score"):
            rubric[field] = str(Decimal(rubric[field]).normalize())
    for field in ("concept_ids", "required_concept_ids", "options", "datasets", "rubrics", "translations"):
        result[field] = sorted(result[field], key=lambda value: json.dumps(value, sort_keys=True))
    return result


def _actual(question):
    from .question_localization import translation_is_current
    return QuestionUpsertRequest(**{
        **{field: getattr(question, field) for field in _FIELDS},
        "options": [{field: getattr(row, field) for field in ("option_label", "option_text", "is_correct")} for row in question.options],
        "datasets": [{field: getattr(row, field) for field in ("dataset_name", "setup_sql", "expected_result", "is_edge_case")} for row in question.datasets],
        "rubrics": [{field: getattr(row, field) for field in ("level_name", "min_score", "max_score", "criteria")} for row in question.rubrics],
        "translations": [{field: getattr(row, field) for field in ("locale", "prompt", "explanation", "option_texts", "rubrics")}
                         for row in question.translations if translation_is_current(question, row)],
        "concept_ids": [t.concept_id for t in question.concept_tags if t.confirmed],
        "required_concept_ids": [t.concept_id for t in question.concept_tags if t.confirmed and t.is_required]})


def _curriculum(db, packs, admin):
    concepts = {c.concept_code: c for c in db.scalars(select(Concept))}
    for pack in packs:
        for item in pack["concepts"]:
            code = item["concept_code"]
            if code not in concepts:
                concepts[code] = Concept(**item)
                db.add(concepts[code])
    db.flush()
    ids = {code: row.concept_id for code, row in concepts.items()}
    clos = {c.clo_code: c for c in db.scalars(select(CourseLearningOutcome))}
    links = {(c.clo_id, c.concept_id) for c in db.scalars(select(CloConcept))}
    edges = {(e.concept_id, e.prerequisite_concept_id) for e in db.scalars(select(ConceptDependency))}
    for pack in packs:
        for item in pack["clos"]:
            code = item["clo_code"]
            if code not in clos:
                clos[code] = CourseLearningOutcome(clo_code=code, title=item["title"],
                    description=item.get("description"), created_by=admin.account_id)
                db.add(clos[code])
                db.flush()
            for concept in item["concept_codes"]:
                pair = clos[code].clo_id, ids[concept]
                if pair not in links:
                    db.add(CloConcept(clo_id=pair[0], concept_id=pair[1], mapping_source="admin", status="confirmed"))
                    links.add(pair)
        for concept, prerequisites in pack["dependencies"].items():
            for prerequisite in prerequisites:
                pair = ids[concept], ids[prerequisite]
                if pair not in edges:
                    db.add(ConceptDependency(concept_id=pair[0], prerequisite_concept_id=pair[1]))
                    edges.add(pair)
    db.flush()
    return ids


def sync_bank(db, admin, *, packs=None, translations=None):
    if not any(role.role_name == "Administrator" for role in admin.roles):
        from ..errors import AppError
        raise AppError(403, "admin_required", "The curated bank requires an administrator")
    if packs is None:
        packs, translations = load_corpus()
    translations = translations or {}
    revision = _digest([packs, translations])
    SecurityRepository(db).lock("curated-bank-upgrade")
    registry = db.get(SystemSetting, REGISTRY_KEY)
    if registry and registry.value.get("revision") == revision:
        return {"added": 0, "reviewed": 0, "preserved_edits": 0}
    failures = bank_problems(packs, translations)
    if failures:
        raise ValueError(f"Curated bank failed validation: {list(failures)[:5]}")
    from .practice_corpus import RESULTS_PATH, result_key
    from .sql_result import parse_expected, compare
    verified = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))["results"]
    for pack in packs:
        for item in pack["questions"]:
            if item["question_type"] == "sql":
                for dataset in item["datasets"]:
                    actual = verified.get(result_key(dataset["setup_sql"], item["reference_answer"]))
                    if actual is None or compare(actual["columns"], actual["rows"], parse_expected(dataset["expected_result"]), actual["column_types"]).status != "passed":
                        raise ValueError(f"SQL requires actual PostgreSQL verification before seed: {item['key']}")
    ids = _curriculum(db, packs, admin)
    repo = QuestionRepository(db)
    existing = list(db.scalars(select(Question).where(Question.source == "bank").options(*repo._detail_loads())))
    by_prompt = defaultdict(list)
    for question in existing:
        by_prompt[question.prompt].append(question)
    identities = dict(registry.value.get("questions", {})) if registry else {}
    before = json.loads((ROOT_DIR / "db/reviewed_question_before.json").read_text(encoding="utf-8"))
    pending, added, reviewed, preserved = [], 0, 0, 0
    for pack in packs:
        for item in pack["questions"]:
            key = item["key"]
            translated = translations.get(key)
            payload = _payload(item, ids, translated)
            wanted = _normalized(payload)
            previous = identities.get(key)
            if previous and previous.get("hash") == _digest(wanted):
                # Owner edits after the previous seed are deliberately preserved.
                continue
            candidates = by_prompt.get(item["prompt"], [])
            old = before.get(key)
            if old and old["question"]["prompt"] != item["prompt"]:
                candidates = [*candidates, *by_prompt.get(old["question"]["prompt"], [])]
            question = next((q for q in candidates if _normalized(_actual(q)) == wanted), None)
            if question is None and old:
                old_payload = _normalized(_payload(old["question"], ids, old.get("translation")))
                question = next((q for q in candidates if _normalized(_actual(q)) == old_payload), None)
                if question:
                    refs = repo.reference_counts(question.question_id)
                    if any(refs.get(field) for field in ("attempt", "session_question_plan", "adaptive_inventory")):
                        question = repo.clone_for_edit(question)
                    for field in _FIELDS:
                        value = getattr(payload, field)
                        setattr(question, field, [r.model_dump() for r in value] if field == "source_refs" else value)
                    _apply_children(repo, db, question, payload)
                    db.expire(question, ["options", "datasets", "rubrics", "concept_tags", "translations"])
                    upsert_question_translations(db, question, payload.translations)
                    question.status = item.get("status", "validated")
                    reviewed += 1
            if question is None:
                if candidates:
                    preserved += 1
                question = Question(**{field: ([r.model_dump() for r in getattr(payload, field)] if field == "source_refs" else getattr(payload, field))
                                       for field in _FIELDS}, source="bank", status=item.get("status", "validated"), created_by=admin.account_id)
                db.add(question)
                pending.append((question, payload, key, wanted))
                added += 1
            else:
                identities[key] = {"id": question.question_id, "hash": _digest(wanted)}
    db.flush()
    for question, payload, key, wanted in pending:
        qid = question.question_id
        db.add_all([QuestionConcept(question_id=qid, concept_id=cid, tag_source="admin", confirmed=True,
                                   is_required=cid in payload.required_concept_ids) for cid in payload.concept_ids])
        db.add_all([McqOption(question_id=qid, **o.model_dump()) for o in payload.options])
        db.add_all([SqlTestDataset(question_id=qid, **d.model_dump()) for d in payload.datasets])
        db.add_all([Rubric(question_id=qid, **r.model_dump()) for r in payload.rubrics])
        identities[key] = {"id": qid, "hash": _digest(wanted)}
    db.flush()
    # Translation fingerprints require the actual inserted canonical children.
    translated_pending = [(q, p) for q, p, _, _ in pending if p.translations]
    if translated_pending:
        rows = {q.question_id: q for q in db.scalars(select(Question).where(Question.question_id.in_([q.question_id for q, _ in translated_pending])).options(*repo._detail_loads()))}
        for question, payload in translated_pending:
            upsert_question_translations(db, rows[question.question_id], payload.translations)
    if registry is None:
        registry = SystemSetting(setting_key=REGISTRY_KEY, updated_by=admin.account_id)
        db.add(registry)
    registry.value = {"revision": revision, "questions": identities}
    db.flush()
    return {"added": added, "reviewed": reviewed, "preserved_edits": preserved}

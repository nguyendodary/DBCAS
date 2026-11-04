"""Bounded live generation with the same content contract as curated sources."""
from copy import deepcopy
from collections import Counter
from math import ceil
from functools import lru_cache
from threading import Lock
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

from .corpus_review import reference
from .llm.provider import ChatMessage
from .practice_config import DIFFICULTY_LEVELS, MAX_QUESTIONS, QUESTION_TYPES, difficulty_band
from .practice_corpus import template_pack, RESULTS_PATH, result_key
from .practice_recipes import RECIPES
from .practice_selection import Candidate, Catalog
from .prompt_builder import canonical
from .question_validator import question_problems, fingerprint

GENERATION_ATTEMPTS = 2
_TEMPLATE_LOCK = Lock()


def levels(payload):
    return [level for band in payload.difficulties for level in DIFFICULTY_LEVELS[band]]


class GeneratedOption(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    text: str = Field(min_length=1, max_length=2000)
    correct: bool


class GeneratedRubric(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    level_name: str = Field(min_length=1, max_length=40)
    min_score: float
    max_score: float
    criteria: str = Field(min_length=1, max_length=2000)


class GeneratedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    concept_ids: list[int] = Field(min_length=1, max_length=20)
    difficulty_level: int = Field(ge=1, le=5)
    question_type: Literal["mcq", "sql", "essay"]
    prompt: str = Field(min_length=8, max_length=6000)
    explanation: str = Field(min_length=8, max_length=8000)
    source_refs: list[str] = Field(min_length=1, max_length=4)
    reference_answer: str = Field(min_length=1, max_length=8000)
    points: int = Field(ge=1, le=10)
    options: list[GeneratedOption] = Field(max_length=4)
    setup_sql: str | None = Field(max_length=12000)
    edge_setup_sql: str | None = Field(default=None, max_length=12000)
    rubrics: list[GeneratedRubric] = Field(max_length=4)


def canonical_generated(item, datasets=()):
    return {"question_type": item["question_type"], "original_locale": "vi", "prompt": item["prompt"],
        "explanation": item["explanation"], "reference_answer": item["reference_answer"],
        "source_refs": [{"url": url} for url in item["source_refs"]], "points": item["points"],
        "difficulty_level": item["difficulty_level"], "concept_ids": item["concept_ids"],
        "options": [{"option_label": chr(65+i), "option_text": o["text"], "is_correct": o["correct"]} for i, o in enumerate(item["options"])],
        "rubrics": item["rubrics"], "datasets": list(datasets)}


@lru_cache(maxsize=1)
def _verified_sql_results():
    import json
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    if data.get("engine") != "PostgreSQL 17" or data.get("executions_per_fixture") != 2:
        raise ValueError("Invalid PostgreSQL verification manifest")
    return data["results"]


def validate_generated(raw, concepts, payload, runner, *, deadline=None):
    if (not isinstance(raw, dict) or set(raw) != {"questions"} or not isinstance(raw["questions"], list)
            or len(raw["questions"]) != payload.question_count):
        raise ValueError("generation_count")
    allowed, allowed_levels = {c.concept_id for c in concepts}, set(levels(payload))
    parsed, seen = [], set()
    for value in raw["questions"]:
        if deadline is not None and time.monotonic() >= deadline:
            raise ValueError("generation_deadline")
        try:
            item = GeneratedQuestion.model_validate(value).model_dump()
        except ValidationError as exc:
            raise ValueError("generation_schema") from exc
        ids = item["concept_ids"]
        if len(set(ids)) != len(ids) or not set(ids) <= allowed or item["difficulty_level"] not in allowed_levels:
            raise ValueError("generation_scope")
        if item["question_type"] != "sql" and (item["setup_sql"] or item["edge_setup_sql"]):
            raise ValueError("generation_type_fields")
        if item["question_type"] == "mcq":
            if (len(item["options"]) != 4 or sum(o["correct"] for o in item["options"]) != 1
                    or item["reference_answer"].strip() != next(o["text"].strip() for o in item["options"] if o["correct"])):
                raise ValueError("generation_mcq")
        signature = fingerprint(item["prompt"])
        if signature in seen:
            raise ValueError("generation_duplicate")
        seen.add(signature)
        datasets = []
        if item["question_type"] == "sql":
            from .dataset_setup import validated_setup_statements
            from .sql_validator import validate_learner_sql
            if validate_learner_sql(item["reference_answer"]) or not item["setup_sql"] or not item["edge_setup_sql"] or runner is None:
                raise ValueError("generation_sql")
            # Validate both seeds before opening a privileged provisioning connection.
            for setup in (item["setup_sql"], item["edge_setup_sql"]):
                validated_setup_statements(setup)
            for edge, setup in ((False, item["setup_sql"]), (True, item["edge_setup_sql"])):
                if deadline is not None and time.monotonic() >= deadline:
                    raise ValueError("generation_deadline")
                cached = _verified_sql_results().get(result_key(setup, item["reference_answer"]))
                if cached is not None:
                    expected = deepcopy(cached)
                else:
                    schema = runner.provision_dataset(setup)
                    try:
                        first = runner.execute(item["reference_answer"], schema=schema)
                        second = runner.execute(item["reference_answer"], schema=schema)
                        if (not first.success or not second.success or not first.rows
                                or first.columns != second.columns or first.rows != second.rows):
                            raise ValueError("generation_sql_execution")
                        expected = {"columns": first.columns, "rows": first.rows, "column_types": first.column_types}
                    finally:
                        runner.drop_dataset(schema)
                datasets.append({"dataset_name": "Generated edge" if edge else "Generated primary", "setup_sql": setup,
                                 "expected_result": expected, "is_edge_case": edge})
        errors = question_problems(canonical_generated(item, datasets), known_concepts=allowed)
        if errors:
            raise ValueError("generation_content:" + errors[0])
        item["_datasets"] = datasets
        parsed.append(item)
    return parsed


def wire_question(question, ids):
    return {"concept_ids": [ids[code] for code in question["concept_codes"]],
        "difficulty_level": question["difficulty_level"], "question_type": question["question_type"],
        "prompt": question["prompt"], "explanation": question["explanation"],
        "reference_answer": (next(o["option_text"] for o in question["options"] if o["is_correct"])
                             if question["question_type"] == "mcq" else question["reference_answer"]),
        "points": int(question["points"]), "source_refs": [r["url"] for r in question["source_refs"]],
        "options": [{"text": o["option_text"], "correct": o["is_correct"]} for o in question.get("options", [])],
        "setup_sql": question["datasets"][0]["setup_sql"] if question["question_type"] == "sql" else None,
        "edge_setup_sql": question["datasets"][1]["setup_sql"] if question["question_type"] == "sql" else None,
        "rubrics": [{**r, "min_score": float(r["min_score"]), "max_score": float(r["max_score"])} for r in question.get("rubrics", [])]}


def concept_codes(concepts):
    return {(getattr(c, "concept_code", None) or getattr(c, "concept_name", "")): c.concept_id for c in concepts}


@lru_cache(maxsize=1)
def _build_template_metadata():
    candidates = []
    for q in template_pack()["questions"]:
        key = "template:" + q["key"]
        candidates.append(Candidate(key, q["question_type"], q["difficulty_level"], frozenset(q["concept_codes"]), key,
                                    fingerprint(q["prompt"]), q, "template"))
    return tuple(candidates)


def template_candidates(concepts):
    ids = concept_codes(concepts)
    # lru_cache alone allows concurrent cold misses to build the entire bank
    # more than once. Keep that peak allocation bounded in the fake provider.
    with _TEMPLATE_LOCK:
        metadata = _build_template_metadata()
    return [Candidate(c.identity, c.kind, c.level, frozenset(ids[code] for code in c.concepts), c.family, c.signature, c.value, "template")
            for c in metadata if c.concepts <= ids.keys()]


def validated_template(question, concepts):
    ids = concept_codes(concepts)
    item = wire_question(question, ids)
    item["_datasets"] = deepcopy(question.get("datasets", []))
    # The exact fixture/query has recorded double execution in template_pack;
    # apply the shared schema/content gate only to the chosen questions.
    if question_problems(canonical_generated(item, item["_datasets"]), known_concepts=set(ids.values())):
        raise ValueError("Invalid deterministic template")
    return item


def template_questions(concepts, payload):
    """Deterministic fake-provider equivalent; uses real reviewed case content."""
    picks = Catalog(template_candidates(concepts)).plan(payload.concept_ids, payload.difficulties, limit=payload.question_count)
    if len(picks) != payload.question_count:
        raise ValueError("No supported deterministic content for these concepts")
    return [{k: v for k, v in validated_template(p.candidate.value, concepts).items() if not k.startswith("_")} for p in picks]


def generate_entries(concepts, payload, learner, runner, llm):
    if not llm or not llm.is_configured():
        return []
    request_data = {"concepts": [{"id": c.concept_id, "code": getattr(c, "concept_code", c.concept_name),
                                 "name": c.concept_name, "description": c.description} for c in concepts],
                    "difficulty_levels": levels(payload), "count": payload.question_count,
                    "documentation_urls": [reference(RECIPES[c.concept_code].document)["url"] for c in concepts if getattr(c, "concept_code", None) in RECIPES]}
    prompt = ("Tạo câu hỏi cơ sở dữ liệu bằng tiếng Việt theo schema JSON và đúng phạm vi. Cân bằng khái niệm, độ khó, MCQ/SQL/essay. "
        "Mỗi câu có explanation và source_refs là URL chính thức https://www.postgresql.org/docs/18/. MCQ đúng một trong 4 đáp án, reference_answer khớp đáp án đó. "
        "SQL chỉ SELECT với hai fixture setup_sql/edge_setup_sql chỉ CREATE TABLE/VIEW và INSERT VALUES; kết quả chính phải có dòng và xác định. "
        "Không gọi catalog, thời gian hiện tại, random hoặc hàm có tác dụng phụ. Chỉ sql có fixture; mcq/essay đặt cả hai null. "
        "Tự luận có mẫu trả lời và bốn rubric Incomplete, Partial, Mostly Complete, Complete liên tục đến 0.01. Không tạo câu mô tả khái niệm đánh số. "
        + canonical(request_data))
    batch = create_model("QuestionBatch", questions=(list[GeneratedQuestion], ...), __config__=ConfigDict(extra="forbid"))
    retained = []
    deadline = time.monotonic() + 24
    for attempt in range(GENERATION_ATTEMPTS):
        if time.monotonic() >= deadline:
            break
        validated = None
        def validate_batch(raw):
            nonlocal validated
            count = len(raw.get("questions", [])) if isinstance(raw, dict) else 0
            if not 1 <= count <= payload.question_count:
                raise ValueError("generation_count")
            validated = validate_generated(raw, concepts, payload.model_copy(update={"question_count": count}), runner, deadline=deadline)
            if count != payload.question_count:
                retained.extend(validated)
                raise ValueError("generation_partial")
            kinds = Counter(q["question_type"] for q in validated)
            if max(kinds[k] for k in QUESTION_TYPES)-min(kinds[k] for k in QUESTION_TYPES) > 1:
                raise ValueError("generation_type_balance")
            band_counts = Counter(difficulty_band(q["difficulty_level"]) for q in validated)
            concept_counts = Counter(cid for q in validated for cid in q["concept_ids"])
            if any(band_counts[b] > ceil(count/len(payload.difficulties)) for b in payload.difficulties):
                raise ValueError("generation_difficulty_balance")
            if any(concept_counts[cid] > ceil(count/len(payload.concept_ids)) for cid in payload.concept_ids):
                raise ValueError("generation_concept_balance")
            return raw
        try:
            raw = llm.generate_structured("practice_generation", [ChatMessage("user", prompt)],
                json_schema={"name": "practice_questions", "strict": True, "schema": batch.model_json_schema()},
                max_tokens=12000, context_version=f"practice-v2:{learner.account_id}:{payload.request_id}:{attempt}", validator=validate_batch)
            if validated is None:
                validate_batch(raw)  # deterministic injected providers obey the same contract
            return validated
        except Exception:
            # The batch has not been persisted. Invalid output is never cached
            # by the domain validator; only fully valid partial batches survive.
            continue
    return retained[:MAX_QUESTIONS]

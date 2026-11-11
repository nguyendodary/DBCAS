"""Bounded live generation with the same content contract as curated sources."""
from copy import deepcopy
from collections import Counter
from math import ceil
from functools import lru_cache
from threading import Lock
import logging
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
LOG = logging.getLogger(__name__)


class GenerationRejected(ValueError):
    """A batch rejection with a stable, secret-free diagnostic payload."""

    def __init__(self, code, *, question_type=None, excerpt=None, index=None):
        super().__init__(code)
        self.code = code
        self.question_type = question_type
        self.excerpt = excerpt
        self.index = index


def levels(payload):
    return [level for band in payload.difficulties for level in DIFFICULTY_LEVELS[band]]


def type_targets(count):
    """Balanced MCQ/SQL/essay counts for the requested total (positive kinds only)."""
    targets = {kind: count // len(QUESTION_TYPES) + (index < count % len(QUESTION_TYPES))
               for index, kind in enumerate(QUESTION_TYPES)}
    return {kind: value for kind, value in targets.items() if value}


def ai_type_targets(count):
    """AI provides every non-SQL question; SQL always comes from the bank."""
    targets = type_targets(count)
    targets.pop("sql", None)
    return targets


def _shape(value):
    if isinstance(value, dict):
        keys = ",".join(sorted(value)[:10])
        return f"object keys={keys}" if keys else "object"
    if isinstance(value, list):
        return f"list[{len(value)}]"
    return type(value).__name__


def normalize_batch(raw):
    """Accept reasonable root variants; per-question validation stays strict."""
    if isinstance(raw, list):
        return {"questions": raw}
    if isinstance(raw, dict):
        questions = raw.get("questions")
        if isinstance(questions, list):
            return {"questions": questions}
        for key in ("items", "data", "result"):
            nested = raw.get(key)
            if isinstance(nested, list):
                return {"questions": nested}
            if isinstance(nested, dict) and isinstance(nested.get("questions"), list):
                return {"questions": nested["questions"]}
    return raw


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


class GeneratedAIQuestion(GeneratedQuestion):
    """Provider contract for source=ai: SQL is bank-only."""
    question_type: Literal["mcq", "essay"]


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


def validate_generated(raw, concepts, payload, runner, *, deadline=None, allowed_types=None, expected_types=None):
    raw = normalize_batch(raw)
    if (not isinstance(raw, dict) or not isinstance(raw.get("questions"), list)
            or len(raw["questions"]) != payload.question_count):
        raise GenerationRejected("generation_count", excerpt=_shape(raw))
    allowed, allowed_levels = {c.concept_id for c in concepts}, set(levels(payload))
    parsed, seen = [], set()
    for index, value in enumerate(raw["questions"]):
        if deadline is not None and time.monotonic() >= deadline:
            raise GenerationRejected("generation_deadline", index=index)
        question_type = value.get("question_type") if isinstance(value, dict) else None
        try:
            item = GeneratedQuestion.model_validate(value).model_dump()
        except ValidationError as exc:
            raise GenerationRejected("generation_schema", question_type=question_type,
                                     excerpt=_shape(value), index=index) from exc
        ids = item["concept_ids"]
        if len(set(ids)) != len(ids) or not set(ids) <= allowed:
            raise GenerationRejected("generation_scope", question_type=item["question_type"],
                                     excerpt="concept_ids", index=index)
        if item["difficulty_level"] not in allowed_levels:
            raise GenerationRejected("generation_scope", question_type=item["question_type"],
                                     excerpt="difficulty_level", index=index)
        if allowed_types is not None and item["question_type"] not in allowed_types:
            raise GenerationRejected("generation_type_source", question_type=item["question_type"],
                                     excerpt="question_type", index=index)
        if item["question_type"] != "sql" and (item["setup_sql"] or item["edge_setup_sql"]):
            raise GenerationRejected("generation_type_fields", question_type=item["question_type"],
                                     excerpt="setup_sql", index=index)
        if item["question_type"] == "mcq":
            if len(item["options"]) != 4:
                raise GenerationRejected("generation_mcq", question_type="mcq",
                                         excerpt=f"options={len(item['options'])}", index=index)
            if sum(o["correct"] for o in item["options"]) != 1:
                raise GenerationRejected("generation_mcq", question_type="mcq",
                                         excerpt="correct_count", index=index)
            if item["reference_answer"].strip() != next(o["text"].strip() for o in item["options"] if o["correct"]):
                raise GenerationRejected("generation_mcq", question_type="mcq",
                                         excerpt="reference_answer", index=index)
        signature = fingerprint(item["prompt"])
        if signature in seen:
            raise GenerationRejected("generation_duplicate", question_type=item["question_type"],
                                     excerpt="prompt", index=index)
        seen.add(signature)
        datasets = []
        if item["question_type"] == "sql":
            from .dataset_setup import validated_setup_statements
            from .sql_validator import validate_learner_sql
            if validate_learner_sql(item["reference_answer"]):
                raise GenerationRejected("generation_sql_syntax", question_type="sql",
                                         excerpt="reference_answer", index=index)
            if not item["setup_sql"] or not item["edge_setup_sql"]:
                raise GenerationRejected("generation_sql_fixture", question_type="sql",
                                         excerpt="setup_sql", index=index)
            if runner is None:
                raise GenerationRejected("generation_sql_fixture", question_type="sql",
                                         excerpt="runner", index=index)
            # Validate both seeds before opening a privileged provisioning connection.
            for setup in (item["setup_sql"], item["edge_setup_sql"]):
                try:
                    validated_setup_statements(setup)
                except ValueError as exc:
                    raise GenerationRejected("generation_sql_fixture", question_type="sql",
                                             excerpt=str(exc)[:120], index=index) from exc
            for edge, setup in ((False, item["setup_sql"]), (True, item["edge_setup_sql"])):
                if deadline is not None and time.monotonic() >= deadline:
                    raise GenerationRejected("generation_deadline", question_type="sql", index=index)
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
                            raise GenerationRejected("generation_sql_execution", question_type="sql",
                                                     excerpt="empty_or_nondeterministic", index=index)
                        expected = {"columns": first.columns, "rows": first.rows, "column_types": first.column_types}
                    finally:
                        runner.drop_dataset(schema)
                datasets.append({"dataset_name": "Generated edge" if edge else "Generated primary", "setup_sql": setup,
                                 "expected_result": expected, "is_edge_case": edge})
        errors = question_problems(canonical_generated(item, datasets), known_concepts=allowed)
        if errors:
            raise GenerationRejected("generation_content", question_type=item["question_type"],
                                     excerpt=str(errors[0]).split(":", 1)[0][:60], index=index)
        item["_datasets"] = datasets
        parsed.append(item)
    if expected_types is not None:
        actual = Counter(item["question_type"] for item in parsed)
        if actual != expected_types:
            raise GenerationRejected("generation_type_mix", excerpt=dict(actual))
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


def template_questions(concepts, payload, *, kinds=None, type_targets_override=None):
    """Deterministic fake-provider equivalent; uses real reviewed case content."""
    candidates = template_candidates(concepts)
    if kinds is not None:
        candidates = [c for c in candidates if c.kind in set(kinds)]
    if type_targets_override:
        # One joint plan keeps the requested type mix while spreading the
        # batch across difficulty bands; separate per-kind plans can put every
        # pick in the same band and fail the strict generation balance rule.
        wanted = Counter({kind: target for kind, target in type_targets_override.items() if target})
        picks = Catalog(c for c in candidates if c.kind in wanted).plan(
            payload.concept_ids, payload.difficulties, limit=sum(wanted.values()))
        if Counter(p.candidate.kind for p in picks) != wanted:
            raise ValueError("No supported deterministic content for these concepts")
    else:
        picks = Catalog(candidates).plan(payload.concept_ids, payload.difficulties, limit=payload.question_count)
    if len(picks) != payload.question_count:
        raise ValueError("No supported deterministic content for these concepts")
    return [{k: v for k, v in validated_template(p.candidate.value, concepts).items() if not k.startswith("_")} for p in picks]


def _reason_code(exc):
    if isinstance(exc, GenerationRejected):
        code = exc.code
        if code == "generation_schema":
            return "schema"
        if code in ("generation_mcq", "generation_mcq_options"):
            return "mcq_options"
        if code == "generation_sql_syntax":
            return "sql_syntax"
        if code == "generation_sql_fixture":
            return "sql_fixture"
        if code == "generation_sql_execution":
            return "sql_empty_output" if exc.excerpt == "empty_or_nondeterministic" else "sql_fixture"
        if code == "generation_scope":
            return "difficulty_mismatch" if exc.excerpt == "difficulty_level" else "out_of_scope_concept"
        if code == "generation_duplicate":
            return "duplicate"
        if code in ("generation_count", "generation_type_mix", "generation_type_balance",
                    "generation_difficulty_balance", "generation_concept_balance", "generation_partial"):
            return "count"
        if code == "generation_deadline":
            return "timeout"
        if code == "generation_type_source":
            return "type_source"
        if code == "generation_type_fields":
            return "type_fields"
        return "content"
    from .llm.errors import LLMError
    import httpx
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)) or (
            isinstance(exc, LLMError) and exc.code == LLMError.TIMEOUT):
        return "timeout"
    if isinstance(exc, LLMError):
        if exc.code == LLMError.INVALID_RESPONSE:
            return getattr(exc, "reason_code", None) or "json_parse"
        return "http_error"
    return "provider_or_validation"


def _diagnostic(attempt, exc):
    if isinstance(exc, GenerationRejected):
        question_type, excerpt, index = exc.question_type, exc.excerpt, exc.index
        reason = exc.code
    else:
        question_type, excerpt, index = None, type(exc).__name__, None
        from .llm.errors import LLMError
        reason = exc.code if isinstance(exc, LLMError) else "provider_or_validation"
    return {"attempt": attempt, "code": _reason_code(exc), "reason": reason,
            "question_type": question_type, "index": index, "excerpt": excerpt}


def generate_entries(concepts, payload, learner, runner, llm, diagnostics=None):
    if not llm or not llm.is_configured():
        return []
    targets = ai_type_targets(payload.question_count)
    ai_count = sum(targets.values())
    if ai_count < 1:
        return []
    request_data = {"concepts": [{"id": c.concept_id, "code": getattr(c, "concept_code", c.concept_name),
                                 "name": c.concept_name, "description": c.description} for c in concepts],
                    "difficulty_levels": levels(payload), "count": ai_count,
                    "type_counts": targets,
                    "sql_from_bank": payload.question_count - ai_count,
                    "documentation_urls": [reference(RECIPES[c.concept_code].document)["url"] for c in concepts if getattr(c, "concept_code", None) in RECIPES]}
    prompt = ("Tạo câu hỏi cơ sở dữ liệu bằng tiếng Việt theo schema JSON và đúng phạm vi. "
        "Chỉ tạo MCQ và tự luận; câu SQL do ngân hàng đã kiểm chứng cung cấp nên không tạo question_type sql. Cân bằng khái niệm và độ khó. "
        "Mỗi câu có explanation và source_refs là URL chính thức https://www.postgresql.org/docs/18/. MCQ đúng một trong 4 đáp án, reference_answer khớp đáp án đó. "
        "Phải đúng số câu từng loại trong type_counts. "
        "Không gọi catalog, thời gian hiện tại, random hoặc hàm có tác dụng phụ. mcq/essay đặt setup_sql và edge_setup_sql là null. "
        "Tự luận có mẫu trả lời và bốn rubric Incomplete, Partial, Mostly Complete, Complete liên tục đến 0.01, không chung điểm biên. Ví dụ points=1: [0,0.24], [0.25,0.49], [0.50,0.74], [0.75,1]. Không tạo câu mô tả khái niệm đánh số. "
        + canonical(request_data))
    batch = create_model("QuestionBatch", questions=(list[GeneratedAIQuestion], ...), __config__=ConfigDict(extra="forbid"))
    retained = []
    deadline = time.monotonic() + 120
    for attempt in range(GENERATION_ATTEMPTS):
        if time.monotonic() >= deadline:
            break
        validated = None
        def validate_batch(raw):
            nonlocal validated
            raw = normalize_batch(raw)
            count = len(raw.get("questions", [])) if isinstance(raw, dict) else 0
            if not 1 <= count <= ai_count:
                raise GenerationRejected("generation_count", excerpt=_shape(raw))
            validated = validate_generated(
                raw, concepts, payload.model_copy(update={"question_count": count}), runner,
                deadline=deadline, allowed_types=set(targets), expected_types=targets if count == ai_count else None)
            if count != ai_count:
                retained.extend(validated)
                raise GenerationRejected("generation_partial", excerpt=f"count={count}/{ai_count}")
            band_counts = Counter(difficulty_band(q["difficulty_level"]) for q in validated)
            concept_counts = Counter(cid for q in validated for cid in q["concept_ids"])
            if any(band_counts[b] > ceil(ai_count/len(payload.difficulties)) for b in payload.difficulties):
                raise GenerationRejected("generation_difficulty_balance", excerpt="difficulty")
            if any(concept_counts[cid] > ceil(ai_count/len(payload.concept_ids)) for cid in payload.concept_ids):
                raise GenerationRejected("generation_concept_balance", excerpt="concept")
            return raw
        try:
            raw = llm.generate_structured("practice_generation", [ChatMessage("user", prompt)],
                json_schema={"name": "practice_questions", "strict": True, "schema": batch.model_json_schema()},
                max_tokens=12000, context_version=f"practice-v3:{learner.account_id}:{payload.request_id}:{attempt}", validator=validate_batch)
            if validated is None:
                validate_batch(raw)  # deterministic injected providers obey the same contract
            return validated
        except Exception as exc:
            entry = _diagnostic(attempt + 1, exc)
            if diagnostics is not None:
                diagnostics.append(entry)
            LOG.warning("Practice generation rejected attempt=%d reason=%s code=%s question_type=%s excerpt=%s",
                        attempt + 1, entry["reason"], entry["code"], entry["question_type"], entry["excerpt"])
            from .llm.errors import LLMError
            if isinstance(exc, LLMError) and exc.code in {LLMError.AUTH_FAILED, LLMError.NOT_CONFIGURED}:
                # New content cannot repair credentials. Preserve the normal
                # reviewed bank/template recovery without spending another call.
                break
            # The batch has not been persisted. Invalid output is never cached
            # by the domain validator; only fully valid partial batches survive.
            continue
    seen, unique, kind_counts = set(), [], Counter()
    for item in retained:
        signature = fingerprint(item["prompt"])
        kind = item["question_type"]
        if signature in seen or kind_counts[kind] >= targets.get(kind, 0):
            continue
        seen.add(signature)
        kind_counts[kind] += 1
        unique.append(item)
    return unique[:MAX_QUESTIONS]

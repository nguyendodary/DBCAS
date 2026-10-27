"""Source-grounded draft generation layered on the existing curation checks.

The model can select source IDs, never invent source URLs. Catalog summaries
are short authored descriptions, not copied documentation. They bound the
request; semantic correctness still requires an identified human reviewer.
"""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
from uuid import uuid4
from types import SimpleNamespace

from sqlalchemy import select

from ..errors import AppError
from ..models import Concept, QuestionCandidate
from ..repositories import CurriculumRepository, QuestionRepository, SecurityRepository
from .blueprints import DIFFICULTY_BANDS
from .llm import ChatMessage, LLMError
from .llm.validation import validate_json_schema

VERSION = "grounded-drafts-v1"
SOURCES = {
    "pg17-queries": {"url": "https://www.postgresql.org/docs/17/queries.html", "version": "17",
        "title": "PostgreSQL 17: Queries", "section": "Chapter 7",
        "summary": "SELECT builds a result from table expressions. Filtering, grouping, joins, set operations, ordering and limits have distinct query semantics."},
    "pg17-ddl": {"url": "https://www.postgresql.org/docs/17/ddl.html", "version": "17",
        "title": "PostgreSQL 17: Data Definition", "section": "Chapter 5",
        "summary": "Table definitions specify columns, types and constraints. Keys and references express integrity rules; schemas organize database objects."},
    "cmu-normalization": {"url": "https://www.cs.cmu.edu/~christos/courses/dbms.S12/slides/17NormI.pdf",
        "title": "CMU 15-415: Schema Refinement and Normalization", "section": "Functional dependencies",
        "summary": "Functional dependencies constrain legal relation instances. Attribute closure and dependency implication are evaluated from the stated dependencies, not guessed from a small sample of rows."},
    "aalto-normalization": {"url": "https://fitech101.aalto.fi/en/courses/databases/part-8/4-normalization",
        "title": "Aalto OpenCS: Normalization, From Anomalies to Normal Forms",
        "section": "Functional dependencies, 1NF, 2NF, 3NF and BCNF",
        "summary": "Redundancy can cause update, insert and delete anomalies. Functional dependencies describe constraints on a schema. Normal forms provide increasingly strong checks; BCNF can identify redundancy that satisfies 3NF."},
    "mit-er": {"url": "https://ocw.mit.edu/courses/11-208-introduction-to-computers-in-public-management-ii-january-iap-2002/f61e098641cd8231afd226e8658026a3_lect52.pdf",
        "title": "MIT OpenCourseWare: Relational Database Design", "section": "From E-R Model to Database Design",
        "summary": "An entity-relationship model describes entities, attributes and relationships. Relational design translates the model into tables and keys while checking normalization and integrity."},
}
for key, page, title, summary in (
    ("types", "datatype", "Data Types", "PostgreSQL has numeric, character, temporal, boolean, array, JSON and other types. Type choice, precision, nullability and conversions affect stored values and query semantics."),
    ("functions", "functions", "Functions and Operators", "Operators and functions have type-dependent behavior. Aggregates summarize sets of input rows; window functions compute over a related window while retaining individual result rows."),
    ("indexes", "indexes", "Indexes", "Indexes can reduce retrieval work but add storage and maintenance overhead. Index type, column order, predicates and query shape affect applicability; an index is not a guarantee of a faster plan."),
    ("concurrency", "mvcc", "Concurrency Control", "Isolation levels, row visibility, explicit locks and serialization failures govern concurrent access. A valid explanation distinguishes snapshot visibility from blocking and accounts for transaction boundaries."),
    ("performance", "performance-tips", "Performance Tips", "EXPLAIN describes a plan; EXPLAIN ANALYZE executes the query and measures actual behavior. Statistics and query structure influence planner estimates and choices. These concepts are assessed without executing administrative commands in the learner sandbox."),
    ("administration", "admin", "Server Administration", "Administration includes server configuration, users, databases, backup and maintenance. Questions must distinguish administrative operations from read-only query execution; the learner sandbox cannot perform those operations."),
    ("security", "client-authentication", "Client Authentication", "Connection authentication determines who can connect as a database user. Object access privileges are a separate authorization concern. Authentication rules and database roles must not be confused with application UI roles."),
    ("programming", "server-programming", "Server Programming", "Server extensions include functions, procedures, user-defined types and triggers. Their execution semantics and privileges matter; learners explain these concepts without installing or executing server-side code in the read-only sandbox."),
):
    SOURCES[f"pg17-{key}"] = {"url": f"https://www.postgresql.org/docs/17/{page}.html", "version": "17",
                              "title": f"PostgreSQL 17: {title}", "summary": summary}


def source_ids_for(concept):
    text = f'{concept.concept_code} {concept.concept_name} {concept.subject_area}'.lower()
    if any(term in text for term in ("normal", "dependenc", "relational design", "entity", "data model", "db-er", "db-fd")):
        return ("cmu-normalization", "aalto-normalization", "mit-er")
    topics = (("programming", ("server programming", "plpgsql", "pl/pgsql", "trigger", "procedure", "user-defined", "function volatility")),
              ("security", ("security", "authentication", "privilege", "grant", "revoke")),
              ("concurrency", ("concurrency", "transaction", "isolation", "locking", "deadlock")),
              ("performance", ("performance", "explain", "planner", "statistics")),
              ("administration", ("administration", "backup", "vacuum", "configuration")),
              ("indexes", ("index", "indexes")), ("types", ("data type", "json", "array")),
              ("functions", ("function", "operator", "aggregate", "window")))
    selected = tuple(f"pg17-{key}" for key, words in topics if any(word in text for word in words))[:2]
    return selected or ("pg17-queries", "pg17-ddl")


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def context(concept):
    metadata = {field: getattr(concept, field) for field in
                ("concept_id", "concept_code", "concept_name", "subject_area", "description", "keywords", "learning_objectives", "sql_feature")}
    if (not isinstance(metadata["description"], str) or len(metadata["description"].strip()) < 20
            or not metadata["keywords"] or not metadata["learning_objectives"]):
        raise AppError(422, "concept_metadata_incomplete",
                       "Add a meaningful concept description, keywords and learning objectives in Curriculum before generating drafts.")
    source_ids = source_ids_for(concept)
    return {"concept": metadata, "sources": {key: SOURCES[key] for key in source_ids}}


def schema_for(kind, count, concept_id, difficulty, locale, sources, objectives):
    text = {"type": "string", "minLength": 1, "maxLength": 12000}
    obj = lambda props: {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
    array = lambda item, low=0, high=10: {"type": "array", "items": item, "minItems": low, "maxItems": high}
    low, high = DIFFICULTY_BANDS[difficulty]
    props = {"prompt": text, "reference_answer": text, "explanation": text,
             "difficulty_level": {"type": "integer", "minimum": low, "maximum": high},
             "points": {"type": "number", "minimum": 0.01, "maximum": 999.99},
             "concept_id": {"type": "integer", "enum": [concept_id]},
             "original_locale": {"type": "string", "enum": [locale]},
             "source_ids": array({"type": "string", "enum": list(sources)}, 1, len(sources)),
             "objective_indices": array({"type": "integer", "minimum": 0, "maximum": len(objectives) - 1}, 1, len(objectives))}
    if kind == "mcq":
        props["options"] = array(obj({"option_label": {"type": "string", "enum": list("ABCDEF")},
            "option_text": text, "is_correct": {"type": "boolean"}}), 2, 6)
    elif kind == "sql":
        cell = {"anyOf": [{"type": t} for t in ("string", "number", "boolean", "null")]}
        props["datasets"] = array(obj({"dataset_name": {**text, "maxLength": 100}, "setup_sql": text,
            "expected_result": obj({"columns": array(text, 1, 50), "rows": array(array(cell, 1, 50), 0, 100),
                                    "ordered": {"type": "boolean"}, "check_columns": {"type": "boolean"}}),
            "is_edge_case": {"type": "boolean"}}), 2, 4)
    else:
        props["rubrics"] = array(obj({"level_name": {"type": "string", "enum": ["Incomplete", "Partial", "Mostly Complete", "Complete"]},
            "criteria": text, "min_score": {"type": "number", "minimum": 0},
            "max_score": {"type": "number", "minimum": 0}}), 4, 4)
    return {"name": "question_candidates", "strict": True, "schema": obj({"questions": array(obj(props), count, count)})}


def generate(db, payload, admin, llm, runner):
    from .ai_admin_service import _SYSTEM, _validate_ai_payload, _run_sql_checks, _validate_candidate, _candidate_detail
    repo = QuestionRepository(db)
    request_id = str(payload.request_id or uuid4())
    identity = {**payload.model_dump(mode="json", exclude={"request_id"}), "admin_id": admin.account_id}
    request_hash = digest(identity)
    SecurityRepository(db).lock(f"candidate-generation:{admin.account_id}:{request_id}")
    previous = list(db.scalars(select(QuestionCandidate).where(
        QuestionCandidate.payload["_generation"]["request_id"].astext == request_id,
        QuestionCandidate.payload["_generation"]["admin_id"].astext == str(admin.account_id))
        .order_by(QuestionCandidate.candidate_id)))
    if previous:
        if any(row.payload["_generation"]["request_hash"] != request_hash for row in previous):
            raise AppError(409, "generation_request_conflict", "This generation request was already used with different selections")
        return [_candidate_detail(row) for row in previous]
    concept = db.scalar(select(Concept).where(Concept.concept_id == payload.concept_id))
    if concept is None:
        raise AppError(404, "concept_not_found", "Concept not found")
    grounding = context(concept)
    wire = schema_for(payload.question_type, payload.count, payload.concept_id, payload.difficulty,
                      payload.locale, grounding["sources"], concept.learning_objectives)
    verified_sql = {}

    def validate(result):
        validate_json_schema(result, wire["schema"])
        _validate_ai_payload(result, "gen_question", payload.question_type)
        for item in result["questions"]:
            if not item["explanation"].strip():
                raise LLMError(LLMError.INVALID_RESPONSE, "Generated questions require a nonempty answer rationale")
            if payload.question_type == "mcq":
                labels = [o["option_label"] for o in item["options"]]
                texts = [o["option_text"].strip() for o in item["options"]]
                correct = next(o for o in item["options"] if o["is_correct"])
                if len(labels) != len(set(labels)) or len(texts) != len(set(texts)):
                    raise LLMError(LLMError.INVALID_RESPONSE, "Generated MCQ contains duplicate choices")
                if item["reference_answer"].strip() not in (correct["option_label"], correct["option_text"].strip()):
                    raise LLMError(LLMError.INVALID_RESPONSE, "Generated MCQ reference answer disagrees with its answer key")
            if payload.question_type == "sql":
                from .bank_validation import sql_fixture_problems
                if concept.sql_feature and sql_fixture_problems([SimpleNamespace(**d) for d in item["datasets"]],
                                                               item["reference_answer"], [concept.sql_feature]):
                    raise LLMError(LLMError.INVALID_RESPONSE, "Generated SQL does not exercise the selected concept")
                if digest(item) in verified_sql:
                    continue
                if runner is None:
                    raise LLMError(LLMError.UNAVAILABLE, "SQL candidates require the verification sandbox")
                runs = _run_sql_checks(runner, item)
                if not runs or not all(r["status"] == "passed" for r in runs):
                    raise LLMError(LLMError.INVALID_RESPONSE, "Generated SQL fixtures do not match the reference query")
                verified_sql[digest(item)] = runs
        return result

    result = llm.generate_structured("gen_question", [ChatMessage("system", _SYSTEM), ChatMessage("user", json.dumps({
        "task": "generate_question_candidates", "count": payload.count, "question_type": payload.question_type,
        **grounding, "difficulty": payload.difficulty, "locale": payload.locale, "generation_intent": request_id,
        "requirements": "Use only the supplied source IDs and concept objectives. Write original prompts, answers and nonblank explanations in the requested language. Points and scores must use 0.01 increments. MCQ reference_answer must equal the correct label or text. SQL references must be read-only SELECT queries with at least two datasets including an edge case; dataset names must be nonblank and at most 100 characters. Essay needs four contiguous 0.01 rubric bands covering zero to points. Never claim human approval or reproduce documentation passages.",
        "candidate_schema": wire["schema"]["properties"]["questions"]["items"],
    }, ensure_ascii=False))], json_schema=wire, max_tokens=4096 * payload.count,
        validator=validate, context_version=VERSION)
    # Also validate injected services; all provider paths have the same contract.
    validate(result)
    SecurityRepository(db).lock("question-bank-publication")
    # Never hold a curriculum row lock across provider I/O. Refresh and lock
    # only for the short persistence transaction, in publication-lock order.
    current = db.scalar(select(Concept).where(Concept.concept_id == payload.concept_id)
                        .with_for_update(read=True).execution_options(populate_existing=True))
    if current is None or digest(context(current)) != digest(grounding):
        raise AppError(409, "generation_context_changed", "The concept changed during generation. Review its metadata and generate a new draft.")
    out = []
    for generated in result["questions"]:
        item = deepcopy(generated)
        item["source_refs"] = [{k: v for k, v in grounding["sources"][key].items() if k != "summary"} for key in item["source_ids"]]
        item["_generation"] = {"version": VERSION, "request_id": request_id, "request_hash": request_hash,
            "admin_id": admin.account_id, "context_hash": digest(grounding), "created_at": datetime.now(timezone.utc).isoformat(),
            "model": getattr(getattr(llm, "_settings", None), "llm_model", "injected-provider"),
            "difficulty": payload.difficulty, "locale": payload.locale}
        if payload.question_type == "sql" and concept.sql_feature:
            item["is_required_concept"] = True
        row = repo.create_candidate(payload.concept_id, payload.question_type, item)
        row.validation_detail = _validate_candidate(repo, row, runner, verified_sql.get(digest(generated)))
        row.validation_status = "validated" if row.validation_detail["ok"] else "pending"
        out.append(row)
    db.commit()
    return [_candidate_detail(repo.get_candidate(row.candidate_id)) for row in out]


def provenance_check(repo, row):
    """Revalidate the frozen authoring context without silently reclassifying it."""
    payload = row.payload or {}
    meta = payload.get("_generation") or {}
    errors = []
    if meta.get("version") != VERSION:
        errors.append("Draft has no current source-grounded generation provenance; regenerate it")
    else:
        concept = CurriculumRepository(repo.db).get_concept(row.concept_id)
        try:
            grounding = context(concept)
        except (AppError, AttributeError):
            grounding = None
        if grounding is None or digest(grounding) != meta.get("context_hash"):
            errors.append("Concept metadata changed; regenerate this draft")
        elif payload.get("source_refs") != [{k: v for k, v in grounding["sources"][key].items() if k != "summary"}
                for key in payload.get("source_ids", []) if key in grounding["sources"]]:
            errors.append("Source references differ from the trusted generation context")
        if grounding is not None:
            try:
                wire = schema_for(row.question_type, 1, row.concept_id, meta["difficulty"], meta["locale"],
                                  grounding["sources"], concept.learning_objectives)
                fields = wire["schema"]["properties"]["questions"]["items"]["properties"]
                item = {key: payload[key] for key in fields if key in payload}
                validate_json_schema({"questions": [item]}, wire["schema"])
            except (LLMError, KeyError):
                errors.append("Draft no longer matches its generation schema")
    return {"check": "provenance", "ok": not errors, "problems": errors}

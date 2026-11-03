"""Learner-defined sessions and live constrained generation; no exam records."""
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from secrets import SystemRandom
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from ..errors import AppError
from ..models import Concept, Question, QuestionConcept, McqOption, Rubric, SqlTestDataset, SessionQuestionPlan, SessionStartRequest, AssessmentSession
from ..repositories import AssessmentRepository, SecurityRepository, QuestionRepository
from .evidence_context import capture_question
from .llm.provider import ChatMessage
from .personalized_assessment import serve_planned
from .system_settings import result_flow


class PracticeStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concept_ids: list[int] = Field(min_length=1, max_length=100)
    difficulties: list[str] = Field(default_factory=lambda: ["EASY", "MEDIUM", "HARD"], min_length=1, max_length=3)
    source: str = "bank"
    question_count: int = Field(default=5, ge=1, le=20, strict=True)
    request_id: UUID

    @field_validator("source")
    @classmethod
    def source_known(cls, value):
        if value not in ("bank", "ai"): raise ValueError("Unknown question source")
        return value

    @field_validator("difficulties")
    @classmethod
    def bands_known(cls, value):
        if len(set(value)) != len(value) or not set(value) <= {"EASY", "MEDIUM", "HARD"}: raise ValueError("Invalid difficulty selection")
        return sorted(value)

    @field_validator("concept_ids")
    @classmethod
    def ids_valid(cls, value):
        if any(type(i) is not int or i < 1 for i in value) or len(set(value)) != len(value): raise ValueError("Invalid concepts")
        return sorted(value)


def levels(payload):
    bands = {"EASY": [1, 2], "MEDIUM": [3], "HARD": [4, 5]}
    return [level for band in payload.difficulties for level in bands[band]]


def bank_pool(db, payload):
    from .question_service import _validation_missing
    candidates = list(db.scalars(select(Question).where(Question.status == "validated", Question.source == "bank",
                                                       Question.difficulty_level.in_(levels(payload))).order_by(Question.question_id)))
    pool, families = [], set()
    for question in candidates:
        tags = {tag.concept_id for tag in question.concept_tags if tag.confirmed}
        family = question.family_id or question.question_id
        if tags and tags <= set(payload.concept_ids) and family not in families and not _validation_missing(QuestionRepository(db), question):
            pool.append(question)
            families.add(family)
    return pool


def sample_bank(pool, count):
    if len(pool) < count:
        raise AppError(422, "insufficient_question_pool", f"Chỉ có {len(pool)} câu phù hợp, cần {count} câu. Hãy chọn thêm khái niệm/độ khó hoặc giảm số câu.",
                       details={"available": len(pool), "requested": count})
    rng = SystemRandom()
    pool = list(pool)
    rng.shuffle(pool)
    chosen = []
    for kind in ("mcq", "sql", "essay"):
        candidate = next((q for q in pool if q.question_type == kind and q not in chosen), None)
        if candidate and len(chosen) < count: chosen.append(candidate)
    chosen.extend(q for q in pool if q not in chosen)
    return chosen[:count]


def template_questions(concepts, payload):
    choices = []
    allowed = levels(payload)
    for index in range(payload.question_count):
        concept = concepts[index % len(concepts)]
        difficulty = allowed[index % len(allowed)]
        description = concept.description or f"Vận dụng {concept.concept_name} đúng yêu cầu của bài toán cơ sở dữ liệu."
        choices.append(dict(concept_ids=[concept.concept_id], difficulty_level=difficulty, question_type="mcq",
            prompt=f"Về {concept.concept_name}, nhận định nào phù hợp với mô tả khái niệm? (Tình huống {index+1})",
            reference_answer=description, points=1,
            options=[{"text": description, "correct": True}, {"text": "Luôn bỏ qua tính đúng đắn của dữ liệu.", "correct": False},
                     {"text": "Chỉ áp dụng khi cơ sở dữ liệu không có dữ liệu.", "correct": False}, {"text": "Không cần xét yêu cầu truy vấn hoặc mô hình dữ liệu.", "correct": False}],
            setup_sql=None, rubrics=[]))
    return choices


def validate_generated(raw, concepts, payload, runner):
    from .sql_validator import validate_learner_sql
    # Use a strict wire model, including no undeclared fields/coercions.
    from pydantic import ValidationError
    allowed_ids, allowed_levels = {c.concept_id for c in concepts}, set(levels(payload))
    if not isinstance(raw, dict) or set(raw) != {"questions"} or not isinstance(raw["questions"], list) or len(raw["questions"]) != payload.question_count:
        raise ValueError("generation_count")
    parsed = []
    for value in raw["questions"]:
        try:
            item = GeneratedQuestion.model_validate(value)
        except ValidationError as exc:
            raise ValueError("generation_schema") from exc
        if not set(item.concept_ids) or not set(item.concept_ids) <= allowed_ids or item.difficulty_level not in allowed_levels:
            raise ValueError("generation_scope")
        if item.question_type == "mcq":
            if len(item.options) != 4 or sum(o.correct for o in item.options) != 1 or len({o.text.strip() for o in item.options}) != 4:
                raise ValueError("generation_mcq")
            if item.reference_answer.strip() != next(o.text.strip() for o in item.options if o.correct):
                raise ValueError("generation_mcq_answer")
        elif item.question_type == "sql":
            if not item.setup_sql or not item.edge_setup_sql or validate_learner_sql(item.reference_answer):
                raise ValueError("generation_sql")
            for setup in (item.setup_sql, item.edge_setup_sql):
                schema = runner.provision_dataset(setup)
                try:
                    result = runner.execute(item.reference_answer, schema=schema)
                    if not result.success: raise ValueError("generation_sql_execution")
                finally:
                    runner.drop_dataset(schema)
        elif item.question_type == "essay" and not item.rubrics:
            raise ValueError("generation_rubric")
        if item.question_type == "essay":
            from .rubric_validation import rubric_problems
            if rubric_problems([r.model_dump() for r in item.rubrics], item.points):
                raise ValueError("generation_rubric")
        parsed.append(item.model_dump())
    return parsed


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
    reference_answer: str = Field(min_length=1, max_length=8000)
    points: int = Field(ge=1, le=10)
    options: list[GeneratedOption] = Field(max_length=4)
    setup_sql: str | None = Field(max_length=12000)
    edge_setup_sql: str | None = Field(default=None, max_length=12000)
    rubrics: list[GeneratedRubric] = Field(max_length=5)

    @field_validator("question_type")
    @classmethod
    def kind(cls, value):
        if value not in ("mcq", "sql", "essay"): raise ValueError("Question type")
        return value


def generate(db, concepts, payload, learner, runner, llm):
    from .prompt_builder import canonical, digest
    import logging, time
    started = time.monotonic()
    request_data = {"concepts": [{"id": c.concept_id, "name": c.concept_name, "description": c.description} for c in concepts],
                    "difficulty_levels": levels(payload), "count": payload.question_count}
    prompt = "Tạo câu hỏi cơ sở dữ liệu bằng tiếng Việt đúng phạm vi, schema JSON. MCQ đúng một đáp án; SQL chỉ SELECT, setup_sql và edge_setup_sql chỉ DDL/INSERT cho bảng thử và dữ liệu biên. Tự luận có bốn mức rubric Incomplete, Partial, Mostly Complete, Complete phủ mọi giá trị điểm đến 0.01. Không cần người duyệt. " + canonical(request_data)
    try:
        if not llm or not llm.is_configured(): raise ValueError("provider_missing")
        from pydantic import create_model
        batch = create_model("QuestionBatch", questions=(list[GeneratedQuestion], ...), __config__=ConfigDict(extra="forbid"))
        raw = llm.generate_structured("practice_generation", [ChatMessage("user", prompt)],
            json_schema={"name": "practice_questions", "strict": True, "schema": batch.model_json_schema()},
            max_tokens=10000, context_version=f"practice:{learner.account_id}:{payload.request_id}")
        generated = validate_generated(raw, concepts, payload, runner)
    except Exception:
        pool = bank_pool(db, payload)
        if len(pool) >= payload.question_count:
            logging.getLogger("dbcas.ai").info("ai_call role=question_generator hash=%s duration_ms=%d status=bank_fallback fallback=True", digest(prompt), (time.monotonic()-started)*1000)
            return sample_bank(pool, payload.question_count), True
        logging.getLogger("dbcas.ai").info("ai_call role=question_generator hash=%s duration_ms=%d status=unavailable fallback=True", digest(prompt), (time.monotonic()-started)*1000)
        raise AppError(503, "generation_unavailable",
                       f"AI chưa tạo được câu hỏi; ngân hàng chỉ có {len(pool)} câu phù hợp. Hãy thử lại, chọn thêm khái niệm hoặc độ khó, hoặc giảm số câu.") from None
    logging.getLogger("dbcas.ai").info("ai_call role=question_generator hash=%s duration_ms=%d status=ok fallback=False", digest(prompt), (time.monotonic()-started)*1000)
    questions = []
    for item in generated:
        question = Question(question_type=item["question_type"], prompt=item["prompt"], original_locale="vi",
            reference_answer=item["reference_answer"], difficulty_level=item["difficulty_level"], points=Decimal(item["points"]),
            source="ai_generated", status="draft", created_by=learner.account_id)
        question.ai_review = {"purpose": "learner_practice"}
        db.add(question)
        db.flush()
        for cid in item["concept_ids"]: db.add(QuestionConcept(question_id=question.question_id, concept_id=cid, tag_source="ai", confirmed=True, is_required=False))
        for index, option in enumerate(item["options"]):
            db.add(McqOption(question_id=question.question_id, option_label=chr(65+index), option_text=option["text"], is_correct=option["correct"]))
        if item["question_type"] == "sql":
            for edge, setup in ((False, item["setup_sql"]), (True, item["edge_setup_sql"])):
                schema = runner.provision_dataset(setup)
                try:
                    result = runner.execute(item["reference_answer"], schema=schema)
                    if not result.success: raise AppError(422, "generation_failed", "Không thể tạo câu SQL hợp lệ. Hãy thử ngân hàng câu hỏi.")
                    expected = {"columns": result.columns, "rows": result.rows, "column_types": result.column_types}
                finally: runner.drop_dataset(schema)
                db.add(SqlTestDataset(question_id=question.question_id, dataset_name="Generated edge" if edge else "Generated primary", setup_sql=setup, expected_result=expected, is_edge_case=edge))
        for rubric in item["rubrics"]: db.add(Rubric(question_id=question.question_id, **rubric))
        db.flush()
        db.expire(question)
        from .question_service import _validation_missing
        if _validation_missing(QuestionRepository(db), question):
            raise AppError(422, "generation_failed", "Câu hỏi chưa hợp lệ. Hãy thử lại từ ngân hàng.")
        questions.append(question)
    return questions, False


def start(db, learner, payload, runner=None, llm=None, *, locale="vi"):
    from . import adaptive_engine
    request_id = str(payload.request_id)
    SecurityRepository(db).lock(f"practice-start:{learner.account_id}")
    binding = db.get(SessionStartRequest, (learner.account_id, request_id))
    selection = payload.model_dump(mode="json", exclude={"request_id"})
    if binding:
        session = AssessmentRepository(db).get_session(binding.session_id)
        if session.config_snapshot.get("selection") != selection:
            raise AppError(409, "start_request_conflict", "Yêu cầu đã dùng cho lựa chọn khác. Hãy bắt đầu lại.")
        return adaptive_engine._state(AssessmentRepository(db), session)
    concepts = list(db.scalars(select(Concept).where(Concept.concept_id.in_(payload.concept_ids)).order_by(Concept.concept_id)))
    if len(concepts) != len(payload.concept_ids): raise AppError(422, "unknown_concept", "Khái niệm đã thay đổi. Hãy tải lại trang.")
    active = db.scalar(select(AssessmentSession).where(AssessmentSession.learner_id == learner.account_id,
        AssessmentSession.status == "in_progress").with_for_update())
    if active:
        raise AppError(409, "active_practice", "Bạn có bài đang làm. Hãy tiếp tục hoặc hoàn thành bài đó.", details={"session_id": active.session_id})
    fallback = False
    if payload.source == "bank": questions = sample_bank(bank_pool(db, payload), payload.question_count)
    else: questions, fallback = generate(db, concepts, payload, learner, runner, llm)
    counts, repo = Counter(q.question_type for q in questions), AssessmentRepository(db)
    now = repo.server_time()
    session = repo.create_session(None, learner.account_id, now + timedelta(minutes=30), started_at=now,
                                 locale=locale, result_release_policy=result_flow(db), start_request_id=request_id)
    session.config_snapshot = {"version": 1, "learner_defined": True, "personalized": True, "assembly_mode": "PRACTICE",
        "assessment_id": None, "title": "Luyện tập tự chọn", "description": "Bài luyện tập theo lựa chọn của bạn.",
        "duration_min": 30, "max_questions": len(questions), "target_mcq": counts["mcq"], "target_sql": counts["sql"], "target_essay": counts["essay"],
        "result_release_policy": session.result_release_policy, "selection": selection, "source": payload.source,
        "generation_fallback": fallback, "selected_concept_ids": payload.concept_ids, "difficulty": ",".join(payload.difficulties),
        "concepts": [{"concept_id": c.concept_id, "concept_code": c.concept_code, "concept_name": c.concept_name, "description": c.description,
            "subject_area": c.subject_area, "keywords": c.keywords, "learning_objectives": c.learning_objectives,
            "min_difficulty": min(levels(payload)), "max_difficulty": max(levels(payload)), "target_pct": "70"} for c in concepts],
        "question_ids": [q.question_id for q in questions], "question_plan": [capture_question(repo, q) for q in questions]}
    db.add(SessionStartRequest(learner_id=learner.account_id, request_id=request_id, session_id=session.session_id))
    db.add_all([SessionQuestionPlan(session_id=session.session_id, seq_no=i+1, question_id=q.question_id) for i,q in enumerate(questions)])
    db.flush()
    serve_planned(repo, session, 1)
    db.commit()
    return adaptive_engine._state(repo, session)

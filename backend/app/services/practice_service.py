"""Learner-defined sessions and live constrained generation; no exam records."""
from collections import Counter
from datetime import timedelta
from uuid import UUID
from typing import Annotated, Literal
import math
import threading
import time

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from ..errors import AppError
from ..models import Concept, SessionQuestionPlan, SessionStartRequest, AssessmentSession
from ..repositories import AssessmentRepository, SecurityRepository
from .evidence_context import capture_question
from .practice_config import MIN_QUESTIONS, DEFAULT_QUESTIONS, MAX_QUESTIONS, DIFFICULTY_LEVELS
from .practice_generation import (  # noqa: F401 - public re-exports used by test/QA harnesses
    GeneratedQuestion, ai_type_targets, generate_entries, levels, template_questions, validate_generated,
)
from .practice_bank import assemble
from .personalized_assessment import serve_planned


class PracticeStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concept_ids: list[Annotated[int, Field(gt=0, strict=True)]] = Field(min_length=1, max_length=100, json_schema_extra={"uniqueItems": True})
    difficulties: list[Literal["EASY", "MEDIUM", "HARD"]] = Field(default_factory=lambda: list(DIFFICULTY_LEVELS), min_length=1, max_length=3, json_schema_extra={"uniqueItems": True})
    source: Literal["bank", "ai"] = "bank"
    question_count: int = Field(default=DEFAULT_QUESTIONS, ge=MIN_QUESTIONS, le=MAX_QUESTIONS, strict=True)
    request_id: UUID

    @field_validator("source")
    @classmethod
    def source_known(cls, value):
        if value not in ("bank", "ai"): raise ValueError("Unknown question source")
        return value

    @field_validator("difficulties", mode="before")
    @classmethod
    def bands_known(cls, value):
        if (not isinstance(value, list) or any(type(v) is not str for v in value)
                or len(set(value)) != len(value) or not set(value) <= set(DIFFICULTY_LEVELS)): raise ValueError("Invalid difficulty selection")
        return sorted(value)

    @field_validator("concept_ids", mode="before")
    @classmethod
    def ids_valid(cls, value):
        if not isinstance(value, list) or any(type(i) is not int or i < 1 for i in value) or len(set(value)) != len(value): raise ValueError("Invalid concepts")
        return sorted(value)


class PracticeConceptRef(BaseModel):
    concept_id: int
    concept_code: str
    concept_name: str


class PracticePreviewResult(BaseModel):
    can_start: bool
    question_count: int
    type_counts: dict[str, int]
    covered_concepts: list[PracticeConceptRef]
    uncovered_concepts: list[PracticeConceptRef]
    notice: str | None = None


class PracticePreviewThrottle:
    """Small in-process sliding window, mirroring the login throttle style."""

    def __init__(self):
        self._hits: dict[int, list[float]] = {}
        self._mutex = threading.RLock()

    def check(self, learner_id: int, settings) -> None:
        now = time.monotonic()
        window = settings.practice_preview_rate_limit_window_seconds
        with self._mutex:
            hits = [hit for hit in self._hits.get(learner_id, []) if hit > now - window]
            if len(hits) >= settings.practice_preview_rate_limit_attempts:
                retry = max(1, math.ceil(window - (now - hits[0])))
                raise AppError(429, "preview_rate_limited",
                               "Too many preview requests. Please retry shortly.",
                               headers={"Retry-After": str(retry)})
            hits.append(now)
            self._hits[learner_id] = hits
            if len(self._hits) > 10000:
                self._hits = {key: value for key, value in self._hits.items()
                              if value and value[-1] > now - window}

    def reset(self) -> None:
        with self._mutex:
            self._hits.clear()


_preview_throttle = PracticePreviewThrottle()


def get_preview_throttle() -> PracticePreviewThrottle:
    return _preview_throttle


def _coverage(concepts, covered_ids):
    def ref(concept):
        return PracticeConceptRef(concept_id=concept.concept_id,
                                  concept_code=concept.concept_code,
                                  concept_name=concept.concept_name)
    covered = [ref(c) for c in concepts if c.concept_id in covered_ids]
    uncovered = [ref(c) for c in concepts if c.concept_id not in covered_ids]
    return covered, uncovered


def _coverage_notice(uncovered):
    if not uncovered:
        return None
    names = ", ".join(c.concept_name for c in uncovered[:8])
    suffix = "" if len(uncovered) <= 8 else f" (+{len(uncovered) - 8})"
    return f"Một số khái niệm chưa có câu hỏi phù hợp: {names}{suffix}. Bài vẫn có thể bắt đầu."


def preview(db, learner, payload):
    """Deterministic, read-only coverage preview; never calls an LLM."""
    from ..config import get_settings
    from .practice_bank import preview_plan
    get_preview_throttle().check(learner.account_id, get_settings())
    request_id = str(payload.request_id)
    binding = db.get(SessionStartRequest, (learner.account_id, request_id))
    if binding:
        session = AssessmentRepository(db).get_session(binding.session_id)
        snapshot = session.config_snapshot or {}
        concepts = list(db.scalars(select(Concept).where(
            Concept.concept_id.in_(snapshot.get("selected_concept_ids", []))
        ).order_by(Concept.concept_id)))
        covered_ids = {c["concept_id"] for item in snapshot.get("question_plan", [])
                       for c in item.get("concepts", [])}
        covered, uncovered = _coverage(concepts, covered_ids)
        return PracticePreviewResult(
            can_start=True, question_count=len(snapshot.get("question_ids", [])),
            type_counts=Counter(item.get("question_type") for item in snapshot.get("question_plan", [])),
            covered_concepts=covered, uncovered_concepts=uncovered,
            notice=_coverage_notice(uncovered),
        )
    concepts = list(db.scalars(select(Concept).where(
        Concept.concept_id.in_(payload.concept_ids)
    ).order_by(Concept.concept_id)))
    if len(concepts) != len(payload.concept_ids):
        raise AppError(422, "unknown_concept", "Khái niệm đã thay đổi. Hãy tải lại trang.")
    active = db.scalar(select(AssessmentSession).where(
        AssessmentSession.learner_id == learner.account_id,
        AssessmentSession.status == "in_progress",
    ).with_for_update())
    if active:
        raise AppError(409, "active_practice",
                       "Bạn có bài đang làm. Hãy tiếp tục hoặc hoàn thành bài đó.",
                       details={"session_id": active.session_id})
    SecurityRepository(db).lock("question-bank-publication", shared=True)
    # A provider-backed start may fill a deterministic shortfall; bank plans
    # stay fail-closed because nothing can extend them.
    concepts, picks = preview_plan(db, learner, payload, require_full=payload.source != "ai")
    covered_ids = {cid for pick in picks for cid in pick.candidate.concepts}
    covered, uncovered = _coverage(concepts, covered_ids)
    return PracticePreviewResult(
        can_start=True, question_count=len(picks),
        type_counts=Counter(pick.candidate.kind for pick in picks),
        covered_concepts=covered, uncovered_concepts=uncovered,
        notice=_coverage_notice(uncovered),
    )


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
    SecurityRepository(db).lock("question-bank-publication", shared=True)
    diagnostics = []
    generated = generate_entries(concepts, payload, learner, runner, llm, diagnostics=diagnostics) if payload.source == "ai" else []
    questions, picks, notice = assemble(db, learner, payload, generated)
    covered_ids = {tag.concept_id for question in questions for tag in question.concept_tags if tag.confirmed}
    _, uncovered = _coverage(concepts, covered_ids)
    coverage_notice = _coverage_notice(uncovered)
    fallback = payload.source == "ai" and any(p.candidate.origin != "ai" for p in picks)
    bank_mixed = payload.source == "ai" and any(p.candidate.origin == "bank" for p in picks)
    template_fallback = any(p.candidate.origin == "template" for p in picks)
    ai_generated_count = sum(p.candidate.origin == "ai" for p in picks)
    counts, repo = Counter(q.question_type for q in questions), AssessmentRepository(db)
    now = repo.server_time()
    session = repo.create_session(None, learner.account_id, now + timedelta(minutes=30), started_at=now,
                                 locale=locale, result_release_policy="HUMAN_VERIFIED", start_request_id=request_id)
    session.config_snapshot = {"version": 1, "learner_defined": True, "personalized": True, "assembly_mode": "PRACTICE",
        "assessment_id": None, "title": "Luyện tập tự chọn", "description": "Bài luyện tập theo lựa chọn của bạn.",
        "duration_min": 30, "max_questions": len(questions), "target_mcq": counts["mcq"], "target_sql": counts["sql"], "target_essay": counts["essay"],
        "result_release_policy": session.result_release_policy, "selection": selection, "source": payload.source,
        "generation_fallback": fallback, "bank_mixed": bank_mixed, "template_fallback": template_fallback,
        "ai_generated_count": ai_generated_count, "generation_diagnostics": diagnostics,
        "selection_notice": notice, "coverage_notice": coverage_notice,
        "uncovered_concepts": [c.model_dump() for c in uncovered],
        "selection_provenance": [{"tier": p.tier, "distance": p.distance, "origin": p.candidate.origin} for p in picks], "selected_concept_ids": payload.concept_ids, "difficulty": ",".join(payload.difficulties),
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

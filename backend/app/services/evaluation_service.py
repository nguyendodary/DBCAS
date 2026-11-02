"""Durable evaluations: leased jobs, data-keyed cache and release boundaries."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, or_
from ..errors import AppError
from ..models import AssessmentSession, EvaluationRecord, GradingJob, GradeEditAudit, Attempt
from ..repositories import AssessmentRepository, SecurityRepository
from .evidence_context import question_view
from .prompt_builder import digest, VERSION, canonical
from .evaluation_pipeline import evaluate


def is_practice(session):
    return bool((session.config_snapshot or {}).get("learner_defined"))


def owned_session(db, learner_id, session_id):
    session = db.scalar(select(AssessmentSession).where(AssessmentSession.session_id == session_id,
        AssessmentSession.learner_id == learner_id).with_for_update().execution_options(populate_existing=True))
    if not session or session.learner_id != learner_id:
        raise AppError(404, "session_not_found", "Không tìm thấy bài làm.")
    return session


def data_for(db, learner_id, session_id=None):
    repo = AssessmentRepository(db)
    all_sessions = repo.sessions_for_learner(learner_id)
    selected = [s for s in all_sessions if s.status != "in_progress" and
                (s.session_id == session_id if session_id else s.release_status == "published")]
    selected.sort(key=lambda s: (s.started_at, s.session_id))
    pending = sum(s.status != "in_progress" and s.release_status != "published" for s in all_sessions)
    metrics = {k: defaultdict(lambda: [Decimal(0), Decimal(0)]) for k in ("clo", "topic", "difficulty")}
    history, items, fingerprints = [], [], []
    recurring = defaultdict(set)
    for session in selected:
        earned, possible = Decimal(0), Decimal(0)
        for attempt in repo.session_attempts(session.session_id):
            if attempt.submitted_at is None:
                continue
            question = question_view(attempt, "vi")
            snapshot = attempt.question_snapshot or {}
            score = attempt.score
            if score is not None and score < question.points:
                for tag in question.concept_tags:
                    if tag.confirmed:
                        recurring[tag.concept.concept_name].add(session.session_id)
            points = question.points
            earned += score or 0
            possible += points
            answer = (attempt.sql_answer or attempt.essay_answer) if question.question_type != "mcq" else str(attempt.selected_option_id)
            fingerprints.append(digest([snapshot, str(score), answer, attempt.review_revision]))
            topics = sorted({t.concept.subject_area for t in question.concept_tags if t.confirmed}) or ["Chưa phân loại"]
            clos = [c.get("clo_code", str(c.get("clo_id"))) for c in snapshot.get("clo_mappings", [])]
            difficulty = "Dễ" if question.difficulty_level <= 2 else "Vừa" if question.difficulty_level == 3 else "Khó"
            for dimension, keys in (("clo", clos), ("topic", topics), ("difficulty", [difficulty])):
                for key in set(keys):
                    metrics[dimension][key][0] += score or 0
                    metrics[dimension][key][1] += points
            items.append(dict(attempt_id=attempt.attempt_id, question_id=question.question_id, type=question.question_type,
                prompt=question.prompt[:1600], answer=str(answer or "")[:2400], points=str(points), score=str(score) if score is not None else None,
                reference_answer=(question.reference_answer or "")[:1600],
                options=[{"id": o.option_id, "text": o.option_text, "correct": o.is_correct} for o in question.options],
                concepts=[t.concept.concept_name for t in question.concept_tags if t.confirmed], clo=clos, topics=topics, difficulty=difficulty,
                rubric=[dict(level=r.level_name, min=str(r.min_score), max=str(r.max_score), criteria=r.criteria) for r in question.rubrics]))
        percentage = float((earned / possible * 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)) if possible else 0
        history.append(dict(session_id=session.session_id, ordinal=len(history)+1, date=session.started_at.isoformat(), earned=str(earned), possible=str(possible), percentage=percentage))
    dimensions = {dimension: [dict(label=label, earned=str(value[0]), possible=str(value[1]),
        percentage=float((value[0] / value[1] * 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)) if value[1] else 0)
        for label, value in sorted(groups.items())] for dimension, groups in metrics.items()}
    total_earned = sum((Decimal(h["earned"]) for h in history), Decimal(0))
    total_possible = sum((Decimal(h["possible"]) for h in history), Decimal(0))
    score = {"earned": str(total_earned), "possible": str(total_possible),
             "percentage": float((total_earned/total_possible*100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)) if total_possible else 0}
    # Keep aggregate evidence from every attempt, with bounded chart detail.
    history_hash = digest(history)
    compact_history = [history[0], *history[-499:]] if len(history) > 500 else history
    data = dict(version=VERSION, mode="attempt" if session_id else "overall", attempt_count=len(selected), score=score,
                history=compact_history, history_hash=history_hash, dimensions=dimensions, items=items[-80:],
                recurring_weaknesses=[{"concept": key, "attempts": len(value)} for key, value in sorted(recurring.items()) if len(value) >= 2],
                evidence_hash=digest(fingerprints), details_truncated=len(items) > 80 or len(history) > 500)
    # All scores and every evidence hash remain represented. Detail is bounded.
    while len(canonical(data).encode()) > 165000 and data["items"]:
        data["items"].pop(0)
        data["details_truncated"] = True
    return data, pending


def ensure(db, learner_id, session_id=None):
    key = f"attempt:{session_id}" if session_id else "overall"
    SecurityRepository(db).lock(f"evaluation:{learner_id}:{key}")
    data, pending = data_for(db, learner_id, session_id)
    row = db.scalar(select(EvaluationRecord).where(EvaluationRecord.learner_id == learner_id, EvaluationRecord.scope_key == key).with_for_update().execution_options(populate_existing=True))
    input_hash = digest(data)
    if not row:
        row = EvaluationRecord(learner_id=learner_id, session_id=session_id, scope_key=key, input_hash=input_hash, status="pending")
        db.add(row)
    elif row.input_hash != input_hash:
        row.input_hash, row.status, row.payload, row.lease_until = input_hash, "pending", None, None
        row.updated_at = datetime.now(timezone.utc)
    db.flush()
    return row, data, pending


def view(db, learner_id, session_id=None, *, admin=False, retry=False):
    session = owned_session(db, learner_id, session_id) if session_id else None
    if session and session.status == "in_progress":
        raise AppError(409, "session_in_progress", "Hãy hoàn thành bài trước khi xem đánh giá.")
    if session and not admin and session.result_release_policy == "HUMAN_VERIFIED" and session.release_status != "published":
        return {"status": "awaiting_approval", "message": "Đang chờ giảng viên duyệt"}
    row, data, pending = ensure(db, learner_id, session_id)
    # A stale worker is safely recoverable, even after a process restart.
    now = datetime.now(timezone.utc)
    force = row.status != "ready" and (retry or (now - row.updated_at).total_seconds() > 45)
    if force:
        db.commit()
        process_one(db, force_id=row.evaluation_id, force_fallback=True)
        db.refresh(row)
        data, pending = data_for(db, learner_id, session_id)
    if session and is_practice(session) and row.status == "ready":
        from .grading_review import reconcile
        reconcile(db, session)
    result = {"status": "empty" if not data["attempt_count"] else row.status,
        "attempt_count": data["attempt_count"], "pending_count": pending, "dimensions": data["dimensions"],
        "history": data["history"], "score": data["score"], "details_truncated": data["details_truncated"],
        "input_hash": row.input_hash, "result": row.payload if row.status == "ready" else None,
        "approved": bool(session and session.result_release_policy == "HUMAN_VERIFIED" and session.release_status == "published"),
        "adjusted": bool(session and db.scalar(select(GradeEditAudit.audit_id).join(Attempt, GradeEditAudit.attempt_id == Attempt.attempt_id)
            .where(Attempt.session_id == session_id, GradeEditAudit.old_score.is_distinct_from(GradeEditAudit.new_score)).limit(1)))}
    if session and not admin and session.release_status != "published":
        result.update(status="pending", dimensions={}, history=[], result=None, score=None)
    db.commit()
    return result


def ready(db, session):
    row, _, _ = ensure(db, session.learner_id, session.session_id)
    return row.status == "ready"


def process_one(db, llm=None, settings=None, *, force_id=None, force_fallback=False):
    from ..config import get_settings
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    query = select(EvaluationRecord).where(or_(EvaluationRecord.status == "pending",
        (EvaluationRecord.status == "processing") & (EvaluationRecord.lease_until < now)))
    if force_id:
        query = select(EvaluationRecord).where(EvaluationRecord.evaluation_id == force_id)
    row = db.scalar(query.order_by(EvaluationRecord.updated_at).with_for_update(skip_locked=True).limit(1).execution_options(populate_existing=True))
    if not row or row.status == "ready":
        return False
    session = db.get(AssessmentSession, row.session_id) if row.session_id else None
    if session:
        attempts = AssessmentRepository(db).session_attempts(session.session_id)
        if any(a.submitted_at and question_view(a).question_type != "essay" and a.score is None for a in attempts):
            db.rollback()
            return False
    row.status, row.lease_until = "processing", now + timedelta(seconds=180)
    row_id, expected_hash, lease = row.evaluation_id, row.input_hash, row.lease_until
    data, _ = data_for(db, row.learner_id, row.session_id)
    db.commit()
    # Never hold a database lock across local inference or a provider request.
    payload = evaluate(data, llm, settings=settings, force_fallback=force_fallback or not data["attempt_count"])
    # Other transactions may have retried or edited while inference was running.
    # expire_on_commit=False must not turn the lease check into a stale read.
    db.expire_all()
    if session:
        session = AssessmentRepository(db).lock_session(session.session_id)
    row = db.scalar(select(EvaluationRecord).where(EvaluationRecord.evaluation_id == row_id).with_for_update().execution_options(populate_existing=True))
    if row.input_hash != expected_hash or row.lease_until != lease:
        db.rollback()
        return True
    latest, _ = data_for(db, row.learner_id, row.session_id)
    if digest(latest) != digest(data):
        row.status, row.input_hash, row.lease_until = "pending", digest(latest), None
        db.commit()
        return True
    if session and is_practice(session):
        proposals = {item["attempt_id"]: item["essay_score_proposal"] for item in payload["evaluation"]["question_comments"]}
        for attempt in AssessmentRepository(db).session_attempts(session.session_id):
            if question_view(attempt).question_type == "essay" and attempt.score is None:
                proposal = proposals.get(attempt.attempt_id)
                if proposal is None:
                    from .evaluation_pipeline import essay_proposal
                    item = next(i for i in data["items"] if i["attempt_id"] == attempt.attempt_id)
                    proposal = essay_proposal(item)
                attempt.score = Decimal(str(proposal)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
                attempt.grading_status = "graded"
                attempt.grading_detail = {"grader": "evaluator", "points_earned": str(attempt.score),
                    "points_possible": str(question_view(attempt).points), "fallback_used": payload["evaluator_fallback"]}
                job = db.scalar(select(GradingJob).where(GradingJob.attempt_id == attempt.attempt_id))
                if job:
                    job.status, job.finished_at, job.lease_until = "completed", now, None
        db.flush()
        data, _ = data_for(db, row.learner_id, row.session_id)
    row.status, row.payload, row.input_hash, row.lease_until = "ready", payload, digest(data), None
    row.updated_at = datetime.now(timezone.utc)
    db.flush()
    if session and is_practice(session):
        from .competency_service import detect_session_gaps
        from .grading_review import reconcile
        detect_session_gaps(db, session, commit=False)
        reconcile(db, session)
    db.commit()
    return True

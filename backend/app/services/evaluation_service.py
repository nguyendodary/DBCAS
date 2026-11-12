"""Durable evaluations: leased jobs, data-keyed cache and release boundaries."""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select, or_, func
from ..errors import AppError
from ..models import AssessmentSession, EvaluationRecord, GradingJob, GradeEditAudit, Attempt, Question
from ..repositories import AssessmentRepository, SecurityRepository
from .evidence_context import question_view
from .prompt_builder import digest, VERSION, canonical
from .evaluation_pipeline import evaluate


def is_practice(session):
    return bool((session.config_snapshot or {}).get("learner_defined"))


def concept_context_for(db, session):
    """Deterministic per-concept context; never contains learner identity."""
    if session is None:
        return []
    snapshot = session.config_snapshot or {}
    attempts = AssessmentRepository(db).session_attempts(session.session_id)
    covered = {tag.concept_id for attempt in attempts for tag in question_view(attempt).concept_tags
               if tag.confirmed}
    from ..models import ConceptCompetency
    rows = {row.concept_id: row for row in db.scalars(
        select(ConceptCompetency).where(ConceptCompetency.session_id == session.session_id)
    )}
    result, seen = [], set()
    for item in snapshot.get("concepts", []):
        cid = item.get("concept_id")
        if not cid or cid in seen:
            continue
        seen.add(cid)
        row = rows.get(cid)
        pct = float(row.competency_pct) if row is not None and row.points_possible else None
        target = item.get("target_pct")
        target = float(target) if target is not None else None
        result.append({
            "concept_id": cid,
            "concept_code": item.get("concept_code"),
            "concept_name": item.get("concept_name"),
            "competency_pct": pct,
            "target_pct": target,
            "below_target": bool(row.below_target) if row is not None else (
                pct is not None and target is not None and pct < target),
            "covered": cid in covered,
        })
    if not result:
        for attempt in attempts:
            for tag in question_view(attempt).concept_tags:
                if not tag.confirmed or tag.concept_id in seen:
                    continue
                seen.add(tag.concept_id)
                row = rows.get(tag.concept_id)
                pct = float(row.competency_pct) if row is not None and row.points_possible else None
                result.append({
                    "concept_id": tag.concept_id,
                    "concept_code": tag.concept.concept_code,
                    "concept_name": tag.concept.concept_name,
                    "competency_pct": pct,
                    "target_pct": None,
                    "below_target": bool(row.below_target) if row is not None else False,
                    "covered": True,
                })
    return result[:100]


def owned_session(db, learner_id, session_id):
    session = db.scalar(select(AssessmentSession).where(AssessmentSession.session_id == session_id,
        AssessmentSession.learner_id == learner_id).with_for_update().execution_options(populate_existing=True))
    if not session or session.learner_id != learner_id:
        raise AppError(404, "session_not_found", "Không tìm thấy bài làm.")
    return session


def shorten_text(value, limit):
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, list):
        return [shorten_text(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: shorten_text(item, limit) for key, item in value.items()}
    return value


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
    # A single attempt must retain every question for feedback, even with long rubrics.
    if session_id:
        for limit in (800, 400, 200, 100, 50, 16):
            if len(canonical(data).encode()) <= 165000:
                break
            data["items"] = shorten_text(data["items"], limit)
            data["details_truncated"] = True
    # Overall aggregates and hashes cover all attempts; only recent detail is bounded.
    while not session_id and len(canonical(data).encode()) > 165000 and data["items"]:
        data["items"].pop(0)
        data["details_truncated"] = True
    return data, pending


def ensure(db, learner_id, session_id=None, *, debounce_seconds=0):
    key = f"attempt:{session_id}" if session_id else "overall"
    SecurityRepository(db).lock(f"evaluation:{learner_id}:{key}")
    data, pending = data_for(db, learner_id, session_id)
    row = db.scalar(select(EvaluationRecord).where(EvaluationRecord.learner_id == learner_id, EvaluationRecord.scope_key == key).with_for_update().execution_options(populate_existing=True))
    input_hash = digest(data)
    now = datetime.now(timezone.utc)
    available_at = now + timedelta(seconds=debounce_seconds)
    if not row:
        row = EvaluationRecord(learner_id=learner_id, session_id=session_id, scope_key=key,
                               input_hash=input_hash, status="pending", available_at=available_at)
        db.add(row)
    elif row.input_hash != input_hash:
        pass
        row.input_hash, row.status, row.payload, row.lease_until = input_hash, "pending", None, None
        row.available_at = available_at
        row.updated_at = now
    db.flush()
    return row, data, pending


def _adjusted(db, session_id):
    return bool(session_id and db.scalar(
        select(GradeEditAudit.audit_id).join(Attempt, GradeEditAudit.attempt_id == Attempt.attempt_id)
        .where(Attempt.session_id == session_id,
               GradeEditAudit.old_score.is_distinct_from(GradeEditAudit.new_score)).limit(1)))


def _question_results(db, session, scores=None):
    score_map = {int(item["attempt_id"]): item for item in (scores or [])}
    results = []
    for attempt in AssessmentRepository(db).session_attempts(session.session_id):
        question = question_view(attempt)
        snapshot = score_map.get(attempt.attempt_id, {})
        results.append({
            "attempt_id": attempt.attempt_id, "question_id": attempt.question_id,
            "question_type": question.question_type, "prompt": question.prompt,
            "score": snapshot.get("score", attempt.score),
            "points": snapshot.get("points", question.points),
            "grading_status": snapshot.get("grading_status", attempt.grading_status),
        })
    return results


def _concept_results(db, session, evaluation, stored=None):
    base = stored if stored else concept_context_for(db, session)
    notes = {int(item["concept_id"]): item for item in (evaluation or {}).get("concepts", [])
             if item.get("concept_id") is not None}
    results = []
    for item in base:
        note = notes.get(int(item["concept_id"]), {})
        results.append({**item, "strength": note.get("strength"),
                        "weakness": note.get("weakness"),
                        "recommendation": note.get("recommendation")})
    return results


def _final_view(db, session, data, pending):
    from ..models import SessionFinalResult
    final = db.scalar(select(SessionFinalResult).where(
        SessionFinalResult.session_id == session.session_id))
    if final is None:
        raise AppError(409, "final_result_unavailable", "The final result is not available yet.")
    ai = final.ai_evaluation or {}
    return {
        "status": "ready", "provisional": False, "final": True,
        "attempt_count": data["attempt_count"], "pending_count": pending,
        "dimensions": data["dimensions"], "history": data["history"],
        "score": final.overall or data["score"],
        "details_truncated": data["details_truncated"],
        "input_hash": final.evaluation_input_hash,
        "uncovered_concepts": final.uncovered_concepts,
        "question_results": _question_results(db, session, final.scores),
        "concept_results": _concept_results(db, session, final.final_evaluation,
                                             final.concept_results),
        "result": {
            "evaluation": final.final_evaluation,
            "prompt_hash": ai.get("prompt_hash", ""),
            "builder_fallback": bool(ai.get("builder_fallback")),
            "evaluator_fallback": bool(ai.get("evaluator_fallback")),
        },
        "approved": True, "adjusted": _adjusted(db, session.session_id),
        "source": "admin_approved" if final.source == "admin" else "legacy_admin_approved",
        "approved_at": final.approved_at,
    }


def _provisional_view(db, session, row, data, pending):
    evaluation = (row.payload or {}).get("evaluation", {})
    snapshot = session.config_snapshot or {}
    return {
        "status": "provisional", "provisional": True, "final": False,
        "attempt_count": data["attempt_count"], "pending_count": pending,
        "dimensions": data["dimensions"], "history": data["history"],
        "score": data["score"], "details_truncated": data["details_truncated"],
        "input_hash": row.input_hash,
        "uncovered_concepts": snapshot.get("uncovered_concepts", []),
        "question_results": _question_results(db, session),
        "concept_results": _concept_results(db, session, evaluation),
        "result": row.payload, "approved": False,
        "adjusted": _adjusted(db, session.session_id), "source": "ai",
        "approved_at": None,
    }


def _updating_view(row, data, pending, session):
    return {
        "status": "updating", "provisional": False, "final": False,
        "attempt_count": data["attempt_count"], "pending_count": pending,
        "dimensions": {}, "history": [], "score": None, "details_truncated": False,
        "input_hash": row.input_hash, "result": None, "approved": False,
        "adjusted": False, "source": None, "approved_at": None,
        "uncovered_concepts": (session.config_snapshot or {}).get("uncovered_concepts", []),
        "question_results": [], "concept_results": [],
    }


def view(db, learner_id, session_id=None, *, admin=False, retry=False):
    session = owned_session(db, learner_id, session_id) if session_id else None
    if session and session.status == "in_progress":
        raise AppError(409, "session_in_progress", "Hãy hoàn thành bài trước khi xem đánh giá.")
    row, data, pending = ensure(db, learner_id, session_id)
    # A stale worker is safely recoverable, even after a process restart.
    now = datetime.now(timezone.utc)
    force = row.status != "ready" and (retry or (now - row.updated_at).total_seconds() > 45)
    if force:
        db.commit()
        process_one(db, force_id=row.evaluation_id, force_fallback=True)
        db.refresh(row)
        data, pending = data_for(db, learner_id, session_id)
    if session and is_practice(session):
        from .grading_review import reconcile
        reconcile(db, session)
        db.commit()
        db.refresh(session)
        db.refresh(row)
        if session.release_status == "published":
            return _final_view(db, session, data, pending)
        if row.status == "ready" and session.release_status in ("provisional_ai", "pending_review"):
            return _provisional_view(db, session, row, data, pending)
        if row.status != "ready" and row.available_at and row.available_at > now:
            return _updating_view(row, data, pending, session)
    if (session and not admin and row.status == "ready"
            and session.release_status != "published"):
        return {"status": "awaiting_approval", "message": "Đang chờ giảng viên duyệt"}
    result = {"status": "empty" if not data["attempt_count"] else row.status,
        "attempt_count": data["attempt_count"], "pending_count": pending, "dimensions": data["dimensions"],
        "history": data["history"], "score": data["score"], "details_truncated": data["details_truncated"],
        "input_hash": row.input_hash, "result": row.payload if row.status == "ready" else None,
        "approved": bool(session and session.result_release_policy == "HUMAN_VERIFIED" and session.release_status == "published"),
        "adjusted": _adjusted(db, session_id)}
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
        (EvaluationRecord.status == "processing") & (EvaluationRecord.lease_until < now)),
        EvaluationRecord.available_at <= now)
    # A failed/pending SQL row must not sit at the queue head and starve other
    # learners. Respect frozen types even if the live bank was later edited.
    blocked = select(Attempt.attempt_id).join(Question, Question.question_id == Attempt.question_id).where(
        Attempt.session_id == EvaluationRecord.session_id, Attempt.submitted_at.is_not(None), Attempt.score.is_(None),
        func.coalesce(Attempt.question_snapshot["question_type"].astext, Question.question_type) != "essay").exists()
    query = query.where(or_(EvaluationRecord.session_id.is_(None), ~blocked))
    if force_id:
        query = select(EvaluationRecord).where(EvaluationRecord.evaluation_id == force_id,
                                                EvaluationRecord.available_at <= now)
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
    concept_context = concept_context_for(db, session) if session else []
    db.commit()
    # Never hold a database lock across local inference or a provider request.
    payload = evaluate(data, llm, settings=settings,
                       force_fallback=force_fallback or not data["attempt_count"],
                       concept_context=concept_context)
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

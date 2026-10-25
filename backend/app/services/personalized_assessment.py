"""Strict bank assembly using the existing assessment configuration and engine.

The complete server-only question plan is frozen before question one is served.
No provider calls, mutable future selections, or difficulty substitutions occur.
"""
from datetime import timedelta
from collections import Counter
from itertools import combinations
from secrets import SystemRandom

from sqlalchemy import select

from ..errors import AppError
from ..models import Assessment, AssessmentSession, Question, SessionQuestionPlan, SessionStartRequest
from ..repositories import AssessmentRepository, QuestionRepository, SecurityRepository
from .evidence_context import capture_assessment, capture_question

DIFFICULTY_BANDS = {"EASY": (1, 2), "MEDIUM": (3, 3), "HARD": (4, 5)}


def practice_quotas(pool, question_count):
    """Explicit practice format balances the formats actually available.

    The request fixes the question count and difficulty, while this format
    deliberately has no mandatory SQL/essay quota for a purely conceptual topic.
    """
    counts = {kind: len({q.family_id or q.question_id for q, _ in pool if q.question_type == kind})
              for kind in ("mcq", "sql", "essay")}
    quotas = dict.fromkeys(counts, 0)
    for _ in range(question_count):
        available = [kind for kind in counts if quotas[kind] < counts[kind]]
        if not available:
            raise AppError(422, "insufficient_question_pool", "The approved bank has fewer questions than the requested practice length at this difficulty")
        kind = min(available, key=lambda kind: (quotas[kind], list(counts).index(kind)))
        quotas[kind] += 1
    return quotas


def _same_selection(config, payload):
    return (config.get("selected_concept_ids") == sorted(payload.concept_ids)
            and config.get("difficulty") == payload.difficulty
            and config.get("assembly_mode", "FORMAL") == payload.mode
            and config.get("requested_question_count", 13) == payload.question_count)


def select_questions(pool, concept_ids, quotas, *, rng=None):
    """Cover every skill, respect type quotas, and deduplicate version families.

    Search only the coverage prefix (at most the number of selected concepts),
    pruning branches without enough remaining distinct question families. Fill
    remaining type quotas by least represented skill, randomizing equal choices.
    """
    rng = rng or SystemRandom()
    candidates = list(pool)
    rng.shuffle(candidates)

    def family(q):
        return q.family_id or q.question_id

    capabilities = {}
    for q, fits in candidates:
        capabilities.setdefault(family(q), set()).add((q.question_type, tuple(sorted(fits))))
    capabilities = {fid: tuple(sorted(values)) for fid, values in capabilities.items()}
    failed_coverage = set()

    def feasible(available, remaining):
        # Hall's condition for type slots versus distinct version families.
        kinds = [kind for kind, count in remaining.items() if count]
        return all(len({family(q) for q, _ in available if q.question_type in subset}) >= sum(remaining[k] for k in subset)
                   for size in range(1, len(kinds) + 1) for subset in combinations(kinds, size))

    def fill(remaining, used, chosen):
        available = [(q, fits) for q, fits in candidates
                     if family(q) not in used and remaining.get(q.question_type, 0) > 0]
        if not feasible(available, remaining):
            return None
        needed = [kind for kind, count in remaining.items() if count]
        if not needed:
            return chosen
        kind = min(needed, key=lambda kind: len({family(q) for q, _ in available if q.question_type == kind}) - remaining[kind])
        coverage = Counter(cid for q in chosen for cid in fits_by_id[q.question_id])
        ordered = sorted([(q, fits) for q, fits in available if q.question_type == kind],
                         key=lambda entry: (min(coverage[c] for c in entry[1]), sum(coverage[c] for c in entry[1])))
        for q, _ in ordered:
            result = fill({**remaining, kind: remaining[kind] - 1}, used | {family(q)}, chosen + [q])
            if result is not None:
                return result
        return None

    fits_by_id = {q.question_id: set(fits) for q, fits in candidates}

    def cover(uncovered, remaining, used, chosen):
        available = [(q, set(fits)) for q, fits in candidates
                     if family(q) not in used and remaining.get(q.question_type, 0) > 0]
        if not feasible(available, remaining):
            return None
        if not uncovered:
            return fill(remaining, used, chosen)
        families = {family(q) for q, _ in available}
        state = (tuple(sorted(uncovered)), tuple(sorted(remaining.items())),
                 tuple(sorted(Counter(capabilities[fid] for fid in families).items())))
        if state in failed_coverage:
            return None
        options = {cid: [(q, fits) for q, fits in available if cid in fits] for cid in uncovered}
        cid = min(uncovered, key=lambda c: (len(options[c]), c))
        if not options[cid]:
            return None
        # A multi-skill question can cover several selected concepts at once.
        tried = set()
        for q, fits in sorted(options[cid], key=lambda entry: -len(entry[1] & uncovered)):
            equivalent = (q.question_type, tuple(sorted(fits)), capabilities[family(q)])
            if equivalent in tried:
                continue
            tried.add(equivalent)
            counts = {**remaining, q.question_type: remaining[q.question_type] - 1}
            result = cover(uncovered - fits, counts, used | {family(q)}, chosen + [q])
            if result is not None:
                return result
        failed_coverage.add(state)
        return None

    result = cover(set(concept_ids), dict(quotas), set(), [])
    if result is None:
        raise AppError(422, "insufficient_question_pool",
                       "The approved question bank cannot cover every selected skill at this difficulty with the required question mix. Select other skills or contact an administrator.",
                       details={"required_by_type": quotas, "selected_concept_ids": sorted(concept_ids)})
    chosen = result
    rng.shuffle(chosen)
    return chosen


def select_practice_questions(pool, concept_ids, question_count, *, rng=None):
    """Prefer balanced formats, then the nearest feasible mix covering all skills.

    Practice has no mandatory type quota. A sparse conceptual bank can need two
    MCQs before an SQL/essay item, or expose different types from one version
    family. Never reject an otherwise valid plan solely to force equal formats.
    """
    preferred = practice_quotas(pool, question_count)
    kinds = tuple(preferred)
    capacities = {kind: len({q.family_id or q.question_id for q, _ in pool if q.question_type == kind})
                  for kind in kinds}
    options = []
    for mcq in range(min(capacities["mcq"], question_count) + 1):
        for sql in range(min(capacities["sql"], question_count - mcq) + 1):
            essay = question_count - mcq - sql
            if essay <= capacities["essay"]:
                options.append(dict(zip(kinds, (mcq, sql, essay))))
    options.sort(key=lambda quota: (sum((quota[k] - preferred[k]) ** 2 for k in kinds),
                                    -quota["mcq"], -quota["sql"]))
    for quotas in options:
        try:
            return select_questions(pool, concept_ids, quotas, rng=rng), quotas
        except AppError as exc:
            if exc.code != "insufficient_question_pool":
                raise
    raise AppError(422, "insufficient_question_pool",
                   "The approved question bank cannot cover every selected skill at this difficulty within the requested practice length")


def start_session(db, assessment_id, learner, payload, *, locale="en"):
    from . import adaptive_engine
    from .question_localization import normalize_locale
    from .question_service import _validation_missing

    repo = AssessmentRepository(db)
    SecurityRepository(db).lock(f"assessment-start-request:{learner.account_id}:{payload.request_id}")
    SecurityRepository(db).lock(f"assessment-start:{learner.account_id}:{assessment_id}")
    request_id = str(payload.request_id)
    requested_ids = sorted(payload.concept_ids)
    if len(requested_ids) != len(set(requested_ids)):
        raise AppError(422, "duplicate_concept_ids", "Select each skill only once")
    previous = db.scalar(select(AssessmentSession).join(SessionStartRequest,
        (SessionStartRequest.session_id == AssessmentSession.session_id)
        & (SessionStartRequest.learner_id == AssessmentSession.learner_id)).where(
        SessionStartRequest.learner_id == learner.account_id,
        SessionStartRequest.request_id == request_id))
    if previous:
        config = previous.config_snapshot or {}
        if previous.assessment_id != assessment_id or not _same_selection(config, payload):
            raise AppError(409, "start_request_conflict", "This start request was already used with different selections")
        adaptive_engine._maybe_timeout(previous, db)
        return adaptive_engine._state(repo, previous)
    db.scalar(select(Assessment).where(Assessment.assessment_id == assessment_id).with_for_update(read=True))
    assessment = repo.get_assessment(assessment_id)
    if assessment is None:
        raise AppError(404, "assessment_not_found", "Assessment not found")
    if assessment.status != "published":
        raise AppError(409, "assessment_not_active", "This assessment is not open")
    snapshot = capture_assessment(assessment)
    allowed = {c["concept_id"] for c in snapshot["concepts"]}
    if not set(requested_ids) <= allowed:
        raise AppError(422, "invalid_skill_selection", "Select skills offered by this assessment")
    active = repo.active_session_for(learner.account_id, assessment_id)
    if active:
        config = active.config_snapshot or {}
        if not _same_selection(config, payload):
            raise AppError(409, "active_selection_conflict", "Resume or finish the existing assessment before changing selections")
        db.add(SessionStartRequest(learner_id=learner.account_id, request_id=request_id,
                                   session_id=active.session_id))
        # Persist the alias even when timeout finalization commits separately.
        db.flush()
        adaptive_engine._maybe_timeout(active, db)
        db.commit()
        return adaptive_engine._state(repo, active)
    low, high = DIFFICULTY_BANDS[payload.difficulty]
    snapshot["concepts"] = [dict(c, min_difficulty=max(low, c["min_difficulty"]),
                                 max_difficulty=min(high, c["max_difficulty"]))
                            for c in snapshot["concepts"] if c["concept_id"] in requested_ids]
    if any(c["min_difficulty"] > c["max_difficulty"] for c in snapshot["concepts"]):
        raise AppError(422, "insufficient_question_pool", "The selected difficulty is outside the allowed range for a selected skill")
    from types import SimpleNamespace
    selected_config = SimpleNamespace(**{**snapshot, "targets": [SimpleNamespace(**c) for c in snapshot["concepts"]]})
    pool = adaptive_engine._eligible_pool(selected_config, set(), repo)
    extra_mcq = assessment.max_questions - (assessment.target_mcq + assessment.target_sql + assessment.target_essay)
    if payload.mode == "PRACTICE":
        chosen, quotas = select_practice_questions(pool, requested_ids, payload.question_count)
    else:
        quotas = {"mcq": assessment.target_mcq + extra_mcq, "sql": assessment.target_sql, "essay": assessment.target_essay}
        chosen = select_questions(pool, requested_ids, quotas)
    if payload.mode == "PRACTICE":
        snapshot.update(template_limits={key: snapshot[key] for key in ("max_questions", "target_mcq", "target_sql", "target_essay")},
                        max_questions=payload.question_count, target_mcq=quotas["mcq"],
                        target_sql=quotas["sql"], target_essay=quotas["essay"])
    # Serialize curation updates against capture; acquire locks in ID order.
    ids = sorted(q.question_id for q in chosen)
    db.execute(select(Question.question_id).where(Question.question_id.in_(ids))
               .order_by(Question.question_id).with_for_update(read=True)).all()
    bank = QuestionRepository(db)
    plan = {}
    locked_types, locked_skills, locked_families = Counter(), set(), set()
    for question_id in ids:
        q = db.scalar(select(Question).where(Question.question_id == question_id)
                      .options(*bank._detail_loads()).execution_options(populate_existing=True))
        if q.status != "validated" or _validation_missing(bank, q):
            raise AppError(409, "question_bank_changed", "The question bank changed. Retry assessment creation.")
        fits = [t for t in q.concept_tags if t.confirmed and t.concept_id in requested_ids
                and any(c["concept_id"] == t.concept_id and c["min_difficulty"] <= q.difficulty_level <= c["max_difficulty"] for c in snapshot["concepts"])]
        if not fits:
            raise AppError(409, "question_bank_changed", "Question classification changed. Retry assessment creation.")
        locked_types[q.question_type] += 1
        locked_skills.update(t.concept_id for t in fits)
        locked_families.add(q.family_id or q.question_id)
        plan[question_id] = capture_question(repo, q)
    # A curation transaction may finish between selection and acquiring locks.
    # Recheck the complete plan, rather than only each question's eligibility.
    if (any(locked_types[kind] != count for kind, count in quotas.items())
            or not set(requested_ids) <= locked_skills
            or len(locked_families) != len(chosen)):
        raise AppError(409, "question_bank_changed", "Question classification changed. Retry assessment creation.")
    snapshot.update(navigation_mode="FREE", personalized=True, selected_concept_ids=requested_ids, difficulty=payload.difficulty,
                    assembly_mode=payload.mode, requested_question_count=payload.question_count,
                    question_ids=[q.question_id for q in chosen],
                    question_plan=[plan[q.question_id] for q in chosen])
    now = repo.server_time()
    session = repo.create_session(assessment_id, learner.account_id, now + timedelta(minutes=assessment.duration_min),
                                  started_at=now, locale=normalize_locale(locale),
                                  result_release_policy=assessment.result_release_policy, start_request_id=request_id)
    session.config_snapshot = snapshot
    db.add(SessionStartRequest(learner_id=learner.account_id, request_id=request_id,
                               session_id=session.session_id))
    db.add_all([SessionQuestionPlan(session_id=session.session_id, seq_no=seq, question_id=q.question_id)
                for seq, q in enumerate(chosen, start=1)])
    db.flush()
    for seq in range(1, len(chosen) + 1):
        serve_planned(repo, session, seq)
    db.commit()
    return adaptive_engine._state(repo, session)


def serve_planned(repo, session, seq_no):
    snapshot = session.config_snapshot["question_plan"][seq_no - 1]
    attempt = repo.create_attempt(session.session_id, snapshot["question_id"], seq_no)
    attempt.question_snapshot = snapshot
    repo.create_selection_log(session.session_id, seq_no, snapshot["question_id"],
        is_fallback=False, decision_detail={"phase": "personalized", "difficulty": session.config_snapshot["difficulty"],
                                          "selected_concept_ids": session.config_snapshot["selected_concept_ids"]})
    return attempt

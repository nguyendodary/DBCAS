"""Reviewed current-row correction; owner edits and historical data stay protected."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest
from sqlalchemy import select, func

from app.benchmark import import_pack
from app.config import ROOT_DIR, get_settings
from app.errors import AppError
from app.models import Question, Assessment, AssessmentSession, Attempt
from app.reconcile_bank import load_packs, preflight, reconcile, apply_correction
from app.repositories import AssessmentRepository, CurriculumRepository
from app.schemas import AssessmentUpsertRequest
from app.services import assessment_service
from app.services.adaptive_engine import _eligible_pool
from app.services.evidence_context import capture_assessment, capture_question
from app.services.sandbox_runner import SandboxRunner
from test_ai_admin import _make_account


@pytest.fixture
def stale_row(db_session):
    pack = deepcopy(load_packs()[2])
    pack['questions'] = [next(q for q in pack['questions'] if q['key'] == 'pg-m089')]
    pack['concepts'] = [c for c in pack['concepts'] if c['concept_code'] == 'PG-TYPE-JSON']
    pack['clos'], pack['dependencies'], pack['assessments'] = [], {}, []
    admin = _make_account(db_session, 'reconcile@test.dev', 'Administrator')
    runner = SandboxRunner(get_settings())
    result = import_pack(db_session, admin, runner, pack)
    q = db_session.get(Question, result['question_ids'][0])
    old = json.loads((ROOT_DIR / 'db/pg_m089_reconciliation.json').read_text(encoding='utf-8'))['before']
    q.explanation = old['explanation']
    texts = {o['option_label']: o['option_text'] for o in old['options']}
    for option in q.options:
        option.option_text = texts[option.option_label]
    db_session.commit()
    return pack, admin, runner, q


def test_reviewed_correction_dry_run_identity_and_idempotency(db_session, stale_row):
    pack, admin, runner, q = stale_row
    ids = [(o.option_id, o.option_label, o.is_correct) for o in q.options]
    before = (q.explanation, q.version_no, q.updated_at, q.translations[0].updated_at)
    plan = preflight(db_session, [pack])
    assert len(plan['corrections']) == 1 and plan['conflicts'] == []
    assert (q.explanation, q.version_no, q.updated_at, q.translations[0].updated_at) == before
    assert reconcile(db_session, admin, runner, [pack])['matched_translations'] == 1
    assert q.version_no == 2 and q.status == 'validated'
    assert [(o.option_id, o.option_label, o.is_correct) for o in q.options] == ids
    after = (q.explanation, q.version_no, q.updated_at, q.translations[0].updated_at)
    result = reconcile(db_session, admin, runner, [pack])
    assert result['corrections'] == [] and result['conflicts'] == []
    assert (q.explanation, q.version_no, q.updated_at, q.translations[0].updated_at) == after
    assert db_session.scalar(select(func.count()).select_from(Question)) == 1


@pytest.mark.parametrize('change', ['explanation', 'points', 'option', 'version', 'status', 'translation', 'duplicate', 'reference'])
def test_reconciliation_refuses_unreviewed_or_referenced_state(db_session, stale_row, change):
    pack, admin, runner, q = stale_row
    if change == 'explanation': q.explanation += ' Owner note.'
    elif change == 'points': q.points = 2
    elif change == 'option': q.options[0].option_text += ' Owner note.'
    elif change == 'version': q.version_no = 9
    elif change == 'status': q.status = 'draft'
    elif change == 'translation': q.translations[0].prompt += ' Owner note.'
    elif change == 'duplicate':
        db_session.add(Question(question_type='mcq', prompt=q.prompt, points=1, difficulty_level=4,
                                status='draft', source='bank', created_by=admin.account_id))
    elif change == 'reference':
        a = Assessment(title='Historical reference', created_by=admin.account_id)
        db_session.add(a); db_session.flush()
        s = AssessmentSession(assessment_id=a.assessment_id, learner_id=admin.account_id,
                              expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        db_session.add(s); db_session.flush()
        db_session.add(Attempt(session_id=s.session_id, question_id=q.question_id, seq_no=1,
                               question_snapshot=capture_question(AssessmentRepository(db_session), q)))
    db_session.commit()
    before = (q.explanation, q.version_no, q.updated_at)
    with pytest.raises(AppError) as caught:
        reconcile(db_session, admin, runner, [pack])
    assert caught.value.code == 'reconciliation_conflict'
    assert (q.explanation, q.version_no, q.updated_at) == before


def test_correction_rechecks_row_after_preflight(db_session, stale_row):
    pack, admin, runner, q = stale_row
    assert len(preflight(db_session, [pack])['corrections']) == 1
    q.explanation += ' Concurrent owner change.'
    db_session.commit()
    with pytest.raises(AppError):
        apply_correction(db_session, q.question_id, pack['questions'][0])
    assert q.version_no == 1


def test_current_foundations_template_publishes_without_mutating_legacy(db_session):
    admin = _make_account(db_session, 'future-foundations@test.dev', 'Administrator')
    runner = SandboxRunner(get_settings())
    for pack in load_packs():
        import_pack(db_session, admin, runner, pack)
    repo = AssessmentRepository(db_session)
    curriculum = CurriculumRepository(db_session)
    old = Assessment(title='Historical Foundations', created_by=admin.account_id, status='published',
                     duration_min=30, max_questions=8, target_mcq=4, target_sql=2, target_essay=2)
    db_session.add(old); db_session.flush()
    for code, pct in [('SELECT', 40), ('JOIN', 30), ('IDX', 30)]:
        repo.upsert_target(old.assessment_id, curriculum.find_concept_by_code(code).concept_id,
                           min_d=1, max_d=3, target_pct=pct)
    db_session.commit()
    old = repo.get_assessment(old.assessment_id)
    old_config = capture_assessment(old)
    legacy = db_session.scalar(select(Question).where(Question.prompt == 'Explain why indexes speed up reads but slow down writes.'))
    successor = db_session.scalar(select(Question).where(Question.prompt.like('A PostgreSQL table is read frequently%')))
    s = AssessmentSession(assessment_id=old.assessment_id, learner_id=admin.account_id, status='completed',
                          expires_at=datetime.now(timezone.utc), config_snapshot=old_config)
    db_session.add(s); db_session.flush()
    saved = capture_question(repo, legacy)
    attempt = Attempt(session_id=s.session_id, question_id=legacy.question_id, seq_no=1,
                      score=2, question_snapshot=saved)
    db_session.add(attempt); db_session.commit()
    assert [q.question_id for q, _ in _eligible_pool(old, set(), repo) if q.question_type == 'essay'] == [successor.question_id]
    template = json.loads((ROOT_DIR / 'db/assessment_templates/postgres_foundations_current.json').read_text(encoding='utf-8'))
    payload = AssessmentUpsertRequest(**{**template, 'concepts': [
        {**c, 'concept_id': curriculum.find_concept_by_code(c['concept_code']).concept_id} for c in template['concepts']]})
    draft = assessment_service.create_assessment(db_session, payload, admin)
    pool = _eligible_pool(repo.get_assessment(draft.assessment_id), set(), repo)
    from collections import Counter
    assert Counter(q.question_type for q, _ in pool) == {'mcq': 14, 'sql': 18, 'essay': 2}
    assert successor.question_id in [q.question_id for q, _ in pool]
    assert legacy.question_id not in [q.question_id for q, _ in pool]
    assert len(set(cid for _, ids in pool for cid in ids)) == 3
    published = assessment_service.set_assessment_status(db_session, draft.assessment_id, 'published', runner)
    assert published.status == 'published'
    from types import SimpleNamespace
    from app.services.adaptive_engine import _pick
    for correct in (True, False):
        attempts = []
        served = []
        current = repo.get_assessment(draft.assessment_id)
        for _ in range(13):
            candidates = [(q, ids) for q, ids in pool if q.question_id not in served]
            chosen, _ = _pick(current, attempts, candidates)
            assert chosen is not None
            served.append(chosen.question_id)
            attempts.append(SimpleNamespace(question=chosen, question_snapshot=capture_question(repo, chosen),
                submitted_at=datetime.now(timezone.utc), score=chosen.points if correct else 0))
        assert Counter(a.question.question_type for a in attempts) == {'mcq': 10, 'sql': 2, 'essay': 1}
        assert successor.question_id in served and legacy.question_id not in served
    with pytest.raises(AppError) as caught:
        assessment_service.replace_assessment(db_session, old.assessment_id, payload)
    assert caught.value.code == 'assessment_not_draft'
    assert capture_assessment(repo.get_assessment(old.assessment_id)) == old_config
    db_session.refresh(s); db_session.refresh(attempt)
    assert s.config_snapshot == old_config and attempt.question_snapshot == saved and attempt.score == 2
    assert successor.question_id not in [saved['question_id']]
    assessment_service.delete_assessment(db_session, draft.assessment_id)
    assert repo.get_assessment(draft.assessment_id) is None

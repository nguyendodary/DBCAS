"""Durable drafts, authoritative finalization, network recovery and snapshots."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import select, func

from app.config import get_settings
from app.db import get_session_factory
from app.models import Account, AccountRole, Assessment, AssessmentConcept, AssessmentSession, Attempt, Concept, GradingJob, McqOption, Question, QuestionConcept, Role, Rubric, SqlTestDataset, UserProfile
from app.security import create_access_token, hash_password
from app.services.assessment_lifecycle import finalize, sweep_expired
from app.services.grading_jobs import process_one
from app.services.competency_service import profile_for_session
from app.services.llm import LLMService, ChatCompletionsProvider


def _fixture(db, kind="mcq", locale="en", policy="IMMEDIATE"):
    learner=Account(email="draft@test.dev",password_hash=hash_password("Secret123!"),status="active")
    learner.profile=UserProfile(full_name="Draft Learner")
    db.add(learner);db.flush()
    role=db.scalar(select(Role).where(Role.role_name=="Learner"));db.add(AccountRole(account_id=learner.account_id,role_id=role.role_id))
    concept=Concept(concept_code="SQL-SELECT",concept_name="SELECT",subject_area="SQL Querying",difficulty_level=1)
    db.add(concept);db.flush()
    assessment=Assessment(title="Immutable test",status="active",created_by=learner.account_id)
    db.add(assessment);db.flush()
    db.add(AssessmentConcept(assessment_id=assessment.assessment_id,concept_id=concept.concept_id,target_pct=Decimal("80")))
    q=Question(question_type=kind,prompt="Original prompt",points=Decimal("1"),difficulty_level=1,status="validated",created_by=learner.account_id,reference_answer="SELECT id FROM t" if kind=="sql" else "3NF definition")
    db.add(q);db.flush()
    db.add(QuestionConcept(question_id=q.question_id,concept_id=concept.concept_id,confirmed=True))
    correct=None
    if kind=="mcq":
        correct=McqOption(question_id=q.question_id,option_label="A",option_text="Original correct answer",is_correct=True)
        db.add_all([correct,McqOption(question_id=q.question_id,option_label="B",option_text="Incorrect",is_correct=False)]);db.flush()
    elif kind=="sql":
        for name,edge in (("base",False),("edge",True)):
            db.add(SqlTestDataset(question_id=q.question_id,dataset_name=name,setup_sql="CREATE TABLE t(id int); INSERT INTO t VALUES(1);",expected_result={"columns":["id"],"rows":[[1]]},is_edge_case=edge))
    else:
        for name,low,high in (("Incomplete",0,.24),("Partial",.25,.49),("Mostly Complete",.5,.74),("Complete",.75,1)):
            db.add(Rubric(question_id=q.question_id,level_name=name,min_score=Decimal(str(low)),max_score=Decimal(str(high)),criteria="Criteria for "+name))
    session=AssessmentSession(assessment_id=assessment.assessment_id,learner_id=learner.account_id,expires_at=datetime.now(timezone.utc)+timedelta(minutes=60),status="in_progress",locale=locale,result_release_policy=policy)
    db.add(session);db.flush()
    attempt=Attempt(session_id=session.session_id,question_id=q.question_id,seq_no=1)
    db.add(attempt);db.commit()
    token,_=create_access_token(learner.account_id,["Learner"],get_settings())
    field={"mcq":"selected_option_id","sql":"sql_answer","essay":"essay_answer"}[kind]
    answer={field:correct.option_id if correct else "SELECT id FROM t" if kind=="sql" else "3NF definition"}
    return learner,session,attempt,q,concept,{"Authorization":"Bearer "+token},answer


def _save(client,session,q,headers,answer,revision=1):
    return client.put(f"/api/v1/sessions/{session.session_id}/draft",headers=headers,json={"question_id":q.question_id,"revision":revision,**answer})


@pytest.mark.parametrize("kind",["mcq","sql","essay"])
def test_draft_survives_new_request_and_connection_without_grading(client,db_session,kind):
    _,session,attempt,q,_,headers,answer=_fixture(db_session,kind)
    assert _save(client,session,q,headers,answer).status_code==200
    with get_session_factory()() as restarted:
        saved=restarted.get(Attempt,attempt.attempt_id)
        assert saved.draft_answer==answer and saved.score is None and saved.submitted_at is None
    state=client.get(f"/api/v1/sessions/{session.session_id}",headers=headers).json()
    assert state["current_question"]["draft"]==answer
    assert state["current_question"]["draft_revision"]==1
    result=client.get(f"/api/v1/sessions/{session.session_id}/draft?question_id={q.question_id}",headers=headers)
    assert result.json()["answer"]==answer and result.json()["saved_at"]


def test_draft_retry_is_idempotent_and_stale_revision_rejected(client,db_session):
    _,session,_,q,_,headers,answer=_fixture(db_session)
    assert _save(client,session,q,headers,answer).status_code==200
    assert _save(client,session,q,headers,answer).status_code==200
    assert _save(client,session,q,headers,{"selected_option_id":None}).status_code==409
    assert _save(client,session,q,headers,{"selected_option_id":None},revision=2).status_code==200


def test_session_and_draft_timestamps_use_database_clock(client, db_session, monkeypatch):
    from app.repositories import AssessmentRepository
    from app.services import adaptive_engine, assessment_lifecycle
    class WrongHostClock:
        @staticmethod
        def now(*args):
            raise AssertionError("Assessment timestamps must use the database clock")
    monkeypatch.setattr(adaptive_engine, "datetime", WrongHostClock)
    monkeypatch.setattr(assessment_lifecycle, "datetime", WrongHostClock)
    _, session, _, question, _, headers, answer = _fixture(db_session)
    repo = AssessmentRepository(db_session)
    before = repo.server_time()
    saved = _save(client, session, question, headers, answer)
    state = client.get(f"/api/v1/sessions/{session.session_id}", headers=headers)
    finished = client.post(f"/api/v1/sessions/{session.session_id}/finish", headers=headers)
    after = repo.server_time()
    assert saved.status_code == state.status_code == finished.status_code == 200
    for value in (saved.json()["saved_at"], state.json()["server_now"], finished.json()["submitted_at"]):
        assert before <= datetime.fromisoformat(value) <= after


def test_empty_finalization_commits_even_when_no_competency_rows_change(client, db_session):
    _, session, _, _, _, headers, _ = _fixture(db_session)
    first = client.post(f"/api/v1/sessions/{session.session_id}/finish", headers=headers)
    assert first.status_code == 200
    with get_session_factory()() as fresh:
        saved = fresh.get(AssessmentSession, session.session_id)
        assert saved.status == "completed" and saved.submitted_at is not None
    second = client.post(f"/api/v1/sessions/{session.session_id}/finish", headers=headers)
    assert second.json()["submitted_at"] == first.json()["submitted_at"]


def test_completed_retry_without_confirmed_tags_commits_its_job(client, db_session, sandbox_runner):
    _, session, attempt, question, concept, headers, answer = _fixture(db_session, "sql")
    tag = db_session.get(QuestionConcept, (question.question_id, concept.concept_id))
    tag.confirmed = False
    db_session.commit()
    assert _save(client, session, question, headers, answer).status_code == 200
    assert client.post(f"/api/v1/sessions/{session.session_id}/finish", headers=headers).status_code == 200
    assert process_one(db_session, sandbox_runner)
    with get_session_factory()() as fresh:
        job = fresh.scalar(select(GradingJob).where(GradingJob.attempt_id == attempt.attempt_id))
        assert job.status == "completed" and job.finished_at is not None
        assert fresh.get(Attempt, attempt.attempt_id).grading_status == "graded"


@pytest.mark.parametrize("kind",["mcq","sql","essay"])
def test_timeout_uses_persisted_draft_and_exact_expiry(client,db_session,kind):
    _,session,attempt,q,_,headers,answer=_fixture(db_session,kind)
    assert _save(client,session,q,headers,answer).status_code==200
    deadline=datetime.now(timezone.utc)-timedelta(seconds=1)
    session.expires_at=deadline;db_session.commit()
    state=client.get(f"/api/v1/sessions/{session.session_id}",headers=headers)
    assert state.status_code==200 and state.json()["status"]=="timed_out"
    db_session.refresh(session);db_session.refresh(attempt)
    assert session.submitted_at==deadline and attempt.submitted_at==deadline
    assert getattr(attempt,next(iter(answer)))==next(iter(answer.values()))
    if kind=="mcq":assert attempt.score==1 and attempt.grading_status=="graded"
    else:assert attempt.score is None and attempt.grading_status=="pending" and db_session.scalar(select(func.count()).select_from(GradingJob))==1
    timestamp=session.submitted_at
    again=client.post(f"/api/v1/sessions/{session.session_id}/finish",headers=headers)
    assert again.status_code==200
    db_session.refresh(session);assert session.submitted_at==timestamp


def test_background_expiry_without_browser_callback(client,db_session):
    _,session,attempt,q,_,headers,answer=_fixture(db_session)
    _save(client,session,q,headers,answer)
    session.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db_session.commit()
    assert sweep_expired(db_session)==1 and sweep_expired(db_session)==0
    db_session.refresh(attempt);assert attempt.score==1


def test_manual_finish_grades_saved_draft_and_duplicate_finish_preserves_timestamp(client,db_session):
    _,session,attempt,q,_,headers,answer=_fixture(db_session)
    _save(client,session,q,headers,answer)
    first=client.post(f"/api/v1/sessions/{session.session_id}/finish",headers=headers).json()
    second=client.post(f"/api/v1/sessions/{session.session_id}/finish",headers=headers).json()
    assert first["status"]==second["status"]=="completed"
    assert first["submitted_at"]==second["submitted_at"]
    db_session.refresh(attempt);assert attempt.score==1
    assert _save(client,session,q,headers,answer,2).status_code==409


def test_finish_and_timeout_race_finalizes_once(client,db_session):
    learner,session,attempt,q,_,headers,answer=_fixture(db_session)
    _save(client,session,q,headers,answer)
    session.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db_session.commit()
    def finish(_):
        with get_session_factory()() as db:
            finalize(db,db.get(AssessmentSession,session.session_id))
    with ThreadPoolExecutor(max_workers=5) as executor:list(executor.map(finish,range(5)))
    db_session.refresh(session);db_session.refresh(attempt)
    assert session.status=="timed_out" and session.submitted_at==session.expires_at and attempt.score==1


def test_atomic_submission_safe_retry_after_lost_response(client,db_session):
    _,session,attempt,q,_,headers,answer=_fixture(db_session)
    second=Question(question_type="mcq",prompt="Next prompt",points=Decimal("1"),difficulty_level=1,status="validated",created_by=session.learner_id)
    db_session.add(second);db_session.flush()
    db_session.add_all([QuestionConcept(question_id=second.question_id,concept_id=1,confirmed=True),McqOption(question_id=second.question_id,option_label="A",option_text="Correct",is_correct=True),McqOption(question_id=second.question_id,option_label="B",option_text="Incorrect",is_correct=False)]);db_session.commit()
    body={"question_id":q.question_id,**answer}
    first=client.post(f"/api/v1/sessions/{session.session_id}/submit",headers=headers,json=body)
    assert first.status_code==200,first.json()
    retry=client.post(f"/api/v1/sessions/{session.session_id}/submit",headers=headers,json=body)
    assert retry.status_code==200
    assert first.json()["answer"]["attempt_id"]==retry.json()["answer"]["attempt_id"]
    assert first.json()["state"]["current_question"]["question_id"]==second.question_id
    assert retry.json()["state"]["current_question"]["question_id"]==second.question_id
    assert db_session.scalar(select(func.count()).select_from(Attempt))==2


def test_other_learner_cannot_read_or_write_draft(client,db_session):
    _,session,_,q,_,_,answer=_fixture(db_session)
    r=client.post("/api/v1/auth/register",json={"name":"Other","email":"other@test.dev","password":"Secret123!","password_confirm":"Secret123!"})
    assert r.status_code==201
    token=client.post("/api/v1/auth/login",json={"email":"other@test.dev","password":"Secret123!"}).json()["access_token"]
    headers={"Authorization":"Bearer "+token}
    assert _save(client,session,q,headers,answer).status_code==404
    assert client.get(f"/api/v1/sessions/{session.session_id}/draft?question_id={q.question_id}",headers=headers).status_code==404


def test_expired_save_cannot_extend_time(client,db_session):
    _,session,attempt,q,_,headers,answer=_fixture(db_session)
    session.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db_session.commit()
    result=_save(client,session,q,headers,answer)
    assert result.status_code==409 and result.json()["error"]["code"]=="session_expired"
    db_session.refresh(attempt);assert attempt.draft_answer is None


def _essay_service(db):
    def handler(request):
        return httpx.Response(200,json={"choices":[{"message":{"content":"{\"rubric_level\":\"Complete\",\"score\":1,\"explanation\":\"Correct definition\",\"feedback\":\"Continue practicing\",\"matched_criteria\":[\"definition\"],\"missing_concepts\":[],\"evidence\":[\"3NF\"]}"}}]})
    return LLMService(get_settings(),provider=ChatCompletionsProvider("https://mock.test","test-only",transport=httpx.MockTransport(handler)))


@pytest.mark.parametrize("kind",["sql","essay"])
def test_timeout_job_grades_saved_draft_and_recomputes_competency(client,db_session,sandbox_runner,kind):
    _,session,attempt,q,_,headers,answer=_fixture(db_session,kind)
    _save(client,session,q,headers,answer)
    session.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1);db_session.commit()
    client.get(f"/api/v1/sessions/{session.session_id}",headers=headers)
    assert process_one(db_session,sandbox_runner,_essay_service(db_session),include_essay=True)
    db_session.refresh(attempt)
    assert attempt.score==1 and attempt.grading_status=="graded"
    assert db_session.scalar(select(GradingJob)).status=="completed"
    assert profile_for_session(db_session,session).concepts[0].competency_pct==100


def test_pending_essay_is_not_invented_as_zero_and_retry_is_bounded(client,db_session,sandbox_runner):
    _,session,attempt,q,_,headers,answer=_fixture(db_session,"essay")
    _save(client,session,q,headers,answer)
    client.post(f"/api/v1/sessions/{session.session_id}/finish",headers=headers)
    assert profile_for_session(db_session,session).concepts==[]
    settings=get_settings().model_copy(update={"grading_job_retry_seconds":0,"grading_job_max_attempts":3})
    for _ in range(3):assert process_one(db_session,sandbox_runner,None,include_essay=True,settings=settings)
    db_session.refresh(attempt)
    assert attempt.score is None and attempt.grading_status=="failed"
    job=db_session.scalar(select(GradingJob));assert job.attempt_count==3 and job.status=="failed"
    assert not process_one(db_session,sandbox_runner,None,include_essay=True,settings=settings)


def test_historical_prompt_points_targets_and_concepts_survive_mutation(client,db_session):
    _,session,attempt,q,concept,headers,answer=_fixture(db_session)
    _save(client,session,q,headers,answer)
    client.post(f"/api/v1/sessions/{session.session_id}/finish",headers=headers)
    before=client.get(f"/api/v1/sessions/{session.session_id}/competency",headers=headers).json()
    q.prompt="Edited prompt";q.points=Decimal("10");q.options[0].option_text="Edited answer"
    concept.concept_name="Edited concept"
    target=db_session.scalar(select(AssessmentConcept));target.target_pct=Decimal("99")
    assessment=db_session.get(Assessment,session.assessment_id);assessment.title="Edited assessment";assessment.duration_min=180
    db_session.commit()
    after=client.get(f"/api/v1/sessions/{session.session_id}/competency",headers=headers).json()
    assert before==after
    evidence=client.get(f"/api/v1/sessions/{session.session_id}/evidence",headers=headers).json()["items"][0]
    assert evidence["prompt"]=="Original prompt" and Decimal(evidence["points"])==1
    assert evidence["options"][0]["option_text"]=="Original correct answer"
    state=client.get(f"/api/v1/sessions/{session.session_id}",headers=headers).json()
    assert state["assessment_title"]=="Immutable test"


def test_unconfirmed_mapping_contributes_no_competency(client,db_session):
    _,session,_,q,_,headers,answer=_fixture(db_session)
    tag=db_session.scalar(select(QuestionConcept));tag.confirmed=False;db_session.commit()
    _save(client,session,q,headers,answer)
    client.post(f"/api/v1/sessions/{session.session_id}/finish",headers=headers)
    assert client.get(f"/api/v1/sessions/{session.session_id}/competency",headers=headers).json()["concepts"]==[]

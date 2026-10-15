"""Isolated real API for browser/load gates; never installed in release images.

The existing Docker fixtures own disposable containers. No local .env AI key
is loaded, and every AI response crosses the real service via MockTransport.
Only this script adds fixture endpoints, on the localhost test listener.
"""
import json
import os
import re
from datetime import timedelta
from pathlib import Path
import sys
import uuid
import subprocess
import argparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(DEPLOYMENT_MODE="development", GOOGLE_CLIENT_ID="", GOOGLE_CLIENT_SECRET="",
    GITHUB_CLIENT_ID="", GITHUB_CLIENT_SECRET="", FRONTEND_URL="http://127.0.0.1:5174",
    CORS_ORIGINS='["http://127.0.0.1:5174"]')
if os.environ.get("DBCAS_RELEASE_WORKER") != "1":
    os.environ["DBCAS_TEST_RUN_ID"] = uuid.uuid4().hex
    import conftest  # Only the launcher creates UUID-named disposable containers.
    manifest = Path(__file__).resolve().parents[3] / "_review/remediation/release-containers.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"run_id": os.environ["DBCAS_TEST_RUN_ID"], "containers": conftest.OWNED_CONTAINERS}), encoding="utf-8")
import httpx
import psycopg
from fastapi import Depends
from sqlalchemy.orm import Session
from app.main import app
from app.db import get_db, get_session_factory
from app.deps import AdminOnly, LearnerOnly, get_llm_service
from app.config import Settings, get_settings
from app.migrate import apply_migrations
from app.models import Account, AccountRole, UserProfile, Role, AssessmentSession
from app.security import hash_password, create_access_token
from app.repositories import LlmCacheRepository, AssessmentRepository
from app.services.llm import LLMService, ChatCompletionsProvider
from app.services.sandbox_runner import SandboxRunner
from app.benchmark import import_pack
from app.errors import AppError

TEST_PASSWORD = "ReleaseTest123!"
ADMIN_EMAIL = "release-admin@test.dev"
pack_ids = json.loads(os.environ.get("DBCAS_RELEASE_PACK_IDS", "{}"))


def provider_response(request):
    body = json.loads(request.content)
    prompt = body["messages"][-1]["content"]
    if prompt.startswith("{"):
        data = json.loads(prompt)
        task = data["task"]
        cid = data.get("concept", {}).get("concept_id") or next((c["concept_id"] for c in data["concepts"]
            if c["concept_code"] == "SQL-SELECT"), data["concepts"][0]["concept_id"])
        if task == "map_clo_to_concepts":
            result = {"concept_ids": [cid], "rationale": "The recorded learning outcome covers this concept."}
        elif task == "generate_question_candidates":
            if data["question_type"] != "mcq":
                raise AssertionError("Browser fixture generates MCQs only; other types use the academic bank")
            result = {"questions": [{"prompt": f"Release candidate {uuid.uuid4().hex[:10]}: which statement projects rows?",
                "difficulty_level": 1, "points": 1,
                "options": [{"option_label": "A", "option_text": "SELECT", "is_correct": True},
                            {"option_label": "B", "option_text": "DROP", "is_correct": False}]}
                for _ in range(data["count"])]}
        else:
            result = {"concept_ids": [cid], "difficulty_level": 2, "evaluation_criteria": "Explain the selected concept accurately."}
    elif "STUDENT ANSWER" in prompt:
        answer = prompt.split("STUDENT ANSWER (identifiers redacted):\n", 1)[1].split("\n\nReturn JSON:", 1)[0]
        points = float(re.search(r"MAXIMUM SCORE: ([\d.]+)", prompt)[1])
        result = {"rubric_level": "Complete", "score": points,
            "explanation": "The fixture answer meets the supplied criteria.", "feedback": "Practice another decomposition.",
            "matched_criteria": ["stated answer"], "missing_concepts": [], "evidence": [answer]}
        if "in natural Vietnamese" in prompt:
            result.update(explanation="Câu trả lời đáp ứng các tiêu chí đã nêu.",
                          feedback="Hãy luyện tập thêm một bài phân rã quan hệ.",
                          matched_criteria=["Nội dung trả lời đáp ứng tiêu chí"])
    else:
        result = {"explanation": "Review the actual recorded mistakes for this concept."}
    return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(result)}}]})


def llm_service(db: Session = Depends(get_db)):
    settings = Settings(_env_file=None, llm_model="release-mock", llm_base_url="https://provider.test/v1", llm_api_key="test-only")
    return LLMService(settings, provider=ChatCompletionsProvider("https://provider.test/v1", "test-only",
        transport=httpx.MockTransport(provider_response)), cache=LlmCacheRepository(db))


# Make accidental new live provider paths fail before any request is sent.
_generate = ChatCompletionsProvider.generate
def no_live_calls(provider, request):
    if provider._transport is None:
        raise AssertionError("Live AI calls are forbidden in the browser/load release server")
    return _generate(provider, request)
ChatCompletionsProvider.generate = no_live_calls
app.dependency_overrides[get_llm_service] = llm_service


@app.get("/__test/fixture")
def fixture(admin: Account = AdminOnly):
    return pack_ids


@app.post("/__test/sessions/{session_id}/deadline")
def deadline(session_id: int, seconds: int = 2, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    if not 1 <= seconds <= 600:
        raise AppError(422, "fixture_limit", "Test deadline must be within 1–600 seconds")
    session = AssessmentRepository(db).lock_session(session_id)
    if session is None or session.learner_id != learner.account_id or session.status != "in_progress":
        raise AppError(404, "session_not_found", "Active test session not found")
    session.expires_at = AssessmentRepository(db).server_time() + timedelta(seconds=seconds)
    db.commit()
    return {"expires_at": session.expires_at}


@app.post("/__test/load-fixture")
def load_fixture(count: int = 100, sql: bool = False, admin: Account = AdminOnly, db: Session = Depends(get_db)):
    from app.services.adaptive_engine import start_session, serve_next, get_state
    from app.services.assessment_lifecycle import submit
    from app.schemas import SubmitAnswerRequest
    from app.repositories import QuestionRepository
    if count not in (4, 100) or sql and count != 4:
        raise AppError(422, "fixture_limit", "Use 100 HTTP learners or four bounded SQL learners")
    role = db.query(Role).filter_by(role_name="Learner").one()
    password_hash = hash_password(TEST_PASSWORD)
    learners = []
    for i in range(count):
        account = Account(email=f"load-{uuid.uuid4().hex}@test.dev", password_hash=password_hash, status="active")
        account.profile = UserProfile(full_name=f"Load fixture {i + 1}")
        db.add(account)
        db.flush()
        db.add(AccountRole(account_id=account.account_id, role_id=role.role_id))
        db.commit()
        token, _ = create_access_token(account.account_id, ["Learner"], get_settings())
        state = start_session(db, pack_ids["assessment_ids"][0], account)
        if sql:
            for _ in range(13):
                question = state.current_question
                if question.question_type == "sql":
                    break
                key = QuestionRepository(db).get_detail(question.question_id)
                answer = {"selected_option_id": next(o.option_id for o in key.options if o.is_correct)} if question.question_type == "mcq" else {"essay_answer": key.reference_answer}
                submit(db, state.session_id, account, SubmitAnswerRequest(question_id=question.question_id, **answer), SandboxRunner(get_settings()), llm_service(db))
                serve_next(db, state.session_id, account)
                state = get_state(db, state.session_id, account)
        fixture = {"token": token, "session_id": state.session_id, "question": state.current_question.model_dump(mode="json")}
        if sql:
            fixture["sql_answer"] = QuestionRepository(db).get_detail(state.current_question.question_id).reference_answer
        learners.append(fixture)
    return learners


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=[1, 2, 4], default=2)
    args = parser.parse_args()
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        apply_migrations(conn)
    with get_session_factory()() as db:
        role = db.query(Role).filter_by(role_name="Administrator").one()
        admin = Account(email=ADMIN_EMAIL, password_hash=hash_password(TEST_PASSWORD), status="active")
        admin.profile = UserProfile(full_name="Release fixture administrator")
        db.add(admin)
        db.flush()
        db.add(AccountRole(account_id=admin.account_id, role_id=role.role_id))
        db.commit()
        pack_ids = import_pack(db, admin, SandboxRunner(get_settings()))
    os.environ["DBCAS_RELEASE_PACK_IDS"] = json.dumps(pack_ids)
    os.environ["DBCAS_RELEASE_WORKER"] = "1"
    # A separate CLI avoids Windows spawn re-importing the seed launcher.
    subprocess.run([sys.executable, "-m", "uvicorn", "release_server:app", "--app-dir", "tests",
        "--host", "127.0.0.1", "--port", "8100", "--workers", str(args.workers),
        "--no-access-log", "--log-level", "warning", "--timeout-keep-alive", "15"], check=True)

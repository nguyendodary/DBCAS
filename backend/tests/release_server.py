"""Isolated real API for browser/load gates; never installed in release images.

The existing Docker fixtures own disposable containers. Child settings disable
local .env AI keys. Default mode uses MockTransport at the provider boundary;
--application serves app.main without overrides or fixture routes.
"""
import json
import os
import re
from collections import Counter
from datetime import timedelta
from pathlib import Path
import sys
import uuid
import subprocess
import argparse
from release_environment import server_environment

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(DEPLOYMENT_MODE="development", GOOGLE_CLIENT_ID="dbcas-e2e-google-client",
    GOOGLE_CLIENT_SECRET="test-only-no-provider-access", GITHUB_CLIENT_ID="dbcas-e2e-github-client",
    GITHUB_CLIENT_SECRET="test-only-no-provider-access",
    GOOGLE_REDIRECT_URI="http://127.0.0.1:5174/api/v1/auth/oauth/google/callback",
    GITHUB_REDIRECT_URI="http://127.0.0.1:5174/api/v1/auth/oauth/github/callback",
    FRONTEND_URL="http://127.0.0.1:5174",
    CORS_ORIGINS='["http://127.0.0.1:5174"]',
    # Browser gates exercise the real recovery flow against the compose
    # Mailpit inbox; conftest's setdefault keeps these values.
    SMTP_HOST="127.0.0.1", SMTP_PORT="1026",
    SMTP_FROM="DBCAS <no-reply@dbcas.local>")
if os.environ.get("DBCAS_RELEASE_WORKER") != "1":
    os.environ["DBCAS_TEST_RUN_ID"] = uuid.uuid4().hex
    import conftest  # Only the launcher creates UUID-named disposable containers.
    manifest = Path(os.environ.get("DBCAS_TEST_MANIFEST", str(Path(__file__).resolve().parents[3] / "_review/remediation/release-containers.json")))
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"run_id": os.environ["DBCAS_TEST_RUN_ID"], "containers": conftest.OWNED_CONTAINERS}), encoding="utf-8")
import httpx
import psycopg
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.main import app
from app.db import get_db, get_session_factory
from app.deps import AdminOnly, LearnerOnly, get_llm_service
from app.config import Settings, get_settings
from app.migrate import apply_migrations
from app.models import Account, AccountRole, UserProfile, Role, AssessmentSession, Question
from app.security import hash_password, create_access_token
from app.repositories import LlmCacheRepository, AssessmentRepository
from app.services.llm import LLMService, ChatCompletionsProvider
from app.services.sandbox_runner import SandboxRunner
from app.services.blueprints import ensure_all_blueprints
from app.benchmark import import_pack
from app.errors import AppError

TEST_PASSWORD = "ReleaseTest123!"
ADMIN_EMAIL = "release-admin@test.dev"
pack_ids = json.loads(os.environ.get("DBCAS_RELEASE_PACK_IDS", "{}"))
_failed_once = set()
_failure_counts = {}


def _injected_failure(prompt):
    """Deterministically fail a bounded number of provider calls per prompt."""
    marker = re.search(r"\[\[AI_FAIL_(\d+)\]\]", prompt)
    if marker:
        limit = int(marker.group(1))
        used = _failure_counts.get(prompt, 0)
        if used < limit:
            _failure_counts[prompt] = used + 1
            return True
        return False
    # Browser acceptance may force one terminal provider failure per answer so
    # the failure/retry state is observable without a live provider.
    if "[[AI_FAIL_ONCE]]" in prompt and prompt not in _failed_once:
        _failed_once.add(prompt)
        return True
    return False


def provider_response(request):
    body = json.loads(request.content)
    prompt = body["messages"][-1]["content"]
    if _injected_failure(prompt):
        return httpx.Response(400, json={"error": {"message": "Injected test provider failure"}})
    if prompt.startswith("{"):
        data = json.loads(prompt)
        task = data["task"]
        cid = data.get("concept", {}).get("concept_id") or next((c["concept_id"] for c in data["concepts"]
            if c["concept_code"] == "SQL-SELECT"), data["concepts"][0]["concept_id"])
        if task == "map_clo_to_concepts":
            result = {"concept_ids": [cid], "rationale": "The recorded learning outcome covers this concept."}
        elif task == "generate_question_candidates":
            from generation_fixtures import grounded
            from test_llm_release import RUBRICS
            items = []
            for index in range(data["count"]):
                marker = "duplicate" if "[[GEN_DUPLICATE]]" in (data["concept"].get("description") or "") else uuid.uuid4().hex[:10]
                item = {"prompt": f"Release candidate {marker}: explain projection and filtering.",
                        "difficulty_level": {"EASY": 1, "MEDIUM": 3, "HARD": 4}[data["difficulty"]], "points": 1}
                if data["question_type"] == "mcq":
                    item.update(options=[{"option_label": "A", "option_text": "SELECT", "is_correct": True},
                                         {"option_label": "B", "option_text": "DROP", "is_correct": False}])
                elif data["question_type"] == "sql":
                    item.update(reference_answer="SELECT id FROM t", datasets=[
                        {"dataset_name": "base", "setup_sql": "CREATE TABLE t(id int); INSERT INTO t VALUES(1);",
                         "expected_result": {"columns": ["id"], "rows": [[1]]}, "is_edge_case": False},
                        {"dataset_name": "empty", "setup_sql": "CREATE TABLE t(id int);",
                         "expected_result": {"columns": ["id"], "rows": []}, "is_edge_case": True}])
                else:
                    item.update(reference_answer="SELECT projects columns; WHERE filters rows.", rubrics=RUBRICS)
                item = grounded(item, concept_id=cid, locale=data["locale"], source=next(iter(data["sources"])))
                if data["locale"] == "vi":
                    item["prompt"] = f"Bản nháp {marker}: giải thích thao tác chọn cột và lọc hàng."
                    item["explanation"] = "SELECT chọn các cột kết quả; WHERE lọc các hàng."
                    if data["question_type"] == "essay":
                        item["reference_answer"] = item["explanation"]
                        item["rubrics"] = [{**r, "criteria": f"Mức {r['level_name']}: đánh giá sự chính xác của giải thích chọn cột và lọc hàng."} for r in item["rubrics"]]
                if "[[GEN_INVALID]]" in (data["concept"].get("description") or ""):
                    item["source_ids"] = ["fabricated-reference"]
                items.append(item)
            result = {"questions": items}
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


@app.get("/__test/blueprints")
def blueprints(admin: Account = AdminOnly, db: Session = Depends(get_db)):
    from app.models import AssessmentBlueprint
    rows = db.scalars(select(AssessmentBlueprint).order_by(
        AssessmentBlueprint.assessment_id, AssessmentBlueprint.subject_area,
        AssessmentBlueprint.difficulty_band, AssessmentBlueprint.version_no)).all()
    return [{
        "assessment_id": row.assessment_id,
        "subject_area": row.subject_area,
        "difficulty_band": row.difficulty_band,
        "version_no": row.version_no,
        "status": row.status,
        "max_questions": row.max_questions,
        "target_mcq": row.target_mcq,
        "target_sql": row.target_sql,
        "target_essay": row.target_essay,
        "approved_by": row.approved_by,
    } for row in rows]


@app.get("/__test/sessions/{session_id}/assembly")
def session_assembly(session_id: int, learner: Account = LearnerOnly, db: Session = Depends(get_db)):
    """Sanitized assembly evidence for browser assertions.

    Deliberately omits prompts, answer keys, options, references and rubrics.
    """
    session = db.get(AssessmentSession, session_id)
    if session is None or session.learner_id != learner.account_id:
        raise AppError(404, "session_not_found", "Assessment session not found")
    config = session.config_snapshot or {}
    plan = []
    for item in config.get("question_plan") or []:
        question = db.get(Question, item["question_id"])
        plan.append({
            "question_id": item["question_id"],
            "question_type": question.question_type if question else None,
            "difficulty_level": question.difficulty_level if question else None,
            "family_id": question.family_id if question else None,
            "concept_ids": sorted({t.concept_id for t in question.concept_tags if t.confirmed}) if question else [],
        })
    mix = Counter(item["question_type"] for item in plan)
    return {
        "session_id": session.session_id,
        "assessment_id": session.assessment_id,
        "status": session.status,
        "release_status": session.release_status,
        "assembly_mode": config.get("assembly_mode"),
        "selected_concept_ids": config.get("selected_concept_ids"),
        "difficulty": config.get("difficulty"),
        "requested_question_count": config.get("requested_question_count"),
        "max_questions": config.get("max_questions"),
        "blueprint": config.get("blueprint"),
        "blueprint_resolution": config.get("blueprint_resolution"),
        "type_mix": {kind: mix.get(kind, 0) for kind in ("mcq", "sql", "essay")},
        "duplicate_families": len(plan) - len({item["family_id"] or item["question_id"] for item in plan}),
        "plan": plan,
    }


@app.post("/__test/grading-jobs/drain")
def drain_grading_jobs(max_attempts: int = 3, include_essay: bool = True,
                       limit: int = 20, admin: Account = AdminOnly, db: Session = Depends(get_db)):
    from app.services.grading_jobs import process_one
    from app.services.sandbox_runner import SandboxRunner
    if not 1 <= max_attempts <= 5 or not 1 <= limit <= 30:
        raise AppError(422, "fixture_limit", "Use bounded grading attempts and job counts")
    settings = get_settings().model_copy(update={"grading_job_max_attempts": max_attempts})
    processed = 0
    while processed < limit and process_one(db, SandboxRunner(get_settings()), llm_service(db),
                                            include_essay=include_essay, settings=settings):
        processed += 1
    return {"processed": processed}


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
    parser.add_argument("--application", action="store_true",
        help="Serve the unmodified app.main entrypoint without provider fixtures or test routes")
    args = parser.parse_args()
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        apply_migrations(conn)
    with get_session_factory()() as db:
        role = db.query(Role).filter_by(role_name="Administrator").one()
        # This isolated browser-test principal is explicitly provisioned as
        # the role manager required to exercise privileged account flows.
        admin = Account(email=ADMIN_EMAIL, password_hash=hash_password(TEST_PASSWORD), status="active",
            can_manage_roles=True)
        admin.profile = UserProfile(full_name="Release fixture administrator")
        db.add(admin)
        db.flush()
        db.add(AccountRole(account_id=admin.account_id, role_id=role.role_id))
        db.commit()
        snapshot = Path(__file__).with_name("fixtures") / "release_content_snapshot.json"
        if snapshot.exists():
            # Activated academic content, exported read-only from the reviewed
            # bank. Accounts, sessions and attempts are never part of it.
            import release_content
            pack_ids = release_content.load(db, admin.account_id)
            db.commit()
        else:
            pack_ids = import_pack(db, admin, SandboxRunner(get_settings()))
            # Include current PostgreSQL content for bank filters and forward
            # coverage checks, without adding another learner-facing assessment.
            extended = json.loads((conftest.ROOT / 'db/postgres_knowledge_pack.json').read_text(encoding='utf-8'))
            extended['assessments'] = []
            import_pack(db, admin, SandboxRunner(get_settings()), extended)
        # Backfill any published assessment that predates blueprint seeding.
        ensure_all_blueprints(db)
        db.commit()
    os.environ["DBCAS_RELEASE_PACK_IDS"] = json.dumps(pack_ids)
    os.environ["DBCAS_RELEASE_WORKER"] = "1"
    # A separate CLI avoids Windows spawn re-importing the seed launcher.
    entrypoint = "app.main:app" if args.application else "release_server:app"
    app_dir = "." if args.application else "tests"
    if any(os.environ.get(key) for key in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")):
        raise RuntimeError("Live AI configuration must be disabled")
    environment = server_environment()
    # Validate in an actual child before serving; never trust implicit Windows
    # inheritance, which removes empty values and lets .env credentials reappear.
    subprocess.run([sys.executable, "-c",
        "import sys; from app.config import get_settings; s=get_settings(); "
        "sys.exit('Live AI configuration must be disabled' if any((s.llm_api_key,s.llm_base_url,s.llm_model)) else 0)"],
        env=environment, check=True)
    print(f"Browser server entrypoint: {entrypoint}; live AI configuration disabled", flush=True)
    subprocess.run([sys.executable, "-m", "uvicorn", entrypoint, "--app-dir", app_dir,
        "--host", "127.0.0.1", "--port", "8100", "--workers", str(args.workers),
        "--no-access-log", "--log-level", "warning", "--timeout-keep-alive", "15"],
        env=environment, check=True)

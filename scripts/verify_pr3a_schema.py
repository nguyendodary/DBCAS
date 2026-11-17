"""Standalone PR 3A schema verification against an isolated PostgreSQL DSN.

Usage:
  PR3A_TEST_DSN=postgresql://user@host:port/db py -3 scripts/verify_pr3a_schema.py

The script creates a fresh temporary schema for each check and drops it at the
end. It never touches public or a shared schema. In CI, backend/tests/conftest.py
supplies the disposable database; this script can also run without pytest.
"""
import hashlib
import os
import uuid
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db" / "schema.sql"
MIGRATION = ROOT / "db" / "migrations" / "026_pr3a_database_foundation.sql"


def dsn():
    value = os.environ.get("PR3A_TEST_DSN") or os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("PR3A_TEST_DSN or DATABASE_URL is required")
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def h(tag="a"):
    return hashlib.sha256(tag.encode()).hexdigest()


def fresh(conn):
    ns = "pr3a_" + uuid.uuid4().hex[:12]
    conn.execute(f'CREATE SCHEMA "{ns}"')
    conn.execute(f'SET search_path TO "{ns}"')
    conn.execute(SCHEMA.read_text(encoding="utf-8"), prepare=False)
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.migrate import apply_migrations
    applied = apply_migrations(conn)
    assert "026_pr3a_database_foundation.sql" in applied
    return ns


def cleanup(conn, ns):
    conn.execute("SET search_path TO public")
    conn.execute(f'DROP SCHEMA IF EXISTS "{ns}" CASCADE')


def seed_session(conn, *, policy="AI_OFFICIAL_REVIEW"):
    account = conn.execute(
        "INSERT INTO account(email,password_hash) VALUES (%s,%s) RETURNING account_id",
        (f"pr3a-{uuid.uuid4().hex[:8]}@test.local", "not-a-login-hash"),
    ).fetchone()[0]
    session = conn.execute(
        """INSERT INTO assessment_session
             (learner_id,status,expires_at,purpose,purpose_source,review_policy,config_snapshot)
           VALUES (%s,'in_progress',NOW()+INTERVAL '1 hour','TEST','SERVER',%s,'{"version":1}')
           RETURNING session_id""",
        (account, policy),
    ).fetchone()[0]
    return account, session


def seed_question(conn, account, kind, points="1.00"):
    return conn.execute(
        "INSERT INTO question(question_type,prompt,created_by,points) VALUES (%s,%s,%s,%s) RETURNING question_id",
        (kind, f"PR3A {kind}", account, points),
    ).fetchone()[0]


def expect_error(conn, sql, params=None, label="operation"):
    try:
        conn.execute(sql, params or ())
    except psycopg.Error:
        return
    raise AssertionError(f"expected failure: {label}")


def check_migration_text():
    text = MIGRATION.read_text(encoding="utf-8")
    assert "^v2:[1-9][0-9]*$" in text
    assert "LIKE 'v2:%'" not in text
    assert "count()" not in text
    assert "CREATE UNIQUE INDEX" in text
    assert "CREATE CONSTRAINT TRIGGER" in text
    assert "-- ---------------------------------------------------------------------------" in text
    return "migration text audit"


def check_schema_shape(conn):
    ns = fresh(conn)
    try:
        tables = {r[0] for r in conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema=current_schema()"
        )}
        required = {
            "question_rubric_profile", "question_rubric_criterion",
            "attempt_rubric_criterion", "session_result_version",
            "session_result_version_score", "session_result_criterion_score",
            "session_result_publication", "session_result_analysis",
            "ai_stage_run", "ai_stage_validation", "ai_stage_attempt",
            "ai_prompt_record", "ai_prompt_content", "retention_purge_audit",
            "prompt_access_audit",
        }
        assert required <= tables
        idx = [r[0] for r in conn.execute(
            "SELECT indexdef FROM pg_indexes WHERE schemaname=current_schema() AND indexname='ai_stage_run_active_session_idx'"
        )]
        assert idx and "session_id" in idx[0] and "scope_key" in idx[0]
        pub_cols = {r[0] for r in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='session_result_publication'"
        )}
        assert {"session_id", "result_version_id", "state", "state_revision"} <= pub_cols
        return "schema shape and session-scoped index"
    finally:
        cleanup(conn, ns)


def check_ai_uniqueness_and_ordering(conn):
    ns = fresh(conn)
    try:
        a1, s1 = seed_session(conn)
        a2, s2 = seed_session(conn)
        h1 = h("run1")
        conn.execute(
            """INSERT INTO ai_stage_run(session_id,scope_key,stage,run_mode,execution_run_no,status,input_hash)
               VALUES (%s,'v1','AI1','V1_GRADING',1,'PENDING',%s)""",
            (s1, h1),
        )
        conn.execute(
            """INSERT INTO ai_stage_run(session_id,scope_key,stage,run_mode,execution_run_no,status,input_hash)
               VALUES (%s,'v1','AI1','V1_GRADING',1,'PENDING',%s)""",
            (s2, h1),
        )
        expect_error(conn,
            """INSERT INTO ai_stage_run(session_id,scope_key,stage,run_mode,execution_run_no,status,input_hash)
               VALUES (%s,'v1','AI1','V1_GRADING',2,'PENDING',%s)""",
            (s1, h("dup")), "duplicate active run in one session")
        expect_error(conn,
            """INSERT INTO ai_stage_run(session_id,scope_key,stage,run_mode,execution_run_no,status,input_hash)
               VALUES (%s,'v2:01','AI1','V2_ANALYSIS',1,'PENDING',%s)""",
            (s1, h("bad")), "invalid v2 scope regex")
        expect_error(conn,
            """INSERT INTO ai_stage_run(session_id,scope_key,stage,run_mode,execution_run_no,status,input_hash)
               VALUES (%s,'v2:1','AI1','V1_GRADING',1,'PENDING',%s)""",
            (s1, h("bad2")), "scope/run_mode mismatch")

        run1 = conn.execute(
            "SELECT stage_run_id FROM ai_stage_run WHERE session_id=%s", (s1,)
        ).fetchone()[0]
        # Invalid validation cannot unlock AI2.
        validation = conn.execute(
            """INSERT INTO ai_stage_validation(session_id,stage_run_id,validator_version,input_hash,output_hash,status)
               VALUES (%s,%s,'v1',%s,%s,'INVALID') RETURNING validation_id""",
            (s1, run1, h1, h1),
        ).fetchone()[0]
        expect_error(conn,
            """INSERT INTO ai_stage_run(session_id,scope_key,stage,run_mode,execution_run_no,status,input_hash,predecessor_validation_id)
               VALUES (%s,'v1','AI2','V1_GRADING',1,'PENDING',%s,%s)""",
            (s1, h("ai2"), validation), "AI2 with invalid AI1 validation")

        # A different session has its own immutable VALID validation.
        run2 = conn.execute(
            "SELECT stage_run_id FROM ai_stage_run WHERE session_id=%s", (s2,)
        ).fetchone()[0]
        conn.execute(
            "UPDATE ai_stage_run SET status='COMPLETED', output_hash=%s WHERE stage_run_id=%s",
            (h1, run2),
        )
        valid_validation = conn.execute(
            """INSERT INTO ai_stage_validation(session_id,stage_run_id,validator_version,input_hash,output_hash,status)
               VALUES (%s,%s,'v1',%s,%s,'VALID') RETURNING validation_id""",
            (s2, run2, h1, h1),
        ).fetchone()[0]
        conn.execute(
            """INSERT INTO ai_stage_run(session_id,scope_key,stage,run_mode,execution_run_no,status,input_hash,predecessor_validation_id)
               VALUES (%s,'v1','AI2','V1_GRADING',1,'PENDING',%s,%s)""",
            (s2, h("ai2"), valid_validation),
        )
        return "AI run uniqueness, regex, and AI2 ordering"
    finally:
        cleanup(conn, ns)


def seed_valid_result(conn, *, swap_plan=False, omit_essay_criterion=False):
    account, session = seed_session(conn)
    mcq = seed_question(conn, account, "mcq")
    essay = seed_question(conn, account, "essay")
    if swap_plan:
        conn.execute(
            "INSERT INTO session_question_plan(session_id,seq_no,question_id) VALUES (%s,1,%s),(%s,2,%s)",
            (session, mcq, session, essay),
        )
        conn.execute(
            """INSERT INTO attempt(session_id,question_id,seq_no,question_snapshot)
               VALUES (%s,%s,1,jsonb_build_object('question_type','essay','points','1.00','rubric_snapshot_hash',%s::text)),
                      (%s,%s,2,jsonb_build_object('question_type','mcq','points','1.00'))""",
            (session, essay, h("snap"), session, mcq),
        )
    else:
        conn.execute(
            "INSERT INTO session_question_plan(session_id,seq_no,question_id) VALUES (%s,1,%s),(%s,2,%s)",
            (session, mcq, session, essay),
        )
        conn.execute(
            """INSERT INTO attempt(session_id,question_id,seq_no,question_snapshot)
               VALUES (%s,%s,1,jsonb_build_object('question_type','mcq','points','1.00')),
                      (%s,%s,2,jsonb_build_object('question_type','essay','points','1.00','rubric_snapshot_hash',%s::text))""",
            (session, mcq, session, essay, h("snap")),
        )
    attempts = conn.execute(
        "SELECT attempt_id, seq_no FROM attempt WHERE session_id=%s ORDER BY seq_no", (session,)
    ).fetchall()
    mcq_attempt = attempts[1][0] if swap_plan else attempts[0][0]
    essay_attempt = attempts[0][0] if swap_plan else attempts[1][0]

    profile = conn.execute(
        """INSERT INTO question_rubric_profile(question_id,version_no,status,profile_hash,created_by)
           VALUES (%s,1,'active',%s,%s) RETURNING rubric_profile_id""",
        (essay, h("profile"), account),
    ).fetchone()[0]
    criterion = conn.execute(
        """INSERT INTO question_rubric_criterion(rubric_profile_id,criterion_code,criterion_name,description,scoring_guidance,max_points,sort_order,criterion_hash)
           VALUES (%s,'C1','Criterion','Desc','Guidance',1.00,1,%s) RETURNING criterion_id""",
        (profile, h("criterion")),
    ).fetchone()[0]
    conn.execute(
        """INSERT INTO attempt_rubric_criterion(session_id,attempt_id,question_id,rubric_profile_id,criterion_id,criterion_code,criterion_name,description,scoring_guidance,max_points,sort_order,profile_snapshot_hash,criterion_hash)
           VALUES (%s,%s,%s,%s,%s,'C1','Criterion','Desc','Guidance',1.00,1,%s,%s)""",
        (session, essay_attempt, essay, profile, criterion, h("snap"), h("criterion")),
    )
    version = conn.execute(
        """INSERT INTO session_result_version(session_id,version_no,source,total_score,max_score,result_hash,approved_review_revision)
           VALUES (%s,1,'V1',2.00,2.00,%s,0) RETURNING result_version_id""",
        (session, h("result")),
    ).fetchone()[0]
    conn.execute(
        """INSERT INTO session_result_version_score(session_id,result_version_id,attempt_id,score,max_score,source)
           VALUES (%s,%s,%s,1.00,1.00,'MACHINE'),(%s,%s,%s,1.00,1.00,'AI2')""",
        (session, version, mcq_attempt, session, version, essay_attempt),
    )
    if not omit_essay_criterion:
        conn.execute(
            """INSERT INTO session_result_criterion_score(session_id,result_version_id,attempt_id,criterion_snapshot_id,score,max_points)
               VALUES (%s,%s,%s,%s,1.00,1.00)""",
            (session, version, essay_attempt, criterion),
        )
    return session, version, mcq_attempt, essay_attempt


def check_result_completeness(conn):
    ns = fresh(conn)
    try:
        with conn.transaction():
            session, version, _, _ = seed_valid_result(conn)
        with conn.transaction():
            conn.execute(
                """INSERT INTO session_result_publication(result_version_id,session_id,state,state_revision)
                   VALUES (%s,%s,'APPROVED_PENDING_ANALYSIS',0)""",
                (version, session),
            )
        conn.execute(
            """UPDATE session_result_publication SET state='OFFICIAL' WHERE result_version_id=%s""",
            (version,),
        )
        conn.execute(
            "UPDATE assessment_session SET current_result_version_id=%s WHERE session_id=%s",
            (version, session),
        )
        expect_error(conn,
            "UPDATE session_result_publication SET state='ANALYSIS_FAILED' WHERE result_version_id=%s",
            (version,), "invalid OFFICIAL to ANALYSIS_FAILED transition")
        expect_error(conn,
            "UPDATE session_result_version_score SET score=0.5 WHERE result_version_id=%s",
            (version,), "immutable score update")
        conn.execute(
            "UPDATE attempt SET score=1.00 WHERE attempt_id IN (SELECT attempt_id FROM attempt WHERE session_id=%s LIMIT 1)",
            (session,),
        )
        expect_error(conn,
            "UPDATE attempt SET seq_no=9 WHERE session_id=%s AND seq_no=1",
            (session,), "structural attempt freeze")
        expect_error(conn,
            """INSERT INTO attempt(session_id,question_id,seq_no,question_snapshot)
               SELECT session_id,question_id,9,'{"question_type":"mcq","points":"1.00"}'::jsonb
               FROM attempt WHERE session_id=%s LIMIT 1""",
            (session,), "attempt insert after version")
        return "complete result, publication transition, and attempt freeze"
    finally:
        cleanup(conn, ns)


def check_completeness_failures(conn):
    ns = fresh(conn)
    try:
        with conn.transaction():
            seed_valid_result(conn, omit_essay_criterion=True)
        raise AssertionError("missing criterion should fail deferred validation")
    except psycopg.Error:
        pass
    cleanup(conn, ns)

    ns = fresh(conn)
    try:
        with conn.transaction():
            seed_valid_result(conn, swap_plan=True)
        raise AssertionError("plan/attempt identity mismatch should fail")
    except psycopg.Error:
        pass
    return "deferred completeness rejects missing criterion and plan identity mismatch"


def check_legacy_workflow(conn):
    ns = fresh(conn)
    try:
        _, session = seed_session(conn, policy="LEGACY")
        question = seed_question(conn, conn.execute("SELECT account_id FROM account LIMIT 1").fetchone()[0], "mcq")
        conn.execute(
            "INSERT INTO attempt(session_id,question_id,seq_no,question_snapshot) VALUES (%s,%s,1,'{\"question_type\":\"mcq\"}')",
            (session, question),
        )
        conn.execute(
            "UPDATE attempt SET draft_answer='{\"selected_option_id\":1}' WHERE session_id=%s",
            (session,),
        )
        conn.execute("DELETE FROM attempt WHERE session_id=%s", (session,))
        conn.execute(
            "INSERT INTO attempt(session_id,question_id,seq_no,question_snapshot) VALUES (%s,%s,1,'{\"question_type\":\"mcq\"}')",
            (session, question),
        )
        return "legacy non-structural and structural attempt operations"
    finally:
        cleanup(conn, ns)


def main():
    results = []
    with psycopg.connect(dsn(), autocommit=True) as conn:
        results.append(check_migration_text())
        results.append(check_schema_shape(conn))
        results.append(check_ai_uniqueness_and_ordering(conn))
        results.append(check_result_completeness(conn))
        results.append(check_completeness_failures(conn))
        results.append(check_legacy_workflow(conn))
    for item in results:
        print(f"PASS: {item}")
    print(f"PASS: {len(results)} PR 3A schema checks")


if __name__ == "__main__":
    main()

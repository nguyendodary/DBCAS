"""Migration 027: review-flow tables, guards and schema.sql equivalence.

The tests use the disposable PostgreSQL provisioned by conftest.py. Every
case builds its own isolated schema so the real application schema and data
are never touched.
"""
import os
import uuid
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "db" / "schema.sql"
MIGRATION = ROOT / "db" / "migrations" / "027_review_flow.sql"

TABLES_SQL = """select c.relname from pg_class c
 join pg_namespace n on n.oid=c.relnamespace
 where n.nspname=current_schema() and c.relkind='r' and c.relpersistence='p'
 order by c.relname collate "C" """
COLUMNS_SQL = """select table_name, column_name, data_type, udt_name, is_nullable,
 column_default, is_identity, character_maximum_length, numeric_precision, numeric_scale
 from information_schema.columns
 where table_schema=current_schema() and table_name<>'schema_migration'
 order by table_name, column_name"""
CONSTRAINTS_SQL = """select c.relname, con.conname, con.contype, pg_get_constraintdef(con.oid)
 from pg_constraint con join pg_class c on c.oid=con.conrelid
 join pg_namespace n on n.oid=c.relnamespace
 where n.nspname=current_schema() and c.relname<>'schema_migration'
 order by c.relname, con.conname collate "C" """
INDEXES_SQL = """select tablename, indexname,
 regexp_replace(indexdef, current_schema(), 'SCHEMA', 'g')
 from pg_indexes
 where schemaname=current_schema() and tablename<>'schema_migration'
 order by tablename collate "C", indexname collate "C" """
TRIGGERS_SQL = """select c.relname, t.tgname,
 regexp_replace(pg_get_triggerdef(t.oid), current_schema(), 'SCHEMA', 'g')
 from pg_trigger t join pg_class c on c.oid=t.tgrelid
 join pg_namespace n on n.oid=c.relnamespace
 where n.nspname=current_schema() and not t.tgisinternal and c.relname<>'schema_migration'
 order by c.relname collate "C", t.tgname collate "C" """
SHAPE = {"tables": TABLES_SQL, "columns": COLUMNS_SQL, "constraints": CONSTRAINTS_SQL,
         "indexes": INDEXES_SQL, "triggers": TRIGGERS_SQL}


def _dsn():
    value = os.environ.get("DATABASE_URL") or os.environ.get("PR3A_TEST_DSN")
    assert value, "DATABASE_URL is required"
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def _shape(conn):
    return {kind: tuple(tuple(r) for r in conn.execute(sql).fetchall())
            for kind, sql in SHAPE.items()}


def _fresh(conn):
    """Create an isolated schema with the full schema.sql (including 027)."""
    ns = "p27_" + uuid.uuid4().hex[:10]
    conn.execute(f'CREATE SCHEMA "{ns}"')
    conn.execute(f'SET search_path TO "{ns}"')
    conn.execute(SCHEMA.read_text(encoding="utf-8"), prepare=False)
    return ns


def _drop(conn, ns):
    conn.execute("SET search_path TO public")
    conn.execute(f'DROP SCHEMA IF EXISTS "{ns}" CASCADE')


def _seed(conn, *, state="OFFICIAL", published_interval="NOW()"):
    """Seed learner/admin, a FIXED TEST session and its v1 publication.

    Runs in one transaction: 026 freezes attempts after a result version exists
    and validates result completeness at commit.
    """
    conn.autocommit = False
    try:
        learner = conn.execute(
            "INSERT INTO account(email,password_hash) VALUES (%s,'x') RETURNING account_id",
            (f"learner-{uuid.uuid4().hex[:8]}@test.local",),
        ).fetchone()[0]
        admin = conn.execute(
            "INSERT INTO account(email,password_hash) VALUES (%s,'x') RETURNING account_id",
            (f"admin-{uuid.uuid4().hex[:8]}@test.local",),
        ).fetchone()[0]
        role = conn.execute(
            """INSERT INTO role(role_name,description) VALUES ('Administrator','test')
               ON CONFLICT (role_name) DO UPDATE SET description=role.description
               RETURNING role_id"""
        ).fetchone()[0]
        conn.execute("INSERT INTO account_role(account_id,role_id) VALUES (%s,%s)", (admin, role))
        session = conn.execute(
            """INSERT INTO assessment_session
                 (learner_id,status,expires_at,purpose,purpose_source,review_policy,config_snapshot)
               VALUES (%s,'completed',NOW()+INTERVAL '1 hour','TEST','SERVER',
                       'AI_OFFICIAL_REVIEW','{"assessment_style":"FIXED"}')
               RETURNING session_id""",
            (learner,),
        ).fetchone()[0]
        question = conn.execute(
            """INSERT INTO question(question_type,prompt,created_by,points)
               VALUES ('mcq','prompt',%s,10.00) RETURNING question_id""",
            (admin,),
        ).fetchone()[0]
        attempt = conn.execute(
            """INSERT INTO attempt(session_id,question_id,seq_no,question_snapshot)
               VALUES (%s,%s,1,'{"question_type":"mcq","points":"10.00"}'::jsonb)
               RETURNING attempt_id""",
            (session, question),
        ).fetchone()[0]
        version = conn.execute(
            """INSERT INTO session_result_version
                 (session_id,version_no,source,total_score,max_score,result_hash)
               VALUES (%s,1,'V1',0.00,10.00,%s) RETURNING result_version_id""",
            (session, "a" * 64),
        ).fetchone()[0]
        conn.execute(
            """INSERT INTO session_result_version_score
                 (session_id,result_version_id,attempt_id,score,max_score,source)
               VALUES (%s,%s,%s,0.00,10.00,'MACHINE')""",
            (session, version, attempt),
        )
        if state == "OFFICIAL":
            conn.execute(
                """INSERT INTO session_result_publication
                     (result_version_id,session_id,state,published_at)
                   VALUES (%s,%s,'OFFICIAL',%s)""",
                (version, session, published_interval),
            )
        else:
            conn.execute(
                """INSERT INTO session_result_publication
                     (result_version_id,session_id,state)
                   VALUES (%s,%s,%s)""",
                (version, session, state),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
    return {"learner": learner, "admin": admin, "session": session,
            "version": version, "question": question, "attempt": attempt}


def _request(conn, seed, *, origin="ADMIN", key=None, status="REQUESTED"):
    return conn.execute(
        """INSERT INTO review_request
             (session_id,learner_id,requested_by,origin,request_key,reason,
              status,base_result_version_id)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING review_request_id""",
        (seed["session"], seed["learner"], seed["admin"], origin,
         key or uuid.uuid4(), "Please review this result", status, seed["version"]),
    ).fetchone()[0]


def _expect_error(conn, sql, params, label):
    try:
        conn.execute(sql, params)
    except psycopg.Error:
        return
    raise AssertionError(f"expected database rejection: {label}")


def test_027_migration_is_idempotent_and_mirrors_schema_sql():
    """Re-applying 027 to the committed schema.sql is a catalog no-op."""
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            before = _shape(conn)
            conn.execute(MIGRATION.read_text(encoding="utf-8"), prepare=False)
            conn.execute(MIGRATION.read_text(encoding="utf-8"), prepare=False)
            after = _shape(conn)
        finally:
            _drop(conn, ns)
    for kind in SHAPE:
        assert before[kind] == after[kind], f"027 re-application changed {kind}"


def test_027_review_tables_and_columns_exist():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            tables = {r[0] for r in conn.execute(TABLES_SQL)}
            assert {"review_request", "question_report", "review_deviation"} <= tables
            cols = {r[1] for r in conn.execute(COLUMNS_SQL).fetchall()
                    if r[0] == "review_request"}
            assert {"request_key", "window_expires_at", "claim_expires_at",
                    "regraded_result_version_id", "revision"} <= cols
        finally:
            _drop(conn, ns)


def test_027_one_request_per_session():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            seed = _seed(conn)
            _request(conn, seed)
            _expect_error(
                conn,
                """INSERT INTO review_request
                     (session_id,learner_id,requested_by,origin,request_key,reason,
                      status,base_result_version_id)
                   VALUES (%s,%s,%s,'ADMIN',%s,%s,'REQUESTED',%s)""",
                (seed["session"], seed["learner"], seed["admin"], uuid.uuid4(),
                 "Second request", seed["version"]),
                "second request for one session",
            )
        finally:
            _drop(conn, ns)


def test_027_learner_window_and_official_base():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            # Non-OFFICIAL base is rejected for learner origin.
            pending = _seed(conn, state="APPROVED_PENDING_ANALYSIS")
            _expect_error(conn, """INSERT INTO review_request
                 (session_id,learner_id,requested_by,origin,request_key,reason,base_result_version_id)
                 VALUES (%s,%s,%s,'LEARNER',%s,%s,%s)""",
                (pending["session"], pending["learner"], pending["learner"], uuid.uuid4(),
                 "Please review this result", pending["version"]),
                "learner request on non-OFFICIAL base")

            # Exactly seven days is still inside the window. The update and the
            # insert share one transaction so NOW() is the same server clock.
            import datetime as _dt
            exact = _seed(conn)
            conn.autocommit = False
            try:
                conn.execute(
                    """UPDATE session_result_publication
                       SET published_at = NOW() - INTERVAL '7 days'
                       WHERE result_version_id=%s""",
                    (exact["version"],),
                )
                request_id = _request(conn, exact, origin="LEARNER", key=uuid.uuid4())
                window = conn.execute(
                    "SELECT window_expires_at FROM review_request WHERE review_request_id=%s",
                    (request_id,),
                ).fetchone()[0]
                published = conn.execute(
                    "SELECT published_at FROM session_result_publication WHERE result_version_id=%s",
                    (exact["version"],),
                ).fetchone()[0]
                assert window == published + _dt.timedelta(days=7)
                conn.commit()
            finally:
                conn.autocommit = True

            # One second past the window is rejected.
            late = _seed(conn)
            conn.autocommit = False
            try:
                conn.execute(
                    """UPDATE session_result_publication
                       SET published_at = NOW() - INTERVAL '7 days 1 second'
                       WHERE result_version_id=%s""",
                    (late["version"],),
                )
                try:
                    _request(conn, late, origin="LEARNER", key=uuid.uuid4())
                except psycopg.Error:
                    conn.rollback()
                else:
                    raise AssertionError("expected learner request past the window to fail")
            finally:
                conn.autocommit = True
        finally:
            _drop(conn, ns)


def test_027_identity_and_status_transitions():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            seed = _seed(conn)
            request_id = _request(conn, seed)

            # Identity columns cannot change.
            _expect_error(conn, "UPDATE review_request SET reason=%s WHERE review_request_id=%s",
                          ("changed reason", request_id), "immutable reason")

            # Illegal jump.
            _expect_error(conn, "UPDATE review_request SET status='REGRADED' WHERE review_request_id=%s",
                          (request_id,), "REQUESTED to REGRADED")

            # Legal claim.
            conn.execute(
                """UPDATE review_request
                   SET status='IN_REVIEW', claimed_by=%s, claimed_at=NOW(),
                       claim_expires_at=NOW()+INTERVAL '30 minutes'
                   WHERE review_request_id=%s""",
                (seed["admin"], request_id),
            )
            assert conn.execute("SELECT revision FROM review_request WHERE review_request_id=%s",
                                (request_id,)).fetchone()[0] == 1

            # Legal lease timeout release.
            conn.execute("UPDATE review_request SET status='REQUESTED' WHERE review_request_id=%s",
                         (request_id,))
            assert conn.execute("SELECT revision FROM review_request WHERE review_request_id=%s",
                                (request_id,)).fetchone()[0] == 2

            # Legal rejection.
            conn.execute(
                """UPDATE review_request
                   SET status='REJECTED', resolved_by=%s, resolved_at=NOW(), resolution_note=%s
                   WHERE review_request_id=%s""",
                (seed["admin"], "No change required", request_id),
            )
            assert conn.execute("SELECT revision FROM review_request WHERE review_request_id=%s",
                                (request_id,)).fetchone()[0] == 3

            # Terminal rows are frozen.
            _expect_error(conn, "UPDATE review_request SET resolution_note=%s WHERE review_request_id=%s",
                          ("edited later", request_id), "terminal review request update")
            _expect_error(conn, "DELETE FROM review_request WHERE review_request_id=%s",
                          (request_id,), "review request delete")
        finally:
            _drop(conn, ns)


def test_027_question_report_uniqueness_and_transitions():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            seed = _seed(conn)
            request_id = _request(conn, seed)
            conn.execute(
                """INSERT INTO question_report
                     (review_request_id,session_id,attempt_id,question_id,reported_by,category,details)
                   VALUES (%s,%s,%s,%s,%s,'WRONG_ANSWER',%s)""",
                (request_id, seed["session"], seed["attempt"], seed["question"],
                 seed["admin"], "The answer key is wrong"),
            )
            _expect_error(conn, """INSERT INTO question_report
                 (review_request_id,session_id,attempt_id,question_id,reported_by,category,details)
                 VALUES (%s,%s,%s,%s,%s,'WRONG_ANSWER',%s)""",
                (request_id, seed["session"], seed["attempt"], seed["question"],
                 seed["admin"], "Duplicate report"),
                "duplicate question report")

            # A non-OPEN status requires resolved_at.
            _expect_error(conn, """UPDATE question_report SET status='ACCEPTED'
                 WHERE session_id=%s AND attempt_id=%s""",
                (seed["session"], seed["attempt"]), "ACCEPTED without resolved_at")
            conn.execute("""UPDATE question_report
                 SET status='ACCEPTED', resolved_at=NOW(), resolved_by=%s,
                     resolution_note='Confirmed'
                 WHERE session_id=%s AND attempt_id=%s""",
                (seed["admin"], seed["session"], seed["attempt"]))
            _expect_error(conn, """UPDATE question_report SET status='REJECTED'
                 WHERE session_id=%s AND attempt_id=%s""",
                (seed["session"], seed["attempt"]), "ACCEPTED to REJECTED")
            _expect_error(conn, "DELETE FROM question_report WHERE session_id=%s",
                          (seed["session"],), "question report delete")
        finally:
            _drop(conn, ns)


def test_027_review_deviation_constraints():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            def new_case():
                seed = _seed(conn)
                request_id = _request(conn, seed)
                return seed, request_id

            def insert_deviation(seed, request_id, *, ai, reviewed, max_points, ratio,
                                 reason, second_admin=None,
                                 confirmation="SECOND_ADMIN"):
                conn.execute(
                    """INSERT INTO review_deviation
                         (review_request_id,session_id,attempt_id,ai_score,reviewed_score,
                          max_points,deviation_ratio,reason,first_reviewer_id,
                          second_reviewer_id,confirmation)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (request_id, seed["session"], seed["attempt"], ai, reviewed,
                     max_points, ratio, reason, seed["admin"], second_admin, confirmation),
                )

            second = conn.execute(
                "INSERT INTO account(email,password_hash) VALUES (%s,'x') RETURNING account_id",
                (f"second-{uuid.uuid4().hex[:8]}@test.local",),
            ).fetchone()[0]

            # Valid second-admin path.
            seed, request_id = new_case()
            insert_deviation(seed, request_id, ai=0, reviewed=3.10, max_points=10,
                             ratio=0.31, reason="Substantial rubric correction",
                             second_admin=second)

            # 0.30 exactly is rejected (threshold is strictly greater).
            seed, request_id = new_case()
            _expect_error(
                conn,
                """INSERT INTO review_deviation
                     (review_request_id,session_id,attempt_id,ai_score,reviewed_score,
                      max_points,deviation_ratio,reason,first_reviewer_id,
                      second_reviewer_id,confirmation)
                   VALUES (%s,%s,%s,0,3.00,10,0.30,'Boundary',%s,%s,'SECOND_ADMIN')""",
                (request_id, seed["session"], seed["attempt"], seed["admin"], second),
                "deviation ratio at 0.30",
            )

            # The same admin cannot confirm their own change.
            seed, request_id = new_case()
            _expect_error(
                conn,
                """INSERT INTO review_deviation
                     (review_request_id,session_id,attempt_id,ai_score,reviewed_score,
                      max_points,deviation_ratio,reason,first_reviewer_id,
                      second_reviewer_id,confirmation)
                   VALUES (%s,%s,%s,0,3.10,10,0.31,'Self confirm',%s,%s,'SECOND_ADMIN')""",
                (request_id, seed["session"], seed["attempt"], seed["admin"], seed["admin"]),
                "self second-admin confirmation",
            )

            # Single-admin long reason needs 120 trimmed characters.
            seed, request_id = new_case()
            _expect_error(
                conn,
                """INSERT INTO review_deviation
                     (review_request_id,session_id,attempt_id,ai_score,reviewed_score,
                      max_points,deviation_ratio,reason,first_reviewer_id,confirmation)
                   VALUES (%s,%s,%s,0,3.10,10,0.31,%s,%s,'SINGLE_ADMIN_LONG_REASON')""",
                (request_id, seed["session"], seed["attempt"], "x" * 119, seed["admin"]),
                "single-admin reason too short",
            )
            seed, request_id = new_case()
            conn.execute(
                """INSERT INTO review_deviation
                     (review_request_id,session_id,attempt_id,ai_score,reviewed_score,
                      max_points,deviation_ratio,reason,first_reviewer_id,confirmation)
                   VALUES (%s,%s,%s,0,3.10,10,0.31,%s,%s,'SINGLE_ADMIN_LONG_REASON')""",
                (request_id, seed["session"], seed["attempt"], "x" * 120, seed["admin"]),
            )

            # Append-only.
            _expect_error(conn, "UPDATE review_deviation SET reason='edited'",
                          (), "review deviation update")
            _expect_error(conn, "DELETE FROM review_deviation", (), "review deviation delete")
        finally:
            _drop(conn, ns)


def test_027_other_active_admins_contract():
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        ns = _fresh(conn)
        try:
            seed = _seed(conn)
            assert conn.execute("SELECT pr3a_other_active_admins(%s)", (seed["admin"],)).fetchone()[0] == 0
            other = conn.execute(
                "INSERT INTO account(email,password_hash) VALUES (%s,'x') RETURNING account_id",
                (f"other-{uuid.uuid4().hex[:8]}@test.local",),
            ).fetchone()[0]
            role = conn.execute("SELECT role_id FROM role WHERE role_name='Administrator'").fetchone()[0]
            conn.execute("INSERT INTO account_role(account_id,role_id) VALUES (%s,%s)", (other, role))
            assert conn.execute("SELECT pr3a_other_active_admins(%s)", (seed["admin"],)).fetchone()[0] == 1
        finally:
            _drop(conn, ns)

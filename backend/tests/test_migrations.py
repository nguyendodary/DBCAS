"""Existing-volume upgrades in isolated schemas, never the developer database."""
import re
import uuid
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import text

from app.config import ROOT_DIR, get_settings
from app.migrate import apply_migrations
from app.models import Account, AssessmentSession, Attempt, Base


def schema_shape(conn):
    return conn.execute("""SELECT table_name,column_name,data_type,character_maximum_length,is_nullable
      FROM information_schema.columns WHERE table_schema=current_schema()
      ORDER BY table_name,column_name""").fetchall()


def ddl_for(variant):
    if variant == "current":
        return (ROOT_DIR / "db/schema.sql").read_text()
    sql = (Path(__file__).parent / "fixtures/schema_20261011.sql").read_text()
    missing = ["concept_dependency"]
    if variant == "pre_oauth":
        missing.append("account_identity")
    for table in missing:
        sql = re.sub(r"CREATE TABLE " + table + r" \(.*?\);", "", sql, flags=re.S)
        sql = re.sub(r"ALTER TABLE " + table + r" .*?;", "", sql)
    return sql


@pytest.mark.parametrize("variant", ["fresh", "pre_oauth", "post_oauth", "current"])
def test_migration_matrix_preserves_data_and_is_repeatable(variant):
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    namespace = "migration_" + uuid.uuid4().hex[:12]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            if variant == "fresh":
                conn.execute((ROOT_DIR / "db/schema.sql").read_text(), prepare=False)
            else:
                conn.execute(ddl_for(variant), prepare=False)
            conn.execute("INSERT INTO account(email,password_hash) VALUES ('preserved@migration.test','not-a-login-hash')")
            conn.execute("INSERT INTO concept(concept_code,concept_name,subject_area) VALUES ('KEEP','Preserve this concept','SQL Querying')")
            first = apply_migrations(conn)
            assert len(first) >= 3
            assert apply_migrations(conn) == []
            assert conn.execute("SELECT count(*) FROM role WHERE role_name IN ('Learner','Administrator')").fetchone()[0] == 2
            assert conn.execute("SELECT email FROM account").fetchone()[0] == "preserved@migration.test"
            assert conn.execute("SELECT concept_code FROM concept").fetchone()[0] == "KEEP"
            # Direct rerun is also safe; no duplicate OAuth FKs appear.
            conn.execute((ROOT_DIR / "db/migrations/001_account_identity.sql").read_text(), prepare=False)
            assert conn.execute("SELECT count(*) FROM pg_constraint WHERE conrelid='account_identity'::regclass AND contype='f'").fetchone()[0] == 1
            assert conn.execute("SELECT to_regclass('concept_dependency')").fetchone()[0]
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='attempt' AND column_name IN ('draft_answer','question_snapshot','grading_status')").fetchone()[0] == 3
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='assessment_session' AND column_name='locale'").fetchone()[0] == 1
            assert conn.execute("SELECT can_manage_roles FROM account WHERE email='preserved@migration.test'").fetchone()[0] is False
            assert conn.execute("SELECT to_regclass('account_role_audit')").fetchone()[0]
            assert conn.execute("SELECT count(*) FROM pg_trigger WHERE tgrelid='account_role_audit'::regclass AND tgname='account_role_audit_immutable'").fetchone()[0] == 1
            assert conn.execute("SELECT to_regclass('question_translation')").fetchone()[0]
            # Compare complete upgraded shape with an independently initialized fresh schema.
            actual = schema_shape(conn)
            reference = namespace + "_reference"
            conn.execute(f'CREATE SCHEMA "{reference}"')
            conn.execute(f'SET search_path TO "{reference}"')
            conn.execute((ROOT_DIR / "db/schema.sql").read_text(), prepare=False)
            apply_migrations(conn)
            assert schema_shape(conn) == actual
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{reference}" CASCADE')
        finally:
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')


def test_core_orm_constraints_and_types_match_ddl(db_session):
    assert any(c.__class__.__name__ == "UniqueConstraint" and {x.name for x in c.columns} == {"provider", "provider_user_id"} for c in Base.metadata.tables["account_identity"].constraints)
    assert any(c.__class__.__name__ == "UniqueConstraint" for c in Base.metadata.tables["attempt"].constraints)
    assert Base.metadata.tables["account"].c.email.type.length == 255
    assert Base.metadata.tables["assessment_session"].c.expires_at.type.timezone
    assert db_session.scalar(text("SELECT to_regclass('grading_job')"))


def test_snapshot_context_is_immutable_in_database(db_session):
    # The trigger protects even accidental repository updates outside normal guards.
    db_session.execute(text("INSERT INTO account(email,password_hash) VALUES ('snapshot@migration.test','not-a-login-hash')"))
    aid = db_session.scalar(text("SELECT account_id FROM account LIMIT 1"))
    db_session.execute(text("INSERT INTO assessment(title,created_by) VALUES ('Snapshot',:aid)"), {"aid": aid})
    assessment_id = db_session.scalar(text("SELECT assessment_id FROM assessment LIMIT 1"))
    db_session.execute(text("INSERT INTO assessment_session(assessment_id,learner_id,expires_at,config_snapshot) VALUES (:a,:u,NOW()+INTERVAL '1 hour',jsonb_build_object('version',1))"), {"a": assessment_id, "u": aid})
    db_session.commit()
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text("UPDATE assessment_session SET config_snapshot=jsonb_build_object('version',2)"))
    assert db_session.scalar(text("SELECT config_snapshot->>'version' FROM assessment_session")) == "1"
    with pytest.raises(Exception):
        with db_session.begin_nested():
            db_session.execute(text("UPDATE assessment_session SET locale='vi'"))
    assert db_session.scalar(text("SELECT locale FROM assessment_session")) == "en"


def test_supervisor_upgrade_preserves_completed_evidence_and_fails_closed_for_new_rows():
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    namespace = "supervisor_migration_" + uuid.uuid4().hex[:12]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((Path(__file__).parent / "fixtures/schema_20261011.sql").read_text(), prepare=False)
            conn.execute("INSERT INTO account(email,password_hash) VALUES ('historical@migration.test','not-a-login-hash')")
            conn.execute("INSERT INTO assessment(title,created_by) VALUES ('Historical rules',1)")
            conn.execute("INSERT INTO question(question_type,prompt,created_by,points) VALUES ('mcq','Preserved question',1,1)")
            for status, score in (("completed", 1), ("completed", None), ("in_progress", None)):
                sid = conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,status,expires_at) VALUES (1,1,%s,NOW()+INTERVAL '1 hour') RETURNING session_id", (status,)).fetchone()[0]
                conn.execute("INSERT INTO attempt(session_id,question_id,seq_no,score,submitted_at) VALUES (%s,1,1,%s,NOW())", (sid, score))
            apply_migrations(conn)
            assert conn.execute("SELECT release_status FROM assessment_session ORDER BY session_id").fetchall() == [("published",), ("auto_grading",), ("unsubmitted",)]
            assert conn.execute("SELECT score FROM attempt ORDER BY attempt_id").fetchall() == [(1,), (None,), (None,)]
            assert conn.execute("SELECT count(*) FROM attempt WHERE question_snapshot->>'prompt'='Preserved question'").fetchone()[0] == 3
            snapshots = conn.execute("SELECT question_snapshot FROM attempt ORDER BY attempt_id").fetchall()
            assert apply_migrations(conn) == []
            assert conn.execute("SELECT question_snapshot FROM attempt ORDER BY attempt_id").fetchall() == snapshots
            row = conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,status,result_release_policy,expires_at) VALUES (1,1,'completed','HUMAN_VERIFIED',NOW()+INTERVAL '1 hour') RETURNING release_status").fetchone()
            assert row == ("unsubmitted",)
        finally:
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')

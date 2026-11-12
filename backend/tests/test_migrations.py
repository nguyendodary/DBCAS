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
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='account' AND column_name IN ('password_set','password_changed_at')").fetchone()[0] == 2
            assert conn.execute("SELECT password_set FROM account WHERE email='preserved@migration.test'").fetchone()[0] is True
            assert conn.execute("SELECT password_changed_at FROM account WHERE email='preserved@migration.test'").fetchone()[0] is None
            assert conn.execute("SELECT to_regclass('password_reset_token')").fetchone()[0]
            assert conn.execute("SELECT to_regclass('password_reset_audit')").fetchone()[0]
            assert conn.execute("SELECT count(*) FROM pg_trigger WHERE tgrelid='password_reset_audit'::regclass AND tgname='password_reset_audit_immutable'").fetchone()[0] == 1
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


def test_019_archives_only_published_assessments_and_preserves_legacy_rows(tmp_path):
    """Upgrade a populated legacy schema through 018, then apply the exact 019."""
    directory = ROOT_DIR / 'db/migrations'
    prior = tmp_path / 'pre019'
    prior.mkdir()
    for path in directory.glob('[0-9][0-9][0-9]_*.sql'):
        if path.name < '019':
            (prior / path.name).write_bytes(path.read_bytes())
    url = get_settings().database_url.replace('postgresql+psycopg://', 'postgresql://')
    namespace = 'archive019_' + uuid.uuid4().hex[:12]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((Path(__file__).parent / 'fixtures/schema_20261011.sql').read_text(), prepare=False)
            assert len(apply_migrations(conn, prior)) == 18
            account = conn.execute("INSERT INTO account(email,password_hash) VALUES ('legacy@archive.test','not-a-login-hash') RETURNING account_id").fetchone()[0]
            question = conn.execute("INSERT INTO question(question_type,prompt,created_by) VALUES ('mcq','Historical prompt',%s) RETURNING question_id", (account,)).fetchone()[0]
            assessments = []
            for status in ('draft', 'published', 'closed', 'published'):
                assessments.append(conn.execute("INSERT INTO assessment(title,status,created_by) VALUES ('Legacy exam',%s,%s) RETURNING assessment_id", (status, account)).fetchone()[0])
            session = conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,status,expires_at,config_snapshot) VALUES (%s,%s,'completed',NOW()+INTERVAL '1 hour','{\"version\":2}') RETURNING session_id", (assessments[1], account)).fetchone()[0]
            conn.execute("INSERT INTO attempt(session_id,question_id,seq_no,score,question_snapshot) VALUES (%s,%s,1,1,'{\"version\":2,\"prompt\":\"Historical prompt\"}')", (session, question))
            tables = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname=current_schema() AND tablename<>'schema_migration' ORDER BY tablename").fetchall()

            def rows():
                snapshots = {}
                for (table,) in tables:
                    projection = "to_jsonb(t) - 'status'" if table == 'assessment' else 'to_jsonb(t)'
                    snapshots[table] = conn.execute(
                        f'SELECT {projection} FROM "{table}" t ORDER BY ({projection})::text'
                    ).fetchall()
                return snapshots

            before = rows()
            assert apply_migrations(conn) == [
                '019_archive_prebuilt_exams.sql',
                '020_provisional_ai_final_results.sql',
            ]
            expected = [('draft',), ('closed',), ('closed',), ('closed',)]
            assert conn.execute('SELECT status FROM assessment ORDER BY assessment_id').fetchall() == expected
            assert rows() == before  # every legacy row and snapshot, excluding intentional status changes
            assert apply_migrations(conn) == []
            conn.execute((directory / '019_archive_prebuilt_exams.sql').read_text(), prepare=False)
            assert conn.execute('SELECT status FROM assessment ORDER BY assessment_id').fetchall() == expected
            assert rows() == before
            assert conn.execute('SELECT count(*) FROM schema_migration').fetchone()[0] == 20
        finally:
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')


def test_original_language_upgrade_preserves_translations_and_snapshots():
    """Upgrade an exact pre-012 schema containing existing source and evidence."""
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    namespace = "original_locale_" + uuid.uuid4().hex[:12]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            pre012 = (ROOT_DIR / "db/schema.sql").read_text().split('-- Original-language question authoring (migration 012).')[0]
            conn.execute(pre012, prepare=False)
            conn.execute("INSERT INTO account(email,password_hash) VALUES ('language@migration.test','not-a-login-hash')")
            conn.execute("INSERT INTO question(question_type,prompt,created_by,points) VALUES ('mcq','Original English',1,1)")
            conn.execute("INSERT INTO question_translation(question_id,locale,source_hash,prompt) VALUES (1,'vi','preserve-this-hash','Nội dung đã duyệt')")
            conn.execute("INSERT INTO assessment(title,created_by) VALUES ('Historical',1)")
            conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,expires_at,config_snapshot) VALUES (1,1,NOW()+INTERVAL '1 hour','{\"version\":2}')")
            conn.execute("INSERT INTO attempt(session_id,question_id,seq_no,question_snapshot) VALUES (1,1,1,'{\"version\":2,\"prompt\":\"Original English\",\"points\":\"1\"}')")
            conn.execute("INSERT INTO mcq_option(question_id,option_label,option_text,is_correct) VALUES (1,'A','WHERE',true),(1,'B','ORDER BY',false)")
            conn.execute("INSERT INTO question(question_type,prompt,reference_answer,created_by,points) VALUES ('sql','Query students','SELECT id FROM students',1,1),('essay','Explain normalization',NULL,1,1)")
            conn.execute("INSERT INTO sql_test_dataset(question_id,dataset_name,setup_sql,expected_result) VALUES (2,'base','CREATE TABLE students(id int); INSERT INTO students VALUES (1)','{\"rows\":[[1]]}')")
            conn.execute("INSERT INTO rubric(question_id,level_name,min_score,max_score,criteria) VALUES (3,'Complete',1,1,'Explain functional dependencies')")
            conn.execute("UPDATE attempt SET score=1,grading_detail='{\"feedback\":\"Official historical feedback\"}' WHERE attempt_id=1")
            conn.execute("INSERT INTO grade_review(attempt_id,reviewer_id,automated_score,automated_detail,approved_score,comments) VALUES (1,1,1,'{\"evidence\":\"captured\"}',1,'Reviewed historical grade')")
            protected = ('question_translation', 'mcq_option', 'sql_test_dataset', 'rubric', 'attempt', 'grade_review', 'assessment_session')
            # Migration 013 adds a nullable assessment_session.blueprint_id column;
            # the additive key is excluded so fingerprints assert row data only.
            def fingerprints():
                return {table: conn.execute(
                    f"SELECT to_jsonb(t) {'- \'blueprint_id\'' if table == 'assessment_session' else ''} "
                    f"FROM {table} t ORDER BY to_jsonb(t)::text"
                ).fetchall() for table in protected}
            preserved = fingerprints()
            before = conn.execute('SELECT question_snapshot FROM attempt').fetchone()[0]
            translated = conn.execute('SELECT source_hash,prompt,updated_at FROM question_translation').fetchone()
            apply_migrations(conn)
            assert conn.execute('SELECT original_locale,prompt FROM question ORDER BY question_id').fetchall() == [('en', 'Original English'), ('en', 'Query students'), ('en', 'Explain normalization')]
            assert fingerprints() == preserved
            assert conn.execute("SELECT count(*) FROM schema_migration WHERE version='012_question_original_locale.sql'").fetchone()[0] == 1
            assert conn.execute('SELECT source_hash,prompt,updated_at FROM question_translation').fetchone() == translated
            assert conn.execute('SELECT question_snapshot FROM attempt').fetchone()[0] == before
            assert apply_migrations(conn) == []
            # Direct SQL rerun is safe too, and English translations can now be stored.
            conn.execute((ROOT_DIR / 'db/migrations/012_question_original_locale.sql').read_text(), prepare=False)
            conn.execute("INSERT INTO question(question_type,prompt,original_locale,created_by,points) VALUES ('mcq','Bản gốc','vi',1,1)")
            conn.execute("INSERT INTO question_translation(question_id,locale,source_hash,prompt) VALUES (4,'en','new-hash','English translation')")
            assert conn.execute('SELECT question_snapshot FROM attempt').fetchone()[0] == before
        finally:
            conn.execute('SET search_path TO public')
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')


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

def test_020_backfills_legacy_published_practice_once(tmp_path):
    """Existing published practice results get one legacy snapshot, repeatably."""
    directory = ROOT_DIR / "db/migrations"
    prior = tmp_path / "pre020"
    prior.mkdir()
    for path in directory.glob("[0-9][0-9][0-9]_*.sql"):
        if path.name < "020":
            (prior / path.name).write_bytes(path.read_bytes())
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    namespace = "legacy020_" + uuid.uuid4().hex[:12]
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((ROOT_DIR / "db/schema.sql").read_text(), prepare=False)
            assert len(apply_migrations(conn, prior)) == 19
            account_id = conn.execute(
                "INSERT INTO account(email,password_hash) VALUES ('legacy-practice@migration.test','not-a-login-hash') RETURNING account_id"
            ).fetchone()[0]
            question_id = conn.execute(
                "INSERT INTO question(question_type,prompt,created_by,points) VALUES ('mcq','Legacy practice item',%s,2) RETURNING question_id",
                (account_id,),
            ).fetchone()[0]
            session_id = conn.execute(
                """INSERT INTO assessment_session(
                     assessment_id,learner_id,status,expires_at,release_status,
                     result_release_policy,review_revision,published_at,config_snapshot)
                   VALUES (NULL,%s,'completed',NOW(),'published','HUMAN_VERIFIED',3,NOW(),
                     '{"uncovered_concepts":[{"concept_id":9,"concept_name":"IDX"}]}'::jsonb)
                   RETURNING session_id""",
                (account_id,),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO attempt(session_id,question_id,seq_no,score,submitted_at,grading_status) VALUES (%s,%s,1,1.5,NOW(),'graded')",
                (session_id, question_id),
            )
            conn.execute(
                """INSERT INTO evaluation_record(learner_id,session_id,scope_key,input_hash,status,payload)
                   VALUES (%s,%s,%s,%s,'ready',
                     '{"evaluation":{"summary":"Legacy AI summary","strengths":["a"],"weaknesses":["b"],"suggestions":["c"],"learning_path":["d"],"question_comments":[],"trend":null},"prompt_hash":"h","builder_fallback":false,"evaluator_fallback":false}'::jsonb)""",
                (account_id, session_id, f"attempt:{session_id}", "a" * 64),
            )
            conn.execute(
                "INSERT INTO result_release_event(session_id,previous_status,new_status,reviewer_id) VALUES (%s,'pending_review','published',%s)",
                (session_id, account_id),
            )
            assert apply_migrations(conn) == ["020_provisional_ai_final_results.sql"]
            row = conn.execute(
                "SELECT source,reviewer_id,ai_evaluation->'evaluation'->>'summary',final_evaluation->>'summary',jsonb_array_length(scores),overall->>'percentage',jsonb_array_length(uncovered_concepts) FROM session_final_result"
            ).fetchone()
            assert row == ("legacy", account_id, "Legacy AI summary", "Legacy AI summary", 1, "75.00", 1)
            assert conn.execute("SELECT release_status,review_revision FROM assessment_session").fetchone() == ("published", 3)
            # Direct rerun of the additive migration must not duplicate the snapshot.
            conn.execute((directory / "020_provisional_ai_final_results.sql").read_text(), prepare=False)
            assert conn.execute("SELECT count(*) FROM session_final_result").fetchone()[0] == 1
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')

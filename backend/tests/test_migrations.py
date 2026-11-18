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
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='attempt' AND column_name IN ('is_flagged','flag_revision','first_opened_at')").fetchone()[0] == 3
            assert conn.execute("SELECT count(*) FROM pg_constraint WHERE conrelid='attempt'::regclass AND conname='attempt_flag_revision_check'").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='assessment_session' AND column_name IN ('tab_leave_count','cancelled_at','cancel_reason')").fetchone()[0] == 3
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='assessment_session' AND column_name IN ('purpose','purpose_source')").fetchone()[0] == 2
            assert conn.execute("SELECT to_regclass('tab_leave_interval')").fetchone()[0]
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='assessment_session' AND column_name='locale'").fetchone()[0] == 1
            assert conn.execute("SELECT can_manage_roles FROM account WHERE email='preserved@migration.test'").fetchone()[0] is False
            assert conn.execute("SELECT to_regclass('account_role_audit')").fetchone()[0]
            assert conn.execute("SELECT count(*) FROM pg_trigger WHERE tgrelid='account_role_audit'::regclass AND tgname='account_role_audit_immutable'").fetchone()[0] == 1
            assert conn.execute("SELECT to_regclass('question_translation')").fetchone()[0]
            assert conn.execute("SELECT to_regclass('question_clo')").fetchone()[0]
            for table in ("course_document", "document_chunk", "document_clo", "question_evidence"):
                assert conn.execute(f"SELECT to_regclass('{table}')").fetchone()[0]
            assert conn.execute("SELECT count(*) FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='document_chunk' AND column_name IN ('ordinal','page_from','page_to','heading','text','text_hash','char_count')").fetchone()[0] == 7
            assert conn.execute("SELECT count(*) FROM pg_constraint WHERE conrelid='question_evidence'::regclass AND contype='f'").fetchone()[0] == 2
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


CATALOG_SQL = {
    "tables": """select c.relname from pg_class c
     join pg_namespace n on n.oid=c.relnamespace
     where n.nspname=current_schema() and c.relkind='r' and c.relpersistence='p'
       and c.relname<>'schema_migration'
     order by c.relname collate "C" """,
    "columns": """select table_name, column_name, data_type, udt_name, is_nullable,
     column_default, is_identity, character_maximum_length, numeric_precision, numeric_scale
     from information_schema.columns
     where table_schema=current_schema() and table_name<>'schema_migration'
     order by table_name, column_name""",
    "constraints": """select c.relname, con.conname, con.contype, pg_get_constraintdef(con.oid)
     from pg_constraint con join pg_class c on c.oid=con.conrelid
     join pg_namespace n on n.oid=c.relnamespace
     where n.nspname=current_schema() and c.relname<>'schema_migration'
     order by c.relname, con.conname collate "C" """,
    "indexes": """select tablename, indexname,
     regexp_replace(indexdef, current_schema(), 'SCHEMA', 'g')
     from pg_indexes
     where schemaname=current_schema() and tablename<>'schema_migration'
     order by tablename collate "C", indexname collate "C" """,
    "triggers": """select c.relname, t.tgname,
     regexp_replace(pg_get_triggerdef(t.oid), current_schema(), 'SCHEMA', 'g')
     from pg_trigger t join pg_class c on c.oid=t.tgrelid
     join pg_namespace n on n.oid=c.relnamespace
     where n.nspname=current_schema() and not t.tgisinternal and c.relname<>'schema_migration'
     order by c.relname collate "C", t.tgname collate "C" """,
}


def catalog_shape(conn):
    return {kind: tuple(tuple(row) for row in conn.execute(sql).fetchall())
            for kind, sql in CATALOG_SQL.items()}


def _load_catalog(conn, namespace, sql, migrate):
    conn.execute(f'DROP SCHEMA IF EXISTS "{namespace}" CASCADE')
    conn.execute(f'CREATE SCHEMA "{namespace}"')
    conn.execute(f'SET search_path TO "{namespace}"')
    try:
        conn.execute(sql, prepare=False)
        if migrate:
            apply_migrations(conn)
        return catalog_shape(conn)
    finally:
        conn.execute("SET search_path TO public")
        conn.execute(f'DROP SCHEMA IF EXISTS "{namespace}" CASCADE')


def test_schema_sql_matches_entire_migration_chain_catalog():
    """db/schema.sql must already contain every migration's DDL.

    Applying the whole real chain to a fresh load of db/schema.sql must be a
    catalog no-op: table, column, constraint, index and trigger sets identical.
    """
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    sql = (ROOT_DIR / "db/schema.sql").read_text()
    token = uuid.uuid4().hex[:10]
    with psycopg.connect(url, autocommit=True) as conn:
        embedded = _load_catalog(conn, f"schema_sql_{token}", sql, migrate=False)
        chain = _load_catalog(conn, f"schema_chain_{token}", sql, migrate=True)
    for kind in CATALOG_SQL:
        assert embedded[kind] == chain[kind], f"schema.sql vs full migration chain differ in {kind}"


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
                    if table == 'assessment':
                        projection = "to_jsonb(t) - 'status'"
                    elif table == 'attempt':
                        projection = ("to_jsonb(t) - 'is_flagged' - 'flag_revision' "
                                      "- 'first_opened_at'")
                    elif table == 'assessment_session':
                        projection = ("to_jsonb(t) - 'tab_leave_count' - 'cancelled_at' "
                                      "- 'cancel_reason' - 'purpose' - 'purpose_source' "
                                      "- 'review_policy' - 'current_result_version_id'")
                    else:
                        projection = "to_jsonb(t)"
                    snapshots[table] = conn.execute(
                        f'SELECT {projection} FROM "{table}" t ORDER BY ({projection})::text'
                    ).fetchall()
                return snapshots

            before = rows()
            assert apply_migrations(conn) == [
                '019_archive_prebuilt_exams.sql',
                '020_provisional_ai_final_results.sql',
                '021_fixed_paper_attempt_state.sql',
                '022_question_clo_tagging.sql',
                '023_document_grounding.sql',
                '024_tab_leave_guard.sql',
                '025_session_purpose.sql',
                '026_pr3a_database_foundation.sql',
            ]
            expected = [('draft',), ('closed',), ('closed',), ('closed',)]
            assert conn.execute('SELECT status FROM assessment ORDER BY assessment_id').fetchall() == expected
            assert rows() == before  # every legacy row and snapshot, excluding intentional status changes
            assert apply_migrations(conn) == []
            conn.execute((directory / '019_archive_prebuilt_exams.sql').read_text(), prepare=False)
            assert conn.execute('SELECT status FROM assessment ORDER BY assessment_id').fetchall() == expected
            assert rows() == before
            assert conn.execute('SELECT count(*) FROM schema_migration').fetchone()[0] == 26
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
                    f"SELECT to_jsonb(t) {'- \'blueprint_id\' - \'tab_leave_count\' - \'cancelled_at\' - \'cancel_reason\' - \'purpose\' - \'purpose_source\' - \'review_policy\' - \'current_result_version_id\'' if table == 'assessment_session' else ''} "
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

def test_022_backfills_single_clo_once_and_preserves_existing_rows():
    """Create the table from pre-022, backfill once, then rerun safely."""
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    namespace = "clo022_" + uuid.uuid4().hex[:12]
    migration = (ROOT_DIR / "db/migrations/022_question_clo_tagging.sql").read_text()
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((ROOT_DIR / "db/schema.sql").read_text(), prepare=False)
            # Emulate a database upgraded from 021: the fresh schema already
            # contains the table, so remove it before exercising the migration.
            conn.execute("DROP TABLE question_clo")
            conn.execute(migration, prepare=False)

            account_id = conn.execute(
                "INSERT INTO account(email,password_hash) "
                "VALUES ('clo022@migration.test','not-a-login-hash') RETURNING account_id"
            ).fetchone()[0]
            clo1 = conn.execute(
                "INSERT INTO course_learning_outcome(clo_code,title,created_by) "
                "VALUES ('CLO-22-A','Querying',%s) RETURNING clo_id",
                (account_id,),
            ).fetchone()[0]
            clo2 = conn.execute(
                "INSERT INTO course_learning_outcome(clo_code,title,created_by) "
                "VALUES ('CLO-22-B','Design',%s) RETURNING clo_id",
                (account_id,),
            ).fetchone()[0]
            concept1 = conn.execute(
                "INSERT INTO concept(concept_code,concept_name,subject_area) "
                "VALUES ('C22-A','Single concept','SQL') RETURNING concept_id"
            ).fetchone()[0]
            concept2 = conn.execute(
                "INSERT INTO concept(concept_code,concept_name,subject_area) "
                "VALUES ('C22-B','Ambiguous concept','SQL') RETURNING concept_id"
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO clo_concept(clo_id,concept_id,mapping_source,status) VALUES "
                "(%s,%s,'admin','confirmed'),(%s,%s,'admin','confirmed'),"
                "(%s,%s,'admin','confirmed')",
                (clo1, concept1, clo1, concept2, clo2, concept2),
            )
            questions = []
            for prompt in ("single", "ambiguous", "admin", "unmapped"):
                questions.append(
                    conn.execute(
                        "INSERT INTO question(question_type,prompt,created_by) "
                        "VALUES ('mcq',%s,%s) RETURNING question_id",
                        (prompt, account_id),
                    ).fetchone()[0]
                )
            conn.execute(
                "INSERT INTO question_concept(question_id,concept_id,confirmed,review_status) VALUES "
                "(%s,%s,TRUE,'confirmed'),(%s,%s,TRUE,'confirmed'),(%s,%s,TRUE,'confirmed')",
                (
                    questions[0], concept1,
                    questions[1], concept2,
                    questions[2], concept1,
                ),
            )
            conn.execute(
                "INSERT INTO question_clo(question_id,clo_id,is_primary,status,tag_source,confirmed_at) "
                "VALUES (%s,%s,TRUE,'confirmed','admin',NOW())",
                (questions[2], clo2),
            )

            conn.execute(migration, prepare=False)
            conn.execute(migration, prepare=False)

            rows = conn.execute(
                "SELECT question_id,clo_id,is_primary,status,tag_source,confirmed_at IS NOT NULL "
                "FROM question_clo ORDER BY question_id"
            ).fetchall()
            assert rows == [
                (questions[0], clo1, True, "confirmed", "auto", True),
                (questions[2], clo2, True, "confirmed", "admin", True),
            ]
            assert conn.execute(
                "SELECT count(*) FROM question_clo WHERE question_id IN (%s,%s)",
                (questions[1], questions[3]),
            ).fetchone()[0] == 0
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
            assert apply_migrations(conn) == [
                "020_provisional_ai_final_results.sql",
                "021_fixed_paper_attempt_state.sql",
                "022_question_clo_tagging.sql",
                "023_document_grounding.sql",
                "024_tab_leave_guard.sql",
                "025_session_purpose.sql",
                "026_pr3a_database_foundation.sql",
            ]
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


def test_023_document_tables_are_additive_and_repeatable(tmp_path):
    """Upgrade a populated pre-023 schema, then rerun the exact migration."""
    directory = ROOT_DIR / "db/migrations"
    prior = tmp_path / "pre023"
    prior.mkdir()
    for path in directory.glob("[0-9][0-9][0-9]_*.sql"):
        if path.name < "023":
            (prior / path.name).write_bytes(path.read_bytes())
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    namespace = "document023_" + uuid.uuid4().hex[:12]
    migration = (directory / "023_document_grounding.sql").read_text()
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((Path(__file__).parent / "fixtures/schema_20261011.sql").read_text(), prepare=False)
            assert len(apply_migrations(conn, prior)) == 22
            account_id = conn.execute(
                "INSERT INTO account(email,password_hash) VALUES ('doc023@migration.test','not-a-login-hash') "
                "RETURNING account_id"
            ).fetchone()[0]
            clo_id = conn.execute(
                "INSERT INTO course_learning_outcome(clo_code,title,created_by) "
                "VALUES ('CLO-23','Document grounding',%s) RETURNING clo_id",
                (account_id,),
            ).fetchone()[0]
            question_id = conn.execute(
                "INSERT INTO question(question_type,prompt,created_by) "
                "VALUES ('mcq','Preserved before documents',%s) RETURNING question_id",
                (account_id,),
            ).fetchone()[0]
            before = conn.execute(
                "SELECT to_jsonb(t) FROM question t WHERE question_id=%s", (question_id,)
            ).fetchone()[0]

            assert apply_migrations(conn) == [
                "023_document_grounding.sql", "024_tab_leave_guard.sql",
                "025_session_purpose.sql", "026_pr3a_database_foundation.sql"]
            assert apply_migrations(conn) == []
            for table in ("course_document", "document_chunk", "document_clo", "question_evidence"):
                assert conn.execute(f"SELECT to_regclass('{table}')").fetchone()[0]
                assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0
            assert conn.execute(
                "SELECT to_jsonb(t) FROM question t WHERE question_id=%s", (question_id,)
            ).fetchone()[0] == before
            assert conn.execute(
                "SELECT count(*) FROM pg_constraint WHERE conrelid='course_document'::regclass AND contype IN ('c','f')"
            ).fetchone()[0] == 6
            assert conn.execute(
                "SELECT count(*) FROM pg_indexes WHERE schemaname=current_schema() "
                "AND indexname IN ('course_document_status_idx','document_chunk_document_idx',"
                "'document_clo_clo_idx','question_evidence_question_idx','question_evidence_chunk_idx')"
            ).fetchone()[0] == 5

            document_id = conn.execute(
                "INSERT INTO course_document(title,mime_type,original_filename,sha256,char_count,page_count,"
                "uploaded_by,status,approved_by,approved_at) VALUES ('Week 1','text/plain','week1.txt',%s,5,1,%s,"
                "'approved',%s,NOW()) RETURNING document_id",
                ("a" * 64, account_id, account_id),
            ).fetchone()[0]
            chunk_id = conn.execute(
                "INSERT INTO document_chunk(document_id,ordinal,page_from,page_to,heading,text,text_hash,char_count) "
                "VALUES (%s,1,1,1,'Heading','hello',%s,5) RETURNING chunk_id",
                (document_id, "b" * 64),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO document_clo(document_id,clo_id,status,approved_by,approved_at) "
                "VALUES (%s,%s,'approved',%s,NOW())",
                (document_id, clo_id, account_id),
            )
            conn.execute(
                "INSERT INTO question_evidence(question_id,chunk_id,quote,start_offset,end_offset,source_hash) "
                "VALUES (%s,%s,'hello',0,5,%s)",
                (question_id, chunk_id, "c" * 64),
            )
            # Direct rerun is also safe and never duplicates or rewrites data.
            conn.execute(migration, prepare=False)
            assert conn.execute("SELECT count(*) FROM course_document").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM document_chunk").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM document_clo").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM question_evidence").fetchone()[0] == 1
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')


def test_025_backfills_historical_purpose_once_and_marks_new_rows_server(tmp_path):
    """Classify pre-025 sessions deterministically; never rewrite after upgrade."""
    directory = ROOT_DIR / "db/migrations"
    prior = tmp_path / "pre025"
    prior.mkdir()
    for path in directory.glob("[0-9][0-9][0-9]_*.sql"):
        if path.name < "025":
            (prior / path.name).write_bytes(path.read_bytes())
    url = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    namespace = "purpose025_" + uuid.uuid4().hex[:12]
    migration = (directory / "025_session_purpose.sql").read_text()
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f'CREATE SCHEMA "{namespace}"')
        try:
            conn.execute(f'SET search_path TO "{namespace}"')
            conn.execute((ROOT_DIR / "db/schema.sql").read_text(), prepare=False)
            # Emulate a real pre-025 volume: the fresh schema already carries
            # the additive columns and index that migration 025 introduces.
            conn.execute("DROP INDEX assessment_session_purpose_idx")
            conn.execute("ALTER TABLE assessment_session DROP COLUMN purpose, DROP COLUMN purpose_source")
            assert len(apply_migrations(conn, prior)) == 24
            account_id = conn.execute(
                "INSERT INTO account(email,password_hash) VALUES ('purpose025@migration.test','not-a-login-hash') "
                "RETURNING account_id"
            ).fetchone()[0]
            assessment_id = conn.execute(
                "INSERT INTO assessment(title,status,created_by) VALUES ('Historical', 'published', %s) "
                "RETURNING assessment_id", (account_id,)
            ).fetchone()[0]
            cases = {
                "formal_without_mode": (assessment_id, '{"version":1}'),
                "formal_practice": (assessment_id, '{"assembly_mode":"PRACTICE"}'),
                "fixed_practice": (None, '{"learner_defined":true,"assembly_mode":"PRACTICE",'
                                         '"assessment_style":"FIXED","runner_mode":"fixed"}'),
                "adaptive_practice": (None, '{"assessment_style":"ADAPTIVE","runner_mode":"adaptive",'
                                            '"result_kind":"estimated_ability"}'),
                "free_choice": (None, '{"learner_defined":true,"assembly_mode":"PRACTICE","source":"ai"}'),
                "legacy_runner_only": (None, '{"runner_mode":"fixed"}'),
            }
            ids = {}
            for key, (aid, snapshot) in cases.items():
                ids[key] = conn.execute(
                    "INSERT INTO assessment_session(assessment_id,learner_id,status,expires_at,config_snapshot) "
                    "VALUES (%s,%s,'completed',NOW()+INTERVAL '1 hour',%s::jsonb) RETURNING session_id",
                    (aid, account_id, snapshot),
                ).fetchone()[0]
            assert apply_migrations(conn) == [
                "025_session_purpose.sql", "026_pr3a_database_foundation.sql"
            ]
            rows = conn.execute(
                "SELECT session_id,purpose,purpose_source FROM assessment_session ORDER BY session_id"
            ).fetchall()
            by_id = {sid: (purpose, source) for sid, purpose, source in rows}
            assert by_id == {
                ids["formal_without_mode"]: ("TEST", "BACKFILL"),
                ids["formal_practice"]: ("PRACTICE", "BACKFILL"),
                ids["fixed_practice"]: ("TEST", "BACKFILL"),
                ids["adaptive_practice"]: ("TEST", "BACKFILL"),
                ids["free_choice"]: ("PRACTICE", "BACKFILL"),
                ids["legacy_runner_only"]: ("TEST", "BACKFILL"),
            }
            new_session = conn.execute(
                "INSERT INTO assessment_session(assessment_id,learner_id,expires_at) "
                "VALUES (%s,%s,NOW()+INTERVAL '1 hour') RETURNING session_id,purpose,purpose_source",
                (assessment_id, account_id),
            ).fetchone()
            assert new_session[1:] == ("PRACTICE", "SERVER")
            with pytest.raises(psycopg.errors.CheckViolation):
                conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,expires_at,purpose) "
                             "VALUES (%s,%s,NOW()+INTERVAL '1 hour','OTHER')",
                             (assessment_id, account_id))
            with pytest.raises(psycopg.errors.CheckViolation):
                conn.execute("INSERT INTO assessment_session(assessment_id,learner_id,expires_at,purpose_source) "
                             "VALUES (%s,%s,NOW()+INTERVAL '1 hour','OTHER')",
                             (assessment_id, account_id))
            # A direct rerun after a later correction must not reclassify rows.
            conn.execute("UPDATE assessment_session SET purpose='PRACTICE' WHERE session_id=%s",
                         (ids["formal_without_mode"],))
            conn.execute(migration, prepare=False)
            assert conn.execute("SELECT purpose,purpose_source FROM assessment_session WHERE session_id=%s",
                                (ids["formal_without_mode"],)).fetchone() == ("PRACTICE", "BACKFILL")
        finally:
            conn.execute("SET search_path TO public")
            conn.execute(f'DROP SCHEMA "{namespace}" CASCADE')

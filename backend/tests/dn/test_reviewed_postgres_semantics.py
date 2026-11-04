"""Counterexamples behind the editorial fixes, on actual PostgreSQL 17."""
from uuid import uuid4

import psycopg
import pytest
from sqlalchemy import text

from app.config import get_settings
from test_question_validator import question


def correct(key):
    return next(o["option_text"] for o in question(key)["options"] if o["is_correct"])


@pytest.fixture
def namespace():
    dsn = get_settings().database_url.replace("postgresql+psycopg://", "postgresql://")
    name = "semantic_" + uuid4().hex[:12]
    with psycopg.connect(dsn, autocommit=True) as conn:
        assert conn.info.dbname == "dbcas_test"
        conn.execute(f'CREATE SCHEMA "{name}"')
        try:
            yield dsn, name
        finally:
            conn.execute(f'DROP SCHEMA "{name}" CASCADE')


def test_no_key_update_blocks_nonkey_writers_but_allows_key_share(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as setup:
        setup.execute(f'CREATE TABLE "{name}".t(id int PRIMARY KEY, value int)')
        setup.execute(f'INSERT INTO "{name}".t VALUES(1,10)')
    with psycopg.connect(dsn) as first, psycopg.connect(dsn) as second:
        first.execute(f'SELECT * FROM "{name}".t FOR NO KEY UPDATE')
        second.execute("SET LOCAL lock_timeout = '150ms'")
        assert second.execute(f'SELECT id FROM "{name}".t FOR KEY SHARE').fetchone() == (1,)
        second.rollback()
        for statement in (f'SELECT * FROM "{name}".t FOR UPDATE', f'SELECT * FROM "{name}".t FOR SHARE',
                          f'UPDATE "{name}".t SET value=value+1 WHERE id=1'):
            second.execute("SET LOCAL lock_timeout = '150ms'")
            with pytest.raises(psycopg.errors.LockNotAvailable):
                second.execute(statement)
            second.rollback()
        first.rollback()
        assert second.execute(f'UPDATE "{name}".t SET value=value+1 WHERE id=1 RETURNING value').fetchone() == (11,)
    assert correct("pg-m183") == "SELECT ... FOR KEY SHARE"


def test_explicit_array_bounds_and_order_match_the_reviewed_answers(db_session):
    actual = db_session.execute(text("SELECT ('[0:2]={10,20,30}'::integer[])[1]")).scalar_one()
    assert correct("pg-m091") == str(actual) == "20"
    assert db_session.execute(text("SELECT ARRAY[3,1,3]")).scalar_one() == [3, 1, 3]
    assert "preserve element order" in question("pg-e040")["reference_answer"]


def test_numeric_div_and_integer_division_have_distinct_types(db_session):
    values = db_session.execute(text("SELECT div(9,2), pg_typeof(div(9,2))::text, 9/2, pg_typeof(9/2)::text")).one()
    assert tuple(map(str, values)) == ("4", "numeric", "4", "integer")
    assert "numeric 4" in correct("pg-m116") and "integer 4" in correct("pg-m116")


def test_union_with_growing_depth_does_not_remove_revisited_nodes(db_session):
    growing = db_session.execute(text("WITH RECURSIVE walk(id,depth) AS (SELECT 1,0 UNION SELECT id,depth+1 FROM walk WHERE depth<3) SELECT count(*) FROM walk")).scalar_one()
    nodes = db_session.execute(text("WITH RECURSIVE walk(id) AS (SELECT 1 UNION SELECT id FROM walk) SELECT count(*) FROM walk")).scalar_one()
    assert growing == 4 and nodes == 1
    assert correct("pg-m060").startswith("No:")


def test_distinct_on_can_sort_by_an_unselected_expression(db_session):
    rows = db_session.execute(text("SELECT DISTINCT ON (dept) dept FROM (VALUES(1,10),(1,20),(2,5)) AS e(dept,salary) ORDER BY dept,salary DESC")).all()
    assert rows == [(1,), (2,)]
    assert "DISTINCT ON can still" in correct("pg-m272")


def test_rows_and_range_current_row_differ_for_peers(db_session):
    rows = db_session.execute(text("SELECT k, v, sum(v) OVER(ORDER BY k ROWS UNBOUNDED PRECEDING), sum(v) OVER(ORDER BY k RANGE UNBOUNDED PRECEDING) FROM(VALUES(1,10),(1,20),(2,30)) AS t(k,v) ORDER BY k,v")).all()
    assert [r[3] for r in rows] == [30, 30, 60]
    assert sorted(r[2] for r in rows[:2]) in ([10, 30], [20, 30])
    assert "every peer" in correct("pg-m281")


def test_configured_english_dictionary_stems_variants(db_session):
    matched = db_session.execute(text("SELECT to_tsvector('english','rated rate') @@ to_tsquery('english','rates')")).scalar_one()
    assert matched is True
    assert "English Snowball" in question("pg-m128")["prompt"]


def test_domain_operator_returns_base_type_and_cast_back_rechecks(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(f'CREATE DOMAIN "{name}".posint AS integer CHECK(VALUE>0)')
        row = conn.execute(f'SELECT (1::"{name}".posint)-1, pg_typeof((1::"{name}".posint)-1)::text').fetchone()
        assert row == (0, "integer")
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(f'SELECT ((1::"{name}".posint)-1)::"{name}".posint')
    assert correct("pg-m106").startswith("0 of type integer")


def test_dynamic_execute_preserves_found_but_reports_row_count(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(f'''CREATE FUNCTION "{name}".probe() RETURNS TABLE(found_after boolean, processed bigint)
            LANGUAGE plpgsql AS $$ BEGIN
            PERFORM 1 WHERE false;
            EXECUTE 'SELECT 1';
            GET DIAGNOSTICS processed = ROW_COUNT;
            found_after := FOUND;
            RETURN NEXT; END $$''')
        assert conn.execute(f'SELECT * FROM "{name}".probe()').fetchone() == (False, 1)
    assert correct("pg-m220").startswith("No;")
    assert "EXECUTE does not change" in question("pg-e024")["reference_answer"]


def test_like_including_all_omits_foreign_keys(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(f'CREATE TABLE "{name}".parent(id int PRIMARY KEY)')
        conn.execute(f'CREATE TABLE "{name}".original(id int PRIMARY KEY, parent_id int REFERENCES "{name}".parent(id), n int CHECK(n>0))')
        conn.execute(f'CREATE TABLE "{name}".copy(LIKE "{name}".original INCLUDING ALL)')
        rows = conn.execute("SELECT contype,count(*) FROM pg_constraint WHERE conrelid=%s::regclass GROUP BY contype", (f'"{name}".copy',)).fetchall()
        types = dict(rows)
        assert types.get("p") == 1 and types.get("c") == 1 and "f" not in types
    assert "foreign keys are not copied" in correct("pg-m304")


def test_not_valid_checks_new_rows_but_does_not_certify_old_rows(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(f'CREATE TABLE "{name}".t(n int)')
        conn.execute(f'INSERT INTO "{name}".t VALUES(-1)')
        conn.execute(f'ALTER TABLE "{name}".t ADD CONSTRAINT positive CHECK(n>0) NOT VALID')
        assert conn.execute("SELECT convalidated FROM pg_constraint WHERE conrelid=%s::regclass", (f'"{name}".t',)).fetchone() == (False,)
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(f'INSERT INTO "{name}".t VALUES(-2)')
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(f'ALTER TABLE "{name}".t VALIDATE CONSTRAINT positive')
        assert conn.execute(f'SELECT n FROM "{name}".t').fetchall() == [(-1,)]
    assert "remain unverified" in correct("pg-m306")


def test_drop_table_can_be_rolled_back(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as setup:
        setup.execute(f'CREATE TABLE "{name}".t(n int)')
        setup.execute(f'INSERT INTO "{name}".t VALUES(7)')
    with psycopg.connect(dsn) as conn:
        conn.execute(f'DROP TABLE "{name}".t')
        conn.rollback()
        assert conn.execute(f'SELECT n FROM "{name}".t').fetchone() == (7,)
    assert "rolling that transaction back" in correct("pg-m130")


def test_jsonb_can_enforce_a_check_constraint(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(f'CREATE TABLE "{name}".t(doc jsonb CHECK((doc->>\'score\')::int>0))')
        conn.execute(f'INSERT INTO "{name}".t VALUES(\'{{"score":1}}\')')
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(f'INSERT INTO "{name}".t VALUES(\'{{"score":-1}}\')')
    assert "CHECK constraints" in question("pg-e005")["reference_answer"]


def test_now_is_stable_and_not_permitted_in_stored_generated_columns(namespace):
    dsn, name = namespace
    with psycopg.connect(dsn, autocommit=True) as conn:
        assert conn.execute("SELECT provolatile FROM pg_proc WHERE oid='now()'::regprocedure").fetchone() == ("s",)
        with pytest.raises(psycopg.errors.InvalidObjectDefinition):
            conn.execute(f'CREATE TABLE "{name}".t(id int, created timestamptz GENERATED ALWAYS AS(now()) STORED)')
    assert "now() is STABLE" in correct("pg-m137")

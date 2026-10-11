"""Real PostgreSQL wire semantics and bounded sandbox regressions."""
import json
import tracemalloc
from decimal import Decimal

import pytest

from app.config import get_settings
from app.services.dataset_setup import validated_setup_statements
from app.services.sandbox_runner import SandboxError, SandboxRunner
from app.services.sql_features import detect_features
from app.services.sql_result import compare, parse_expected


@pytest.mark.parametrize("expression,expected", [
    ("1::integer",1.00),("1::bigint",1),("1.00::numeric",1.0),
    ("1.00::decimal",1),("1.0::real",1),("1.0::double precision",1),
    ("TRUE::boolean",True),("NULL::integer",None),("'1'::text","1"),
    ("12345678901234567890.12::numeric",Decimal("12345678901234567890.12")),
])
def test_real_postgresql_values_survive_wire_comparison(sandbox_runner, expression, expected):
    result = sandbox_runner.execute("SELECT " + expression + " AS value")
    assert result.success, result.error_message
    # HTTP-safe representation plus PostgreSQL type metadata retains meaning.
    wire = json.loads(json.dumps({"columns":result.columns,"rows":result.rows,"types":result.column_types}))
    target = parse_expected({"columns":["value"],"rows":[[expected]]})
    assert compare(wire["columns"], wire["rows"], target, wire["types"]).status == "passed"


@pytest.mark.parametrize("expression,expected", [("TRUE",1),("FALSE",0),("1",True),("0",False),("'1'::text",1)])
def test_real_boolean_and_text_never_equal_numbers(sandbox_runner, expression, expected):
    result=sandbox_runner.execute("SELECT "+expression+" AS value")
    assert result.success
    assert compare(result.columns,result.rows,parse_expected({"rows":[[expected]]}),result.column_types).status == "failed"


@pytest.mark.parametrize("value", ["abc"," abc","abc ","abc  "])
def test_text_whitespace_is_significant(sandbox_runner,value):
    result=sandbox_runner.execute("SELECT '"+value+"'::text AS value")
    assert result.success
    assert compare(result.columns,result.rows,parse_expected({"rows":[[value]]}),result.column_types).status == "passed"
    if value != "abc":
        assert compare(result.columns,result.rows,parse_expected({"rows":[["abc"]]}),result.column_types).status == "failed"


@pytest.mark.parametrize("sql", [
    "SELECT query_to_xml('SELECT * FROM pg_catalog.pg_class',true,false,'')",
    "SELECT query_to_xmlschema('SELECT * FROM information_schema.tables',true,false,'')",
    "SELECT query_to_xml_and_xmlschema('SELECT 1',true,false,'')",
    "SELECT schema_to_xml('pg_catalog',true,false,'')",
    "SELECT table_to_xml('pg_catalog.pg_class',true,false,'')",
    "SELECT * FROM ts_stat('SELECT secret FROM other_schema.t')",
    "SELECT * FROM information_schema.tables", "SELECT * FROM pg_catalog.pg_class",
])
def test_dynamic_catalog_surfaces_are_rejected(sandbox_runner,sql):
    result=sandbox_runner.execute(sql)
    assert not result.success
    assert result.error_type in {"unsafe_function","forbidden_schema"}


def test_oversized_cell_is_rejected_before_transfer(sandbox_runner):
    tracemalloc.start()
    try:
        result=sandbox_runner.execute("SELECT repeat('x',1000000)")
        _,peak=tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert not result.success and result.error_type=="result_too_large"
    assert result.rows==[]
    assert peak < 5_000_000


def test_serialized_result_limit(sandbox_runner):
    runner=SandboxRunner(get_settings().model_copy(update={"sandbox_max_result_bytes":1024,"sandbox_max_cell_bytes":256}))
    result=runner.execute("SELECT repeat('x',200) FROM generate_series(1,20)")
    assert not result.success and result.error_type=="result_too_large"
    assert result.rows==[]


def test_zero_column_postgresql_rows_remain_valid_and_bounded(sandbox_runner):
    result = sandbox_runner.execute("SELECT FROM generate_series(1,2)")
    assert result.success, result.error_message
    assert result.columns == [] and result.column_types == []
    assert result.rows == [[], []] and result.row_count == 2


@pytest.mark.parametrize("setup", [
    "DROP SCHEMA public CASCADE", "CREATE ROLE attacker SUPERUSER",
    "CREATE TABLE public.t(id int)", "CREATE TABLE t AS SELECT * FROM pg_catalog.pg_class",
    "CREATE TABLE t(id int); INSERT INTO t SELECT * FROM generate_series(1,100000000)",
    "CREATE FUNCTION evil() RETURNS int AS 'SELECT 1' LANGUAGE SQL",
    "CREATE TABLE t(id int DEFAULT pg_backend_pid())",
    "CREATE TABLE t(id int); INSERT INTO t VALUES(query_to_xml('SELECT 1',true,false,''))",
])
def test_setup_whitelist_rejects_before_execution(sandbox_runner,setup):
    with pytest.raises(SandboxError,match="Dataset"):
        sandbox_runner.provision_dataset(setup)


def test_minimal_setup_role_and_views(sandbox_runner):
    schema=sandbox_runner.provision_dataset("CREATE TABLE t(id integer); INSERT INTO t VALUES(1); CREATE VIEW v AS SELECT id FROM t;")
    try:
        result=sandbox_runner.execute("SELECT * FROM v",schema=schema)
        assert result.success and result.rows==[[1]]
        import psycopg
        with psycopg.connect(get_settings().sandbox_admin_url) as conn:
            flags=conn.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolcanlogin FROM pg_roles WHERE rolname='dbcas_dataset_setup'").fetchone()
            assert flags==(False,False,False,False)
    finally:sandbox_runner.drop_dataset(schema)


@pytest.mark.parametrize("sql,feature", [
    ("SELECT COALESCE(NULL,1)","null_handling"),("SELECT NULLIF(1,1)","null_handling"),
    ("SELECT * FROM a JOIN b USING(id)","join"),
    ("SELECT id,count(*) FROM a GROUP BY id HAVING count(*)>1","having"),
    ("SELECT * FROM a WHERE id IN(SELECT id FROM b)","subquery"),
])
def test_postgresql_required_features(sql,feature):
    assert feature in detect_features(sql)


@pytest.mark.parametrize("raw", [
    {"rows":[[1],[1,2]]}, {"columns":["x"],"rows":[[1,2]]},
    {"rows":[[float('nan')]]}, {"rows":[[{}]]}, {"rows":[],"ordered":"false"},
])
def test_invalid_expected_fixture_rejected(raw):
    assert parse_expected(raw) is None

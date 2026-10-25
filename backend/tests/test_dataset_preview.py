from app.services.dataset_preview import dataset_tables


def test_literal_tables_preserve_columns_values_and_quoted_names():
    result = dataset_tables('''CREATE TABLE "Students" (id INTEGER, name TEXT, score NUMERIC(5,2), active BOOLEAN);
        INSERT INTO "Students" (name, active, score, id) VALUES ('An, O''Brien', TRUE, -8.5, 1), ('Binh', FALSE, NULL, 2);
        CREATE TABLE classes (id INTEGER);''')
    assert [t["name"] for t in result] == ["Students", "classes"]
    assert [c["name"] for c in result[0]["columns"]] == ["id", "name", "score", "active"]
    assert result[0]["rows"] == [["1", "An, O'Brien", "-8.5", True], ["2", "Binh", None, False]]
    assert result[1]["rows"] == []


def test_preview_does_not_guess_computed_or_omitted_values():
    for setup in [
        'CREATE TABLE t (id INT); INSERT INTO t SELECT 1;',
        'CREATE TABLE t (id INT); INSERT INTO t VALUES (1+2);',
        'CREATE TABLE t (id INT, name TEXT DEFAULT \'An\'); INSERT INTO t (id) VALUES (1);',
        'CREATE TABLE t (id INT); INSERT INTO t VALUES (1); UPDATE t SET id=2;',
    ]:
        assert dataset_tables(setup) == []


def test_limits_visible_rows_and_reports_total_without_changing_values():
    data = dataset_tables('CREATE TABLE t (id INT); INSERT INTO t VALUES ' + ','.join(f'({i})' for i in range(105)) + ';')[0]
    assert data["row_count"] == 105
    assert len(data["rows"]) == 100
    assert data["rows"][-1] == ["99"]

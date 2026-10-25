"""SQL Foundations expansion, MEDIUM band (level 3).

Ten MCQs, two practicals and one essay cover DDL and DML knowledge at
multi-step level: upsert arbitration, DELETE ... USING, UPDATE ... FROM,
identity versus serial, referential actions, UNIQUE and NULL, CTAS, and
NOT VALID constraints. Practicals remain read-only SELECTs inside the
sandbox rules.
"""

from lib import essay, mcq, sqlq
from sources import (
    PG_ALTER,
    PG_CONSTRAINTS,
    PG_CREATE_TABLE,
    PG_CREATE_TABLE_AS,
    PG_DELETE,
    PG_IDENTITY,
    PG_INSERT,
    PG_TRUNCATE,
    PG_UPDATE,
    PG_VIEW,
)

QUESTIONS = [
    mcq(
        "sf-medium-on-conflict-do-nothing",
        ["SQL-DML-KNOW"],
        3,
        (
            "Table account(account_id INT PRIMARY KEY, email TEXT NOT NULL "
            "UNIQUE) already holds account_id = 7. The statement INSERT INTO "
            "account (account_id, email) VALUES (7, 'new@example.edu') ON "
            "CONFLICT (account_id) DO NOTHING; is executed. What is the "
            "result?"
        ),
        [
            "No new row is stored and the statement completes successfully.",
            "The existing row's email is replaced with 'new@example.edu'.",
            "An error is raised because account_id already exists.",
            "A second row with account_id = 7 is inserted.",
        ],
        0,
        (
            "ON CONFLICT (account_id) DO NOTHING names account_id as the "
            "arbiter; when a conflict with the existing key occurs, the proposed "
            "row is discarded and the command still succeeds. Replacing the "
            "email requires DO UPDATE, and a duplicate key is an error only "
            "when no conflict action is supplied."
        ),
        [PG_INSERT, PG_CONSTRAINTS],
    ),
    mcq(
        "sf-medium-on-conflict-excluded",
        ["SQL-DML-KNOW"],
        3,
        (
            "In INSERT INTO t (id, qty) VALUES (1, 5) ON CONFLICT (id) DO "
            "UPDATE SET qty = EXCLUDED.qty, what does EXCLUDED refer to?"
        ),
        [
            "The row proposed by the INSERT, whose qty is 5.",
            "The row currently stored with id = 1.",
            "A copy of the whole table after the insert.",
            "The unique index that detected the conflict.",
        ],
        0,
        (
            "EXCLUDED is the special relation holding the row that the INSERT "
            "attempted to add. Referring to it lets the update copy the proposed "
            "values; the stored row is referenced through the target table "
            "name, not through EXCLUDED."
        ),
        [PG_INSERT],
    ),
    mcq(
        "sf-medium-update-from",
        ["SQL-DML-KNOW"],
        3,
        (
            "The statement UPDATE sale s SET amount = p.amount FROM price p "
            "WHERE p.sale_id = s.sale_id; is executed and a sale matches more "
            "than one price row. What does PostgreSQL guarantee?"
        ),
        [
            "Each target row is updated at most once, using one of the "
            "matching price rows chosen arbitrarily.",
            "The target row is updated once per matching price row, so the last "
            "match wins deterministically.",
            "The statement fails with a cardinality error.",
            "Every matching price row is inserted as a new sale row.",
        ],
        0,
        (
            "UPDATE ... FROM joins the target to the source, and a target row "
            "that matches several source rows is still updated only once; which "
            "match supplies the value is not defined. A deterministic result "
            "therefore requires the source side to be unique per key. No "
            "cardinality error is raised, and UPDATE never inserts rows."
        ),
        [PG_UPDATE],
    ),
    mcq(
        "sf-medium-delete-using",
        ["SQL-DML-KNOW"],
        3,
        (
            "The statement DELETE FROM sale s USING customer c WHERE "
            "c.customer_id = s.customer_id AND c.status = 'closed'; is "
            "executed. Which rows are deleted?"
        ),
        [
            "Sales whose customer exists in customer and has status 'closed'.",
            "Every customer row with status 'closed'.",
            "All sales rows, because USING replaces the WHERE clause.",
            "Sales with no matching customer.",
        ],
        0,
        (
            "DELETE ... USING names extra tables that the WHERE clause may "
            "reference; only rows of the deletion target (sale) that satisfy "
            "the join and filter are removed. Customer rows are never deleted "
            "by a DELETE targeting sale, and sales with no match fail the join "
            "condition and survive."
        ),
        [PG_DELETE],
    ),
    mcq(
        "sf-medium-identity-vs-serial",
        ["SQL-DDL-KNOW"],
        3,
        (
            "Which statement about identity columns compared with serial is "
            "correct in PostgreSQL?"
        ),
        [
            "GENERATED ALWAYS AS IDENTITY is SQL-standard, is backed by a "
            "sequence, and rejects an explicit value unless OVERRIDING SYSTEM "
            "VALUE is given.",
            "Identity columns store no sequence and generate unique values "
            "without any catalog object.",
            "GENERATED ALWAYS AS IDENTITY accepts explicit values exactly like "
            "serial does.",
            "Serial columns are the standard syntax and identity columns are a "
            "deprecated compatibility feature.",
        ],
        0,
        (
            "Identity columns are the standard replacement for serial. Both use "
            "a sequence, but GENERATED ALWAYS rejects an explicit insert value "
            "unless the statement says OVERRIDING SYSTEM VALUE; GENERATED BY "
            "DEFAULT accepts explicit values. Serial is the older, "
            "non-standard shorthand."
        ),
        [PG_IDENTITY, PG_CREATE_TABLE],
    ),
    mcq(
        "sf-medium-fk-on-delete",
        ["SQL-DDL-KNOW"],
        3,
        (
            "Table order_line references order with ON DELETE RESTRICT, while "
            "table audit_note references order with ON DELETE CASCADE. An "
            "order that has rows in both tables is deleted. What happens?"
        ),
        [
            "The DELETE is rejected because order_line rows would be orphaned; "
            "no order row is removed.",
            "The order and all referencing rows in both tables are deleted.",
            "The order is deleted and only audit_note rows are removed.",
            "The order is deleted and the referencing rows are set to NULL.",
        ],
        0,
        (
            "Referential actions are enforced per constraint. RESTRICT prevents "
            "the deletion while a referencing row exists, and the whole "
            "statement fails atomically, so the order is not deleted and the "
            "CASCADE effect never happens. SET NULL applies only when the "
            "constraint declares ON DELETE SET NULL."
        ),
        [PG_CONSTRAINTS],
    ),
    mcq(
        "sf-medium-unique-nulls",
        ["SQL-DDL-KNOW"],
        3,
        (
            "Table customer(email TEXT UNIQUE) uses the default NULL treatment. "
            "Two rows are inserted with email = NULL. What happens?"
        ),
        [
            "Both rows are accepted, because a UNIQUE constraint treats NULL "
            "values as distinct.",
            "The second insert is rejected, because NULL equals NULL for a "
            "unique constraint.",
            "The first NULL is replaced by the second NULL.",
            "Both rows are accepted, and one NULL is converted to an empty "
            "string.",
        ],
        0,
        (
            "A UNIQUE constraint compares values with equality, and NULL is "
            "never equal to NULL, so any number of NULLs may coexist. A "
            "constraint declared UNIQUE NULLS NOT DISTINCT would reject the "
            "second NULL. No value is rewritten."
        ),
        [PG_CONSTRAINTS, PG_INSERT],
    ),
    mcq(
        "sf-medium-create-table-as",
        ["SQL-DDL-KNOW"],
        3,
        (
            "CREATE TABLE sale_backup AS SELECT * FROM sale; is executed. What "
            "does the new table contain?"
        ),
        [
            "A copy of the current rows, with column types inferred but without "
            "the primary key or other constraints of sale.",
            "An empty table whose columns and constraints are copied from sale.",
            "A view over sale that always shows the latest rows.",
            "A table that stays synchronized with sale automatically.",
        ],
        0,
        (
            "CREATE TABLE AS materializes the query result once; later changes "
            "to sale do not appear. Column names and types are derived from the "
            "query, but constraints such as primary keys, unique constraints "
            "and foreign keys are not copied. A view or a materialized view is "
            "a different object."
        ),
        [PG_CREATE_TABLE_AS],
    ),
    mcq(
        "sf-medium-constraint-not-valid",
        ["SQL-DDL-KNOW"],
        3,
        (
            "ALTER TABLE sale ADD CONSTRAINT sale_amount_ck CHECK (amount >= 0) "
            "NOT VALID; is executed on a table that already contains a negative "
            "amount. What is the effect?"
        ),
        [
            "The constraint is added without checking existing rows; new "
            "inserts and updates of any row must satisfy it.",
            "The statement is rejected because existing rows violate the "
            "constraint.",
            "The constraint is added and the offending rows are deleted.",
            "The constraint is added and the offending values are set to 0.",
        ],
        0,
        (
            "NOT VALID skips the initial scan of existing rows, which is why the "
            "statement succeeds despite the stored negative amount. The "
            "constraint is enforced for every new or changed row. Existing rows "
            "can be checked later with ALTER TABLE ... VALIDATE CONSTRAINT. "
            "Nothing is deleted or rewritten automatically."
        ),
        [PG_ALTER, PG_CONSTRAINTS],
    ),
    mcq(
        "sf-medium-truncate",
        ["SQL-DML-KNOW"],
        3,
        (
            "Which statement about TRUNCATE TABLE sale is correct in PostgreSQL?"
        ),
        [
            "It removes every row, accepts no WHERE clause, and can be rolled "
            "back because it is transactional.",
            "It removes every row and cannot be rolled back because it commits "
            "immediately.",
            "It removes selected rows when a WHERE clause is supplied.",
            "It removes the table definition as well as its rows.",
        ],
        0,
        (
            "TRUNCATE empties the table; it has no WHERE clause, so it cannot "
            "remove selected rows. In PostgreSQL TRUNCATE is transactional and "
            "rolls back with the transaction. It does not drop the table; DROP "
            "TABLE removes the definition."
        ),
        [PG_TRUNCATE, PG_DELETE],
    ),
    sqlq(
        "sf-medium-view-aggregate",
        ["SQL-DDL-KNOW"],
        3,
        (
            "The setup creates dept(dept_id INT PRIMARY KEY, dept_name TEXT NOT "
            "NULL) and emp(emp_id INT PRIMARY KEY, dept_id INT, name TEXT), "
            "then the view dept_headcount whose stored query left-joins emp to "
            "dept and groups by department, producing dept_id, dept_name and "
            "headcount = count(emp.emp_id). Return dept_id, dept_name and "
            "headcount for every row of the view, ordered by dept_id ascending."
        ),
        (
            "SELECT dept_id, dept_name, headcount FROM dept_headcount "
            "ORDER BY dept_id"
        ),
        [
            (
                "aggregate_view",
                False,
                "CREATE TABLE dept(dept_id INT PRIMARY KEY, dept_name TEXT NOT "
                "NULL);"
                "CREATE TABLE emp(emp_id INT PRIMARY KEY, dept_id INT, name "
                "TEXT);"
                "CREATE VIEW dept_headcount AS SELECT d.dept_id, d.dept_name, "
                "count(e.emp_id) AS headcount FROM dept d LEFT JOIN emp e ON "
                "e.dept_id = d.dept_id GROUP BY d.dept_id, d.dept_name;"
                "INSERT INTO dept VALUES (1,'Research'),(2,'Sales');"
                "INSERT INTO emp VALUES (10,1,'An'),(11,1,'Binh'),(12,NULL,'Chi');",
            ),
            (
                "empty_tables",
                True,
                "CREATE TABLE dept(dept_id INT PRIMARY KEY, dept_name TEXT NOT "
                "NULL);"
                "CREATE TABLE emp(emp_id INT PRIMARY KEY, dept_id INT, name "
                "TEXT);"
                "CREATE VIEW dept_headcount AS SELECT d.dept_id, d.dept_name, "
                "count(e.emp_id) AS headcount FROM dept d LEFT JOIN emp e ON "
                "e.dept_id = d.dept_id GROUP BY d.dept_id, d.dept_name;",
            ),
        ],
        (
            "A view stores the query, so the aggregate is recomputed on every "
            "read. Because the view left-joins from dept, Sales has headcount 0 "
            "rather than disappearing, and the employee with a NULL dept_id "
            "matches no department and is not counted. The empty dataset "
            "returns no rows."
        ),
        [PG_VIEW, PG_CONSTRAINTS],
    ),
    sqlq(
        "sf-medium-insert-duplicates",
        ["SQL-DML-KNOW"],
        3,
        (
            "The setup creates note(note_id INT, body TEXT) with no primary key "
            "or unique constraint and inserts some note_id values more than "
            "once. Return note_id and copies (BIGINT) for the note_id values "
            "that are stored more than once, ordered by note_id ascending."
        ),
        (
            "SELECT note_id, count(*) AS copies FROM note "
            "GROUP BY note_id HAVING count(*) > 1 ORDER BY note_id"
        ),
        [
            (
                "duplicates_accepted",
                False,
                "CREATE TABLE note(note_id INT, body TEXT);"
                "INSERT INTO note VALUES (1,'a'),(1,'b'),(2,'c'),(3,'d'),"
                "(3,'e'),(3,'f');",
            ),
            (
                "no_duplicates",
                True,
                "CREATE TABLE note(note_id INT, body TEXT);"
                "INSERT INTO note VALUES (1,'a'),(2,'b'),(3,'c');",
            ),
        ],
        (
            "Without a primary key or unique constraint INSERT performs no "
            "duplicate checking, so the same note_id can be stored repeatedly. "
            "GROUP BY with HAVING count(*) > 1 surfaces those keys; note_id 1 "
            "appears twice and note_id 3 three times in the first dataset, and "
            "the clean dataset correctly returns no rows. Declaring note_id as "
            "a primary key would have rejected the repeated values instead."
        ),
        [PG_INSERT, PG_CONSTRAINTS],
    ),
    essay(
        "sf-medium-upsert",
        ["SQL-DML-KNOW", "SQL-DDL-KNOW"],
        3,
        (
            "Explain how INSERT ... ON CONFLICT works in PostgreSQL. Cover which "
            "object acts as the arbiter, the difference between DO NOTHING and "
            "DO UPDATE, the role of EXCLUDED, what happens when no unique index "
            "matches the conflict target, and why this is safer than a "
            "SELECT-then-INSERT sequence under concurrent writers."
        ),
        (
            "ON CONFLICT requires an arbiter: a unique index or unique/Primary "
            "key constraint on the conflict target, either named with ON "
            "CONFLICT ON CONSTRAINT or inferred from a column list. DO NOTHING "
            "discards the proposed row silently; DO UPDATE applies an update "
            "whose SET expression may read EXCLUDED, the proposed row, and the "
            "existing row through the table name. If no matching unique index "
            "exists, PostgreSQL raises an error because it cannot detect the "
            "conflict. A SELECT followed by INSERT is a race: two sessions can "
            "both find no row and then both insert. ON CONFLICT resolves the "
            "conflict atomically inside the INSERT, so one statement succeeds "
            "and the intended action (skip or update) is applied without a "
            "window for a duplicate-key failure."
        ),
        (
            "The answer must identify the unique index as the arbiter, contrast "
            "DO NOTHING with DO UPDATE, explain EXCLUDED, note the error when no "
            "matching index exists, and justify the concurrency advantage over "
            "check-then-insert."
        ),
        (
            "Describes ON CONFLICT as a generic INSERT flag without an arbiter, "
            "or cannot say what EXCLUDED means; no reference to unique indexes "
            "or concurrency.",
            "Correct high-level idea but confuses DO NOTHING with DO UPDATE, or "
            "omits what happens when no unique index matches the target. "
            "Concurrency argument is vague.",
            "Correct arbiter and action semantics with EXCLUDED explained, but "
            "one detail is missing, such as the error for a missing index or the "
            "race in check-then-insert.",
            "Fully correct: names the unique index/constraint arbiter, "
            "distinguishes DO NOTHING and DO UPDATE, explains EXCLUDED as the "
            "proposed row, states the error when no matching index exists, and "
            "shows that ON CONFLICT resolves the conflict atomically while "
            "SELECT-then-INSERT can race.",
        ),
        [PG_INSERT, PG_CONSTRAINTS],
    ),
]

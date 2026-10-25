"""PostgreSQL Data Manipulation expansion, EASY band (levels 1-2).

The two practicals use the pattern that the read-only sandbox allows: the
prompt names a DML statement and the learner returns exactly the rows that
statement would store, so the answer tests the statement's visible result
rather than replaying the write.
"""

from lib import essay, mcq, sqlq
from sources import PG_CONSTRAINTS, PG_DELETE, PG_INSERT, PG_MERGE, PG_UPDATE

QUESTIONS = [
    mcq(
        "dm-easy-default-values",
        ["PG-DML"],
        2,
        (
            "Table session_log(session_id INT GENERATED ALWAYS AS IDENTITY "
            "PRIMARY KEY, started_at TEXT NOT NULL DEFAULT 'unknown', note "
            "TEXT) is empty. The statement INSERT INTO session_log DEFAULT "
            "VALUES; is executed. What is stored?"
        ),
        [
            "One row with a generated session_id, started_at = 'unknown' and "
            "note = NULL.",
            "No row, because DEFAULT VALUES requires at least one explicit "
            "column value.",
            "One row with every column set to NULL.",
            "An error, because an identity column cannot be combined with "
            "DEFAULT VALUES.",
        ],
        0,
        (
            "DEFAULT VALUES inserts a row in which every column receives its "
            "default. The identity column generates a value, started_at takes "
            "its declared default, and note has no default and is nullable, so "
            "it becomes NULL. The statement is valid whenever every NOT NULL "
            "column can be satisfied by a default or identity."
        ),
        [PG_INSERT],
    ),
    mcq(
        "dm-easy-insert-select",
        ["PG-DML"],
        2,
        (
            "The statement INSERT INTO archive (sale_id, amount) SELECT sale_id, "
            "amount FROM sale WHERE status = 'closed'; is executed. Which rows "
            "are added to archive?"
        ),
        [
            "One archive row for every sale row whose status is 'closed'.",
            "One archive row per column of sale, because SELECT is evaluated per "
            "column.",
            "All sale rows regardless of status, because INSERT copies the whole "
            "source table.",
            "No rows unless archive is empty, because INSERT refuses to append "
            "to a non-empty table.",
        ],
        0,
        (
            "INSERT ... SELECT inserts one row for every row the SELECT returns, "
            "so the WHERE clause decides which sales are archived. The source "
            "can be non-empty and the target can already hold rows; nothing "
            "prevents appending."
        ),
        [PG_INSERT],
    ),
    mcq(
        "dm-easy-update-null-flag",
        ["PG-DML"],
        2,
        (
            "Table account has a nullable verified BOOLEAN column. The statement "
            "UPDATE account SET verified = FALSE WHERE verified IS NULL; is "
            "executed twice in a row. What is the effect?"
        ),
        [
            "The first run changes the rows whose verified is NULL; the second "
            "run changes no rows.",
            "Each run changes every row, because UPDATE always rewrites the "
            "whole table.",
            "The second run restores NULL values, because WHERE is re-evaluated "
            "against the original snapshot.",
            "The statement fails the second time because FALSE is not a valid "
            "boolean.",
        ],
        0,
        (
            "The WHERE clause selects only rows whose value is NULL, so the "
            "first run sets them to FALSE. After that no row satisfies the "
            "predicate, so the second run updates zero rows. UPDATE never "
            "rewrites rows that fail the WHERE clause."
        ),
        [PG_UPDATE],
    ),
    mcq(
        "dm-easy-insert-returning",
        ["PG-DML"],
        2,
        (
            "Table task(task_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, "
            "title TEXT) is used with INSERT INTO task (title) VALUES ('write "
            "report') RETURNING task_id; What does the statement return?"
        ),
        [
            "One row containing the generated task_id of the inserted row.",
            "An empty result, because RETURNING applies only to UPDATE and "
            "DELETE.",
            "Every task_id currently stored in the table.",
            "The text 'write report' instead of a number.",
        ],
        0,
        (
            "RETURNING is available on INSERT as well as UPDATE and DELETE and "
            "reports values from the rows the statement affected. Here it "
            "surfaces the identity value generated for the new row, so the "
            "client learns the key without a second query."
        ),
        [PG_INSERT],
    ),
    mcq(
        "dm-easy-merge-purpose",
        ["PG-MERGE"],
        2,
        (
            "What is MERGE used for?"
        ),
        [
            "Applying conditional insert, update or delete actions to a target "
            "table from rows of a source in one statement.",
            "Merging two tables into a single physical file on disk.",
            "Concatenating the text columns of two tables.",
            "Combining two result sets into one output, like UNION.",
        ],
        0,
        (
            "MERGE compares source rows with target rows using an ON condition "
            "and runs the action of the first matching WHEN clause, so one "
            "statement can update matched rows, insert unmatched source rows and, "
            "in PostgreSQL 17, delete target rows with no source match. It is "
            "not a storage or set-operation command."
        ),
        [PG_MERGE],
    ),
    mcq(
        "dm-easy-multi-row-atomicity",
        ["PG-DML"],
        2,
        (
            "INSERT INTO tag (tag_id, label) VALUES (1, 'a'), (1, 'b'); is run "
            "on tag(tag_id INT PRIMARY KEY, label TEXT), and no row with tag_id "
            "= 1 exists yet. What is the outcome?"
        ),
        [
            "The whole statement fails and no row is stored, because the second "
            "row violates the primary key.",
            "The first row is stored and only the second row is rejected.",
            "Both rows are stored, because a primary key is checked after the "
            "statement.",
            "The second row replaces the first one silently.",
        ],
        0,
        (
            "A single INSERT statement is atomic: the primary key is checked for "
            "each proposed row, and a violation aborts the statement, so the "
            "first row is not kept either. MySQL-style per-row continuation and "
            "silent replacement both require different syntax and are not "
            "PostgreSQL behaviour."
        ),
        [PG_INSERT, PG_CONSTRAINTS],
    ),
    sqlq(
        "dm-easy-inserted-state",
        ["PG-DML"],
        2,
        (
            "The setup creates shipment(shipment_id INT GENERATED ALWAYS AS "
            "IDENTITY PRIMARY KEY, carrier TEXT NOT NULL, status TEXT NOT NULL "
            "DEFAULT 'pending', note TEXT) and then runs the INSERT statements "
            "shown in the dataset. Return shipment_id, carrier, status and note "
            "for every stored row, ordered by shipment_id ascending."
        ),
        (
            "SELECT shipment_id, carrier, status, note FROM shipment "
            "ORDER BY shipment_id"
        ),
        [
            (
                "omitted_columns",
                False,
                "CREATE TABLE shipment(shipment_id INT GENERATED ALWAYS AS "
                "IDENTITY PRIMARY KEY, carrier TEXT NOT NULL, status TEXT NOT "
                "NULL DEFAULT 'pending', note TEXT);"
                "INSERT INTO shipment (carrier) VALUES ('DHL'),('Viettel Post');",
            ),
            (
                "mixed_explicit_and_omitted",
                True,
                "CREATE TABLE shipment(shipment_id INT GENERATED ALWAYS AS "
                "IDENTITY PRIMARY KEY, carrier TEXT NOT NULL, status TEXT NOT "
                "NULL DEFAULT 'pending', note TEXT);"
                "INSERT INTO shipment (carrier) VALUES ('DHL');"
                "INSERT INTO shipment (carrier, status) VALUES "
                "('GHN','delivered');"
                "INSERT INTO shipment (carrier, note) VALUES ('VNPost',NULL);",
            ),
        ],
        (
            "Each INSERT stores exactly the columns it names; an identity "
            "column fills its own value and any column omitted from the column "
            "list receives its default or NULL. In the first dataset one insert "
            "names status explicitly as 'delivered' while the others fall back "
            "to 'pending', and every note is NULL; the second dataset has status "
            "'pending' everywhere because no insert names it. Because the id is "
            "GENERATED ALWAYS, the statements cannot supply shipment_id "
            "themselves."
        ),
        [PG_INSERT, PG_CONSTRAINTS],
    ),
    sqlq(
        "dm-easy-insert-select-rows",
        ["PG-DML"],
        2,
        (
            "The setup creates sale(sale_id INT PRIMARY KEY, status TEXT, "
            "amount INT) and archive(sale_id INT PRIMARY KEY, amount INT), "
            "inserts rows into sale and leaves archive empty. The next step is "
            "INSERT INTO archive (sale_id, amount) SELECT sale_id, amount FROM "
            "sale WHERE status = 'closed'; Writing the INSERT itself is not "
            "possible in the sandbox, so return exactly the sale_id and amount "
            "rows that this statement would add to archive, ordered by sale_id "
            "ascending."
        ),
        (
            "SELECT sale_id, amount FROM sale WHERE status = 'closed' "
            "ORDER BY sale_id"
        ),
        [
            (
                "closed_sales",
                False,
                "CREATE TABLE sale(sale_id INT PRIMARY KEY, status TEXT, amount "
                "INT);"
                "CREATE TABLE archive(sale_id INT PRIMARY KEY, amount INT);"
                "INSERT INTO sale VALUES (1,'closed',100),(2,'open',200),"
                "(3,'closed',NULL),(4,'closed',300);",
            ),
            (
                "no_closed_sales",
                True,
                "CREATE TABLE sale(sale_id INT PRIMARY KEY, status TEXT, amount "
                "INT);"
                "CREATE TABLE archive(sale_id INT PRIMARY KEY, amount INT);"
                "INSERT INTO sale VALUES (5,'open',50),(6,'pending',70);",
            ),
        ],
        (
            "INSERT ... SELECT copies one row per row returned by its SELECT, so "
            "the archived rows are exactly the 'closed' sales: 1, 3 and 4, "
            "including sale 3 whose NULL amount is copied unchanged. The second "
            "dataset has no closed sales, so the INSERT would add nothing and "
            "the correct result is empty."
        ),
        [PG_INSERT],
    ),
    essay(
        "dm-easy-returning",
        ["PG-DML"],
        2,
        (
            "Explain RETURNING in PostgreSQL INSERT, UPDATE and DELETE. State "
            "what values it exposes, give one example of INSERT ... RETURNING "
            "and one of DELETE ... RETURNING, and explain why returning the "
            "affected rows inside the same statement is preferable to issuing a "
            "follow-up SELECT."
        ),
        (
            "RETURNING computes an output row for every row the statement "
            "inserted, updated or deleted, and may reference that row's columns. "
            "For INSERT INTO task (title) VALUES ('x') RETURNING task_id, the "
            "generated identity value is returned. For DELETE FROM task WHERE "
            "task_id = 7 RETURNING *, the deleted row's contents are returned, "
            "which is useful for archiving. UPDATE ... RETURNING reports the "
            "values after the update. Because the rows are returned by the same "
            "statement, the client avoids a second query that could see "
            "different data if another session changed the rows in between, and "
            "it avoids guessing which row was affected. The values correspond "
            "exactly to the rows this statement modified, inside the same "
            "transactional snapshot."
        ),
        (
            "The answer must define RETURNING across the three statements, give "
            "a valid example, and justify atomicity: the returned rows are "
            "exactly the affected rows in the same statement, so a follow-up "
            "SELECT can race."
        ),
        (
            "Says RETURNING exists only for SELECT-like queries or gives no "
            "example; no atomicity argument.",
            "Correct basic examples but confuses which statement's rows are "
            "returned, or claims RETURNING replaces a WHERE clause.",
            "Correct semantics and examples, but the atomicity/race argument is "
            "missing or vague.",
            "Fully correct: RETURNING exposes affected-row values for INSERT, "
            "UPDATE and DELETE with valid examples, notes that UPDATE reports "
            "post-update values, and explains that a follow-up SELECT can see "
            "changed data whereas RETURNING reports exactly the affected rows in "
            "the same statement.",
        ),
        [PG_INSERT, PG_UPDATE, PG_DELETE],
    ),
]

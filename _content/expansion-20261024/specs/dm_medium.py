"""PostgreSQL Data Manipulation expansion, MEDIUM band (level 3).

Seven MCQs cover conditional conflict actions, MERGE clause ordering, data-
modifying CTEs, RETURNING scope and VALUES sources. The two practicals ask
for the rows a named UPDATE or ON CONFLICT statement would produce, which the
read-only sandbox can verify without executing the write.
"""

from lib import mcq, sqlq
from sources import (
    PG_QUERIES_WITH,
    PG_DELETE,
    PG_INSERT,
    PG_JOIN_TUTORIAL,
    PG_MERGE,
    PG_COMPARISON,
    PG_UPDATE,
)

QUESTIONS = [
    mcq(
        "dm-medium-on-conflict-update-where",
        ["PG-DML"],
        3,
        (
            "The statement INSERT INTO stock (item, qty) VALUES ('bolt', 5) ON "
            "CONFLICT (item) DO UPDATE SET qty = EXCLUDED.qty WHERE stock.qty < "
            "EXCLUDED.qty is executed, and the stored qty for 'bolt' is 9. What "
            "happens?"
        ),
        [
            "Neither the update nor the insert occurs; the row is skipped "
            "because the DO UPDATE condition is false.",
            "The insert occurs and a second 'bolt' row is added.",
            "The update occurs anyway, and the WHERE clause is ignored for DO "
            "UPDATE.",
            "The stored qty is set to 5 and then to 9.",
        ],
        0,
        (
            "A WHERE clause attached to DO UPDATE is a condition on the update "
            "itself. When it is false, the conflicting row is left unchanged and "
            "the proposed row is not inserted either, so the statement simply "
            "skips that row. It never turns a conflict into an insert."
        ),
        [PG_INSERT],
    ),
    mcq(
        "dm-medium-merge-clause-order",
        ["PG-MERGE"],
        3,
        (
            "A MERGE statement has two WHEN MATCHED clauses, the first guarded by "
            "AND s.priority = 'high' and the second unconditional. A target row "
            "matches a source row whose priority is 'low'. Which clause runs?"
        ),
        [
            "The second, unconditional WHEN MATCHED clause, because clauses are "
            "evaluated in order and the first condition is false.",
            "Both clauses run, applying two updates.",
            "Neither clause runs, because a guarded clause disables the rest.",
            "The statement is rejected because only one WHEN MATCHED clause is "
            "allowed.",
        ],
        0,
        (
            "MERGE evaluates WHEN clauses in the order written and runs the "
            "first one whose condition holds; later clauses are not applied to "
            "the same row. Several WHEN MATCHED clauses are legal, which is how "
            "priority-dependent actions are expressed."
        ),
        [PG_MERGE],
    ),
    mcq(
        "dm-medium-data-modifying-cte",
        ["PG-DML", "PG-CTE"],
        3,
        (
            "The statement WITH moved AS (DELETE FROM inbox WHERE archived RETURNING *) "
            "INSERT INTO archive SELECT * FROM moved; is executed. What is the "
            "effect?"
        ),
        [
            "The matching inbox rows are deleted and the same rows are inserted "
            "into archive in one atomic statement.",
            "The rows are copied into archive and remain in inbox until a "
            "separate DELETE runs.",
            "The statement fails, because a CTE may not contain DELETE.",
            "The DELETE runs once per row inserted into archive, duplicating "
            "the source.",
        ],
        0,
        (
            "PostgreSQL allows data-modifying statements inside WITH. The DELETE "
            "runs once, and its RETURNING output is the row set the INSERT "
            "consumes, so the move is atomic within the statement. A CTE is "
            "executed once even if referenced more than once, and both "
            "operations see the same snapshot."
        ),
        [PG_QUERIES_WITH, PG_DELETE, PG_INSERT],
    ),
    mcq(
        "dm-medium-returning-scope",
        ["PG-DML"],
        3,
        (
            "In PostgreSQL 17, for UPDATE, what values does a RETURNING clause "
            "report?"
        ),
        [
            "The values of each updated row after the update; in PostgreSQL 17 "
            "there is no OLD pseudo-row exposing the previous values.",
            "The values each updated row had before the update.",
            "Both the old and new values, in two parallel columns.",
            "Only rows whose value actually changed; unchanged rows are "
            "omitted.",
        ],
        0,
        (
            "In PostgreSQL 17, RETURNING reports the row as it stands after the "
            "statement, so it shows the new values; there is no OLD relation in "
            "RETURNING. PostgreSQL 18 added OLD/NEW support, so version matters. "
            "Capturing previous values in 17 requires reading them beforehand or "
            "using a trigger. Rows matched by WHERE are reported even when the "
            "new value equals the old one."
        ),
        [PG_UPDATE],
    ),
    mcq(
        "dm-medium-on-conflict-on-constraint",
        ["PG-DML"],
        3,
        (
            "A unique expression index is defined on lower(email). Which conflict "
            "target lets INSERT ... ON CONFLICT resolve it explicitly?"
        ),
        [
            "ON CONFLICT (lower(email)), repeating the index expression exactly.",
            "ON CONFLICT (email), because the bare column is inferred from the "
            "expression.",
            "ON CONFLICT DO ANYTHING, which catches every unique index.",
            "ON CONFLICT (lower), naming the function without its argument.",
        ],
        0,
        (
            "The unique index is an expression index on lower(email), and an "
            "expression index is not a table constraint, so ON CONFLICT ON "
            "CONSTRAINT cannot name it. Column-list inference matches a unique "
            "index whose expressions equal the listed expressions, so the target "
            "must be (lower(email)); a bare email does not match an index on "
            "lower(email). DO ANYTHING is not PostgreSQL syntax, and a function "
            "name without its argument is not an expression."
        ),
        [PG_INSERT],
    ),
    mcq(
        "dm-medium-merge-values-source",
        ["PG-MERGE"],
        3,
        (
            "Which MERGE statement correctly uses an inline VALUES list as its "
            "source?"
        ),
        [
            "MERGE INTO stock s USING (VALUES (1, 'bolt'), (2, 'nut')) AS src "
            "(id, item) ON s.item = src.item WHEN MATCHED THEN UPDATE SET "
            "id = src.id;",
            "MERGE INTO stock s USING VALUES (1, 'bolt') ON s.item = item "
            "WHEN MATCHED THEN UPDATE SET id = 1;",
            "MERGE INTO stock s USING (VALUES (1, 'bolt')) ON s.item = item "
            "WHEN MATCHED THEN UPDATE SET id = 1;",
            "MERGE INTO stock s USING src VALUES (1, 'bolt') ON s.item = "
            "src.item WHEN MATCHED THEN UPDATE SET id = 1;",
        ],
        0,
        (
            "A VALUES list used as a MERGE source must be a parenthesized "
            "subquery with a table alias and explicit column names, so that ON "
            "and the actions can refer to src.item. Without the alias and "
            "column list the source columns have no deterministic names. The "
            "other options are syntax that PostgreSQL does not accept."
        ),
        [PG_MERGE],
    ),
    mcq(
        "dm-medium-delete-using-returning",
        ["PG-DML"],
        3,
        (
            "DELETE FROM stale s USING current c WHERE s.sale_id = c.sale_id "
            "RETURNING s.sale_id, s.amount; is executed. What does RETURNING "
            "contain?"
        ),
        [
            "One row for each stale row deleted, with the deleted row's sale_id "
            "and amount.",
            "One row for each current row matched by the USING clause.",
            "Columns from both stale and current.",
            "An error, because RETURNING cannot be combined with USING.",
        ],
        0,
        (
            "RETURNING reports the rows the DELETE removed, so it contains "
            "stale columns only. The USING table participates in the join but "
            "no row of current is deleted, and RETURNING with USING is valid."
        ),
        [PG_DELETE],
    ),
    sqlq(
        "dm-medium-update-result",
        ["PG-DML", "PG-NULLS"],
        3,
        (
            "The setup creates account(account_id INT PRIMARY KEY, balance INT) "
            "and inserts rows, some with a NULL balance. The next step is "
            "UPDATE account SET balance = balance + 100 WHERE balance IS NOT "
            "NULL; Writing the UPDATE is not possible in the sandbox, so return "
            "the rows the statement would leave with columns account_id and "
            "balance (the new value), ordered by account_id ascending."
        ),
        (
            "SELECT account_id, balance + 100 AS balance FROM account "
            "WHERE balance IS NOT NULL ORDER BY account_id"
        ),
        [
            (
                "mixed_null_balances",
                False,
                "CREATE TABLE account(account_id INT PRIMARY KEY, balance INT);"
                "INSERT INTO account VALUES (1,0),(2,NULL),(3,250),(4,-40);",
            ),
            (
                "all_balances_null",
                True,
                "CREATE TABLE account(account_id INT PRIMARY KEY, balance INT);"
                "INSERT INTO account VALUES (5,NULL),(6,NULL);",
            ),
        ],
        (
            "The UPDATE applies to rows whose balance is non-NULL, so the "
            "resulting rows are 1 -> 100, 3 -> 350 and 4 -> 60; account 2 is "
            "excluded because NULL IS NOT NULL is false, and its NULL balance "
            "is not treated as zero. The second dataset has no matching row, so "
            "the statement would update nothing and the correct result is "
            "empty."
        ),
        [PG_UPDATE, PG_COMPARISON],
    ),
    sqlq(
        "dm-medium-on-conflict-skips",
        ["PG-DML"],
        3,
        (
            "The setup creates customer(customer_id INT PRIMARY KEY, name TEXT "
            "NOT NULL) and staging(customer_id INT PRIMARY KEY, name TEXT NOT "
            "NULL). The next step is INSERT INTO customer (customer_id, name) "
            "SELECT customer_id, name FROM staging ON CONFLICT (customer_id) DO "
            "NOTHING; Writing the INSERT is not possible in the sandbox, so "
            "return the staging rows that the statement would skip because "
            "their customer_id already exists in customer, with columns "
            "customer_id and name, ordered by customer_id ascending."
        ),
        (
            "SELECT s.customer_id, s.name FROM staging s "
            "JOIN customer c ON c.customer_id = s.customer_id "
            "ORDER BY s.customer_id"
        ),
        [
            (
                "overlapping_keys",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT "
                "NOT NULL);"
                "CREATE TABLE staging(customer_id INT PRIMARY KEY, name TEXT "
                "NOT NULL);"
                "INSERT INTO customer VALUES (1,'An'),(2,'Binh');"
                "INSERT INTO staging VALUES (2,'Binh Nguyen'),(3,'Chi'),"
                "(4,'Dung');",
            ),
            (
                "no_overlap",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT "
                "NOT NULL);"
                "CREATE TABLE staging(customer_id INT PRIMARY KEY, name TEXT "
                "NOT NULL);"
                "INSERT INTO customer VALUES (1,'An');"
                "INSERT INTO staging VALUES (2,'Binh'),(3,'Chi');",
            ),
        ],
        (
            "The conflict target is customer_id, so DO NOTHING skips exactly "
            "the staging rows whose key is already present. In the first "
            "dataset staging keys 2 and 3 have no customer match, so nothing is "
            "skipped; in the second dataset customer_id 2 conflicts and is "
            "skipped while 3 and 4 would be inserted. The join expresses that "
            "key overlap directly, so the second dataset returns one skipped "
            "row."
        ),
        [PG_INSERT],
    ),
]

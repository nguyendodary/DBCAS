"""PostgreSQL Data Manipulation expansion, HARD band (levels 4-5).

Eight MCQs, two practicals and one essay cover PostgreSQL 17 MERGE RETURNING
and NOT MATCHED BY SOURCE, duplicate source matches, data-modifying CTE
semantics, multi-column UPDATE from a subquery, OVERRIDING SYSTEM VALUE, and
self-referencing DELETE. Practicals return the rows a named write would
produce, which is what the read-only sandbox can verify exactly.
"""

from lib import essay, mcq, sqlq
from sources import (
    PG_COMPARISON,
    PG_QUERIES_WITH,
    PG_DELETE,
    PG_IDENTITY,
    PG_INSERT,
    PG_MERGE,
    PG_UPDATE,
)

QUESTIONS = [
    mcq(
        "dm-hard-merge-returning",
        ["PG-MERGE"],
        5,
        (
            "PostgreSQL 17 executes MERGE INTO stock s USING feed f ON "
            "s.item = f.item WHEN MATCHED THEN UPDATE SET qty = f.qty WHEN NOT "
            "MATCHED THEN INSERT (item, qty) VALUES (f.item, f.qty) RETURNING "
            "merge_action(), s.item; What does RETURNING produce?"
        ),
        [
            "One row per affected target row with the action performed "
            "('INSERT', 'UPDATE' or 'DELETE') and the item.",
            "One row per source row, regardless of whether it matched.",
            "Only the inserted rows, because RETURNING on MERGE is limited to "
            "INSERT actions.",
            "An error, because RETURNING is not supported on MERGE in "
            "PostgreSQL 17.",
        ],
        0,
        (
            "PostgreSQL 17 adds RETURNING to MERGE. The output covers every row "
            "inserted, updated or deleted by the command, and merge_action() "
            "reports which action ran for that row. Rows skipped because no WHEN "
            "clause applied are not reported."
        ),
        [PG_MERGE],
    ),
    mcq(
        "dm-hard-merge-not-matched-by-source",
        ["PG-MERGE"],
        5,
        (
            "MERGE INTO product p USING feed f ON f.product_id = p.product_id "
            "WHEN MATCHED THEN UPDATE SET price = f.price WHEN NOT MATCHED BY "
            "SOURCE THEN DELETE; is executed. Which rows does the "
            "NOT MATCHED BY SOURCE clause act on?"
        ),
        [
            "Target rows that have no matching source row; the clause deletes "
            "them.",
            "Source rows that have no matching target row.",
            "Target rows that matched but whose price is NULL.",
            "All target rows, because BY SOURCE overrides the ON condition.",
        ],
        0,
        (
            "WHEN NOT MATCHED BY SOURCE is a PostgreSQL extension that addresses "
            "rows of the target which the source never matched, so it is the "
            "natural place to delete products no longer present in the feed. "
            "Source rows with no target match are the ordinary NOT MATCHED "
            "[BY TARGET] case, which inserts."
        ),
        [PG_MERGE],
    ),
    mcq(
        "dm-hard-merge-duplicate-match",
        ["PG-MERGE"],
        5,
        (
            "A MERGE source table contains two rows with the same join key, and "
            "both match one target row through an unconditional WHEN MATCHED "
            "THEN UPDATE. What happens?"
        ),
        [
            "The target row is modified by one candidate change row, and a later "
            "attempt to modify the same row raises an error, so the join must "
            "produce at most one source row per target row.",
            "The target row is updated twice and the second value wins.",
            "The two source rows are merged into one automatically.",
            "The WHEN MATCHED clause is skipped for that target row and the "
            "statement commits.",
        ],
        0,
        (
            "MERGE requires at most one candidate change row per target row. "
            "When several source rows match, only one is used to modify the "
            "target and any later attempt to modify the same row errors, so the "
            "whole statement fails. Deduplicating or aggregating the source "
            "before the MERGE is the standard fix."
        ),
        [PG_MERGE],
    ),
    mcq(
        "dm-hard-cte-move-upsert",
        ["PG-DML", "PG-CTE"],
        4,
        (
            "WITH pulled AS (DELETE FROM inbox WHERE processed RETURNING *) "
            "INSERT INTO archive (id, body) SELECT id, body FROM pulled "
            "ON CONFLICT (id) DO NOTHING; is executed. What is the result?"
        ),
        [
            "The processed inbox rows are deleted once, and archive receives the "
            "rows whose id is not already present.",
            "The processed inbox rows are deleted only for archive rows that "
            "were actually inserted.",
            "The statement fails, because a data-modifying CTE cannot feed an "
            "INSERT with ON CONFLICT.",
            "Each processed inbox row is moved even if archive already has the "
            "same id, creating duplicates.",
        ],
        0,
        (
            "The DELETE in the CTE runs once and its RETURNING rows feed the "
            "INSERT. Because ON CONFLICT (id) DO NOTHING is evaluated on the "
            "target, ids already archived are skipped, while the source rows "
            "are deleted regardless. The combination does not fail, and no "
            "duplicate id can be created because archive enforces uniqueness."
        ),
        [PG_QUERIES_WITH, PG_DELETE, PG_INSERT],
    ),
    mcq(
        "dm-hard-multi-column-subquery",
        ["PG-DML"],
        4,
        (
            "UPDATE account a SET (tier, score) = (SELECT m.tier, m.score FROM "
            "metrics m WHERE m.account_id = a.account_id); is executed, and one "
            "account has no metrics row. What happens to that account?"
        ),
        [
            "Both tier and score are set to NULL, because the scalar subquery "
            "returns no row.",
            "The account is left unchanged, because no metrics row matched.",
            "The statement fails because a row is missing from metrics.",
            "Only score becomes NULL; tier keeps its old value.",
        ],
        0,
        (
            "A multi-column assignment with a subquery sets every listed column "
            "from the subquery's single row. When the subquery yields no row, "
            "the row value is NULL, so every assigned column becomes NULL. All "
            "target rows are updated, which is why a WHERE EXISTS guard is "
            "usually added when unmatched rows should keep their values."
        ),
        [PG_UPDATE],
    ),
    mcq(
        "dm-hard-cte-evaluated-once",
        ["PG-DML", "PG-CTE"],
        4,
        (
            "WITH changed AS (UPDATE task SET done = TRUE RETURNING task_id) "
            "SELECT (SELECT count(*) FROM changed) AS updated, (SELECT "
            "count(*) FROM changed) AS total; is executed. What do the two "
            "subqueries report?"
        ),
        [
            "Both report the same count, because the CTE is executed once and "
            "both references read the same rows.",
            "The first reports the updated rows and the second reports their "
            "doubled count.",
            "The second reports zero, because a CTE can be consumed only once.",
            "The UPDATE runs twice, once per reference.",
        ],
        0,
        (
            "A WITH query is evaluated once per statement even when referenced "
            "several times; both subqueries therefore see the same set of rows "
            "returned by the UPDATE's RETURNING clause. There is no double "
            "execution and no restriction on referencing the CTE more than "
            "once."
        ),
        [PG_QUERIES_WITH, PG_UPDATE],
    ),
    mcq(
        "dm-hard-overriding-system-value",
        ["PG-DML", "PG-IDENTITY"],
        5,
        (
            "Table invoice(invoice_id INT GENERATED ALWAYS AS IDENTITY PRIMARY "
            "KEY, total INT) already contains ids 1 to 5, and the statement "
            "INSERT INTO invoice (invoice_id, total) OVERRIDING SYSTEM VALUE "
            "VALUES (100, 50); is executed. What is the consequence?"
        ),
        [
            "The explicit id 100 is stored, and the identity sequence is not "
            "advanced, so a later default insert can collide once the sequence "
            "reaches 100.",
            "The statement fails, because GENERATED ALWAYS identity columns "
            "never accept explicit values.",
            "The value 100 is ignored and an id from the sequence is used.",
            "The sequence is automatically set to 101, preventing any future "
            "collision.",
        ],
        0,
        (
            "OVERRIDING SYSTEM VALUE is exactly the escape hatch that lets an "
            "explicit value into a GENERATED ALWAYS identity column, so the "
            "statement succeeds. The sequence itself is not synchronized by the "
            "insert, which leaves a future collision unless the sequence is "
            "advanced or restarted manually. Option D describes behaviour that "
            "PostgreSQL does not perform automatically."
        ),
        [PG_IDENTITY, PG_INSERT],
    ),
    mcq(
        "dm-hard-self-join-delete",
        ["PG-DML"],
        4,
        (
            "DELETE FROM price p USING price older WHERE p.product_id = "
            "older.product_id AND older.valid_from < p.valid_from; is executed. "
            "What does it do?"
        ),
        [
            "It deletes every price row that has an older row for the same "
            "product, keeping the rows with the earliest valid_from.",
            "It deletes every price row for products that appear more than "
            "once.",
            "It deletes both the newer and the older row for each product.",
            "The statement is invalid, because a table cannot reference itself "
            "in USING.",
        ],
        0,
        (
            "The target and the USING table are the same table under different "
            "aliases, which PostgreSQL allows. A row is deleted when a row with "
            "the same product_id and a smaller valid_from exists, so only rows "
            "that are not the earliest are removed; equal valid_from values do "
            "not delete each other because the comparison is strict."
        ),
        [PG_DELETE, PG_UPDATE],
    ),
    sqlq(
        "dm-hard-update-from-changes",
        ["PG-DML", "PG-NULLS"],
        4,
        (
            "The setup creates account(account_id INT PRIMARY KEY, email TEXT) "
            "and staging(account_id INT PRIMARY KEY, email TEXT). The next step "
            "is UPDATE account a SET email = s.email FROM staging s WHERE "
            "s.account_id = a.account_id AND s.email IS DISTINCT FROM "
            "a.email; Writing the UPDATE is not possible in the sandbox, so "
            "return the rows the statement would change with columns "
            "account_id, old_email and new_email, ordered by account_id "
            "ascending."
        ),
        (
            "SELECT a.account_id, a.email AS old_email, s.email AS new_email "
            "FROM account a JOIN staging s ON s.account_id = a.account_id "
            "WHERE s.email IS DISTINCT FROM a.email ORDER BY a.account_id"
        ),
        [
            (
                "null_and_changed_values",
                False,
                "CREATE TABLE account(account_id INT PRIMARY KEY, email TEXT);"
                "CREATE TABLE staging(account_id INT PRIMARY KEY, email TEXT);"
                "INSERT INTO account VALUES (1,'a@x.edu'),(2,NULL),(3,'c@x.edu'),"
                "(4,'d@x.edu');"
                "INSERT INTO staging VALUES (1,'a@x.edu'),(2,'b@x.edu'),"
                "(3,NULL),(5,'e@x.edu');",
            ),
            (
                "already_in_sync",
                True,
                "CREATE TABLE account(account_id INT PRIMARY KEY, email TEXT);"
                "CREATE TABLE staging(account_id INT PRIMARY KEY, email TEXT);"
                "INSERT INTO account VALUES (1,'a@x.edu'),(2,'b@x.edu');"
                "INSERT INTO staging VALUES (1,'a@x.edu'),(2,'b@x.edu');",
            ),
        ],
        (
            "UPDATE ... FROM changes each target row whose join partner supplies "
            "a value that is distinct from the stored one, and IS DISTINCT FROM "
            "treats NULL as a comparable value. Account 1 is equal and skipped; "
            "account 2 changes from NULL to 'b@x.edu'; account 3 changes from "
            "'c@x.edu' to NULL; account 4 has no staging row and is untouched; "
            "staging id 5 has no target row and changes nothing. The "
            "already-in-sync dataset yields no changes."
        ),
        [PG_UPDATE, PG_COMPARISON],
    ),
    sqlq(
        "dm-hard-merge-by-source-delete",
        ["PG-MERGE", "PG-DML"],
        4,
        (
            "The setup creates product(product_id INT PRIMARY KEY, name TEXT "
            "NOT NULL) and feed(product_id INT PRIMARY KEY, price INT). The "
            "next step is MERGE INTO product p USING feed f ON "
            "f.product_id = p.product_id WHEN NOT MATCHED BY SOURCE THEN "
            "DELETE; Writing the MERGE is not possible in the sandbox, so "
            "return the target rows it would delete with columns product_id and "
            "name, ordered by product_id ascending."
        ),
        (
            "SELECT p.product_id, p.name FROM product p "
            "WHERE NOT EXISTS (SELECT 1 FROM feed f "
            "WHERE f.product_id = p.product_id) ORDER BY p.product_id"
        ),
        [
            (
                "discontinued_products",
                False,
                "CREATE TABLE product(product_id INT PRIMARY KEY, name TEXT NOT "
                "NULL);"
                "CREATE TABLE feed(product_id INT PRIMARY KEY, price INT);"
                "INSERT INTO product VALUES (1,'pen'),(2,'desk'),(3,'lamp');"
                "INSERT INTO feed VALUES (1,10),(3,45),(4,90);",
            ),
            (
                "everything_still_listed",
                True,
                "CREATE TABLE product(product_id INT PRIMARY KEY, name TEXT NOT "
                "NULL);"
                "CREATE TABLE feed(product_id INT PRIMARY KEY, price INT);"
                "INSERT INTO product VALUES (1,'pen'),(2,'desk');"
                "INSERT INTO feed VALUES (1,10),(2,20);",
            ),
        ],
        (
            "WHEN NOT MATCHED BY SOURCE addresses target rows for which the ON "
            "condition matched no source row, so the delete set is the "
            "anti-join of product against feed. In the first dataset only "
            "product 2 is absent from the feed; feed row 4 is a source-only row, "
            "which this clause does not address. The second dataset is fully "
            "matched, so the correct result is empty."
        ),
        [PG_MERGE, PG_QUERIES_WITH],
    ),
    essay(
        "dm-hard-merge-versus-upsert",
        ["PG-MERGE", "PG-DML"],
        5,
        (
            "Compare INSERT ... ON CONFLICT with MERGE in PostgreSQL 17 for a "
            "data-loading job. Address which statements can express which "
            "actions, how each treats a source that yields several rows per "
            "target key, what RETURNING offers in each, transaction and locking "
            "behaviour, and when you would choose one over the other."
        ),
        (
            "ON CONFLICT is an INSERT extension: it can skip or update a "
            "conflicting row, using a unique index as arbiter, but it cannot "
            "delete and it cannot update rows that the incoming set does not "
            "mention. MERGE can express INSERT, UPDATE and DELETE, including "
            "PostgreSQL 17's WHEN NOT MATCHED BY SOURCE for target rows absent "
            "from the source, and PostgreSQL 17 adds RETURNING with "
            "merge_action(). Both require at most one incoming row per target "
            "row; duplicates make ON CONFLICT DO UPDATE raise an error about "
            "affecting a row twice, and make MERGE raise an error when it would "
            "modify the same target row again, so the source must be "
            "deduplicated. Both run as a single statement inside the caller's "
            "transaction and take row locks on the rows they change; ON CONFLICT "
            "relies on the unique index for arbitration, while MERGE performs a "
            "join between source and target, so its plan and locking depend on "
            "that join. Choose ON CONFLICT for simple keyed upserts where only "
            "conflicting keys matter; choose MERGE when the job must also delete "
            "target rows missing from the source or apply different actions to "
            "different classes of rows in one statement."
        ),
        (
            "The answer must distinguish action coverage (upsert versus "
            "insert/update/delete), name the unique index as arbiter for ON "
            "CONFLICT, describe the single-source-row-per-target rule for both, "
            "mention PostgreSQL 17 MERGE RETURNING/NOT MATCHED BY SOURCE, and "
            "give a defensible selection rule."
        ),
        (
            "Treats the two as synonyms, or claims MERGE cannot delete. No "
            "discussion of duplicate source rows.",
            "Correct action coverage but misses the duplicate-source rule or the "
            "arbiter requirement, and the choice rule is vague.",
            "Correct actions, arbiter and duplicate rule, but RETURNING, locking "
            "or the selection guidance is incomplete.",
            "Fully correct: ON CONFLICT is an INSERT extension needing a unique "
            "arbiter and able only to skip/update conflicts; MERGE can insert, "
            "update, delete and (17+) delete unmatched target rows, with "
            "RETURNING and merge_action(); both require one source row per "
            "target row and fail on duplicates; both are single-statement, "
            "transactional and lock the changed rows; the choice rule follows "
            "from the required actions.",
        ),
        [PG_MERGE, PG_INSERT, PG_UPDATE, PG_DELETE],
    ),
]

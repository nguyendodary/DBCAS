"""SQL Foundations expansion, HARD band (levels 4-5).

Ten MCQs, two practicals and one essay target subtle DDL/DML behaviour:
MERGE in PostgreSQL 17, conflict arbitration on expression indexes, the
duplicate-row error inside ON CONFLICT, deferrable foreign keys, stored
generated columns, ALTER TYPE conversions, LIKE versus CTAS, TRUNCATE with
foreign keys and identity restart, view updatability, and NULL-tolerant
foreign keys.
"""

from lib import essay, mcq, sqlq
from sources import (
    PG_ALTER,
    PG_CONSTRAINTS,
    PG_CREATE_TABLE,
    PG_DELETE,
    PG_DROP_TABLE,
    PG_GENCOL,
    PG_IDENTITY,
    PG_INSERT,
    PG_MERGE,
    PG_TRUNCATE,
    PG_UPDATE,
    PG_VIEW,
)

QUESTIONS = [
    mcq(
        "sf-hard-merge-actions",
        ["SQL-DML-KNOW"],
        5,
        (
            "PostgreSQL 17 executes MERGE INTO stock s USING delivery d ON "
            "s.item = d.item WHEN MATCHED THEN UPDATE SET qty = s.qty + d.qty "
            "WHEN NOT MATCHED THEN INSERT (item, qty) VALUES (d.item, d.qty). "
            "What does the statement guarantee?"
        ),
        [
            "Each target row is changed at most once; matched rows are updated "
            "and unmatched source rows are inserted.",
            "A target row matched by several source rows is updated once per "
            "source row.",
            "The WHEN NOT MATCHED clause inserts only source rows that match "
            "no target row after the updates run.",
            "MERGE is not available in PostgreSQL 17 and the statement fails "
            "to parse.",
        ],
        0,
        (
            "MERGE evaluates the source against the target and applies the "
            "first matching WHEN clause per target row, so a target row is "
            "modified at most once; if several source rows match the same "
            "target row, PostgreSQL 17 raises a cardinality error instead of "
            "updating twice. WHEN NOT MATCHED refers to source rows with "
            "no target match and inserts them; the clause order does not create "
            "a second pass. MERGE was introduced in PostgreSQL 15 and extended "
            "in 17, so the statement is valid."
        ),
        [PG_MERGE, PG_INSERT],
    ),
    mcq(
        "sf-hard-on-conflict-expression-index",
        ["SQL-DML-KNOW", "SQL-DDL-KNOW"],
        4,
        (
            "Table account has UNIQUE (lower(email)) as its only unique index on "
            "email. The statement INSERT INTO account (email) VALUES ('a@x.edu') "
            "ON CONFLICT (email) DO NOTHING; is executed. What happens?"
        ),
        [
            "It fails, because ON CONFLICT (email) finds no unique index on the "
            "bare column; the conflict target must repeat the index expression "
            "exactly, as ON CONFLICT (lower(email)).",
            "It succeeds and skips the row, because PostgreSQL matches any "
            "unique index that involves email.",
            "It succeeds and inserts the row, because expression indexes are "
            "ignored by ON CONFLICT.",
            "It succeeds only when the email value has no uppercase letters.",
        ],
        0,
        (
            "Inference for ON CONFLICT (column list) looks for a unique index "
            "whose expressions match the listed expressions exactly. An index "
            "on lower(email) does not match the bare expression email, so "
            "arbiter inference fails and the statement errors. Naming the "
            "expression makes the arbiter explicit; an expression index is not "
            "a constraint, so ON CONFLICT ON CONSTRAINT cannot name it."
        ),
        [PG_INSERT, PG_CONSTRAINTS],
    ),
    mcq(
        "sf-hard-on-conflict-duplicate-source",
        ["SQL-DML-KNOW"],
        5,
        (
            "INSERT INTO account (account_id, email) SELECT account_id, email "
            "FROM staging ON CONFLICT (account_id) DO UPDATE SET email = "
            "EXCLUDED.email; is executed, and staging contains the same "
            "account_id twice. What happens?"
        ),
        [
            "The statement fails: ON CONFLICT DO UPDATE cannot affect the same "
            "row a second time within one command.",
            "The statement succeeds and the last staging row wins.",
            "The statement succeeds and the first staging row wins.",
            "The statement succeeds and both staging rows are merged into one "
            "value by concatenation.",
        ],
        0,
        (
            "ON CONFLICT DO UPDATE requires that each target row be touched at "
            "most once per statement; a duplicate key inside the incoming "
            "result set would touch the same row twice, so PostgreSQL raises an "
            "error. The fix is to deduplicate the source before the insert. "
            "There is no defined first/last winner and no automatic merging."
        ),
        [PG_INSERT],
    ),
    mcq(
        "sf-hard-deferrable-fk",
        ["SQL-DDL-KNOW"],
        4,
        (
            "Table line references header with a constraint declared DEFERRABLE "
            "INITIALLY DEFERRED. Inside one transaction, a line row is inserted "
            "before its header row. What happens?"
        ),
        [
            "Both statements succeed; the foreign key is checked at COMMIT, by "
            "which time the header exists.",
            "The line insert fails immediately, because foreign keys are always "
            "checked per statement.",
            "Both statements succeed even at COMMIT, because DEFERRABLE "
            "disables the constraint permanently.",
            "The line insert fails at COMMIT, because the header insert cannot "
            "be rolled back.",
        ],
        0,
        (
            "A constraint declared DEFERRABLE INITIALLY DEFERRED is checked at "
            "the end of the transaction rather than after each statement, so "
            "the temporarily missing header is acceptable while the header is "
            "inserted before COMMIT. It is still enforced at commit, so option "
            "C is wrong. NOT DEFERRABLE constraints, the default, are checked "
            "immediately."
        ),
        [PG_CONSTRAINTS, PG_INSERT],
    ),
    mcq(
        "sf-hard-generated-stored",
        ["SQL-DDL-KNOW"],
        4,
        (
            "Table invoice(id INT, qty INT, unit_price INT, total INT GENERATED "
            "ALWAYS AS (qty * unit_price) STORED) is created. What happens when "
            "an INSERT supplies a value for total?"
        ),
        [
            "The statement is rejected; a stored generated column is computed "
            "from the row and cannot be written directly.",
            "The supplied value is stored and the expression is ignored.",
            "The supplied value is stored, and the expression is applied only "
            "on UPDATE.",
            "The value is silently replaced by NULL.",
        ],
        0,
        (
            "A stored generated column is maintained by the database: its "
            "value is computed on insert and on every update of the referenced "
            "columns, and only DEFAULT may be written for it. Supplying a "
            "literal is an error, because the database will not accept a value "
            "it cannot verify against the expression."
        ),
        [PG_GENCOL, PG_CREATE_TABLE],
    ),
    mcq(
        "sf-hard-alter-type-using",
        ["SQL-DDL-KNOW"],
        4,
        (
            "A column amount is declared TEXT and holds numeric text. The "
            "statement ALTER TABLE sale ALTER COLUMN amount TYPE INT; fails. "
            "Which change makes the conversion explicit and correct?"
        ),
        [
            "ALTER TABLE sale ALTER COLUMN amount TYPE INT USING amount::INT;",
            "ALTER TABLE sale ALTER COLUMN amount TYPE INT DEFAULT 0;",
            "ALTER TABLE sale ALTER COLUMN amount SET DATA TYPE INT CASCADE;",
            "CREATE TABLE sale_new AS SELECT * FROM sale;",
        ],
        0,
        (
            "Without a USING clause PostgreSQL only applies an assignment cast, "
            "and TEXT to INT is not one, so the statement fails. USING defines "
            "the per-row expression that produces the new value, here an "
            "explicit cast. A DEFAULT clause does not convert existing values, "
            "CASCADE is unrelated to type conversion, and CTAS creates a new "
            "table rather than altering this one."
        ),
        [PG_ALTER],
    ),
    mcq(
        "sf-hard-create-like-including",
        ["SQL-DDL-KNOW"],
        4,
        (
            "Which statement correctly contrasts CREATE TABLE copy (LIKE sale "
            "INCLUDING ALL) with CREATE TABLE copy AS SELECT * FROM sale?"
        ),
        [
            "LIKE ... INCLUDING ALL copies the definition and its constraints "
            "and indexes but no rows; CREATE TABLE AS copies rows with inferred "
            "columns but not constraints.",
            "Both copy the rows and the constraints.",
            "LIKE ... INCLUDING ALL copies the rows; CREATE TABLE AS copies only "
            "the definition.",
            "CREATE TABLE AS copies neither rows nor column types.",
        ],
        0,
        (
            "CREATE TABLE ... LIKE produces an empty table that inherits column "
            "definitions, and INCLUDING ALL adds defaults, constraints, indexes "
            "and identity properties. CREATE TABLE AS materializes the query "
            "result, so it copies rows and column types, but it does not carry "
            "primary keys, unique constraints or foreign keys."
        ),
        [PG_CREATE_TABLE],
    ),
    mcq(
        "sf-hard-truncate-restart",
        ["SQL-DML-KNOW", "SQL-DDL-KNOW"],
        4,
        (
            "Table ticket has an identity column, and table comment references "
            "ticket(ticket_id). The statement TRUNCATE TABLE ticket RESTART "
            "IDENTITY; is executed with no other options. What happens?"
        ),
        [
            "It fails, because another table references ticket; TRUNCATE "
            "CASCADE is required to truncate the referencing table too.",
            "It succeeds and resets the identity sequence; referencing rows are "
            "deleted automatically.",
            "It succeeds but leaves the identity sequence unchanged, because "
            "TRUNCATE never affects sequences.",
            "It succeeds and truncates comment instead of ticket.",
        ],
        0,
        (
            "TRUNCATE refuses to run when another table has a foreign key to the "
            "target unless that table is included with CASCADE. RESTART "
            "IDENTITY resets owned sequences, so the option is meaningful; it "
            "is not ignored. Referencing tables are never silently modified "
            "without CASCADE."
        ),
        [PG_TRUNCATE, PG_IDENTITY],
    ),
    mcq(
        "sf-hard-updatable-view",
        ["SQL-DDL-KNOW"],
        5,
        (
            "Which view can PostgreSQL update automatically, without an INSTEAD "
            "OF trigger or rule?"
        ),
        [
            "A view over one base table whose select list contains only plain "
            "columns, with no DISTINCT, grouping or aggregate.",
            "A view whose select list contains an aggregate such as count(*) "
            "grouped by department.",
            "A view that uses UNION of two base tables.",
            "A view that selects DISTINCT city from customer.",
        ],
        0,
        (
            "A view is automatically updatable when it has exactly one base "
            "relation, no DISTINCT, GROUP BY, HAVING, set operation, aggregate "
            "or window function, and every output column maps to a base column. "
            "Aggregates, set operations and DISTINCT break the mapping, so those "
            "views need an INSTEAD OF trigger or rule to accept writes."
        ),
        [PG_VIEW, PG_UPDATE],
    ),
    mcq(
        "sf-hard-fk-match-simple",
        ["SQL-DDL-KNOW"],
        5,
        (
            "Table line(order_id INT, product_id INT, FOREIGN KEY (order_id, "
            "product_id) REFERENCES order_item(order_id, product_id)) uses the "
            "default MATCH SIMPLE. The row (NULL, 99) is inserted. What happens?"
        ),
        [
            "The row is accepted, because with MATCH SIMPLE a composite foreign "
            "key is not checked when any of its columns is NULL.",
            "The row is rejected, because product_id 99 has no matching "
            "order_item row.",
            "The row is accepted only if 99 also appears in order_item.",
            "The row is rejected, because a composite foreign key may not "
            "contain NULL.",
        ],
        0,
        (
            "MATCH SIMPLE, the default, requires the foreign key condition to "
            "hold only when all key columns are non-NULL; a single NULL "
            "disables the check for that row. MATCH FULL would reject a "
            "partially NULL key, and no automatic lookup of product_id occurs "
            "in either mode."
        ),
        [PG_CONSTRAINTS],
    ),
    sqlq(
        "sf-hard-view-join-filter",
        ["SQL-DDL-KNOW"],
        4,
        (
            "The setup creates customer(customer_id INT PRIMARY KEY, name TEXT "
            "NOT NULL) and orders(order_id INT PRIMARY KEY, customer_id INT, "
            "status TEXT, qty INT, unit_price INT), then the view "
            "open_order_value whose stored query joins orders to customer, "
            "keeps rows with status 'open', and computes line_value = qty * "
            "unit_price. Return order_id, name and line_value for every view "
            "row, ordered by order_id ascending."
        ),
        (
            "SELECT order_id, name, line_value FROM open_order_value "
            "ORDER BY order_id"
        ),
        [
            (
                "join_view_with_filter",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT "
                "NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, "
                "status TEXT, qty INT, unit_price INT);"
                "CREATE VIEW open_order_value AS SELECT o.order_id, c.name, "
                "o.qty * o.unit_price AS line_value FROM orders o JOIN "
                "customer c ON c.customer_id = o.customer_id WHERE o.status = "
                "'open';"
                "INSERT INTO customer VALUES (1,'An'),(2,'Binh');"
                "INSERT INTO orders VALUES (10,1,'open',2,50),(11,1,'closed',1,"
                "90),(12,2,'open',3,20),(13,NULL,'open',1,10);",
            ),
            (
                "no_open_orders",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT "
                "NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, "
                "status TEXT, qty INT, unit_price INT);"
                "CREATE VIEW open_order_value AS SELECT o.order_id, c.name, "
                "o.qty * o.unit_price AS line_value FROM orders o JOIN "
                "customer c ON c.customer_id = o.customer_id WHERE o.status = "
                "'open';"
                "INSERT INTO customer VALUES (1,'An');"
                "INSERT INTO orders VALUES (20,1,'closed',4,25);",
            ),
        ],
        (
            "The view's stored query is evaluated when the view is read, so the "
            "join, the status filter and the multiplication all apply at "
            "query time. Orders 10 and 12 survive with computed values 100 and "
            "60; the closed order 11 is filtered out, and order 13 disappears "
            "because its NULL customer_id matches no customer through the inner "
            "join. The dataset without open orders returns no rows."
        ),
        [PG_VIEW, PG_CONSTRAINTS],
    ),
    sqlq(
        "sf-hard-unique-null-groups",
        ["SQL-DML-KNOW", "SQL-DDL-KNOW"],
        4,
        (
            "The setup creates article(article_id INT PRIMARY KEY, code TEXT "
            "UNIQUE) using the default NULL treatment and inserts rows, "
            "including more than one row with a NULL code. Return code and "
            "copies (BIGINT) giving the number of rows stored per code, "
            "ordered by code ascending with NULL values last."
        ),
        (
            "SELECT code, count(*) AS copies FROM article "
            "GROUP BY code ORDER BY code NULLS LAST"
        ),
        [
            (
                "nulls_are_distinct",
                False,
                "CREATE TABLE article(article_id INT PRIMARY KEY, code TEXT "
                "UNIQUE);"
                "INSERT INTO article VALUES "
                "(1,'A'),(2,'A2'),(3,NULL),(4,NULL),(5,NULL);",
            ),
            (
                "no_null_codes",
                True,
                "CREATE TABLE article(article_id INT PRIMARY KEY, code TEXT "
                "UNIQUE);"
                "INSERT INTO article VALUES (1,'A'),(2,'B'),(3,'C');",
            ),
        ],
        (
            "UNIQUE compares with equality, and NULL is never equal to NULL, so "
            "all three NULL-coded rows are accepted and GROUP BY collects them "
            "into one group of three. Every non-NULL code is unique, so each "
            "has copies = 1. A UNIQUE NULLS NOT DISTINCT constraint would have "
            "rejected the second NULL insert instead."
        ),
        [PG_CONSTRAINTS, PG_INSERT],
    ),
    essay(
        "sf-hard-delete-truncate-drop",
        ["SQL-DML-KNOW", "SQL-DDL-KNOW"],
        5,
        (
            "Compare DELETE, TRUNCATE and DROP TABLE in PostgreSQL. Address (a) "
            "which rows or objects each removes, (b) filtering and WHERE, (c) "
            "transactional behaviour and rollback, (d) foreign-key dependencies "
            "and required options, (e) identity sequences and RESTART IDENTITY, "
            "and (f) the locking consequences you would weigh before running "
            "each in production."
        ),
        (
            "DELETE is DML: it removes rows that satisfy an optional WHERE "
            "clause, leaves the table, its constraints and its sequences in "
            "place, and is fully transactional, so it can be rolled back and "
            "each deleted row is logged. TRUNCATE removes every row, accepts no "
            "WHERE clause, keeps the table definition, and in PostgreSQL is "
            "transactional, though it takes an ACCESS EXCLUSIVE lock on the "
            "table and is much cheaper than row-by-row deletion. It refuses to "
            "run when a foreign key references the table unless the referencing "
            "tables are included with CASCADE, and RESTART IDENTITY resets "
            "owned sequences. DROP TABLE removes the definition and all rows and "
            "is DDL; it is transactional but requires ownership and is blocked "
            "by dependent objects unless CASCADE, which can cascade far beyond "
            "the intended target. In production, DELETE is chosen for selective "
            "removal and lets concurrent readers continue, at the cost of "
            "bloat and vacuum work; TRUNCATE is chosen for emptying a whole "
            "table but blocks other access while it runs; DROP is chosen only "
            "when the object itself is no longer needed."
        ),
        (
            "The answer must separate the three commands by scope (rows versus "
            "all rows versus object), by filtering, by transactionality, by "
            "foreign-key behaviour, by identity handling and by locking, and "
            "must connect each to an appropriate production use."
        ),
        (
            "Treats the three commands as interchangeable, or claims TRUNCATE "
            "cannot be rolled back in PostgreSQL; no mention of foreign keys or "
            "locking.",
            "Correct basic scope but confuses at least two properties, for "
            "example saying DROP can be filtered or that DELETE resets "
            "sequences. Locking is not discussed.",
            "Correct scope, filtering, transactionality and foreign-key "
            "behaviour, but identity or locking detail is missing or stated "
            "imprecisely.",
            "Fully correct: DELETE is filtered DML on rows, TRUNCATE empties the "
            "table with no WHERE and is transactional but takes a strong lock, "
            "DROP removes the object as DDL; foreign-key CASCADE requirements, "
            "RESTART IDENTITY, ownership and the production trade-offs are all "
            "stated accurately.",
        ),
        [PG_DELETE, PG_TRUNCATE, PG_DROP_TABLE, PG_CREATE_TABLE, PG_IDENTITY, PG_CONSTRAINTS],
    ),
]

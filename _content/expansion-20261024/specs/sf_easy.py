"""SQL Foundations expansion, EASY band (levels 1-2).

Eight MCQs plus two practicals close the EASY gap for assessment 4. The
practicals stay inside the sandbox rules: both references are single
read-only SELECTs over tables the setup defines, so a view's stored query
and an identity/default column can be observed directly.
"""

from lib import mcq, sqlq
from sources import (
    PG_ALTER,
    PG_CONSTRAINTS,
    PG_CREATE_TABLE,
    PG_DELETE,
    PG_IDENTITY,
    PG_INSERT,
    PG_UPDATE,
    PG_VIEW,
)

QUESTIONS = [
    mcq(
        "sf-easy-alter-add-column",
        ["SQL-DDL-KNOW"],
        2,
        (
            "A table already holds production rows and must gain a new nullable "
            "column without losing data. Which statement does this?"
        ),
        [
            "ALTER TABLE customer ADD COLUMN loyalty_code TEXT;",
            "CREATE TABLE customer ADD loyalty_code TEXT;",
            "UPDATE customer SET loyalty_code = NULL;",
            "INSERT INTO customer (loyalty_code) VALUES (NULL);",
        ],
        0,
        (
            "ALTER TABLE ... ADD COLUMN extends an existing table in place; the "
            "new column is nullable by default and existing rows receive NULL. "
            "CREATE TABLE would try to create a second table, UPDATE cannot "
            "introduce a column, and INSERT adds rows rather than columns."
        ),
        [PG_ALTER, PG_CREATE_TABLE],
    ),
    mcq(
        "sf-easy-delete-selected-rows",
        ["SQL-DML-KNOW"],
        2,
        (
            "Which statement deletes selected rows from a table while keeping "
            "the table definition and all other rows?"
        ),
        [
            "DELETE FROM customer WHERE city = 'Hue';",
            "DROP TABLE customer;",
            "ALTER TABLE customer DROP COLUMN city;",
            "TRUNCATE TABLE customer;",
        ],
        0,
        (
            "DELETE removes the rows that satisfy its WHERE clause and leaves "
            "the table structure and the remaining rows intact. DROP TABLE "
            "removes the table itself, ALTER ... DROP COLUMN removes a column "
            "from every row, and TRUNCATE empties the whole table because it "
            "does not accept a WHERE clause."
        ),
        [PG_DELETE, PG_ALTER],
    ),
    mcq(
        "sf-easy-update-expression",
        ["SQL-DML-KNOW"],
        2,
        (
            "The statement UPDATE product SET price = price * 2; is executed "
            "on a table where every row is non-NULL. What is the effect?"
        ),
        [
            "Every row's price is doubled, using each row's current value.",
            "Only the first row's price is doubled.",
            "The statement fails because a column cannot appear on both sides "
            "of the assignment.",
            "A new column named price * 2 is added to the table.",
        ],
        0,
        (
            "Without a WHERE clause the UPDATE applies to every row, and the "
            "right-hand expression is evaluated from the row's current value, "
            "so the new price is twice the old one. An UPDATE never adds "
            "columns, and referring to the column being assigned is valid."
        ),
        [PG_UPDATE],
    ),
    mcq(
        "sf-easy-primary-key-guarantees",
        ["SQL-DDL-KNOW"],
        1,
        (
            "What does a PRIMARY KEY constraint on a column guarantee?"
        ),
        [
            "Every value is non-NULL and unique, and a unique index supports "
            "the constraint.",
            "Every value is unique but NULL is allowed many times.",
            "Every value is non-NULL but duplicates are allowed.",
            "Values are sorted physically in the table.",
        ],
        0,
        (
            "A primary key combines NOT NULL with uniqueness and is backed by "
            "a unique index. Allowing repeated NULLs is the behaviour of a "
            "plain UNIQUE constraint in PostgreSQL, not of a primary key. "
            "Physical row order is never guaranteed by any constraint."
        ),
        [PG_CONSTRAINTS, PG_CREATE_TABLE],
    ),
    mcq(
        "sf-easy-insert-omitted-column",
        ["SQL-DML-KNOW"],
        2,
        (
            "Table note(note_id INT PRIMARY KEY, body TEXT, pinned BOOLEAN) "
            "has no defaults. The statement INSERT INTO note (note_id, body) "
            "VALUES (1, 'hello'); is executed. What is stored in pinned?"
        ),
        [
            "NULL, because the column is omitted from the column list and has "
            "no default.",
            "FALSE, because boolean columns default to false.",
            "An error, because every column must be listed in INSERT.",
            "An empty string, because PostgreSQL converts missing values to "
            "text.",
        ],
        0,
        (
            "Columns omitted from the INSERT column list receive their declared "
            "default; without a default the value is NULL. PostgreSQL has no "
            "implicit FALSE default for booleans, listing every column is not "
            "required, and no implicit text conversion occurs."
        ),
        [PG_INSERT],
    ),
    mcq(
        "sf-easy-drop-column",
        ["SQL-DDL-KNOW"],
        2,
        (
            "The statement ALTER TABLE customer DROP COLUMN nickname; is "
            "executed. What is the result?"
        ),
        [
            "The column and the data it held are removed; the other columns and "
            "the remaining rows stay.",
            "The column is emptied but still exists with NULL values.",
            "Only the values in the column are deleted; the column definition "
            "remains.",
            "The whole table is removed.",
        ],
        0,
        (
            "DROP COLUMN removes the column definition and its stored values "
            "from every row; the table and its other columns survive. Emptying "
            "a column without removing it is UPDATE ... SET col = NULL, not "
            "DROP COLUMN, and dropping a table is DROP TABLE."
        ),
        [PG_ALTER],
    ),
    mcq(
        "sf-easy-check-constraint",
        ["SQL-DDL-KNOW"],
        2,
        (
            "Table order_line(quantity INT) is created with the constraint "
            "CHECK (quantity > 0). What happens when an INSERT supplies "
            "quantity = 0?"
        ),
        [
            "The statement is rejected because the row violates the check "
            "constraint.",
            "The row is stored with quantity set to 1.",
            "The row is stored and a warning is logged.",
            "The row is stored with quantity set to NULL.",
        ],
        0,
        (
            "A CHECK constraint must evaluate to TRUE or NULL for every inserted "
            "or updated row; a row for which it evaluates to FALSE is rejected "
            "and the statement fails. PostgreSQL never silently repairs the "
            "value or downgrades the violation to a warning."
        ),
        [PG_CONSTRAINTS, PG_INSERT],
    ),
    mcq(
        "sf-easy-multi-row-insert",
        ["SQL-DML-KNOW"],
        1,
        (
            "Which statement inserts two rows into tag(tag_id, label) in a "
            "single command?"
        ),
        [
            "INSERT INTO tag (tag_id, label) VALUES (1, 'sql'), (2, 'db');",
            "INSERT INTO tag (tag_id, label) VALUES (1, 'sql') VALUES (2, 'db');",
            "INSERT INTO tag (tag_id, label) SELECT 1, 'sql' AND 2, 'db';",
            "INSERT INTO tag VALUES (1, 'sql'); INSERT INTO tag VALUES (2, 'db');",
        ],
        0,
        (
            "A multi-row VALUES list is the standard way to insert several rows "
            "in one statement. Repeating the VALUES keyword is a syntax error, "
            "SELECT 1, 'sql' AND 2, 'db' is not valid row construction, and the "
            "last option uses two statements rather than one command."
        ),
        [PG_INSERT],
    ),
    sqlq(
        "sf-easy-view-rows",
        ["SQL-DDL-KNOW"],
        2,
        (
            "The setup creates product(product_id INT PRIMARY KEY, name TEXT "
            "NOT NULL, price INT) and then the view cheap_product, whose "
            "stored query selects product_id, name and price from product "
            "where price < 100. Rows were inserted after the view was created. "
            "Return product_id, name and price for the rows the view exposes, "
            "ordered by product_id ascending."
        ),
        (
            "SELECT product_id, name, price FROM cheap_product "
            "ORDER BY product_id"
        ),
        [
            (
                "view_over_current_rows",
                False,
                "CREATE TABLE product(product_id INT PRIMARY KEY, name TEXT "
                "NOT NULL, price INT);"
                "CREATE VIEW cheap_product AS "
                "SELECT product_id, name, price FROM product WHERE price < 100;"
                "INSERT INTO product VALUES "
                "(1,'pen',10),(2,'desk',250),(3,'notebook',45),(4,'monitor',400);",
            ),
            (
                "view_on_empty_table",
                True,
                "CREATE TABLE product(product_id INT PRIMARY KEY, name TEXT "
                "NOT NULL, price INT);"
                "CREATE VIEW cheap_product AS "
                "SELECT product_id, name, price FROM product WHERE price < 100;",
            ),
        ],
        (
            "A view stores a query, not a copy of the data, and rows inserted "
            "after CREATE VIEW are visible when the view is queried: the view's "
            "WHERE price < 100 keeps products 1 and 3 and drops 2 and 4. The "
            "empty dataset correctly returns no rows."
        ),
        [PG_VIEW, PG_CREATE_TABLE],
    ),
    sqlq(
        "sf-easy-identity-defaults",
        ["SQL-DML-KNOW", "SQL-DDL-KNOW"],
        2,
        (
            "The setup creates ticket(ticket_id INT GENERATED ALWAYS AS "
            "IDENTITY PRIMARY KEY, subject TEXT NOT NULL, status TEXT NOT NULL "
            "DEFAULT 'open') and inserts rows, sometimes naming status and "
            "sometimes omitting it. Return ticket_id, subject and status for "
            "every row, ordered by ticket_id ascending."
        ),
        (
            "SELECT ticket_id, subject, status FROM ticket ORDER BY ticket_id"
        ),
        [
            (
                "generated_ids_and_default_status",
                False,
                "CREATE TABLE ticket(ticket_id INT GENERATED ALWAYS AS "
                "IDENTITY PRIMARY KEY, subject TEXT NOT NULL, status TEXT NOT "
                "NULL DEFAULT 'open');"
                "INSERT INTO ticket (subject) VALUES ('printer'),('vpn');",
            ),
            (
                "explicit_status_overrides_default",
                True,
                "CREATE TABLE ticket(ticket_id INT GENERATED ALWAYS AS "
                "IDENTITY PRIMARY KEY, subject TEXT NOT NULL, status TEXT NOT "
                "NULL DEFAULT 'open');"
                "INSERT INTO ticket (subject, status) VALUES "
                "('printer','open'),('vpn','closed'),('badge','closed');",
            ),
        ],
        (
            "The identity column fills ticket_id automatically, so the INSERT "
            "statements never supply it and the generated values start at 1. "
            "Omitting status applies the declared 'open' default, while an "
            "explicit value such as 'closed' is stored as given. The second "
            "dataset therefore contrasts defaulted and explicit status values."
        ),
        [PG_IDENTITY, PG_INSERT, PG_CREATE_TABLE],
    ),
]

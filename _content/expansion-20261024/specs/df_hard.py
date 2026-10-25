"""PostgreSQL Data Definition expansion, HARD band (levels 4-5).

Four MCQs restore the HARD MCQ quota and cover candidate keys, updatable
views, concurrent refresh and table inheritance; two practicals exercise a
generated column feeding an aggregate and a duplicate candidate-key audit.
"""

from lib import mcq, sqlq
from sources import (
    PG_CONSTRAINTS,
    PG_CREATE_TABLE,
    PG_GENCOL,
    PG_MATVIEW,
    PG_VIEW,
)

QUESTIONS = [
    mcq(
        "df-hard-composite-primary-key",
        ["PG-KEYS"],
        4,
        (
            "Table enrolment is created with PRIMARY KEY (student_id, "
            "course_id). Which statement is correct?"
        ),
        [
            "The pair must be unique and both columns are NOT NULL, but "
            "student_id alone may repeat for different courses.",
            "Each column is individually unique because it participates in the "
            "primary key.",
            "NULL is allowed in either column as long as the non-NULL pair is "
            "unique.",
            "The constraint is enforced only for rows inserted after the table "
            "is created, not for existing rows.",
        ],
        0,
        (
            "A primary key is a composite unique constraint plus NOT NULL on "
            "every participating column. Uniqueness applies to the combination, "
            "not to each column separately, so one student may enrol in many "
            "courses. NULLs are rejected in primary-key columns, and a "
            "constraint is part of the table definition from creation onward."
        ),
        [PG_CONSTRAINTS],
    ),
    mcq(
        "df-hard-updatable-view",
        ["PG-VIEW"],
        4,
        (
            "Which statement about automatically updatable views is correct?"
        ),
        [
            "A view over one base table without DISTINCT, GROUP BY, HAVING, "
            "LIMIT, OFFSET or set operations is auto-updatable, and WITH CHECK "
            "OPTION rejects inserts or updates that would make the row "
            "invisible through the view.",
            "Every view is auto-updatable; INSTEAD OF triggers are only an "
            "optimization.",
            "WITH CHECK OPTION validates only the data types of the affected "
            "columns, not the view's WHERE condition.",
            "A view containing GROUP BY is auto-updatable as long as the base "
            "table has a unique index.",
        ],
        0,
        (
            "PostgreSQL makes a view automatically updatable when it selects "
            "from exactly one table or updatable view and contains no "
            "DISTINCT, GROUP BY, HAVING, LIMIT, OFFSET, set operation, "
            "aggregate, window or set-returning function. WITH CHECK OPTION "
            "adds a guard: an insert or update through the view is rejected if "
            "the resulting row would not satisfy the view's own WHERE clause. "
            "Views with GROUP BY require an INSTEAD OF trigger to be modified."
        ),
        [PG_VIEW],
    ),
    mcq(
        "df-hard-refresh-concurrently",
        ["PG-MATVIEW"],
        4,
        (
            "What does REFRESH MATERIALIZED VIEW CONCURRENTLY require, and how "
            "does it differ from a plain refresh?"
        ),
        [
            "It requires a unique index on the materialized view and keeps the "
            "view readable while refreshing, whereas a plain refresh blocks "
            "readers.",
            "It requires no additional objects and updates only the rows whose "
            "base data changed since the last refresh.",
            "It requires a primary key on the base table and blocks readers "
            "until the new contents are swapped in.",
            "It requires the materialized view to be created WITH NO DATA, "
            "because the unique index is built during the first refresh.",
        ],
        0,
        (
            "REFRESH MATERIALIZED VIEW CONCURRENTLY compares the old and new "
            "contents, so it needs a unique index that covers every row of the "
            "materialized view, and it allows concurrent reads while it runs. "
            "The plain form takes an exclusive lock that blocks readers. "
            "Neither form performs incremental updates: the defining query is "
            "re-executed in full. The view must already be populated, so a "
            "view created WITH NO DATA cannot be refreshed concurrently before "
            "its first normal refresh."
        ),
        [PG_MATVIEW],
    ),
    mcq(
        "df-hard-table-inheritance",
        ["PG-TABLE"],
        4,
        (
            "When a child table is created with INHERITS (parent), which "
            "statement is correct?"
        ),
        [
            "It inherits the parent's columns and CHECK/NOT NULL constraints, "
            "but not its indexes, primary key, unique constraints or foreign "
            "keys, and a query on the parent includes child rows unless ONLY "
            "is used.",
            "It inherits all indexes, primary keys and foreign keys, so the "
            "parent's constraints also protect child rows.",
            "A query on the parent returns only parent rows; child rows appear "
            "only when the child table is named explicitly.",
            "The child must redeclare every parent column, because inheritance "
            "only shares physical storage between the tables.",
        ],
        0,
        (
            "Table inheritance copies column definitions and check/not-null "
            "constraints into the child, but indexes, primary keys, unique "
            "constraints and foreign keys are not inherited. By default a "
            "SELECT on the parent includes rows from descendant tables; ONLY "
            "parent restricts it to the parent. Each table stores its own rows; "
            "there is no shared storage."
        ),
        [PG_CREATE_TABLE],
    ),
    sqlq(
        "df-hard-generated-revenue",
        ["PG-GENCOL"],
        4,
        (
            "The setup creates sale(sale_id INT PRIMARY KEY, region TEXT NOT "
            "NULL, unit_price NUMERIC(8,2) NOT NULL, qty INT NOT NULL, net "
            "NUMERIC(10,2) GENERATED ALWAYS AS (unit_price * qty) STORED). "
            "Return region and sum(net) aliased revenue for every region, "
            "ordered by region ascending."
        ),
        (
            "SELECT region, sum(net) AS revenue FROM sale "
            "GROUP BY region ORDER BY region"
        ),
        [
            (
                "two_regions",
                False,
                "CREATE TABLE sale(sale_id INT PRIMARY KEY, region TEXT NOT "
                "NULL, unit_price NUMERIC(8,2) NOT NULL, qty INT NOT NULL, net "
                "NUMERIC(10,2) GENERATED ALWAYS AS (unit_price * qty) STORED);"
                "INSERT INTO sale(sale_id, region, unit_price, qty) VALUES "
                "(1,'north',10.00,2),(2,'north',5.00,3),"
                "(3,'south',8.00,4),(4,'south',2.50,2);",
            ),
            (
                "no_sales",
                True,
                "CREATE TABLE sale(sale_id INT PRIMARY KEY, region TEXT NOT "
                "NULL, unit_price NUMERIC(8,2) NOT NULL, qty INT NOT NULL, net "
                "NUMERIC(10,2) GENERATED ALWAYS AS (unit_price * qty) STORED);",
            ),
        ],
        (
            "Each row stores its generated net value: 20, 15, 32 and 5. "
            "Grouping by region sums those stored values to 35 for north and 37 "
            "for south, in region order. The empty dataset produces no groups, "
            "so the aggregate query correctly returns no rows rather than a "
            "single NULL row."
        ),
        [PG_GENCOL],
    ),
    sqlq(
        "df-hard-duplicate-candidate-key",
        ["PG-KEYS"],
        4,
        (
            "The setup creates payment(payment_id INT PRIMARY KEY, customer_id "
            "INT NOT NULL, paid_on DATE NOT NULL, amount NUMERIC(8,2) NOT "
            "NULL). The pair (customer_id, paid_on) is being considered as a "
            "candidate key. Return customer_id, paid_on and count(*) aliased "
            "payments for every pair that occurs more than once, ordered by "
            "customer_id then paid_on ascending."
        ),
        (
            "SELECT customer_id, paid_on, count(*) AS payments FROM payment "
            "GROUP BY customer_id, paid_on HAVING count(*) > 1 "
            "ORDER BY customer_id, paid_on"
        ),
        [
            (
                "repeated_pairs",
                False,
                "CREATE TABLE payment(payment_id INT PRIMARY KEY, customer_id "
                "INT NOT NULL, paid_on DATE NOT NULL, amount NUMERIC(8,2) NOT "
                "NULL);"
                "INSERT INTO payment VALUES "
                "(1,1,'2024-01-05',10.00),(2,1,'2024-01-05',25.00),"
                "(3,2,'2024-01-05',5.00),(4,2,'2024-01-06',7.00),"
                "(5,1,'2024-01-05',3.00);",
            ),
            (
                "already_unique",
                True,
                "CREATE TABLE payment(payment_id INT PRIMARY KEY, customer_id "
                "INT NOT NULL, paid_on DATE NOT NULL, amount NUMERIC(8,2) NOT "
                "NULL);"
                "INSERT INTO payment VALUES "
                "(1,1,'2024-01-05',10.00),(2,1,'2024-01-06',25.00),"
                "(3,2,'2024-01-05',5.00);",
            ),
        ],
        (
            "A candidate key must be unique, so the audit groups by the proposed "
            "key columns and keeps only groups with more than one row. Customer "
            "1 has three payments on 2024-01-05 and therefore cannot be identified "
            "by (customer_id, paid_on) alone; the result reports that pair with "
            "a count of 3. In the edge dataset every pair is unique, so HAVING "
            "removes all groups and the result is empty."
        ),
        [PG_CONSTRAINTS],
    ),
]

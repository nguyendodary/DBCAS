"""PostgreSQL Data Definition expansion, MEDIUM band (level 3).

Two read-only practicals close the SQL quota: one aggregates a stored
generated column, the other queries an aggregate view that joins two tables.
"""

from lib import sqlq
from sources import PG_GENCOL, PG_VIEW

QUESTIONS = [
    sqlq(
        "df-medium-generated-subtotal",
        ["PG-GENCOL"],
        3,
        (
            "The setup creates invoice(invoice_id INT PRIMARY KEY, unit_price "
            "NUMERIC(8,2) NOT NULL, qty INT NOT NULL, discount NUMERIC(8,2), "
            "subtotal NUMERIC(10,2) GENERATED ALWAYS AS (unit_price * qty - "
            "discount) STORED). Return invoice_id and subtotal for every "
            "invoice whose stored subtotal is at least 10, ordered by "
            "invoice_id ascending. Rows whose subtotal is NULL must not appear."
        ),
        (
            "SELECT invoice_id, subtotal FROM invoice "
            "WHERE subtotal >= 10 ORDER BY invoice_id"
        ),
        [
            (
                "mixed_discounts",
                False,
                "CREATE TABLE invoice(invoice_id INT PRIMARY KEY, unit_price "
                "NUMERIC(8,2) NOT NULL, qty INT NOT NULL, discount NUMERIC(8,2), "
                "subtotal NUMERIC(10,2) GENERATED ALWAYS AS (unit_price * qty - "
                "discount) STORED);"
                "INSERT INTO invoice(invoice_id, unit_price, qty, discount) "
                "VALUES (1,10.00,2,5.00),(2,4.00,5,NULL),(3,2.00,4,0),"
                "(4,3.00,6,2.00);",
            ),
            (
                "all_subtotals_null",
                True,
                "CREATE TABLE invoice(invoice_id INT PRIMARY KEY, unit_price "
                "NUMERIC(8,2) NOT NULL, qty INT NOT NULL, discount NUMERIC(8,2), "
                "subtotal NUMERIC(10,2) GENERATED ALWAYS AS (unit_price * qty - "
                "discount) STORED);"
                "INSERT INTO invoice(invoice_id, unit_price, qty, discount) "
                "VALUES (1,5.00,3,NULL),(2,2.00,4,NULL);",
            ),
        ],
        (
            "subtotal is a stored generated column, so the predicate can "
            "reference it directly; the database computed it from the base "
            "columns. Invoice 1 stores 15.00 and invoice 4 stores 16.00, so "
            "both qualify; invoice 3 stores 8.00 and is filtered out. Invoice 2 "
            "and every edge row have a NULL discount, which makes the "
            "subtraction NULL, and NULL >= 10 is unknown, so those rows are "
            "excluded rather than returned."
        ),
        [PG_GENCOL],
    ),
    sqlq(
        "df-medium-order-total-view",
        ["PG-VIEW"],
        3,
        (
            "The setup creates orders, order_line and the view order_total, "
            "whose stored query groups order_line by order and sums qty * "
            "unit_price as total. Return order_id and total for every order "
            "whose total is at least 20, ordered by order_id ascending."
        ),
        (
            "SELECT order_id, total FROM order_total "
            "WHERE total >= 20 ORDER BY order_id"
        ),
        [
            (
                "orders_above_threshold",
                False,
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT "
                "NOT NULL);"
                "CREATE TABLE order_line(order_id INT NOT NULL, qty INT NOT "
                "NULL, unit_price NUMERIC(8,2) NOT NULL);"
                "INSERT INTO orders VALUES (1,10),(2,10),(3,11);"
                "INSERT INTO order_line VALUES "
                "(1,2,10.00),(2,1,5.00),(2,1,10.00),(3,4,6.00);"
                "CREATE VIEW order_total AS SELECT o.order_id, sum(l.qty * "
                "l.unit_price) AS total FROM orders o JOIN order_line l ON "
                "l.order_id = o.order_id GROUP BY o.order_id;",
            ),
            (
                "view_over_empty_lines",
                True,
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT "
                "NOT NULL);"
                "CREATE TABLE order_line(order_id INT NOT NULL, qty INT NOT "
                "NULL, unit_price NUMERIC(8,2) NOT NULL);"
                "INSERT INTO orders VALUES (1,10);"
                "CREATE VIEW order_total AS SELECT o.order_id, sum(l.qty * "
                "l.unit_price) AS total FROM orders o JOIN order_line l ON "
                "l.order_id = o.order_id GROUP BY o.order_id;",
            ),
        ],
        (
            "The view stores an aggregate query, so querying it returns one row "
            "per order with the computed total. Order 1 totals 20.00 and order "
            "3 totals 24.00, while order 2 totals 15.00 and is removed by the "
            "WHERE clause on total. In the edge dataset order_line is empty, so "
            "the inner join produces no groups and the view returns no rows. "
            "Filtering on total is valid because total is an output column of "
            "the view."
        ),
        [PG_VIEW],
    ),
]

"""SQL Querying expansion, MEDIUM band (level 3).

Ten MCQs cover all six SQL-* concepts; four double as assessment-2
SELECT/JOIN items. Two SQL practicals and two essays likewise serve both
scopes, so assessment 2's MEDIUM selection becomes feasible from the same
reviewed inventory.
"""

from lib import essay, mcq, sqlq
from sources import (
    PG_AGGREGATE,
    PG_COMPARISON,
    PG_EXPRESSIONS,
    PG_JOIN_TUTORIAL,
    PG_SELECT,
    PG_SUBQUERY_FUNCTIONS,
    PG_TABLE_EXPRESSIONS,
)

QUESTIONS = [
    mcq(
        "sq-medium-alias-visibility",
        ["SQL-SELECT", "SELECT"],
        3,
        (
            "Which statement about an output alias introduced in the SELECT "
            "list is correct in PostgreSQL?"
        ),
        [
            "The alias can be used in WHERE because WHERE is evaluated after "
            "SELECT.",
            "The alias can be used in ORDER BY but not in WHERE, because WHERE "
            "is evaluated before the SELECT list.",
            "The alias is visible in every clause, including HAVING and WHERE.",
            "The alias replaces the input column, so the original column is no "
            "longer accessible anywhere.",
        ],
        1,
        (
            "Logical evaluation reaches WHERE before SELECT computes output "
            "expressions, so the alias does not exist yet. ORDER BY runs after "
            "SELECT and may refer to an output name. HAVING runs before SELECT "
            "as well, so aliases are not generally available there. An alias "
            "changes only the output name; input columns remain accessible by "
            "their own names."
        ),
        [PG_SELECT],
    ),
    mcq(
        "sq-medium-not-in-null",
        ["SQL-SUBQUERY", "SQL-WHERE"],
        3,
        (
            "Table orders has a nullable customer_id, and the subquery SELECT "
            "customer_id FROM orders currently returns at least one NULL. Which "
            "query reliably returns customers that have no orders?"
        ),
        [
            "SELECT id FROM customer WHERE id NOT IN (SELECT customer_id FROM "
            "orders);",
            "SELECT c.id FROM customer c WHERE NOT EXISTS (SELECT 1 FROM orders "
            "o WHERE o.customer_id = c.id);",
            "SELECT id FROM customer WHERE id <> ALL (SELECT customer_id FROM "
            "orders);",
            "SELECT id FROM customer WHERE NOT id IN (SELECT customer_id FROM "
            "orders);",
        ],
        1,
        (
            "NOT IN is equivalent to a chain of <> comparisons. Comparing any "
            "value with NULL yields UNKNOWN, so a NULL in the subquery makes "
            "the predicate UNKNOWN for every customer and the query returns no "
            "rows. NOT EXISTS tests the absence of a matching row and is "
            "unaffected by NULL values. Option C has the same NULL sensitivity, "
            "and option D applies NOT to the same IN test, so it is also "
            "NULL-sensitive and returns no rows when the subquery yields NULL."
        ),
        [PG_SUBQUERY_FUNCTIONS, PG_COMPARISON],
    ),
    mcq(
        "sq-medium-left-join-filter",
        ["SQL-JOIN", "JOIN"],
        3,
        (
            "Which query returns only customers that have at least one order, "
            "although it is written with a LEFT JOIN?"
        ),
        [
            "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = "
            "c.id WHERE o.customer_id IS NOT NULL;",
            "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = "
            "c.id WHERE o.customer_id IS NULL;",
            "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = "
            "c.id HAVING count(*) > 0;",
            "SELECT c.id FROM customer c LEFT JOIN orders o ON o.customer_id = "
            "c.id AND o.amount > 0;",
        ],
        0,
        (
            "A LEFT JOIN emits NULL-extended rows for unmatched customers. "
            "Filtering o.customer_id IS NOT NULL afterwards removes those rows, "
            "leaving only customers with at least one match. IS NULL is the "
            "anti-join and returns the opposite set. HAVING without GROUP BY "
            "does not filter per customer. Moving the condition into ON only "
            "restricts which orders match and still keeps unmatched customers."
        ),
        [PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-medium-count-null",
        ["SQL-GROUP", "SQL-SELECT"],
        3,
        (
            "Table customer has a nullable email column. What does SELECT "
            "count(*), count(email) FROM customer return?"
        ),
        [
            "Two equal counts, because count ignores NULL in both forms.",
            "count(*) counts all rows, while count(email) counts only rows where "
            "email is not NULL.",
            "count(email) counts all rows, while count(*) counts only non-NULL "
            "emails.",
            "The query raises an error because an aggregate without GROUP BY "
            "cannot mix the two forms.",
        ],
        1,
        (
            "count(*) counts rows. count(expression) counts non-NULL values of "
            "that expression, so the two numbers can differ. The forms can be "
            "combined in one aggregate query without GROUP BY, which then "
            "produces exactly one row."
        ),
        [PG_AGGREGATE],
    ),
    mcq(
        "sq-medium-where-having-order",
        ["SQL-HAVING", "SQL-WHERE"],
        3,
        (
            "Consider SELECT dept_id FROM emp WHERE salary > 1000 GROUP BY "
            "dept_id HAVING count(*) >= 2. What does the query return?"
        ),
        [
            "Departments with at least two employees whose salary is greater "
            "than 1000.",
            "All departments with at least two employees, regardless of salary.",
            "Departments whose total salary is greater than 1000.",
            "Individual employees who earn more than 1000 and appear at least "
            "twice.",
        ],
        0,
        (
            "WHERE removes employees with salary <= 1000 or NULL salary before "
            "grouping. GROUP BY then forms departments from the surviving rows, "
            "and HAVING keeps departments whose surviving row count is at least "
            "two. The filter is per employee before grouping, not a sum, and "
            "the result has one row per qualifying department."
        ),
        [PG_SELECT, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-medium-group-functional-dependency",
        ["SQL-GROUP", "SQL-SELECT"],
        3,
        (
            "Table dept has dept_id as its primary key and a dept_name column. "
            "Why does PostgreSQL accept SELECT d.dept_id, d.dept_name, count(*) "
            "FROM dept d JOIN emp e ON e.dept_id = d.dept_id GROUP BY d.dept_id?"
        ),
        [
            "Because dept_name is functionally dependent on the grouped primary "
            "key dept_id; ungrouped columns are otherwise rejected.",
            "Because PostgreSQL always allows ungrouped columns and chooses an "
            "arbitrary value for them.",
            "Because dept_name is implicitly added to the GROUP BY list by the "
            "planner.",
            "It is not accepted; every selected column must appear in GROUP BY.",
        ],
        0,
        (
            "PostgreSQL permits an ungrouped column when it is functionally "
            "dependent on the grouped columns, and a primary key determines the "
            "other columns of its table. The join does not break that "
            "dependency because dept_name comes from dept. Without such a "
            "dependency, each group could contain several dept_name values and "
            "PostgreSQL rejects the query instead of inventing an answer."
        ),
        [PG_SELECT, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-medium-join-fanout-sum",
        ["SQL-JOIN", "JOIN"],
        3,
        (
            "Each order has three rows in orders and two rows in items per "
            "order. The query SELECT sum(o.amount) FROM orders o JOIN items i ON "
            "i.order_id = o.order_id returns a total much larger than the sum of "
            "order amounts. Why?"
        ),
        [
            "SUM counts duplicate values automatically, so every order amount is "
            "counted twice.",
            "The join emits one row per order-item pair, so each order amount is "
            "repeated once per item and summed repeatedly.",
            "NULL amounts are treated as zero, which increases the total.",
            "The join removes rows that have no items, which inflates the average "
            "but not a sum.",
        ],
        1,
        (
            "A one-to-many join multiplies each order row by its number of item "
            "rows. SUM has no DISTINCT here, so the repeated amount contributes "
            "once per joined row. The repair is to aggregate items first or sum "
            "the order amounts in a separate subquery. SUM does not deduplicate "
            "on its own, NULLs are ignored rather than converted to zero, and "
            "removing rows cannot increase a sum of non-negative amounts."
        ),
        [PG_JOIN_TUTORIAL, PG_AGGREGATE],
    ),
    mcq(
        "sq-medium-select-computed-column",
        ["SQL-SELECT", "SELECT"],
        3,
        (
            "Which select-list expression returns one row per sale with the "
            "original id and a computed column labelled gross, equal to amount "
            "multiplied by 1.1?"
        ),
        [
            "SELECT id, amount * 1.1 AS gross FROM sales;",
            "SELECT id, gross = amount * 1.1 FROM sales;",
            "SELECT id, amount * 1.1 FROM sales AS gross;",
            "SELECT id AS gross, amount * 1.1 FROM sales;",
        ],
        0,
        (
            "AS labels the computed expression gross without changing the row "
            "count. Option B is a boolean comparison with an undefined "
            "identifier; option C aliases the table rather than the output "
            "column and leaves the computed column unnamed; option D puts the "
            "gross label on id."
        ),
        [PG_SELECT],
    ),
    mcq(
        "sq-medium-where-null-exclusion",
        ["SQL-WHERE"],
        3,
        (
            "Column status is nullable. Which rows does WHERE status <> "
            "'cancelled' return?"
        ),
        [
            "Rows whose status is any value except 'cancelled', including NULL "
            "rows.",
            "Only rows whose status is a non-NULL value different from "
            "'cancelled'; NULL rows are excluded because the comparison is "
            "UNKNOWN.",
            "All rows, because NULL is treated as an empty string.",
            "The query fails because <> cannot be used with a nullable column.",
        ],
        1,
        (
            "In three-valued logic, NULL <> 'cancelled' evaluates to UNKNOWN, "
            "and WHERE keeps only TRUE. Rows with status NULL are therefore "
            "dropped. To include them, test status IS NULL OR status <> "
            "'cancelled', or use IS DISTINCT FROM, which treats NULL as a "
            "comparable value. NULL is not an empty string."
        ),
        [PG_COMPARISON, PG_SELECT],
    ),
    mcq(
        "sq-medium-scalar-subquery-multirow",
        ["SQL-SUBQUERY", "SQL-SELECT"],
        3,
        (
            "A scalar subquery appears in the SELECT list. What happens if that "
            "subquery returns more than one row at execution time?"
        ),
        [
            "PostgreSQL returns the first row and ignores the rest.",
            "PostgreSQL raises an error because a scalar subquery must return at "
            "most one row.",
            "PostgreSQL returns NULL for the extra rows.",
            "PostgreSQL automatically aggregates the rows into one value.",
        ],
        1,
        (
            "A scalar subquery is used where a single value is expected. Zero "
            "rows yield NULL, but more than one row is an error ('more than one "
            "row returned by a subquery used as an expression'). PostgreSQL does "
            "not silently choose a row or aggregate; the query must guarantee "
            "cardinality with an aggregate, LIMIT 1, or a correlated condition."
        ),
        [PG_EXPRESSIONS, PG_SUBQUERY_FUNCTIONS],
    ),
    sqlq(
        "sq-medium-customer-order-count",
        ["SQL-SELECT", "SELECT", "SQL-GROUP"],
        3,
        (
            "Table customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) and "
            "table orders(order_id INT PRIMARY KEY, customer_id INT, amount "
            "NUMERIC(10,2)). Return customer_id, name and order_count (BIGINT) "
            "for every customer, including customers with no orders. Order by "
            "order_count descending, then customer_id ascending."
        ),
        (
            "SELECT c.customer_id, c.name, count(o.order_id) AS order_count "
            "FROM customer c LEFT JOIN orders o ON o.customer_id = c.customer_id "
            "GROUP BY c.customer_id, c.name "
            "ORDER BY order_count DESC, c.customer_id"
        ),
        [
            (
                "customers_with_and_without_orders",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2));"
                "INSERT INTO customer VALUES (1,'An'),(2,'Binh'),(3,'Chi');"
                "INSERT INTO orders VALUES (10,1,5.00),(11,1,7.00),(12,3,9.00);",
            ),
            (
                "no_orders",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2));"
                "INSERT INTO customer VALUES (1,'An'),(2,'Binh');",
            ),
        ],
        (
            "The LEFT JOIN keeps customers without orders, and counting "
            "o.order_id rather than * turns the join's NULL placeholder into 0. "
            "Grouping by customer_id and name keeps the selected name valid. "
            "ORDER BY may use the output alias order_count; the tie-breaker on "
            "customer_id makes the result deterministic."
        ),
        [PG_SELECT, PG_AGGREGATE, PG_JOIN_TUTORIAL],
    ),
    sqlq(
        "sq-medium-order-customer-flag",
        ["SQL-JOIN", "JOIN"],
        3,
        (
            "Table customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) and "
            "table orders(order_id INT PRIMARY KEY, customer_id INT). Return "
            "order_id (INT), name (TEXT) and has_customer (BOOLEAN) for every "
            "order. Orders with a customer_id that matches no customer are "
            "returned with NULL name and has_customer false; NULL customer_id "
            "is treated the same way. Order by order_id ascending."
        ),
        (
            "SELECT o.order_id, c.name, (c.customer_id IS NOT NULL) AS "
            "has_customer FROM orders o LEFT JOIN customer c ON "
            "c.customer_id = o.customer_id ORDER BY o.order_id"
        ),
        [
            (
                "orphan_and_null_keys",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT);"
                "INSERT INTO customer VALUES (1,'An'),(2,'Binh');"
                "INSERT INTO orders VALUES (10,1),(11,99),(12,NULL);",
            ),
            (
                "no_orders",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT);"
                "INSERT INTO customer VALUES (1,'An');",
            ),
        ],
        (
            "The LEFT JOIN preserves every order. c.customer_id IS NOT NULL is "
            "FALSE for both an orphan key and a NULL key, so the boolean flag "
            "distinguishes matched from unmatched orders without converting "
            "NULL to text. The edge dataset has no orders and correctly "
            "returns no rows."
        ),
        [PG_JOIN_TUTORIAL, PG_COMPARISON],
    ),
    essay(
        "sq-medium-result-bag-join",
        ["SQL-SELECT", "SELECT", "SQL-JOIN", "JOIN"],
        3,
        (
            "Explain how a SELECT statement that joins two tables and applies "
            "WHERE produces its result. Cover the select list, row filtering, "
            "bag semantics and duplicate multiplication. Give an example in "
            "which a one-to-many join changes the number of rows and explain "
            "when DISTINCT or pre-aggregation is the appropriate correction."
        ),
        (
            "FROM builds the joined table, applying the ON condition to form "
            "pairs. WHERE then keeps rows for which the predicate is TRUE. The "
            "SELECT list evaluates expressions for each surviving row and labels "
            "them. SQL tables are bags: a left row matching three right rows "
            "produces three output rows, and no automatic deduplication occurs. "
            "If a customer has three orders, joining customer to orders yields "
            "three rows for that customer. SELECT DISTINCT removes duplicate "
            "whole result rows, which is appropriate when the question asks for "
            "distinct entities and the selected columns uniquely identify them. "
            "When the goal is one row per customer with an aggregate, "
            "pre-aggregating orders in a subquery and then joining is safer than "
            "DISTINCT, because DISTINCT would not repair an incorrect SUM "
            "inflated by fan-out."
        ),
        (
            "The essential points are logical clause order, bag semantics, "
            "one-to-many row multiplication, and the distinction between "
            "DISTINCT as duplicate-row removal and pre-aggregation as a way to "
            "fix incorrect aggregates."
        ),
        (
            "Treats SQL results as sets with automatic deduplication, or cannot "
            "explain where rows are filtered; no example of row multiplication.",
            "Describes FROM/WHERE/SELECT but claims joins remove duplicates, or "
            "suggests DISTINCT as a universal fix for inflated aggregates.",
            "Correct logical order and bag semantics; gives an example, but the "
            "guidance on DISTINCT versus pre-aggregation is partial.",
            "Correctly explains FROM/ON, WHERE, SELECT, bag semantics and "
            "one-to-many fan-out with a concrete example; distinguishes DISTINCT "
            "(duplicate whole rows) from pre-aggregation (correct per-entity "
            "totals) and chooses the right tool for each goal.",
        ),
        [PG_SELECT, PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
    ),
    essay(
        "sq-medium-join-aggregate-null",
        ["SQL-JOIN", "JOIN", "SQL-GROUP"],
        3,
        (
            "Explain how INNER JOIN and LEFT JOIN affect count and sum "
            "aggregates. Address unmatched rows, NULL amounts, count(*) versus "
            "count(column), and row multiplication when the joined table has "
            "several matches. Give the rule you would use to count customers "
            "with zero orders correctly."
        ),
        (
            "INNER JOIN keeps only matching pairs, so customers without orders "
            "disappear and cannot be counted as zero. LEFT JOIN keeps every "
            "left row and NULL-extends the right columns. count(*) counts the "
            "NULL-extended row as one, which is wrong for counting orders; "
            "count(o.order_id) counts only non-NULL matched keys and yields 0 "
            "for unmatched customers. sum ignores NULL amounts, so an unmatched "
            "customer or an order with NULL amount contributes nothing, which "
            "may be the desired numeric total but must be documented. If the "
            "right table has several matches per left row, each left row is "
            "repeated and count(*)/sum can be inflated; pre-aggregate the many "
            "side to one row per key before joining, or count distinct keys. "
            "For customers with zero orders: LEFT JOIN orders, GROUP BY "
            "customer key, and use count(o.order_id)."
        ),
        (
            "The correct rule combines LEFT JOIN, grouping by customer, and "
            "count(o.order_id); count(*) after a LEFT JOIN counts the "
            "placeholder row and reports one instead of zero."
        ),
        (
            "Uses INNER JOIN for zero-order customers or count(*) after a LEFT "
            "JOIN; does not discuss NULL aggregates or fan-out.",
            "Knows LEFT JOIN preserves customers but mixes count(*) and "
            "count(column), or ignores row multiplication.",
            "Correct treatment of NULLs and count(column), but the fan-out "
            "discussion or the final counting rule is incomplete.",
            "Explains INNER versus LEFT preservation, NULL extension, count(*) "
            "versus count(column), sum's NULL behavior, one-to-many fan-out and "
            "pre-aggregation; states the zero-order rule as LEFT JOIN plus "
            "count(o.order_id) grouped by customer.",
        ),
        [PG_JOIN_TUTORIAL, PG_AGGREGATE],
    ),
]

"""SQL Querying expansion, HARD band (levels 4-5).

Ten MCQs, one practical and one essay cover all six SQL-* concepts with
Level-4/5 reasoning: three-valued logic, grouping sets and the GROUPING
function, window-function tie behaviour, LATERAL, aggregate FILTER, and
semi-join duplicate semantics. The practical derives its expected rows by
executing a DISTINCT ON reference through the sandbox.
"""

from lib import essay, mcq, sqlq
from sources import (
    PG_AGGREGATE,
    PG_AGGREGATE_EXPRESSIONS,
    PG_COMPARISON,
    PG_FUNCTIONS_WINDOW,
    PG_JOIN_TUTORIAL,
    PG_SELECT,
    PG_SUBQUERY_FUNCTIONS,
    PG_TABLE_EXPRESSIONS,
)

QUESTIONS = [
    mcq(
        "sq-hard-distinct-on",
        ["SQL-SELECT", "SQL-GROUP"],
        4,
        (
            "Both statements below intend to return one row per region. Which "
            "statement about them is correct?\n"
            "(1) SELECT DISTINCT ON (region_id) region_id, sale_id, amount "
            "FROM sale ORDER BY region_id, amount DESC;\n"
            "(2) SELECT DISTINCT region_id, sale_id FROM sale;"
        ),
        [
            "Statement 1 returns the highest-amount sale per region because "
            "DISTINCT ON keeps the first row of each region in ORDER BY order; "
            "statement 2 returns one row per distinct (region_id, sale_id) "
            "pair, so it does not collapse to one row per region.",
            "Statement 1 fails, because DISTINCT ON requires the DISTINCT ON "
            "expression to appear in the SELECT list twice.",
            "Statement 2 returns one row per region because DISTINCT removes "
            "all non-key columns automatically.",
            "Both statements return the same rows, because DISTINCT ON and "
            "DISTINCT are equivalent when the first ORDER BY key is the "
            "DISTINCT ON argument.",
        ],
        0,
        (
            "DISTINCT ON keeps the first row of each group of rows that share "
            "the DISTINCT ON expressions, where 'first' is defined by the "
            "query's ORDER BY, which must begin with those expressions. "
            "DISTINCT, by contrast, compares entire output rows, so "
            "(region_id, sale_id) pairs are deduplicated, not regions. "
            "DISTINCT ON does not require the expression to appear twice, and "
            "it is not equivalent to DISTINCT."
        ),
        [PG_SELECT],
    ),
    mcq(
        "sq-hard-not-predicate-null",
        ["SQL-WHERE"],
        4,
        (
            "Table t(x INT) holds the rows 1, 2 and NULL. The statement "
            "SELECT x FROM t WHERE NOT (x > 5) is executed. Which result set "
            "does PostgreSQL return?"
        ),
        [
            "The rows 1 and 2, plus the NULL row, because NOT turns the "
            "unknown comparison into true.",
            "The rows 1 and 2 only; the NULL row is excluded because "
            "NOT (UNKNOWN) is still UNKNOWN and WHERE keeps only TRUE.",
            "No rows at all, because a NULL value makes the whole predicate "
            "invalid.",
            "The NULL row only, because NOT (x > 5) is true whenever x is "
            "NULL.",
        ],
        1,
        (
            "Comparing NULL with 5 yields UNKNOWN. NOT UNKNOWN is UNKNOWN, "
            "not TRUE, so WHERE discards the NULL row. Rows 1 and 2 both "
            "satisfy NOT (x > 5) because 1 > 5 and 2 > 5 are FALSE and NOT "
            "FALSE is TRUE. The common mistake is to read NOT (x > 5) as "
            "x <= 5, which would include NULL under an invalid two-valued "
            "reading."
        ),
        [PG_COMPARISON, PG_SELECT],
    ),
    mcq(
        "sq-hard-full-join-symmetric",
        ["SQL-JOIN"],
        4,
        (
            "Tables a(id) and b(id) have no NULL ids. Which query returns "
            "exactly the ids that appear in one table but not the other?"
        ),
        [
            "SELECT id FROM a FULL JOIN b USING (id) "
            "WHERE a.id IS NULL OR b.id IS NULL;",
            "SELECT id FROM a FULL JOIN b USING (id) "
            "WHERE a.id IS NOT NULL AND b.id IS NOT NULL;",
            "SELECT id FROM a INNER JOIN b USING (id);",
            "SELECT id FROM a CROSS JOIN b WHERE a.id = b.id;",
        ],
        0,
        (
            "A FULL JOIN emits matched rows plus one NULL-extended row for "
            "each unmatched row on either side. After USING (id) the join "
            "column is merged, but a.id and b.id still reveal which side was "
            "NULL-extended. Keeping rows where exactly one side is NULL "
            "therefore returns the symmetric difference. Option B keeps only "
            "matched rows, and options C and D are inner joins."
        ),
        [PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-hard-grouping-sets",
        ["SQL-GROUP"],
        5,
        (
            "The statement SELECT region_id, count(*) AS n FROM sale GROUP BY "
            "GROUPING SETS ((region_id), ()) ORDER BY region_id NULLS LAST is "
            "executed on a non-empty table. What does it return?"
        ),
        [
            "One row per distinct region_id plus one grand-total row whose "
            "region_id is NULL.",
            "One row per distinct region_id only, because an empty grouping "
            "set contributes no rows.",
            "One row per row of sale, because grouping sets disable "
            "aggregation.",
            "An error, because GROUP BY accepts only a column list, never "
            "grouping sets.",
        ],
        0,
        (
            "A grouping set is the set of columns a single aggregate pass "
            "groups by. GROUPING SETS ((region_id), ()) runs two passes: one "
            "grouped by region_id and one over the whole table. The grand "
            "total therefore appears as an extra row, and columns that are "
            "not part of that grouping set are reported as NULL. The empty "
            "set is meaningful, not ignored, and GROUP BY does accept grouping "
            "sets in PostgreSQL."
        ),
        [PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-hard-having-without-group",
        ["SQL-HAVING"],
        4,
        (
            "The table sale is currently empty. The statement SELECT count(*) "
            "AS n FROM sale HAVING count(*) > 0 is executed. What is the "
            "result?"
        ),
        [
            "One row containing the value 0.",
            "No rows, because without GROUP BY the whole table forms one group "
            "and HAVING rejects that group when its condition is not true.",
            "One row containing NULL.",
            "A syntax error, because HAVING requires a GROUP BY clause.",
        ],
        1,
        (
            "When a query has HAVING but no GROUP BY, the entire table is "
            "treated as a single group, so exactly one candidate row is "
            "produced before HAVING runs. count(*) on an empty table is 0, so "
            "the condition 0 > 0 is false and the group is discarded, leaving "
            "an empty result. PostgreSQL permits HAVING without GROUP BY; it "
            "is not a syntax error."
        ),
        [PG_SELECT, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-hard-exists-semi-join",
        ["SQL-SUBQUERY", "SQL-JOIN"],
        4,
        (
            "customer(customer_id) has one row per customer, while orders may "
            "contain several rows per customer. Which query returns each "
            "customer with at least one order exactly once?"
        ),
        [
            "SELECT c.customer_id FROM customer c WHERE EXISTS "
            "(SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id);",
            "SELECT c.customer_id FROM customer c JOIN orders o "
            "ON o.customer_id = c.customer_id;",
            "SELECT c.customer_id FROM customer c WHERE EXISTS "
            "(SELECT 1 FROM orders);",
            "SELECT c.customer_id FROM customer c WHERE c.customer_id = "
            "(SELECT o.customer_id FROM orders o "
            "WHERE o.customer_id = c.customer_id);",
        ],
        0,
        (
            "EXISTS is a semi-join: it answers a yes/no question per outer row "
            "and never duplicates that row, so several orders still produce "
            "one customer row. The plain JOIN multiplies the customer once per "
            "order. The uncorrelated EXISTS in option C is true for every "
            "customer as soon as orders is non-empty, and option D uses a "
            "scalar subquery that raises an error when the customer has more "
            "than one order."
        ),
        [PG_SUBQUERY_FUNCTIONS, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-hard-window-rank",
        ["SQL-SELECT"],
        5,
        (
            "Table score(player TEXT, points INT) contains ('a',100), "
            "('b',100) and ('c',90). The statement SELECT player, points, "
            "row_number() OVER (ORDER BY points DESC) AS rn, rank() OVER "
            "(ORDER BY points DESC) AS rk, dense_rank() OVER (ORDER BY points "
            "DESC) AS dr FROM score is executed. Which pattern of values is "
            "produced?"
        ),
        [
            "rn 1,1,2; rk 1,1,2; dr 1,1,2",
            "rn 1,1,2; rk 1,1,3; dr 1,1,2",
            "rn receives 1 and 2 for the two tied rows in an unspecified "
            "order, rk is 1 for both tied rows and then 3, and dr is 1 for "
            "both tied rows and then 2.",
            "rn, rk and dr all receive 1,2,3 because every window function "
            "numbers rows consecutively.",
        ],
        2,
        (
            "row_number always assigns distinct integers, so the two tied "
            "rows get 1 and 2, but which player receives 1 is not defined "
            "because ORDER BY points DESC is not a total order. rank leaves a "
            "gap after ties and continues at 3, while dense_rank continues at "
            "2. Options A and B wrongly give row_number a duplicate value, "
            "and option D wrongly assumes all three functions behave alike."
        ),
        [PG_FUNCTIONS_WINDOW, PG_SELECT],
    ),
    mcq(
        "sq-hard-lateral-from",
        ["SQL-JOIN"],
        5,
        (
            "Which statement about the LATERAL key word is correct?"
        ),
        [
            "A subquery in FROM marked LATERAL may reference columns of FROM "
            "items that appear before it, which an ordinary FROM subquery may "
            "not do.",
            "LATERAL may appear only in the SELECT list, never in FROM.",
            "Without LATERAL, PostgreSQL still allows a FROM subquery to "
            "reference columns of earlier FROM items.",
            "LATERAL is needed only when the subquery returns more than one "
            "row.",
        ],
        0,
        (
            "A FROM subquery is normally evaluated independently and cannot "
            "see other FROM items. LATERAL lifts that restriction, allowing "
            "the subquery to refer to columns of preceding items, which is how "
            "a per-row top-N lookup is expressed. LATERAL is valid in FROM, it "
            "is not a SELECT-list feature, and it has nothing to do with the "
            "number of rows returned."
        ),
        [PG_TABLE_EXPRESSIONS, PG_SELECT],
    ),
    mcq(
        "sq-hard-aggregate-filter",
        ["SQL-GROUP", "SQL-HAVING"],
        4,
        (
            "Table emp(dept_id INT, salary INT) has a nullable salary column. "
            "The query SELECT dept_id, count(*) AS all_rows, count(*) FILTER "
            "(WHERE salary > 5000) AS high FROM emp GROUP BY dept_id returns "
            "one row per department. What does the high column contain?"
        ),
        [
            "The number of rows in that department whose salary > 5000 is "
            "TRUE; rows with NULL salary are not counted.",
            "The number of rows in the whole table whose salary > 5000, "
            "repeated on every department row.",
            "The number of rows in that department whose salary > 5000, "
            "treating NULL salary as high.",
            "It is invalid, because FILTER may be applied to sum but not to "
            "count.",
        ],
        0,
        (
            "FILTER restricts the rows fed to one aggregate inside the current "
            "group. Comparing NULL salary with 5000 yields UNKNOWN, and only "
            "TRUE rows are fed to the aggregate, so NULL salaries are skipped "
            "while count(*) still counts them in all_rows. FILTER is general: "
            "it applies to any aggregate, including count."
        ),
        [PG_AGGREGATE_EXPRESSIONS, PG_AGGREGATE],
    ),
    mcq(
        "sq-hard-grouping-function",
        ["SQL-GROUP"],
        5,
        (
            "Table sale(region_id INT, amount INT) stores rows whose "
            "region_id may be NULL. The query SELECT region_id, "
            "GROUPING(region_id) AS g, count(*) AS n FROM sale GROUP BY "
            "ROLLUP (region_id) ORDER BY g, region_id is executed. How can the "
            "grand-total row be distinguished from the group formed by the "
            "rows whose region_id is NULL?"
        ),
        [
            "The grand total has GROUPING(region_id) = 1, while the NULL-region "
            "group has GROUPING(region_id) = 0.",
            "Both rows have GROUPING(region_id) = 0, so they cannot be told "
            "apart.",
            "The NULL-region group has GROUPING(region_id) = 1 and the grand "
            "total has GROUPING(region_id) = 0.",
            "ROLLUP discards rows whose region_id is NULL, so the ambiguity "
            "cannot arise.",
        ],
        0,
        (
            "ROLLUP (region_id) is shorthand for GROUPING SETS ((region_id), "
            "()), so it produces per-region rows plus one grand total. Both "
            "can show NULL in region_id, which is why the GROUPING function "
            "exists: it returns 1 when the column was supplied by the "
            "grouping-set machinery rather than read from the data, and 0 when "
            "it is a real value. NULL regions are grouped normally, they are "
            "not discarded."
        ),
        [PG_TABLE_EXPRESSIONS, PG_AGGREGATE],
    ),
    sqlq(
        "sq-hard-top-sale-per-region",
        ["SQL-SELECT", "SQL-GROUP"],
        5,
        (
            "Table sale(sale_id INT PRIMARY KEY, region_id INT, amount INT) "
            "records sales; amount is nullable and a region can have several "
            "sales. Return one row per region with the columns region_id "
            "(INT), sale_id (INT) and amount (INT): the sale with the greatest "
            "amount in that region, breaking ties by the lower sale_id. A "
            "region whose sales all have a NULL amount still gets a row, "
            "choosing the sale with the lowest sale_id. Order by region_id "
            "ascending."
        ),
        (
            "SELECT DISTINCT ON (region_id) region_id, sale_id, amount "
            "FROM sale "
            "ORDER BY region_id, amount DESC NULLS LAST, sale_id"
        ),
        [
            (
                "ties_and_null_group",
                False,
                "CREATE TABLE sale(sale_id INT PRIMARY KEY, region_id INT, "
                "amount INT);"
                "INSERT INTO sale VALUES "
                "(1,1,500),(2,1,500),(3,2,700),(4,3,NULL),(5,1,300),"
                "(6,3,NULL);",
            ),
            (
                "no_sales",
                True,
                "CREATE TABLE sale(sale_id INT PRIMARY KEY, region_id INT, "
                "amount INT);",
            ),
        ],
        (
            "DISTINCT ON keeps the first row per region in ORDER BY order. "
            "Within a region, amount DESC NULLS LAST ranks the largest amount "
            "first while placing NULL amounts last, and sale_id breaks the "
            "500/500 tie in favour of sale 1. For region 3, where every amount "
            "is NULL, the sale_id key decides and sale 4 is chosen. The empty "
            "dataset correctly returns no rows."
        ),
        [PG_SELECT],
    ),
    essay(
        "sq-hard-three-valued-reporting",
        ["SQL-WHERE", "SQL-HAVING", "SQL-SUBQUERY"],
        5,
        (
            "A reporting team writes:\n"
            "SELECT order_id FROM orders o\n"
            "WHERE amount <> 0\n"
            "  AND customer_id NOT IN (SELECT customer_id FROM blocked)\n"
            "Table orders has nullable amount and customer_id columns, and the "
            "blocked table may contain NULL.\n"
            "(a) Explain which rows the WHERE clause keeps and why NULL "
            "amounts or a NULL in the subquery silently remove rows.\n"
            "(b) Rewrite the exclusion so it is NULL-safe, using NOT EXISTS, "
            "and state which rows the rewrite now includes that the original "
            "dropped.\n"
            "(c) Explain how the same reasoning applies to HAVING with "
            "sum(amount) > 100 on a group whose amounts are all NULL, and "
            "state what you must decide explicitly."
        ),
        (
            "(a) WHERE keeps only rows for which the whole predicate is TRUE. "
            "amount <> 0 evaluates to UNKNOWN when amount is NULL, so those "
            "rows are dropped even though the amount is not zero. NOT IN is a "
            "chain of <> comparisons: a NULL customer_id, or any NULL produced "
            "by the subquery, makes the comparison UNKNOWN, and UNKNOWN AND "
            "anything is never TRUE. The row therefore disappears silently, "
            "and the report under-counts without raising an error.\n"
            "(b) Rewrite: WHERE amount IS DISTINCT FROM 0 AND NOT EXISTS "
            "(SELECT 1 FROM blocked b WHERE b.customer_id = o.customer_id). "
            "IS DISTINCT FROM is the null-safe inequality, returning TRUE for "
            "a NULL amount against 0. NOT EXISTS is TRUE when no row satisfies "
            "the inner predicate; a NULL customer_id simply matches nothing, "
            "so the order is included. The rewrite therefore keeps rows the "
            "original dropped: orders with NULL amount, and orders with NULL "
            "customer_id. Whether a NULL customer should count as unblocked "
            "is a business decision that must be stated, not left implicit.\n"
            "(c) HAVING runs after aggregation and keeps groups whose "
            "predicate is TRUE. sum ignores NULL inputs, so a group whose "
            "amounts are all NULL produces NULL, sum(amount) > 100 is "
            "UNKNOWN, and the group is dropped. If the intended rule is that "
            "such a group counts as zero, write coalesce(sum(amount), 0) > "
            "100; if it should be excluded, say so explicitly. count(*) is "
            "never NULL, so count-based HAVING conditions do not have this "
            "problem."
        ),
        (
            "The answer must tie the behaviour to three-valued logic rather "
            "than to a vague 'NULL is special' claim. Part (a) should show "
            "that UNKNOWN is neither TRUE nor FALSE and that WHERE/HAVING keep "
            "only TRUE. Part (b) must give the NOT EXISTS form and identify "
            "the rows it recovers. Part (c) must note that SUM over an "
            "all-NULL group is NULL and that coalesce or an explicit exclusion "
            "rule is needed."
        ),
        (
            "Claims that NULL compares equal, treats UNKNOWN as FALSE, or "
            "gives no rewrite; does not connect the WHERE behaviour to the "
            "HAVING question.",
            "Recognises that NULL makes comparisons UNKNOWN and may state that "
            "rows are dropped, but the NOT EXISTS rewrite is missing or still "
            "NULL-sensitive, and HAVING is not addressed.",
            "Correct explanation of NULL propagation through NOT IN and a "
            "correct NOT EXISTS rewrite, but the rows recovered by the rewrite "
            "are not identified, or the HAVING part is only partly right.",
            "Fully correct: explains that only TRUE rows survive, that a "
            "NULL amount or a NULL in the subquery turns the predicate "
            "UNKNOWN, gives the NOT EXISTS rewrite with IS DISTINCT FROM or an "
            "explicit NULL rule, names the rows the rewrite recovers, and "
            "explains that SUM over an all-NULL group is NULL so coalesce or "
            "an explicit policy is required in HAVING.",
        ),
        [PG_COMPARISON, PG_SUBQUERY_FUNCTIONS, PG_AGGREGATE, PG_SELECT],
    ),
]

"""SQL Querying expansion, EASY band.

Four MCQs, one SQL practical and two essays. The MCQs and the SQL practical
are tagged with the assessment-2 SELECT/JOIN concepts as well as the
assessment-3 SQL-* concepts, so the same validated items cover both scopes.
"""

from lib import essay, mcq, sqlq
from sources import (
    PG_AGGREGATE,
    PG_FUNCTIONS_STRING,
    PG_JOIN_TUTORIAL,
    PG_SELECT,
    PG_TABLE_EXPRESSIONS,
)

QUESTIONS = [
    mcq(
        "sq-easy-select-alias",
        ["SQL-SELECT", "SELECT"],
        1,
        (
            "Table customer(customer_id, name, city) has one row per customer. "
            "Which statement returns one row per customer with columns name and "
            "city_label, where city_label contains the city value?"
        ),
        [
            "SELECT name, city AS city_label FROM customer;",
            "SELECT name, city, city_label FROM customer;",
            "SELECT name AS city_label, city FROM customer;",
            "SELECT name, city = city_label FROM customer;",
        ],
        0,
        (
            "AS renames the output column without changing the value, so "
            "city AS city_label produces the requested label. Option B asks for "
            "a column named city_label that does not exist; option C assigns "
            "the label to name instead of city; option D is a comparison "
            "expression that references an undefined identifier."
        ),
        [PG_SELECT],
    ),
    mcq(
        "sq-easy-left-join-semantics",
        ["SQL-JOIN", "JOIN"],
        1,
        (
            "Which join returns every row of the left table and fills columns "
            "from the right table with NULL when no matching row exists?"
        ),
        [
            "INNER JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "CROSS JOIN",
        ],
        1,
        (
            "LEFT JOIN preserves the left input and NULL-extends unmatched "
            "rows. INNER JOIN discards unmatched rows on both sides. RIGHT JOIN "
            "preserves the right input, not the left. CROSS JOIN forms every "
            "pair with no matching condition."
        ),
        [PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-easy-where-before-grouping",
        ["SQL-WHERE", "SQL-HAVING"],
        1,
        (
            "Which clause filters individual rows before grouping and therefore "
            "cannot contain an aggregate such as count(*)?"
        ),
        [
            "WHERE",
            "HAVING",
            "ORDER BY",
            "SELECT",
        ],
        0,
        (
            "WHERE runs on individual rows before groups exist, so aggregates "
            "are not available. HAVING runs after grouping and is the place for "
            "aggregate conditions. ORDER BY sorts the final result, and SELECT "
            "evaluates output expressions after grouping."
        ),
        [PG_SELECT, PG_TABLE_EXPRESSIONS],
    ),
    mcq(
        "sq-easy-group-count-star",
        ["SQL-GROUP"],
        1,
        (
            "The query SELECT region_id, count(*) FROM sales GROUP BY "
            "region_id returns one row per region. What does count(*) count "
            "inside each group?"
        ),
        [
            "Every row in the group, including rows whose other columns are "
            "NULL.",
            "Only rows where region_id is not NULL.",
            "Only distinct combinations of all columns.",
            "Every row in the whole table, not only the group.",
        ],
        0,
        (
            "count(*) counts rows in the current group and ignores no column "
            "values. NULL region_id rows form their own group when GROUP BY is "
            "used. count(region_id) would instead skip NULLs. The table-wide "
            "count would require removing GROUP BY; distinct counting requires "
            "count(DISTINCT ...)."
        ),
        [PG_AGGREGATE, PG_TABLE_EXPRESSIONS],
    ),
    sqlq(
        "sq-easy-customer-name-length",
        ["SQL-SELECT", "SELECT"],
        2,
        (
            "Table customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, "
            "city TEXT). Return customer_id, name, and name_length "
            "(INT, the number of characters in name) for customers whose city "
            "is not NULL. Order by name ascending, then customer_id ascending."
        ),
        (
            "SELECT customer_id, name, length(name) AS name_length "
            "FROM customer WHERE city IS NOT NULL ORDER BY name, customer_id"
        ),
        [
            (
                "customers_in_cities",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, city TEXT);"
                "INSERT INTO customer VALUES "
                "(1,'An','Hanoi'),(2,'Binh',NULL),(3,'Chi','Hue'),(4,'An','Da Nang');",
            ),
            (
                "no_city_values",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, city TEXT);"
                "INSERT INTO customer VALUES (1,'An',NULL),(2,'Binh',NULL);",
            ),
        ],
        (
            "length returns the character count and is labelled name_length. "
            "WHERE ... IS NOT NULL keeps only rows with a city; writing "
            "city <> 'x' would also drop NULL cities. The secondary sort key "
            "customer_id makes the order deterministic when names repeat, and "
            "the edge dataset correctly returns no rows."
        ),
        [PG_SELECT, PG_FUNCTIONS_STRING],
    ),
    essay(
        "sq-easy-select-logical-order",
        ["SQL-SELECT", "SQL-WHERE", "SELECT"],
        2,
        (
            "Explain the logical order in which the clauses FROM, WHERE, GROUP "
            "BY, HAVING, SELECT and ORDER BY are processed. Then explain why an "
            "output alias defined in SELECT cannot be referenced in WHERE but "
            "can be used in ORDER BY."
        ),
        (
            "Logical processing starts with FROM (including joins), then WHERE "
            "filters individual rows, then GROUP BY forms groups, then HAVING "
            "filters groups, then SELECT computes the output expressions and "
            "aliases, and finally ORDER BY sorts the result (LIMIT/OFFSET apply "
            "after sorting). WHERE is evaluated before SELECT, so a SELECT alias "
            "does not exist yet and referencing it there is an error. ORDER BY is "
            "evaluated after SELECT, so PostgreSQL accepts output names there. "
            "The physical plan may reorder operations, but the logical order "
            "determines which names and aggregates are visible."
        ),
        (
            "The key distinction is visibility: WHERE sees input columns but no "
            "output aliases or aggregates; HAVING sees grouped aggregates; "
            "ORDER BY sees the SELECT list. Naming the stages in the correct "
            "order and connecting them to alias visibility is the learning "
            "objective."
        ),
        (
            "Lists clauses in an incorrect order or claims WHERE can see SELECT "
            "aliases; gives no coherent reason for alias visibility.",
            "Gets some of the order right and states that WHERE runs before "
            "SELECT, but misplaces HAVING or cannot explain why ORDER BY can use "
            "an alias.",
            "Correct order and alias explanation, but omits that HAVING operates "
            "on groups or that LIMIT applies after ORDER BY.",
            "Correctly orders FROM, WHERE, GROUP BY, HAVING, SELECT and ORDER BY; "
            "explains that WHERE is evaluated before SELECT so aliases do not "
            "exist there, while ORDER BY is evaluated after SELECT and can use "
            "them; notes that this is logical, not necessarily physical, order.",
        ),
        [PG_SELECT, PG_TABLE_EXPRESSIONS],
    ),
    essay(
        "sq-easy-join-null-fanout",
        ["SQL-JOIN", "JOIN"],
        2,
        (
            "Compare INNER JOIN and LEFT JOIN. Explain what NULL extension means "
            "for unmatched left rows, and explain what happens to the row count "
            "when a row on the left matches several rows on the right."
        ),
        (
            "INNER JOIN returns only pairs that satisfy the join condition: "
            "left rows without a match disappear, and right rows without a "
            "match also disappear. LEFT JOIN returns every left row; when no "
            "right row matches, the right-side columns are filled with NULL "
            "(NULL extension). The result is a bag, not a set: if one left row "
            "matches three right rows, it appears three times with the three "
            "right-side values, so joins can multiply rows. Aggregating after "
            "such a join can overcount unless the query pre-aggregates the many "
            "side or counts distinct keys."
        ),
        (
            "INNER JOIN is a match filter; LEFT JOIN preserves the left side "
            "and NULL-extends. Neither removes duplicates by itself, so a "
            "one-to-many join produces repeated left rows and can inflate "
            "counts and sums."
        ),
        (
            "Confuses INNER and LEFT behavior or says LEFT JOIN fills left "
            "columns with NULL; no mention of row multiplication.",
            "Correctly distinguishes matched versus preserved rows but explains "
            "NULL extension imprecisely or omits join fan-out.",
            "Correct semantics for both joins and NULL extension; mentions "
            "duplicates but does not connect them to incorrect aggregates.",
            "Explains INNER as matched pairs only, LEFT as all left rows with "
            "NULL-extended unmatched columns, bag semantics with explicit "
            "one-to-many row multiplication, and the risk of inflated counts or "
            "sums when aggregating after the join.",
        ),
        [PG_JOIN_TUTORIAL, PG_TABLE_EXPRESSIONS],
    ),
]

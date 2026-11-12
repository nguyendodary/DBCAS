"""PostgreSQL Querying expansion, HARD band (levels 4-5).

Eight MCQs complete the HARD MCQ quota and give every querying concept a HARD
family. One item deliberately spans DISTINCT and ORDER BY so the 14 querying
concepts can be covered by 13 question slots.
"""

from lib import mcq
from sources import PG_CONDITIONAL, PG_EXPRESSIONS, PG_FUNCTIONS_MATH, PG_SELECT

QUESTIONS = [
    mcq(
        "qy-hard-case-no-else",
        ["PG-CASE"],
        4,
        (
            "The expression CASE WHEN rating >= 4 THEN 'high' WHEN rating >= 2 "
            "THEN 'mid' END is evaluated with rating = 1. What is the result?"
        ),
        [
            "NULL, because no WHEN condition is true and the CASE has no ELSE "
            "branch.",
            "'mid', because CASE falls back to the last branch when nothing "
            "matches.",
            "'low', because CASE treats an unmatched value as the lowest "
            "category.",
            "An error, because a CASE expression must always return a value.",
        ],
        0,
        (
            "A searched CASE evaluates its WHEN conditions in order and returns "
            "the result of the first one that is true; later branches are not "
            "evaluated. If none is true and there is no ELSE, the result is "
            "NULL. No implicit lowest category and no error occurs."
        ),
        [PG_CONDITIONAL],
    ),
    mcq(
        "qy-hard-distinct-rows-and-nulls",
        ["PG-DISTINCT"],
        4,
        (
            "The table customer(city, state) contains the rows ('Hue', NULL), "
            "('Hue', NULL) and ('Hue', 'Thua Thien Hue'). How many rows does "
            "SELECT DISTINCT city, state FROM customer return?"
        ),
        [
            "Two, because DISTINCT compares the whole row and treats the two "
            "NULL states as equal.",
            "Three, because NULL is never equal to NULL, so each NULL row is "
            "distinct.",
            "One, because DISTINCT keeps only the first city value.",
            "An error, because DISTINCT cannot be used with nullable columns.",
        ],
        0,
        (
            "DISTINCT operates on the complete selected row, not on one "
            "column. For the purpose of duplicate elimination, NULL values are "
            "considered equal, so the two ('Hue', NULL) rows collapse into one "
            "and the result has two rows. This differs from the = comparison, "
            "for which NULL = NULL is unknown."
        ),
        [PG_SELECT],
    ),
    mcq(
        "qy-hard-exponent-operator",
        ["PG-EXPR"],
        4,
        (
            "What does the PostgreSQL expression 2 ^ 3 return?"
        ),
        [
            "8, because ^ is exponentiation in PostgreSQL.",
            "1, because ^ is the bitwise exclusive-or operator.",
            "9, because ^ is evaluated as 2 raised to the power 3 minus 1.",
            "6, because ^ is treated as multiplication by two.",
        ],
        0,
        (
            "In PostgreSQL, ^ is the exponentiation operator: 2 ^ 3 raises 2 to "
            "the third power and yields 8 (as a floating-point value). It is "
            "not exclusive-or and not multiplication. Unary minus binds more "
            "tightly than ^, so -2 ^ 2 means (-2) ^ 2 and yields 4; write "
            "-(2 ^ 2) to square first and then negate."
        ),
        [PG_FUNCTIONS_MATH],
    ),
    mcq(
        "qy-hard-limit-pagination-ties",
        ["PG-LIMIT"],
        4,
        (
            "A client pages through results with ORDER BY score DESC LIMIT 10 "
            "OFFSET n, and many rows share the same score. What is the "
            "correctness risk?"
        ),
        [
            "Rows with equal scores can appear on more than one page or be "
            "skipped entirely, because their relative order is not "
            "deterministic; a unique tiebreaker in ORDER BY fixes this.",
            "OFFSET cannot be combined with LIMIT, so the query fails as soon "
            "as n is greater than zero.",
            "The second page necessarily continues exactly after the first, "
            "because ties are returned in physical insertion order.",
            "LIMIT counts only distinct scores, so pages can contain more than "
            "ten rows.",
        ],
        0,
        (
            "LIMIT/OFFSET are applied to an ordered result, but an ORDER BY on a "
            "non-unique column leaves the order of tied rows unspecified and it "
            "may differ between executions. Separate executions can therefore "
            "place a tied row on two pages or on none. Adding a unique column, "
            "such as a primary key, as a final ORDER BY key makes paging "
            "deterministic. Keyset pagination is the scalable alternative."
        ),
        [PG_SELECT],
    ),
    mcq(
        "qy-hard-order-by-nulls",
        ["PG-ORDERBY"],
        4,
        (
            "With a default sort, where do NULL values appear in ORDER BY score "
            "ASC and ORDER BY score DESC?"
        ),
        [
            "Last in ASC and first in DESC, because NULL is treated as larger "
            "than any non-NULL value.",
            "First in ASC and last in DESC, because NULL sorts as the smallest "
            "value.",
            "In an unspecified position in both directions, because NULL has no "
            "order.",
            "NULL rows are removed from the result in both directions.",
        ],
        0,
        (
            "PostgreSQL sorts NULLs as if they were larger than any non-NULL "
            "value, so ascending order places them last and descending order "
            "places them first. ORDER BY ... NULLS FIRST or NULLS LAST "
            "overrides the default explicitly; NULL rows are not removed."
        ),
        [PG_SELECT],
    ),
    mcq(
        "qy-hard-intersect-precedence",
        ["PG-SETOPS"],
        4,
        (
            "What does SELECT 1 UNION SELECT 2 INTERSECT SELECT 2 return?"
        ),
        [
            "The rows 1 and 2, because INTERSECT binds more tightly than UNION "
            "and is evaluated first.",
            "Only the row 2, because UNION is evaluated first and the "
            "intersection then keeps 2.",
            "Only the row 1, because INTERSECT removes 2 from the union.",
            "A syntax error, because set operations must be parenthesized when "
            "they are mixed.",
        ],
        0,
        (
            "INTERSECT has higher precedence than UNION and EXCEPT, so the "
            "intersection of the second and third SELECT is computed first and "
            "yields 2; the union with 1 then produces {1, 2}. Mixing set "
            "operations is legal, and parentheses can make a different "
            "grouping explicit. When in doubt, parenthesize."
        ),
        [PG_SELECT],
    ),
    mcq(
        "qy-hard-distinct-order-by-expression",
        ["PG-DISTINCT", "PG-ORDERBY"],
        4,
        (
            "Why does SELECT DISTINCT city FROM customer ORDER BY lower(city) "
            "fail in PostgreSQL?"
        ),
        [
            "For SELECT DISTINCT, ORDER BY expressions must appear in the "
            "select list, so lower(city) must be selected or ORDER BY city "
            "must be used.",
            "It does not fail: ORDER BY is evaluated after DISTINCT, so the "
            "expression is always allowed.",
            "It fails because lower() cannot be used in ORDER BY at all.",
            "It fails because DISTINCT and ORDER BY can never be combined in "
            "one query.",
        ],
        0,
        (
            "With DISTINCT, the output is a set of rows, and PostgreSQL "
            "requires each ORDER BY expression to match an output column. "
            "lower(city) is not in the select list, so the query is rejected "
            "with 'for SELECT DISTINCT, ORDER BY expressions must appear in "
            "select list'. Selecting lower(city) AS city_key or ordering by "
            "the selected city column avoids the error. DISTINCT and ORDER BY "
            "can otherwise be combined normally."
        ),
        [PG_SELECT],
    ),
    mcq(
        "qy-hard-alias-visibility",
        ["PG-SYNTAX"],
        4,
        (
            "What happens when SELECT price * qty AS total FROM item WHERE "
            "total > 100 ORDER BY total is executed?"
        ),
        [
            "It fails because total is an output alias and is not visible in "
            "WHERE, although the same alias is allowed in ORDER BY.",
            "It runs successfully because an output alias is visible in every "
            "clause of the query.",
            "It runs, but WHERE is applied after the multiplication only when "
            "the alias is also used in ORDER BY.",
            "It fails only if two selected columns are both named total.",
        ],
        0,
        (
            "WHERE is evaluated before the select list, so an output alias does "
            "not exist at that point; the query raises 'column total does not "
            "exist'. ORDER BY, by contrast, may reference output column names "
            "and accepts total. Repeating price * qty in WHERE, or wrapping the "
            "query in a subquery that exposes total, resolves the problem."
        ),
        [PG_SELECT],
    ),
]

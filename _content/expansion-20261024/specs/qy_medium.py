"""PostgreSQL Querying expansion, MEDIUM band (level 3).

A single multi-concept MCQ adds the missing syntax family and strengthens
LIMIT reasoning; the band already meets its type quotas.
"""

from lib import mcq
from sources import PG_SELECT, PG_TABLE_EXPRESSIONS

QUESTIONS = [
    mcq(
        "qy-medium-clause-order-limit",
        ["PG-SYNTAX", "PG-LIMIT"],
        3,
        (
            "Consider SELECT dept, count(*) AS n FROM employee WHERE active "
            "GROUP BY dept HAVING count(*) > 2 ORDER BY n DESC LIMIT 3. Which "
            "statement about how the clauses interact is correct?"
        ),
        [
            "WHERE filters individual rows before grouping, HAVING filters "
            "groups after aggregation, ORDER BY sorts the selected rows, and "
            "LIMIT keeps the first three rows of that sorted result.",
            "WHERE runs after GROUP BY, so it can filter groups by their count.",
            "LIMIT is applied before ORDER BY, so it selects three arbitrary "
            "employees and then sorts them.",
            "ORDER BY n is invalid because an output alias cannot be used in "
            "ORDER BY when the query also has GROUP BY.",
        ],
        0,
        (
            "The logical processing order is FROM, WHERE, GROUP BY, HAVING, "
            "SELECT, then ORDER BY and LIMIT. WHERE therefore sees individual "
            "rows and cannot filter on an aggregate; HAVING is the aggregate "
            "filter. ORDER BY sorts the result of the select list, and LIMIT is "
            "applied last to that ordered result. An output alias such as n may "
            "be used in ORDER BY, but not in WHERE."
        ),
        [PG_SELECT, PG_TABLE_EXPRESSIONS],
    ),
]

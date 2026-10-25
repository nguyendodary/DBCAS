"""PostgreSQL Querying expansion, EASY band (levels 1-2).

The band lacked an essay and had no family for recursive queries, so one
introductory essay covers the recursive CTE concept.
"""

from lib import essay
from sources import PG_QUERIES_WITH

QUESTIONS = [
    essay(
        "qy-easy-recursive-cte",
        ["PG-RECURSIVE"],
        2,
        (
            "Explain the structure of a WITH RECURSIVE query in PostgreSQL. "
            "Identify the base term and the recursive term, state what the "
            "recursive term must reference, and explain why a termination "
            "condition is required. Describe the difference between UNION and "
            "UNION ALL in this context."
        ),
        (
            "A WITH RECURSIVE query defines a common table expression that can "
            "refer to itself. It has the form WITH RECURSIVE name AS (base "
            "term UNION [ALL] recursive term) SELECT ... FROM name. The base "
            "term runs once and produces the starting rows. The recursive term "
            "references the CTE name and is evaluated repeatedly, each time "
            "consuming the rows produced by the previous iteration, until an "
            "iteration returns no rows. Without a termination condition, such "
            "as a level counter or a join that stops at the root, the recursion "
            "never becomes empty and the query runs until it is cancelled or "
            "runs out of resources. UNION removes duplicate rows between "
            "iterations, which can stop a cycle in a cyclic graph; UNION ALL "
            "keeps duplicates and is faster but can loop forever on a cycle. "
            "A typical use is walking an employee table from a manager down "
            "through subordinates by joining the table to the CTE on the "
            "parent key."
        ),
        (
            "The answer must identify the base term as the non-recursive "
            "starting rows, the recursive term as the part that references the "
            "CTE, and the repeated evaluation until no rows are produced. It "
            "must explain a termination condition and distinguish UNION "
            "(duplicate removal) from UNION ALL (duplicates kept, faster, cycle "
            "risk)."
        ),
        (
            "Describes a recursive CTE as an ordinary subquery, or shows no "
            "base/recursive split and no termination reasoning.",
            "Names the base and recursive parts but cannot explain how "
            "iteration stops, or confuses UNION with UNION ALL.",
            "Explains the structure and termination, but the UNION versus "
            "UNION ALL distinction is incomplete or the cycle risk is not "
            "stated.",
            "Fully correct: base term, self-referencing recursive term, "
            "iterative evaluation to an empty result, an explicit or naturally "
            "reached termination condition, and UNION deduplication versus "
            "UNION ALL with its cycle risk.",
        ),
        [PG_QUERIES_WITH],
    ),
]

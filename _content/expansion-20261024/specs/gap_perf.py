"""Practice-depth gap fill for A6 Performance.

Formal assessment is blocked by the mandatory SQL quota; PG-INDEX-TYPES and
PG-STATS had no EASY family, which also broke practice at that band.
"""

from lib import mcq
from sources import PG_INDEX_TYPES, PG_STATS

QUESTIONS = [
    mcq(
        "perf-easy-default-index-type",
        ["PG-INDEX-TYPES"],
        2,
        (
            "Which statement correctly contrasts the default PostgreSQL index "
            "type with the hash type?"
        ),
        [
            "B-tree is the default and supports equality, range and ordering "
            "operations, while hash supports only equality comparisons.",
            "Hash is the default and supports range queries, while B-tree "
            "supports only equality.",
            "GIN is the default for all scalar columns, while B-tree is used "
            "only for full-text search.",
            "B-tree and hash support exactly the same operators, so the choice "
            "affects only index size.",
        ],
        0,
        (
            "CREATE INDEX without a type creates a B-tree, which serves "
            "equality, range and ORDER BY-style comparisons. A hash index "
            "supports only equality. GIN is specialized for composite values "
            "such as arrays, jsonb and full-text lexemes, not the default for "
            "scalar columns. The operator support differs, not just the size."
        ),
        [PG_INDEX_TYPES],
    ),
    mcq(
        "perf-easy-planner-statistics",
        ["PG-STATS"],
        2,
        (
            "What are the table statistics collected by ANALYZE used for?"
        ),
        [
            "They let the planner estimate row counts and selectivity so it can "
            "choose between plans such as sequential scan and index scan.",
            "They enforce uniqueness and foreign-key rules at insert time.",
            "They cache the results of recent queries so repeated SELECTs skip "
            "execution.",
            "They record the disk space used by each index for reporting only.",
        ],
        0,
        (
            "ANALYZE samples table contents and stores distributions such as "
            "most common values and histograms. The planner uses them to "
            "estimate how many rows a condition will match and to compare plan "
            "costs. If statistics are stale, estimates can be badly wrong and a "
            "poor plan may be chosen, which is why autovacuum and manual ANALYZE "
            "matter. Constraints and query results are unrelated."
        ),
        [PG_STATS],
    ),
]

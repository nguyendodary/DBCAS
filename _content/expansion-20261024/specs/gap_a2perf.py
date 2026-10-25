"""A2 Performance (indexes) practice-depth fill.

A2 formal assessment requires two SQL practicals, which no honest read-only
SELECT can satisfy for the index concept. These MCQs bring EASY and MEDIUM to
practice readiness and improve concept coverage without relabelling queries.
"""

from lib import mcq
from sources import (
    PG_CREATE_INDEX,
    PG_EXPLAIN,
    PG_INDEX_MULTICOLUMN,
    PG_INDEX_TYPES,
    PG_INDEXES,
)

QUESTIONS = [
    mcq(
        "a2-easy-index-tradeoff",
        ["IDX"],
        2,
        (
            "A B-tree index is added on a frequently filtered column. Which "
            "statement best describes the effect?"
        ),
        [
            "Lookups of matching rows can become faster, but the index uses "
            "storage and adds work to inserts, updates and deletes, and the "
            "planner may still choose a sequential scan.",
            "Every query on the table becomes faster because the planner must "
            "use the newest index.",
            "Write operations become faster because the index organizes new "
            "rows before they are stored.",
            "The index also guarantees that the column is unique.",
        ],
        0,
        (
            "An index is a trade-off: it can make selective reads cheaper but "
            "consumes space and must be maintained on writes, so bulk changes "
            "can slow down. The planner compares costs and may ignore the index, "
            "for example when most rows match or the table is small. Only a "
            "UNIQUE index or constraint enforces uniqueness."
        ),
        [PG_INDEXES, PG_EXPLAIN],
    ),
    mcq(
        "a2-easy-composite-leftmost",
        ["IDX"],
        2,
        (
            "A composite B-tree index is created on (customer_id, created_on). "
            "Which predicate can use it efficiently?"
        ),
        [
            "A filter on customer_id, or on customer_id together with a range "
            "on created_on, because the leading column is constrained.",
            "A filter on created_on alone, because it is part of the index.",
            "Any filter on any column of the table, because the index covers "
            "the whole row.",
            "Only a filter that constrains both columns to equality; a range on "
            "created_on makes the index unusable.",
        ],
        0,
        (
            "A B-tree on (customer_id, created_on) is ordered by customer_id "
            "first, then created_on within each customer. It can be used when "
            "customer_id is constrained, optionally with a range on created_on. "
            "A predicate on created_on alone cannot use the index efficiently "
            "because the leading column is unconstrained. Equality on both "
            "columns works, but a range on the trailing column is also "
            "supported."
        ),
        [PG_INDEX_MULTICOLUMN, PG_INDEX_TYPES],
    ),
    mcq(
        "a2-easy-index-write-cost",
        ["IDX"],
        1,
        (
            "Why does adding several indexes to a table slow down INSERT, "
            "UPDATE and DELETE statements?"
        ),
        [
            "Every affected index must be updated to reflect the changed rows, "
            "so more indexes mean more maintenance work per write.",
            "Indexes lock the entire table on every write, so only one writer "
            "can proceed at a time.",
            "PostgreSQL rewrites every index from scratch after each write.",
            "Indexes copy the full table, so each write is duplicated once per "
            "index.",
        ],
        0,
        (
            "Each index is a separate data structure keyed on its columns. An "
            "insert or a change to an indexed column requires an entry in every "
            "affected index, which adds I/O and CPU work. Writers are not "
            "serialized by a table-wide lock, indexes are updated incrementally "
            "rather than rebuilt, and an index stores keys and row references, "
            "not a copy of the table."
        ),
        [PG_INDEXES],
    ),
    mcq(
        "a2-medium-expression-index",
        ["IDX"],
        3,
        (
            "Queries run WHERE lower(email) = 'a@example.com' on a large table "
            "that has a plain B-tree index on email. Why is the index not used, "
            "and what helps?"
        ),
        [
            "The expression lower(email) is not the indexed value, so an "
            "expression index on lower(email) is needed to match the predicate.",
            "The index is not used because B-tree indexes never support text; "
            "only hash indexes do.",
            "The index is ignored only when email is nullable; adding NOT NULL "
            "makes lower(email) use the plain index.",
            "Nothing helps: PostgreSQL cannot index the result of any function.",
        ],
        0,
        (
            "A plain index on email stores email values, while the predicate "
            "compares lower(email). The planner would need an index whose key is "
            "the same expression, created as CREATE INDEX ... ON t "
            "(lower(email)). PostgreSQL supports expression indexes, and the "
            "function used must be immutable. Nullability and the B-tree text "
            "support are not the reason."
        ),
        [PG_CREATE_INDEX, PG_EXPLAIN],
    ),
    mcq(
        "a2-medium-partial-index",
        ["IDX"],
        3,
        (
            "A status column is 'pending' for about 1% of rows, and almost all "
            "queries filter status = 'pending'. Which index is the best fit?"
        ),
        [
            "A partial index with WHERE status = 'pending', which stores only "
            "the matching rows and is maintained only when the predicate holds.",
            "A full B-tree index on status, because partial indexes are not "
            "usable for equality filters.",
            "An index on every other column, because status has low cardinality "
            "and cannot be indexed.",
            "No index at all, because a filter matching 1% of rows always uses a "
            "sequential scan.",
        ],
        0,
        (
            "A partial index is defined with a WHERE predicate; it contains only "
            "the rows satisfying that predicate, so it is much smaller than a "
            "full index and is only maintained for matching rows. Queries must "
            "include a predicate that implies the index predicate to use it. Low "
            "cardinality alone does not prevent indexing, and a highly selective "
            "filter is exactly where an index can help."
        ),
        [PG_CREATE_INDEX, PG_INDEXES],
    ),
]

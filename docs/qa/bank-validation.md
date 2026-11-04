# Question-bank audit — 2026-11-04

Before: **442** source questions: **326 MCQ / 67 SQL / 49 essay**, **80** unique
concepts across `benchmark_pack.json`, `sql_knowledge_pack.json` and
`postgres_knowledge_pack.json`. Default seed: **24** questions / **15** concepts;
one historical essay retired. No question/history IDs have been changed.

Official site and `/docs/current/` fetched: stable **PostgreSQL 18.6**; sandbox
uses PostgreSQL 17, so executable references must work on that actual sandbox.
Fetched **123/125** existing official reference URLs. Two return HTTP errors:
`sql-syntax-expressions.html` → `sql-expressions.html`, `textsearch-types.html`
→ `datatype-textsearch.html`; both correct destinations verified on the official
site. Local cached pages/fetch hashes: `_review/audit-20261104/postgres-docs/`.

References reviewed: [commands](https://www.postgresql.org/docs/18/sql-commands.html),
[types](https://www.postgresql.org/docs/18/datatype.html),
[functions/operators](https://www.postgresql.org/docs/18/functions.html),
[queries/joins/grouping](https://www.postgresql.org/docs/18/queries-table-expressions.html),
[subqueries](https://www.postgresql.org/docs/18/functions-subquery.html),
[aggregates](https://www.postgresql.org/docs/18/functions-aggregate.html),
[windows](https://www.postgresql.org/docs/18/functions-window.html),
[CTEs](https://www.postgresql.org/docs/18/queries-with.html),
[indexes](https://www.postgresql.org/docs/18/indexes.html),
[transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html),
[constraints](https://www.postgresql.org/docs/18/ddl-constraints.html),
[views](https://www.postgresql.org/docs/18/tutorial-views.html),
[EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html),
[performance](https://www.postgresql.org/docs/18/performance-tips.html).

Existing product bounds: minimum **1**, default **5**, maximum **20**. With
three balanced types, the worst single-concept/single-difficulty allocation is
`ceil(20 / 3) = 7` per type. Coverage target: **7 per concept × difficulty × type**;
coverage is not yet achieved or claimed. Widening must remain explicit.

| Question ID | Original issue | Fix/replacement | PostgreSQL documentation URL | Validation result |
| --- | --- | --- | --- | --- |
| Core 24 + SQL supplement 3 | No references/explanations; two missing essay samples | Pending | queries/constraints/indexes pages above | Not yet fixed |
| pg-m022, pg-m023 | NULL/tie ordering assumptions missing | Pending | https://www.postgresql.org/docs/18/queries-select-lists.html | Not yet fixed |
| pg-m046 | Missing schema assumption for functional dependence | Pending | https://www.postgresql.org/docs/18/queries-table-expressions.html | Not yet fixed |
| pg-m056, pg-m060 | CTE inlining/cycle termination overgeneralized | Pending | https://www.postgresql.org/docs/18/queries-with.html | Not yet fixed |
| pg-m076, pg-m091, pg-m104, pg-m106 | Trailing-space exception, array bounds, distractor/domain ambiguity | Pending | https://www.postgresql.org/docs/18/datatype.html | Not yet fixed |
| pg-m130, pg-m141, pg-m146, pg-m156 | Transaction rollback, CHECK/FK/refresh qualifications | Pending | https://www.postgresql.org/docs/18/sql-commands.html | Not yet fixed |
| pg-m178, pg-m183, pg-m205, pg-m209, pg-m220, pg-m223 | MVCC/lock/role/FOUND/procedure qualifications | Pending | https://www.postgresql.org/docs/18/explicit-locking.html | Not yet fixed |
| pg-m255, pg-m269, pg-m272, pg-m281, pg-m289, pg-m304, pg-m306 | Sequence/upsert/order/window/report/LIKE/NOT VALID claims | Pending | https://www.postgresql.org/docs/18/sql-commands.html | Not yet fixed |
| pg-s034 | Single highest employee contradicts include-ties requirement | Pending | https://www.postgresql.org/docs/18/functions-window.html | Not yet fixed |
| pg-s053 | Single-token name gets trailing dot; only handles two words | Pending | https://www.postgresql.org/docs/18/functions-string.html | Not yet fixed |
| pg-s056 | Manager IDs compared to department IDs; primary result empty | Pending | https://www.postgresql.org/docs/18/functions-subquery.html | Not yet fixed |
| Extended essay samples | MVCC, jsonb constraints, RPO, FOUND, skip scan, arrays and other overclaims | Pending itemized corrections | Relevant per-question source_refs | Not yet fixed |

All 442 have been inventoried; factual review has read all prompts/MCQ choices
and SQL references, with essay/rubric review ongoing. Full shared automated
validation and actual SQL execution are pending. No global pass claimed.

## Before coverage

Counts are active source questions; multi-concept questions count in each tagged
concept. Each cell is **MCQ / SQL / essay**. Target is 7 / 7 / 7.

| Concept | Dễ | Vừa | Khó |
| --- | --- | --- | --- |
| DB-1NF | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| DB-2NF | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| DB-3NF | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| DB-ER | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| DB-FD | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| DB-NORM | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| IDX | 0 / 0 / 0 | 0 / 0 / 1 | 0 / 0 / 0 |
| JOIN | 1 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| PG-AGG-FUNC | 4 / 2 / 0 | 3 / 4 / 0 | 1 / 3 / 0 |
| PG-ALTER | 1 / 0 / 0 | 1 / 0 / 0 | 0 / 0 / 1 |
| PG-BACKUP | 1 / 0 / 0 | 3 / 0 / 0 | 1 / 0 / 1 |
| PG-CASE | 4 / 1 / 0 | 1 / 1 / 1 | 0 / 0 / 0 |
| PG-COLLATION | 0 / 0 / 0 | 2 / 0 / 0 | 1 / 0 / 0 |
| PG-CONFIG | 2 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-CONSTRAINT | 3 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 |
| PG-CTE | 2 / 1 / 0 | 2 / 2 / 1 | 2 / 0 / 0 |
| PG-DISTINCT | 3 / 1 / 0 | 2 / 1 / 0 | 0 / 0 / 0 |
| PG-DML | 4 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 |
| PG-DOMAIN | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-EXPLAIN | 2 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 2 |
| PG-EXPR | 5 / 0 / 0 | 5 / 0 / 1 | 0 / 0 / 0 |
| PG-FTS | 0 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 1 |
| PG-FUNC-DATE | 3 / 0 / 0 | 1 / 3 / 0 | 0 / 2 / 0 |
| PG-FUNC-NUM | 3 / 2 / 0 | 1 / 1 / 0 | 0 / 0 / 0 |
| PG-FUNC-STR | 5 / 1 / 0 | 1 / 3 / 0 | 0 / 0 / 0 |
| PG-GENCOL | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-IDENTITY | 1 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 |
| PG-INDEX | 2 / 0 / 0 | 3 / 0 / 2 | 2 / 0 / 1 |
| PG-INDEX-TYPES | 0 / 0 / 0 | 2 / 0 / 1 | 3 / 0 / 0 |
| PG-ISOLATION | 1 / 0 / 0 | 3 / 0 / 0 | 3 / 0 / 1 |
| PG-JOIN-TYPES | 6 / 2 / 0 | 3 / 3 / 1 | 1 / 2 / 0 |
| PG-KEYS | 3 / 0 / 0 | 2 / 0 / 2 | 0 / 0 / 0 |
| PG-LIMIT | 3 / 1 / 0 | 1 / 1 / 0 | 0 / 0 / 0 |
| PG-LOCK | 1 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 1 |
| PG-MATVIEW | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-MERGE | 0 / 0 / 0 | 1 / 0 / 0 | 1 / 0 / 0 |
| PG-MONITOR | 1 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-MVCC | 1 / 0 / 0 | 3 / 0 / 1 | 1 / 0 / 1 |
| PG-NULLS | 5 / 0 / 0 | 2 / 6 / 1 | 0 / 1 / 0 |
| PG-ORDERBY | 3 / 2 / 0 | 2 / 1 / 0 | 0 / 0 / 0 |
| PG-PARTITION | 0 / 0 / 0 | 2 / 0 / 0 | 3 / 0 / 1 |
| PG-PATTERN | 3 / 0 / 0 | 2 / 1 / 1 | 0 / 0 / 0 |
| PG-PLPGSQL | 1 / 0 / 0 | 3 / 0 / 1 | 3 / 0 / 0 |
| PG-PRIVILEGE | 1 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 1 |
| PG-PROC | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-RECURSIVE | 0 / 0 / 0 | 2 / 0 / 0 | 2 / 3 / 1 |
| PG-REPLICATION | 0 / 0 / 0 | 2 / 0 / 0 | 3 / 0 / 1 |
| PG-RLS | 0 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 2 |
| PG-ROLES | 2 / 0 / 0 | 3 / 0 / 1 | 1 / 0 / 1 |
| PG-SCHEMA | 2 / 0 / 0 | 1 / 0 / 1 | 1 / 0 / 0 |
| PG-SELECT-LIST | 5 / 3 / 0 | 0 / 10 / 0 | 0 / 4 / 0 |
| PG-SETOPS | 4 / 1 / 0 | 3 / 2 / 0 | 1 / 0 / 0 |
| PG-STATS | 0 / 0 / 0 | 1 / 0 / 0 | 2 / 0 / 2 |
| PG-SYNTAX | 4 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| PG-TABLE | 4 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-TRIGGER | 1 / 0 / 0 | 3 / 0 / 1 | 2 / 0 / 0 |
| PG-TXN | 3 / 0 / 0 | 2 / 0 / 2 | 1 / 0 / 0 |
| PG-TYPE-ARRAY | 2 / 0 / 0 | 3 / 2 / 1 | 0 / 1 / 0 |
| PG-TYPE-BOOL | 3 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| PG-TYPE-CHAR | 3 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| PG-TYPE-DATE | 2 / 0 / 0 | 3 / 0 / 1 | 0 / 0 / 0 |
| PG-TYPE-JSON | 2 / 0 / 0 | 4 / 1 / 1 | 1 / 1 / 1 |
| PG-TYPE-MISC | 2 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-TYPE-NUM | 4 / 0 / 0 | 1 / 0 / 0 | 0 / 0 / 0 |
| PG-TYPE-RANGE | 0 / 0 / 0 | 2 / 0 / 0 | 1 / 0 / 0 |
| PG-TYPECONV | 1 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 |
| PG-UDF | 1 / 0 / 0 | 3 / 0 / 1 | 2 / 0 / 1 |
| PG-VACUUM | 1 / 0 / 0 | 3 / 0 / 1 | 2 / 0 / 1 |
| PG-VIEW | 1 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 |
| PG-WAL | 0 / 0 / 0 | 1 / 0 / 1 | 2 / 0 / 1 |
| PG-WINDOW | 3 / 0 / 0 | 3 / 3 / 1 | 3 / 2 / 0 |
| SELECT | 1 / 1 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| SQL-DDL-KNOW | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| SQL-DML-KNOW | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 |
| SQL-GROUP | 1 / 3 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| SQL-HAVING | 1 / 1 / 0 | 0 / 1 / 0 | 0 / 0 / 0 |
| SQL-JOIN | 1 / 3 / 0 | 0 / 1 / 0 | 0 / 0 / 0 |
| SQL-SELECT | 1 / 1 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| SQL-SUBQUERY | 1 / 3 / 0 | 0 / 2 / 0 | 0 / 1 / 0 |
| SQL-WHERE | 1 / 1 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

Of 720 cells, 719 are below quota and 450 are empty. Canonical duplicate prompts: 0.

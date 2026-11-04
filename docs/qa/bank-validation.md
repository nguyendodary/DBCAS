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
all 720 cells now meet this quota. Widening must remain explicit.

| Question ID | Original issue | Fix/replacement | PostgreSQL documentation URL | Validation result |
| --- | --- | --- | --- | --- |
| legacy-mcq-select-filter | A row-predicate question should distinguish filtering before grouping from result truncation. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| legacy-mcq-inner-join | The matching condition should be explicit so CROSS JOIN cannot be interpreted as matching every pair. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| legacy-sql-customer-names | Missing explanation/provenance.; edge output was empty | Add a reviewed explanation and official reference; synchronize Vietnamese content. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| legacy-essay-index-read-write | Missing explanation/provenance; missing sample answer and invalid historical rubric | Add sample and four contiguous bands; freeze the old three-band definition for history tests. | https://www.postgresql.org/docs/18/indexes-intro.html | Strict gate passed |
| essay-index-workload-tradeoff | Missing explanation/provenance; missing sample answer | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/indexes-intro.html | Strict gate passed |
| mcq-sql-select | Vietnamese prompt asked which attributes rather than which query component selects them. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/queries-select-lists.html | Strict gate passed |
| mcq-sql-where | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| mcq-sql-join | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| mcq-sql-group | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| mcq-sql-having | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| mcq-sql-subquery | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/functions-subquery.html | Strict gate passed |
| mcq-db-er | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/planner-stats.html | Strict gate passed |
| mcq-db-norm | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/planner-stats.html | Strict gate passed |
| mcq-db-fd | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/planner-stats.html | Strict gate passed |
| mcq-db-1nf | Fixed separately named atomic columns are not unambiguously a formal 1NF violation. | Replace the ambiguous distractor; preserve labels and the correct-option identity. | https://www.postgresql.org/docs/18/arrays.html | Strict gate passed |
| mcq-db-2nf | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/planner-stats.html | Strict gate passed |
| mcq-db-3nf | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/planner-stats.html | Strict gate passed |
| sql-sql-select | Missing explanation/provenance.; edge output was empty | Add a reviewed explanation and official reference; synchronize Vietnamese content. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| sql-sql-where | Missing explanation/provenance.; edge output was empty | Add a reviewed explanation and official reference; synchronize Vietnamese content. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| sql-sql-join | Missing explanation/provenance.; edge output was empty | Add a reviewed explanation and official reference; synchronize Vietnamese content. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| sql-sql-group | Missing explanation/provenance.; edge output was empty | Add a reviewed explanation and official reference; synchronize Vietnamese content. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| sql-sql-having | Missing explanation/provenance.; edge output was empty | Add a reviewed explanation and official reference; synchronize Vietnamese content. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| sql-sql-subquery | Missing explanation/provenance.; edge output was empty | Add a reviewed explanation and official reference; synchronize Vietnamese content. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-subquery.html | Strict gate passed |
| essay-normalization | Missing explanation/provenance; complex essay misclassified EASY | Classify as HARD (4); add explanation and provenance. | https://www.postgresql.org/docs/18/planner-stats.html | Strict gate passed |
| dml-knowledge | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/dml.html | Strict gate passed |
| ddl-knowledge | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/ddl-constraints.html | Strict gate passed |
| essay-dml-ddl-knowledge | Missing explanation/provenance. | Add a reviewed explanation and official reference; synchronize Vietnamese content. | https://www.postgresql.org/docs/18/ddl-constraints.html | Strict gate passed |
| pg-m005 | Obsolete official documentation path. | Use the current sql-expressions.html or datatype-textsearch.html URL. | https://www.postgresql.org/docs/18/sql-expressions.html | Strict gate passed |
| pg-m006 | Obsolete official documentation path. | Use the current sql-expressions.html or datatype-textsearch.html URL. | https://www.postgresql.org/docs/18/sql-expressions.html | Strict gate passed |
| pg-m007 | Obsolete official documentation path. | Use the current sql-expressions.html or datatype-textsearch.html URL. | https://www.postgresql.org/docs/18/functions-comparison.html | Strict gate passed |
| pg-m022 | DESC puts NULL first; tied salaries did not identify a deterministic employee. | One highest-paid employee per department; a salary tie is resolved by name in ascending order | https://www.postgresql.org/docs/18/sql-select.html | Strict gate passed |
| pg-m023 | Predictable newest-row selection omitted NULL and tie assumptions. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/queries-select-lists.html | Strict gate passed |
| pg-m046 | The claimed GROUP BY error is absent if dept is a primary key. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| pg-m056 | Inlining also requires a side-effect-free SELECT; volatile CTEs are not generally inlined. | It can be folded into the parent query so the planner can optimize them together | https://www.postgresql.org/docs/18/queries-with.html | Strict gate passed |
| pg-m060 | UNION does not stop a cycle when a depth/path column keeps making distinct rows. | No: UNION removes duplicate complete rows, but increasing depth keeps the rows distinct; explicit cycle detection is needed | https://www.postgresql.org/docs/18/queries-with.html | Strict gate passed |
| pg-m076 | An unspecified six-character string could contain removable trailing spaces. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/datatype-character.html | Strict gate passed |
| pg-m091 | PostgreSQL permits array lower bounds other than one. | The explicit lower bound is zero: indexes 0, 1 and 2 hold 10, 20 and 30 | https://www.postgresql.org/docs/18/arrays.html | Strict gate passed |
| pg-m104 | The ICU-only distractor was a defensible second factual answer. | Replace the ambiguous distractor; preserve labels and the correct-option identity. | https://www.postgresql.org/docs/18/collation.html | Strict gate passed |
| pg-m106 | Domain checks were inaccurately described as ignored by casts and indexes. | 0 of type integer; explicitly casting this result back to posint would fail its CHECK | https://www.postgresql.org/docs/18/domains.html | Strict gate passed |
| pg-m107 | A distractor repeated the correct string with an ambiguous cast qualifier. | Replace the ambiguous distractor; preserve labels and the correct-option identity. | https://www.postgresql.org/docs/18/functions-string.html | Strict gate passed |
| pg-m116 | div(numeric,numeric) returns numeric, not the integer result type of integer division. | div(9, 2) returns numeric 4, while 9 / 2 returns integer 4; both truncate the quotient toward zero | https://www.postgresql.org/docs/18/functions-math.html | Strict gate passed |
| pg-m125 | Double-negative wording obscured which predicate was being tested. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/functions-matching.html | Strict gate passed |
| pg-m126 | Obsolete official documentation path. | Use the current sql-expressions.html or datatype-textsearch.html URL. | https://www.postgresql.org/docs/18/datatype-textsearch.html | Strict gate passed |
| pg-m128 | Not every text-search configuration performs stemming. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/textsearch-dictionaries.html | Strict gate passed |
| pg-m130 | DROP TABLE was incorrectly described as irrevocably permanent before transaction commit. | It drops the table definition and data in the current transaction; rolling that transaction back can undo the DROP | https://www.postgresql.org/docs/18/sql-droptable.html | Strict gate passed |
| pg-m137 | now() is STABLE, not VOLATILE; either category is disallowed in a generated expression because it is not IMMUTABLE. | A generated expression must be immutable, contain no subqueries or references to another row or generated column | https://www.postgresql.org/docs/18/xfunc-volatility.html | Strict gate passed |
| pg-m141 | CHECK immutability is assumed, not a universal rejection of functions reading other rows. | Later changes to those other rows do not recheck this row, so the invariant is not guaranteed; use a suitable declarative cross-row constraint | https://www.postgresql.org/docs/18/ddl-constraints.html | Strict gate passed |
| pg-m146 | A nullable foreign key need not match exactly one parent; temporal keys also need qualification. | A child key value must identify one unambiguous parent row; uniqueness prevents multiple parent rows with that key | https://www.postgresql.org/docs/18/ddl-constraints.html | Strict gate passed |
| pg-m156 | Concurrent materialized-view refresh omitted populated/all-row/plain-column index requirements. | It permits concurrent reads of a populated materialized view and needs a UNIQUE index using plain columns and covering every row | https://www.postgresql.org/docs/18/sql-refreshmaterializedview.html | Strict gate passed |
| pg-m178 | Readers/writers can still conflict through table or explicitly requested row locks. | Reads use visible row versions rather than conflicting writer row locks; explicit locking and conflicting DDL can still block | https://www.postgresql.org/docs/18/mvcc-intro.html | Strict gate passed |
| pg-m183 | FOR NO KEY UPDATE still blocks other non-key writers; it is compatible with FOR KEY SHARE. | FOR NO KEY UPDATE conflicts with FOR UPDATE, FOR SHARE and another FOR NO KEY UPDATE, including an ordinary non-key UPDATE | https://www.postgresql.org/docs/18/explicit-locking.html | Strict gate passed |
| pg-m205 | Since PostgreSQL 16, privilege inheritance is governed by each membership's INHERIT option. | Automatic use of the member roles' ordinary object privileges; special role attributes such as CREATEDB are not inherited this way | https://www.postgresql.org/docs/18/role-membership.html | Strict gate passed |
| pg-m209 | Non-owner superusers/BYPASSRLS roles are exceptions to default-deny RLS. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/ddl-rowsecurity.html | Strict gate passed |
| pg-m220 | Dynamic EXECUTE does not update FOUND, unlike several static PL/pgSQL statements. | No; EXECUTE leaves FOUND unchanged. Use GET DIAGNOSTICS ... ROW_COUNT to inspect the dynamic command's row count | https://www.postgresql.org/docs/18/plpgsql-statements.html | Strict gate passed |
| pg-m223 | Procedures support OUT parameters; transaction control depends on invocation/security context. | Procedures use CALL, may return OUT parameters, and can control transactions only in permitted call contexts; they are not scalar function expressions | https://www.postgresql.org/docs/18/xproc.html | Strict gate passed |
| pg-m234 | The distractor 'VACUUM locks the table' is true: ordinary VACUUM takes SHARE UPDATE EXCLUSIVE. | Replace the ambiguous distractor; preserve labels and the correct-option identity. | https://www.postgresql.org/docs/18/explicit-locking.html | Strict gate passed |
| pg-m244 | WAL retention is not unconditional if a slot is invalidated or a retention limit applies. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/warm-standby.html | Strict gate passed |
| pg-m255 | Sequences can decrement, cycle or be reset; allocated values do not imply commit ordering. | Atomically allocates the next configured sequence value; gaps are possible and order is not transaction commit order | https://www.postgresql.org/docs/18/functions-sequence.html | Strict gate passed |
| pg-m266 | An atomic coordinated online filesystem snapshot can be crash-consistent without stopping or freezing the database server. | It needs a consistent cluster-wide copy: stop the server or use a coordinated atomic snapshot including required WAL; an ordinary partial file copy is | https://www.postgresql.org/docs/18/backup-file.html | Strict gate passed |
| pg-m269 | ON CONFLICT DO NOTHING without a target does not require the claimed matching target index. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/sql-insert.html | Strict gate passed |
| pg-m272 | DISTINCT ON can sort by extra unselected expressions; the blanket DISTINCT restriction was wrong. | An ordinary SELECT can; DISTINCT and set operations impose specific restrictions, while DISTINCT ON can still use additional unselected sort keys | https://www.postgresql.org/docs/18/sql-select.html | Strict gate passed |
| pg-m281 | The original question conflated RANGE offset semantics with peer handling at CURRENT ROW. | ROWS stops at the current physical row; RANGE includes every peer with the same ORDER BY values at that boundary | https://www.postgresql.org/docs/18/sql-expressions.html | Strict gate passed |
| pg-m289 | DEFERRABLE can initially wait, and backups were a defensible distractor. | A long read-only serializable transaction may wait initially for a safe snapshot, then avoid serialization-abort overhead for that snapshot | https://www.postgresql.org/docs/18/transaction-iso.html | Strict gate passed |
| pg-m294 | Implicit pg_catalog/temporary-schema lookup was omitted from a blanket resolution claim. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/ddl-schemas.html | Strict gate passed |
| pg-m304 | LIKE INCLUDING ALL does not copy foreign-key constraints. | A new empty table copying columns and all supported LIKE options, including defaults, CHECK constraints and indexes; foreign keys are not copied | https://www.postgresql.org/docs/18/sql-createtable.html | Strict gate passed |
| pg-m306 | Existing rows under NOT VALID are unverified, not trusted as valid. | It enforces the constraint on new or changed rows; existing rows remain unverified until VALIDATE CONSTRAINT checks them | https://www.postgresql.org/docs/18/sql-altertable.html | Strict gate passed |
| pg-s034 | The prompt demanded a single employee while also requiring all salary ties. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/functions-window.html | Strict gate passed |
| pg-s035 | Skipping NULL totals was ambiguous about retaining the corresponding order rows and a zero denominator. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/functions-conditional.html | Strict gate passed |
| pg-s036 | The prompt gave two different names for the same output count. | State the required assumptions explicitly; synchronize the Vietnamese prompt. | https://www.postgresql.org/docs/18/functions-aggregate.html | Strict gate passed |
| pg-s045 | The explanation incorrectly generalized one-based array bounds to every PostgreSQL array. | These fixtures use ordinary one-based arrays | https://www.postgresql.org/docs/18/arrays.html | Strict gate passed |
| pg-s050 | NULL alone does not distinguish a grand-total row from a real NULL grouping key. | ROLLUP(status) produces (status) and () | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| pg-s053 | split_part returns an empty string, not NULL, for a missing second word; the answer added a trailing dot and omitted later words. | Split all words with ordinality; aggregate initials without a trailing separator. | https://www.postgresql.org/docs/18/functions-string.html | Strict gate passed |
| pg-s056 | Manager IDs were compared to department IDs, not employee IDs; the primary fixture returned no rows. | Compare mgr_id with employees.id; add an orphan; save actual reference outputs. | https://www.postgresql.org/docs/18/functions-subquery.html | Strict gate passed |
| pg-e001 | MVCC does not remove every lock conflict; DELETE does not create a replacement tuple. | MVCC uses row versions and snapshot visibility; ordinary reads avoid conflicting writer row locks, but explicit row locking and DDL can still wait. | https://www.postgresql.org/docs/18/routine-vacuuming.html | Strict gate passed |
| pg-e005 | jsonb can still have CHECK/expression constraints and indexes; integrity was categorically ruled out. | jsonb can enforce selected rules with CHECK, expression indexes and generated columns; compare actual integrity needs with document flexibility. | https://www.postgresql.org/docs/18/datatype-json.html | Strict gate passed |
| pg-e009 | Asynchronous WAL archiving alone cannot guarantee near-zero data loss. | PITR needs a base backup and continuous WAL; asynchronous archiving leaves a loss window, and near-zero RPO needs additional durable off-host acknowle | https://www.postgresql.org/docs/18/backup.html | Strict gate passed |
| pg-e011 | CTE inlining qualifications were missing, and performance equivalence was stated too strongly. | CTE folding depends on recursion, side effects, volatile functions, reference count and MATERIALIZED/NOT MATERIALIZED directives. | https://www.postgresql.org/docs/18/queries-with.html | Strict gate passed |
| pg-e013 | SKIP LOCKED was suggested for account transfers without warning that required rows cannot be skipped. | Consistent lock ordering and full-transaction retry help with deadlocks; SKIP LOCKED must not omit required transfer accounts. | https://www.postgresql.org/docs/18/explicit-locking.html | Strict gate passed |
| pg-e014 | Sequential identity values were ambiguous about gaps, and DEFAULT is permitted on generated columns. | IDENTITY/serial do not replace UNIQUE/PRIMARY KEY and permit gaps; generated columns accept DEFAULT but not an explicit computed value. | https://www.postgresql.org/docs/18/ddl-generated-columns.html | Strict gate passed |
| pg-e016 | An integer room identifier needs an equality GiST operator class, commonly supplied by btree_gist. | Exclusion constraints need operator classes for room equality and span overlap; integers commonly need btree_gist, and business nullability may need N | https://www.postgresql.org/docs/18/btree-gist.html | Strict gate passed |
| pg-e017 | Domain casts were said to ignore checks rather than distinguishing base-type results and conversion back. | Conversion into a domain checks its constraint; operators yield base-typed results, and casting back rechecks CHECK. | https://www.postgresql.org/docs/18/domains.html | Strict gate passed |
| pg-e018 | Sequential bigint identifiers were described as opaque, and natural-key index savings as unconditional. | Sequential bigint identifiers are enumerable; a surrogate is neither a secret nor authorization, and does not remove the business uniqueness requireme | https://www.postgresql.org/docs/18/ddl-constraints.html | Strict gate passed |
| pg-e019 | The sample counted reads as writes and treated mandatory audit work as optionally discardable. | Required transfer and audit work belong in one transaction; a savepoint must not allow a mandatory step to be silently omitted. | https://www.postgresql.org/docs/18/mvcc-intro.html | Strict gate passed |
| pg-e020 | Upsert was incorrectly said to prevent all concurrent errors and lost business updates. | Atomic upsert covers the chosen conflict target; other constraints, deadlocks, serialization failures and stale application calculations remain possib | https://www.postgresql.org/docs/18/sql-merge.html | Strict gate passed |
| pg-e021 | Schema/sequence privileges and membership-level inheritance were omitted from least-privilege guidance. | Least privilege includes schema USAGE, table and sequence grants, and the actual creating role; the application must not be able to SET ROLE to the ow | https://www.postgresql.org/docs/18/role-membership.html | Strict gate passed |
| pg-e024 | EXECUTE was wrongly listed as updating FOUND; ON CONFLICT predates PostgreSQL 15. | EXECUTE does not change FOUND; GET DIAGNOSTICS ROW_COUNT reports its row count | https://www.postgresql.org/docs/18/plpgsql-statements.html | Strict gate passed |
| pg-e025 | Extended statistics were presented as a general cross-table join-selectivity fix and a plan change was guaranteed. | Extended statistics describe columns in the same table; they are not a general fix for cross-table JOIN estimates and cannot guarantee a specific plan | https://www.postgresql.org/docs/18/using-explain.html | Strict gate passed |
| pg-e026 | The answer ignored narrower-index tradeoffs and PostgreSQL 18 B-tree skip scan. | Compare index size, cache use, UNIQUE requirements and plans; PostgreSQL 18 can sometimes use skip scan, which is not assumed in the PostgreSQL 17 san | https://www.postgresql.org/docs/18/indexes-multicolumn.html | Strict gate passed |
| pg-e027 | A staged type migration still needs bounded DDL locks and cannot promise literal zero locking. | Expand/backfill/contract can reduce blocking, but DDL still needs short locks; bound lock waits, retries and rollback plans. | https://www.postgresql.org/docs/18/sql-altertable.html | Strict gate passed |
| pg-e028 | Implicit temporary-schema lookup and the SECURITY DEFINER pg_temp ordering requirement were omitted. | SECURITY DEFINER needs a trusted search_path, qualified objects, appropriate pg_temp ordering and reviewed execution rights. | https://www.postgresql.org/docs/18/ddl-schemas.html | Strict gate passed |
| pg-e031 | UNION cycle handling depends on complete-row equality; SEARCH does not force traversal execution order. | UNION compares complete rows, so a changing depth/path can defeat deduplication | https://www.postgresql.org/docs/18/queries-with.html | Strict gate passed |
| pg-e032 | Not every transaction consumes an assigned XID; read-only transactions may never need one. | Read-only transactions need not receive a normal XID | https://www.postgresql.org/docs/18/routine-vacuuming.html | Strict gate passed |
| pg-e033 | Recovery was described as physical rollback of uncommitted pages, and checkpoint REDO position was oversimplified. | Recovery replays WAL from a checkpoint REDO position; changes without a durable commit do not become visible committed data through physical page undo | https://www.postgresql.org/docs/18/wal-intro.html | Strict gate passed |
| pg-e038 | The sample incorrectly claimed PostgreSQL COALESCE normally evaluates a subquery twice. | COALESCE/CASE normally evaluate only required runtime branches; early planning/aggregate errors and the business distinction between NULL and zero sti | https://www.postgresql.org/docs/18/functions-conditional.html | Strict gate passed |
| pg-e039 | ILIKE was incorrectly said not to change B-tree indexability; a lower-expression index needs a matching query expression. | A lower(name) index needs a matching query expression and operator class; an unchanged ILIKE predicate does not automatically use it | https://www.postgresql.org/docs/18/indexes-types.html | Strict gate passed |
| pg-e040 | Arrays preserve order and support element assignment; those capabilities were incorrectly said to be lost. | Arrays preserve order, duplicate values and subscript assignment; relational constraints and independent lifecycle may favor child rows, since editing | https://www.postgresql.org/docs/18/functions-array.html | Strict gate passed |
| pg-e041 | Procedure transaction control is restricted to permitted call contexts. | CALL does not universally permit COMMIT; check the call chain, explicit transaction block, SECURITY DEFINER and SET context. | https://www.postgresql.org/docs/18/plpgsql-transactions.html | Strict gate passed |
| pg-e045 | A missing/reset tenant GUC can error or be empty; a user-settable GUC is not an independent trust boundary. | Trusted SET LOCAL context must follow authentication; handle missing/empty tenant values and pooled reuse | https://www.postgresql.org/docs/18/role-attributes.html | Strict gate passed |
| pg-s001 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/tutorial-join.html | Strict gate passed |
| pg-s002 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| pg-s005 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-aggregate.html | Strict gate passed |
| pg-s007 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-subquery.html | Strict gate passed |
| pg-s009 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-subquery.html | Strict gate passed |
| pg-s010 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-union.html | Strict gate passed |
| pg-s011 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-union.html | Strict gate passed |
| pg-s012 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-union.html | Strict gate passed |
| pg-s015 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-comparison.html | Strict gate passed |
| pg-s017 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-select-lists.html | Strict gate passed |
| pg-s020 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-limit.html | Strict gate passed |
| pg-s023 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-matching.html | Strict gate passed |
| pg-s024 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-matching.html | Strict gate passed |
| pg-s025 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-with.html | Strict gate passed |
| pg-s026 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-with.html | Strict gate passed |
| pg-s041 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-datetime.html | Strict gate passed |
| pg-s042 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/datatype-json.html | Strict gate passed |
| pg-s043 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/datatype-json.html | Strict gate passed |
| pg-s044 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/arrays.html | Strict gate passed |
| pg-s046 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| pg-s048 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |
| pg-s055 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/functions-subquery.html | Strict gate passed |
| pg-s057 | Empty edge output did not meet the nonempty served-fixture requirement | Apply the recorded source correction. Retain negative rows, add qualifying boundary rows, compute both expected grids in PostgreSQL. | https://www.postgresql.org/docs/18/queries-table-expressions.html | Strict gate passed |

| case-db-2nf-easy-1-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-1-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-1-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-2-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-2-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-2-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-3-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-3-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-3-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-4-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-4-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-4-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-5-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-5-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-5-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-6-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-6-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-6-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-7-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-7-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-easy-7-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-1-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-1-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-1-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-2-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-2-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-2-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-3-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-3-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-3-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-4-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-4-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-4-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-5-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-5-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-5-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-6-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-6-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-6-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-7-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-7-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-hard-7-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-1-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-1-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-1-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-2-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-2-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-2-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-3-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-3-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-3-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-4-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-4-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-4-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-5-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-5-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-5-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-6-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-6-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-6-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-7-essay | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-7-mcq | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |
| case-db-2nf-medium-7-sql | Composite candidate key described, but id alone was the primary key | Declare PRIMARY KEY(grp,id); regenerate real PostgreSQL grids | https://www.postgresql.org/docs/18/ddl-constraints.html | Composite-key SQL regression passed |

Source milestone: **442 before / 442 after**, **121 corrected definitions**,
**326 MCQ / 67 SQL / 49 essay**. IDs/MCQ labels and correct flags are retained.
The historical before-definitions and translations are in
`db/reviewed_question_before.json`; the historical three-band assertions remain
and now read that explicit fixture. Stored learner history has not been edited.
The three previously unmapped foundation aliases now have a source CLO mapping;
existing attempt CLO context remains snapshotted.

- Initial new regression: **4 failed / 18 passed**, 16.47s; 121 source flags
  included real missing metadata and an overly narrow language word list.
- Broader content/import/history regression: **162/162**, 203.93s, before the
  final three MCQ clarifications. Final corpus + executable semantics:
  **41/41**, 18.86s, including those clarifications.
- Current structural validator: **442/442** valid; translation validator:
  **442/442**, 326/326 option sets, **0** missing/extra/English-prose/duplicate
  or integrity errors. Builder check, backend lint/build pass.
- SQL: **67/67**, **134 fixtures**, each reference checked twice by
  `test_every_source_sql_has_nonempty_primary_and_executes_repeatably`.
  **0** invalid primary results at that milestone. Later tightening rejects every empty edge output too; original empty-input behavior is retained in separate regression tests.
- `test_initials_reference_handles_one_many_and_repeated_space_words` and
  `test_orphan_manager_reference_uses_employees_not_departments` were red and
  now pass against real PostgreSQL. All 14 native semantic probes are in
  `tests/dn/test_reviewed_postgres_semantics.py`.
- CI now explicitly runs `manage.py validate-bank`; full backend tests execute
  the real SQL checks. Current pushed-HEAD CI still needs verification.

**Earlier milestone limitations:** coverage and safe seeding were subsequently completed below. Exact-count and final runtime gates remain in progress. Formal
normal-form reasoning uses explicit dependencies; PostgreSQL's planner/constraint
pages supply implementation context rather than a complete normal-form textbook.

## Before/after coverage

Counts are active source questions; multi-concept questions count in each tagged
concept. Each cell is **MCQ / SQL / essay**. Target is 7 / 7 / 7.

| Concept | Dễ | Vừa | Khó | After E | After M | After H |
| --- | --- | --- | --- | --- | --- | --- |
| DB-1NF | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 8 |
| DB-2NF | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 8 |
| DB-3NF | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 8 |
| DB-ER | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 8 |
| DB-FD | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 8 |
| DB-NORM | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 8 |
| IDX | 0 / 0 / 0 | 0 / 0 / 1 | 0 / 0 / 0 | 7 / 7 / 7 | 7 / 7 / 8 | 7 / 7 / 7 |
| JOIN | 1 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |
| PG-AGG-FUNC | 4 / 2 / 0 | 3 / 4 / 0 | 1 / 3 / 0 | 11 / 9 / 7 | 10 / 11 / 7 | 8 / 10 / 7 |
| PG-ALTER | 1 / 0 / 0 | 1 / 0 / 0 | 0 / 0 / 1 | 8 / 7 / 7 | 8 / 7 / 7 | 7 / 7 / 8 |
| PG-BACKUP | 1 / 0 / 0 | 3 / 0 / 0 | 1 / 0 / 1 | 8 / 7 / 7 | 10 / 7 / 7 | 8 / 7 / 8 |
| PG-CASE | 4 / 1 / 0 | 1 / 1 / 1 | 0 / 0 / 0 | 11 / 8 / 7 | 8 / 8 / 8 | 7 / 7 / 7 |
| PG-COLLATION | 0 / 0 / 0 | 2 / 0 / 0 | 1 / 0 / 0 | 7 / 7 / 7 | 9 / 7 / 7 | 8 / 7 / 7 |
| PG-CONFIG | 2 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 9 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-CONSTRAINT | 3 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 | 10 / 7 / 7 | 9 / 7 / 8 | 8 / 7 / 7 |
| PG-CTE | 2 / 1 / 0 | 2 / 2 / 1 | 2 / 0 / 0 | 9 / 8 / 7 | 9 / 9 / 8 | 9 / 7 / 7 |
| PG-DISTINCT | 3 / 1 / 0 | 2 / 1 / 0 | 0 / 0 / 0 | 10 / 8 / 7 | 9 / 8 / 7 | 7 / 7 / 7 |
| PG-DML | 4 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 | 11 / 7 / 7 | 9 / 7 / 8 | 8 / 7 / 7 |
| PG-DOMAIN | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 7 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-EXPLAIN | 2 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 2 | 9 / 7 / 7 | 9 / 7 / 7 | 9 / 7 / 9 |
| PG-EXPR | 5 / 0 / 0 | 5 / 0 / 1 | 0 / 0 / 0 | 12 / 7 / 7 | 12 / 7 / 8 | 7 / 7 / 7 |
| PG-FTS | 0 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 1 | 7 / 7 / 7 | 9 / 7 / 7 | 9 / 7 / 8 |
| PG-FUNC-DATE | 3 / 0 / 0 | 1 / 3 / 0 | 0 / 2 / 0 | 10 / 7 / 7 | 8 / 10 / 7 | 7 / 9 / 7 |
| PG-FUNC-NUM | 3 / 2 / 0 | 1 / 1 / 0 | 0 / 0 / 0 | 10 / 9 / 7 | 8 / 8 / 7 | 7 / 7 / 7 |
| PG-FUNC-STR | 5 / 1 / 0 | 1 / 3 / 0 | 0 / 0 / 0 | 12 / 8 / 7 | 8 / 10 / 7 | 7 / 7 / 7 |
| PG-GENCOL | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 7 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-IDENTITY | 1 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 | 8 / 7 / 7 | 9 / 7 / 8 | 8 / 7 / 7 |
| PG-INDEX | 2 / 0 / 0 | 3 / 0 / 2 | 2 / 0 / 1 | 9 / 7 / 7 | 10 / 7 / 9 | 9 / 7 / 8 |
| PG-INDEX-TYPES | 0 / 0 / 0 | 2 / 0 / 1 | 3 / 0 / 0 | 7 / 7 / 7 | 9 / 7 / 8 | 10 / 7 / 7 |
| PG-ISOLATION | 1 / 0 / 0 | 3 / 0 / 0 | 3 / 0 / 1 | 8 / 7 / 7 | 10 / 7 / 7 | 10 / 7 / 8 |
| PG-JOIN-TYPES | 6 / 2 / 0 | 3 / 3 / 1 | 1 / 2 / 0 | 13 / 9 / 7 | 10 / 10 / 8 | 8 / 9 / 7 |
| PG-KEYS | 3 / 0 / 0 | 2 / 0 / 2 | 0 / 0 / 0 | 10 / 7 / 7 | 9 / 7 / 9 | 7 / 7 / 7 |
| PG-LIMIT | 3 / 1 / 0 | 1 / 1 / 0 | 0 / 0 / 0 | 10 / 8 / 7 | 8 / 8 / 7 | 7 / 7 / 7 |
| PG-LOCK | 1 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 1 | 8 / 7 / 7 | 9 / 7 / 7 | 9 / 7 / 8 |
| PG-MATVIEW | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 7 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-MERGE | 0 / 0 / 0 | 1 / 0 / 0 | 1 / 0 / 0 | 7 / 7 / 7 | 8 / 7 / 7 | 8 / 7 / 7 |
| PG-MONITOR | 1 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 8 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-MVCC | 1 / 0 / 0 | 3 / 0 / 1 | 1 / 0 / 1 | 8 / 7 / 7 | 10 / 7 / 8 | 8 / 7 / 8 |
| PG-NULLS | 5 / 0 / 0 | 2 / 6 / 1 | 0 / 1 / 0 | 12 / 7 / 7 | 9 / 13 / 8 | 7 / 8 / 7 |
| PG-ORDERBY | 3 / 2 / 0 | 2 / 1 / 0 | 0 / 0 / 0 | 10 / 9 / 7 | 9 / 8 / 7 | 7 / 7 / 7 |
| PG-PARTITION | 0 / 0 / 0 | 2 / 0 / 0 | 3 / 0 / 1 | 7 / 7 / 7 | 9 / 7 / 7 | 10 / 7 / 8 |
| PG-PATTERN | 3 / 0 / 0 | 2 / 1 / 1 | 0 / 0 / 0 | 10 / 7 / 7 | 9 / 8 / 8 | 7 / 7 / 7 |
| PG-PLPGSQL | 1 / 0 / 0 | 3 / 0 / 1 | 3 / 0 / 0 | 8 / 7 / 7 | 10 / 7 / 8 | 10 / 7 / 7 |
| PG-PRIVILEGE | 1 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 1 | 8 / 7 / 7 | 9 / 7 / 8 | 8 / 7 / 8 |
| PG-PROC | 0 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 7 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-RECURSIVE | 0 / 0 / 0 | 2 / 0 / 0 | 2 / 3 / 1 | 7 / 7 / 7 | 9 / 7 / 7 | 9 / 10 / 8 |
| PG-REPLICATION | 0 / 0 / 0 | 2 / 0 / 0 | 3 / 0 / 1 | 7 / 7 / 7 | 9 / 7 / 7 | 10 / 7 / 8 |
| PG-RLS | 0 / 0 / 0 | 2 / 0 / 0 | 2 / 0 / 2 | 7 / 7 / 7 | 9 / 7 / 7 | 9 / 7 / 9 |
| PG-ROLES | 2 / 0 / 0 | 3 / 0 / 1 | 1 / 0 / 1 | 9 / 7 / 7 | 10 / 7 / 8 | 8 / 7 / 8 |
| PG-SCHEMA | 2 / 0 / 0 | 1 / 0 / 1 | 1 / 0 / 0 | 9 / 7 / 7 | 8 / 7 / 8 | 8 / 7 / 7 |
| PG-SELECT-LIST | 5 / 3 / 0 | 0 / 10 / 0 | 0 / 4 / 0 | 12 / 10 / 7 | 7 / 17 / 7 | 7 / 11 / 7 |
| PG-SETOPS | 4 / 1 / 0 | 3 / 2 / 0 | 1 / 0 / 0 | 11 / 8 / 7 | 10 / 9 / 7 | 8 / 7 / 7 |
| PG-STATS | 0 / 0 / 0 | 1 / 0 / 0 | 2 / 0 / 2 | 7 / 7 / 7 | 8 / 7 / 7 | 9 / 7 / 9 |
| PG-SYNTAX | 4 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 11 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |
| PG-TABLE | 4 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 11 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-TRIGGER | 1 / 0 / 0 | 3 / 0 / 1 | 2 / 0 / 0 | 8 / 7 / 7 | 10 / 7 / 8 | 9 / 7 / 7 |
| PG-TXN | 3 / 0 / 0 | 2 / 0 / 2 | 1 / 0 / 0 | 10 / 7 / 7 | 9 / 7 / 9 | 8 / 7 / 7 |
| PG-TYPE-ARRAY | 2 / 0 / 0 | 3 / 2 / 1 | 0 / 1 / 0 | 9 / 7 / 7 | 10 / 9 / 8 | 7 / 8 / 7 |
| PG-TYPE-BOOL | 3 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 10 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |
| PG-TYPE-CHAR | 3 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 10 / 7 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |
| PG-TYPE-DATE | 2 / 0 / 0 | 3 / 0 / 1 | 0 / 0 / 0 | 9 / 7 / 7 | 10 / 7 / 8 | 7 / 7 / 7 |
| PG-TYPE-JSON | 2 / 0 / 0 | 4 / 1 / 1 | 1 / 1 / 1 | 9 / 7 / 7 | 11 / 8 / 8 | 8 / 8 / 8 |
| PG-TYPE-MISC | 2 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 9 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-TYPE-NUM | 4 / 0 / 0 | 1 / 0 / 0 | 0 / 0 / 0 | 11 / 7 / 7 | 8 / 7 / 7 | 7 / 7 / 7 |
| PG-TYPE-RANGE | 0 / 0 / 0 | 2 / 0 / 0 | 1 / 0 / 0 | 7 / 7 / 7 | 9 / 7 / 7 | 8 / 7 / 7 |
| PG-TYPECONV | 1 / 0 / 0 | 2 / 0 / 1 | 1 / 0 / 0 | 8 / 7 / 7 | 9 / 7 / 8 | 8 / 7 / 7 |
| PG-UDF | 1 / 0 / 0 | 3 / 0 / 1 | 2 / 0 / 1 | 8 / 7 / 7 | 10 / 7 / 8 | 9 / 7 / 8 |
| PG-VACUUM | 1 / 0 / 0 | 3 / 0 / 1 | 2 / 0 / 1 | 8 / 7 / 7 | 10 / 7 / 8 | 9 / 7 / 8 |
| PG-VIEW | 1 / 0 / 0 | 2 / 0 / 1 | 0 / 0 / 0 | 8 / 7 / 7 | 9 / 7 / 8 | 7 / 7 / 7 |
| PG-WAL | 0 / 0 / 0 | 1 / 0 / 1 | 2 / 0 / 1 | 7 / 7 / 7 | 8 / 7 / 8 | 9 / 7 / 8 |
| PG-WINDOW | 3 / 0 / 0 | 3 / 3 / 1 | 3 / 2 / 0 | 10 / 7 / 7 | 10 / 10 / 8 | 10 / 9 / 7 |
| SELECT | 1 / 1 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 8 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |
| SQL-DDL-KNOW | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 8 | 7 / 7 / 7 | 7 / 7 / 7 |
| SQL-DML-KNOW | 1 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 7 / 8 | 7 / 7 / 7 | 7 / 7 / 7 |
| SQL-GROUP | 1 / 3 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 10 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |
| SQL-HAVING | 1 / 1 / 0 | 0 / 1 / 0 | 0 / 0 / 0 | 8 / 8 / 7 | 7 / 8 / 7 | 7 / 7 / 7 |
| SQL-JOIN | 1 / 3 / 0 | 0 / 1 / 0 | 0 / 0 / 0 | 8 / 10 / 7 | 7 / 8 / 7 | 7 / 7 / 7 |
| SQL-SELECT | 1 / 1 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 8 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |
| SQL-SUBQUERY | 1 / 3 / 0 | 0 / 2 / 0 | 0 / 1 / 0 | 8 / 10 / 7 | 7 / 9 / 7 | 7 / 8 / 7 |
| SQL-WHERE | 1 / 1 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 8 / 8 / 7 | 7 / 7 / 7 | 7 / 7 / 7 |

Before: of 720 cells, 719 were below quota and 450 were empty. After: all 720 meet quota, none empty. Canonical duplicate prompts: 0.

## Complete case corpus and safe initialization

After: **5,482 = 2,006 MCQ / 1,747 SQL / 1,729 essay**; 5,040 new native-Vietnamese case questions, 80 concepts. Each of 720 cells has at least **7**, derived as ceil(max 20 / 3 types); the table gives raw active counts. Seven input classes cover NULL, ties/duplicates, thresholds, rounding, whitespace, Unicode/quoting and missing JSON/array values. Questions apply explicit concept-specific rules to real data; operational topics analyse labelled controlled snapshots, never cluster internals or privileged commands. No numbered description filler.

Expected grids in `practice_template_results.json` are bound to SHA-256(setup + query), obtained through **6,056 actual PostgreSQL executions / 292.263s**, twice per distinct fixture/query; identical pairs reused. The manifest includes all 67 original SQL questions (266 additional executions; one shared fixture/query pair reused). CI's whole-corpus test independently reruns every SQL question and fixture; initialization only accepts matching verified grids. A changed query/fixture needs a new executed manifest. Static gate: **5,482/5,482**, no duplicate canonical prompts or invalid items. All new metadata has versioned official URLs; seven additional official pages fetched successfully. Normal-form theory is checked separately by dependency closure and a lossless SQL reconstruction, since the PG manual is not a normative normal-form textbook.

Safe seed/coverage suite: **11/11, 56.32s**, including complete seed, all 80 concepts mapped to confirmed CLOs, repeat initialization, owner edit preservation, unused ID stability, referenced-question versioning with unchanged score/snapshot, and preflight rejection before writes. Independent full SQL/content retest: **41/41, 436.78s**, all 1,747 SQL / 3,494 fixtures executed twice (6,988 executions), zero mismatches, nondeterministic results or invalid primary outputs. No persistent learner database has been modified. Central limits now live in `practice_config.py`; API/UI adoption follows in the exact-count milestone.

Strict nonempty-fixture follow-up: **30 red** before repair; **57/57** content/SQL/seed/history tests pass, **422.45s**. Every one of **3,494 served SQL fixtures** now has a nonempty deterministic output. `test_original_empty_input_sql_behavior_remains_covered_separately` executes all **30** original negative fixtures; no empty-data behavior test was removed. `test_registered_source_revision_preserves_history_and_local_edits` proves subsequent registered revisions preserve history and administrator edits. Additional repair validation executed both fixtures twice for all 30 changed SQL questions (**120 executions**); manifest regeneration added 60 new fixture/query executions. Localization **442/442**, zero errors; builder check/lint/build pass. No real-provider calls.

Latest review: **184 changed definitions** (121 original + 63 DB-2NF case variants), each ID listed above and retained in the before/fix manifests. Composite-key semantic and complete-seed suite **25/25, 7.58s**. Manifest now **6,140 actual PostgreSQL executions / 296.475s**, including 84 new executions / 4.212s for the corrected key. Shared SQL reference guard reproduced **11 failures**, then passed within **41/41, 25.02s**: rejects schema/user/database/clock-dependent expressions while accepting quoted instructional examples. Whole-source static check is included.

Owned-stack upgrade preserved full-row hashes for **61 attempts and 7 sessions**; seven referenced corrected questions were versioned, leaving their originals retired. Original external stacks remain untouched. This replaces the earlier statement that no persistent learner database had been changed: only the isolated audit stack was upgraded.

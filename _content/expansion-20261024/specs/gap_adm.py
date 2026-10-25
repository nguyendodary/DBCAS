"""Practice-depth gap fill for A6 Administration.

Formal assessment for this area is blocked because two SQL practicals are
mandatory and the learner sandbox cannot execute EXPLAIN, catalog reads or
configuration changes. These MCQs close the concept gaps that made even
practice mode fail at EASY and HARD.
"""

from lib import mcq
from sources import PG_CONFIG_SETTING, PG_MONITOR, PG_REPLICATION, PG_WAL

QUESTIONS = [
    mcq(
        "adm-easy-wal-purpose",
        ["PG-WAL"],
        2,
        (
            "Why does PostgreSQL write changes to the write-ahead log (WAL)?"
        ),
        [
            "WAL records are flushed before the corresponding data pages, so "
            "committed changes can be redone after a crash.",
            "WAL stores a copy of every query plan so that frequently used "
            "queries skip planning.",
            "WAL is only needed when streaming replication is enabled; a "
            "single server does not use it.",
            "WAL keeps recent rows in memory so that SELECT statements avoid "
            "reading table pages.",
        ],
        0,
        (
            "WAL is the crash-recovery mechanism: change records are written "
            "and flushed before the modified data pages reach disk, so after a "
            "crash the server can replay committed changes. It exists "
            "independently of replication, although replication reuses the same "
            "stream. It is not a plan cache and not a row cache."
        ),
        [PG_WAL],
    ),
    mcq(
        "adm-easy-streaming-standby",
        ["PG-REPLICATION"],
        2,
        (
            "In streaming replication, what does a hot standby server receive "
            "from the primary and what can it do?"
        ),
        [
            "It continuously receives WAL records and applies them, and it can "
            "serve read-only queries while possibly lagging behind the primary.",
            "It receives only a full logical dump of each table at every "
            "checkpoint and cannot serve queries.",
            "It receives the SQL text of SELECT statements and returns their "
            "results to the primary.",
            "It receives committed row versions directly through shared memory "
            "and is always exactly current.",
        ],
        0,
        (
            "Streaming replication ships WAL records from the primary to the "
            "standby, which continuously applies them. A hot standby accepts "
            "read-only queries, and because applying can trail the primary, "
            "replica reads can be slightly stale. There is no shared-memory "
            "row transfer and no per-checkpoint logical dump."
        ),
        [PG_REPLICATION, PG_WAL],
    ),
    mcq(
        "adm-hard-alter-system",
        ["PG-CONFIG"],
        4,
        (
            "What does ALTER SYSTEM SET work_mem = '16MB'; do?"
        ),
        [
            "It writes the setting to postgresql.auto.conf; the new value takes "
            "effect according to the parameter's context, which may require a "
            "reload or a restart.",
            "It edits postgresql.conf in place and applies the value to every "
            "running session immediately.",
            "It changes only the current session and disappears when the "
            "session ends.",
            "It recreates the cluster so that the new value becomes the "
            "compiled default.",
        ],
        0,
        (
            "ALTER SYSTEM stores the override in postgresql.auto.conf, which "
            "is read in addition to postgresql.conf. Whether the running server "
            "picks the value up after a reload or needs a restart depends on "
            "the parameter's context; work_mem is a user-context parameter, so "
            "a reload is enough (sessions adopt the new value before their next "
            "command), while postmaster-context parameters require a restart. A "
            "session-level change would be SET, not ALTER SYSTEM, and the "
            "cluster is never recreated."
        ),
        [PG_CONFIG_SETTING],
    ),
    mcq(
        "adm-hard-pg-stat-activity",
        ["PG-MONITOR"],
        4,
        (
            "Which statement about the pg_stat_activity view is correct?"
        ),
        [
            "It has one row per server process with the current state and query; "
            "an ordinary role generally sees other sessions' query text only "
            "when granted pg_read_all_stats or comparable privileges.",
            "It stores a permanent history of every statement ever executed on "
            "the server.",
            "It reports only the number of rows in each user table and nothing "
            "about sessions.",
            "It shows only autovacuum workers, because client backends are "
            "listed in a separate per-database view.",
        ],
        0,
        (
            "pg_stat_activity is a live, one-row-per-backend view: it reports "
            "the state, wait event and current query of each server process. It "
            "is not historical; statement history requires an extension such as "
            "pg_stat_statements. For privacy, non-superusers see limited "
            "information about other users' sessions unless they have "
            "pg_read_all_stats. Client backends and autovacuum workers both "
            "appear in the same view."
        ),
        [PG_MONITOR],
    ),
]

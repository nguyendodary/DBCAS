"""Verified source references used by the expansion pack.

Each entry records exactly where a rule was read. PostgreSQL facts point at
the 17 documentation; database-theory facts point at academic references and
are never presented as PostgreSQL documentation claims.
"""

RETRIEVED = "2026-10-24"

PG17 = "https://www.postgresql.org/docs/17/"

PG_AGGREGATE = {
    "url": f"{PG17}functions-aggregate.html",
    "version": "17",
    "section": "9.21 Aggregate Functions",
    "title": "Aggregate Functions",
    "retrieved": RETRIEVED,
}

PG_SELECT = {
    "url": f"{PG17}sql-select.html",
    "version": "17",
    "section": "SELECT",
    "title": "SELECT",
    "retrieved": RETRIEVED,
}

PG_TABLE_EXPRESSIONS = {
    "url": f"{PG17}queries-table-expressions.html",
    "version": "17",
    "section": "7.2 Table Expressions (joined tables, GROUP BY, HAVING)",
    "title": "Table Expressions",
    "retrieved": RETRIEVED,
}

PG_JOIN_TUTORIAL = {
    "url": f"{PG17}tutorial-join.html",
    "version": "17",
    "section": "2.6 Joins Between Tables",
    "title": "Joins Between Tables",
    "retrieved": RETRIEVED,
}

PG_UPDATE = {
    "url": f"{PG17}sql-update.html",
    "version": "17",
    "section": "UPDATE",
    "title": "UPDATE",
    "retrieved": RETRIEVED,
}

PG_INSERT = {
    "url": f"{PG17}sql-insert.html",
    "version": "17",
    "section": "INSERT",
    "title": "INSERT",
    "retrieved": RETRIEVED,
}

PG_DELETE = {
    "url": f"{PG17}sql-delete.html",
    "version": "17",
    "section": "DELETE",
    "title": "DELETE",
    "retrieved": RETRIEVED,
}

PG_CREATE_TABLE = {
    "url": f"{PG17}sql-createtable.html",
    "version": "17",
    "section": "CREATE TABLE",
    "title": "CREATE TABLE",
    "retrieved": RETRIEVED,
}

PG_CONSTRAINTS = {
    "url": f"{PG17}ddl-constraints.html",
    "version": "17",
    "section": "5.5 Constraints",
    "title": "Constraints",
    "retrieved": RETRIEVED,
}

PG_COMPARISON = {
    "url": f"{PG17}functions-comparison.html",
    "version": "17",
    "section": "9.2 Comparison Functions and Operators",
    "title": "Comparison Functions and Operators",
    "retrieved": RETRIEVED,
}

PG_EXPRESSIONS = {
    "url": f"{PG17}sql-expressions.html",
    "version": "17",
    "section": "4.2.11 Scalar Subqueries",
    "title": "Value Expressions",
    "retrieved": RETRIEVED,
}

PG_SUBQUERY_FUNCTIONS = {
    "url": f"{PG17}functions-subquery.html",
    "version": "17",
    "section": "9.24 Subquery Expressions",
    "title": "Subquery Expressions",
    "retrieved": RETRIEVED,
}

PG_INDEXES = {
    "url": f"{PG17}indexes-intro.html",
    "version": "17",
    "section": "11.1 Introduction",
    "title": "Indexes",
    "retrieved": RETRIEVED,
}

PG_INDEX_TYPES = {
    "url": f"{PG17}indexes-types.html",
    "version": "17",
    "section": "11.2 Index Types",
    "title": "Index Types",
    "retrieved": RETRIEVED,
}

PG_CREATE_INDEX = {
    "url": f"{PG17}sql-createindex.html",
    "version": "17",
    "section": "CREATE INDEX",
    "title": "CREATE INDEX",
    "retrieved": RETRIEVED,
}

PG_ROUTINE_VACUUM = {
    "url": f"{PG17}routine-vacuuming.html",
    "version": "17",
    "section": "24.1 Routine Vacuuming",
    "title": "Routine Vacuuming",
    "retrieved": RETRIEVED,
}

# Adrienne Watt, Database Design - 2nd Edition (BCcampus, 2014).
# Verified record at the Open Textbook Library; chapters 11-12 cover
# functional dependencies and first/second/third normal form.
WATT_DB_DESIGN = {
    "url": "https://open.umn.edu/opentextbooks/textbooks/354",
    "version": "2nd edition",
    "section": "Chapters 11-12: Functional Dependencies; Normalization",
    "title": "Database Design - 2nd Edition (Adrienne Watt, BCcampus)",
    "retrieved": RETRIEVED,
}

# E. F. Codd, "Further Normalization of the Data Base Relational Model",
# IBM Research Report RJ909 (1971). Stable bibliographic record.
CODD_1971 = {
    "url": "https://dblp.org/rec/persons/Codd71a",
    "version": "1971",
    "section": "IBM Research Report RJ909",
    "title": "Further Normalization of the Data Base Relational Model",
    "retrieved": RETRIEVED,
}

# P. P.-S. Chen, "The Entity-Relationship Model - Toward a Unified View of
# Data", ACM TODS 1(1), 1976. DOI record for the ER model's original paper.
CHEN_1976 = {
    "url": "https://doi.org/10.1145/320434.320440",
    "version": "1976",
    "section": "ACM Transactions on Database Systems 1(1), 9-36",
    "title": "The Entity-Relationship Model - Toward a Unified View of Data",
    "retrieved": RETRIEVED,
}

PG_QUERIES_WITH = {
    "url": f"{PG17}queries-with.html",
    "version": "17",
    "section": "7.8 WITH Queries (Common Table Expressions)",
    "title": "WITH Queries",
    "retrieved": RETRIEVED,
}

PG_ARRAYS = {
    "url": f"{PG17}arrays.html",
    "version": "17",
    "section": "8.15 Arrays",
    "title": "Arrays",
    "retrieved": RETRIEVED,
}

PG_FUNCTIONS_STRING = {
    "url": f"{PG17}functions-string.html",
    "version": "17",
    "section": "9.4 String Functions and Operators",
    "title": "String Functions and Operators",
    "retrieved": RETRIEVED,
}

PG_FUNCTIONS_MATH = {
    "url": f"{PG17}functions-math.html",
    "version": "17",
    "section": "9.3 Mathematical Functions and Operators",
    "title": "Mathematical Functions and Operators",
    "retrieved": RETRIEVED,
}

PG_FUNCTIONS_DATE = {
    "url": f"{PG17}functions-datetime.html",
    "version": "17",
    "section": "9.9 Date/Time Functions and Operators",
    "title": "Date/Time Functions and Operators",
    "retrieved": RETRIEVED,
}

PG_PATTERN = {
    "url": f"{PG17}functions-matching.html",
    "version": "17",
    "section": "9.7 Pattern Matching",
    "title": "Pattern Matching",
    "retrieved": RETRIEVED,
}

PG_TEXTSEARCH = {
    "url": f"{PG17}textsearch.html",
    "version": "17",
    "section": "12 Full Text Search",
    "title": "Full Text Search",
    "retrieved": RETRIEVED,
}

PG_TYPE_NUM = {
    "url": f"{PG17}datatype-numeric.html",
    "version": "17",
    "section": "8.1 Numeric Types",
    "title": "Numeric Types",
    "retrieved": RETRIEVED,
}

PG_TYPE_CHAR = {
    "url": f"{PG17}datatype-character.html",
    "version": "17",
    "section": "8.3 Character Types",
    "title": "Character Types",
    "retrieved": RETRIEVED,
}

PG_TYPE_BOOL = {
    "url": f"{PG17}datatype-boolean.html",
    "version": "17",
    "section": "8.6 Boolean Type",
    "title": "Boolean Type",
    "retrieved": RETRIEVED,
}

PG_TYPE_DATE = {
    "url": f"{PG17}datatype-datetime.html",
    "version": "17",
    "section": "8.5 Date/Time Types",
    "title": "Date/Time Types",
    "retrieved": RETRIEVED,
}

PG_TYPE_JSON = {
    "url": f"{PG17}datatype-json.html",
    "version": "17",
    "section": "8.14 JSON Types",
    "title": "JSON Types",
    "retrieved": RETRIEVED,
}

PG_TYPE_RANGE = {
    "url": f"{PG17}rangetypes.html",
    "version": "17",
    "section": "8.17 Range Types",
    "title": "Range Types",
    "retrieved": RETRIEVED,
}

PG_TYPE_ENUM = {
    "url": f"{PG17}datatype-enum.html",
    "version": "17",
    "section": "8.7 Enumerated Types",
    "title": "Enumerated Types",
    "retrieved": RETRIEVED,
}

PG_TYPE_UUID = {
    "url": f"{PG17}datatype-uuid.html",
    "version": "17",
    "section": "8.12 UUID Type",
    "title": "UUID Type",
    "retrieved": RETRIEVED,
}

PG_TYPECONV = {
    "url": f"{PG17}typeconv-oper.html",
    "version": "17",
    "section": "10.2 Operators",
    "title": "Operators",
    "retrieved": RETRIEVED,
}

PG_COLLATION = {
    "url": f"{PG17}collation.html",
    "version": "17",
    "section": "23.2 Collation Support",
    "title": "Collation Support",
    "retrieved": RETRIEVED,
}

PG_DOMAIN = {
    "url": f"{PG17}domains.html",
    "version": "17",
    "section": "8.18 Domain Types",
    "title": "Domain Types",
    "retrieved": RETRIEVED,
}

PG_DDL = {
    "url": f"{PG17}ddl.html",
    "version": "17",
    "section": "5 Data Definition",
    "title": "Data Definition",
    "retrieved": RETRIEVED,
}

PG_IDENTITY = {
    "url": f"{PG17}ddl-identity-columns.html",
    "version": "17",
    "section": "5.3 Identity Columns",
    "title": "Identity Columns",
    "retrieved": RETRIEVED,
}

PG_GENCOL = {
    "url": f"{PG17}ddl-generated-columns.html",
    "version": "17",
    "section": "5.4 Generated Columns",
    "title": "Generated Columns",
    "retrieved": RETRIEVED,
}

PG_ALTER = {
    "url": f"{PG17}sql-altertable.html",
    "version": "17",
    "section": "ALTER TABLE",
    "title": "ALTER TABLE",
    "retrieved": RETRIEVED,
}

PG_SCHEMA = {
    "url": f"{PG17}ddl-schemas.html",
    "version": "17",
    "section": "5.10 Schemas",
    "title": "Schemas",
    "retrieved": RETRIEVED,
}

PG_VIEW = {
    "url": f"{PG17}sql-createview.html",
    "version": "17",
    "section": "CREATE VIEW",
    "title": "CREATE VIEW",
    "retrieved": RETRIEVED,
}

PG_MATVIEW = {
    "url": f"{PG17}sql-creatematerializedview.html",
    "version": "17",
    "section": "CREATE MATERIALIZED VIEW",
    "title": "CREATE MATERIALIZED VIEW",
    "retrieved": RETRIEVED,
}

PG_PARTITION = {
    "url": f"{PG17}ddl-partitioning.html",
    "version": "17",
    "section": "5.11 Table Partitioning",
    "title": "Table Partitioning",
    "retrieved": RETRIEVED,
}

PG_MERGE = {
    "url": f"{PG17}sql-merge.html",
    "version": "17",
    "section": "MERGE",
    "title": "MERGE",
    "retrieved": RETRIEVED,
}

PG_TXN = {
    "url": f"{PG17}tutorial-transactions.html",
    "version": "17",
    "section": "3.4 Transactions",
    "title": "Transactions",
    "retrieved": RETRIEVED,
}

PG_ISOLATION = {
    "url": f"{PG17}transaction-iso.html",
    "version": "17",
    "section": "13.2 Transaction Isolation",
    "title": "Transaction Isolation",
    "retrieved": RETRIEVED,
}

PG_MVCC = {
    "url": f"{PG17}mvcc.html",
    "version": "17",
    "section": "13.1 Introduction (MVCC)",
    "title": "Concurrency Control",
    "retrieved": RETRIEVED,
}

PG_LOCK = {
    "url": f"{PG17}explicit-locking.html",
    "version": "17",
    "section": "13.3 Explicit Locking",
    "title": "Explicit Locking",
    "retrieved": RETRIEVED,
}

PG_EXPLAIN = {
    "url": f"{PG17}using-explain.html",
    "version": "17",
    "section": "14.1 Using EXPLAIN",
    "title": "Using EXPLAIN",
    "retrieved": RETRIEVED,
}

PG_STATS = {
    "url": f"{PG17}planner-stats.html",
    "version": "17",
    "section": "14.2 Statistics Used by the Planner",
    "title": "Statistics Used by the Planner",
    "retrieved": RETRIEVED,
}

PG_CONFIG = {
    "url": f"{PG17}runtime-config.html",
    "version": "17",
    "section": "19 Server Configuration",
    "title": "Server Configuration",
    "retrieved": RETRIEVED,
}

PG_BACKUP = {
    "url": f"{PG17}backup-dump.html",
    "version": "17",
    "section": "25.1 SQL Dump",
    "title": "SQL Dump",
    "retrieved": RETRIEVED,
}

PG_BASEBACKUP = {
    "url": f"{PG17}app-pgbasebackup.html",
    "version": "17",
    "section": "pg_basebackup",
    "title": "pg_basebackup",
    "retrieved": RETRIEVED,
}

PG_WAL_CONFIG = {
    "url": f"{PG17}runtime-config-wal.html",
    "version": "17",
    "section": "19.5 Write Ahead Log",
    "title": "Write Ahead Log Configuration",
    "retrieved": RETRIEVED,
}

PG_MONITOR_STATS = {
    "url": f"{PG17}monitoring-stats.html",
    "version": "17",
    "section": "27.2 The Statistics Collector",
    "title": "The Statistics Collector",
    "retrieved": RETRIEVED,
}

PG_MONITOR_ACTIVITY = {
    "url": f"{PG17}monitoring-stats.html",
    "version": "17",
    "section": "27.2.3 Dynamic Statistics Views (pg_stat_activity)",
    "title": "Dynamic Statistics Views",
    "retrieved": RETRIEVED,
}

PG_CLIENT_AUTH = {
    "url": f"{PG17}auth-password.html",
    "version": "17",
    "section": "20.5 Password Authentication",
    "title": "Password Authentication",
    "retrieved": RETRIEVED,
}

PG_WAL = {
    "url": f"{PG17}wal.html",
    "version": "17",
    "section": "28 Write-Ahead Logging (WAL)",
    "title": "Write-Ahead Logging",
    "retrieved": RETRIEVED,
}

PG_REPLICATION = {
    "url": f"{PG17}warm-standby.html",
    "version": "17",
    "section": "26.2 Log-Shipping Standby Servers",
    "title": "Log-Shipping Standby Servers",
    "retrieved": RETRIEVED,
}

PG_MONITOR = {
    "url": f"{PG17}monitoring.html",
    "version": "17",
    "section": "27 Monitoring Database Activity",
    "title": "Monitoring Database Activity",
    "retrieved": RETRIEVED,
}

PG_ROLES = {
    "url": f"{PG17}role-attributes.html",
    "version": "17",
    "section": "21.2 Role Attributes",
    "title": "Role Attributes",
    "retrieved": RETRIEVED,
}

PG_PRIV = {
    "url": f"{PG17}ddl-priv.html",
    "version": "17",
    "section": "5.8 Privileges",
    "title": "Privileges",
    "retrieved": RETRIEVED,
}

PG_RLS = {
    "url": f"{PG17}ddl-rowsecurity.html",
    "version": "17",
    "section": "5.9 Row Security Policies",
    "title": "Row Security Policies",
    "retrieved": RETRIEVED,
}

PG_UDF = {
    "url": f"{PG17}xfunc.html",
    "version": "17",
    "section": "36.3 User-Defined Functions",
    "title": "User-Defined Functions",
    "retrieved": RETRIEVED,
}

PG_PLPGSQL = {
    "url": f"{PG17}plpgsql.html",
    "version": "17",
    "section": "41 PL/pgSQL - SQL Procedural Language",
    "title": "PL/pgSQL",
    "retrieved": RETRIEVED,
}

PG_PROC = {
    "url": f"{PG17}sql-createprocedure.html",
    "version": "17",
    "section": "CREATE PROCEDURE",
    "title": "CREATE PROCEDURE",
    "retrieved": RETRIEVED,
}

PG_CALL = {
    "url": f"{PG17}sql-call.html",
    "version": "17",
    "section": "CALL",
    "title": "CALL",
    "retrieved": RETRIEVED,
}

PG_TRIGGER = {
    "url": f"{PG17}sql-createtrigger.html",
    "version": "17",
    "section": "CREATE TRIGGER",
    "title": "CREATE TRIGGER",
    "retrieved": RETRIEVED,
}

PG_FUNCTIONS_WINDOW = {
    "url": f"{PG17}functions-window.html",
    "version": "17",
    "section": "9.22 Window Functions",
    "title": "Window Functions",
    "retrieved": RETRIEVED,
}

PG_AGGREGATE_EXPRESSIONS = {
    "url": f"{PG17}sql-expressions.html",
    "version": "17",
    "section": "4.2.7 Aggregate Expressions",
    "title": "Aggregate Expressions",
    "retrieved": RETRIEVED,
}

PG_TYPE_NET = {
    "url": f"{PG17}datatype-net-types.html",
    "version": "17",
    "section": "8.9 Network Address Types",
    "title": "Network Address Types",
    "retrieved": RETRIEVED,
}

PG_FUNCTIONS_NET = {
    "url": f"{PG17}functions-net.html",
    "version": "17",
    "section": "9.12 Network Address Functions and Operators",
    "title": "Network Address Functions and Operators",
    "retrieved": RETRIEVED,
}

PG_PROTOCOL = {
    "url": f"{PG17}protocol-flow.html",
    "version": "17",
    "section": "53.2.9 Termination",
    "title": "Termination",
    "retrieved": RETRIEVED,
}

PG_SUBXACTS = {
    "url": f"{PG17}subxacts.html",
    "version": "17",
    "section": "66.3 Subtransactions",
    "title": "Subtransactions",
    "retrieved": RETRIEVED,
}

PG_SERIALIZATION_FAILURE = {
    "url": f"{PG17}mvcc-serialization-failure-handling.html",
    "version": "17",
    "section": "13.5 Serialization Failure Handling",
    "title": "Serialization Failure Handling",
    "retrieved": RETRIEVED,
}

PG_STORAGE_HOT = {
    "url": f"{PG17}storage-hot.html",
    "version": "17",
    "section": "65.7 Heap-Only Tuples (HOT)",
    "title": "Heap-Only Tuples (HOT)",
    "retrieved": RETRIEVED,
}

PG_CONFIG_SETTING = {
    "url": f"{PG17}config-setting.html",
    "version": "17",
    "section": "19.1 Setting Parameters",
    "title": "Setting Parameters",
    "retrieved": RETRIEVED,
}

PG_INDEX_ORDERING = {
    "url": f"{PG17}indexes-ordering.html",
    "version": "17",
    "section": "11.4 Indexes and ORDER BY",
    "title": "Indexes and ORDER BY",
    "retrieved": RETRIEVED,
}

PG_INDEX_MULTICOLUMN = {
    "url": f"{PG17}indexes-multicolumn.html",
    "version": "17",
    "section": "11.3 Multicolumn Indexes",
    "title": "Multicolumn Indexes",
    "retrieved": RETRIEVED,
}

PG_INDEX_PARTIAL = {
    "url": f"{PG17}indexes-partial.html",
    "version": "17",
    "section": "11.8 Partial Indexes",
    "title": "Partial Indexes",
    "retrieved": RETRIEVED,
}

PG_BTREE = {
    "url": f"{PG17}indexes-types.html",
    "version": "17",
    "section": "11.2.1 B-Tree",
    "title": "B-Tree",
    "retrieved": RETRIEVED,
}

PG_PREPARE = {
    "url": f"{PG17}sql-prepare.html",
    "version": "17",
    "section": "PREPARE",
    "title": "PREPARE",
    "retrieved": RETRIEVED,
}

PG_PLANNER_OPTIONS = {
    "url": f"{PG17}runtime-config-query.html",
    "version": "17",
    "section": "19.7.4 Other Planner Options",
    "title": "Other Planner Options",
    "retrieved": RETRIEVED,
}

PG_CONDITIONAL = {
    "url": f"{PG17}functions-conditional.html",
    "version": "17",
    "section": "9.18.1 CASE",
    "title": "CASE",
    "retrieved": RETRIEVED,
}

PG_ROLE_MEMBERSHIP = {
    "url": f"{PG17}role-membership.html",
    "version": "17",
    "section": "21.3 Role Membership",
    "title": "Role Membership",
    "retrieved": RETRIEVED,
}

PG_CLIENT_AUTH_CH = {
    "url": f"{PG17}client-authentication.html",
    "version": "17",
    "section": "Chapter 20. Client Authentication",
    "title": "Client Authentication",
    "retrieved": RETRIEVED,
}

PG_SASL = {
    "url": f"{PG17}sasl-authentication.html",
    "version": "17",
    "section": "53.3 SASL Authentication",
    "title": "SASL Authentication",
    "retrieved": RETRIEVED,
}

PG_PGDUMP = {
    "url": f"{PG17}app-pgdump.html",
    "version": "17",
    "section": "pg_dump",
    "title": "pg_dump",
    "retrieved": RETRIEVED,
}

PG_ALTER_DEFAULT_PRIVILEGES = {
    "url": f"{PG17}sql-alterdefaultprivileges.html",
    "version": "17",
    "section": "ALTER DEFAULT PRIVILEGES",
    "title": "ALTER DEFAULT PRIVILEGES",
    "retrieved": RETRIEVED,
}

PG_PG_CLASS = {
    "url": f"{PG17}catalog-pg-class.html",
    "version": "17",
    "section": "51.11 pg_class",
    "title": "pg_class",
    "retrieved": RETRIEVED,
}

PG_CREATE_POLICY = {
    "url": f"{PG17}sql-createpolicy.html",
    "version": "17",
    "section": "CREATE POLICY",
    "title": "CREATE POLICY",
    "retrieved": RETRIEVED,
}

PG_FUNCTIONS_INFO = {
    "url": f"{PG17}functions-info.html",
    "version": "17",
    "section": "9.27 System Information Functions and Operators",
    "title": "System Information Functions and Operators",
    "retrieved": RETRIEVED,
}

PG_PLPGSQL_TRIGGER = {
    "url": f"{PG17}plpgsql-trigger.html",
    "version": "17",
    "section": "41.10 Trigger Functions",
    "title": "Trigger Functions",
    "retrieved": RETRIEVED,
}

PG_PLPGSQL_TX = {
    "url": f"{PG17}plpgsql-transactions.html",
    "version": "17",
    "section": "41.8 Transaction Management",
    "title": "Transaction Management",
    "retrieved": RETRIEVED,
}

PG_CREATE_TABLE_AS = {
    "url": f"{PG17}sql-createtableas.html",
    "version": "17",
    "section": "CREATE TABLE AS",
    "title": "CREATE TABLE AS",
    "retrieved": RETRIEVED,
}

PG_TRUNCATE = {
    "url": f"{PG17}sql-truncate.html",
    "version": "17",
    "section": "TRUNCATE",
    "title": "TRUNCATE",
    "retrieved": RETRIEVED,
}

PG_DROP_TABLE = {
    "url": f"{PG17}sql-droptable.html",
    "version": "17",
    "section": "DROP TABLE",
    "title": "DROP TABLE",
    "retrieved": RETRIEVED,
}

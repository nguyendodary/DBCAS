#!/bin/bash
# Read-only role for executing untrusted learner SQL (NFR-02 / QA03).
# Backend connects as this role for evaluation; every statement runs inside a
# READ ONLY transaction that is rolled back after scoring. Credentials and
# the statement timeout come from .env (SANDBOX_LEARNER_PASSWORD /
# SANDBOX_STATEMENT_TIMEOUT_MS) — never hardcode them here.
set -e

LEARNER_PASSWORD="${SANDBOX_LEARNER_PASSWORD:-learner_ro_dev}"
STMT_TIMEOUT="${SANDBOX_STATEMENT_TIMEOUT_MS:-3000}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Unprivileged executor role: SELECT only, no CREATE, no TEMP objects,
    -- read-only by default even outside an explicit transaction.
    CREATE ROLE learner_ro LOGIN PASSWORD '$LEARNER_PASSWORD';
    ALTER ROLE learner_ro SET statement_timeout = '$STMT_TIMEOUT';
    ALTER ROLE learner_ro SET default_transaction_read_only = on;
    ALTER ROLE learner_ro SET idle_in_transaction_session_timeout = '15s';
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    REVOKE TEMPORARY ON DATABASE "$POSTGRES_DB" FROM PUBLIC;
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO learner_ro;
    GRANT USAGE ON SCHEMA public TO learner_ro;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO learner_ro;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO learner_ro;
EOSQL

#!/bin/bash
# Read-only role for executing untrusted learner SQL (NFR-02 / QA03).
# Backend connects as this role for evaluation; every statement runs inside a
# READ ONLY transaction that is rolled back after scoring. Credentials and
# the statement timeout come from .env (SANDBOX_LEARNER_PASSWORD /
# SANDBOX_STATEMENT_TIMEOUT_MS) — never hardcode them here.
set -e

LEARNER_PASSWORD="${SANDBOX_LEARNER_PASSWORD:-learner_ro_dev}"
STMT_TIMEOUT="${SANDBOX_STATEMENT_TIMEOUT_MS:-3000}"
if ! [[ "$STMT_TIMEOUT" =~ ^[0-9]+$ ]] || (( STMT_TIMEOUT < 1 || STMT_TIMEOUT > 3000 )); then
    echo 'SANDBOX_STATEMENT_TIMEOUT_MS must be an integer from 1 to 3000' >&2
    exit 1
fi

psql -v ON_ERROR_STOP=1 -v learner_password="$LEARNER_PASSWORD" -v statement_timeout="$STMT_TIMEOUT" -v database_name="$POSTGRES_DB" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Unprivileged executor role: SELECT only, no CREATE, no TEMP objects,
    -- read-only by default even outside an explicit transaction.
    CREATE ROLE learner_ro LOGIN PASSWORD :'learner_password';
    ALTER ROLE learner_ro SET statement_timeout = :'statement_timeout';
    ALTER ROLE learner_ro SET default_transaction_read_only = on;
    ALTER ROLE learner_ro SET idle_in_transaction_session_timeout = '15s';
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    REVOKE TEMPORARY ON DATABASE :"database_name" FROM PUBLIC;
    GRANT CONNECT ON DATABASE :"database_name" TO learner_ro;
    GRANT USAGE ON SCHEMA public TO learner_ro;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO learner_ro;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO learner_ro;
EOSQL

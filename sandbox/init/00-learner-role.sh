#!/bin/bash
# Read-only role for executing untrusted learner SQL (NFR-02 / ADR-001).
# Backend connects as this role for evaluation; transactions are rolled back
# after scoring. Password comes from SANDBOX_LEARNER_PASSWORD (.env).
set -e

LEARNER_PASSWORD="${SANDBOX_LEARNER_PASSWORD:-learner_ro_dev}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE learner_ro LOGIN PASSWORD '$LEARNER_PASSWORD';
    ALTER ROLE learner_ro SET statement_timeout = '${SANDBOX_STATEMENT_TIMEOUT_MS:-3000}';
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO learner_ro;
    GRANT USAGE ON SCHEMA public TO learner_ro;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO learner_ro;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO learner_ro;
EOSQL

-- Read-only role for executing untrusted learner SQL (NFR / ADR-001).
-- Backend connects as this role for evaluation; transactions are rolled back after scoring.
CREATE ROLE learner_ro LOGIN PASSWORD 'learner_ro_dev';
ALTER ROLE learner_ro SET statement_timeout = '3s';
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE postgres TO learner_ro;
GRANT USAGE ON SCHEMA public TO learner_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO learner_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO learner_ro;

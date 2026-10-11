-- 001_account_identity.sql — additive migration for existing databases.
-- Fresh installs already get this table from db/schema.sql.
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/001_account_identity.sql
--
-- Linked social sign-in identities (Google/GitHub). One row per
-- (provider, provider_user_id) — an account may link several providers.
-- Linking only ever happens on provider-verified emails (see
-- app/services/oauth.py); unverified emails can never attach an identity
-- to an existing account.

CREATE TABLE IF NOT EXISTS account_identity (
  identity_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL,
  provider VARCHAR(20) NOT NULL,
  provider_user_id VARCHAR(255) NOT NULL,
  provider_email VARCHAR(255),
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (provider, provider_user_id)
);

ALTER TABLE account_identity
  ADD FOREIGN KEY (account_id) REFERENCES account (account_id);

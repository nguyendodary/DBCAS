-- Refresh credentials are random bearer values; persist only their SHA-256 hash.
CREATE TABLE IF NOT EXISTS refresh_session (
  token_hash VARCHAR(64) PRIMARY KEY CHECK (token_hash ~ '^[0-9a-f]{64}$'),
  family_id VARCHAR(32) NOT NULL CHECK (family_id ~ '^[0-9a-f]{32}$'),
  account_id INT NOT NULL REFERENCES account(account_id) ON DELETE CASCADE,
  credential_version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS refresh_session_family_idx ON refresh_session(family_id);
CREATE INDEX IF NOT EXISTS refresh_session_account_idx ON refresh_session(account_id);
CREATE INDEX IF NOT EXISTS refresh_session_expiry_idx ON refresh_session(expires_at);

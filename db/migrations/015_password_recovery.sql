-- 015 — self-service password recovery.
-- Forward-only: existing accounts keep working unchanged. password_set
-- defaults to TRUE because every account that predates this migration
-- owns a password hash; OAuth-only sign-ups created afterwards are
-- recorded with password_set = FALSE so the interface can tell the
-- difference without inferring from hashes (a random hash is still a
-- hash). Tokens are stored only as SHA-256 digests.

ALTER TABLE account ADD COLUMN IF NOT EXISTS password_set BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE account ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS password_reset_token (
  token_hash VARCHAR(64) PRIMARY KEY,
  account_id INT NOT NULL REFERENCES account(account_id),
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  CHECK (expires_at > requested_at)
);
CREATE INDEX IF NOT EXISTS password_reset_token_account_idx
  ON password_reset_token(account_id, requested_at DESC);
CREATE INDEX IF NOT EXISTS password_reset_token_expiry_idx
  ON password_reset_token(expires_at);

CREATE TABLE IF NOT EXISTS password_reset_audit (
  audit_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL REFERENCES account(account_id),
  event VARCHAR(20) NOT NULL CHECK (event IN ('requested', 'completed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS password_reset_audit_account_idx
  ON password_reset_audit(account_id, audit_id DESC);

CREATE OR REPLACE FUNCTION preserve_password_reset_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Password reset audit is immutable';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='password_reset_audit'::regclass
                 AND tgname='password_reset_audit_immutable') THEN
    CREATE TRIGGER password_reset_audit_immutable BEFORE UPDATE OR DELETE ON password_reset_audit
      FOR EACH ROW EXECUTE FUNCTION preserve_password_reset_audit();
  END IF;
END $$;

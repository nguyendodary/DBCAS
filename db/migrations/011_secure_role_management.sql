-- Explicit, default-deny role-management capability and immutable role audit.
-- Existing accounts are not granted the capability by this migration.
ALTER TABLE account
  ADD COLUMN IF NOT EXISTS can_manage_roles BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS account_role_audit (
  audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  action_type VARCHAR(40) NOT NULL,
  actor_account_id INT REFERENCES account(account_id),
  target_account_id INT NOT NULL REFERENCES account(account_id),
  previous_role VARCHAR(50),
  new_role VARCHAR(50),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT account_role_audit_action_check CHECK (
    (action_type IN ('ROLE_GRANTED', 'ROLE_REVOKED')
      AND actor_account_id IS NOT NULL
      AND previous_role IN ('Learner', 'Administrator')
      AND new_role IN ('Learner', 'Administrator')
      AND previous_role <> new_role)
    OR
    (action_type = 'ROLE_MANAGER_BOOTSTRAPPED'
      AND actor_account_id IS NULL
      AND previous_role IS NULL
      AND new_role IS NULL)
  )
);

CREATE INDEX IF NOT EXISTS account_role_audit_target_idx
  ON account_role_audit(target_account_id, audit_id DESC);
CREATE INDEX IF NOT EXISTS account_role_audit_actor_idx
  ON account_role_audit(actor_account_id, audit_id DESC);

CREATE OR REPLACE FUNCTION preserve_account_role_audit() RETURNS trigger
  LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Account role audit records are immutable';
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgrelid='account_role_audit'::regclass
      AND tgname='account_role_audit_immutable'
  ) THEN
    CREATE TRIGGER account_role_audit_immutable
      BEFORE UPDATE OR DELETE ON account_role_audit
      FOR EACH ROW EXECUTE FUNCTION preserve_account_role_audit();
  END IF;
END $$;

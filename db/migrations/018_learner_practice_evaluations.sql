-- Historical assessment FKs remain valid; new practice sessions have no exam.
ALTER TABLE assessment_session ALTER COLUMN assessment_id DROP NOT NULL;
CREATE TABLE IF NOT EXISTS system_setting (
  setting_key VARCHAR(80) PRIMARY KEY,
  value JSONB NOT NULL,
  updated_by INT REFERENCES account(account_id),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO system_setting(setting_key, value) VALUES ('result_flow', '"IMMEDIATE"') ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS evaluation_record (
  evaluation_id SERIAL PRIMARY KEY,
  learner_id INT NOT NULL REFERENCES account(account_id),
  session_id INT REFERENCES assessment_session(session_id),
  scope_key VARCHAR(80) NOT NULL,
  input_hash VARCHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','ready')),
  payload JSONB,
  lease_until TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (learner_id, scope_key)
);
CREATE INDEX IF NOT EXISTS evaluation_record_jobs ON evaluation_record(status, updated_at);
CREATE TABLE IF NOT EXISTS grade_edit_audit (
  audit_id SERIAL PRIMARY KEY,
  attempt_id INT NOT NULL REFERENCES attempt(attempt_id),
  reviewer_id INT NOT NULL REFERENCES account(account_id),
  old_score NUMERIC(5,2),
  new_score NUMERIC(5,2) NOT NULL CHECK (new_score >= 0),
  reason VARCHAR(1000) NOT NULL CHECK (length(trim(reason)) >= 3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE OR REPLACE FUNCTION reject_grade_edit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Grade edit audit is immutable'; END $$;
DROP TRIGGER IF EXISTS grade_edit_audit_immutable ON grade_edit_audit;
CREATE TRIGGER grade_edit_audit_immutable BEFORE UPDATE OR DELETE ON grade_edit_audit
FOR EACH ROW EXECUTE FUNCTION reject_grade_edit_mutation();

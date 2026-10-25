-- Keep every accepted start/resume request idempotent after session completion.
-- Only known original request IDs are backfilled; assessment evidence is intact.
DO $$ BEGIN
  PERFORM set_config('lock_timeout', '5s', true);
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='assessment_session'::regclass AND conname='session_owner_unique') THEN
    ALTER TABLE assessment_session ADD CONSTRAINT session_owner_unique UNIQUE (session_id,learner_id);
  END IF;
  CREATE TABLE IF NOT EXISTS session_start_request (
    learner_id INT NOT NULL,
    request_id VARCHAR(36) NOT NULL,
    session_id INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (learner_id,request_id),
    FOREIGN KEY (session_id,learner_id) REFERENCES assessment_session(session_id,learner_id)
  );
  CREATE INDEX IF NOT EXISTS session_start_request_session_idx ON session_start_request(session_id);
  INSERT INTO session_start_request(learner_id,request_id,session_id)
    SELECT learner_id,start_request_id,session_id FROM assessment_session
    WHERE start_request_id IS NOT NULL
    ON CONFLICT (learner_id,request_id) DO NOTHING;
END $$;

CREATE OR REPLACE FUNCTION preserve_session_start_request() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Accepted assessment start request bindings are immutable';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='session_start_request'::regclass AND tgname='session_start_request_immutable') THEN
    CREATE TRIGGER session_start_request_immutable BEFORE UPDATE OR DELETE ON session_start_request
      FOR EACH ROW EXECUTE FUNCTION preserve_session_start_request();
  END IF;
END $$;

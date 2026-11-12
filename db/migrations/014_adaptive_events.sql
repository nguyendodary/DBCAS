-- Optional adaptive practice adds evidence; no historical row is rewritten.
-- Policy and inventory remain in the existing immutable session snapshot.
CREATE TABLE IF NOT EXISTS adaptive_event (
  session_id INT NOT NULL REFERENCES assessment_session(session_id),
  round_no SMALLINT NOT NULL CHECK (round_no BETWEEN 1 AND 13),
  event_type VARCHAR(16) NOT NULL CHECK (event_type IN ('batch', 'decision')),
  payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (session_id, round_no, event_type)
);

CREATE OR REPLACE FUNCTION preserve_adaptive_event() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Adaptive selection and decision evidence is immutable';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='adaptive_event'::regclass AND tgname='adaptive_event_immutable') THEN
    CREATE TRIGGER adaptive_event_immutable BEFORE UPDATE OR DELETE ON adaptive_event
      FOR EACH ROW EXECUTE FUNCTION preserve_adaptive_event();
  END IF;
END $$;

-- Tab-leave anti-cheat for FIXED papers (migration 024).
-- Additive only: existing sessions keep zero violations and no cancellation.
ALTER TABLE assessment_session
  ADD COLUMN IF NOT EXISTS tab_leave_count INT NOT NULL DEFAULT 0;

ALTER TABLE assessment_session
  ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;

ALTER TABLE assessment_session
  ADD COLUMN IF NOT EXISTS cancel_reason VARCHAR(40);

ALTER TABLE assessment_session
  DROP CONSTRAINT IF EXISTS assessment_session_status_check;

ALTER TABLE assessment_session
  ADD CONSTRAINT assessment_session_status_check
  CHECK (status IN ('in_progress', 'completed', 'timed_out', 'cancelled'));

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'assessment_session'::regclass
      AND conname = 'assessment_session_tab_leave_count_check'
  ) THEN
    ALTER TABLE assessment_session
      ADD CONSTRAINT assessment_session_tab_leave_count_check
      CHECK (tab_leave_count >= 0);
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS tab_leave_interval (
  leave_event_id UUID PRIMARY KEY,
  session_id INT NOT NULL REFERENCES assessment_session(session_id) ON DELETE CASCADE,
  left_at TIMESTAMPTZ NOT NULL,
  returned_at TIMESTAMPTZ,
  return_event_id UUID UNIQUE,
  away_seconds INT,
  counted BOOLEAN NOT NULL DEFAULT FALSE,
  CHECK (away_seconds IS NULL OR away_seconds >= 0)
);

-- Only one unreported leave may be open at a time; the server serializes the
-- interval under the session row lock and this index is the final guard.
CREATE UNIQUE INDEX IF NOT EXISTS tab_leave_interval_open_idx
  ON tab_leave_interval(session_id) WHERE returned_at IS NULL;
CREATE INDEX IF NOT EXISTS tab_leave_interval_session_idx
  ON tab_leave_interval(session_id, left_at DESC);

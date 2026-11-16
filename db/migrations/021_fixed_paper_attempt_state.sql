-- FIXED paper attempt UI state (migration 021).
-- Additive only: old attempts get false/0/NULL defaults; no row rewrite.
ALTER TABLE attempt
  ADD COLUMN IF NOT EXISTS is_flagged BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE attempt
  ADD COLUMN IF NOT EXISTS flag_revision INT NOT NULL DEFAULT 0;

ALTER TABLE attempt
  ADD COLUMN IF NOT EXISTS first_opened_at TIMESTAMPTZ;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'attempt'::regclass
      AND conname = 'attempt_flag_revision_check'
  ) THEN
    ALTER TABLE attempt
      ADD CONSTRAINT attempt_flag_revision_check CHECK (flag_revision >= 0);
  END IF;
END $$;

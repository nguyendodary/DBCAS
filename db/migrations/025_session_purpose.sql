-- Session purpose and cumulative-competency provenance (migration 025).
-- TEST sessions are scored tests; PRACTICE sessions are learning evidence.
-- purpose_source separates server-created rows from deterministic backfill.
-- Additive only: existing session evidence and snapshots are not rewritten.

DO $$
DECLARE
  added_purpose BOOLEAN := FALSE;
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'assessment_session'
      AND column_name = 'purpose'
  ) THEN
    ALTER TABLE assessment_session
      ADD COLUMN purpose VARCHAR(10) NOT NULL DEFAULT 'PRACTICE';
    added_purpose := TRUE;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'assessment_session'
      AND column_name = 'purpose_source'
  ) THEN
    ALTER TABLE assessment_session
      ADD COLUMN purpose_source VARCHAR(10) NOT NULL DEFAULT 'SERVER';
  END IF;

  IF added_purpose THEN
    -- Deterministic classification of historical rows. Formal assessment
    -- sessions are TEST; explicit assessment PRACTICE mode is PRACTICE;
    -- FIXED/ADAPTIVE runner snapshots are TEST; rows without any of these
    -- markers fail closed as PRACTICE.
    UPDATE assessment_session
    SET purpose = CASE
      WHEN assessment_id IS NOT NULL
           AND config_snapshot->>'assembly_mode' = 'PRACTICE' THEN 'PRACTICE'
      WHEN assessment_id IS NOT NULL THEN 'TEST'
      WHEN config_snapshot->>'assessment_style' IN ('FIXED', 'ADAPTIVE') THEN 'TEST'
      WHEN config_snapshot->>'runner_mode' IN ('fixed', 'adaptive') THEN 'TEST'
      ELSE 'PRACTICE'
    END,
    purpose_source = 'BACKFILL';
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'assessment_session'::regclass
      AND conname = 'assessment_session_purpose_check'
  ) THEN
    ALTER TABLE assessment_session
      ADD CONSTRAINT assessment_session_purpose_check
      CHECK (purpose IN ('TEST', 'PRACTICE'));
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'assessment_session'::regclass
      AND conname = 'assessment_session_purpose_source_check'
  ) THEN
    ALTER TABLE assessment_session
      ADD CONSTRAINT assessment_session_purpose_source_check
      CHECK (purpose_source IN ('SERVER', 'BACKFILL'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS assessment_session_purpose_idx
  ON assessment_session(learner_id, purpose, purpose_source, started_at DESC);

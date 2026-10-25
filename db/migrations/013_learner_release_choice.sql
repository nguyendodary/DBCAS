-- A learner may choose the release mode once, while submitting their session.
-- Existing results, configuration snapshots and start requests are preserved.
SET LOCAL lock_timeout = '5s';
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS release_policy_chosen_at TIMESTAMPTZ;

CREATE OR REPLACE FUNCTION preserve_session_release_policy() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.start_request_id IS DISTINCT FROM OLD.start_request_id THEN
    RAISE EXCEPTION 'Started assessment start request is immutable';
  END IF;
  IF OLD.release_policy_chosen_at IS NOT NULL AND
      NEW.release_policy_chosen_at IS DISTINCT FROM OLD.release_policy_chosen_at THEN
    RAISE EXCEPTION 'Submitted result release choice is immutable';
  END IF;
  IF NEW.result_release_policy IS DISTINCT FROM OLD.result_release_policy OR
      NEW.release_policy_chosen_at IS DISTINCT FROM OLD.release_policy_chosen_at THEN
    IF NOT (OLD.status = 'in_progress' AND NEW.status = 'in_progress'
            AND OLD.release_status = 'unsubmitted' AND NEW.release_status = 'unsubmitted'
            AND OLD.release_policy_chosen_at IS NULL AND NEW.release_policy_chosen_at IS NOT NULL) THEN
      RAISE EXCEPTION 'Result release choice can only be recorded once before submission';
    END IF;
  END IF;
  RETURN NEW;
END $$;

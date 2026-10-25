-- Repair stale legacy publication decisions without changing grade evidence.
-- Keep migration 008's applied checksum intact. The DO block also makes this
-- safe in fresh schema.sql installs that execute statements in autocommit mode.
DO $$ BEGIN
  PERFORM set_config('lock_timeout', '5s', true);
  -- Serialize release decisions with application grading transactions. A busy
  -- database fails the upgrade safely rather than waiting without a deadline.
  LOCK TABLE assessment_session, attempt IN EXCLUSIVE MODE;
  WITH invalid AS (
    SELECT s.session_id, s.release_status AS previous_status,
      CASE WHEN EXISTS (
        SELECT 1 FROM attempt a WHERE a.session_id=s.session_id
          AND a.submitted_at IS NOT NULL AND a.grading_status='failed'
      ) THEN 'grading_failed' ELSE 'auto_grading' END AS corrected_status
    FROM assessment_session s
    WHERE s.status <> 'in_progress'
      AND s.release_status IN ('published','reviewed','pending_review')
      AND EXISTS (
        SELECT 1 FROM attempt a WHERE a.session_id=s.session_id
          AND a.submitted_at IS NOT NULL
          AND (a.score IS NULL OR a.grading_status IS DISTINCT FROM 'graded')
      )
  ), changed AS (
    UPDATE assessment_session s
      SET release_status=i.corrected_status, review_revision=s.review_revision+1
    FROM invalid i WHERE s.session_id=i.session_id
    RETURNING s.session_id, i.previous_status, s.release_status AS new_status
  )
  INSERT INTO result_release_event(session_id,previous_status,new_status)
    SELECT session_id,previous_status,new_status FROM changed;
END $$;

-- Practice results are visible as provisional AI drafts, then replaced by an
-- immutable administrator-approved snapshot. Additive only; existing rows are
-- never rewritten except the idempotent legacy-snapshot insert below.
ALTER TABLE assessment_session DROP CONSTRAINT IF EXISTS session_release_check;
ALTER TABLE assessment_session ADD CONSTRAINT session_release_check CHECK (
  result_release_policy IN ('IMMEDIATE','HUMAN_VERIFIED') AND review_revision >= 0 AND
  release_status IN ('unsubmitted','auto_grading','provisional_ai','pending_review','reviewed','published','grading_failed')
);

-- Score edits defer the next provider evaluation without delaying first results.
ALTER TABLE evaluation_record ADD COLUMN IF NOT EXISTS available_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
CREATE INDEX IF NOT EXISTS evaluation_record_available ON evaluation_record(status, available_at);

CREATE TABLE IF NOT EXISTS session_final_result (
  result_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL UNIQUE REFERENCES assessment_session(session_id),
  reviewer_id INT REFERENCES account(account_id),
  source VARCHAR(20) NOT NULL CHECK (source IN ('admin','legacy')),
  evaluation_input_hash VARCHAR(64) NOT NULL,
  approval_revision INT NOT NULL CHECK (approval_revision >= 0),
  ai_evaluation JSONB NOT NULL,
  final_evaluation JSONB NOT NULL,
  concept_results JSONB NOT NULL DEFAULT '[]'::jsonb,
  scores JSONB NOT NULL DEFAULT '[]'::jsonb,
  overall JSONB NOT NULL,
  uncovered_concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
  approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK ((source = 'admin' AND reviewer_id IS NOT NULL) OR source = 'legacy')
);
CREATE INDEX IF NOT EXISTS session_final_result_reviewer_idx
  ON session_final_result(reviewer_id, approved_at);

CREATE OR REPLACE FUNCTION preserve_final_result() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Final result snapshots are immutable'; END $$;
DROP TRIGGER IF EXISTS session_final_result_immutable ON session_final_result;
CREATE TRIGGER session_final_result_immutable BEFORE UPDATE OR DELETE ON session_final_result
FOR EACH ROW EXECUTE FUNCTION preserve_final_result();

-- Backfill only already-published practice sessions. The AI draft was already
-- approved under the legacy flow, so keep it as the audit and final text.
INSERT INTO session_final_result (
  session_id, reviewer_id, source, evaluation_input_hash, approval_revision,
  ai_evaluation, final_evaluation, concept_results, scores, overall,
  uncovered_concepts, approved_at
)
SELECT
  s.session_id,
  pub.reviewer_id,
  'legacy',
  er.input_hash,
  s.review_revision,
  er.payload,
  er.payload->'evaluation',
  '[]'::jsonb,
  COALESCE((
    SELECT jsonb_agg(jsonb_build_object(
      'attempt_id', a.attempt_id,
      'question_id', a.question_id,
      'score', a.score,
      'points', q.points,
      'grading_status', a.grading_status
    ) ORDER BY a.seq_no)
    FROM attempt a
    JOIN question q ON q.question_id = a.question_id
    WHERE a.session_id = s.session_id AND a.submitted_at IS NOT NULL
  ), '[]'::jsonb),
  jsonb_build_object(
    'earned', COALESCE((
      SELECT sum(a.score) FROM attempt a
      WHERE a.session_id = s.session_id AND a.submitted_at IS NOT NULL
    ), 0),
    'possible', COALESCE((
      SELECT sum(q.points) FROM attempt a
      JOIN question q ON q.question_id = a.question_id
      WHERE a.session_id = s.session_id AND a.submitted_at IS NOT NULL
    ), 0),
    'percentage', CASE WHEN COALESCE((
      SELECT sum(q.points) FROM attempt a
      JOIN question q ON q.question_id = a.question_id
      WHERE a.session_id = s.session_id AND a.submitted_at IS NOT NULL
    ), 0) > 0 THEN round(COALESCE((
      SELECT sum(a.score) FROM attempt a
      WHERE a.session_id = s.session_id AND a.submitted_at IS NOT NULL
    ), 0) / (
      SELECT sum(q.points) FROM attempt a
      JOIN question q ON q.question_id = a.question_id
      WHERE a.session_id = s.session_id AND a.submitted_at IS NOT NULL
    ) * 100, 2) ELSE 0 END
  ),
  COALESCE(s.config_snapshot->'uncovered_concepts', '[]'::jsonb),
  COALESCE(s.published_at, er.updated_at, NOW())
FROM assessment_session s
JOIN evaluation_record er
  ON er.session_id = s.session_id
 AND er.status = 'ready'
 AND er.payload ? 'evaluation'
LEFT JOIN LATERAL (
  SELECT e.reviewer_id
  FROM result_release_event e
  WHERE e.session_id = s.session_id AND e.new_status = 'published'
  ORDER BY e.event_id DESC
  LIMIT 1
) pub ON TRUE
WHERE s.assessment_id IS NULL
  AND s.status <> 'in_progress'
  AND s.release_status = 'published'
ON CONFLICT (session_id) DO NOTHING;

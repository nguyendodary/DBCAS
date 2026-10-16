-- Preserve existing rows. Legacy snapshots capture the best available context
-- at upgrade time; they cannot reconstruct edits made before this migration.
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS config_snapshot JSONB;
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS question_snapshot JSONB;
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS draft_answer JSONB;
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS draft_revision INT NOT NULL DEFAULT 0;
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS draft_saved_at TIMESTAMPTZ;
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS submission_hash VARCHAR(64);
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS grading_status VARCHAR(20) NOT NULL DEFAULT 'unsubmitted';
ALTER TABLE question ADD COLUMN IF NOT EXISTS ai_review JSONB;
ALTER TABLE question_concept ADD COLUMN IF NOT EXISTS review_status VARCHAR(20) NOT NULL DEFAULT 'pending';
ALTER TABLE competency_gap ADD COLUMN IF NOT EXISTS explanation_context_hash VARCHAR(64);

UPDATE question_concept SET review_status='confirmed' WHERE confirmed AND review_status='pending';
UPDATE attempt SET grading_status='graded' WHERE submitted_at IS NOT NULL AND score IS NOT NULL AND grading_status='unsubmitted';
UPDATE assessment_session SET submitted_at=expires_at
  WHERE status='timed_out' AND submitted_at IS NULL;

CREATE TABLE IF NOT EXISTS oauth_handoff (
  jti_hash VARCHAR(64) PRIMARY KEY,
  account_id INT NOT NULL REFERENCES account(account_id),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS oauth_handoff_expiry_idx ON oauth_handoff(expires_at);

CREATE TABLE IF NOT EXISTS login_throttle (
  key_hash VARCHAR(64) PRIMARY KEY,
  failures JSONB NOT NULL DEFAULT '[]',
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS login_throttle_expiry_idx ON login_throttle(expires_at);

CREATE TABLE IF NOT EXISTS grading_job (
  job_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  attempt_id INT NOT NULL UNIQUE REFERENCES attempt(attempt_id),
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  attempt_count INT NOT NULL DEFAULT 0,
  available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  lease_until TIMESTAMPTZ,
  last_error_code VARCHAR(80),
  finished_at TIMESTAMPTZ,
  CHECK (status IN ('pending','processing','completed','failed')),
  CHECK (attempt_count >= 0)
);
CREATE INDEX IF NOT EXISTS grading_job_ready_idx ON grading_job(status,available_at);
CREATE INDEX IF NOT EXISTS assessment_session_learner_idx ON assessment_session(learner_id,started_at DESC);
CREATE INDEX IF NOT EXISTS assessment_session_expiry_idx ON assessment_session(status,expires_at);
CREATE INDEX IF NOT EXISTS attempt_question_idx ON attempt(question_id);
CREATE INDEX IF NOT EXISTS question_concept_concept_idx ON question_concept(concept_id,confirmed);

UPDATE assessment_session s SET config_snapshot = jsonb_build_object(
  'version',1,'legacy_backfill',true,'assessment_id',a.assessment_id,'title',a.title,
  'description',a.description,'max_questions',a.max_questions,'duration_min',a.duration_min,
  'target_mcq',a.target_mcq,'target_sql',a.target_sql,'target_essay',a.target_essay,
  'concepts',COALESCE((SELECT jsonb_agg(jsonb_build_object(
    'concept_id',c.concept_id,'concept_code',c.concept_code,'concept_name',c.concept_name,
    'subject_area',c.subject_area,'description',c.description,
    'min_difficulty',t.min_difficulty,'max_difficulty',t.max_difficulty,'target_pct',t.target_pct
  ) ORDER BY c.concept_id) FROM assessment_concept t JOIN concept c USING(concept_id)
  WHERE t.assessment_id=a.assessment_id),'[]'::jsonb)
) FROM assessment a WHERE s.assessment_id=a.assessment_id AND s.config_snapshot IS NULL;

UPDATE attempt t SET question_snapshot = jsonb_build_object(
  'version',1,'legacy_backfill',true,'question_id',q.question_id,'question_type',q.question_type,
  'prompt',q.prompt,'reference_answer',q.reference_answer,'points',q.points,
  'difficulty_level',q.difficulty_level,
  'concepts',COALESCE((SELECT jsonb_agg(jsonb_build_object(
    'concept_id',c.concept_id,'concept_code',c.concept_code,'concept_name',c.concept_name,
    'subject_area',c.subject_area,'description',c.description,'confirmed',true,'is_required',qc.is_required
  ) ORDER BY c.concept_id) FROM question_concept qc JOIN concept c USING(concept_id)
  WHERE qc.question_id=q.question_id AND qc.confirmed),'[]'::jsonb),
  'options',COALESCE((SELECT jsonb_agg(jsonb_build_object(
    'option_id',o.option_id,'option_label',o.option_label,'option_text',o.option_text,'is_correct',o.is_correct
  ) ORDER BY o.option_id) FROM mcq_option o WHERE o.question_id=q.question_id),'[]'::jsonb),
  'datasets',COALESCE((SELECT jsonb_agg(jsonb_build_object(
    'dataset_id',d.dataset_id,'dataset_name',d.dataset_name,'setup_sql',d.setup_sql,
    'expected_result',d.expected_result,'is_edge_case',d.is_edge_case
  ) ORDER BY d.dataset_id) FROM sql_test_dataset d WHERE d.question_id=q.question_id),'[]'::jsonb),
  'rubrics',COALESCE((SELECT jsonb_agg(jsonb_build_object(
    'level_name',r.level_name,'min_score',r.min_score,'max_score',r.max_score,'criteria',r.criteria
  ) ORDER BY r.min_score) FROM rubric r WHERE r.question_id=q.question_id),'[]'::jsonb)
) FROM question q WHERE t.question_id=q.question_id AND t.question_snapshot IS NULL;

CREATE OR REPLACE FUNCTION preserve_question_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.question_snapshot IS NOT NULL AND NEW.question_snapshot IS DISTINCT FROM OLD.question_snapshot THEN
    RAISE EXCEPTION 'Question evidence context is immutable';
  END IF;
  RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION preserve_session_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.config_snapshot IS NOT NULL AND NEW.config_snapshot IS DISTINCT FROM OLD.config_snapshot THEN
    RAISE EXCEPTION 'Assessment evidence context is immutable';
  END IF;
  RETURN NEW;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='attempt'::regclass AND tgname='attempt_snapshot_immutable') THEN
    CREATE TRIGGER attempt_snapshot_immutable BEFORE UPDATE ON attempt
      FOR EACH ROW EXECUTE FUNCTION preserve_question_snapshot();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='assessment_session'::regclass AND tgname='session_snapshot_immutable') THEN
    CREATE TRIGGER session_snapshot_immutable BEFORE UPDATE ON assessment_session
      FOR EACH ROW EXECUTE FUNCTION preserve_session_snapshot();
  END IF;
END $$;

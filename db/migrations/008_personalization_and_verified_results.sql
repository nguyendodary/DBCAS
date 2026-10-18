-- Additive supervisor requirements. Never rewrite existing immutable snapshots.
ALTER TABLE concept ADD COLUMN IF NOT EXISTS keywords TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE concept ADD COLUMN IF NOT EXISTS learning_objectives TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE assessment ADD COLUMN IF NOT EXISTS result_release_policy VARCHAR(20) NOT NULL DEFAULT 'IMMEDIATE';
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS result_release_policy VARCHAR(20) NOT NULL DEFAULT 'IMMEDIATE';
-- Legacy finalized, fully graded results retain their existing availability.
-- Application-created sessions explicitly start at unsubmitted.
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS release_status VARCHAR(20) NOT NULL DEFAULT 'unsubmitted';
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS start_request_id VARCHAR(36);
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS review_revision INT NOT NULL DEFAULT 0;
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS review_revision INT NOT NULL DEFAULT 0;
-- Thirteen valid 999.99-point items can total 12999.87. Widen capacity while
-- preserving the established two-decimal score scale and every existing value.
ALTER TABLE concept_competency ALTER COLUMN points_earned TYPE NUMERIC(10,2);
ALTER TABLE concept_competency ALTER COLUMN points_possible TYPE NUMERIC(10,2);

UPDATE assessment_session s SET release_status = CASE
  WHEN s.status='in_progress' THEN 'unsubmitted'
  WHEN EXISTS (SELECT 1 FROM attempt a WHERE a.session_id=s.session_id AND a.submitted_at IS NOT NULL AND a.grading_status='failed') THEN 'grading_failed'
  WHEN EXISTS (SELECT 1 FROM attempt a WHERE a.session_id=s.session_id AND a.submitted_at IS NOT NULL AND a.score IS NULL) THEN 'auto_grading'
  ELSE 'published' END
WHERE s.result_release_policy='IMMEDIATE' AND s.review_revision=0 AND s.published_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS session_start_request_idx
  ON assessment_session(learner_id,start_request_id) WHERE start_request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS session_review_queue_idx
  ON assessment_session(result_release_policy,release_status,submitted_at);

CREATE TABLE IF NOT EXISTS grade_review (
  review_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  attempt_id INT NOT NULL UNIQUE REFERENCES attempt(attempt_id),
  reviewer_id INT NOT NULL REFERENCES account(account_id),
  automated_score NUMERIC(5,2),
  automated_detail JSONB,
  approved_score NUMERIC(5,2) NOT NULL CHECK (approved_score >= 0),
  comments TEXT,
  reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS grade_review_reviewer_idx ON grade_review(reviewer_id,reviewed_at);
CREATE TABLE IF NOT EXISTS result_release_event (
  event_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL REFERENCES assessment_session(session_id),
  previous_status VARCHAR(20) NOT NULL,
  new_status VARCHAR(20) NOT NULL,
  reviewer_id INT REFERENCES account(account_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS result_release_event_session_idx ON result_release_event(session_id,event_id);

-- Protect every reserved question, including questions not served yet. The
-- complete immutable content stays in the session's existing JSON snapshot.
CREATE TABLE IF NOT EXISTS session_question_plan (
  session_id INT NOT NULL REFERENCES assessment_session(session_id),
  seq_no SMALLINT NOT NULL CHECK (seq_no > 0),
  question_id INT NOT NULL REFERENCES question(question_id),
  PRIMARY KEY (session_id,seq_no),
  UNIQUE (session_id,question_id)
);
CREATE INDEX IF NOT EXISTS session_question_plan_question_idx ON session_question_plan(question_id);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='assessment'::regclass AND conname='assessment_release_policy_check') THEN
    ALTER TABLE assessment ADD CONSTRAINT assessment_release_policy_check CHECK (result_release_policy IN ('IMMEDIATE','HUMAN_VERIFIED'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='assessment_session'::regclass AND conname='session_release_check') THEN
    ALTER TABLE assessment_session ADD CONSTRAINT session_release_check CHECK (
      result_release_policy IN ('IMMEDIATE','HUMAN_VERIFIED') AND review_revision >= 0 AND
      release_status IN ('unsubmitted','auto_grading','pending_review','reviewed','published','grading_failed'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='attempt'::regclass AND conname='attempt_review_revision_check') THEN
    ALTER TABLE attempt ADD CONSTRAINT attempt_review_revision_check CHECK (review_revision >= 0);
  END IF;
END $$;

CREATE OR REPLACE FUNCTION preserve_grade_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Grade review and publication audit records are immutable';
END $$;
CREATE OR REPLACE FUNCTION preserve_session_release_policy() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.result_release_policy IS DISTINCT FROM OLD.result_release_policy
     OR NEW.start_request_id IS DISTINCT FROM OLD.start_request_id THEN
    RAISE EXCEPTION 'Started assessment policy and start request are immutable';
  END IF;
  RETURN NEW;
END $$;
CREATE OR REPLACE FUNCTION preserve_planned_question() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'The reserved assessment question plan is immutable';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='session_question_plan'::regclass AND tgname='session_question_plan_immutable') THEN
    CREATE TRIGGER session_question_plan_immutable BEFORE UPDATE OR DELETE ON session_question_plan FOR EACH ROW EXECUTE FUNCTION preserve_planned_question();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='grade_review'::regclass AND tgname='grade_review_immutable') THEN
    CREATE TRIGGER grade_review_immutable BEFORE UPDATE OR DELETE ON grade_review FOR EACH ROW EXECUTE FUNCTION preserve_grade_audit();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='result_release_event'::regclass AND tgname='result_release_event_immutable') THEN
    CREATE TRIGGER result_release_event_immutable BEFORE UPDATE OR DELETE ON result_release_event FOR EACH ROW EXECUTE FUNCTION preserve_grade_audit();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='assessment_session'::regclass AND tgname='session_release_policy_immutable') THEN
    CREATE TRIGGER session_release_policy_immutable BEFORE UPDATE ON assessment_session FOR EACH ROW EXECUTE FUNCTION preserve_session_release_policy();
  END IF;
END $$;

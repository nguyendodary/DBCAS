-- DBCAS schema (PostgreSQL 17)

CREATE TABLE account (
  account_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  can_manage_roles BOOLEAN NOT NULL DEFAULT FALSE,
  avatar_data_url TEXT,
  token_version INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE role (
  role_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  role_name VARCHAR(50) NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE account_role (
  account_id INT NOT NULL,
  role_id INT NOT NULL,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (account_id, role_id)
);

CREATE TABLE user_profile (
  user_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL UNIQUE,
  full_name VARCHAR(100) NOT NULL,
  student_code VARCHAR(20),
  phone_number VARCHAR(20),
  date_of_birth DATE
);

CREATE TABLE account_identity (
  identity_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL,
  provider VARCHAR(20) NOT NULL,
  provider_user_id VARCHAR(255) NOT NULL,
  provider_email VARCHAR(255),
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (provider, provider_user_id)
);

CREATE TABLE course_learning_outcome (
  clo_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  clo_code VARCHAR(20) NOT NULL UNIQUE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE concept (
  concept_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  concept_code VARCHAR(30) NOT NULL UNIQUE,
  concept_name VARCHAR(100) NOT NULL,
  subject_area VARCHAR(100) NOT NULL,
  description TEXT,
  difficulty_level SMALLINT NOT NULL DEFAULT 1,
  CHECK (difficulty_level BETWEEN 1 AND 5)
);

CREATE TABLE clo_concept (
  clo_id INT NOT NULL,
  concept_id INT NOT NULL,
  mapping_source VARCHAR(10) NOT NULL DEFAULT 'admin',
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (clo_id, concept_id)
);

-- Prerequisite skill graph: concept_id depends on prerequisite_concept_id.
-- Directed edge prerequisite -> concept; the PK also blocks duplicate edges
-- and the CHECK blocks self-dependency. Transitive-cycle freedom is enforced
-- by the service layer on every write (a CHECK cannot see transitive edges).
CREATE TABLE concept_dependency (
  concept_id INT NOT NULL,
  prerequisite_concept_id INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (concept_id, prerequisite_concept_id),
  CHECK (concept_id <> prerequisite_concept_id)
);

CREATE TABLE question (
  question_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_type VARCHAR(10) NOT NULL,
  prompt TEXT NOT NULL,
  reference_answer TEXT,
  difficulty_level SMALLINT NOT NULL DEFAULT 1,
  points NUMERIC(5,2) NOT NULL DEFAULT 1.0,
  source VARCHAR(15) NOT NULL DEFAULT 'bank',
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_by INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (question_type IN ('mcq', 'sql', 'essay')),
  CHECK (difficulty_level BETWEEN 1 AND 5)
);

CREATE TABLE question_concept (
  question_id INT NOT NULL,
  concept_id INT NOT NULL,
  tag_source VARCHAR(10) NOT NULL DEFAULT 'admin',
  is_required BOOLEAN NOT NULL DEFAULT FALSE,
  confirmed BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (question_id, concept_id)
);

CREATE TABLE mcq_option (
  option_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL,
  option_label VARCHAR(5) NOT NULL,
  option_text TEXT NOT NULL,
  is_correct BOOLEAN NOT NULL DEFAULT FALSE
);

-- Locale-specific learner prose. English remains canonical on question,
-- mcq_option and rubric; this table contains translated display fields only.
CREATE TABLE question_translation (
  question_id INT NOT NULL REFERENCES question(question_id) ON DELETE CASCADE,
  locale VARCHAR(16) NOT NULL,
  source_hash VARCHAR(64) NOT NULL,
  prompt TEXT NOT NULL,
  explanation TEXT,
  option_texts JSONB NOT NULL DEFAULT '{}'::jsonb,
  rubrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (question_id, locale),
  CHECK (locale <> 'en' AND locale ~ '^[a-z]{2}(-[A-Z]{2})?$'),
  CHECK (jsonb_typeof(option_texts) = 'object'),
  CHECK (jsonb_typeof(rubrics) = 'object')
);
CREATE INDEX IF NOT EXISTS question_translation_locale_idx
  ON question_translation(locale, question_id);

CREATE TABLE sql_test_dataset (
  dataset_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL,
  dataset_name VARCHAR(100) NOT NULL,
  setup_sql TEXT NOT NULL,
  expected_result JSONB NOT NULL,
  is_edge_case BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE rubric (
  rubric_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL,
  level_name VARCHAR(30) NOT NULL,
  min_score NUMERIC(5,2) NOT NULL,
  max_score NUMERIC(5,2) NOT NULL,
  criteria TEXT NOT NULL,
  CHECK (min_score <= max_score)
);

CREATE TABLE assessment (
  assessment_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  max_questions SMALLINT NOT NULL DEFAULT 13,
  duration_min SMALLINT NOT NULL DEFAULT 60,
  target_mcq SMALLINT NOT NULL DEFAULT 10,
  target_sql SMALLINT NOT NULL DEFAULT 2,
  target_essay SMALLINT NOT NULL DEFAULT 1,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_by INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (max_questions BETWEEN 1 AND 13),
  CHECK (target_mcq + target_sql + target_essay <= max_questions)
);

CREATE TABLE assessment_concept (
  assessment_id INT NOT NULL,
  concept_id INT NOT NULL,
  min_difficulty SMALLINT NOT NULL DEFAULT 1,
  max_difficulty SMALLINT NOT NULL DEFAULT 5,
  target_pct NUMERIC(5,2) NOT NULL,
  PRIMARY KEY (assessment_id, concept_id),
  CHECK (min_difficulty BETWEEN 1 AND 5),
  CHECK (max_difficulty BETWEEN min_difficulty AND 5),
  CHECK (target_pct BETWEEN 0 AND 100)
);

CREATE TABLE assessment_session (
  session_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assessment_id INT NOT NULL,
  learner_id INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
  locale VARCHAR(16) NOT NULL DEFAULT 'en' CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$'),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  submitted_at TIMESTAMPTZ,
  CHECK (status IN ('in_progress', 'completed', 'timed_out'))
);

CREATE TABLE attempt (
  attempt_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  question_id INT NOT NULL,
  seq_no SMALLINT NOT NULL,
  selected_option_id INT,
  selected_option_ids JSONB,
  sql_answer TEXT,
  essay_answer TEXT,
  score NUMERIC(5,2),
  grading_detail JSONB,
  served_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  submitted_at TIMESTAMPTZ,
  UNIQUE (session_id, seq_no)
);

CREATE TABLE selection_log (
  log_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  seq_no SMALLINT NOT NULL,
  question_id INT NOT NULL,
  is_fallback BOOLEAN NOT NULL DEFAULT FALSE,
  decision_detail JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, seq_no)
);

CREATE TABLE concept_competency (
  competency_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  concept_id INT NOT NULL,
  points_earned NUMERIC(6,2) NOT NULL DEFAULT 0,
  points_possible NUMERIC(6,2) NOT NULL DEFAULT 0,
  competency_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
  below_target BOOLEAN NOT NULL DEFAULT FALSE,
  computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, concept_id)
);

CREATE TABLE competency_gap (
  gap_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  concept_id INT NOT NULL,
  llm_explanation TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, concept_id)
);

CREATE TABLE llm_cache (
  cache_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  request_hash VARCHAR(64) NOT NULL UNIQUE,
  task_type VARCHAR(30) NOT NULL,
  model VARCHAR(50) NOT NULL,
  response JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE question_candidate (
  candidate_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  concept_id INT NOT NULL,
  question_type VARCHAR(10) NOT NULL,
  payload JSONB NOT NULL,
  validation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  validation_detail JSONB,
  promoted_question_id INT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE account_role ADD FOREIGN KEY (account_id) REFERENCES account (account_id);
ALTER TABLE account_role ADD FOREIGN KEY (role_id) REFERENCES role (role_id);
ALTER TABLE user_profile ADD FOREIGN KEY (account_id) REFERENCES account (account_id);
ALTER TABLE account_identity ADD FOREIGN KEY (account_id) REFERENCES account (account_id);
ALTER TABLE course_learning_outcome ADD FOREIGN KEY (created_by) REFERENCES account (account_id);
ALTER TABLE clo_concept ADD FOREIGN KEY (clo_id) REFERENCES course_learning_outcome (clo_id);
ALTER TABLE clo_concept ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE concept_dependency ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE concept_dependency ADD FOREIGN KEY (prerequisite_concept_id) REFERENCES concept (concept_id);
ALTER TABLE question ADD FOREIGN KEY (created_by) REFERENCES account (account_id);
ALTER TABLE question_concept ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE question_concept ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE mcq_option ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE sql_test_dataset ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE rubric ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE assessment ADD FOREIGN KEY (created_by) REFERENCES account (account_id);
ALTER TABLE assessment_concept ADD FOREIGN KEY (assessment_id) REFERENCES assessment (assessment_id);
ALTER TABLE assessment_concept ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE assessment_session ADD FOREIGN KEY (assessment_id) REFERENCES assessment (assessment_id);
ALTER TABLE assessment_session ADD FOREIGN KEY (learner_id) REFERENCES account (account_id);
ALTER TABLE attempt ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE attempt ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE attempt ADD FOREIGN KEY (selected_option_id) REFERENCES mcq_option (option_id);
ALTER TABLE selection_log ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE selection_log ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE concept_competency ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE concept_competency ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE competency_gap ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE competency_gap ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE question_candidate ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE question_candidate ADD FOREIGN KEY (promoted_question_id) REFERENCES question (question_id);

-- Fresh installation extension: 002_concept_dependency.sql
-- Additive prerequisite graph upgrade for existing volumes; safe to repeat.
CREATE TABLE IF NOT EXISTS concept_dependency (
  concept_id INT NOT NULL REFERENCES concept(concept_id),
  prerequisite_concept_id INT NOT NULL REFERENCES concept(concept_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (concept_id, prerequisite_concept_id),
  CHECK (concept_id <> prerequisite_concept_id)
);
CREATE INDEX IF NOT EXISTS concept_dependency_prerequisite_idx
  ON concept_dependency(prerequisite_concept_id);

-- Fresh installation extension: 003_drafts_evidence_and_security.sql
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
CREATE OR REPLACE FUNCTION preserve_session_locale() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.locale IS DISTINCT FROM NEW.locale THEN
    RAISE EXCEPTION 'Assessment question locale is immutable';
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
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='assessment_session'::regclass AND tgname='session_locale_immutable') THEN
    CREATE TRIGGER session_locale_immutable BEFORE UPDATE ON assessment_session
      FOR EACH ROW EXECUTE FUNCTION preserve_session_locale();
  END IF;
END $$;

-- Migration 004: bank version lineage and canonical terms
-- Additive version lineage and canonical persistence terms (Database Design 1.3).
ALTER TABLE concept ADD COLUMN IF NOT EXISTS sql_feature VARCHAR(30);
-- Known legacy codes receive explicit metadata; unknown techniques need admin review.
UPDATE concept SET sql_feature = CASE upper(concept_code)
  WHEN 'SQL-SELECT' THEN 'select' WHEN 'SQL-WHERE' THEN 'where'
  WHEN 'SQL-JOIN' THEN 'join' WHEN 'SQL-GROUP' THEN 'group_by'
  WHEN 'SQL-GROUP-BY' THEN 'group_by' WHEN 'SQL-GROUPBY' THEN 'group_by'
  WHEN 'SQL-HAVING' THEN 'having' WHEN 'SQL-SUBQUERY' THEN 'subquery'
  WHEN 'SQL-COALESCE' THEN 'null_handling' ELSE NULL END
WHERE sql_feature IS NULL;
ALTER TABLE question ADD COLUMN IF NOT EXISTS family_id INT REFERENCES question(question_id);
ALTER TABLE question ADD COLUMN IF NOT EXISTS version_no INT NOT NULL DEFAULT 1;
ALTER TABLE assessment ADD COLUMN IF NOT EXISTS family_id INT REFERENCES assessment(assessment_id);
ALTER TABLE assessment ADD COLUMN IF NOT EXISTS version_no INT NOT NULL DEFAULT 1;

UPDATE question SET source='ai_generated' WHERE source='ai';
UPDATE question SET status='retired' WHERE status='rejected';
UPDATE assessment SET status='published' WHERE status='active';
UPDATE question_candidate SET validation_status='validated'
  WHERE validation_status='approved' AND promoted_question_id IS NOT NULL;
UPDATE question_concept SET review_status='confirmed' WHERE confirmed AND review_status <> 'confirmed';

CREATE UNIQUE INDEX IF NOT EXISTS question_family_version_idx
  ON question(COALESCE(family_id,question_id),version_no);
CREATE UNIQUE INDEX IF NOT EXISTS assessment_family_version_idx
  ON assessment(COALESCE(family_id,assessment_id),version_no);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='question_terms_check' AND conrelid='question'::regclass) THEN
    ALTER TABLE question ADD CONSTRAINT question_terms_check
      CHECK (source IN ('bank','ai_generated') AND status IN ('draft','validated','retired') AND points > 0 AND version_no > 0);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='assessment_terms_check' AND conrelid='assessment'::regclass) THEN
    ALTER TABLE assessment ADD CONSTRAINT assessment_terms_check
      CHECK (status IN ('draft','published','closed') AND version_no > 0);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='clo_review_check' AND conrelid='clo_concept'::regclass) THEN
    ALTER TABLE clo_concept ADD CONSTRAINT clo_review_check
      CHECK (mapping_source IN ('admin','ai') AND status IN ('pending','confirmed','rejected'));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='tag_review_check' AND conrelid='question_concept'::regclass) THEN
    ALTER TABLE question_concept ADD CONSTRAINT tag_review_check
      CHECK (tag_source IN ('admin','ai') AND review_status IN ('pending','confirmed','rejected')
             AND confirmed = (review_status='confirmed'));
  END IF;
END $$;

-- 005_release_roles.sql: reference roles without development accounts.
INSERT INTO role (role_name, description) VALUES
  ('Learner', 'Takes adaptive assessments and views competency results'),
  ('Administrator', 'Curates curriculum, questions and assessments')
ON CONFLICT (role_name) DO NOTHING;

-- 006_question_provenance.sql: official-source provenance for curated items.
ALTER TABLE question ADD COLUMN IF NOT EXISTS explanation TEXT;
ALTER TABLE question ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE question ADD COLUMN IF NOT EXISTS source_refs JSONB NOT NULL DEFAULT '[]'::jsonb;

-- 008_personalization_and_verified_results.sql
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

-- 009_incomplete_grade_release_repair.sql
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

-- 010_session_start_request_bindings.sql
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

-- 011_secure_role_management.sql
ALTER TABLE account ADD COLUMN IF NOT EXISTS can_manage_roles BOOLEAN NOT NULL DEFAULT FALSE;
CREATE TABLE IF NOT EXISTS account_role_audit (
  audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  action_type VARCHAR(40) NOT NULL,
  actor_account_id INT REFERENCES account(account_id),
  target_account_id INT NOT NULL REFERENCES account(account_id),
  previous_role VARCHAR(50),
  new_role VARCHAR(50),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT account_role_audit_action_check CHECK (
    (action_type IN ('ROLE_GRANTED', 'ROLE_REVOKED') AND actor_account_id IS NOT NULL
      AND previous_role IN ('Learner', 'Administrator')
      AND new_role IN ('Learner', 'Administrator') AND previous_role <> new_role)
    OR (action_type = 'ROLE_MANAGER_BOOTSTRAPPED' AND actor_account_id IS NULL
      AND previous_role IS NULL AND new_role IS NULL)
  )
);
CREATE INDEX IF NOT EXISTS account_role_audit_target_idx ON account_role_audit(target_account_id,audit_id DESC);
CREATE INDEX IF NOT EXISTS account_role_audit_actor_idx ON account_role_audit(actor_account_id,audit_id DESC);
CREATE OR REPLACE FUNCTION preserve_account_role_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Account role audit records are immutable';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='account_role_audit'::regclass AND tgname='account_role_audit_immutable') THEN
    CREATE TRIGGER account_role_audit_immutable BEFORE UPDATE OR DELETE ON account_role_audit
      FOR EACH ROW EXECUTE FUNCTION preserve_account_role_audit();
  END IF;
END $$;

-- Learner result release choice (migration 013).
-- A learner may choose the release mode once, while submitting their session.
-- Existing results, configuration snapshots and start requests are preserved.
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

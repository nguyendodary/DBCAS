-- DBCAS schema (PostgreSQL 17)

CREATE TABLE account (
  account_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
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

-- DBCAS schema (PostgreSQL 17)
-- Refresh-token storage is declared at the end, after account exists.

CREATE TABLE account (
  account_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  -- FALSE only for accounts created through OAuth whose password hash is
  -- an unusable random value; a password reset flips it to TRUE.
  password_set BOOLEAN NOT NULL DEFAULT TRUE,
  password_changed_at TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  can_manage_roles BOOLEAN NOT NULL DEFAULT FALSE,
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

-- One direct CLO assignment or AI proposal per question/CLO pair. The partial
-- unique index below permits only one active primary CLO per question.
CREATE TABLE question_clo (
  question_id INT NOT NULL,
  clo_id INT NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  tag_source VARCHAR(10) NOT NULL DEFAULT 'admin',
  confirmed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (question_id, clo_id),
  CONSTRAINT question_clo_status_check
    CHECK (status IN ('pending', 'confirmed', 'rejected')),
  CONSTRAINT question_clo_source_check
    CHECK (tag_source IN ('admin', 'auto', 'ai'))
);
CREATE UNIQUE INDEX IF NOT EXISTS question_clo_primary_idx
  ON question_clo(question_id)
  WHERE is_primary AND status <> 'rejected';
CREATE INDEX IF NOT EXISTS question_clo_clo_idx ON question_clo(clo_id);
CREATE INDEX IF NOT EXISTS question_clo_status_idx ON question_clo(status);

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
  purpose VARCHAR(10) NOT NULL DEFAULT 'PRACTICE'
    CHECK (purpose IN ('TEST', 'PRACTICE')),
  purpose_source VARCHAR(10) NOT NULL DEFAULT 'SERVER'
    CHECK (purpose_source IN ('SERVER', 'BACKFILL')),
  locale VARCHAR(16) NOT NULL DEFAULT 'en' CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$'),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  submitted_at TIMESTAMPTZ,
  CHECK (status IN ('in_progress', 'completed', 'timed_out', 'cancelled'))
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
  is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
  flag_revision INT NOT NULL DEFAULT 0 CHECK (flag_revision >= 0),
  first_opened_at TIMESTAMPTZ,
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

-- Admin-supplied course documents (migration 023). The uploaded file is never
-- stored: only extracted text, chunk text and checksums are persisted.
CREATE TABLE course_document (
  document_id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  title VARCHAR(300) NOT NULL,
  source_type VARCHAR(20) NOT NULL DEFAULT 'upload',
  mime_type VARCHAR(100) NOT NULL,
  original_filename VARCHAR(255),
  sha256 VARCHAR(64) NOT NULL,
  char_count INT NOT NULL,
  page_count INT,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  uploaded_by INT NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  approved_by INT,
  approved_at TIMESTAMPTZ,
  text_policy_version VARCHAR(20) NOT NULL DEFAULT 'untrusted-v1',
  CONSTRAINT course_document_status_check
    CHECK (status IN ('draft', 'approved', 'archived')),
  CONSTRAINT course_document_source_check
    CHECK (source_type IN ('upload')),
  CONSTRAINT course_document_sha256_check
    CHECK (sha256 ~ '^[a-f0-9]{64}$'),
  CONSTRAINT course_document_counts_check
    CHECK (char_count >= 1 AND (page_count IS NULL OR page_count >= 1)),
  CONSTRAINT course_document_uploaded_by_fk
    FOREIGN KEY (uploaded_by) REFERENCES account (account_id),
  CONSTRAINT course_document_approved_by_fk
    FOREIGN KEY (approved_by) REFERENCES account (account_id)
);
CREATE INDEX IF NOT EXISTS course_document_status_idx
  ON course_document(status, uploaded_at DESC);

CREATE TABLE document_chunk (
  chunk_id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  document_id INT NOT NULL,
  ordinal INT NOT NULL,
  page_from INT,
  page_to INT,
  heading TEXT,
  text TEXT NOT NULL,
  text_hash VARCHAR(64) NOT NULL,
  char_count INT NOT NULL,
  CONSTRAINT document_chunk_document_fk
    FOREIGN KEY (document_id) REFERENCES course_document (document_id)
    ON DELETE CASCADE,
  CONSTRAINT document_chunk_document_ordinal_key UNIQUE (document_id, ordinal),
  CONSTRAINT document_chunk_ordinal_check CHECK (ordinal >= 1),
  CONSTRAINT document_chunk_pages_check CHECK (
    (page_from IS NULL OR page_from >= 1)
    AND (page_to IS NULL OR page_from IS NULL OR page_to >= page_from)
  ),
  CONSTRAINT document_chunk_text_check CHECK (length(text) >= 1),
  CONSTRAINT document_chunk_chars_check CHECK (char_count = length(text)),
  CONSTRAINT document_chunk_hash_check CHECK (text_hash ~ '^[a-f0-9]{64}$')
);
CREATE INDEX IF NOT EXISTS document_chunk_document_idx
  ON document_chunk(document_id, ordinal);

CREATE TABLE document_clo (
  document_id INT NOT NULL,
  clo_id INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'approved',
  approved_by INT,
  approved_at TIMESTAMPTZ,
  PRIMARY KEY (document_id, clo_id),
  CONSTRAINT document_clo_document_fk
    FOREIGN KEY (document_id) REFERENCES course_document (document_id)
    ON DELETE CASCADE,
  CONSTRAINT document_clo_clo_fk
    FOREIGN KEY (clo_id) REFERENCES course_learning_outcome (clo_id),
  CONSTRAINT document_clo_approved_by_fk
    FOREIGN KEY (approved_by) REFERENCES account (account_id),
  CONSTRAINT document_clo_status_check
    CHECK (status IN ('pending', 'approved', 'rejected'))
);
CREATE INDEX IF NOT EXISTS document_clo_clo_idx
  ON document_clo(clo_id, status);

CREATE TABLE question_evidence (
  evidence_id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL,
  chunk_id INT NOT NULL,
  quote TEXT NOT NULL,
  start_offset INT,
  end_offset INT,
  source_hash VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT question_evidence_question_fk
    FOREIGN KEY (question_id) REFERENCES question (question_id) ON DELETE CASCADE,
  CONSTRAINT question_evidence_chunk_fk
    FOREIGN KEY (chunk_id) REFERENCES document_chunk (chunk_id),
  CONSTRAINT question_evidence_quote_check CHECK (length(quote) >= 1),
  CONSTRAINT question_evidence_offsets_check CHECK (
    (start_offset IS NULL OR start_offset >= 0)
    AND (end_offset IS NULL OR start_offset IS NULL OR end_offset >= start_offset)
  ),
  CONSTRAINT question_evidence_hash_check
    CHECK (source_hash ~ '^[a-f0-9]{64}$')
);
CREATE INDEX IF NOT EXISTS question_evidence_question_idx
  ON question_evidence(question_id);
CREATE INDEX IF NOT EXISTS question_evidence_chunk_idx
  ON question_evidence(chunk_id);

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
ALTER TABLE question_clo ADD CONSTRAINT question_clo_question_fk FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE question_clo ADD CONSTRAINT question_clo_clo_fk FOREIGN KEY (clo_id) REFERENCES course_learning_outcome (clo_id);
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

-- Self-service password recovery: only the SHA-256 digest of a reset
-- token is stored; a row is redeemable while used_at/revoked_at are NULL
-- and expires_at is in the future. Issuing a new token revokes older
-- unredeemed tokens for the same account.
CREATE TABLE IF NOT EXISTS password_reset_token (
  token_hash VARCHAR(64) PRIMARY KEY,
  account_id INT NOT NULL REFERENCES account(account_id),
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  CHECK (expires_at > requested_at)
);
CREATE INDEX IF NOT EXISTS password_reset_token_account_idx
  ON password_reset_token(account_id, requested_at DESC);
CREATE INDEX IF NOT EXISTS password_reset_token_expiry_idx
  ON password_reset_token(expires_at);

CREATE TABLE IF NOT EXISTS password_reset_audit (
  audit_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL REFERENCES account(account_id),
  event VARCHAR(20) NOT NULL CHECK (event IN ('requested', 'completed')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS password_reset_audit_account_idx
  ON password_reset_audit(account_id, audit_id DESC);

CREATE OR REPLACE FUNCTION preserve_password_reset_audit() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Password reset audit is immutable';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='password_reset_audit'::regclass
                 AND tgname='password_reset_audit_immutable') THEN
    CREATE TRIGGER password_reset_audit_immutable BEFORE UPDATE OR DELETE ON password_reset_audit
      FOR EACH ROW EXECUTE FUNCTION preserve_password_reset_audit();
  END IF;
END $$;

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
CREATE INDEX IF NOT EXISTS assessment_session_purpose_idx ON assessment_session(learner_id,purpose,purpose_source,started_at DESC);
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

-- Original-language question authoring (migration 012).
-- Source prose has an explicit language. Existing source prose remains English.
-- No questions, translations, attempts or historical snapshots are rewritten.
ALTER TABLE question ADD COLUMN IF NOT EXISTS original_locale VARCHAR(16) NOT NULL DEFAULT 'en';
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='question'::regclass AND conname='question_original_locale_check') THEN
    ALTER TABLE question ADD CONSTRAINT question_original_locale_check CHECK (original_locale IN ('en', 'vi'));
  END IF;
END $$;

-- Migration 007 excluded English because English was always the source.
-- Locate that constraint by definition, including databases with renamed checks.
DO $$ DECLARE item RECORD; BEGIN
  FOR item IN SELECT conname FROM pg_constraint
    WHERE conrelid='question_translation'::regclass AND contype='c'
      AND pg_get_constraintdef(oid) LIKE '%locale%'
      AND pg_get_constraintdef(oid) LIKE '%<>%'
      AND pg_get_constraintdef(oid) LIKE '%en%'
  LOOP
    EXECUTE format('ALTER TABLE question_translation DROP CONSTRAINT %I', item.conname);
  END LOOP;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='question_translation'::regclass AND conname='question_translation_supported_locale_check') THEN
    ALTER TABLE question_translation ADD CONSTRAINT question_translation_supported_locale_check
      CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$');
  END IF;
END $$;

-- 013_assessment_blueprints.sql
CREATE TABLE IF NOT EXISTS assessment_blueprint (
  blueprint_id INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  -- Blueprint history belongs to the assessment; the delete guard in the
  -- application prevents deletion of assessments that have sessions, so a
  -- cascade here never removes a version referenced by a session snapshot.
  assessment_id INT NOT NULL REFERENCES assessment(assessment_id) ON DELETE CASCADE,
  subject_area VARCHAR(100) NOT NULL,
  difficulty_band VARCHAR(10) NOT NULL,
  version_no INT NOT NULL DEFAULT 1,
  status VARCHAR(20) NOT NULL DEFAULT 'approved',
  max_questions SMALLINT NOT NULL,
  target_mcq SMALLINT NOT NULL,
  target_sql SMALLINT NOT NULL,
  target_essay SMALLINT NOT NULL,
  scoring JSONB NOT NULL DEFAULT '{}'::jsonb,
  evidence_types JSONB NOT NULL DEFAULT '[]'::jsonb,
  approval_basis TEXT NOT NULL,
  approved_by INT REFERENCES account(account_id),
  approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT assessment_blueprint_band_check
    CHECK (difficulty_band IN ('EASY', 'MEDIUM', 'HARD')),
  CONSTRAINT assessment_blueprint_status_check
    CHECK (status IN ('approved', 'retired')),
  CONSTRAINT assessment_blueprint_counts_check
    CHECK (max_questions > 0 AND target_mcq >= 0 AND target_sql >= 0
           AND target_essay >= 0 AND target_mcq + target_sql + target_essay = max_questions),
  CONSTRAINT assessment_blueprint_version_check CHECK (version_no > 0),
  CONSTRAINT assessment_blueprint_scoring_check
    CHECK (jsonb_typeof(scoring) = 'object'),
  CONSTRAINT assessment_blueprint_evidence_check
    CHECK (jsonb_typeof(evidence_types) = 'array'),
  CONSTRAINT assessment_blueprint_approval_check
    CHECK (length(btrim(approval_basis)) > 0),
  CONSTRAINT assessment_blueprint_version_unique
    UNIQUE (assessment_id, subject_area, difficulty_band, version_no)
);
CREATE INDEX IF NOT EXISTS assessment_blueprint_lookup_idx
  ON assessment_blueprint(assessment_id, subject_area, difficulty_band, version_no DESC);
ALTER TABLE assessment_session
  ADD COLUMN IF NOT EXISTS blueprint_id INT REFERENCES assessment_blueprint(blueprint_id);

-- A new version is a new row. No version is ever rewritten; the rows that a
-- published session snapshot references cannot be deleted without deleting
-- that session first (assessment_session.blueprint_id FK).
CREATE OR REPLACE FUNCTION preserve_assessment_blueprint() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Assessment blueprint versions are immutable; insert a new version';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='assessment_blueprint'::regclass
                 AND tgname='assessment_blueprint_immutable') THEN
    CREATE TRIGGER assessment_blueprint_immutable
      BEFORE UPDATE ON assessment_blueprint
      FOR EACH ROW EXECUTE FUNCTION preserve_assessment_blueprint();
  END IF;
END $$;
-- Optional adaptive practice adds evidence; no historical row is rewritten.
-- Policy and inventory remain in the existing immutable session snapshot.
CREATE TABLE IF NOT EXISTS adaptive_event (
  session_id INT NOT NULL REFERENCES assessment_session(session_id),
  round_no SMALLINT NOT NULL CHECK (round_no BETWEEN 1 AND 13),
  event_type VARCHAR(16) NOT NULL CHECK (event_type IN ('batch', 'decision')),
  payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (session_id, round_no, event_type)
);

CREATE OR REPLACE FUNCTION preserve_adaptive_event() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Adaptive selection and decision evidence is immutable';
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='adaptive_event'::regclass AND tgname='adaptive_event_immutable') THEN
    CREATE TRIGGER adaptive_event_immutable BEFORE UPDATE OR DELETE ON adaptive_event
      FOR EACH ROW EXECUTE FUNCTION preserve_adaptive_event();
  END IF;
END $$;

-- Refresh credentials are random bearer values; persist only their SHA-256 hash.
CREATE TABLE IF NOT EXISTS refresh_session (
  token_hash VARCHAR(64) PRIMARY KEY CHECK (token_hash ~ '^[0-9a-f]{64}$'),
  family_id VARCHAR(32) NOT NULL CHECK (family_id ~ '^[0-9a-f]{32}$'),
  account_id INT NOT NULL REFERENCES account(account_id) ON DELETE CASCADE,
  credential_version BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS refresh_session_family_idx ON refresh_session(family_id);
CREATE INDEX IF NOT EXISTS refresh_session_account_idx ON refresh_session(account_id);
CREATE INDEX IF NOT EXISTS refresh_session_expiry_idx ON refresh_session(expires_at);

-- Optional curated pool; an empty pool keeps existing concept-based selection.
CREATE TABLE IF NOT EXISTS assessment_question (
  assessment_id INT NOT NULL REFERENCES assessment(assessment_id) ON DELETE CASCADE,
  question_id INT NOT NULL REFERENCES question(question_id),
  PRIMARY KEY (assessment_id, question_id)
);
CREATE INDEX IF NOT EXISTS assessment_question_question_idx ON assessment_question(question_id);

-- Historical assessment FKs remain valid; new practice sessions have no exam.
ALTER TABLE assessment_session ALTER COLUMN assessment_id DROP NOT NULL;
CREATE TABLE IF NOT EXISTS system_setting (
  setting_key VARCHAR(80) PRIMARY KEY,
  value JSONB NOT NULL,
  updated_by INT REFERENCES account(account_id),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO system_setting(setting_key, value) VALUES ('result_flow', '"IMMEDIATE"') ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS evaluation_record (
  evaluation_id SERIAL PRIMARY KEY,
  learner_id INT NOT NULL REFERENCES account(account_id),
  session_id INT REFERENCES assessment_session(session_id),
  scope_key VARCHAR(80) NOT NULL,
  input_hash VARCHAR(64) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','ready')),
  payload JSONB,
  lease_until TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (learner_id, scope_key)
);
CREATE INDEX IF NOT EXISTS evaluation_record_jobs ON evaluation_record(status, updated_at);
CREATE TABLE IF NOT EXISTS grade_edit_audit (
  audit_id SERIAL PRIMARY KEY,
  attempt_id INT NOT NULL REFERENCES attempt(attempt_id),
  reviewer_id INT NOT NULL REFERENCES account(account_id),
  old_score NUMERIC(5,2),
  new_score NUMERIC(5,2) NOT NULL CHECK (new_score >= 0),
  reason VARCHAR(1000) NOT NULL CHECK (length(trim(reason)) >= 3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE OR REPLACE FUNCTION reject_grade_edit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Grade edit audit is immutable'; END $$;
DROP TRIGGER IF EXISTS grade_edit_audit_immutable ON grade_edit_audit;
CREATE TRIGGER grade_edit_audit_immutable BEFORE UPDATE OR DELETE ON grade_edit_audit
FOR EACH ROW EXECUTE FUNCTION reject_grade_edit_mutation();

-- Preserve all historical FKs and snapshots; prebuilt exams cannot be started.
UPDATE assessment SET status = 'closed' WHERE status = 'published';

-- ---------------------------------------------------------------------------
-- 020_provisional_ai_final_results.sql (provisional AI final results).
-- Mirrored from db/migrations/020_provisional_ai_final_results.sql so a fresh
-- load of this file describes the same catalog as the migration chain.
-- Every statement is idempotent; the legacy backfill is data-only and stays in
-- the migration so it runs exactly once per upgraded database.
-- ---------------------------------------------------------------------------
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

-- 024_tab_leave_guard.sql: FIXED-paper v1 tab-leave anti-cheat.
-- Additive only. The server measures each reported leave interval; clients
-- never supply the away duration. Existing sessions keep zero violations.
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS tab_leave_count INT NOT NULL DEFAULT 0;
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
ALTER TABLE assessment_session ADD COLUMN IF NOT EXISTS cancel_reason VARCHAR(40);
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='assessment_session'::regclass
                 AND conname='assessment_session_tab_leave_count_check') THEN
    ALTER TABLE assessment_session ADD CONSTRAINT assessment_session_tab_leave_count_check
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
CREATE UNIQUE INDEX IF NOT EXISTS tab_leave_interval_open_idx
  ON tab_leave_interval(session_id) WHERE returned_at IS NULL;
CREATE INDEX IF NOT EXISTS tab_leave_interval_session_idx
  ON tab_leave_interval(session_id, left_at DESC);


-- ---------------------------------------------------------------------------
-- 026_pr3a_database_foundation.sql (PR 3A result foundation).
-- Mirrored verbatim from db/migrations/026_pr3a_database_foundation.sql so a
-- fresh load of this file describes the same catalog as the migration chain.
-- Every statement is idempotent; see test_026_schema_sql_matches_migration_catalog.
-- PR 3A MIGRATION 026 BEGIN (mirrored from db/migrations/026_pr3a_database_foundation.sql)
-- ---------------------------------------------------------------------------

-- PR 3A database foundation.
-- Adds immutable result evidence, rubric snapshots, AI stage/validation runs,
-- prompt retention audit, and mutable publication state.
-- Additive only. Existing rows and migrations are not rewritten.

-- ---------------------------------------------------------------------------
-- Keys required for composite foreign keys.
-- ---------------------------------------------------------------------------
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='attempt'::regclass AND conname='attempt_session_attempt_uk'
  ) THEN
    ALTER TABLE attempt ADD CONSTRAINT attempt_session_attempt_uk
      UNIQUE (session_id, attempt_id);
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Weighted essay rubric profiles and immutable attempt snapshots.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS question_rubric_profile (
  rubric_profile_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL REFERENCES question(question_id),
  version_no INT NOT NULL CHECK (version_no > 0),
  status VARCHAR(10) NOT NULL CHECK (status IN ('active','retired')),
  profile_hash CHAR(64) NOT NULL CHECK (profile_hash ~ '^[0-9a-f]{64}$'),
  created_by INT NOT NULL REFERENCES account(account_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  retired_at TIMESTAMPTZ NULL,
  UNIQUE (question_id, version_no),
  UNIQUE (question_id, rubric_profile_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS question_rubric_profile_active_idx
  ON question_rubric_profile (question_id) WHERE status = 'active';

CREATE TABLE IF NOT EXISTS question_rubric_criterion (
  criterion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  rubric_profile_id BIGINT NOT NULL
    REFERENCES question_rubric_profile(rubric_profile_id),
  criterion_code VARCHAR(40) NOT NULL,
  criterion_name VARCHAR(120) NOT NULL,
  description TEXT NOT NULL,
  scoring_guidance TEXT NOT NULL,
  max_points NUMERIC(5,2) NOT NULL CHECK (max_points > 0),
  sort_order SMALLINT NOT NULL CHECK (sort_order > 0),
  criterion_hash CHAR(64) NOT NULL CHECK (criterion_hash ~ '^[0-9a-f]{64}$'),
  UNIQUE (rubric_profile_id, criterion_code),
  UNIQUE (rubric_profile_id, sort_order)
);

CREATE TABLE IF NOT EXISTS attempt_rubric_criterion (
  criterion_snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  attempt_id INT NOT NULL,
  question_id INT NOT NULL,
  rubric_profile_id BIGINT NOT NULL,
  criterion_id BIGINT NOT NULL,
  criterion_code VARCHAR(40) NOT NULL,
  criterion_name VARCHAR(120) NOT NULL,
  description TEXT NOT NULL,
  scoring_guidance TEXT NOT NULL,
  max_points NUMERIC(5,2) NOT NULL CHECK (max_points > 0),
  sort_order SMALLINT NOT NULL CHECK (sort_order > 0),
  profile_snapshot_hash CHAR(64) NOT NULL
    CHECK (profile_snapshot_hash ~ '^[0-9a-f]{64}$'),
  criterion_hash CHAR(64) NOT NULL CHECK (criterion_hash ~ '^[0-9a-f]{64}$'),
  UNIQUE (session_id, attempt_id, criterion_snapshot_id),
  UNIQUE (attempt_id, criterion_id),
  FOREIGN KEY (session_id, attempt_id)
    REFERENCES attempt(session_id, attempt_id),
  FOREIGN KEY (question_id, rubric_profile_id)
    REFERENCES question_rubric_profile(question_id, rubric_profile_id),
  FOREIGN KEY (criterion_id) REFERENCES question_rubric_criterion(criterion_id)
);

-- ---------------------------------------------------------------------------
-- Immutable result evidence.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_result_version (
  result_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL REFERENCES assessment_session(session_id),
  version_no INT NOT NULL CHECK (version_no >= 1),
  source VARCHAR(10) NOT NULL CHECK (source IN ('V1','V2')),
  supersedes_version_id BIGINT NULL
    REFERENCES session_result_version(result_version_id),
  total_score NUMERIC(7,2) NOT NULL,
  max_score NUMERIC(7,2) NOT NULL,
  result_hash CHAR(64) NOT NULL CHECK (result_hash ~ '^[0-9a-f]{64}$'),
  approved_by INT NULL REFERENCES account(account_id),
  approved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  approved_draft_hash CHAR(64) NULL,
  approved_review_revision INT NOT NULL DEFAULT 0
    CHECK (approved_review_revision >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, version_no),
  UNIQUE (session_id, result_version_id),
  CHECK (total_score >= 0 AND total_score <= max_score),
  CHECK (source = 'V1' OR approved_by IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS session_result_version_score (
  version_score_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  result_version_id BIGINT NOT NULL,
  attempt_id INT NOT NULL,
  score NUMERIC(5,2) NOT NULL,
  max_score NUMERIC(5,2) NOT NULL,
  source VARCHAR(20) NOT NULL
    CHECK (source IN ('MACHINE','AI2','REVIEW','REGRADE')),
  UNIQUE (session_id, result_version_id, attempt_id),
  FOREIGN KEY (session_id, result_version_id)
    REFERENCES session_result_version(session_id, result_version_id),
  FOREIGN KEY (session_id, attempt_id)
    REFERENCES attempt(session_id, attempt_id),
  CHECK (score >= 0 AND score <= max_score)
);

CREATE TABLE IF NOT EXISTS session_result_criterion_score (
  criterion_score_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  result_version_id BIGINT NOT NULL,
  attempt_id INT NOT NULL,
  criterion_snapshot_id BIGINT NOT NULL,
  score NUMERIC(5,2) NOT NULL,
  max_points NUMERIC(5,2) NOT NULL,
  comment VARCHAR(2000) NULL,
  UNIQUE (session_id, result_version_id, attempt_id, criterion_snapshot_id),
  FOREIGN KEY (session_id, result_version_id, attempt_id)
    REFERENCES session_result_version_score(session_id, result_version_id, attempt_id),
  FOREIGN KEY (session_id, attempt_id, criterion_snapshot_id)
    REFERENCES attempt_rubric_criterion(session_id, attempt_id, criterion_snapshot_id),
  CHECK (score >= 0 AND score <= max_points)
);

-- ---------------------------------------------------------------------------
-- Mutable publication state, kept separate from immutable result evidence.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_result_publication (
  result_version_id BIGINT PRIMARY KEY,
  session_id INT NOT NULL,
  state VARCHAR(30) NOT NULL CHECK (state IN
    ('APPROVED_PENDING_ANALYSIS','ANALYSIS_FAILED','OFFICIAL')),
  state_revision INT NOT NULL DEFAULT 0 CHECK (state_revision >= 0),
  published_at TIMESTAMPTZ NULL,
  analysis_failed_at TIMESTAMPTZ NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by INT NULL REFERENCES account(account_id),
  UNIQUE (session_id, result_version_id),
  FOREIGN KEY (session_id, result_version_id)
    REFERENCES session_result_version(session_id, result_version_id),
  CHECK ((state = 'OFFICIAL') = (published_at IS NOT NULL)),
  CHECK ((state = 'ANALYSIS_FAILED') = (analysis_failed_at IS NOT NULL))
);

-- ---------------------------------------------------------------------------
-- AI stage runs, attempts, validation, prompts, and retention audit.
-- scope_key is either 'v1' or v2 plus a positive decimal review_request_id.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_stage_run (
  stage_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL REFERENCES assessment_session(session_id),
  scope_key VARCHAR(40) NOT NULL
    CHECK (scope_key = 'v1' OR scope_key ~ '^v2:[1-9][0-9]*$'),
  stage VARCHAR(3) NOT NULL CHECK (stage IN ('AI1','AI2')),
  run_mode VARCHAR(20) NOT NULL CHECK (run_mode IN ('V1_GRADING','V2_ANALYSIS')),
  result_version_id BIGINT NULL
    REFERENCES session_result_version(result_version_id),
  execution_run_no INT NOT NULL CHECK (execution_run_no >= 1),
  recovery_of_run_id BIGINT NULL REFERENCES ai_stage_run(stage_run_id),
  recovery_authorized_by INT NULL REFERENCES account(account_id),
  recovery_reason VARCHAR(1000) NULL,
  predecessor_validation_id BIGINT NULL,
  status VARCHAR(20) NOT NULL CHECK (status IN
    ('PENDING','PROCESSING','RETRY_WAIT','COMPLETED','FAILED','CANCELLED')),
  attempt_count INT NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 3),
  input_hash CHAR(64) NOT NULL CHECK (input_hash ~ '^[0-9a-f]{64}$'),
  output_hash CHAR(64) NULL CHECK (output_hash IS NULL OR output_hash ~ '^[0-9a-f]{64}$'),
  last_error_code VARCHAR(80) NULL,
  available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  lease_until TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ NULL,
  finished_at TIMESTAMPTZ NULL,
  UNIQUE (stage_run_id, session_id),
  UNIQUE (session_id, scope_key, stage, execution_run_no),
  CHECK (
    (scope_key = 'v1' AND run_mode = 'V1_GRADING')
    OR
    (scope_key ~ '^v2:[1-9][0-9]*$' AND run_mode = 'V2_ANALYSIS')
  ),
  CHECK (
    (recovery_of_run_id IS NULL AND recovery_authorized_by IS NULL AND recovery_reason IS NULL)
    OR
    (recovery_of_run_id IS NOT NULL AND recovery_authorized_by IS NOT NULL
      AND recovery_reason IS NOT NULL AND length(btrim(recovery_reason)) >= 20)
  ),
  CHECK (
    (stage = 'AI1' AND predecessor_validation_id IS NULL)
    OR
    (stage = 'AI2' AND predecessor_validation_id IS NOT NULL)
  )
);
CREATE UNIQUE INDEX IF NOT EXISTS ai_stage_run_active_session_idx
  ON ai_stage_run (session_id, scope_key, stage)
  WHERE status IN ('PENDING','PROCESSING','RETRY_WAIT');

CREATE TABLE IF NOT EXISTS ai_stage_validation (
  validation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  stage_run_id BIGINT NOT NULL,
  validator_version VARCHAR(40) NOT NULL,
  input_hash CHAR(64) NOT NULL CHECK (input_hash ~ '^[0-9a-f]{64}$'),
  output_hash CHAR(64) NOT NULL CHECK (output_hash ~ '^[0-9a-f]{64}$'),
  status VARCHAR(10) NOT NULL CHECK (status IN ('VALID','INVALID')),
  validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (stage_run_id),
  FOREIGN KEY (stage_run_id, session_id)
    REFERENCES ai_stage_run(stage_run_id, session_id)
);

ALTER TABLE ai_stage_run DROP CONSTRAINT IF EXISTS ai_stage_run_predecessor_fk;
ALTER TABLE ai_stage_run ADD CONSTRAINT ai_stage_run_predecessor_fk
  FOREIGN KEY (predecessor_validation_id) REFERENCES ai_stage_validation(validation_id);

CREATE TABLE IF NOT EXISTS ai_stage_attempt (
  stage_attempt_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  stage_run_id BIGINT NOT NULL,
  attempt_no INT NOT NULL CHECK (attempt_no BETWEEN 1 AND 3),
  status VARCHAR(20) NOT NULL CHECK (status IN ('STARTED','SUCCEEDED','FAILED')),
  input_hash CHAR(64) NOT NULL CHECK (input_hash ~ '^[0-9a-f]{64}$'),
  output_hash CHAR(64) NULL CHECK (output_hash IS NULL OR output_hash ~ '^[0-9a-f]{64}$'),
  error_code VARCHAR(80) NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ NULL,
  UNIQUE (session_id, stage_run_id, attempt_no),
  FOREIGN KEY (stage_run_id, session_id)
    REFERENCES ai_stage_run(stage_run_id, session_id)
);

CREATE TABLE IF NOT EXISTS ai_prompt_record (
  prompt_record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  stage_run_id BIGINT NOT NULL,
  stage VARCHAR(3) NOT NULL CHECK (stage IN ('AI1','AI2')),
  prompt_hash CHAR(64) NOT NULL CHECK (prompt_hash ~ '^[0-9a-f]{64}$'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  purged_at TIMESTAMPTZ NULL,
  FOREIGN KEY (stage_run_id, session_id)
    REFERENCES ai_stage_run(stage_run_id, session_id),
  CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS ai_prompt_record_expires_idx
  ON ai_prompt_record (expires_at);

CREATE TABLE IF NOT EXISTS ai_prompt_content (
  prompt_record_id BIGINT PRIMARY KEY
    REFERENCES ai_prompt_record(prompt_record_id),
  prompt_text TEXT NULL,
  model_identifier VARCHAR(80) NULL
);

CREATE TABLE IF NOT EXISTS retention_purge_audit (
  purge_audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  object_type VARCHAR(20) NOT NULL CHECK (object_type IN ('PROMPT_CONTENT','LLM_CACHE')),
  object_id TEXT NOT NULL,
  content_hash CHAR(64) NULL,
  purged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  purge_reason VARCHAR(40) NOT NULL CHECK (purge_reason IN
    ('AGE_60_DAYS','MANUAL_ADMIN','MIGRATION_BACKFILL')),
  actor VARCHAR(80) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prompt_access_audit (
  access_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  prompt_record_id BIGINT NOT NULL
    REFERENCES ai_prompt_record(prompt_record_id),
  actor_id INT NOT NULL REFERENCES account(account_id),
  result VARCHAR(20) NOT NULL CHECK (result IN
    ('GRANTED','DENIED_EXPIRED','DENIED_PURGED')),
  accessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  request_id UUID NULL
);
CREATE INDEX IF NOT EXISTS prompt_access_audit_record_idx
  ON prompt_access_audit (prompt_record_id, accessed_at);

CREATE TABLE IF NOT EXISTS session_result_analysis (
  analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  result_version_id BIGINT NOT NULL,
  ai1_run_id BIGINT NOT NULL,
  ai2_run_id BIGINT NOT NULL,
  analysis_schema_version INT NOT NULL CHECK (analysis_schema_version > 0),
  analysis_hash CHAR(64) NOT NULL CHECK (analysis_hash ~ '^[0-9a-f]{64}$'),
  analysis JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, result_version_id),
  FOREIGN KEY (session_id, result_version_id)
    REFERENCES session_result_version(session_id, result_version_id),
  FOREIGN KEY (ai1_run_id, session_id)
    REFERENCES ai_stage_run(stage_run_id, session_id),
  FOREIGN KEY (ai2_run_id, session_id)
    REFERENCES ai_stage_run(stage_run_id, session_id)
);

-- ---------------------------------------------------------------------------
-- Additive changes to existing tables.
-- ---------------------------------------------------------------------------
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema=current_schema() AND table_name='assessment_session'
      AND column_name='review_policy'
  ) THEN
    ALTER TABLE assessment_session
      ADD COLUMN review_policy VARCHAR(20) NOT NULL DEFAULT 'LEGACY';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema=current_schema() AND table_name='assessment_session'
      AND column_name='current_result_version_id'
  ) THEN
    ALTER TABLE assessment_session ADD COLUMN current_result_version_id BIGINT;
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='assessment_session'::regclass
      AND conname='assessment_session_review_policy_check'
  ) THEN
    ALTER TABLE assessment_session ADD CONSTRAINT assessment_session_review_policy_check
      CHECK (review_policy IN ('LEGACY','AI_OFFICIAL_REVIEW'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='assessment_session'::regclass
      AND conname='assessment_session_pointer_policy_check'
  ) THEN
    ALTER TABLE assessment_session ADD CONSTRAINT assessment_session_pointer_policy_check
      CHECK (current_result_version_id IS NULL OR review_policy = 'AI_OFFICIAL_REVIEW');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='assessment_session'::regclass
      AND conname='assessment_session_current_version_fk'
  ) THEN
    ALTER TABLE assessment_session ADD CONSTRAINT assessment_session_current_version_fk
      FOREIGN KEY (session_id, current_result_version_id)
      REFERENCES session_result_version(session_id, result_version_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;

ALTER TABLE session_start_request ADD COLUMN IF NOT EXISTS request_hash CHAR(64);
ALTER TABLE llm_cache ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;
UPDATE llm_cache SET expires_at = created_at + INTERVAL '60 days'
  WHERE expires_at IS NULL;
ALTER TABLE llm_cache ALTER COLUMN expires_at SET NOT NULL;
CREATE INDEX IF NOT EXISTS llm_cache_expires_idx ON llm_cache (expires_at);

-- ---------------------------------------------------------------------------
-- Shared trigger helpers.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pr3a_reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '% is immutable', TG_TABLE_NAME;
END $$;

CREATE OR REPLACE FUNCTION pr3a_enforce_rubric_profile() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.status = 'active' AND NEW.status = 'retired' THEN
    IF OLD.question_id IS DISTINCT FROM NEW.question_id
       OR OLD.version_no IS DISTINCT FROM NEW.version_no
       OR OLD.profile_hash IS DISTINCT FROM NEW.profile_hash
       OR OLD.created_by IS DISTINCT FROM NEW.created_by
       OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
      RAISE EXCEPTION 'rubric profile evidence cannot change';
    END IF;
    NEW.retired_at := COALESCE(NEW.retired_at, NOW());
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'rubric profile status may only change active to retired';
END $$;

CREATE OR REPLACE FUNCTION pr3a_enforce_attempt_set_freeze() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF EXISTS (SELECT 1 FROM session_result_version v WHERE v.session_id = NEW.session_id) THEN
      RAISE EXCEPTION 'attempt set is frozen after result version creation';
    END IF;
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    IF EXISTS (SELECT 1 FROM session_result_version v WHERE v.session_id = OLD.session_id) THEN
      RAISE EXCEPTION 'attempt set is frozen after result version creation';
    END IF;
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    IF (NEW.session_id IS DISTINCT FROM OLD.session_id
        OR NEW.seq_no IS DISTINCT FROM OLD.seq_no
        OR NEW.question_id IS DISTINCT FROM OLD.question_id)
       AND EXISTS (SELECT 1 FROM session_result_version v WHERE v.session_id = OLD.session_id) THEN
      RAISE EXCEPTION 'structural attempt changes are frozen after result version creation';
    END IF;
    RETURN NEW;
  END IF;
  RETURN NULL;
END $$;

CREATE OR REPLACE FUNCTION pr3a_enforce_ai_stage_order() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_pred RECORD;
BEGIN
  IF NEW.stage = 'AI2' THEN
    SELECT v.status AS validation_status,
           r.stage AS predecessor_stage,
           r.session_id AS predecessor_session,
           r.scope_key AS predecessor_scope,
           r.status AS predecessor_status,
           r.input_hash AS run_input_hash,
           r.output_hash AS run_output_hash,
           v.input_hash AS validation_input_hash,
           v.output_hash AS validation_output_hash
      INTO v_pred
      FROM ai_stage_validation v
      JOIN ai_stage_run r ON r.stage_run_id = v.stage_run_id
     WHERE v.validation_id = NEW.predecessor_validation_id;

    IF NOT FOUND
       OR v_pred.predecessor_stage <> 'AI1'
       OR v_pred.predecessor_session IS DISTINCT FROM NEW.session_id
       OR v_pred.predecessor_scope IS DISTINCT FROM NEW.scope_key
       OR v_pred.predecessor_status <> 'COMPLETED'
       OR v_pred.validation_status <> 'VALID'
       OR v_pred.run_input_hash IS DISTINCT FROM v_pred.validation_input_hash
       OR v_pred.run_output_hash IS DISTINCT FROM v_pred.validation_output_hash THEN
      RAISE EXCEPTION 'AI2 requires validated AI1 output in the same session and scope';
    END IF;
  END IF;
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION pr3a_enforce_publication_transition() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_allowed BOOLEAN := FALSE;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'publication rows cannot be deleted';
  END IF;

  IF NEW.result_version_id IS DISTINCT FROM OLD.result_version_id
     OR NEW.session_id IS DISTINCT FROM OLD.session_id THEN
    RAISE EXCEPTION 'publication identity cannot change';
  END IF;

  IF NEW.state IS DISTINCT FROM OLD.state THEN
    v_allowed :=
      (OLD.state = 'APPROVED_PENDING_ANALYSIS' AND NEW.state IN ('OFFICIAL','ANALYSIS_FAILED'))
      OR
      (OLD.state = 'ANALYSIS_FAILED' AND NEW.state IN ('APPROVED_PENDING_ANALYSIS','OFFICIAL'));
    IF NOT v_allowed THEN
      RAISE EXCEPTION 'invalid publication transition % to %', OLD.state, NEW.state;
    END IF;
    NEW.state_revision := OLD.state_revision + 1;
    IF NEW.state = 'OFFICIAL' AND NEW.published_at IS NULL THEN
      NEW.published_at := NOW();
    END IF;
    IF NEW.state = 'ANALYSIS_FAILED' AND NEW.analysis_failed_at IS NULL THEN
      NEW.analysis_failed_at := NOW();
    END IF;
    IF NEW.state = 'APPROVED_PENDING_ANALYSIS' THEN
      NEW.published_at := NULL;
      NEW.analysis_failed_at := NULL;
    END IF;
  ELSE
    NEW.state_revision := OLD.state_revision;
  END IF;
  NEW.updated_at := NOW();
  RETURN NEW;
END $$;

CREATE OR REPLACE FUNCTION pr3a_check_current_pointer() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_state VARCHAR(30);
BEGIN
  IF NEW.current_result_version_id IS NOT NULL THEN
    SELECT p.state INTO v_state
      FROM session_result_publication p
     WHERE p.session_id = NEW.session_id
       AND p.result_version_id = NEW.current_result_version_id;
    IF NOT FOUND OR v_state <> 'OFFICIAL' THEN
      RAISE EXCEPTION 'current result pointer must reference an OFFICIAL version';
    END IF;
  END IF;
  RETURN NULL;
END $$;

-- ---------------------------------------------------------------------------
-- Totals and completeness validation. All aggregates are COUNT(*)/SUM.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pr3a_validate_result_totals(
  p_session_id INT, p_result_version_id BIGINT
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_total NUMERIC(7,2);
  v_max NUMERIC(7,2);
  v_sum_score NUMERIC(7,2);
  v_sum_max NUMERIC(7,2);
  v_bad BIGINT;
BEGIN
  SELECT total_score, max_score INTO v_total, v_max
    FROM session_result_version
   WHERE session_id = p_session_id AND result_version_id = p_result_version_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'result version %,% not found', p_session_id, p_result_version_id;
  END IF;

  SELECT COALESCE(SUM(score),0), COALESCE(SUM(max_score),0)
    INTO v_sum_score, v_sum_max
    FROM session_result_version_score
   WHERE session_id = p_session_id AND result_version_id = p_result_version_id;

  IF v_sum_score <> v_total OR v_sum_max <> v_max THEN
    RAISE EXCEPTION 'version totals mismatch: total %, sum %, max %, sum max %',
      v_total, v_sum_score, v_max, v_sum_max;
  END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_version_score vs
    JOIN attempt a ON a.session_id = vs.session_id AND a.attempt_id = vs.attempt_id
    JOIN question q ON q.question_id = a.question_id
   WHERE vs.session_id = p_session_id
     AND vs.result_version_id = p_result_version_id
     AND COALESCE(a.question_snapshot->>'question_type', q.question_type) = 'essay'
     AND NOT EXISTS (
       SELECT 1 FROM attempt_rubric_criterion arc
        WHERE arc.session_id = vs.session_id AND arc.attempt_id = vs.attempt_id
     );
  IF v_bad > 0 THEN
    RAISE EXCEPTION 'essay attempt without rubric criteria';
  END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_version_score vs
    JOIN attempt a ON a.session_id = vs.session_id AND a.attempt_id = vs.attempt_id
    JOIN question q ON q.question_id = a.question_id
   WHERE vs.session_id = p_session_id
     AND vs.result_version_id = p_result_version_id
     AND COALESCE(a.question_snapshot->>'question_type', q.question_type) = 'essay'
     AND (
       vs.score <> COALESCE((
         SELECT SUM(cs.score) FROM session_result_criterion_score cs
          WHERE cs.session_id=vs.session_id
            AND cs.result_version_id=vs.result_version_id
            AND cs.attempt_id=vs.attempt_id),0)
       OR vs.max_score <> COALESCE((
         SELECT SUM(cs.max_points) FROM session_result_criterion_score cs
          WHERE cs.session_id=vs.session_id
            AND cs.result_version_id=vs.result_version_id
            AND cs.attempt_id=vs.attempt_id),0)
     );
  IF v_bad > 0 THEN
    RAISE EXCEPTION 'criterion totals mismatch';
  END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_criterion_score cs
    JOIN attempt_rubric_criterion arc
      ON arc.session_id=cs.session_id
     AND arc.attempt_id=cs.attempt_id
     AND arc.criterion_snapshot_id=cs.criterion_snapshot_id
   WHERE cs.session_id=p_session_id
     AND cs.result_version_id=p_result_version_id
     AND cs.max_points <> arc.max_points;
  IF v_bad > 0 THEN
    RAISE EXCEPTION 'criterion max_points mismatch';
  END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_version_score vs
    JOIN attempt a ON a.session_id=vs.session_id AND a.attempt_id=vs.attempt_id
    JOIN attempt_rubric_criterion arc
      ON arc.session_id=vs.session_id AND arc.attempt_id=vs.attempt_id
   WHERE vs.session_id=p_session_id
     AND vs.result_version_id=p_result_version_id
     AND arc.profile_snapshot_hash IS DISTINCT FROM
         (a.question_snapshot->>'rubric_snapshot_hash');
  IF v_bad > 0 THEN
    RAISE EXCEPTION 'rubric snapshot hash mismatch';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION pr3a_validate_result_completeness(
  p_session_id INT, p_result_version_id BIGINT
) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  v_expected BIGINT;
  v_actual BIGINT;
  v_bad BIGINT;
BEGIN
  IF EXISTS (SELECT 1 FROM session_question_plan WHERE session_id=p_session_id) THEN
    SELECT COUNT(*) INTO v_expected
      FROM session_question_plan WHERE session_id=p_session_id;
  ELSE
    SELECT COUNT(*) INTO v_expected FROM attempt WHERE session_id=p_session_id;
  END IF;

  SELECT COUNT(*) INTO v_actual
    FROM session_result_version_score
   WHERE session_id=p_session_id AND result_version_id=p_result_version_id;

  IF v_expected <> v_actual THEN
    RAISE EXCEPTION 'attempt score count mismatch: expected %, found %',
      v_expected, v_actual;
  END IF;

  SELECT COUNT(*) INTO v_bad
    FROM attempt a
   WHERE a.session_id=p_session_id
     AND NOT EXISTS (
       SELECT 1 FROM session_result_version_score vs
        WHERE vs.session_id=a.session_id
          AND vs.result_version_id=p_result_version_id
          AND vs.attempt_id=a.attempt_id
     );
  IF v_bad > 0 THEN RAISE EXCEPTION '% attempts missing scores', v_bad; END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_version_score vs
   WHERE vs.session_id=p_session_id
     AND vs.result_version_id=p_result_version_id
     AND NOT EXISTS (
       SELECT 1 FROM attempt a
        WHERE a.session_id=vs.session_id AND a.attempt_id=vs.attempt_id
     );
  IF v_bad > 0 THEN RAISE EXCEPTION '% extra attempt scores', v_bad; END IF;

  IF EXISTS (SELECT 1 FROM session_question_plan WHERE session_id=p_session_id) THEN
    SELECT COUNT(*) INTO v_bad FROM attempt WHERE session_id=p_session_id;
    IF v_bad <> v_expected THEN
      RAISE EXCEPTION 'attempt/plan count mismatch: attempts %, plan %', v_bad, v_expected;
    END IF;

    SELECT COUNT(*) INTO v_bad
      FROM attempt a
     WHERE a.session_id=p_session_id
       AND NOT EXISTS (
         SELECT 1 FROM session_question_plan p
          WHERE p.session_id=a.session_id
            AND p.seq_no=a.seq_no
            AND p.question_id=a.question_id
       );
    IF v_bad > 0 THEN
      RAISE EXCEPTION '% attempts do not match frozen plan identity', v_bad;
    END IF;

    SELECT COUNT(*) INTO v_bad
      FROM session_question_plan p
     WHERE p.session_id=p_session_id
       AND NOT EXISTS (
         SELECT 1 FROM attempt a
          WHERE a.session_id=p.session_id
            AND a.seq_no=p.seq_no
            AND a.question_id=p.question_id
       );
    IF v_bad > 0 THEN
      RAISE EXCEPTION '% plan rows have no matching attempt identity', v_bad;
    END IF;
  END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_version_score vs
    JOIN attempt a ON a.session_id=vs.session_id AND a.attempt_id=vs.attempt_id
    JOIN question q ON q.question_id=a.question_id
   WHERE vs.session_id=p_session_id
     AND vs.result_version_id=p_result_version_id
     AND vs.max_score <> COALESCE((a.question_snapshot->>'points')::numeric, q.points);
  IF v_bad > 0 THEN RAISE EXCEPTION 'question max_score mismatch'; END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_version_score vs
    JOIN attempt a ON a.session_id=vs.session_id AND a.attempt_id=vs.attempt_id
    JOIN question q ON q.question_id=a.question_id
   WHERE vs.session_id=p_session_id
     AND vs.result_version_id=p_result_version_id
     AND COALESCE(a.question_snapshot->>'question_type', q.question_type) = 'essay'
     AND (
       (SELECT COUNT(*) FROM attempt_rubric_criterion arc
         WHERE arc.session_id=vs.session_id AND arc.attempt_id=vs.attempt_id) = 0
       OR
       (SELECT COUNT(*) FROM attempt_rubric_criterion arc
         WHERE arc.session_id=vs.session_id AND arc.attempt_id=vs.attempt_id)
       <>
       (SELECT COUNT(*) FROM session_result_criterion_score cs
         WHERE cs.session_id=vs.session_id
           AND cs.result_version_id=vs.result_version_id
           AND cs.attempt_id=vs.attempt_id)
     );
  IF v_bad > 0 THEN RAISE EXCEPTION 'essay criterion count mismatch'; END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_version_score vs
    JOIN attempt a ON a.session_id=vs.session_id AND a.attempt_id=vs.attempt_id
    JOIN question q ON q.question_id=a.question_id
    JOIN attempt_rubric_criterion arc
      ON arc.session_id=vs.session_id AND arc.attempt_id=vs.attempt_id
   WHERE vs.session_id=p_session_id
     AND vs.result_version_id=p_result_version_id
     AND COALESCE(a.question_snapshot->>'question_type', q.question_type) = 'essay'
     AND NOT EXISTS (
       SELECT 1 FROM session_result_criterion_score cs
        WHERE cs.session_id=vs.session_id
          AND cs.result_version_id=vs.result_version_id
          AND cs.attempt_id=vs.attempt_id
          AND cs.criterion_snapshot_id=arc.criterion_snapshot_id
     );
  IF v_bad > 0 THEN RAISE EXCEPTION 'missing criterion score'; END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_criterion_score cs
   WHERE cs.session_id=p_session_id
     AND cs.result_version_id=p_result_version_id
     AND NOT EXISTS (
       SELECT 1 FROM attempt_rubric_criterion arc
        WHERE arc.session_id=cs.session_id
          AND arc.attempt_id=cs.attempt_id
          AND arc.criterion_snapshot_id=cs.criterion_snapshot_id
     );
  IF v_bad > 0 THEN RAISE EXCEPTION 'extra or foreign criterion score'; END IF;

  SELECT COUNT(*) INTO v_bad
    FROM session_result_criterion_score cs
    JOIN attempt a ON a.session_id=cs.session_id AND a.attempt_id=cs.attempt_id
    JOIN question q ON q.question_id=a.question_id
   WHERE cs.session_id=p_session_id
     AND cs.result_version_id=p_result_version_id
     AND COALESCE(a.question_snapshot->>'question_type', q.question_type) <> 'essay';
  IF v_bad > 0 THEN RAISE EXCEPTION 'criterion score on non-essay'; END IF;
END $$;

CREATE OR REPLACE FUNCTION pr3a_check_result_all() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_session_id INT;
  v_result_version_id BIGINT;
BEGIN
  IF TG_TABLE_NAME = 'session_result_publication' THEN
    IF TG_OP = 'DELETE' THEN
      v_session_id := OLD.session_id;
      v_result_version_id := OLD.result_version_id;
    ELSE
      v_session_id := NEW.session_id;
      v_result_version_id := NEW.result_version_id;
    END IF;
  ELSIF TG_TABLE_NAME = 'session_result_version' THEN
    IF TG_OP = 'DELETE' THEN
      v_session_id := OLD.session_id;
      v_result_version_id := OLD.result_version_id;
    ELSE
      v_session_id := NEW.session_id;
      v_result_version_id := NEW.result_version_id;
    END IF;
  ELSIF TG_TABLE_NAME = 'session_result_version_score' THEN
    IF TG_OP = 'DELETE' THEN
      v_session_id := OLD.session_id;
      v_result_version_id := OLD.result_version_id;
    ELSE
      v_session_id := NEW.session_id;
      v_result_version_id := NEW.result_version_id;
    END IF;
  ELSIF TG_TABLE_NAME = 'session_result_criterion_score' THEN
    IF TG_OP = 'DELETE' THEN
      v_session_id := OLD.session_id;
      v_result_version_id := OLD.result_version_id;
    ELSE
      v_session_id := NEW.session_id;
      v_result_version_id := NEW.result_version_id;
    END IF;
  ELSE
    RAISE EXCEPTION 'unexpected result validation table %', TG_TABLE_NAME;
  END IF;

  PERFORM pr3a_validate_result_totals(v_session_id, v_result_version_id);
  PERFORM pr3a_validate_result_completeness(v_session_id, v_result_version_id);
  RETURN NULL;
END $$;

-- ---------------------------------------------------------------------------
-- Trigger installation.
-- ---------------------------------------------------------------------------
DO $$ DECLARE t TEXT; BEGIN
  FOREACH t IN ARRAY ARRAY[
    'session_result_version','session_result_version_score',
    'session_result_criterion_score','attempt_rubric_criterion',
    'question_rubric_criterion','ai_stage_validation','session_result_analysis',
    'retention_purge_audit','prompt_access_audit'
  ] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS %I ON %I', 'pr3a_immutable_' || t, t);
    EXECUTE format(
      'CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION pr3a_reject_mutation()',
      'pr3a_immutable_' || t, t
    );
  END LOOP;
END $$;

DROP TRIGGER IF EXISTS question_rubric_profile_status ON question_rubric_profile;
CREATE TRIGGER question_rubric_profile_status
BEFORE UPDATE ON question_rubric_profile
FOR EACH ROW EXECUTE FUNCTION pr3a_enforce_rubric_profile();

DROP TRIGGER IF EXISTS attempt_structural_insert_freeze ON attempt;
CREATE TRIGGER attempt_structural_insert_freeze
BEFORE INSERT ON attempt
FOR EACH ROW EXECUTE FUNCTION pr3a_enforce_attempt_set_freeze();

DROP TRIGGER IF EXISTS attempt_structural_delete_freeze ON attempt;
CREATE TRIGGER attempt_structural_delete_freeze
BEFORE DELETE ON attempt
FOR EACH ROW EXECUTE FUNCTION pr3a_enforce_attempt_set_freeze();

DROP TRIGGER IF EXISTS attempt_structural_update_freeze ON attempt;
CREATE TRIGGER attempt_structural_update_freeze
BEFORE UPDATE OF session_id, seq_no, question_id ON attempt
FOR EACH ROW EXECUTE FUNCTION pr3a_enforce_attempt_set_freeze();

DROP TRIGGER IF EXISTS ai_stage_order ON ai_stage_run;
CREATE TRIGGER ai_stage_order
BEFORE INSERT OR UPDATE OF stage, predecessor_validation_id, status ON ai_stage_run
FOR EACH ROW EXECUTE FUNCTION pr3a_enforce_ai_stage_order();

DROP TRIGGER IF EXISTS session_result_publication_transition ON session_result_publication;
CREATE TRIGGER session_result_publication_transition
BEFORE UPDATE OF state ON session_result_publication
FOR EACH ROW EXECUTE FUNCTION pr3a_enforce_publication_transition();

DROP TRIGGER IF EXISTS session_result_publication_immutable ON session_result_publication;
CREATE TRIGGER session_result_publication_immutable
BEFORE DELETE ON session_result_publication
FOR EACH ROW EXECUTE FUNCTION pr3a_reject_mutation();

DROP TRIGGER IF EXISTS assessment_session_current_pointer_check ON assessment_session;
CREATE CONSTRAINT TRIGGER assessment_session_current_pointer_check
AFTER INSERT OR UPDATE OF current_result_version_id ON assessment_session
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION pr3a_check_current_pointer();

DROP TRIGGER IF EXISTS session_result_version_all_check ON session_result_version;
CREATE CONSTRAINT TRIGGER session_result_version_all_check
AFTER INSERT OR UPDATE OR DELETE ON session_result_version
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION pr3a_check_result_all();

DROP TRIGGER IF EXISTS session_result_version_score_all_check ON session_result_version_score;
CREATE CONSTRAINT TRIGGER session_result_version_score_all_check
AFTER INSERT OR UPDATE OR DELETE ON session_result_version_score
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION pr3a_check_result_all();

DROP TRIGGER IF EXISTS session_result_criterion_score_all_check ON session_result_criterion_score;
CREATE CONSTRAINT TRIGGER session_result_criterion_score_all_check
AFTER INSERT OR UPDATE OR DELETE ON session_result_criterion_score
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION pr3a_check_result_all();

DROP TRIGGER IF EXISTS session_result_publication_all_check ON session_result_publication;
CREATE CONSTRAINT TRIGGER session_result_publication_all_check
AFTER INSERT OR UPDATE ON session_result_publication
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION pr3a_check_result_all();

-- PR 3A MIGRATION 026 END (mirrored from db/migrations/026_pr3a_database_foundation.sql)


-- ---------------------------------------------------------------------------
-- 027_review_flow.sql (grading-review foundation).
-- Mirrored verbatim from db/migrations/027_review_flow.sql so a fresh load
-- of this file describes the same catalog as the migration chain.
-- Every statement is idempotent; see backend/tests/test_migrations_027.py.
-- PR 3B MIGRATION 027 BEGIN (mirrored from db/migrations/027_review_flow.sql)
-- ---------------------------------------------------------------------------

-- 027 review flow foundation.
-- Additive only: no existing row, migration or trigger is rewritten.
-- This migration stores review intent and evidence only; no service or
-- endpoint behavior is wired here.
--
-- Named defaults (the service layer must mirror these values):
--   REVIEW_WINDOW_DAYS        = 7    (learner request window after v1 publication)
--   CLAIM_LEASE_MINUTES       = 30   (admin claim lease before reclaim)
--   CASE_TTL_DAYS             = 30   (unactioned case expiry)
--   LONG_REASON_MIN_CHARS     = 120  (single-admin long-reason path)
-- The 120-character rule is enforced below; the other defaults are service
-- contracts because they depend on runtime clocks and worker cadence.
--
-- Owner rule: SINGLE_ADMIN_LONG_REASON is permitted only when no OTHER active
-- Administrator exists. pr3a_other_active_admins() exposes that count as a
-- read-only contract; it is intentionally not enforced by a DB constraint.

-- ---------------------------------------------------------------------------
-- One review case per session. Learner- or admin-originated.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_request (
  review_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL UNIQUE REFERENCES assessment_session(session_id),
  learner_id INT NOT NULL REFERENCES account(account_id),
  requested_by INT NOT NULL REFERENCES account(account_id),
  origin VARCHAR(12) NOT NULL CHECK (origin IN ('LEARNER','ADMIN_REPORT','ADMIN')),
  request_key UUID NOT NULL UNIQUE,
  reason VARCHAR(2000) NOT NULL CHECK (length(btrim(reason)) >= 10),
  status VARCHAR(20) NOT NULL DEFAULT 'REQUESTED'
    CHECK (status IN ('REQUESTED','IN_REVIEW','REGRADED','REJECTED','EXPIRED')),
  base_result_version_id BIGINT NOT NULL,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  window_expires_at TIMESTAMPTZ NULL,
  claimed_by INT NULL REFERENCES account(account_id),
  claimed_at TIMESTAMPTZ NULL,
  claim_expires_at TIMESTAMPTZ NULL,
  resolved_by INT NULL REFERENCES account(account_id),
  resolved_at TIMESTAMPTZ NULL,
  resolution_note VARCHAR(2000) NULL,
  regraded_result_version_id BIGINT NULL,
  revision INT NOT NULL DEFAULT 0 CHECK (revision >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  FOREIGN KEY (session_id, base_result_version_id)
    REFERENCES session_result_version(session_id, result_version_id),
  FOREIGN KEY (session_id, regraded_result_version_id)
    REFERENCES session_result_version(session_id, result_version_id),
  CHECK (origin <> 'LEARNER' OR window_expires_at IS NOT NULL),
  CHECK (claimed_by IS NULL OR (claimed_at IS NOT NULL AND claim_expires_at IS NOT NULL)),
  CHECK (status <> 'REGRADED' OR regraded_result_version_id IS NOT NULL),
  CHECK (status NOT IN ('REGRADED','REJECTED') OR resolved_at IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS review_request_queue_idx
  ON review_request (status, created_at);

-- Window and transition guard. NOW() is the server transaction clock.
CREATE OR REPLACE FUNCTION pr3a_review_request_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_state VARCHAR(30);
  v_published TIMESTAMPTZ;
  v_source VARCHAR(10);
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.origin = 'LEARNER' THEN
      SELECT p.state, p.published_at, v.source
        INTO v_state, v_published, v_source
        FROM session_result_publication p
        JOIN session_result_version v
          ON v.session_id = p.session_id
         AND v.result_version_id = p.result_version_id
       WHERE p.session_id = NEW.session_id
         AND p.result_version_id = NEW.base_result_version_id;
      IF NOT FOUND OR v_state <> 'OFFICIAL' OR v_published IS NULL
         OR v_source <> 'V1' THEN
        RAISE EXCEPTION 'review base must be an OFFICIAL V1 result version';
      END IF;
      NEW.window_expires_at := v_published + INTERVAL '7 days';
      IF NOW() > NEW.window_expires_at THEN
        RAISE EXCEPTION 'review window closed';
      END IF;
    END IF;
    NEW.revision := 0;
    RETURN NEW;
  END IF;

  -- UPDATE: identity is immutable; only legal workflow transitions may change.
  IF NEW.session_id IS DISTINCT FROM OLD.session_id
     OR NEW.learner_id IS DISTINCT FROM OLD.learner_id
     OR NEW.requested_by IS DISTINCT FROM OLD.requested_by
     OR NEW.origin IS DISTINCT FROM OLD.origin
     OR NEW.request_key IS DISTINCT FROM OLD.request_key
     OR NEW.reason IS DISTINCT FROM OLD.reason
     OR NEW.base_result_version_id IS DISTINCT FROM OLD.base_result_version_id
     OR NEW.requested_at IS DISTINCT FROM OLD.requested_at
     OR NEW.window_expires_at IS DISTINCT FROM OLD.window_expires_at
     OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
    RAISE EXCEPTION 'review request identity is immutable';
  END IF;

  IF OLD.status IN ('REGRADED','REJECTED','EXPIRED') THEN
    RAISE EXCEPTION 'terminal review request is immutable';
  END IF;

  IF NEW.status IS DISTINCT FROM OLD.status THEN
    IF NOT (
      (OLD.status = 'REQUESTED' AND NEW.status IN ('IN_REVIEW','REJECTED','EXPIRED'))
      OR
      (OLD.status = 'IN_REVIEW' AND NEW.status IN ('REQUESTED','REGRADED','REJECTED','EXPIRED'))
    ) THEN
      RAISE EXCEPTION 'invalid review request transition % -> %', OLD.status, NEW.status;
    END IF;
    NEW.revision := OLD.revision + 1;
  ELSE
    NEW.revision := OLD.revision;
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS review_request_guard ON review_request;
CREATE TRIGGER review_request_guard
BEFORE INSERT OR UPDATE ON review_request
FOR EACH ROW EXECUTE FUNCTION pr3a_review_request_guard();

DROP TRIGGER IF EXISTS review_request_no_delete ON review_request;
CREATE TRIGGER review_request_no_delete
BEFORE DELETE ON review_request
FOR EACH ROW EXECUTE FUNCTION pr3a_reject_mutation();

-- ---------------------------------------------------------------------------
-- Wrong question/answer report. MCQ and SQL scores are never edited directly.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS question_report (
  question_report_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  review_request_id BIGINT NULL REFERENCES review_request(review_request_id),
  session_id INT NOT NULL,
  attempt_id INT NOT NULL,
  question_id INT NOT NULL REFERENCES question(question_id),
  reported_by INT NOT NULL REFERENCES account(account_id),
  category VARCHAR(20) NOT NULL CHECK (category IN
    ('WRONG_ANSWER','WRONG_QUESTION','AMBIGUOUS','TECHNICAL')),
  details VARCHAR(2000) NOT NULL CHECK (length(btrim(details)) >= 10),
  status VARCHAR(10) NOT NULL DEFAULT 'OPEN'
    CHECK (status IN ('OPEN','ACCEPTED','REJECTED')),
  resolution_note VARCHAR(2000) NULL,
  resolved_by INT NULL REFERENCES account(account_id),
  resolved_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, attempt_id, category),
  FOREIGN KEY (session_id, attempt_id) REFERENCES attempt(session_id, attempt_id),
  CHECK (status = 'OPEN' OR resolved_at IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS question_report_open_idx
  ON question_report (status, created_at);
CREATE INDEX IF NOT EXISTS question_report_review_idx
  ON question_report (review_request_id, status);

CREATE OR REPLACE FUNCTION pr3a_question_report_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'question reports cannot be deleted';
  END IF;
  IF NEW.session_id IS DISTINCT FROM OLD.session_id
     OR NEW.attempt_id IS DISTINCT FROM OLD.attempt_id
     OR NEW.question_id IS DISTINCT FROM OLD.question_id
     OR NEW.reported_by IS DISTINCT FROM OLD.reported_by
     OR NEW.category IS DISTINCT FROM OLD.category
     OR NEW.details IS DISTINCT FROM OLD.details
     OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
    RAISE EXCEPTION 'question report identity is immutable';
  END IF;
  IF OLD.review_request_id IS NOT NULL
     AND NEW.review_request_id IS DISTINCT FROM OLD.review_request_id THEN
    RAISE EXCEPTION 'question report case link is immutable once set';
  END IF;
  IF NEW.status IS DISTINCT FROM OLD.status THEN
    IF NOT (OLD.status = 'OPEN' AND NEW.status IN ('ACCEPTED','REJECTED')) THEN
      RAISE EXCEPTION 'invalid question report transition % -> %', OLD.status, NEW.status;
    END IF;
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS question_report_guard ON question_report;
CREATE TRIGGER question_report_guard
BEFORE UPDATE OR DELETE ON question_report
FOR EACH ROW EXECUTE FUNCTION pr3a_question_report_guard();

-- ---------------------------------------------------------------------------
-- One row per large score change: second-admin confirmation or the documented
-- single-admin long-reason path. Append-only.
-- deviation_ratio is measured against the question's max points:
--   abs(reviewed_score - ai_score) / max_points, rounded to 4 decimals.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_deviation (
  deviation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  review_request_id BIGINT NOT NULL REFERENCES review_request(review_request_id),
  session_id INT NOT NULL,
  attempt_id INT NOT NULL,
  criterion_snapshot_id BIGINT NULL,
  ai_score NUMERIC(5,2) NOT NULL,
  reviewed_score NUMERIC(5,2) NOT NULL,
  max_points NUMERIC(5,2) NOT NULL CHECK (max_points > 0),
  deviation_ratio NUMERIC(6,4) NOT NULL CHECK (deviation_ratio > 0.30),
  reason VARCHAR(4000) NOT NULL CHECK (length(btrim(reason)) >= 10),
  first_reviewer_id INT NOT NULL REFERENCES account(account_id),
  second_reviewer_id INT NULL REFERENCES account(account_id),
  confirmation VARCHAR(24) NOT NULL
    CHECK (confirmation IN ('SECOND_ADMIN','SINGLE_ADMIN_LONG_REASON')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  FOREIGN KEY (session_id, attempt_id)
    REFERENCES attempt(session_id, attempt_id),
  FOREIGN KEY (session_id, attempt_id, criterion_snapshot_id)
    REFERENCES attempt_rubric_criterion(session_id, attempt_id, criterion_snapshot_id),
  CHECK (deviation_ratio = round(abs(reviewed_score - ai_score) / max_points, 4)),
  CHECK (second_reviewer_id IS NULL OR second_reviewer_id <> first_reviewer_id),
  CHECK ((confirmation = 'SECOND_ADMIN') = (second_reviewer_id IS NOT NULL)),
  CHECK (confirmation <> 'SINGLE_ADMIN_LONG_REASON'
         OR length(btrim(reason)) >= 120)
);
CREATE UNIQUE INDEX IF NOT EXISTS review_deviation_attempt_uk
  ON review_deviation (review_request_id, attempt_id)
  WHERE criterion_snapshot_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS review_deviation_criterion_uk
  ON review_deviation (review_request_id, attempt_id, criterion_snapshot_id)
  WHERE criterion_snapshot_id IS NOT NULL;

DROP TRIGGER IF EXISTS review_deviation_immutable ON review_deviation;
CREATE TRIGGER review_deviation_immutable
BEFORE UPDATE OR DELETE ON review_deviation
FOR EACH ROW EXECUTE FUNCTION pr3a_reject_mutation();

-- ---------------------------------------------------------------------------
-- Contract helper for the owner rule. Returns the number of active
-- Administrator accounts other than the given actor. The service layer must
-- allow SINGLE_ADMIN_LONG_REASON only when this returns 0; otherwise a
-- SECOND_ADMIN confirmation is mandatory. Not enforced in the database.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION pr3a_other_active_admins(p_actor_id INT)
RETURNS INT LANGUAGE sql STABLE AS $$
  SELECT COUNT(*)::int
  FROM account a
  JOIN account_role ar ON ar.account_id = a.account_id
  JOIN role r ON r.role_id = ar.role_id
  WHERE r.role_name = 'Administrator'
    AND a.status = 'active'
    AND a.account_id <> p_actor_id
$$;

COMMENT ON FUNCTION pr3a_other_active_admins(INT) IS
  'Read-only contract: SINGLE_ADMIN_LONG_REASON is allowed only when this returns 0; otherwise SECOND_ADMIN is mandatory. No DB enforcement.';

-- ---------------------------------------------------------------------------
-- Optional traceability link: v2 -> review case. Deferrable because the case
-- references the v1 row first.
-- ---------------------------------------------------------------------------
ALTER TABLE session_result_version
  ADD COLUMN IF NOT EXISTS review_request_id BIGINT;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'session_result_version'::regclass
      AND conname = 'session_result_version_review_request_fk'
  ) THEN
    ALTER TABLE session_result_version
      ADD CONSTRAINT session_result_version_review_request_fk
      FOREIGN KEY (review_request_id)
      REFERENCES review_request(review_request_id)
      DEFERRABLE INITIALLY DEFERRED;
  END IF;
END $$;
-- PR 3B MIGRATION 027 END (mirrored from db/migrations/027_review_flow.sql)

-- A nomination becomes usable only after the nominated administrator confirms it.
CREATE TABLE IF NOT EXISTS review_deviation_confirmation (
  deviation_id BIGINT PRIMARY KEY REFERENCES review_deviation(deviation_id),
  confirmed_by INT NOT NULL REFERENCES account(account_id),
  confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION review_deviation_confirmation_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM review_deviation
    WHERE deviation_id = NEW.deviation_id
      AND confirmation = 'SECOND_ADMIN'
      AND second_reviewer_id = NEW.confirmed_by
  ) THEN
    RAISE EXCEPTION 'Only the nominated second administrator can confirm the deviation'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS review_deviation_confirmation_guard ON review_deviation_confirmation;
CREATE TRIGGER review_deviation_confirmation_guard
BEFORE INSERT ON review_deviation_confirmation
FOR EACH ROW EXECUTE FUNCTION review_deviation_confirmation_guard();

DROP TRIGGER IF EXISTS review_deviation_confirmation_immutable ON review_deviation_confirmation;
CREATE TRIGGER review_deviation_confirmation_immutable
BEFORE UPDATE OR DELETE ON review_deviation_confirmation
FOR EACH ROW EXECUTE FUNCTION pr3a_reject_mutation();

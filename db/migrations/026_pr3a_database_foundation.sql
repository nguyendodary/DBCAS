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

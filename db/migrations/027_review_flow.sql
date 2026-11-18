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

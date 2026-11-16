-- Migration 022: automatic CLO tagging.
--
-- Additive only. Every question keeps its content and serving behaviour.
-- The deterministic backfill assigns the single reachable CLO (confirmed
-- question concept -> confirmed CLO concept -> active CLO) as an automatic,
-- confirmed primary row. Questions with zero or several reachable CLOs are
-- left for the AI proposal service, which stores pending 'ai' rows.
--
-- Re-running this migration is safe: the table/indexes are IF NOT EXISTS and
-- the backfill never touches a question that already has any CLO row.

CREATE TABLE IF NOT EXISTS question_clo (
  question_id INT NOT NULL,
  clo_id INT NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  tag_source VARCHAR(10) NOT NULL DEFAULT 'admin',
  confirmed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (question_id, clo_id),
  CONSTRAINT question_clo_question_fk
    FOREIGN KEY (question_id) REFERENCES question(question_id),
  CONSTRAINT question_clo_clo_fk
    FOREIGN KEY (clo_id) REFERENCES course_learning_outcome(clo_id),
  CONSTRAINT question_clo_status_check
    CHECK (status IN ('pending', 'confirmed', 'rejected')),
  CONSTRAINT question_clo_source_check
    CHECK (tag_source IN ('admin', 'auto', 'ai'))
);

-- Only an active primary counts for the one-primary rule. Rejected rows keep
-- their audit value without blocking a later reviewed decision.
CREATE UNIQUE INDEX IF NOT EXISTS question_clo_primary_idx
  ON question_clo(question_id)
  WHERE is_primary AND status <> 'rejected';
CREATE INDEX IF NOT EXISTS question_clo_clo_idx ON question_clo(clo_id);
CREATE INDEX IF NOT EXISTS question_clo_status_idx ON question_clo(status);

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'question_clo_status_check'
      AND conrelid = 'question_clo'::regclass
  ) THEN
    ALTER TABLE question_clo ADD CONSTRAINT question_clo_status_check
      CHECK (status IN ('pending', 'confirmed', 'rejected'));
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'question_clo_source_check'
      AND conrelid = 'question_clo'::regclass
  ) THEN
    ALTER TABLE question_clo ADD CONSTRAINT question_clo_source_check
      CHECK (tag_source IN ('admin', 'auto', 'ai'));
  END IF;
END $$;

-- Deterministic initial tagging. A question with exactly one active CLO
-- reachable through confirmed concepts receives that CLO as its primary.
-- Any existing row (admin, auto or ai) wins: the backfill never overwrites
-- or duplicates a decision.
WITH reachable AS (
  SELECT
    qc.question_id,
    array_agg(DISTINCT cc.clo_id ORDER BY cc.clo_id) AS clo_ids
  FROM question_concept qc
  JOIN clo_concept cc
    ON cc.concept_id = qc.concept_id
   AND cc.status = 'confirmed'
  JOIN course_learning_outcome clo
    ON clo.clo_id = cc.clo_id
   AND clo.status = 'active'
  WHERE qc.confirmed
  GROUP BY qc.question_id
)
INSERT INTO question_clo(
  question_id, clo_id, is_primary, status, tag_source, confirmed_at
)
SELECT
  r.question_id,
  r.clo_ids[1],
  TRUE,
  'confirmed',
  'auto',
  NOW()
FROM reachable r
WHERE cardinality(r.clo_ids) = 1
  AND NOT EXISTS (
    SELECT 1 FROM question_clo existing
    WHERE existing.question_id = r.question_id
  )
ON CONFLICT (question_id, clo_id) DO NOTHING;

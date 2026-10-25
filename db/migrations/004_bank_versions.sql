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

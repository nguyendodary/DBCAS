-- Official-source provenance for curated bank items (PostgreSQL knowledge
-- pack). Learner-facing content stays unchanged; these columns let admins
-- trace each question to its reviewed documentation source and topic tags.
ALTER TABLE question ADD COLUMN IF NOT EXISTS explanation TEXT;
ALTER TABLE question ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE question ADD COLUMN IF NOT EXISTS source_refs JSONB NOT NULL DEFAULT '[]'::jsonb;

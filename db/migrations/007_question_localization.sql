-- Bilingual display content is additive; canonical English, answer keys,
-- SQL fixtures and immutable historical evidence remain untouched.
ALTER TABLE assessment_session
  ADD COLUMN IF NOT EXISTS locale VARCHAR(16) NOT NULL DEFAULT 'en';

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid='assessment_session'::regclass
      AND conname='assessment_session_locale_check'
  ) THEN
    ALTER TABLE assessment_session
      ADD CONSTRAINT assessment_session_locale_check
      CHECK (locale ~ '^[a-z]{2}(-[A-Z]{2})?$');
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS question_translation (
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

CREATE OR REPLACE FUNCTION preserve_session_locale() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.locale IS DISTINCT FROM NEW.locale THEN
    RAISE EXCEPTION 'Assessment question locale is immutable';
  END IF;
  RETURN NEW;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger
    WHERE tgrelid='assessment_session'::regclass AND tgname='session_locale_immutable'
  ) THEN
    CREATE TRIGGER session_locale_immutable BEFORE UPDATE ON assessment_session
      FOR EACH ROW EXECUTE FUNCTION preserve_session_locale();
  END IF;
END $$;

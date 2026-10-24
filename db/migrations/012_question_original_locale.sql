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

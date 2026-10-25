-- Persistent account avatars and credential revocation after password changes.
ALTER TABLE account ADD COLUMN IF NOT EXISTS avatar_data_url TEXT;
ALTER TABLE account ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;

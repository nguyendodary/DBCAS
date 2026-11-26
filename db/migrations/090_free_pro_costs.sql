-- Additive upgrade for existing DBCAS installations; copy into db/migrations.
ALTER TABLE account ADD COLUMN IF NOT EXISTS plan VARCHAR(10) NOT NULL DEFAULT 'free';
ALTER TABLE account ADD COLUMN IF NOT EXISTS pro_expires_at TIMESTAMPTZ;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='account'::regclass AND conname='account_plan_check') THEN
    ALTER TABLE account ADD CONSTRAINT account_plan_check CHECK (plan IN ('free','pro'));
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS pro_purchase (
  purchase_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL REFERENCES account(account_id),
  amount_usd NUMERIC(12,6) NOT NULL DEFAULT 0 CHECK (amount_usd >= 0),
  simulated BOOLEAN NOT NULL DEFAULT TRUE CHECK (simulated),
  purchased_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  CHECK (expires_at > purchased_at)
);
CREATE INDEX IF NOT EXISTS pro_purchase_account_idx ON pro_purchase(account_id, purchased_at DESC);

CREATE TABLE IF NOT EXISTS operating_cost (
  cost_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  kind VARCHAR(16) NOT NULL CHECK (kind IN ('ai','hosting')),
  account_id INT REFERENCES account(account_id),
  task_type VARCHAR(64),
  model VARCHAR(100),
  prompt_tokens INT CHECK (prompt_tokens >= 0),
  completion_tokens INT CHECK (completion_tokens >= 0),
  amount_usd NUMERIC(12,8) CHECK (amount_usd >= 0),
  outcome VARCHAR(20) NOT NULL CHECK (outcome IN ('success','http_error','network_error','provider_error')),
  http_status INT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (kind <> 'ai' OR task_type IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS operating_cost_kind_time_idx ON operating_cost(kind, created_at DESC);

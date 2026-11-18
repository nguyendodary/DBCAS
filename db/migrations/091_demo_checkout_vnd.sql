-- Existing demo purchases retain their recorded USD amount. New checkouts
-- record the agreed 99,000 VND package price exactly.
ALTER TABLE pro_purchase
  ADD COLUMN IF NOT EXISTS amount_vnd BIGINT NOT NULL DEFAULT 0;
ALTER TABLE pro_purchase
  ADD COLUMN IF NOT EXISTS checkout_request_id UUID;
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'pro_purchase'::regclass
      AND conname = 'pro_purchase_amount_vnd_check'
  ) THEN
    ALTER TABLE pro_purchase ADD CONSTRAINT pro_purchase_amount_vnd_check
      CHECK (amount_vnd >= 0);
  END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS pro_purchase_checkout_request_idx
  ON pro_purchase(checkout_request_id);

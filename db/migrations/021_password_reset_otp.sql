-- 021 — email one-time passcode for self-service password recovery.
-- Additive and forward-only. One live code per account: issuing a new code
-- replaces the previous row. Only an HMAC digest of the code is stored; the
-- plaintext exists solely inside the email message. A successful
-- verification deletes the row and issues a short-lived single-use token in
-- password_reset_token, which the confirm step redeems.

CREATE TABLE IF NOT EXISTS password_reset_otp (
  account_id INT PRIMARY KEY REFERENCES account(account_id),
  otp_hash VARCHAR(64) NOT NULL,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  attempts INT NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  CHECK (expires_at > requested_at)
);
CREATE INDEX IF NOT EXISTS password_reset_otp_expiry_idx
  ON password_reset_otp(expires_at);

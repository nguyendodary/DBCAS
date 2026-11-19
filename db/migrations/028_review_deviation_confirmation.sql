-- A nomination becomes usable only after the nominated administrator confirms it.
CREATE TABLE IF NOT EXISTS review_deviation_confirmation (
  deviation_id BIGINT PRIMARY KEY REFERENCES review_deviation(deviation_id),
  confirmed_by INT NOT NULL REFERENCES account(account_id),
  confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION review_deviation_confirmation_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM review_deviation
    WHERE deviation_id = NEW.deviation_id
      AND confirmation = 'SECOND_ADMIN'
      AND second_reviewer_id = NEW.confirmed_by
  ) THEN
    RAISE EXCEPTION 'Only the nominated second administrator can confirm the deviation'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END
$$;

DROP TRIGGER IF EXISTS review_deviation_confirmation_guard ON review_deviation_confirmation;
CREATE TRIGGER review_deviation_confirmation_guard
BEFORE INSERT ON review_deviation_confirmation
FOR EACH ROW EXECUTE FUNCTION review_deviation_confirmation_guard();

DROP TRIGGER IF EXISTS review_deviation_confirmation_immutable ON review_deviation_confirmation;
CREATE TRIGGER review_deviation_confirmation_immutable
BEFORE UPDATE OR DELETE ON review_deviation_confirmation
FOR EACH ROW EXECUTE FUNCTION pr3a_reject_mutation();

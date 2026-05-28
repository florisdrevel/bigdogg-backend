-- 2026-05-28: three pricing tiers (monthly / yearly / pay-as-you-go).
--
-- - subscriptions.plan distinguishes Stripe recurring plans from PAYG.
--   PAYG users have status='active' AND plan='payg'; they can use the
--   app freely but pay per annual/BTW report PDF generation.
-- - report_download_credits records one-shot purchases by PAYG users.
--   Every PDF generation = one credit. We don't pre-issue or cache;
--   each tap on "Download" creates a Stripe one-time payment and the
--   webhook inserts a row here, which the PDF endpoint then consumes.
--
-- Safe to re-run: uses IF NOT EXISTS guards.

ALTER TABLE subscriptions
  ADD COLUMN IF NOT EXISTS plan TEXT NULL;

-- Lock the value space — keeps junk out of the column.
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'subscriptions_plan_check'
  ) THEN
    ALTER TABLE subscriptions
      ADD CONSTRAINT subscriptions_plan_check
      CHECK (plan IS NULL OR plan IN ('monthly', 'yearly', 'payg'));
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS report_download_credits (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL,
  type            TEXT NOT NULL CHECK (type IN ('annual_report', 'vat_report')),
  year            INT  NOT NULL,
  quarter         INT  NULL,
  stripe_session_id TEXT UNIQUE,
  paid_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  used_at         TIMESTAMPTZ NULL
);

-- Fast lookup for the "find an unused credit for this exact report"
-- query the PDF endpoint runs. Partial index — used credits are dead
-- weight and don't need to be searched.
CREATE INDEX IF NOT EXISTS report_credits_user_unused
  ON report_download_credits (user_id, type, year, quarter)
  WHERE used_at IS NULL;

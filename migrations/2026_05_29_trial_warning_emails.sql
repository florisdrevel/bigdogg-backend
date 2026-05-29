-- 2026-05-29: dedupe table for the trial-expiry warning cron.
--
-- The /cron/trial-expiry endpoint runs daily and sends a 7-day and a
-- 3-day reminder. Without dedupe a retry of the same day would email
-- twice. One row per (user, threshold) prevents that — uniqueness is
-- enforced by the primary key.
--
-- Safe to re-run.

CREATE TABLE IF NOT EXISTS trial_warning_emails (
  user_id        UUID NOT NULL,
  threshold_days INT  NOT NULL CHECK (threshold_days IN (7, 3)),
  sent_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, threshold_days)
);

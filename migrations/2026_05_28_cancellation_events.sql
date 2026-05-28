-- 2026-05-28: append-only churn log.
--
-- Every cancellation attempt (whether the user took the save offer, went
-- through with cancelling, or reactivated) writes one row. Lets us
-- analyse churn reasons over time without trying to keep current state
-- in sync on the subscriptions row.
--
-- We also use this table to prevent retention-offer abuse: if a user
-- accepted an offer in the last 12 months we skip the offer step on the
-- next cancel attempt.
--
-- Safe to re-run: uses IF NOT EXISTS guards.

CREATE TABLE IF NOT EXISTS subscription_cancellation_events (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID NOT NULL,
  happened_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  reason             TEXT NOT NULL CHECK (reason IN (
                       'too_expensive',
                       'not_using',
                       'missing_feature',
                       'found_alternative',
                       'stopped_freelancing',
                       'other'
                     )),
  comment            TEXT NULL,
  outcome            TEXT NOT NULL CHECK (outcome IN (
                       'offer_accepted',
                       'cancelled',
                       'reactivated'
                     )),
  -- For offer_accepted: the Stripe credit txn id or local marker.
  stripe_reference   TEXT NULL,
  -- Snapshot of the plan at cancellation time — handy for analytics
  -- since a later plan change would otherwise lose the signal.
  plan_at_event      TEXT NULL
);

-- Quick lookups for "did this user accept a save offer recently?" (abuse
-- prevention) and per-user history.
CREATE INDEX IF NOT EXISTS cancel_events_user_recent
  ON subscription_cancellation_events (user_id, happened_at DESC);

CREATE INDEX IF NOT EXISTS cancel_events_offer_accepted
  ON subscription_cancellation_events (user_id, happened_at DESC)
  WHERE outcome = 'offer_accepted';

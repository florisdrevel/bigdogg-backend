-- Finding #9: quote share_tokens and client-onboarding invite tokens had
-- no expiry, so any leaked share link worked forever. Add nullable expiry
-- columns. NULL = legacy non-expiring token (kept working until re-issued);
-- new tokens get a timestamp stamped by the app at issue time.
--
-- Apply this to Supabase BEFORE deploying the matching backend code.

ALTER TABLE quotes
    ADD COLUMN IF NOT EXISTS share_token_expires_at timestamptz;

ALTER TABLE client_invites
    ADD COLUMN IF NOT EXISTS expires_at timestamptz;

-- Optional: index for any future cleanup job that prunes expired invites.
CREATE INDEX IF NOT EXISTS idx_client_invites_expires_at
    ON client_invites (expires_at);

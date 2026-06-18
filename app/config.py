import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    secret_key: str = os.getenv("SECRET_KEY", "fallback_secret")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    # Single source of truth for the Claude model used across all AI features
    # (invoice/quote gen, receipt + bank-statement parsing, annual tax tips).
    # When Anthropic retires a model the old id starts returning 404 — bump
    # this one value (or set ANTHROPIC_MODEL in the env) instead of editing
    # every router. Verify current ids at platform.claude.com when changing.
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_connect_webhook_secret: str = os.getenv("STRIPE_CONNECT_WEBHOOK_SECRET", "")
    gmail_user: str = os.getenv("GMAIL_USER", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    # No default — the previous default literal leaked in git history.
    # Fail-closed in require_cron_secret() when this is empty.
    cron_secret: str = os.getenv("CRON_SECRET", "")
    # TrueLayer Open Banking. Sandbox is free and instant for testing;
    # live access requires KYC (uploaded business docs in the Console).
    # Flip `truelayer_use_sandbox` to "false" once live creds are issued.
    truelayer_client_id: str = os.getenv("TRUELAYER_CLIENT_ID", "")
    truelayer_client_secret: str = os.getenv("TRUELAYER_CLIENT_SECRET", "")
    truelayer_use_sandbox: str = os.getenv("TRUELAYER_USE_SANDBOX", "true")
    # Fernet key used to encrypt TrueLayer access/refresh tokens at rest in
    # user_profiles. Generate once with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Rotating this key orphans existing connections (they fail to decrypt
    # and surface as "reconnect needed") — acceptable, the user just
    # reconnects. /connect fails closed (500) if this is unset.
    tl_token_enc_key: str = os.getenv("TL_TOKEN_ENC_KEY", "")
    # Optional restriction on the LIVE bank-connect flow. DEFAULT-OPEN:
    # unset/empty means everyone can use it (launched state). Set to a
    # comma-separated list of Supabase user_ids to RESTRICT it to those
    # accounts (closed beta / incident kill-switch); "*" also = everyone.
    bank_live_user_ids: str = os.getenv("BANK_LIVE_USER_IDS", "")
    # Origin used in share links (client invites + quote share). Defaults
    # to the Railway hostname so previews render without extra DNS work;
    # set to "https://link.bigdogg.nl" once the custom subdomain is live.
    share_link_origin: str = os.getenv("SHARE_LINK_ORIGIN", "https://bigdogg-production.up.railway.app")

settings = Settings()

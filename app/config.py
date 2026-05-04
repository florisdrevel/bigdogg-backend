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
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_connect_webhook_secret: str = os.getenv("STRIPE_CONNECT_WEBHOOK_SECRET", "")
    gmail_user: str = os.getenv("GMAIL_USER", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "")
    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    cron_secret: str = os.getenv("CRON_SECRET", "bigdogg-cron-2026")
    tink_client_id: str = os.getenv("TINK_CLIENT_ID", "")
    tink_client_secret: str = os.getenv("TINK_CLIENT_SECRET", "")
    gocardless_secret_id: str = os.getenv("GOCARDLESS_SECRET_ID", "")
    gocardless_secret_key: str = os.getenv("GOCARDLESS_SECRET_KEY", "")

settings = Settings()

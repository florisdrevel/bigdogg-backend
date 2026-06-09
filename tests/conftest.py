"""Test configuration. Sets fake env vars so `app.config` + `app.database`
import cleanly in test contexts without needing a real Supabase or
TrueLayer. None of the matcher tests touch Supabase — they exercise pure
functions on `app.routers.banking` — but the surrounding module imports do."""

import os

from cryptography.fernet import Fernet

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake_service_key")
os.environ.setdefault("SUPABASE_ANON_KEY", "fake_anon_key")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake_anthropic")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("RESEND_API_KEY", "fake_resend")
os.environ.setdefault("TRUELAYER_CLIENT_ID", "fake_truelayer_id")
os.environ.setdefault("TRUELAYER_CLIENT_SECRET", "fake_truelayer_secret")
# A valid (ephemeral) Fernet key so the token-encryption helpers work.
os.environ.setdefault("TL_TOKEN_ENC_KEY", Fernet.generate_key().decode())
os.environ.setdefault("CRON_SECRET", "fake_cron_secret_for_tests")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

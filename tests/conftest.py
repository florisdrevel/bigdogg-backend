"""Test configuration. Sets fake env vars so `app.config` + `app.database`
import cleanly in test contexts without needing a real Supabase or Tink.
None of the matcher tests touch Supabase — they exercise pure functions
on `app.routers.banking` — but the surrounding module imports do."""

import os

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake_service_key")
os.environ.setdefault("SUPABASE_ANON_KEY", "fake_anon_key")
os.environ.setdefault("ANTHROPIC_API_KEY", "fake_anthropic")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("RESEND_API_KEY", "fake_resend")
os.environ.setdefault("TINK_CLIENT_ID", "fake_tink_id")
os.environ.setdefault("TINK_CLIENT_SECRET", "fake_tink_secret")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

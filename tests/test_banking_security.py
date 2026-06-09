"""Security-relevant unit tests for the flag-gated TrueLayer rollout.

Covers the two controls added when un-gating the live bank flow:
  * token-at-rest encryption — access/refresh tokens are Fernet-encrypted
    before they hit user_profiles, decrypt round-trips, and legacy
    plaintext rows (written before encryption existed) still read.
  * the BANK_LIVE_USER_IDS allowlist that keeps the live flow dark for
    everyone except the founder during rollout.

Pure functions only — no Supabase, no network. TL_TOKEN_ENC_KEY is set to
an ephemeral Fernet key in conftest.py.
"""
import pytest

from app.config import settings
from app.routers.banking import (
    _encrypt_token,
    _decrypt_token,
    _live_enabled,
)


# ─── token encryption at rest ──────────────────────────────────
def test_encrypt_decrypt_round_trip():
    plain = "test-access-token-abc123"
    encrypted = _encrypt_token(plain)
    assert encrypted is not None
    assert encrypted != plain                      # actually ciphertext
    assert "test-access-token" not in encrypted    # token not recoverable by eye
    assert _decrypt_token(encrypted) == plain


def test_encrypt_none_passes_through():
    # A missing refresh_token must not blow up the write path.
    assert _encrypt_token(None) is None


def test_decrypt_tolerates_legacy_plaintext():
    # A row written before encryption existed isn't a valid Fernet token;
    # it must read back unchanged rather than raising.
    assert _decrypt_token("legacy-plaintext-token") == "legacy-plaintext-token"


def test_decrypt_empty_passes_through():
    assert _decrypt_token(None) is None
    assert _decrypt_token("") == ""


def test_encrypt_fails_closed_without_key(monkeypatch):
    # With no key configured we must refuse to store a plaintext token.
    from fastapi import HTTPException
    monkeypatch.setattr(settings, "tl_token_enc_key", "")
    with pytest.raises(HTTPException) as exc:
        _encrypt_token("would-be-plaintext")
    assert exc.value.status_code == 500


# ─── live-flow allowlist ───────────────────────────────────────
def test_live_enabled_allows_listed_user(monkeypatch):
    monkeypatch.setattr(settings, "bank_live_user_ids", "user-a, user-b ,user-c")
    assert _live_enabled("user-b") is True


def test_live_enabled_blocks_unlisted_user(monkeypatch):
    monkeypatch.setattr(settings, "bank_live_user_ids", "user-a,user-b")
    assert _live_enabled("user-z") is False


def test_live_enabled_empty_allowlist_allows_everyone(monkeypatch):
    # Default-open launched state: no allowlist configured -> everyone in.
    monkeypatch.setattr(settings, "bank_live_user_ids", "")
    assert _live_enabled("user-a") is True


def test_live_enabled_wildcard_allows_everyone(monkeypatch):
    monkeypatch.setattr(settings, "bank_live_user_ids", "*")
    assert _live_enabled("anyone-at-all") is True


def test_live_enabled_blank_user_id_with_restriction(monkeypatch):
    # When an explicit allowlist IS set, a blank user_id is still refused.
    monkeypatch.setattr(settings, "bank_live_user_ids", "user-a")
    assert _live_enabled("") is False

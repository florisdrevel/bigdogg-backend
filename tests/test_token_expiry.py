"""Regression tests for finding #9 — quote share_tokens and client-onboarding
invite tokens never expired. Now stamped at issue time and enforced at use."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from app.services.tokens import is_expired, expiry_in_days
from app.routers import quotes as quotes_router
from app.routers import clients as clients_router
from tests.fake_supabase import FakeSupabase

PAST = expiry_in_days(-1)
FUTURE = expiry_in_days(30)


# ── is_expired unit ─────────────────────────────────────────────

def test_is_expired_semantics():
    assert is_expired(PAST) is True
    assert is_expired(FUTURE) is False
    assert is_expired(None) is False        # legacy non-expiring
    assert is_expired("") is False
    assert is_expired("not-a-date") is False  # fail open, don't lock out
    # 'Z' suffix form Supabase sometimes returns.
    assert is_expired("2000-01-01T00:00:00Z") is True


# ── quote share link ────────────────────────────────────────────

def _quotes_db(monkeypatch, expires_at):
    fake = FakeSupabase({
        "quotes": [{"id": "q1", "user_id": "u1", "share_token": "tok",
                    "share_token_expires_at": expires_at}],
    })
    monkeypatch.setattr(quotes_router, "supabase", fake)
    return fake


def test_quote_lookup_rejects_expired(monkeypatch):
    _quotes_db(monkeypatch, PAST)
    with pytest.raises(HTTPException) as exc:
        quotes_router._lookup_quote_by_token("tok")
    assert exc.value.status_code == 410


def test_quote_lookup_allows_valid(monkeypatch):
    _quotes_db(monkeypatch, FUTURE)
    assert quotes_router._lookup_quote_by_token("tok")["id"] == "q1"


def test_quote_lookup_allows_legacy_null(monkeypatch):
    _quotes_db(monkeypatch, None)
    assert quotes_router._lookup_quote_by_token("tok")["id"] == "q1"


def test_quote_lookup_unknown_token_404(monkeypatch):
    _quotes_db(monkeypatch, FUTURE)
    with pytest.raises(HTTPException) as exc:
        quotes_router._lookup_quote_by_token("nope")
    assert exc.value.status_code == 404


# ── client onboarding invite ────────────────────────────────────

def _clients_db(monkeypatch, expires_at):
    fake = FakeSupabase({
        "client_invites": [{"token": "inv", "user_id": "u1",
                            "used": False, "expires_at": expires_at}],
    })
    monkeypatch.setattr(clients_router, "supabase", fake)
    return fake


async def test_onboarding_info_expired_is_invalid(monkeypatch):
    _clients_db(monkeypatch, PAST)
    res = await clients_router.get_onboarding_info("inv")
    assert res["valid"] is False


async def test_onboarding_info_valid(monkeypatch):
    _clients_db(monkeypatch, FUTURE)
    res = await clients_router.get_onboarding_info("inv")
    assert res["valid"] is True


async def test_complete_onboarding_expired_410(monkeypatch):
    _clients_db(monkeypatch, PAST)
    payload = clients_router.ClientOnboarding(
        company_name="X", contact_name="Y", email="y@x.com",
    )
    with pytest.raises(HTTPException) as exc:
        await clients_router.complete_onboarding("inv", payload)
    assert exc.value.status_code == 410

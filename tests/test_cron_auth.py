"""Tests for the constant-time cron secret check."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from app.services import cron_auth


def _req(secret_header: str | None) -> SimpleNamespace:
    headers = {"x-cron-secret": secret_header} if secret_header is not None else {}
    return SimpleNamespace(headers=headers)


def test_accepts_matching_secret(monkeypatch):
    monkeypatch.setattr(cron_auth.settings, "cron_secret", "the_real_secret")
    # No exception = accepted
    cron_auth.require_cron_secret(_req("the_real_secret"))


def test_rejects_wrong_secret(monkeypatch):
    monkeypatch.setattr(cron_auth.settings, "cron_secret", "the_real_secret")
    with pytest.raises(HTTPException) as exc:
        cron_auth.require_cron_secret(_req("wrong"))
    assert exc.value.status_code == 401


def test_rejects_missing_header(monkeypatch):
    monkeypatch.setattr(cron_auth.settings, "cron_secret", "the_real_secret")
    with pytest.raises(HTTPException) as exc:
        cron_auth.require_cron_secret(_req(None))
    assert exc.value.status_code == 401


def test_fails_closed_when_configured_secret_is_empty(monkeypatch):
    """Misconfig must not silently accept any header."""
    monkeypatch.setattr(cron_auth.settings, "cron_secret", "")
    with pytest.raises(HTTPException) as exc:
        cron_auth.require_cron_secret(_req("anything"))
    assert exc.value.status_code == 503
    assert exc.value.detail == "cron_secret_not_configured"


def test_fails_closed_when_configured_secret_is_legacy_default(monkeypatch):
    """The pre-fix default literal was leaked in git history and must
    never be honored even if Railway is misconfigured back to it."""
    monkeypatch.setattr(cron_auth.settings, "cron_secret", "bigdogg-cron-2026")
    with pytest.raises(HTTPException) as exc:
        cron_auth.require_cron_secret(_req("bigdogg-cron-2026"))
    assert exc.value.status_code == 503


def test_constant_time_compare_does_not_short_circuit(monkeypatch):
    """Sanity check: a header that shares a long prefix with the real
    secret should still get rejected (not return on the first byte mismatch)."""
    monkeypatch.setattr(cron_auth.settings, "cron_secret", "abcdefghij")
    with pytest.raises(HTTPException):
        cron_auth.require_cron_secret(_req("abcdefghix"))
    with pytest.raises(HTTPException):
        cron_auth.require_cron_secret(_req("xbcdefghij"))

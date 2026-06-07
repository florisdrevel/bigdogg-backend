"""Tests for the signed download-token mechanism (finding #7)."""
from types import SimpleNamespace
import time
import pytest
from fastapi import HTTPException

from app.services import download_token as dt


def _req(headers=None, query=None):
    return SimpleNamespace(
        headers=headers or {},
        query_params=query or {},
    )


def test_issue_verify_roundtrip():
    tok = dt.issue("user-A", "a@b.com", "invoice_pdf:inv1")
    uid, email = dt.verify(tok, "invoice_pdf:inv1")
    assert uid == "user-A"
    assert email == "a@b.com"


def test_verify_rejects_wrong_scope():
    tok = dt.issue("user-A", "a@b.com", "invoice_pdf:inv1")
    with pytest.raises(HTTPException) as exc:
        dt.verify(tok, "invoice_pdf:inv2")
    assert exc.value.status_code == 403


def test_verify_rejects_tampered_signature():
    tok = dt.issue("user-A", "a@b.com", "btw_pdf")
    body, _sig = tok.split(".", 1)
    forged = body + "." + "AAAA"
    with pytest.raises(HTTPException) as exc:
        dt.verify(forged, "btw_pdf")
    assert exc.value.status_code == 401


def test_verify_rejects_tampered_payload():
    # Re-sign nothing: flip the body to escalate to another user but keep
    # the old signature — must fail the HMAC check.
    tok = dt.issue("user-A", "a@b.com", "btw_pdf")
    body, sig = tok.split(".", 1)
    other = dt._b64e(b'{"u":"user-B","m":"","s":"btw_pdf","e":9999999999}')
    with pytest.raises(HTTPException):
        dt.verify(f"{other}.{sig}", "btw_pdf")


def test_verify_rejects_expired():
    tok = dt.issue("user-A", "a@b.com", "btw_pdf", ttl_seconds=-1)
    with pytest.raises(HTTPException) as exc:
        dt.verify(tok, "btw_pdf")
    assert exc.value.status_code == 401


def test_verify_rejects_garbage():
    with pytest.raises(HTTPException):
        dt.verify("not-a-token", "btw_pdf")


# ── resolve_download_identity priority order ────────────────────

def test_resolve_prefers_dt_query(monkeypatch):
    tok = dt.issue("user-A", "a@b.com", "invoice_pdf:inv1")
    uid, email = dt.resolve_download_identity(
        _req(query={"dt": tok}), scope="invoice_pdf:inv1")
    assert uid == "user-A"


def test_resolve_uses_bearer_header(monkeypatch):
    fake_user = SimpleNamespace(user=SimpleNamespace(id="user-H", email="h@b.com"))
    monkeypatch.setattr(dt.supabase.auth, "get_user", lambda _t: fake_user)
    uid, email = dt.resolve_download_identity(
        _req(headers={"authorization": "Bearer xyz"}), scope="btw_pdf")
    assert uid == "user-H"
    assert email == "h@b.com"


def test_resolve_legacy_jwt_fallback(monkeypatch):
    fake_user = SimpleNamespace(user=SimpleNamespace(id="user-L", email="l@b.com"))
    monkeypatch.setattr(dt.supabase.auth, "get_user", lambda _t: fake_user)
    uid, _ = dt.resolve_download_identity(
        _req(), scope="btw_pdf", legacy_jwt="legacy-jwt")
    assert uid == "user-L"


def test_resolve_dt_scope_mismatch_403():
    tok = dt.issue("user-A", "a@b.com", "invoice_pdf:inv1")
    with pytest.raises(HTTPException) as exc:
        dt.resolve_download_identity(_req(query={"dt": tok}), scope="invoice_pdf:OTHER")
    assert exc.value.status_code == 403


def test_resolve_no_credentials_401():
    with pytest.raises(HTTPException) as exc:
        dt.resolve_download_identity(_req(), scope="btw_pdf")
    assert exc.value.status_code == 401

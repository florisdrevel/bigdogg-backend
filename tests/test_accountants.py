"""Tests for the token-gated accountant portal.

The old "accept-invite + accountant_clients" flow was replaced by a simpler
link-as-credential model. These tests cover the three security gates
(`_resolve_portal_token`: not_found / revoked / expired) and the
overview-aggregation math.
"""
from datetime import datetime, timezone, timedelta
import types
import pytest
from fastapi import HTTPException

from app.routers import accountants as acc


class _FakeQuery:
    """Tiny chainable stub mimicking the supabase-py builder API."""

    def __init__(self, rows):
        self._rows = rows

    def select(self, *_a, **_kw): return self
    def eq(self, *_a, **_kw):     return self
    def lte(self, *_a, **_kw):    return self
    def gte(self, *_a, **_kw):    return self
    def order(self, *_a, **_kw):  return self
    def limit(self, *_a, **_kw):  return self
    def insert(self, *_a, **_kw): return self
    def update(self, *_a, **_kw): return self
    def delete(self, *_a, **_kw): return self
    def single(self):             return self

    def execute(self):
        return types.SimpleNamespace(data=self._rows)


class _FakeSupabase:
    def __init__(self, table_rows):
        self._table_rows = table_rows

    def table(self, name):
        return _FakeQuery(self._table_rows.get(name, []))


def _patch_supabase(monkeypatch, table_rows):
    monkeypatch.setattr(acc, "supabase", _FakeSupabase(table_rows))


# ── _resolve_portal_token ──────────────────────────────────────
def test_resolve_token_not_found(monkeypatch):
    _patch_supabase(monkeypatch, {"accountant_invites": []})
    with pytest.raises(HTTPException) as exc:
        acc._resolve_portal_token("does-not-exist")
    assert exc.value.status_code == 404
    assert exc.value.detail == "link_not_found"


def test_resolve_token_revoked(monkeypatch):
    row = {
        "token": "t1", "user_id": "u", "email": "a@b.c",
        "used": True,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
    }
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        acc._resolve_portal_token("t1")
    assert exc.value.status_code == 403
    assert exc.value.detail == "link_revoked"


def test_resolve_token_expired(monkeypatch):
    row = {
        "token": "t1", "user_id": "u", "email": "a@b.c",
        "used": False,
        "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    }
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        acc._resolve_portal_token("t1")
    assert exc.value.status_code == 410
    assert exc.value.detail == "link_expired"


def test_resolve_token_active(monkeypatch):
    row = {
        "token": "t1", "user_id": "u", "email": "a@b.c",
        "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
    }
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    result = acc._resolve_portal_token("t1")
    assert result["user_id"] == "u"


# ── portal_overview math ──────────────────────────────────────
async def test_portal_overview_math(monkeypatch):
    valid_row = {
        "token": "tok", "user_id": "owner-1", "email": "a@b.c",
        "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }
    invoices = [
        {"total_excl_btw": 1000, "total_incl_btw": 1210, "btw_amount": 210, "status": "paid", "issue_date": "2026-03-01"},
        {"total_excl_btw": 500,  "total_incl_btw": 605,  "btw_amount": 105, "status": "sent", "issue_date": "2026-04-01"},
    ]
    expenses = [
        {"amount_excl_btw": 200, "amount_incl_btw": 242, "btw_amount": 42, "expense_date": "2026-03-15"},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [valid_row],
        "invoices":           invoices,
        "expenses":           expenses,
    })

    result = await acc.portal_overview("tok")
    assert result["revenue_excl"] == 1500.0
    assert result["btw_collected"] == 315.0
    assert result["expense_excl"] == 200.0
    assert result["btw_paid"]     == 42.0
    assert result["btw_payable"]  == round(315.0 - 42.0, 2)
    assert result["profit_excl"]  == 1300.0
    assert result["invoice_count"] == 2
    assert result["paid_count"]    == 1
    assert result["expense_count"] == 1


async def test_portal_overview_revoked(monkeypatch):
    row = {
        "token": "tok", "user_id": "u", "email": "a@b.c", "used": True,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        await acc.portal_overview("tok")
    assert exc.value.status_code == 403


async def test_portal_invoices_expired(monkeypatch):
    row = {
        "token": "tok", "user_id": "u", "email": "a@b.c", "used": False,
        "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    }
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        await acc.portal_invoices("tok")
    assert exc.value.status_code == 410


async def test_portal_meta_owner_name_fallback(monkeypatch):
    row = {
        "token": "tok", "user_id": "u", "email": "a@b.c", "used": False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
        "created_at": "2026-05-01T10:00:00Z",
    }
    profile = {"business_name": "", "full_name": "Floris D",
               "kvk_number": "12345678", "btw_number": "NL000000000B01"}
    _patch_supabase(monkeypatch, {
        "accountant_invites": [row],
        "user_profiles":      [profile],
    })

    result = await acc.portal_meta("tok")
    assert result["owner_name"] == "Floris D"
    assert result["business_name"] == ""
    assert result["kvk_number"] == "12345678"
    assert result["btw_number"] == "NL000000000B01"
    assert result["invite_email"] == "a@b.c"

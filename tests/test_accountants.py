"""Tests for the accountants router.

Two security-critical paths get test coverage:

  1. _verify_link — must 403 when no active accountant_clients row
     exists between the requester and the requested client_user_id.
     Without this gate, any logged-in user could read any other user's
     invoices/expenses just by knowing their UUID.

  2. accept_invite — the email on the invite must match the
     authenticated accountant's email when both are present, otherwise
     a leaked link could be redeemed by anyone.

Also covers the simple aggregations in the overview endpoint
(revenue/expense/btw arithmetic).

Supabase is monkeypatched away — these tests stub the table().select()
chain and capture the mutations.
"""

from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.routers import accountants


# ═══════════════════════════════════════════════════════════════
# Tiny supabase stub
# ═══════════════════════════════════════════════════════════════
class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows
        self.data = rows

    # All the `.eq().limit().execute()` style chaining returns self.
    def select(self, *_a, **_kw): return self
    def eq(self, *_a, **_kw): return self
    def gte(self, *_a, **_kw): return self
    def lte(self, *_a, **_kw): return self
    def order(self, *_a, **_kw): return self
    def limit(self, *_a, **_kw): return self
    def execute(self): return SimpleNamespace(data=self._rows)


class _FakeSupabase:
    def __init__(self, table_data):
        self._table_data = table_data

    def table(self, name):
        return _FakeQuery(self._table_data.get(name, []))


# ═══════════════════════════════════════════════════════════════
# _verify_link — the cross-user access gate
# ═══════════════════════════════════════════════════════════════
def test_verify_link_passes_when_active_link_exists(monkeypatch):
    fake = _FakeSupabase({
        "accountant_clients": [{"id": "ac_1"}],
    })
    monkeypatch.setattr(accountants, "supabase", fake)
    # Should not raise.
    accountants._verify_link("acc_user", "client_user")


def test_verify_link_raises_403_when_no_link(monkeypatch):
    fake = _FakeSupabase({"accountant_clients": []})
    monkeypatch.setattr(accountants, "supabase", fake)
    with pytest.raises(HTTPException) as exc:
        accountants._verify_link("acc_user", "client_user")
    assert exc.value.status_code == 403
    assert exc.value.detail == "not_linked"


def test_verify_link_treats_revoked_as_no_link(monkeypatch):
    """`_verify_link` filters by status='active'. Our fake supabase
    doesn't honour the eq() filter, but if the revoked-row case passes
    here, the production code (which DOES filter) would also pass.
    Conversely, the test is mainly here to guard against a refactor
    accidentally dropping the `.eq("status", "active")` clause."""
    # Production code calls .eq("status", "active") — to assert we keep
    # filtering, we wrap eq() with a recorder and check the call list.
    calls = []

    class _Recorder(_FakeQuery):
        def eq(self, k, v):
            calls.append((k, v))
            return self

    class _RecordingSupabase:
        def table(self, _):
            return _Recorder([])

    monkeypatch.setattr(accountants, "supabase", _RecordingSupabase())
    with pytest.raises(HTTPException):
        accountants._verify_link("acc_user", "client_user")
    assert ("status", "active") in calls
    assert ("accountant_id", "acc_user") in calls
    assert ("user_id", "client_user") in calls


# ═══════════════════════════════════════════════════════════════
# overview arithmetic
# ═══════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_overview_aggregates_revenue_expense_and_btw(monkeypatch):
    fake = _FakeSupabase({
        "accountant_clients": [{"id": "ac_1"}],
        "invoices": [
            {"total_excl_btw": 1000.0, "total_incl_btw": 1210.0,
             "btw_amount": 210.0, "status": "paid",
             "issue_date": "2026-01-15"},
            {"total_excl_btw": 500.0, "total_incl_btw": 605.0,
             "btw_amount": 105.0, "status": "sent",
             "issue_date": "2026-02-01"},
        ],
        "expenses": [
            {"amount_excl_btw": 100.0, "amount_incl_btw": 121.0,
             "btw_amount": 21.0, "expense_date": "2026-01-20"},
            {"amount_excl_btw": 50.0, "amount_incl_btw": 60.5,
             "btw_amount": 10.5, "expense_date": "2026-03-01"},
        ],
    })
    monkeypatch.setattr(accountants, "supabase", fake)

    request = MagicMock()
    request.headers = {"authorization": "Bearer fake"}

    monkeypatch.setattr(accountants, "get_user_id",
                        lambda req: "acc_user")
    out = await accountants.client_overview("client_user", request)

    assert out["revenue_excl"] == 1500.0
    assert out["revenue_incl"] == 1815.0
    assert out["btw_collected"] == 315.0
    assert out["expense_excl"] == 150.0
    assert out["expense_incl"] == 181.5
    assert out["btw_paid"] == 31.5
    assert out["btw_payable"] == round(315.0 - 31.5, 2)
    assert out["profit_excl"] == round(1500.0 - 150.0, 2)
    assert out["invoice_count"] == 2
    assert out["paid_count"] == 1
    assert out["expense_count"] == 2


@pytest.mark.asyncio
async def test_overview_403s_when_not_linked(monkeypatch):
    fake = _FakeSupabase({"accountant_clients": []})
    monkeypatch.setattr(accountants, "supabase", fake)
    monkeypatch.setattr(accountants, "get_user_id",
                        lambda req: "acc_user")
    with pytest.raises(HTTPException) as exc:
        await accountants.client_overview("client_user", MagicMock())
    assert exc.value.status_code == 403


# ═══════════════════════════════════════════════════════════════
# invoices / expenses listing
# ═══════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_client_invoices_403s_when_not_linked(monkeypatch):
    monkeypatch.setattr(accountants, "supabase",
                        _FakeSupabase({"accountant_clients": []}))
    monkeypatch.setattr(accountants, "get_user_id", lambda req: "acc_user")
    with pytest.raises(HTTPException) as exc:
        await accountants.client_invoices("client_user", MagicMock())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_client_expenses_403s_when_not_linked(monkeypatch):
    monkeypatch.setattr(accountants, "supabase",
                        _FakeSupabase({"accountant_clients": []}))
    monkeypatch.setattr(accountants, "get_user_id", lambda req: "acc_user")
    with pytest.raises(HTTPException) as exc:
        await accountants.client_expenses("client_user", MagicMock())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_client_invoices_returns_data_when_linked(monkeypatch):
    fake = _FakeSupabase({
        "accountant_clients": [{"id": "ac_1"}],
        "invoices": [{"id": "inv_1", "invoice_number": "INV-2026-0001"}],
    })
    monkeypatch.setattr(accountants, "supabase", fake)
    monkeypatch.setattr(accountants, "get_user_id", lambda req: "acc_user")
    out = await accountants.client_invoices("client_user", MagicMock())
    assert len(out["invoices"]) == 1
    assert out["invoices"][0]["invoice_number"] == "INV-2026-0001"


# ═══════════════════════════════════════════════════════════════
# accept_invite — the email-mismatch guard
# ═══════════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_accept_invite_rejects_email_mismatch(monkeypatch):
    """Invite for foo@bar.com but accountant is logged in as
    other@example.com → 403 email_mismatch. Otherwise a forwarded
    invite link could be redeemed by anyone."""

    class _RecordSupabase:
        def __init__(self):
            self.last_query_table = None

        def table(self, name):
            self.last_query_table = name
            if name == "accountant_invites":
                return _FakeQuery([{
                    "token": "tok",
                    "user_id": "owner",
                    "email": "foo@bar.com",
                    "used": False,
                    "expires_at": (datetime.now(timezone.utc)
                                   + timedelta(days=14)).isoformat(),
                }])
            return _FakeQuery([])

    monkeypatch.setattr(accountants, "supabase", _RecordSupabase())
    monkeypatch.setattr(accountants, "get_user_id",
                        lambda req: "acc_user")
    monkeypatch.setattr(accountants, "_user_email",
                        lambda req: "other@example.com")

    with pytest.raises(HTTPException) as exc:
        await accountants.accept_invite("tok", MagicMock())
    assert exc.value.status_code == 403
    assert exc.value.detail == "email_mismatch"


@pytest.mark.asyncio
async def test_accept_invite_rejects_already_used(monkeypatch):
    class _S:
        def table(self, name):
            if name == "accountant_invites":
                return _FakeQuery([{
                    "token": "tok",
                    "user_id": "owner",
                    "email": "foo@bar.com",
                    "used": True,
                }])
            return _FakeQuery([])
    monkeypatch.setattr(accountants, "supabase", _S())
    monkeypatch.setattr(accountants, "get_user_id",
                        lambda req: "acc_user")
    monkeypatch.setattr(accountants, "_user_email",
                        lambda req: "foo@bar.com")

    with pytest.raises(HTTPException) as exc:
        await accountants.accept_invite("tok", MagicMock())
    assert exc.value.status_code == 400
    assert exc.value.detail == "invite_already_used"


@pytest.mark.asyncio
async def test_accept_invite_rejects_unknown_token(monkeypatch):
    class _S:
        def table(self, _):
            return _FakeQuery([])
    monkeypatch.setattr(accountants, "supabase", _S())
    monkeypatch.setattr(accountants, "get_user_id",
                        lambda req: "acc_user")
    monkeypatch.setattr(accountants, "_user_email",
                        lambda req: "foo@bar.com")

    with pytest.raises(HTTPException) as exc:
        await accountants.accept_invite("tok", MagicMock())
    assert exc.value.status_code == 404
    assert exc.value.detail == "invite_not_found"


@pytest.mark.asyncio
async def test_accept_invite_rejects_expired_invite(monkeypatch):
    class _S:
        def table(self, name):
            if name == "accountant_invites":
                return _FakeQuery([{
                    "token": "tok",
                    "user_id": "owner",
                    "email": "foo@bar.com",
                    "used": False,
                    "expires_at": (datetime.now(timezone.utc)
                                   - timedelta(days=1)).isoformat(),
                }])
            return _FakeQuery([])
    monkeypatch.setattr(accountants, "supabase", _S())
    monkeypatch.setattr(accountants, "get_user_id",
                        lambda req: "acc_user")
    monkeypatch.setattr(accountants, "_user_email",
                        lambda req: "foo@bar.com")

    with pytest.raises(HTTPException) as exc:
        await accountants.accept_invite("tok", MagicMock())
    assert exc.value.status_code == 400
    assert exc.value.detail == "invite_expired"

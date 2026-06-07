"""Cross-tenant regression tests for the banking link IDOR (finding #1).

Before the fix: any authenticated user could POST /banking/transactions/
{tx_id}/link with link_type='invoice' and linked_id=<victim's invoice id>,
and the backend would flip the victim's invoice to status='paid'. Same on
unlink (status='sent'). These tests reproduce the attack and assert it
now fails with 404 + no mutation to the victim's row.
"""
from types import SimpleNamespace
import pytest

from app.routers import banking
from app.services import tenant_db
from tests.fake_supabase import FakeSupabase


@pytest.fixture
def two_user_db(monkeypatch):
    """User A and User B with one invoice each; no existing bank links."""
    fake = FakeSupabase({
        "invoices": [
            {"id": "inv-A", "user_id": "user-A", "status": "sent",  "invoice_number": "A-1"},
            {"id": "inv-B", "user_id": "user-B", "status": "sent",  "invoice_number": "B-1"},
        ],
        "expenses": [
            {"id": "exp-A", "user_id": "user-A", "amount_ex_btw": 50},
            {"id": "exp-B", "user_id": "user-B", "amount_ex_btw": 70},
        ],
        "investments": [
            {"id": "inv-asset-A", "user_id": "user-A", "amount": 1000},
        ],
        "bank_transaction_links": [],
    })
    # Both the route module and the tenant_db helpers must see the same fake.
    monkeypatch.setattr(banking, "supabase", fake)
    monkeypatch.setattr(tenant_db, "supabase", fake)
    return fake


def _fake_request(body: dict) -> SimpleNamespace:
    """Just enough of a Starlette Request to satisfy banking.set_transaction_link."""
    async def _json():
        return body
    return SimpleNamespace(json=_json)


# ── CONFIRMED IDOR regression ───────────────────────────────
async def test_user_B_cannot_mark_user_A_invoice_paid_via_link(two_user_db, monkeypatch):
    """The exact attack from finding #1:
    User B authenticates and posts a link with linked_id=inv-A
    (User A's invoice). Must 404; invoice A must stay 'sent'."""
    monkeypatch.setattr(banking, "get_user_id", lambda _req: "user-B")
    req = _fake_request({"link_type": "invoice", "linked_id": "inv-A"})

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await banking.set_transaction_link("tx-evil", req)
    assert exc.value.status_code == 404

    # The victim's invoice must NOT have been flipped to paid.
    inv_A = next(r for r in two_user_db.rows("invoices") if r["id"] == "inv-A")
    assert inv_A["status"] == "sent"

    # No link row should have been persisted (the ownership check must
    # fire BEFORE the _persist_link call).
    assert two_user_db.rows("bank_transaction_links") == []


async def test_user_B_cannot_link_user_A_expense(two_user_db, monkeypatch):
    """Same attack via expense link_type — expense doesn't have a
    side-effect status flip, but allowing the link still cross-pollutes
    bank_transaction_links with a foreign FK. Must 404."""
    monkeypatch.setattr(banking, "get_user_id", lambda _req: "user-B")
    req = _fake_request({"link_type": "expense", "linked_id": "exp-A"})

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await banking.set_transaction_link("tx-evil", req)
    assert exc.value.status_code == 404
    assert two_user_db.rows("bank_transaction_links") == []


async def test_user_B_cannot_link_user_A_investment(two_user_db, monkeypatch):
    monkeypatch.setattr(banking, "get_user_id", lambda _req: "user-B")
    req = _fake_request({"link_type": "investment", "linked_id": "inv-asset-A"})

    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await banking.set_transaction_link("tx-evil", req)
    assert exc.value.status_code == 404
    assert two_user_db.rows("bank_transaction_links") == []


# ── Legitimate owner still works ──────────────────────────
async def test_user_A_can_link_own_invoice_and_marks_paid(two_user_db, monkeypatch):
    """The happy path must continue to work — owner can link their own
    invoice and the status flips to 'paid'."""
    monkeypatch.setattr(banking, "get_user_id", lambda _req: "user-A")
    # _persist_link upserts on (user_id, tx_id) — see banking.py:711.
    req = _fake_request({"link_type": "invoice", "linked_id": "inv-A"})

    result = await banking.set_transaction_link("tx-1", req)
    assert result["success"] is True
    assert result["link"]["type"] == "invoice"
    inv_A = next(r for r in two_user_db.rows("invoices") if r["id"] == "inv-A")
    assert inv_A["status"] == "paid"


# ── Unlink revert is also owner-scoped ────────────────────
async def test_unlink_does_not_revert_foreign_invoice(two_user_db, monkeypatch):
    """Pre-fix state: a malicious link from User B referring to User A's
    invoice exists in bank_transaction_links (planted directly in the
    test DB to simulate a historical IDOR before the patch). User B then
    unlinks — the unlink path must NOT flip User A's invoice back to
    'sent' if it's been legitimately paid.
    """
    # Plant a historical bad link + force User A's invoice to 'paid' so
    # we can prove the unlink revert respects ownership.
    two_user_db.rows("invoices")[0]["status"] = "paid"  # inv-A
    two_user_db.rows("bank_transaction_links").append({
        "user_id":   "user-B",
        "tx_id":     "tx-hist",
        "link_type": "invoice",
        "linked_id": "inv-A",          # <-- foreign invoice
        "auto":      True,
    })
    monkeypatch.setattr(banking, "get_user_id", lambda _req: "user-B")
    req = _fake_request({"link_type": None, "linked_id": None})

    result = await banking.set_transaction_link("tx-hist", req)
    # Unlink itself succeeds (the link row was B's), but the revert is
    # skipped because the invoice doesn't belong to B.
    assert result["success"] is True
    inv_A = next(r for r in two_user_db.rows("invoices") if r["id"] == "inv-A")
    assert inv_A["status"] == "paid"  # untouched

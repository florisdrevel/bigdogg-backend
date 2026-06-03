"""Cross-tenant regression tests for the client-delete IDOR (finding #2).

Pre-fix: DELETE /api/v1/clients/{client_id} filtered the invoice probe
and the `UPDATE invoices SET client_id=NULL WHERE client_id=$1` only by
client_id — no user_id. An authenticated user could pass a foreign
client_id and (a) learn whether the other tenant had unpaid invoices,
and (b) null out the client_id on the victim's paid invoices.

The tests reproduce both probes and assert the route now 404s without
touching the victim's data.
"""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from app.routers import clients as clients_router
from app.services import tenant_db
from tests.fake_supabase import FakeSupabase


@pytest.fixture
def two_user_db(monkeypatch):
    """User A has a client with 2 invoices (1 paid, 1 sent).
       User B has nothing."""
    fake = FakeSupabase({
        "clients": [
            {"id": "cli-A", "user_id": "user-A", "contact_name": "Alice"},
        ],
        "invoices": [
            {"id": "inv-A-paid", "user_id": "user-A", "client_id": "cli-A", "status": "paid"},
            {"id": "inv-A-sent", "user_id": "user-A", "client_id": "cli-A", "status": "sent"},
        ],
    })
    monkeypatch.setattr(clients_router, "supabase", fake)
    monkeypatch.setattr(tenant_db, "supabase", fake)
    return fake


def _req() -> SimpleNamespace:
    return SimpleNamespace()


async def test_user_B_cannot_probe_user_A_unpaid_invoices(two_user_db, monkeypatch):
    """User B tries to DELETE User A's client. Pre-fix this would have
    returned 400 with an unpaid count (the probe). Now it must 404
    BEFORE touching invoices at all."""
    monkeypatch.setattr(clients_router, "get_user_id", lambda _req: "user-B")

    with pytest.raises(HTTPException) as exc:
        await clients_router.delete_client("cli-A", _req())
    assert exc.value.status_code == 404


async def test_user_B_cannot_null_out_user_A_invoices(two_user_db, monkeypatch):
    """The 'null out paid invoices client_id' mass update must NOT run
    against the victim's invoices."""
    monkeypatch.setattr(clients_router, "get_user_id", lambda _req: "user-B")

    with pytest.raises(HTTPException) as exc:
        await clients_router.delete_client("cli-A", _req())
    assert exc.value.status_code == 404

    # Verify ALL of User A's invoices still have client_id='cli-A'.
    invoices = two_user_db.rows("invoices")
    assert all(inv["client_id"] == "cli-A" for inv in invoices)


async def test_user_A_legitimate_delete_still_works_with_no_unpaid(two_user_db, monkeypatch):
    """Owner can still delete their own client when no unpaid invoices
    exist — the paid invoice keeps its row but loses client_id."""
    # Flip the sent invoice to paid so the legitimate delete proceeds.
    sent = next(i for i in two_user_db.rows("invoices") if i["id"] == "inv-A-sent")
    sent["status"] = "paid"
    monkeypatch.setattr(clients_router, "get_user_id", lambda _req: "user-A")

    result = await clients_router.delete_client("cli-A", _req())
    assert result["message"] == "Client deleted"

    # The client row is gone.
    assert not any(c["id"] == "cli-A" for c in two_user_db.rows("clients"))
    # Both paid invoices kept, but client_id detached.
    for inv in two_user_db.rows("invoices"):
        assert inv["client_id"] is None


async def test_user_A_blocked_by_own_unpaid_invoices(two_user_db, monkeypatch):
    """Owner with unpaid invoices still gets the 400 + Dutch message."""
    monkeypatch.setattr(clients_router, "get_user_id", lambda _req: "user-A")

    with pytest.raises(HTTPException) as exc:
        await clients_router.delete_client("cli-A", _req())
    assert exc.value.status_code == 400
    assert "onbetaalde" in exc.value.detail.lower()
    # Client and invoices untouched.
    assert any(c["id"] == "cli-A" for c in two_user_db.rows("clients"))

"""Cross-tenant regression tests for finding #10 — no-op writes returning 200.

Pre-fix: DELETE on hours / investments / expenses and the soft-delete on
products were scoped with `.eq("user_id", user_id)` but ignored whether
the filter actually matched a row, so a foreign / non-existent id returned
200. That leaks "row exists somewhere" vs "doesn't exist" to a UUID-probing
attacker. Post-fix every path 404s on a miss and leaves the victim's row
untouched.
"""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from app.routers import hours as hours_router
from app.routers import investments as investments_router
from app.routers import expenses as expenses_router
from app.routers import products as products_router
from app.services import tenant_db
from tests.fake_supabase import FakeSupabase


def _req() -> SimpleNamespace:
    return SimpleNamespace()


@pytest.fixture
def db(monkeypatch):
    """User A owns one row in each table. User B owns nothing."""
    fake = FakeSupabase({
        "hours": [{"id": "h-A", "user_id": "user-A", "hours": 3}],
        "investments": [{"id": "i-A", "user_id": "user-A", "amount": 500}],
        "expenses": [{"id": "e-A", "user_id": "user-A", "amount_ex_btw": 50}],
        "products": [{"id": "p-A", "user_id": "user-A", "is_active": True}],
    })
    for mod in (hours_router, investments_router, expenses_router, products_router, tenant_db):
        monkeypatch.setattr(mod, "supabase", fake)
    return fake


def _as_user(monkeypatch, uid):
    for mod in (hours_router, investments_router, expenses_router, products_router):
        monkeypatch.setattr(mod, "get_user_id", lambda _req, _uid=uid: _uid)


async def test_foreign_delete_hours_404s(db, monkeypatch):
    _as_user(monkeypatch, "user-B")
    with pytest.raises(HTTPException) as exc:
        await hours_router.delete_hours("h-A", _req())
    assert exc.value.status_code == 404
    assert any(r["id"] == "h-A" for r in db.rows("hours"))


async def test_foreign_delete_investment_404s(db, monkeypatch):
    _as_user(monkeypatch, "user-B")
    with pytest.raises(HTTPException) as exc:
        await investments_router.delete_investment("i-A", _req())
    assert exc.value.status_code == 404
    assert any(r["id"] == "i-A" for r in db.rows("investments"))


async def test_foreign_delete_expense_404s(db, monkeypatch):
    _as_user(monkeypatch, "user-B")
    with pytest.raises(HTTPException) as exc:
        await expenses_router.delete_expense("e-A", _req())
    assert exc.value.status_code == 404
    assert any(r["id"] == "e-A" for r in db.rows("expenses"))


async def test_foreign_delete_product_404s_and_stays_active(db, monkeypatch):
    _as_user(monkeypatch, "user-B")
    with pytest.raises(HTTPException) as exc:
        await products_router.delete_product("p-A", _req())
    assert exc.value.status_code == 404
    # Soft-delete must not have flipped the victim's is_active flag.
    prod = next(r for r in db.rows("products") if r["id"] == "p-A")
    assert prod["is_active"] is True


async def test_owner_delete_still_works(db, monkeypatch):
    _as_user(monkeypatch, "user-A")
    assert (await hours_router.delete_hours("h-A", _req()))["success"] is True
    assert not any(r["id"] == "h-A" for r in db.rows("hours"))
    assert (await investments_router.delete_investment("i-A", _req()))["success"] is True
    await expenses_router.delete_expense("e-A", _req())
    assert not any(r["id"] == "e-A" for r in db.rows("expenses"))
    await products_router.delete_product("p-A", _req())
    prod = next(r for r in db.rows("products") if r["id"] == "p-A")
    assert prod["is_active"] is False

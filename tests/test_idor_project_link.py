"""Cross-tenant regression tests for finding #8 — project_id from the body
not verified against the caller.

Pre-fix: hours / expenses / invoices accepted a project_id straight from
the request body and stored it without checking the project belonged to
the caller, letting an attacker link their own row to a foreign tenant's
project. Post-fix each insert routes the project_id through
`tenant_db.require_owned_id`, which 404s on a foreign / missing id before
any row is written.
"""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from app.routers import hours as hours_router
from app.routers import expenses as expenses_router
from app.routers.expenses import ExpenseCreate
from app.routers import subscription as subscription_router
from app.services import tenant_db
from tests.fake_supabase import FakeSupabase


class _JsonRequest:
    """Minimal stand-in for starlette Request with an async .json()."""
    def __init__(self, body: dict):
        self._body = body

    async def json(self):
        return self._body


@pytest.fixture
def db(monkeypatch):
    """User A owns project proj-A. User B owns nothing."""
    fake = FakeSupabase({
        "projects": [{"id": "proj-A", "user_id": "user-A", "name": "Alice site"}],
        "hours": [],
        "expenses": [],
    })
    for mod in (hours_router, expenses_router, tenant_db):
        monkeypatch.setattr(mod, "supabase", fake)
    # Neutralise the paywall + bank-reconcile side-effects on the expense path.
    monkeypatch.setattr(subscription_router, "require_active_paid", lambda _uid: None)
    monkeypatch.setattr(expenses_router, "schedule_reconcile", lambda _uid: None)
    return fake


# ── hours.add_hours ─────────────────────────────────────────────

async def test_hours_foreign_project_404s_and_inserts_nothing(db, monkeypatch):
    monkeypatch.setattr(hours_router, "get_user_id", lambda _req: "user-B")
    req = _JsonRequest({"hours": 2, "project_id": "proj-A"})
    with pytest.raises(HTTPException) as exc:
        await hours_router.add_hours(req)
    assert exc.value.status_code == 404
    assert db.rows("hours") == []


async def test_hours_own_project_succeeds(db, monkeypatch):
    monkeypatch.setattr(hours_router, "get_user_id", lambda _req: "user-A")
    req = _JsonRequest({"hours": 2, "project_id": "proj-A"})
    result = await hours_router.add_hours(req)
    assert result["success"] is True
    assert db.rows("hours")[0]["project_id"] == "proj-A"


async def test_hours_no_project_still_works(db, monkeypatch):
    monkeypatch.setattr(hours_router, "get_user_id", lambda _req: "user-B")
    req = _JsonRequest({"hours": 1})
    result = await hours_router.add_hours(req)
    assert result["success"] is True


# ── expenses.create_expense ─────────────────────────────────────

async def test_expense_foreign_project_404s_and_inserts_nothing(db, monkeypatch):
    monkeypatch.setattr(expenses_router, "get_user_id", lambda _req: "user-B")
    payload = ExpenseCreate(description="x", amount_ex_btw=10, project_id="proj-A")
    with pytest.raises(HTTPException) as exc:
        await expenses_router.create_expense(payload, SimpleNamespace())
    assert exc.value.status_code == 404
    assert db.rows("expenses") == []


async def test_expense_own_project_succeeds(db, monkeypatch):
    monkeypatch.setattr(expenses_router, "get_user_id", lambda _req: "user-A")
    payload = ExpenseCreate(description="x", amount_ex_btw=10, project_id="proj-A")
    result = await expenses_router.create_expense(payload, SimpleNamespace())
    assert result["expense"]["project_id"] == "proj-A"

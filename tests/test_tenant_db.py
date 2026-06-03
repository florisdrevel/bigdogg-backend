"""Unit tests for the owner-scoped data access helpers.

These tests verify the mechanism in isolation: given a fake DB with rows
from multiple users, every helper must 404 when the caller isn't the
owner — never silently operate on a foreign row.
"""
import pytest
from fastapi import HTTPException

from app.services import tenant_db
from tests.fake_supabase import FakeSupabase


@pytest.fixture
def fake_db(monkeypatch):
    """Two users, three invoices: one owned by A, two by B."""
    fake = FakeSupabase({
        "invoices": [
            {"id": "inv-1", "user_id": "user-A", "status": "sent",  "total": 100},
            {"id": "inv-2", "user_id": "user-B", "status": "sent",  "total": 200},
            {"id": "inv-3", "user_id": "user-B", "status": "draft", "total": 50},
        ],
    })
    monkeypatch.setattr(tenant_db, "supabase", fake)
    return fake


# ── get_owned ───────────────────────────────────────────────
def test_get_owned_returns_row_for_owner(fake_db):
    row = tenant_db.get_owned("invoices", "inv-1", "user-A")
    assert row["id"] == "inv-1"
    assert row["total"] == 100


def test_get_owned_404_when_foreign_user(fake_db):
    """User A asks for User B's invoice → 404."""
    with pytest.raises(HTTPException) as exc:
        tenant_db.get_owned("invoices", "inv-2", "user-A")
    assert exc.value.status_code == 404
    assert exc.value.detail == "not_found"


def test_get_owned_404_when_row_missing(fake_db):
    with pytest.raises(HTTPException) as exc:
        tenant_db.get_owned("invoices", "inv-does-not-exist", "user-A")
    assert exc.value.status_code == 404


def test_get_owned_404_when_user_id_empty(fake_db):
    """Defensive: an empty user_id must not return all rows."""
    with pytest.raises(HTTPException) as exc:
        tenant_db.get_owned("invoices", "inv-1", "")
    assert exc.value.status_code == 404


def test_get_owned_404_when_row_id_empty(fake_db):
    with pytest.raises(HTTPException) as exc:
        tenant_db.get_owned("invoices", "", "user-A")
    assert exc.value.status_code == 404


# ── update_owned ────────────────────────────────────────────
def test_update_owned_applies_patch_for_owner(fake_db):
    out = tenant_db.update_owned(
        "invoices", "inv-1", "user-A", {"status": "paid"},
    )
    assert out["status"] == "paid"
    # The underlying row is also mutated
    assert fake_db.rows("invoices")[0]["status"] == "paid"


def test_update_owned_404_when_foreign_user_no_mutation(fake_db):
    """User A tries to update User B's invoice. Must 404 AND leave the
    victim's row untouched — this is the IDOR regression we care about.
    """
    victim_before = dict(
        next(r for r in fake_db.rows("invoices") if r["id"] == "inv-2")
    )
    with pytest.raises(HTTPException) as exc:
        tenant_db.update_owned(
            "invoices", "inv-2", "user-A", {"status": "paid"},
        )
    assert exc.value.status_code == 404
    victim_after = next(r for r in fake_db.rows("invoices") if r["id"] == "inv-2")
    assert victim_after == victim_before


def test_update_owned_404_when_row_missing(fake_db):
    with pytest.raises(HTTPException) as exc:
        tenant_db.update_owned(
            "invoices", "inv-does-not-exist", "user-A", {"status": "paid"},
        )
    assert exc.value.status_code == 404


def test_update_owned_with_empty_patch_returns_row(fake_db):
    """An empty patch should still verify ownership (and return the row)."""
    row = tenant_db.update_owned("invoices", "inv-1", "user-A", {})
    assert row["id"] == "inv-1"
    # And still 404 across tenants:
    with pytest.raises(HTTPException):
        tenant_db.update_owned("invoices", "inv-2", "user-A", {})


# ── delete_owned ────────────────────────────────────────────
def test_delete_owned_removes_row_for_owner(fake_db):
    tenant_db.delete_owned("invoices", "inv-1", "user-A")
    assert not any(r["id"] == "inv-1" for r in fake_db.rows("invoices"))


def test_delete_owned_404_when_foreign_user_no_deletion(fake_db):
    """The whole point: User A must NOT delete User B's invoice."""
    before = [r["id"] for r in fake_db.rows("invoices")]
    with pytest.raises(HTTPException) as exc:
        tenant_db.delete_owned("invoices", "inv-2", "user-A")
    assert exc.value.status_code == 404
    after = [r["id"] for r in fake_db.rows("invoices")]
    assert before == after  # nothing was removed


def test_delete_owned_404_when_row_missing(fake_db):
    with pytest.raises(HTTPException) as exc:
        tenant_db.delete_owned("invoices", "inv-x", "user-A")
    assert exc.value.status_code == 404


# ── require_owned_id ────────────────────────────────────────
def test_require_owned_id_returns_id_for_owner(fake_db):
    out = tenant_db.require_owned_id("invoices", "inv-1", "user-A")
    assert out == "inv-1"


def test_require_owned_id_404_when_foreign(fake_db):
    with pytest.raises(HTTPException) as exc:
        tenant_db.require_owned_id("invoices", "inv-2", "user-A")
    assert exc.value.status_code == 404

"""Tests for the token-gated accountant portal."""
from datetime import datetime, timezone, timedelta, date
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
    def neq(self, *_a, **_kw):    return self
    def lte(self, *_a, **_kw):    return self
    def gte(self, *_a, **_kw):    return self
    def in_(self, *_a, **_kw):    return self
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


def _active_invite_row(token="tok", user_id="owner-1"):
    return {
        "token":      token,
        "user_id":    user_id,
        "email":      "a@b.c",
        "used":       False,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": "2026-05-01T10:00:00Z",
    }


# ── _resolve_portal_token ──────────────────────────────────────
def test_resolve_token_not_found(monkeypatch):
    _patch_supabase(monkeypatch, {"accountant_invites": []})
    with pytest.raises(HTTPException) as exc:
        acc._resolve_portal_token("does-not-exist")
    assert exc.value.status_code == 404
    assert exc.value.detail == "link_not_found"


def test_resolve_token_revoked(monkeypatch):
    row = _active_invite_row()
    row["used"] = True
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        acc._resolve_portal_token("tok")
    assert exc.value.status_code == 403
    assert exc.value.detail == "link_revoked"


def test_resolve_token_expired(monkeypatch):
    row = _active_invite_row()
    row["expires_at"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        acc._resolve_portal_token("tok")
    assert exc.value.status_code == 410
    assert exc.value.detail == "link_expired"


def test_resolve_token_active(monkeypatch):
    _patch_supabase(monkeypatch, {"accountant_invites": [_active_invite_row()]})
    result = acc._resolve_portal_token("tok")
    assert result["user_id"] == "owner-1"


# ── portal_overview math (with correct column names) ─────────
async def test_portal_overview_yearly_totals(monkeypatch):
    invoices = [
        {"subtotal_ex_btw": 1000, "total_incl_btw": 1210, "btw_amount": 210, "status": "paid", "invoice_date": "2026-03-01"},
        {"subtotal_ex_btw": 500,  "total_incl_btw": 605,  "btw_amount": 105, "status": "sent", "invoice_date": "2026-04-01"},
    ]
    expenses = [
        {"amount_ex_btw": 200, "btw_amount": 42, "category": "office",   "expense_date": "2026-03-15"},
        {"amount_ex_btw": 80,  "btw_amount": 17, "category": "software", "expense_date": "2026-04-15"},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "invoices":           invoices,
        "expenses":           expenses,
    })

    result = await acc.portal_overview("tok", year=2026)
    assert result["year"] == 2026
    assert result["revenue_ex"]    == 1500.0
    assert result["btw_collected"] == 315.0
    assert result["expense_ex"]    == 280.0
    assert result["btw_paid"]      == 59.0
    assert result["btw_payable"]   == round(315.0 - 59.0, 2)
    assert result["profit_ex"]     == 1220.0
    assert result["paid_count"]    == 1
    # Quarter breakdown — Q1 has one invoice + one expense, Q2 has one each.
    quarters = {q["quarter"]: q for q in result["quarters"]}
    assert quarters[1]["revenue_ex"]    == 1000.0
    assert quarters[1]["btw_collected"] == 210.0
    assert quarters[1]["btw_paid"]      == 42.0
    assert quarters[2]["revenue_ex"]    == 500.0
    assert quarters[2]["btw_paid"]      == 17.0
    # Categories sorted by amount_ex desc
    assert result["categories"][0]["category"] == "office"
    assert result["categories"][0]["amount_ex"] == 200.0
    # KOR ratio = 1500 / 20000 = 0.075
    assert result["kor_ratio"] == 0.075


async def test_portal_overview_revoked(monkeypatch):
    row = _active_invite_row()
    row["used"] = True
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        await acc.portal_overview("tok")
    assert exc.value.status_code == 403


async def test_portal_invoices_includes_line_items(monkeypatch):
    invoices = [
        {"id": "inv1", "invoice_number": "2026-000001",
         "client_name": "ACME", "client_company": "ACME BV",
         "subtotal_ex_btw": 100, "total_incl_btw": 121, "btw_amount": 21,
         "invoice_date": "2026-03-01", "due_date": "2026-03-31", "status": "paid"},
    ]
    invoice_lines = [
        {"invoice_id": "inv1", "description": "Hours",
         "quantity": 4, "unit_price_ex_btw": 25, "btw_rate": 21,
         "line_total_ex_btw": 100, "unit": "hour"},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "invoices":           invoices,
        "invoice_lines":      invoice_lines,
    })
    result = await acc.portal_invoices("tok", year=2026)
    assert len(result["invoices"]) == 1
    assert result["invoices"][0]["lines"][0]["description"] == "Hours"


async def test_portal_invoices_expired(monkeypatch):
    row = _active_invite_row()
    row["expires_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    _patch_supabase(monkeypatch, {"accountant_invites": [row]})
    with pytest.raises(HTTPException) as exc:
        await acc.portal_invoices("tok")
    assert exc.value.status_code == 410


async def test_portal_expenses_amount_incl_synthesized(monkeypatch):
    expenses = [
        {"id": "e1", "description": "Coffee", "amount_ex_btw": 10,
         "btw_amount": 2.1, "btw_rate": 21, "category": "food",
         "expense_date": "2026-03-15", "receipt_url": None,
         "payment_method": "card"},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "expenses":           expenses,
    })
    result = await acc.portal_expenses("tok", year=2026)
    assert result["expenses"][0]["amount_incl_btw"] == 12.1


async def test_portal_investments_depreciation_for_year(monkeypatch):
    # €1000 over 5 years = €200/yr. Purchased 2024.
    investments = [
        {"id": "i1", "description": "Laptop", "purchase_date": "2024-06-15",
         "amount": 1000.0, "depreciation_years": 5, "category": "general",
         "receipt_url": None},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "investments":        investments,
    })
    # In 2026 (year 3 of 5), this year's depreciation = 200, cumulative = 600.
    result = await acc.portal_investments("tok", year=2026)
    item = result["investments"][0]
    assert item["annual_depreciation"]     == 200.0
    assert item["this_year_depreciation"]  == 200.0
    assert item["cumulative_depreciation"] == 600.0
    assert item["book_value"]              == 400.0
    assert result["total_this_year"]       == 200.0


async def test_portal_hours_per_project(monkeypatch):
    hours = [
        {"id": "h1", "hours": 4,  "date": "2026-03-01", "description": "client A", "project_id": "p1"},
        {"id": "h2", "hours": 2,  "date": "2026-03-02", "description": "client A", "project_id": "p1"},
        {"id": "h3", "hours": 3,  "date": "2026-03-03", "description": "admin",    "project_id": None},
    ]
    projects = [{"id": "p1", "name": "Project Alpha"}]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "hours":              hours,
        "projects":           projects,
    })
    result = await acc.portal_hours("tok", year=2026)
    assert result["total_hours"] == 9.0
    # Highest first
    assert result["project_summary"][0]["project_name"] == "Project Alpha"
    assert result["project_summary"][0]["hours"] == 6.0


async def test_portal_years_distinct(monkeypatch):
    invoices = [
        {"invoice_date": "2024-03-01"},
        {"invoice_date": "2025-06-01"},
    ]
    expenses = [{"expense_date": "2025-12-31"}]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "invoices":           invoices,
        "expenses":           expenses,
    })
    result = await acc.portal_years("tok")
    # Always includes the current year + distinct years from data
    assert 2024 in result["years"]
    assert 2025 in result["years"]
    assert datetime.now().year in result["years"]
    assert result["years"] == sorted(result["years"], reverse=True)


async def test_portal_btw_breakdown_per_rate(monkeypatch):
    invoices = [
        {"id": "inv1", "invoice_date": "2026-02-01", "status": "paid"},
        {"id": "inv2", "invoice_date": "2026-05-01", "status": "sent"},
    ]
    lines = [
        {"invoice_id": "inv1", "quantity": 1, "unit_price_ex_btw": 100,
         "btw_rate": 21, "line_total_ex_btw": 100},
        {"invoice_id": "inv1", "quantity": 1, "unit_price_ex_btw": 50,
         "btw_rate": 9,  "line_total_ex_btw": 50},
        {"invoice_id": "inv2", "quantity": 2, "unit_price_ex_btw": 200,
         "btw_rate": 21, "line_total_ex_btw": 400},
    ]
    expenses = [
        {"amount_ex_btw": 80, "btw_amount": 16.8, "expense_date": "2026-02-15"},
        {"amount_ex_btw": 50, "btw_amount": 4.5,  "expense_date": "2026-05-15"},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "invoices":           invoices,
        "invoice_lines":      lines,
        "expenses":           expenses,
    })
    result = await acc.portal_btw_breakdown("tok", year=2026)
    q1 = result["quarters"]["1"]
    q2 = result["quarters"]["2"]
    assert q1["rate_21"]["ex"] == 100.0
    assert q1["rate_21"]["btw"] == 21.0
    assert q1["rate_9"]["ex"] == 50.0
    assert q1["rate_9"]["btw"] == 4.5
    assert q1["voorbelasting"] == 16.8
    assert q2["rate_21"]["ex"] == 400.0
    assert q2["voorbelasting"] == 4.5
    assert result["year"]["btw_owed"] == round(21.0 + 4.5 + 84.0, 2)


async def test_portal_aging_buckets(monkeypatch):
    today = date.today()
    inv = [
        # 10 days overdue → 0-30
        {"id": "a", "invoice_number": "1", "client_name": "A", "client_company": "",
         "invoice_date": "2026-01-01",
         "due_date": (today - timedelta(days=10)).isoformat(),
         "total_incl_btw": 121.0, "status": "sent"},
        # 45 days overdue → 31-60
        {"id": "b", "invoice_number": "2", "client_name": "B", "client_company": "",
         "invoice_date": "2026-01-01",
         "due_date": (today - timedelta(days=45)).isoformat(),
         "total_incl_btw": 242.0, "status": "overdue"},
        # 100 days overdue → 90+
        {"id": "c", "invoice_number": "3", "client_name": "C", "client_company": "",
         "invoice_date": "2026-01-01",
         "due_date": (today - timedelta(days=100)).isoformat(),
         "total_incl_btw": 50.0, "status": "sent"},
        # not yet due → excluded
        {"id": "d", "invoice_number": "4", "client_name": "D", "client_company": "",
         "invoice_date": "2026-04-01",
         "due_date": (today + timedelta(days=5)).isoformat(),
         "total_incl_btw": 99.0, "status": "sent"},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "invoices":           inv,
    })
    result = await acc.portal_aging("tok")
    assert result["buckets"]["0-30"]["count"] == 1
    assert result["buckets"]["0-30"]["total"] == 121.0
    assert result["buckets"]["31-60"]["count"] == 1
    assert result["buckets"]["31-60"]["total"] == 242.0
    assert result["buckets"]["90+"]["count"] == 1
    assert result["buckets"]["90+"]["total"] == 50.0
    assert result["grand_count"] == 3  # the not-yet-due one is excluded
    assert result["grand_total"] == round(121.0 + 242.0 + 50.0, 2)


def test_depreciation_schedule_full_period():
    # €1000 over 5 years starting 2024
    schedule = acc._depreciation_schedule(1000.0, "2024-06-15", 5)
    assert len(schedule) == 5
    assert schedule[0]["year"] == 2024
    assert schedule[-1]["year"] == 2028
    assert schedule[0]["amount"] == 200.0
    # Cumulative must add up to the original amount on the last row
    assert schedule[-1]["cumulative"] == 1000.0
    assert schedule[-1]["book_value"] == 0.0


async def test_portal_export_csv_contains_invoice_and_expense_rows(monkeypatch):
    invoices = [
        {"id": "inv1", "invoice_number": "2026-000001",
         "invoice_date": "2026-03-01", "status": "paid",
         "client_name": "ACME", "client_company": "ACME BV"},
    ]
    lines = [
        {"invoice_id": "inv1", "description": "Hours",
         "quantity": 1, "unit_price_ex_btw": 100,
         "btw_rate": 21, "line_total_ex_btw": 100},
    ]
    expenses = [
        {"expense_date": "2026-03-15", "description": "Office supplies",
         "amount_ex_btw": 50, "btw_amount": 10.5, "btw_rate": 21,
         "category": "office"},
    ]
    _patch_supabase(monkeypatch, {
        "accountant_invites": [_active_invite_row()],
        "invoices":           invoices,
        "invoice_lines":      lines,
        "expenses":           expenses,
    })
    response = await acc.portal_export_csv("tok", year=2026)
    body = response.body.decode("utf-8")
    assert "Verkoop;2026-03-01;2026-000001" in body
    assert "Inkoop;2026-03-15" in body
    # Default ledger mapping
    assert ";8000" in body          # 21% revenue
    assert ";4500" in body          # office expense


async def test_portal_meta_owner_name_fallback(monkeypatch):
    row = _active_invite_row()
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

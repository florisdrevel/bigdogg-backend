from fastapi import APIRouter, HTTPException, Request
from datetime import date
from app.database import supabase

router = APIRouter()


def get_user_id(request: Request) -> str:
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_quarter_dates(year: int, quarter: int):
    """Return (start_date, end_date) for a given quarter."""
    starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    return date(year, *starts[quarter]), date(year, *ends[quarter])


def compute_financials(user_id: str, start_date: date, end_date: date) -> dict:
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    # Fetch invoices in the date range
    invoices_resp = (
        supabase.table("invoices")
        .select("id, status, amount_ex_btw, btw_amount, total")
        .eq("user_id", user_id)
        .gte("invoice_date", start_str)
        .lte("invoice_date", end_str)
        .execute()
    )
    invoices = invoices_resp.data or []

    revenue_ex_btw = sum(float(inv.get("amount_ex_btw") or 0) for inv in invoices)
    revenue_btw = sum(float(inv.get("btw_amount") or 0) for inv in invoices)

    paid_revenue = sum(
        float(inv.get("total") or 0)
        for inv in invoices
        if inv.get("status") == "paid"
    )
    outstanding = sum(
        float(inv.get("total") or 0)
        for inv in invoices
        if inv.get("status") != "paid"
    )

    # Fetch expenses in the date range
    expenses_resp = (
        supabase.table("expenses")
        .select("amount_ex_btw, btw_rate")
        .eq("user_id", user_id)
        .gte("expense_date", start_str)
        .lte("expense_date", end_str)
        .execute()
    )
    expenses = expenses_resp.data or []

    expenses_ex_btw = sum(float(e.get("amount_ex_btw") or 0) for e in expenses)
    expenses_btw = sum(
        float(e.get("amount_ex_btw") or 0) * float(e.get("btw_rate") or 0) / 100
        for e in expenses
    )

    return {
        "revenue_ex_btw": round(revenue_ex_btw, 2),
        "revenue_btw": round(revenue_btw, 2),
        "revenue_total": round(revenue_ex_btw + revenue_btw, 2),
        "paid_revenue": round(paid_revenue, 2),
        "outstanding": round(outstanding, 2),
        "expenses_ex_btw": round(expenses_ex_btw, 2),
        "expenses_btw": round(expenses_btw, 2),
        "expenses_total": round(expenses_ex_btw + expenses_btw, 2),
        "btw_to_pay": round(revenue_btw - expenses_btw, 2),
    }


@router.get("/quarterly")
async def get_quarterly_overview(request: Request):
    user_id = get_user_id(request)
    today = date.today()
    quarter = (today.month - 1) // 3 + 1
    year = today.year
    start_date, end_date = get_quarter_dates(year, quarter)

    financials = compute_financials(user_id, start_date, end_date)

    return {
        "period": f"Q{quarter} {year}",
        "start_date": start_date.strftime("%d %b %Y"),
        "end_date": end_date.strftime("%d %b %Y"),
        **financials,
    }


@router.get("/annual")
async def get_annual_overview(request: Request, year: int = None):
    user_id = get_user_id(request)
    if year is None:
        year = date.today().year

    quarters_data = []
    total_revenue_ex_btw = 0.0
    total_expenses_ex_btw = 0.0
    total_btw_to_pay = 0.0

    for q in range(1, 5):
        start_date, end_date = get_quarter_dates(year, q)
        financials = compute_financials(user_id, start_date, end_date)
        quarters_data.append({"quarter": q, **financials})
        total_revenue_ex_btw += financials["revenue_ex_btw"]
        total_expenses_ex_btw += financials["expenses_ex_btw"]
        total_btw_to_pay += financials["btw_to_pay"]

    return {
        "year": year,
        "quarters": quarters_data,
        "total_revenue_ex_btw": round(total_revenue_ex_btw, 2),
        "total_expenses_ex_btw": round(total_expenses_ex_btw, 2),
        "net_profit_indicative": round(total_revenue_ex_btw - total_expenses_ex_btw, 2),
        "total_btw_to_pay": round(total_btw_to_pay, 2),
    }

from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from datetime import date

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
    quarters = {
        1: ("01-01", "03-31"),
        2: ("04-01", "06-30"),
        3: ("07-01", "09-30"),
        4: ("10-01", "12-31"),
    }
    start, end = quarters[quarter]
    return f"{year}-{start}", f"{year}-{end}"


@router.get("/quarterly")
async def get_quarterly_overview(request: Request, year: int = None, quarter: int = None):
    user_id = get_user_id(request)

    today = date.today()
    if year is None:
        year = today.year
    if quarter is None:
        quarter = (today.month - 1) // 3 + 1

    start_date, end_date = get_quarter_dates(year, quarter)

    try:
        invoices = supabase.table("invoices")\
            .select("subtotal_ex_btw, btw_amount, total_incl_btw, status")\
            .eq("user_id", user_id)\
            .gte("invoice_date", start_date)\
            .lte("invoice_date", end_date)\
            .neq("status", "draft")\
            .execute()

        expenses = supabase.table("expenses")\
            .select("amount_ex_btw, btw_amount")\
            .eq("user_id", user_id)\
            .gte("expense_date", start_date)\
            .lte("expense_date", end_date)\
            .execute()

        revenue_ex_btw = sum(i["subtotal_ex_btw"] for i in invoices.data)
        revenue_btw = sum(i["btw_amount"] for i in invoices.data)
        paid_revenue = sum(i["total_incl_btw"] for i in invoices.data if i["status"] == "paid")
        outstanding = sum(i["total_incl_btw"] for i in invoices.data if i["status"] in ["sent", "overdue"])

        expenses_ex_btw = sum(e["amount_ex_btw"] for e in expenses.data)
        expenses_btw = sum(e["btw_amount"] for e in expenses.data)

        btw_to_pay = round(revenue_btw - expenses_btw, 2)

        return {
            "year": year,
            "quarter": quarter,
            "period": f"Q{quarter} {year}",
            "start_date": start_date,
            "end_date": end_date,
            "revenue_ex_btw": round(revenue_ex_btw, 2),
            "revenue_btw": round(revenue_btw, 2),
            "revenue_total": round(revenue_ex_btw + revenue_btw, 2),
            "paid_revenue": round(paid_revenue, 2),
            "outstanding": round(outstanding, 2),
            "expenses_ex_btw": round(expenses_ex_btw, 2),
            "expenses_btw": round(expenses_btw, 2),
            "expenses_total": round(expenses_ex_btw + expenses_btw, 2),
            "btw_to_pay": btw_to_pay,
            "invoice_count": len(invoices.data),
            "expense_count": len(expenses.data),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/annual")
async def get_annual_overview(request: Request, year: int = None):
    user_id = get_user_id(request)

    today = date.today()
    if year is None:
        year = today.year - 1 if today.month < 3 else today.year

    quarters = []
    for q in range(1, 5):
        start_date, end_date = get_quarter_dates(year, q)

        invoices = supabase.table("invoices")\
            .select("subtotal_ex_btw, btw_amount, total_incl_btw, status")\
            .eq("user_id", user_id)\
            .gte("invoice_date", start_date)\
            .lte("invoice_date", end_date)\
            .neq("status", "draft")\
            .execute()

        expenses = supabase.table("expenses")\
            .select("amount_ex_btw, btw_amount")\
            .eq("user_id", user_id)\
            .gte("expense_date", start_date)\
            .lte("expense_date", end_date)\
            .execute()

        revenue_ex_btw = sum(i["subtotal_ex_btw"] for i in invoices.data)
        revenue_btw = sum(i["btw_amount"] for i in invoices.data)
        expenses_ex_btw = sum(e["amount_ex_btw"] for e in expenses.data)
        expenses_btw = sum(e["btw_amount"] for e in expenses.data)

        quarters.append({
            "quarter": q,
            "revenue_ex_btw": round(revenue_ex_btw, 2),
            "revenue_btw": round(revenue_btw, 2),
            "expenses_ex_btw": round(expenses_ex_btw, 2),
            "expenses_btw": round(expenses_btw, 2),
            "btw_to_pay": round(revenue_btw - expenses_btw, 2),
        })

    total_revenue = sum(q["revenue_ex_btw"] for q in quarters)
    total_expenses = sum(q["expenses_ex_btw"] for q in quarters)
    total_btw = sum(q["btw_to_pay"] for q in quarters)

    return {
        "year": year,
        "quarters": quarters,
        "total_revenue_ex_btw": round(total_revenue, 2),
        "total_expenses_ex_btw": round(total_expenses, 2),
        "total_btw_to_pay": round(total_btw, 2),
        "net_profit_indicative": round(total_revenue - total_expenses, 2),
    }
    
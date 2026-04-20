from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from datetime import date

router = APIRouter()

HOURS_PER_DAY = 9.0


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


def _calc_invoice_hours(user_id: str, year_start: str, year_end: str) -> tuple:
    try:
        inv_result = supabase.table("invoices")\
            .select("id, invoice_date, invoice_number, project_id, status")\
            .eq("user_id", user_id)\
            .neq("status", "draft")\
            .gte("invoice_date", year_start)\
            .lte("invoice_date", year_end)\
            .execute()
        invoices = inv_result.data or []
        if not invoices:
            return 0.0, []

        inv_ids = [i["id"] for i in invoices]
        inv_map = {i["id"]: i for i in invoices}

        lines_result = supabase.table("invoice_lines")\
            .select("invoice_id, description, quantity, unit")\
            .in_("invoice_id", inv_ids)\
            .execute()
        lines = lines_result.data or []

        total = 0.0
        breakdown = []
        for line in lines:
            unit = (line.get("unit") or "fixed").lower()
            qty = float(line.get("quantity", 0) or 0)
            inv = inv_map.get(line["invoice_id"], {})
            hrs = 0.0
            if unit == "day":
                hrs = qty * HOURS_PER_DAY
            elif unit == "hour":
                hrs = qty
            if hrs > 0:
                total += hrs
                breakdown.append({
                    "source": "invoice",
                    "invoice_number": inv.get("invoice_number", ""),
                    "invoice_id": line["invoice_id"],
                    "project_id": inv.get("project_id"),
                    "description": line.get("description", ""),
                    "quantity": qty,
                    "unit": unit,
                    "hours": hrs,
                    "date": inv.get("invoice_date", ""),
                })
        return round(total, 2), breakdown
    except Exception as e:
        print(f"Error calculating invoice hours: {e}")
        return 0.0, []


@router.get("/")
async def get_hours(request: Request, year: int = None, quarter: int = None):
    user_id = get_user_id(request)
    today = date.today()
    if year is None:
        year = today.year
    try:
        query = supabase.table("hours").select("*").eq("user_id", user_id)
        if quarter is not None:
            quarters = {1: ("01-01", "03-31"), 2: ("04-01", "06-30"),
                        3: ("07-01", "09-30"), 4: ("10-01", "12-31")}
            start, end = quarters[quarter]
            query = query.gte("date", f"{year}-{start}").lte("date", f"{year}-{end}")
        else:
            query = query.gte("date", f"{year}-01-01").lte("date", f"{year}-12-31")
        result = query.order("date", desc=True).execute()
        entries = result.data or []
        manual_year = sum(float(e["hours"]) for e in entries)

        inv_year_hrs, inv_breakdown = _calc_invoice_hours(user_id, f"{year}-01-01", f"{year}-12-31")
        total_year = manual_year + inv_year_hrs

        current_quarter = (today.month - 1) // 3 + 1
        q_ends = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
        q_starts = {1: "01", 2: "04", 3: "07", 4: "10"}
        q_start_str = f"{today.year}-{q_starts[current_quarter]}-01"
        q_end_str = f"{today.year}-{q_ends[current_quarter]}"

        q_result = supabase.table("hours").select("hours").eq("user_id", user_id)\
            .gte("date", q_start_str).lte("date", q_end_str).execute()
        manual_quarter = sum(float(e["hours"]) for e in (q_result.data or []))
        inv_q_hrs, _ = _calc_invoice_hours(user_id, q_start_str, q_end_str)
        total_quarter = manual_quarter + inv_q_hrs

        return {
            "entries": entries,
            "invoice_hours_breakdown": inv_breakdown[:20],
            "total_year": round(total_year, 2),
            "total_quarter": round(total_quarter, 2),
            "manual_year": round(manual_year, 2),
            "invoice_year": round(inv_year_hrs, 2),
            "year": year,
            "urencriterium": 1225,
            "urencriterium_progress": round(min(total_year / 1225 * 100, 100), 1),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def add_hours(request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
        hours_val = float(body.get("hours", 0))
        if hours_val <= 0:
            raise HTTPException(status_code=400, detail="Hours must be greater than 0")
        data = {
            "user_id": user_id,
            "hours": hours_val,
            "date": body.get("date", date.today().isoformat()),
            "description": body.get("description", ""),
        }
        if body.get("project_id"):
            data["project_id"] = body["project_id"]
        result = supabase.table("hours").insert(data).execute()
        return {"success": True, "entry": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}")
async def delete_hours(entry_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("hours").delete().eq("id", entry_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

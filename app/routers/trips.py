"""
Kilometerregistratie — per-trip business-mileage log for the €0,23/km
zakelijke-kilometer aftrek.

The Belastingdienst requires per-trip substantiation (datum, vertrekadres,
bestemming, doel, zakelijk/privé, km), so this is a per-trip LOG, not a
running counter. Mirrors the urenregistratie (hours) feature exactly:
app-level user_id scoping on every query, delete_owned for safe deletes,
optional project_id with ownership validation.
"""
from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.services.tenant_db import require_owned_id, delete_owned
from app.constants.tax_rates import km_rate_for_year
from datetime import date

router = APIRouter()

_QUARTERS = {1: ("01-01", "03-31"), 2: ("04-01", "06-30"),
             3: ("07-01", "09-30"), 4: ("10-01", "12-31")}


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


def year_km_total(user_id: str, year: int) -> dict:
    """
    Total deductible business kilometres for a tax year and the resulting
    €-deduction. Resilient by design: if the trip_registrations table does not
    exist yet (SQL not run), returns zeros so the annual report and tax-reserve
    estimate keep working. Only is_business rows count toward the aftrek.
    """
    rate = km_rate_for_year(year)
    try:
        result = supabase.table("trip_registrations")\
            .select("km, is_business")\
            .eq("user_id", user_id)\
            .gte("trip_date", f"{year}-01-01")\
            .lte("trip_date", f"{year}-12-31")\
            .execute()
        rows = result.data or []
    except Exception:
        rows = []
    business_km = round(sum(float(r.get("km") or 0) for r in rows if r.get("is_business")), 1)
    deduction = round(business_km * rate, 2)
    return {
        "total_business_km": business_km,
        "km_rate": rate,
        "km_deduction_eur": deduction,
    }


@router.get("/")
async def get_trips(request: Request, year: int = None, quarter: int = None):
    user_id = get_user_id(request)
    today = date.today()
    if year is None:
        year = today.year
    try:
        query = supabase.table("trip_registrations").select("*").eq("user_id", user_id)
        if quarter is not None:
            start, end = _QUARTERS[quarter]
            query = query.gte("trip_date", f"{year}-{start}").lte("trip_date", f"{year}-{end}")
        else:
            query = query.gte("trip_date", f"{year}-01-01").lte("trip_date", f"{year}-12-31")
        result = query.order("trip_date", desc=True).execute()
        entries = result.data or []

        business_km = round(sum(float(e.get("km") or 0) for e in entries if e.get("is_business")), 1)
        private_km = round(sum(float(e.get("km") or 0) for e in entries if not e.get("is_business")), 1)
        rate = km_rate_for_year(year)

        # Current-quarter business km (mirrors the hours card's quarter total).
        current_quarter = (today.month - 1) // 3 + 1
        q_start, q_end = _QUARTERS[current_quarter]
        q_result = supabase.table("trip_registrations").select("km, is_business")\
            .eq("user_id", user_id)\
            .gte("trip_date", f"{today.year}-{q_start}")\
            .lte("trip_date", f"{today.year}-{q_end}").execute()
        q_business_km = round(sum(float(e.get("km") or 0) for e in (q_result.data or []) if e.get("is_business")), 1)

        return {
            "entries": entries,
            "total_business_km": business_km,
            "total_private_km": private_km,
            "quarter_business_km": q_business_km,
            "km_rate": rate,
            "km_deduction_eur": round(business_km * rate, 2),
            "year": year,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def add_trip(request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
        km_val = float(body.get("km", 0))
        if km_val <= 0:
            raise HTTPException(status_code=400, detail="Km must be greater than 0")
        from_address = (body.get("from_address") or "").strip()
        to_address = (body.get("to_address") or "").strip()
        purpose = (body.get("purpose") or "").strip()
        if not from_address or not to_address or not purpose:
            raise HTTPException(status_code=400, detail="from_address, to_address and purpose are required")
        data = {
            "user_id": user_id,
            "trip_date": body.get("trip_date", date.today().isoformat()),
            "from_address": from_address,
            "to_address": to_address,
            "purpose": purpose,
            "is_business": bool(body.get("is_business", True)),
            "km": km_val,
        }
        if body.get("project_id"):
            # Mirror hours: verify the project belongs to the caller before linking.
            require_owned_id("projects", body["project_id"], user_id)
            data["project_id"] = body["project_id"]
        result = supabase.table("trip_registrations").insert(data).execute()
        return {"success": True, "entry": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}")
async def delete_trip(entry_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        delete_owned("trip_registrations", entry_id, user_id)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/km-total")
async def get_km_total(request: Request, year: int = None):
    """Per-tax-year deductible business-km total (used by the annual overview)."""
    user_id = get_user_id(request)
    if year is None:
        year = date.today().year
    totals = year_km_total(user_id, year)
    return {"year": year, **totals}

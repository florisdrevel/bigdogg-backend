from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from datetime import date, datetime

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

        total_year = sum(float(e["hours"]) for e in entries)

        current_quarter = (today.month - 1) // 3 + 1
        q_months = {1: [1,2,3], 2: [4,5,6], 3: [7,8,9], 4: [10,11,12]}
        q_start = f"{today.year}-{str(q_months[current_quarter][0]).zfill(2)}-01"
        q_end_map = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
        q_end = f"{today.year}-{q_end_map[current_quarter]}"

        q_result = supabase.table("hours").select("hours")\
            .eq("user_id", user_id)\
            .gte("date", q_start)\
            .lte("date", q_end)\
            .execute()
        total_quarter = sum(float(e["hours"]) for e in (q_result.data or []))

        return {
            "entries": entries,
            "total_year": round(total_year, 2),
            "total_quarter": round(total_quarter, 2),
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
        entry_date = body.get("date", date.today().isoformat())
        description = body.get("description", "")
        project_id = body.get("project_id")

        data = {
            "user_id": user_id,
            "hours": hours_val,
            "date": entry_date,
            "description": description,
        }
        if project_id:
            data["project_id"] = project_id

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
        supabase.table("hours").delete()\
            .eq("id", entry_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
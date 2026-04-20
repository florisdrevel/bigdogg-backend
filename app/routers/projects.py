import re
from fastapi import APIRouter, HTTPException, Request
from app.database import supabase

router = APIRouter()

HOURS_PER_DAY = 9.0
DAY_KEYWORDS = ["dag", "day", "days", "dagen", "dagdeel"]
HOUR_KEYWORDS = ["uur", "hour", "hours", "uren", "hr", "hrs"]
DAY_KEYWORDS = ['dag', 'day', 'days', 'dagen', 'dagdeel']
HOUR_KEYWORDS = ['uur', 'hour', 'hours', 'uren', 'hr', 'hrs']


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


def _is_day_unit(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in DAY_KEYWORDS)


def _is_hour_unit(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in HOUR_KEYWORDS)


def _calc_invoice_hours_for_project(project_id: str, user_id: str) -> float:
    """Calculate hours derived from invoice lines for a specific project."""
    try:
        inv_result = supabase.table("invoices")\
            .select("id")\
            .eq("user_id", user_id)\
            .eq("project_id", project_id)\
            .neq("status", "draft")\
            .execute()
        invoices = inv_result.data or []
        if not invoices:
            return 0.0

        inv_ids = [i["id"] for i in invoices]
        lines_result = supabase.table("invoice_lines")\
            .select("description, quantity")\
            .in_("invoice_id", inv_ids)\
            .execute()
        lines = lines_result.data or []

        total = 0.0
        for line in lines:
            desc = line.get("description", "") or ""
            qty = float(line.get("quantity", 0) or 0)
            if _is_day_unit(desc):
                total += qty * HOURS_PER_DAY
            elif _is_hour_unit(desc):
                total += qty
        return round(total, 2)
    except Exception as e:
        print(f"Error calculating invoice hours for project {project_id}: {e}")
        return 0.0


@router.get("/")
async def get_projects(request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("projects").select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        projects = result.data or []

        for proj in projects:
            pid = proj["id"]

            inv = supabase.table("invoices")\
                .select("subtotal_ex_btw, status")\
                .eq("user_id", user_id)\
                .eq("project_id", pid)\
                .neq("status", "draft")\
                .execute()
            proj["invoice_count"] = len(inv.data or [])
            proj["total_revenue"] = round(sum(float(i["subtotal_ex_btw"] or 0) for i in (inv.data or [])), 2)

            exp = supabase.table("expenses")\
                .select("amount_ex_btw")\
                .eq("user_id", user_id)\
                .eq("project_id", pid)\
                .execute()
            proj["expense_count"] = len(exp.data or [])
            proj["total_expenses"] = round(sum(float(e["amount_ex_btw"] or 0) for e in (exp.data or [])), 2)
            proj["profit"] = round(proj["total_revenue"] - proj["total_expenses"], 2)

            # Manual hours
            hrs = supabase.table("hours")\
                .select("hours")\
                .eq("user_id", user_id)\
                .eq("project_id", pid)\
                .execute()
            manual_hours = round(sum(float(h["hours"]) for h in (hrs.data or [])), 2)

            # Invoice-derived hours
            invoice_hours = _calc_invoice_hours_for_project(pid, user_id)

            proj["total_hours"] = round(manual_hours + invoice_hours, 2)
            proj["manual_hours"] = manual_hours
            proj["invoice_hours"] = invoice_hours

        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_project(request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
        name = body.get("name", "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Project name is required")
        result = supabase.table("projects").insert({
            "user_id": user_id,
            "name": name,
            "description": body.get("description", ""),
            "status": body.get("status", "active"),
            "color": body.get("color", "#1B3A4B"),
        }).execute()
        return {"success": True, "project": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{project_id}")
async def update_project(project_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
        update = {k: v for k, v in body.items() if k in ["name", "description", "status", "color"]}
        if not update:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        supabase.table("projects").update(update)\
            .eq("id", project_id).eq("user_id", user_id).execute()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("invoices").update({"project_id": None})\
            .eq("project_id", project_id).eq("user_id", user_id).execute()
        supabase.table("expenses").update({"project_id": None})\
            .eq("project_id", project_id).eq("user_id", user_id).execute()
        supabase.table("projects").delete()\
            .eq("id", project_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
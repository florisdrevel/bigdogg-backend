from fastapi import APIRouter, HTTPException, Request
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


@router.get("/")
async def get_projects(request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("projects").select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        projects = result.data or []

        # Add totals for each project
        for proj in projects:
            pid = proj["id"]

            inv_result = supabase.table("invoices")\
                .select("total_incl_btw, subtotal_ex_btw, status")\
                .eq("user_id", user_id)\
                .eq("project_id", pid)\
                .neq("status", "draft")\
                .execute()
            invoices = inv_result.data or []
            proj["invoice_count"] = len(invoices)
            proj["total_revenue"] = round(sum(float(i["subtotal_ex_btw"] or 0) for i in invoices), 2)

            exp_result = supabase.table("expenses")\
                .select("amount_ex_btw")\
                .eq("user_id", user_id)\
                .eq("project_id", pid)\
                .execute()
            expenses = exp_result.data or []
            proj["expense_count"] = len(expenses)
            proj["total_expenses"] = round(sum(float(e["amount_ex_btw"] or 0) for e in expenses), 2)
            proj["profit"] = round(proj["total_revenue"] - proj["total_expenses"], 2)

            hours_result = supabase.table("hours")\
                .select("hours")\
                .eq("user_id", user_id)\
                .eq("project_id", pid)\
                .execute()
            proj["total_hours"] = round(sum(float(h["hours"]) for h in (hours_result.data or [])), 2)

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

        data = {
            "user_id": user_id,
            "name": name,
            "description": body.get("description", ""),
            "status": body.get("status", "active"),
            "color": body.get("color", "#1B3A4B"),
        }
        result = supabase.table("projects").insert(data).execute()
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
        allowed = ["name", "description", "status", "color"]
        update = {k: v for k, v in body.items() if k in allowed}
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
        # Unlink invoices and expenses before deleting
        supabase.table("invoices").update({"project_id": None})\
            .eq("project_id", project_id).eq("user_id", user_id).execute()
        supabase.table("expenses").update({"project_id": None})\
            .eq("project_id", project_id).eq("user_id", user_id).execute()
        supabase.table("projects").delete()\
            .eq("id", project_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.routers.banking import schedule_reconcile
from app.services.tenant_db import delete_owned
from datetime import date

router = APIRouter()
DEPRECIATION_THRESHOLD = 450.0

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

def calculate_depreciation(amount: float, purchase_date: str, years: int = 5):
    annual = round(amount / years, 2)
    purchase_year = int(purchase_date[:4])
    return [{"year": purchase_year + i, "amount": annual, "cumulative": round(annual * (i + 1), 2), "remaining": round(amount - annual * (i + 1), 2)} for i in range(years)]

@router.get("/")
async def get_investments(request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("investments").select("*").eq("user_id", user_id).order("purchase_date", desc=True).execute()
        investments = result.data or []
        current_year = date.today().year
        for inv in investments:
            inv["depreciation_schedule"] = calculate_depreciation(float(inv["amount"]), inv["purchase_date"], inv.get("depreciation_years", 5))
            inv["current_year_depreciation"] = next((s["amount"] for s in inv["depreciation_schedule"] if s["year"] == current_year), 0)
        return {"investments": investments}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/annual/{year}")
async def get_annual_depreciation(year: int, request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("investments").select("*").eq("user_id", user_id).execute()
        total = 0.0
        items = []
        for inv in (result.data or []):
            schedule = calculate_depreciation(float(inv["amount"]), inv["purchase_date"], inv.get("depreciation_years", 5))
            dep = next((s["amount"] for s in schedule if s["year"] == year), 0)
            if dep > 0:
                total += dep
                items.append({"description": inv["description"], "amount": dep, "original_amount": float(inv["amount"]), "purchase_date": inv["purchase_date"]})
        return {"year": year, "total_depreciation": round(total, 2), "items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/")
async def add_investment(request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
        amount = float(body.get("amount", 0))
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        description = body.get("description", "").strip()
        if not description:
            raise HTTPException(status_code=400, detail="Description is required")
        purchase_date = body.get("purchase_date", date.today().isoformat())
        depreciation_years = int(body.get("depreciation_years", 5))
        data = {"user_id": user_id, "description": description, "purchase_date": purchase_date, "amount": amount, "category": body.get("category", "general"), "depreciation_years": depreciation_years}
        if body.get("receipt_url"):
            data["receipt_url"] = body["receipt_url"]
        result = supabase.table("investments").insert(data).execute()
        inv = result.data[0] if result.data else {}
        if inv:
            inv["depreciation_schedule"] = calculate_depreciation(amount, purchase_date, depreciation_years)
            inv["suggest_depreciation"] = amount > DEPRECIATION_THRESHOLD
        # Fire-and-forget reconcile.
        schedule_reconcile(user_id)
        return {"success": True, "investment": inv}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{investment_id}")
async def delete_investment(investment_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        # Finding #10: 404 on a foreign/missing id instead of silent 200.
        delete_owned("investments", investment_id, user_id)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

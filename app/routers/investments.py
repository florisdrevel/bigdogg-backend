from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from datetime import date

router = APIRouter()

DEPRECIATION_THRESHOLD = 450.0  # Dutch threshold for depreciation


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
    """Calculate annual depreciation schedule."""
    annual = round(amount / years, 2)
    purchase_year = int(purchase_date[:4])
    schedule = []
    for i in range(years):
        yr = purchase_year + i
        schedule.append({
            "year": yr,
            "amount": annual,
            "cumulative": round(annual * (i + 1), 2),
            "remaining": round(amount - annual * (i + 1), 2),
        })
    return schedule


@router.get("/")
async def get_investments(request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("investments").select("*")\
            .eq("user_id", user_id)\
            .order("purchase_date", desc=True)\
            .execute()
        investments = result.data or []

        # Add depreciation schedule to each investment
        for inv in investments:
            inv["depreciation_schedule"] = calculate_depreciation(
                float(inv["amount"]),
                inv["purchase_date"],
                inv.get("depreciation_years", 5)
            )
            # Current year depreciation
            current_year = date.today().year
            inv["current_year_depreciation"] = next(
                (s["amount"] for s in inv["depreciation_schedule"] if s["year"] == current_year),
                0
            )

        return {"investments": investments}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/annual/{year}")
async def get_annual_depreciation(year: int, request: Request):
    """Get total depreciation for a specific year across all investments."""
    user_id = get_user_id(request)
    try:
        result = supabase.table("investments").select("*")\
            .eq("user_id", user_id).execute()
        investments = result.data or []

        total_depreciation = 0.0
        items = []
        for inv in investments:
            schedule = calculate_depreciation(
                float(inv["amount"]),
                inv["purchase_date"],
                inv.get("depreciation_years", 5)
            )
            year_dep = next((s["amount"] for s in schedule if s["year"] == year), 0)
            if year_dep > 0:
                total_depreciation += year_dep
                items.append({
                    "description": inv["description"],
                    "amount": year_dep,
                    "original_amount": float(inv["amount"]),
                    "purchase_date": inv["purchase_date"],
                })

        return {
            "year": year,
            "total_depreciation": round(total_depreciation, 2),
            "items": items,
        }
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
        category = body.get("category", "general")
        depreciation_years = int(body.get("depreciation_years", 5))
        receipt_url = body.get("receipt_url")

        data = {
            "user_id": user_id,
            "description": description,
            "purchase_date": purchase_date,
            "amount": amount,
            "category": category,
            "depreciation_years": depreciation_years,
        }
        if receipt_url:
            data["receipt_url"] = receipt_url

        result = supabase.table("investments").insert(data).execute()
        inv = result.data[0] if result.data else {}
        if inv:
            inv["depreciation_schedule"] = calculate_depreciation(
                amount, purchase_date, depreciation_years)
            inv["suggest_depreciation"] = amount > DEPRECIATION_THRESHOLD

        return {"success": True, "investment": inv}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{investment_id}")
async def delete_investment(investment_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("investments").delete()\
            .eq("id", investment_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
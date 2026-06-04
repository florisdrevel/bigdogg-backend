from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.database import supabase

router = APIRouter()


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    unit_price: float
    btw_rate: int = 21
    unit: str = "hour"
    vat_included: bool = False


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    btw_rate: Optional[int] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None
    vat_included: Optional[bool] = None


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
async def get_products(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("products")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .order("created_at", desc=False)\
            .execute()
        return {"products": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_product(product: ProductCreate, request: Request):
    user_id = get_user_id(request)
    try:
        # If vat_included, store the back-calculated ex-BTW price
        unit_price = product.unit_price
        if product.vat_included and product.btw_rate > 0:
            unit_price = round(product.unit_price / (1 + product.btw_rate / 100), 4)

        response = supabase.table("products").insert({
            "user_id": user_id,
            "name": product.name,
            "description": product.description,
            "unit_price": unit_price,
            "btw_rate": product.btw_rate,
            "unit": product.unit,
            "vat_included": product.vat_included,
        }).execute()
        return {"product": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{product_id}")
async def update_product(product_id: str, product: ProductUpdate, request: Request):
    user_id = get_user_id(request)
    try:
        update_data = {k: v for k, v in product.model_dump().items() if v is not None}

        # If vat_included is being set and we have a price, back-calculate
        if update_data.get("vat_included") and "unit_price" in update_data:
            btw_rate = update_data.get("btw_rate", 21)
            if btw_rate > 0:
                update_data["unit_price"] = round(update_data["unit_price"] / (1 + btw_rate / 100), 4)

        response = supabase.table("products")\
            .update(update_data)\
            .eq("id", product_id)\
            .eq("user_id", user_id)\
            .execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"product": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{product_id}")
async def delete_product(product_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        # Finding #10: soft-delete (is_active=False) scoped to the caller;
        # 404 if the id isn't theirs instead of a silent 200.
        response = supabase.table("products")\
            .update({"is_active": False})\
            .eq("id", product_id)\
            .eq("user_id", user_id)\
            .execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
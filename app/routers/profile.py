from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.database import supabase

router = APIRouter()


class ProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    full_name: Optional[str] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    kvk_number: Optional[str] = None
    btw_number: Optional[str] = None
    iban: Optional[str] = None
    language: Optional[str] = None
    onboarding_complete: Optional[bool] = None


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
async def get_profile(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("user_profiles")\
            .select("*")\
            .eq("id", user_id)\
            .execute()
        if not response.data:
            return {"profile": None}
        return {"profile": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def upsert_profile(profile: ProfileUpdate, request: Request):
    user_id = get_user_id(request)
    try:
        update_data = {k: v for k, v in profile.model_dump().items() if v is not None}
        update_data["id"] = user_id

        existing = supabase.table("user_profiles")\
            .select("id")\
            .eq("id", user_id)\
            .execute()

        if existing.data:
            response = supabase.table("user_profiles")\
                .update(update_data)\
                .eq("id", user_id)\
                .execute()
        else:
            response = supabase.table("user_profiles")\
                .insert(update_data)\
                .execute()

        return {"profile": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
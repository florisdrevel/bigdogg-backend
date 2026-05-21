from fastapi import APIRouter, HTTPException, Request, UploadFile, File
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
    # Optional override for the "Ten name van" line on invoice emails.
    # Falls back to business_name / full_name when blank.
    bank_account_name: Optional[str] = None
    language: Optional[str] = None
    onboarding_complete: Optional[bool] = None
    # Hex strings like "#1B3A4B". Used as the line/header color and the
    # accent (totals row, OFFERTE/FACTUUR label) on PDF invoices/quotes.
    invoice_primary_color: Optional[str] = None
    invoice_accent_color: Optional[str] = None
    # Per-user default for whether outgoing invoice emails should include
    # the Stripe payment link. The per-send toggle in the send dialog
    # always wins; this is just the initial check state.
    default_exclude_payment_link: Optional[bool] = None


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

@router.post("/logo")
async def upload_logo(request: Request, file: UploadFile = File(...)):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        # Ensure logos bucket exists
        try:
            supabase.storage.create_bucket("logos", options={"public": True})
        except Exception:
            pass
        file_bytes = await file.read()
        ext = file.filename.split(".")[-1].lower() if file.filename else "png"
        path = f"{user_id}/logo.{ext}"
        # Remove old logo if exists
        try:
            supabase.storage.from_("logos").remove([path])
        except Exception:
            pass
        supabase.storage.from_("logos").upload(
            path, file_bytes,
            file_options={"content-type": file.content_type or "image/png", "upsert": "true"}
        )
        public_url = supabase.storage.from_("logos").get_public_url(path)
        # Save to profile
        existing = supabase.table("user_profiles").select("id").eq("id", user_id).execute()
        if existing.data:
            supabase.table("user_profiles").update({"logo_url": public_url}).eq("id", user_id).execute()
        else:
            supabase.table("user_profiles").insert({"id": user_id, "logo_url": public_url}).execute()
        return {"success": True, "logo_url": public_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

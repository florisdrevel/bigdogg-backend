from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import supabase

router = APIRouter()


class ClientCreate(BaseModel):
    company_name: Optional[str] = None
    contact_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: str = "Nederland"
    btw_number: Optional[str] = None
    kvk_number: Optional[str] = None


class ClientOnboarding(BaseModel):
    company_name: Optional[str] = None
    contact_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: str = "Nederland"
    btw_number: Optional[str] = None
    kvk_number: Optional[str] = None


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
async def get_clients(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("clients")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=False)\
            .execute()
        return {"clients": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_client(client: ClientCreate, request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("clients").insert({
            "user_id": user_id,
            "company_name": client.company_name,
            "contact_name": client.contact_name,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
            "postcode": client.postcode,
            "city": client.city,
            "country": client.country,
            "btw_number": client.btw_number,
            "kvk_number": client.kvk_number,
        }).execute()
        return {"client": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{client_id}")
async def delete_client(client_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("clients")\
            .delete()\
            .eq("id", client_id)\
            .eq("user_id", user_id)\
            .execute()
        return {"message": "Client deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/onboarding/{token}")
async def get_onboarding_info(token: str):
    try:
        response = supabase.table("clients")\
            .select("user_id")\
            .eq("onboarding_token", token)\
            .execute()
        if response.data:
            return {"valid": False, "message": "Token already used"}
        return {"valid": True, "token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/onboarding/{token}")
async def complete_onboarding(token: str, client: ClientOnboarding):
    try:
        # Get the user_id from the token
        response = supabase.table("clients")\
            .select("user_id")\
            .eq("onboarding_token", token)\
            .execute()

        # Find which user owns this token by checking pending invites
        # For now we store the user_id in a separate invites approach
        # The token IS the onboarding_token on a pre-created stub record
        stub = supabase.table("client_invites")\
            .select("*")\
            .eq("token", token)\
            .single()\
            .execute()

        if not stub.data:
            raise HTTPException(status_code=404, detail="Invalid or expired invite link")

        user_id = stub.data['user_id']

        result = supabase.table("clients").insert({
            "user_id": user_id,
            "company_name": client.company_name,
            "contact_name": client.contact_name,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
            "postcode": client.postcode,
            "city": client.city,
            "country": client.country,
            "btw_number": client.btw_number,
            "kvk_number": client.kvk_number,
        }).execute()

        # Mark invite as used
        supabase.table("client_invites")\
            .update({"used": True})\
            .eq("token", token)\
            .execute()

        return {"message": "Client added successfully", "client": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invite")
async def create_invite(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("client_invites").insert({
            "user_id": user_id,
        }).execute()
        token = response.data[0]['token']
        return {"invite_url": f"https://bigdogg-production.up.railway.app/onboard/{token}", "token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
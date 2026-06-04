from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import supabase
from app.services.tenant_db import require_owned_id
from app.services.tokens import expiry_in_days, is_expired, CLIENT_INVITE_TTL_DAYS

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


class ClientUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    postcode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
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


@router.put("/{client_id}")
async def update_client(client_id: str, client: ClientUpdate, request: Request):
    user_id = get_user_id(request)
    try:
        update_data = {k: v for k, v in client.model_dump().items() if v is not None}
        response = supabase.table("clients")\
            .update(update_data)\
            .eq("id", client_id)\
            .eq("user_id", user_id)\
            .execute()
        return {"client": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{client_id}")
async def delete_client(client_id: str, request: Request):
    user_id = get_user_id(request)
    # Verify the client belongs to the caller UPFRONT — 404 otherwise.
    # Without this the subsequent invoice queries scoped only by
    # client_id could probe / mutate another tenant's invoices.
    require_owned_id("clients", client_id, user_id)
    try:
        # Block deletion if THIS user has any unpaid invoices for the
        # client. Both client_id and user_id eq required so we only ever
        # see the caller's own invoices.
        unpaid = supabase.table("invoices")\
            .select("id, status")\
            .eq("client_id", client_id)\
            .eq("user_id", user_id)\
            .in_("status", ["draft", "sent", "overdue"])\
            .execute()

        if unpaid.data:
            raise HTTPException(
                status_code=400,
                detail=f"Deze klant heeft {len(unpaid.data)} onbetaalde factuur/facturen. Markeer ze als betaald voor je de klant verwijdert."
            )

        # Set client_id to null on the caller's own paid invoices to
        # preserve history; other tenants' invoices are NEVER touched.
        supabase.table("invoices")\
            .update({"client_id": None})\
            .eq("client_id", client_id)\
            .eq("user_id", user_id)\
            .execute()

        # Delete client
        supabase.table("clients")\
            .delete()\
            .eq("id", client_id)\
            .eq("user_id", user_id)\
            .execute()

        return {"message": "Client deleted"}
    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e)
        if '23503' in error_str or 'foreign key' in error_str.lower():
            raise HTTPException(
                status_code=400,
                detail="Deze klant heeft openstaande facturen. Markeer ze als betaald voor je de klant verwijdert."
            )
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/onboarding/{token}")
async def get_onboarding_info(token: str):
    try:
        result = supabase.table("client_invites")\
            .select("*")\
            .eq("token", token)\
            .eq("used", False)\
            .execute()
        if not result.data:
            return {"valid": False, "message": "Invalid or expired invite link"}
        # Finding #9: reject expired onboarding links.
        if is_expired(result.data[0].get("expires_at")):
            return {"valid": False, "message": "Invalid or expired invite link"}
        return {"valid": True, "token": token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/onboarding/{token}")
async def complete_onboarding(token: str, client: ClientOnboarding):
    try:
        stub = supabase.table("client_invites")\
            .select("*")\
            .eq("token", token)\
            .eq("used", False)\
            .execute()

        if not stub.data:
            raise HTTPException(status_code=404, detail="Invalid or expired invite link")
        # Finding #9: reject expired onboarding links before creating the client.
        if is_expired(stub.data[0].get("expires_at")):
            raise HTTPException(status_code=410, detail="Invalid or expired invite link")

        user_id = stub.data[0]['user_id']

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

        supabase.table("client_invites")\
            .update({"used": True})\
            .eq("token", token)\
            .execute()

        from app.routers.notifications import create_notification
        new_client = result.data[0] if result.data else {}
        display_name = (
            client.company_name or client.contact_name or "Een nieuwe klant"
        )
        create_notification(
            user_id=user_id,
            notification_type="client_onboarded",
            title="Nieuwe klant 👋",
            body=f"{display_name} heeft het onboarding-formulier ingevuld.",
            data={"client_id": new_client.get("id")},
        )

        return {"message": "Client added successfully", "client": result.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/invite")
async def create_invite(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("client_invites").insert({
            "user_id": user_id,
            # Finding #9: onboarding links expire after 14 days.
            "expires_at": expiry_in_days(CLIENT_INVITE_TTL_DAYS),
        }).execute()
        token = response.data[0]['token']
        # Use the share-link short URL so WhatsApp/Slack/Facebook show
        # a personalized "Floris nodigt je uit" preview instead of the
        # generic landing-page meta tags. Host is settings-driven so
        # swapping in `link.bigdogg.nl` later is one Railway env change.
        from app.config import settings as _s
        return {
            "invite_url": f"{_s.share_link_origin}/o/{token}",
            "token": token
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
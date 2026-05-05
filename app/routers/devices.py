"""Device-token registration for OS-level push (FCM).

The Flutter app fetches an FCM registration token at startup and
posts it here. We upsert by (user_id, fcm_token) so the same device
re-registering on app reopen is a no-op.

Companion endpoint: DELETE /api/v1/devices/fcm-token to clear a token
on logout (so the next account using that device doesn't receive
the previous user's pushes).
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
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


@router.post("/register-fcm-token")
async def register_fcm_token(request: Request):
    """Body: { token: str, platform: 'android'|'ios'|'web', device_name?: str }"""
    user_id = get_user_id(request)
    body = await request.json() if await _has_body(request) else {}
    token = (body or {}).get("token") or ""
    platform = ((body or {}).get("platform") or "android").lower()
    device_name = (body or {}).get("device_name")
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    if platform not in ("android", "ios", "web"):
        raise HTTPException(status_code=400, detail="invalid platform")

    try:
        supabase.table("fcm_device_tokens").upsert({
            "user_id":     user_id,
            "fcm_token":   token,
            "platform":    platform,
            "device_name": device_name,
            "last_seen":   datetime.now(timezone.utc).isoformat(),
        }, on_conflict="user_id,fcm_token").execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True}


@router.delete("/fcm-token")
async def delete_fcm_token(request: Request):
    """Body: { token: str }"""
    user_id = get_user_id(request)
    body = await request.json() if await _has_body(request) else {}
    token = (body or {}).get("token") or ""
    if not token:
        raise HTTPException(status_code=400, detail="token required")
    try:
        supabase.table("fcm_device_tokens").delete()\
            .eq("user_id", user_id).eq("fcm_token", token).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"success": True}


async def _has_body(request: Request) -> bool:
    return (request.headers.get("content-length") or "0") != "0"

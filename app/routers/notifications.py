"""
In-app notifications.

Public helper `create_notification` is imported by other routers (payments,
quotes, clients) to insert a notification row when something noteworthy
happens. Errors are swallowed — a missing notifications table or RLS
hiccup must never break the upstream operation that triggered it.

REST surface:
  GET    /api/v1/notifications              — list recent (newest first)
  GET    /api/v1/notifications/unread-count — fast badge count
  POST   /api/v1/notifications/{id}/read    — mark one as read
  POST   /api/v1/notifications/read-all     — mark everything as read
  DELETE /api/v1/notifications/{id}         — dismiss a notification
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, Any
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


def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    body: Optional[str] = None,
    data: Optional[dict] = None,
) -> None:
    """Best-effort insert. Used from other routers."""
    if not user_id or not notification_type or not title:
        print(f"[notifications] skipped — missing user_id/type/title")
        return
    try:
        supabase.table("notifications").insert({
            "user_id": user_id,
            "type":    notification_type,
            "title":   title,
            "body":    body,
            "data":    data,
        }).execute()
        print(f"[notifications] inserted type={notification_type} for user={user_id[:8]}…")
    except Exception as e:
        msg = str(e).lower()
        if "row-level security" in msg or "42501" in msg:
            print(f"[notifications] RLS rejected — RUN migrations/notifications.sql ({e})")
        elif "does not exist" in msg or "relation" in msg or "pgrst" in msg:
            print(f"[notifications] table missing — RUN migrations/notifications.sql ({e})")
        else:
            print(f"[notifications] insert skipped: {e}")


@router.get("/")
async def list_notifications(request: Request, limit: int = 50):
    user_id = get_user_id(request)
    try:
        result = supabase.table("notifications")\
            .select("*").eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .limit(limit).execute()
        return {"notifications": result.data or []}
    except Exception as e:
        print(f"[notifications] list failed: {e}")
        return {"notifications": []}


@router.get("/unread-count")
async def unread_count(request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("notifications")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .is_("read_at", "null")\
            .execute()
        return {"count": result.count or 0}
    except Exception as e:
        print(f"[notifications] unread-count failed: {e}")
        return {"count": 0}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("notifications").update({
            "read_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", notification_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/read-all")
async def mark_all_read(request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("notifications").update({
            "read_at": datetime.now(timezone.utc).isoformat(),
        }).eq("user_id", user_id).is_("read_at", "null").execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("notifications").delete()\
            .eq("id", notification_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

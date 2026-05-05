"""Accountant portal — invitations + read-only client list.

Two parties:

  * Owner: a regular BigDogg user. Can invite their accountant by
    email, list/revoke active accountants, see pending invites.
  * Accountant: a separate Supabase user (signs up like anyone else).
    Once the owner sends an invite and the accountant taps the
    /accept-invite link with a valid token, an `accountant_clients`
    row is created and Postgres RLS auto-grants the accountant
    SELECT access to the owner's invoices/expenses/etc.

This module only handles the invitation / acceptance / management
flow. Read access for the accountant is granted via the SQL RLS
policies in migrations/accountant_portal.sql — no extra Python.

Endpoints (under /api/v1/accountants):

  POST   /invite                      — owner: invite by email
  GET    /invites                     — owner: list pending invites
  DELETE /invites/{token}             — owner: cancel a pending invite
  GET    /                            — owner: list active accountants
  DELETE /{accountant_id}             — owner: revoke an accountant

  GET    /clients                     — accountant: list owners they
                                        have access to
  POST   /accept-invite/{token}       — accountant: redeem an invite
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from app.database import supabase
from app.config import settings
import resend

router = APIRouter()
resend.api_key = settings.resend_api_key


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


def _user_email(request: Request) -> str:
    auth_header = request.headers.get("authorization") or ""
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return (user.user.email or "").lower()
    except Exception:
        return ""


# ─── Owner: invite an accountant ──────────────────────────────
@router.post("/invite")
async def invite_accountant(request: Request):
    user_id = get_user_id(request)
    body = await request.json()
    email = (body or {}).get("email", "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="invalid_email")

    insert = supabase.table("accountant_invites").insert({
        "user_id": user_id,
        "email":   email,
        "used":    False,
    }).execute()
    if not insert.data:
        raise HTTPException(status_code=400, detail="invite_failed")

    token = insert.data[0]["token"]

    # Fetch the inviting user's display name for the email body.
    profile = supabase.table("user_profiles")\
        .select("business_name, full_name")\
        .eq("id", user_id).limit(1).execute()
    inviter = "Een BigDogg-gebruiker"
    if profile.data:
        p = profile.data[0]
        inviter = (p.get("business_name") or p.get("full_name") or inviter).strip()

    accept_url = f"{settings.share_link_origin}/a/{token}"

    # Best-effort email — never fail the invite creation if email errors.
    try:
        if settings.resend_api_key:
            resend.Emails.send({
                "from": "BigDogg <noreply@bigdogg.nl>",
                "to":   [email],
                "subject": f"{inviter} nodigt je uit om hun boekhouding in te zien",
                "html": (
                    f"<p>Hallo,</p>"
                    f"<p><strong>{inviter}</strong> nodigt je uit als accountant op BigDogg. "
                    "Klik hieronder om je in te loggen en hun facturen, kosten en BTW-overzicht "
                    "in te zien (alleen-lezen).</p>"
                    f'<p><a href="{accept_url}" '
                    'style="background:#1B3A4B;color:#fff;padding:12px 22px;'
                    'border-radius:8px;text-decoration:none;font-weight:600">'
                    "Accepteer uitnodiging</a></p>"
                    f'<p style="color:#4A6572;font-size:12px">Of plak deze link in je browser: '
                    f'<a href="{accept_url}">{accept_url}</a></p>'
                    "<p>De link is 14 dagen geldig.</p>"
                ),
            })
    except Exception as e:
        print(f"[accountants] invite email skipped: {e}")

    return {"success": True, "token": token, "accept_url": accept_url}


@router.get("/invites")
async def list_invites(request: Request):
    user_id = get_user_id(request)
    result = supabase.table("accountant_invites")\
        .select("token, email, used, expires_at, created_at")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True).execute()
    return {"invites": result.data or []}


@router.delete("/invites/{token}")
async def cancel_invite(token: str, request: Request):
    user_id = get_user_id(request)
    supabase.table("accountant_invites").delete()\
        .eq("user_id", user_id).eq("token", token).execute()
    return {"success": True}


# ─── Owner: list / revoke active accountants ─────────────────
@router.get("/")
async def list_accountants(request: Request):
    user_id = get_user_id(request)
    rows = supabase.table("accountant_clients")\
        .select("id, accountant_id, status, created_at")\
        .eq("user_id", user_id)\
        .eq("status", "active").execute()

    out = []
    for r in (rows.data or []):
        # Lookup display name for the accountant.
        try:
            ap = supabase.table("user_profiles")\
                .select("full_name, business_name")\
                .eq("id", r["accountant_id"]).limit(1).execute()
            display_name = ""
            if ap.data:
                d = ap.data[0]
                display_name = (d.get("business_name") or d.get("full_name") or "").strip()
        except Exception:
            display_name = ""
        out.append({
            "id":            r["id"],
            "accountant_id": r["accountant_id"],
            "display_name":  display_name,
            "since":         r.get("created_at"),
        })
    return {"accountants": out}


@router.delete("/{accountant_id}")
async def revoke_accountant(accountant_id: str, request: Request):
    user_id = get_user_id(request)
    supabase.table("accountant_clients").update({
        "status": "revoked",
        "revoked_at": datetime.now(timezone.utc).isoformat(),
    }).eq("user_id", user_id).eq("accountant_id", accountant_id).execute()
    return {"success": True}


# ─── Accountant side ────────────────────────────────────────
@router.post("/accept-invite/{token}")
async def accept_invite(token: str, request: Request):
    """Called by an accountant after they sign up / log in to BigDogg
    and tap the link in their email. Validates the token, creates the
    accountant_clients row, marks the invite used."""
    accountant_id = get_user_id(request)
    accountant_email = _user_email(request)

    invite = supabase.table("accountant_invites")\
        .select("token, user_id, email, used, expires_at")\
        .eq("token", token).limit(1).execute()
    if not invite.data:
        raise HTTPException(status_code=404, detail="invite_not_found")
    row = invite.data[0]
    if row.get("used"):
        raise HTTPException(status_code=400, detail="invite_already_used")

    # Sanity: the email on the invite must match the authenticated
    # accountant's email. This is the only guard against forwarding the
    # link to someone else.
    invite_email = (row.get("email") or "").lower().strip()
    if invite_email and accountant_email and invite_email != accountant_email:
        raise HTTPException(status_code=403, detail="email_mismatch")

    expires_raw = row.get("expires_at")
    if expires_raw:
        try:
            exp = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) >= exp:
                raise HTTPException(status_code=400, detail="invite_expired")
        except HTTPException:
            raise
        except Exception:
            pass

    owner_id = row["user_id"]

    # Idempotent insert: re-accepting just refreshes status.
    supabase.table("accountant_clients").upsert({
        "accountant_id": accountant_id,
        "user_id":       owner_id,
        "status":        "active",
        "revoked_at":    None,
    }, on_conflict="accountant_id,user_id").execute()
    supabase.table("accountant_invites").update({
        "used": True,
    }).eq("token", token).execute()

    # Notify the owner that their accountant is now linked.
    try:
        from app.routers.notifications import create_notification
        create_notification(
            user_id=owner_id,
            notification_type="accountant_linked",
            title="Accountant heeft toegang",
            body="Je accountant heeft de uitnodiging geaccepteerd en kan nu je administratie inzien.",
            data={"accountant_id": accountant_id},
        )
    except Exception as e:
        print(f"[accountants] linked-notification skipped: {e}")

    return {"success": True, "owner_id": owner_id}


@router.get("/clients")
async def list_clients_of_accountant(request: Request):
    """Accountant view: list every BigDogg user that has an active
    `accountant_clients` row pointing at me."""
    accountant_id = get_user_id(request)
    rows = supabase.table("accountant_clients")\
        .select("id, user_id, status, created_at")\
        .eq("accountant_id", accountant_id)\
        .eq("status", "active").execute()

    out = []
    for r in (rows.data or []):
        try:
            up = supabase.table("user_profiles")\
                .select("full_name, business_name")\
                .eq("id", r["user_id"]).limit(1).execute()
            display_name = ""
            if up.data:
                d = up.data[0]
                display_name = (d.get("business_name") or d.get("full_name") or "").strip()
        except Exception:
            display_name = ""
        out.append({
            "user_id":       r["user_id"],
            "display_name":  display_name,
            "since":         r.get("created_at"),
        })
    return {"clients": out}

from fastapi import APIRouter, HTTPException, Request, status
import resend
from app.config import settings
resend.api_key = settings.resend_api_key
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import supabase
from datetime import datetime, timezone
import hashlib
import re
import stripe
import requests as http_requests
stripe.api_key = settings.stripe_secret_key

router = APIRouter()


# ─── New-device login notifications ─────────────────────────────
def _device_fingerprint(user_agent: str) -> str:
    """Stable hash of the device class.

    Strip version numbers from the User-Agent so a Chrome point-update
    doesn't look like a new device, then SHA-256 the result.
    """
    ua = (user_agent or "").lower()
    normalized = re.sub(r'\d+\.\d+(\.\d+)*', 'X', ua)[:200]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def _describe_device(user_agent: str) -> str:
    ua = (user_agent or "").lower()
    if "iphone" in ua:    return "een iPhone"
    if "ipad" in ua:      return "een iPad"
    if "android" in ua:   return "een Android-apparaat"
    if "mac" in ua:       return "een Mac"
    if "windows" in ua:   return "een Windows-pc"
    if "linux" in ua:     return "een Linux-apparaat"
    return "een onbekend apparaat"


def _ip_location(ip: str) -> str:
    """Best-effort IP geolocation via ipapi.co (free, no API key).

    Returns 'City, Country' (or just country, or empty) — never raises.
    Hard 2-second timeout so a slow geo lookup can't slow down login.
    """
    if not ip or ip in ("unknown", "127.0.0.1", "::1") or ip.startswith("10."):
        return ""
    try:
        import urllib.request as _ur
        import json as _json
        req = _ur.Request(
            f"https://ipapi.co/{ip}/json/",
            headers={"User-Agent": "BigDogg/1.0"},
        )
        with _ur.urlopen(req, timeout=2) as r:
            data = _json.loads(r.read())
        city    = (data.get("city")         or "").strip()
        country = (data.get("country_name") or "").strip()
        if city and country:
            return f"{city}, {country}"
        return country or city or ""
    except Exception as e:
        print(f"[auth/devices] geolocation skipped: {e}")
        return ""


def _send_new_device_email(email: str, user_agent: str, ip: str) -> None:
    if not settings.resend_api_key or not email:
        print(f"[auth/devices] email skipped — resend_api_key={bool(settings.resend_api_key)} email_present={bool(email)}")
        return
    device   = _describe_device(user_agent)
    location = _ip_location(ip)
    when     = datetime.now(timezone.utc).strftime("%d-%m-%Y, %H:%M UTC")
    change_pw_url = "https://bigdogg.nl/#/login"

    # ── Plain-text body (fallback for clients that strip HTML) ──
    location_line = f" Locatie: {location}.\n" if location else ""
    text_body = (
        f"Hoi,\n\n"
        f"We zagen zojuist een nieuwe inlog op je BigDogg-account vanaf "
        f"{device} (IP: {ip}) op {when}.\n"
        f"{location_line}"
        f"\nWas jij dit? Dan hoef je niets te doen.\n\n"
        f"Was jij dit NIET? Wijzig dan direct je wachtwoord via:\n"
        f"{change_pw_url}\n\n"
        f"Vragen? Mail info@bigdogg.nl\n\n"
        f"Met vriendelijke groet,\nBigDogg\n\n---\nbigdogg.nl\n"
    )

    # ── Branded HTML body (BigDogg teal/gold, same vibe as quote email) ──
    location_html = (
        f'<tr><td style="padding:6px 0;color:#4A6572;font-size:13px;">'
        f'<strong style="color:#1B3A4B;">Locatie:</strong> {location}</td></tr>'
    ) if location else ""
    html_body = f"""<!DOCTYPE html>
<html lang="nl">
<body style="margin:0;padding:0;background:#F5F3EF;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1B3A4B;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F3EF;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;border:1px solid #E2DDD6;overflow:hidden;">
        <tr><td align="center" style="padding:28px 28px 8px 28px;">
          <img src="https://bigdogg.nl/icons/Icon-512.png" alt="BigDogg" width="64" height="64" style="display:block;border-radius:14px;" />
          <h1 style="margin:14px 0 0 0;font-size:20px;font-weight:800;color:#1B3A4B;letter-spacing:-0.3px;">Nieuwe inlog op je account</h1>
        </td></tr>
        <tr><td style="padding:8px 28px 4px 28px;">
          <p style="margin:0 0 14px 0;font-size:14px;line-height:1.6;color:#4A6572;">
            We zagen zojuist een nieuwe inlog op je BigDogg-account.
          </p>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F3EF;border-radius:10px;padding:14px 16px;">
            <tr><td style="padding:6px 0;color:#4A6572;font-size:13px;"><strong style="color:#1B3A4B;">Apparaat:</strong> {device}</td></tr>
            <tr><td style="padding:6px 0;color:#4A6572;font-size:13px;"><strong style="color:#1B3A4B;">IP:</strong> {ip}</td></tr>
            {location_html}
            <tr><td style="padding:6px 0;color:#4A6572;font-size:13px;"><strong style="color:#1B3A4B;">Tijdstip:</strong> {when}</td></tr>
          </table>
          <p style="margin:18px 0 6px 0;font-size:14px;line-height:1.6;color:#1B3A4B;">
            <strong>Was jij dit?</strong> Dan hoef je niets te doen.
          </p>
          <p style="margin:0 0 18px 0;font-size:14px;line-height:1.6;color:#1B3A4B;">
            <strong>Was jij dit NIET?</strong> Wijzig direct je wachtwoord via de knop hieronder.
          </p>
        </td></tr>
        <tr><td align="center" style="padding:0 28px 28px 28px;">
          <a href="{change_pw_url}" style="display:inline-block;background:#C9A96E;color:#ffffff;text-decoration:none;padding:13px 28px;border-radius:8px;font-weight:700;font-size:15px;">
            Wachtwoord wijzigen
          </a>
        </td></tr>
        <tr><td style="padding:0 28px 24px 28px;border-top:1px solid #E2DDD6;">
          <p style="margin:14px 0 0 0;font-size:12px;line-height:1.5;color:#4A6572;">
            Vragen of klopt iets niet? Mail
            <a href="mailto:info@bigdogg.nl" style="color:#1B3A4B;">info@bigdogg.nl</a>.
          </p>
        </td></tr>
      </table>
      <p style="margin:14px 0 0 0;font-size:11px;color:#9CA3AF;">BigDogg · bigdogg.nl</p>
    </td></tr>
  </table>
</body>
</html>"""

    try:
        resend.Emails.send({
            "from": "BigDogg <info@bigdogg.nl>",
            "to": [email],
            "subject": "Nieuwe inlog op je BigDogg-account",
            "text": text_body,
            "html": html_body,
        })
        print(f"[auth/devices] new-device email sent to {email} (location={location or 'unknown'})")
    except Exception as e:
        print(f"[auth/devices] notify email failed: {e}")


def _record_login_and_maybe_notify(
    user_id: str, email: str, ip: str, user_agent: str
) -> None:
    """
    Find or create the (user, fingerprint) row. Send a notification email
    on first sight only. All errors are swallowed — security is nice to
    have, but a missing user_devices table mustn't break logins.
    """
    fingerprint = _device_fingerprint(user_agent)
    try:
        existing = supabase.table("user_devices")\
            .select("id").eq("user_id", user_id)\
            .eq("fingerprint", fingerprint).execute()
        now = datetime.now(timezone.utc).isoformat()
        if existing.data:
            supabase.table("user_devices").update({
                "last_seen": now,
                "last_ip":   ip,
            }).eq("id", existing.data[0]["id"]).execute()
            print(f"[auth/devices] known device for {email} fp={fingerprint[:8]}…")
        else:
            supabase.table("user_devices").insert({
                "user_id":     user_id,
                "fingerprint": fingerprint,
                "user_agent":  (user_agent or "")[:500],
                "last_ip":     ip,
            }).execute()
            print(f"[auth/devices] NEW device for {email} fp={fingerprint[:8]}… → sending email")
            _send_new_device_email(email, user_agent, ip)
    except Exception as e:
        # Common causes: missing migration or missing RLS policy. The
        # error string from PostgREST tells us which.
        msg = str(e).lower()
        if "row-level security" in msg or "42501" in msg:
            print(f"[auth/devices] RLS rejected — RUN migrations/user_devices_rls.sql ({e})")
        elif "does not exist" in msg or "relation" in msg or "pgrst" in msg:
            print(f"[auth/devices] table missing — RUN migrations/user_devices.sql ({e})")
        else:
            print(f"[auth/devices] tracking skipped: {e}")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    ref: Optional[str] = None  # referral code, optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    current_password: str


def _verify_current_password(email: str, current_password: str) -> None:
    """Re-prove possession of the current password before destructive
    actions (change password, delete account). A valid access token by
    itself is not enough — a stolen token would otherwise be able to
    lock the user out or wipe the account.

    Uses sign_in_with_password as a verifier; the resulting session is
    discarded. Raises 401 with a generic message on any mismatch.
    """
    if not current_password:
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    try:
        supabase.auth.sign_in_with_password({
            "email": email,
            "password": current_password,
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Current password is incorrect")


@router.post("/register")
async def register(data: RegisterRequest):
    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "full_name": data.full_name
                }
            }
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )

        if response.user.identities is not None and len(response.user.identities) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists. Please sign in instead."
            )

        # Track referral if code present (non-fatal — never block signup on this)
        if data.ref:
            try:
                ref_code = data.ref.strip().upper()
                ref_lookup = supabase.table("referrals")\
                    .select("referrer_user_id")\
                    .eq("code", ref_code)\
                    .execute()
                if ref_lookup.data:
                    referrer_user_id = ref_lookup.data[0]["referrer_user_id"]
                    supabase.table("referral_signups").insert({
                        "referrer_code": ref_code,
                        "referrer_user_id": referrer_user_id,
                        "new_user_id": response.user.id,
                        "converted": False,
                    }).execute()
                    # Recompute referrer's bonus eligibility (per 2 signups
                    # they earn 1 free pro month, capped at 3). Failures
                    # never block signup.
                    try:
                        from app.routers.subscription import (
                            maybe_grant_referral_bonus,
                        )
                        maybe_grant_referral_bonus(referrer_user_id)
                    except Exception as bonus_err:
                        print(
                            "Referral bonus grant error (non-fatal): "
                            f"{bonus_err}"
                        )
            except Exception as ref_err:
                print(f"Referral signup tracking error (non-fatal): {ref_err}")

        return {
            "message": "Registration successful. Please check your email to confirm.",
            "user_id": response.user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(data: LoginRequest, request: Request):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if response.user.email_confirmed_at is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please confirm your email address before signing in. Check your inbox."
            )

        # New-device notification: hash the User-Agent, look up in
        # user_devices; if unseen, insert and email the user.
        forwarded = request.headers.get("x-forwarded-for", "")
        ip = (forwarded.split(",")[0].strip() if forwarded
              else (request.client.host if request.client else "unknown"))
        user_agent = request.headers.get("user-agent", "")
        _record_login_and_maybe_notify(
            response.user.id, response.user.email, ip, user_agent
        )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "full_name": response.user.user_metadata.get("full_name", "")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/refresh")
async def refresh_token(data: RefreshRequest):
    try:
        response = supabase.auth.refresh_session(data.refresh_token)
        if response.session is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")


@router.post("/logout")
async def logout():
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    try:
        supabase.auth.reset_password_email(data.email)
        return {"message": "Reset email sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/change-password")
async def change_password(data: ChangePasswordRequest, request: Request):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        user_email = user.user.email
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not data.new_password or len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Re-prove the current password — a stolen JWT alone must not be
    # able to change the password and lock the user out.
    _verify_current_password(user_email, data.current_password)

    try:
        supabase.auth.admin.update_user_by_id(user_id, {"password": data.new_password})
        try:
            email = user_email
            if email:
                resend.Emails.send({
                    "from": "BigDogg <info@bigdogg.nl>",
                    "to": [email],
                    "subject": "Je wachtwoord is gewijzigd",
                    "html": f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <tr><td style="background:#1B3A4B;padding:28px 40px;text-align:center;">
          <div style="font-size:26px;font-weight:900;color:#C9A96E;font-family:Arial,sans-serif;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:12px;margin-top:4px;">Slim boekhouden voor ZZP'ers</div>
        </td></tr>
        <tr><td style="padding:36px 40px;">
          <div style="font-size:22px;font-weight:bold;color:#1B3A4B;margin-bottom:16px;">&#x1F512; Wachtwoord gewijzigd</div>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 16px 0;">
            Je wachtwoord voor je BigDogg account is zojuist succesvol gewijzigd op {datetime.now().strftime("%d-%m-%Y om %H:%M")}.
          </p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 24px 0;">
            Als jij dit niet was, neem dan direct contact op via <a href="mailto:info@bigdogg.nl" style="color:#1B3A4B;">info@bigdogg.nl</a>.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="https://bigdogg.nl" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:8px;font-weight:bold;font-size:14px;">Ga naar BigDogg</a>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="background:#f5f3ef;padding:20px 40px;text-align:center;border-top:1px solid #E2DDD6;">
          <div style="color:#4A6572;font-size:12px;">BigDogg &middot; <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a></div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
                })
        except Exception:
            pass
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/delete-account")
async def delete_account(data: DeleteAccountRequest, request: Request):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        user_id = user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Grab email now, before we delete anything
    user_email = None
    try:
        user_email = user.user.email
    except Exception:
        pass

    # Re-prove the current password — a stolen JWT alone must not be
    # able to wipe the account.
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    _verify_current_password(user_email, data.current_password)

    try:
        # 1. Cancel Stripe subscription if active (non-fatal)
        try:
            sub_result = supabase.table("subscriptions") \
                .select("stripe_subscription_id") \
                .eq("user_id", user_id) \
                .execute()
            if sub_result.data:
                stripe_sub_id = sub_result.data[0].get("stripe_subscription_id")
                if stripe_sub_id:
                    stripe.Subscription.cancel(stripe_sub_id)
        except Exception as e:
            print(f"Stripe cancellation error (non-fatal): {e}")

        # 2. Delete invoice_lines first (no user_id column, linked via invoice_id)
        try:
            invoices = supabase.table("invoices").select("id").eq("user_id", user_id).execute()
            if invoices.data:
                for inv in invoices.data:
                    supabase.table("invoice_lines").delete().eq("invoice_id", inv["id"]).execute()
        except Exception:
            pass

        # 3. Delete all user data. Cover every table that stores a user_id
        # so nothing is left orphaned referencing a deleted auth user —
        # especially accountant_invites (would otherwise leave valid
        # portal tokens pointing at a deleted owner) and the various
        # notification / device / bank-link tables.
        for table in [
            "invoices", "expenses", "clients", "products", "user_profiles",
            "hours", "investments", "projects", "subscriptions",
            "accountant_invites", "client_invites", "quotes",
            "notifications", "user_devices", "fcm_device_tokens",
            "bank_transactions", "bank_transaction_links",
            "invoice_reminders", "referral_signups",
        ]:
            try:
                supabase.table(table).delete().eq("user_id", user_id).execute()
            except Exception:
                pass

        # 4. Send goodbye email (non-fatal)
        try:
            if user_email:
                resend.Emails.send({
                    "from": "BigDogg <info@bigdogg.nl>",
                    "to": [user_email],
                    "subject": "Je BigDogg account is verwijderd",
                    "html": f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <tr><td style="background:#1B3A4B;padding:28px 40px;text-align:center;">
          <div style="font-size:26px;font-weight:900;color:#C9A96E;font-family:Arial,sans-serif;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:12px;margin-top:4px;">Slim boekhouden voor ZZP'ers</div>
        </td></tr>
        <tr><td style="padding:36px 40px;">
          <div style="font-size:22px;font-weight:bold;color:#1B3A4B;margin-bottom:16px;">Account verwijderd</div>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 16px 0;">
            Je BigDogg account en alle bijbehorende gegevens zijn op {datetime.now().strftime("%d-%m-%Y om %H:%M")} succesvol en permanent verwijderd.
          </p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 16px 0;">
            Dit omvat al je facturen, klanten, kosten, producten en profielgegevens. Er zijn geen gegevens meer van jou opgeslagen bij BigDogg.
          </p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 24px 0;">
            Als je ooit opnieuw wilt starten kun je je altijd opnieuw aanmelden op <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a>.
          </p>
          <p style="color:#4A6572;font-size:14px;line-height:1.6;margin:0;">
            Bedankt dat je BigDogg hebt gebruikt. We wensen je veel succes als ondernemer!
          </p>
        </td></tr>
        <tr><td style="background:#f5f3ef;padding:20px 40px;text-align:center;border-top:1px solid #E2DDD6;">
          <div style="color:#4A6572;font-size:12px;">BigDogg &middot; <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a></div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
                })
        except Exception:
            pass

        # 5. Delete auth user via direct REST call (bypasses Python client version quirks)
        delete_resp = http_requests.delete(
            f"{settings.supabase_url}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": settings.supabase_service_key,
                "Authorization": f"Bearer {settings.supabase_service_key}",
            },
            timeout=10,
        )
        if delete_resp.status_code not in (200, 204):
            raise Exception(f"Auth delete failed: {delete_resp.status_code} — {delete_resp.text}")

        return {"message": "Account deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
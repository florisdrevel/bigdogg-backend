from fastapi import APIRouter, HTTPException, Request, status
import resend
from app.config import settings
resend.api_key = settings.resend_api_key
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import supabase
import stripe
import requests as http_requests
stripe.api_key = settings.stripe_secret_key

router = APIRouter()


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
async def login(data: LoginRequest):
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
async def change_password(request: Request):
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
        body = await request.json()
        new_password = body.get("new_password")
        if not new_password or len(new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        supabase.auth.admin.update_user_by_id(user_id, {"password": new_password})
        try:
            user_data = supabase.auth.get_user(token)
            email = user_data.user.email if user_data.user else None
            if email:
                from datetime import datetime
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
async def delete_account(request: Request):
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

        # 3. Delete all user data
        for table in ["invoices", "expenses", "clients", "products", "user_profiles",
                      "hours", "investments", "projects", "subscriptions"]:
            try:
                supabase.table(table).delete().eq("user_id", user_id).execute()
            except Exception:
                pass

        # 4. Send goodbye email (non-fatal)
        try:
            if user_email:
                from datetime import datetime
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
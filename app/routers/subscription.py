from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.database import supabase
from app.config import settings
from datetime import datetime, timezone, timedelta, date
import stripe
import json
import resend

router = APIRouter()
stripe.api_key = settings.stripe_secret_key
resend.api_key = settings.resend_api_key

APP_URL = "https://bigdogg.nl"
PRICE_AMOUNT = 999  # €9.99
PRICE_CURRENCY = "eur"

# BigDogg subscription expense (€9.99 incl. 21% BTW)
BIGDOGG_AMOUNT_EX_BTW = 8.26
BIGDOGG_BTW_AMOUNT = 1.73
BIGDOGG_BTW_RATE = 21


class CheckoutRequest(BaseModel):
    email: Optional[str] = None


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


def require_active_paid(user_id: str):
    """Raises 403 if user is not on active paid tier."""
    result = supabase.table("subscriptions")\
        .select("status")\
        .eq("user_id", user_id)\
        .execute()
    if not result.data:
        raise HTTPException(status_code=403, detail="paid_tier_required")
    status = result.data[0].get("status")
    if status != "active":
        raise HTTPException(status_code=403, detail="paid_tier_required")


@router.get("/status")
async def get_subscription_status(request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("subscriptions")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()

        if not result.data:
            new_sub = supabase.table("subscriptions").insert({
                "user_id": user_id,
            }).execute()
            sub = new_sub.data[0]
        else:
            sub = result.data[0]

        now = datetime.now(timezone.utc)
        trial_ends = datetime.fromisoformat(sub['trial_ends_at'].replace('Z', '+00:00'))

        if sub['status'] == 'trial':
            days_left = (trial_ends - now).days
            is_active = now < trial_ends
            return {
                "status": "trial",
                "is_active": is_active,
                "days_left": max(0, days_left),
                "trial_ends_at": sub['trial_ends_at'],
            }
        elif sub['status'] == 'active':
            return {
                "status": "active",
                "is_active": True,
                "days_left": None,
                "subscription_ends_at": sub.get('subscription_ends_at'),
            }
        else:
            return {
                "status": "expired",
                "is_active": False,
                "days_left": 0,
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/checkout")
async def create_checkout(request: Request, data: CheckoutRequest = None):
    user_id = get_user_id(request)
    try:
        email = data.email if data and data.email else None

        session_params = {
            "line_items": [{
                "price_data": {
                    "currency": PRICE_CURRENCY,
                    "product_data": {
                        "name": "Bigdogg Pro",
                        "description": "Monthly subscription — unlimited invoices, AI, expenses and more",
                    },
                    "unit_amount": PRICE_AMOUNT,
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }],
            "mode": "subscription",
            "success_url": f"{APP_URL}/#/dashboard?payment=success",
            "cancel_url": f"{APP_URL}/#/dashboard",
            "metadata": {"user_id": user_id},
        }

        if email:
            session_params["customer_email"] = email

        session = stripe.checkout.Session.create(**session_params)
        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _insert_bigdogg_expense(user_id: str, label: str) -> None:
    """Insert BigDogg Pro subscription as a bookkeeping expense for the user."""
    supabase.table("expenses").insert({
        "user_id": user_id,
        "description": "BigDogg Pro abonnement",
        "amount_ex_btw": BIGDOGG_AMOUNT_EX_BTW,
        "btw_amount": BIGDOGG_BTW_AMOUNT,
        "btw_rate": BIGDOGG_BTW_RATE,
        "expense_date": str(date.today()),
        "category": "Software & abonnementen",
    }).execute()
    print(f"BigDogg expense inserted for user {user_id} ({label})")


def _send_trial_expiry_email(email: str, name: str, days_left: int, checkout_url: str) -> None:
    """Send a trial expiry warning email in Dutch."""
    if days_left == 7:
        subject = "Je gratis proefperiode verloopt over 7 dagen"
        urgency_color = "#92400E"
        urgency_bg = "#FEF3C7"
        urgency_icon = "⏰"
        urgency_text = "Nog 7 dagen gratis"
        body_line = "Je gratis proefperiode van 30 dagen verloopt over <strong>7 dagen</strong>. Na afloop verlies je toegang tot al je facturen, klanten en financiële overzichten."
    else:  # 1 day
        subject = "Laatste dag — je proefperiode verloopt morgen"
        urgency_color = "#991B1B"
        urgency_bg = "#FEE2E2"
        urgency_icon = "🚨"
        urgency_text = "Nog 1 dag"
        body_line = "Je gratis proefperiode verloopt <strong>morgen</strong>. Abonneer je nu om toegang te behouden tot al je gegevens en BigDogg te blijven gebruiken."

    resend.Emails.send({
        "from": "BigDogg <info@bigdogg.nl>",
        "to": [email],
        "subject": subject,
        "html": f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr><td style="background:#1B3A4B;padding:28px 40px;text-align:center;">
          <div style="font-size:26px;font-weight:900;color:#C9A96E;font-family:Arial,sans-serif;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:12px;margin-top:4px;">Slim boekhouden voor ZZP'ers</div>
        </td></tr>

        <!-- Urgency banner -->
        <tr><td style="background:{urgency_bg};padding:16px 40px;text-align:center;border-bottom:1px solid #E2DDD6;">
          <div style="font-size:28px;">{urgency_icon}</div>
          <div style="color:{urgency_color};font-size:18px;font-weight:bold;margin-top:6px;">{urgency_text}</div>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:36px 40px;">
          <p style="color:#1B3A4B;font-size:16px;margin:0 0 12px 0;">Hoi {name},</p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 20px 0;">
            {body_line}
          </p>

          <!-- What you keep -->
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;border-radius:12px;margin-bottom:24px;">
            <tr><td style="background:#1B3A4B;padding:12px 20px;border-radius:12px 12px 0 0;">
              <span style="color:#C9A96E;font-weight:bold;font-size:13px;">WAT JE BEHOUDT MET BIGDOGG PRO</span>
            </td></tr>
            <tr><td style="padding:16px 20px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr><td style="padding:4px 0;color:#4A6572;font-size:14px;">✓&nbsp;&nbsp;Al je facturen en klantgegevens</td></tr>
                <tr><td style="padding:4px 0;color:#4A6572;font-size:14px;">✓&nbsp;&nbsp;Kwartaal BTW-overzicht en aangifte PDF</td></tr>
                <tr><td style="padding:4px 0;color:#4A6572;font-size:14px;">✓&nbsp;&nbsp;Jaarrapport met AI belastingtips</td></tr>
                <tr><td style="padding:4px 0;color:#4A6572;font-size:14px;">✓&nbsp;&nbsp;Historische factuur- en kostenimport</td></tr>
                <tr><td style="padding:4px 0;color:#4A6572;font-size:14px;">✓&nbsp;&nbsp;Betaallinks via Stripe op je facturen</td></tr>
              </table>
            </td></tr>
          </table>

          <!-- Price -->
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#1B3A4B;border-radius:10px;margin-bottom:24px;">
            <tr><td style="padding:16px 24px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="color:#ffffff;font-size:15px;">BigDogg Pro</td>
                  <td style="text-align:right;">
                    <span style="color:#C9A96E;font-size:22px;font-weight:bold;">€9,99</span>
                    <span style="color:#ffffff;opacity:0.6;font-size:13px;">/maand</span>
                  </td>
                </tr>
                <tr>
                  <td colspan="2" style="color:#ffffff;opacity:0.6;font-size:12px;padding-top:4px;">Altijd opzegbaar · iDEAL en creditcard</td>
                </tr>
              </table>
            </td></tr>
          </table>

          <!-- CTA -->
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="{checkout_url}" style="display:inline-block;background:#C9A96E;color:#ffffff;text-decoration:none;padding:16px 40px;border-radius:10px;font-weight:bold;font-size:16px;letter-spacing:0.3px;">
                Abonneer nu — €9,99/maand
              </a>
            </td></tr>
          </table>

          <p style="color:#4A6572;font-size:13px;line-height:1.6;margin:20px 0 0 0;text-align:center;">
            Of open de BigDogg app en ga naar <strong>Instellingen → Abonnement</strong>
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f5f3ef;padding:20px 40px;text-align:center;border-top:1px solid #E2DDD6;">
          <div style="color:#4A6572;font-size:12px;">BigDogg &middot; <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a></div>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>""",
    })


@router.post("/cron/trial-expiry")
async def send_trial_expiry_notifications(request: Request):
    """
    Daily cron job — sends trial expiry emails to users with 7 or 1 days left.
    Call with header: x-cron-secret: <your_cron_secret>
    Suggested schedule: daily at 09:00 Europe/Amsterdam
    """
    auth = request.headers.get("x-cron-secret", "")
    if auth != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    now = datetime.now(timezone.utc)
    sent_7 = 0
    sent_1 = 0
    errors = 0

    try:
        # Get all trial subscriptions
        result = supabase.table("subscriptions")\
            .select("user_id, trial_ends_at")\
            .eq("status", "trial")\
            .execute()

        trial_subs = result.data or []
        print(f"Trial expiry cron: checking {len(trial_subs)} trial users")

        for sub in trial_subs:
            try:
                user_id = sub["user_id"]
                trial_ends = datetime.fromisoformat(
                    sub["trial_ends_at"].replace("Z", "+00:00")
                )
                days_left = (trial_ends - now).days

                # Only notify at exactly 7 or 1 days left
                if days_left not in (7, 1):
                    continue

                # Get user email
                user_data = supabase.auth.admin.get_user_by_id(user_id)
                email = user_data.user.email if user_data.user else None
                if not email:
                    continue

                # Get user name
                profile_result = supabase.table("user_profiles")\
                    .select("full_name, business_name")\
                    .eq("id", user_id)\
                    .execute()
                profile = profile_result.data[0] if profile_result.data else {}
                name = profile.get("full_name") or profile.get("business_name") or email.split("@")[0]

                # Generate a fresh checkout URL for this user
                session = stripe.checkout.Session.create(
                    line_items=[{
                        "price_data": {
                            "currency": PRICE_CURRENCY,
                            "product_data": {"name": "Bigdogg Pro"},
                            "unit_amount": PRICE_AMOUNT,
                            "recurring": {"interval": "month"},
                        },
                        "quantity": 1,
                    }],
                    mode="subscription",
                    success_url=f"{APP_URL}/#/dashboard?payment=success",
                    cancel_url=f"{APP_URL}/#/dashboard",
                    metadata={"user_id": user_id},
                )

                _send_trial_expiry_email(email, name, days_left, session.url)

                if days_left == 7:
                    sent_7 += 1
                else:
                    sent_1 += 1

                print(f"Trial expiry email sent to {email} ({days_left} days left)")

            except Exception as e:
                errors += 1
                print(f"Trial expiry email error for user {sub.get('user_id')}: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "sent_7_day": sent_7,
        "sent_1_day": sent_1,
        "errors": errors,
        "checked": len(trial_subs),
    }


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if settings.stripe_webhook_secret and settings.stripe_webhook_secret != "whsec_placeholder":
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        else:
            event = json.loads(payload)
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return {"status": "ok"}

    try:
        event_type = event["type"]
        print(f"Webhook event: {event_type}")

        if event_type == "checkout.session.completed":
            session = event["data"]["object"]
            if hasattr(session, 'to_dict'):
                session = session.to_dict()
            elif not isinstance(session, dict):
                session = dict(session)

            metadata = session.get("metadata") or {}
            user_id = metadata.get("user_id")

            if user_id:
                ends_at = datetime.now(timezone.utc) + timedelta(days=30)
                existing = supabase.table("subscriptions")\
                    .select("id")\
                    .eq("user_id", user_id)\
                    .execute()

                if existing.data:
                    supabase.table("subscriptions")\
                        .update({
                            "status": "active",
                            "stripe_customer_id": session.get("customer"),
                            "stripe_subscription_id": session.get("subscription"),
                            "subscription_ends_at": ends_at.isoformat(),
                        })\
                        .eq("user_id", user_id)\
                        .execute()
                else:
                    supabase.table("subscriptions").insert({
                        "user_id": user_id,
                        "status": "active",
                        "stripe_customer_id": session.get("customer"),
                        "stripe_subscription_id": session.get("subscription"),
                        "subscription_ends_at": ends_at.isoformat(),
                    }).execute()

                # Insert first month's BigDogg expense
                try:
                    _insert_bigdogg_expense(user_id, "initial checkout")
                except Exception as e:
                    print(f"BigDogg expense insert error (non-fatal): {e}")

        elif event_type == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            if hasattr(invoice, 'to_dict'):
                invoice = invoice.to_dict()
            elif not isinstance(invoice, dict):
                invoice = dict(invoice)

            customer_id = invoice.get("customer")
            billing_reason = invoice.get("billing_reason", "")

            if customer_id:
                ends_at = datetime.now(timezone.utc) + timedelta(days=30)
                supabase.table("subscriptions")\
                    .update({
                        "status": "active",
                        "subscription_ends_at": ends_at.isoformat(),
                    })\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()

                # Insert expense on renewal only (initial handled by checkout.session.completed)
                if billing_reason == "subscription_cycle":
                    try:
                        sub_row = supabase.table("subscriptions")\
                            .select("user_id")\
                            .eq("stripe_customer_id", customer_id)\
                            .execute()
                        if sub_row.data:
                            _insert_bigdogg_expense(sub_row.data[0]["user_id"], "renewal")
                    except Exception as e:
                        print(f"BigDogg expense insert error (non-fatal): {e}")

        elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
            subscription = event["data"]["object"]
            if hasattr(subscription, 'to_dict'):
                subscription = subscription.to_dict()
            elif not isinstance(subscription, dict):
                subscription = dict(subscription)

            customer_id = subscription.get("customer")
            if customer_id:
                supabase.table("subscriptions")\
                    .update({"status": "expired"})\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()

        elif event_type == "invoice.payment_failed":
            invoice = event["data"]["object"]
            if hasattr(invoice, 'to_dict'):
                invoice = invoice.to_dict()
            elif not isinstance(invoice, dict):
                invoice = dict(invoice)

            customer_id = invoice.get("customer")
            if customer_id:
                supabase.table("subscriptions")\
                    .update({"status": "expired"})\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()

    except Exception as e:
        print(f"Webhook processing error: {str(e)}")

    return {"status": "ok"}
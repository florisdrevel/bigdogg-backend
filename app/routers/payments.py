from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.config import settings
import stripe
import json

router = APIRouter()
stripe.api_key = settings.stripe_secret_key

APP_URL = "https://bigdogg.nl"


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


def get_profile(user_id: str) -> dict:
    result = supabase.table("user_profiles")\
        .select("*")\
        .eq("id", user_id)\
        .execute()
    return result.data[0] if result.data else {}


def _mark_invoice_paid(invoice_id: str):
    """Mark an invoice as paid and disable its payment link."""
    try:
        supabase.table("invoices")\
            .update({"status": "paid"})\
            .eq("id", invoice_id)\
            .execute()

        # Deactivate the payment link on Stripe so it can't be paid twice
        inv = supabase.table("invoices")\
            .select("payment_link_id, user_id")\
            .eq("id", invoice_id)\
            .single()\
            .execute()

        if inv.data and inv.data.get("payment_link_id"):
            payment_link_id = inv.data["payment_link_id"]
            user_id = inv.data["user_id"]
            profile = get_profile(user_id)
            account_id = profile.get("stripe_connect_account_id")
            if account_id:
                try:
                    stripe.PaymentLink.modify(
                        payment_link_id,
                        active=False,
                        stripe_account=account_id,
                    )
                    print(f"Payment link {payment_link_id} deactivated")
                except Exception as e:
                    print(f"Could not deactivate payment link: {e}")

        # Send paid notification email to the user
        try:
            full_inv = supabase.table("invoices")                .select("invoice_number, total_incl_btw, subtotal_ex_btw, btw_amount, client_name, clients(contact_name, company_name)")                .eq("id", invoice_id)                .single()                .execute()
            if full_inv.data and inv.data:
                uid = inv.data["user_id"]
                user = supabase.auth.admin.get_user_by_id(uid)
                email = user.user.email if user.user else None
                if email:
                    inv_data = full_inv.data
                    inv_num = inv_data.get("invoice_number", "")
                    total = inv_data.get("total_incl_btw", 0)
                    subtotal = inv_data.get("subtotal_ex_btw", 0)
                    btw = inv_data.get("btw_amount", 0)
                    client = inv_data.get("clients", {}) or {}
                    client_name = client.get("company_name") or client.get("contact_name") or inv_data.get("client_name") or "je klant"
                    profile_data = get_profile(uid)
                    business_name = profile_data.get("business_name") or profile_data.get("full_name") or "BigDogg gebruiker"
                    resend.Emails.send({
                        "from": "BigDogg <info@bigdogg.nl>",
                        "to": [email],
                        "subject": f"\U0001f4b0 Factuur {inv_num} is betaald!",
                        "html": f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr><td style="background:#1B3A4B;padding:32px 40px;text-align:center;">
          <div style="font-size:28px;font-weight:900;color:#C9A96E;letter-spacing:-0.5px;font-family:Arial,sans-serif;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:13px;margin-top:4px;">Slim boekhouden voor ZZP'ers</div>
        </td></tr>
        <!-- Success banner -->
        <tr><td style="background:#166534;padding:20px 40px;text-align:center;">
          <div style="font-size:36px;">&#x1F4B0;</div>
          <div style="color:#ffffff;font-size:22px;font-weight:bold;margin-top:8px;">Betaling ontvangen!</div>
          <div style="color:#bbf7d0;font-size:14px;margin-top:4px;">Je factuur is succesvol betaald</div>
        </td></tr>
        <!-- Body -->
        <tr><td style="padding:40px;">
          <p style="color:#1B3A4B;font-size:16px;margin:0 0 8px 0;">Hoi {business_name},</p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 24px 0;">
            Goed nieuws — <strong style="color:#1B3A4B;">{client_name}</strong> heeft zojuist je factuur betaald. Het bedrag wordt verrekend via Stripe naar je bankrekening.
          </p>
          <!-- Invoice details box -->
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;border-radius:12px;overflow:hidden;margin-bottom:24px;">
            <tr><td style="background:#1B3A4B;padding:14px 20px;">
              <span style="color:#C9A96E;font-weight:bold;font-size:14px;letter-spacing:0.5px;">FACTUURDETAILS</span>
            </td></tr>
            <tr><td style="padding:20px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="color:#4A6572;font-size:14px;padding-bottom:10px;">Factuurnummer</td>
                  <td style="color:#1B3A4B;font-size:14px;font-weight:bold;text-align:right;padding-bottom:10px;">{inv_num}</td>
                </tr>
                <tr>
                  <td style="color:#4A6572;font-size:14px;padding-bottom:10px;">Klant</td>
                  <td style="color:#1B3A4B;font-size:14px;text-align:right;padding-bottom:10px;">{client_name}</td>
                </tr>
                <tr>
                  <td style="color:#4A6572;font-size:14px;padding-bottom:10px;">Subtotaal ex BTW</td>
                  <td style="color:#1B3A4B;font-size:14px;text-align:right;padding-bottom:10px;">&euro; {float(subtotal):,.2f}</td>
                </tr>
                <tr>
                  <td style="color:#4A6572;font-size:14px;padding-bottom:10px;">BTW</td>
                  <td style="color:#1B3A4B;font-size:14px;text-align:right;padding-bottom:10px;">&euro; {float(btw):,.2f}</td>
                </tr>
                <tr style="border-top:2px solid #C9A96E;">
                  <td style="color:#1B3A4B;font-size:16px;font-weight:bold;padding-top:12px;">Totaal ontvangen</td>
                  <td style="color:#166534;font-size:20px;font-weight:bold;text-align:right;padding-top:12px;">&euro; {float(total):,.2f}</td>
                </tr>
              </table>
            </td></tr>
          </table>
          <p style="color:#4A6572;font-size:14px;line-height:1.6;margin:0 0 24px 0;">
            Je kunt de factuur terugvinden in de BigDogg app onder je factuuroverzicht.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="https://bigdogg.nl" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:bold;font-size:15px;">Bekijk in BigDogg</a>
            </td></tr>
          </table>
        </td></tr>
        <!-- Footer -->
        <tr><td style="background:#f5f3ef;padding:24px 40px;text-align:center;border-top:1px solid #E2DDD6;">
          <div style="color:#4A6572;font-size:12px;line-height:1.6;">
            BigDogg &middot; Slim boekhouden voor ZZP'ers &middot; <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a>
          </div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>""",
                    })
                    print(f"Payment notification email sent to {email}")
        except Exception as email_err:
            print(f"Could not send payment notification email: {email_err}")

        print(f"Invoice {invoice_id} marked as paid")
    except Exception as e:
        print(f"Error marking invoice paid: {e}")


@router.post("/connect")
async def create_connect_link(request: Request):
    user_id = get_user_id(request)
    profile = get_profile(user_id)

    try:
        account_id = profile.get("stripe_connect_account_id")

        if not account_id:
            account = stripe.Account.create(
                type="express",
                country="NL",
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                metadata={"user_id": user_id},
            )
            account_id = account.id
            supabase.table("user_profiles")\
                .update({"stripe_connect_account_id": account_id})\
                .eq("id", user_id)\
                .execute()

        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=f"{APP_URL}/dashboard?stripe=refresh",
            return_url=f"{APP_URL}/dashboard?stripe=success",
            type="account_onboarding",
        )

        return {"url": link.url, "account_id": account_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connect/status")
async def get_connect_status(request: Request):
    user_id = get_user_id(request)
    profile = get_profile(user_id)

    account_id = profile.get("stripe_connect_account_id")
    if not account_id:
        return {"connected": False, "enabled": False}

    try:
        account = stripe.Account.retrieve(account_id)
        enabled = account.charges_enabled and account.payouts_enabled
        supabase.table("user_profiles")\
            .update({"stripe_connect_enabled": enabled})\
            .eq("id", user_id)\
            .execute()
        return {
            "connected": True,
            "enabled": enabled,
            "account_id": account_id,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
        }
    except Exception as e:
        return {"connected": False, "enabled": False, "error": str(e)}


@router.post("/invoice/{invoice_id}/payment-link")
async def create_payment_link(invoice_id: str, request: Request):
    user_id = get_user_id(request)
    profile = get_profile(user_id)

    account_id = profile.get("stripe_connect_account_id")
    if not account_id:
        raise HTTPException(status_code=400, detail="No Stripe account connected")

    if not profile.get("stripe_connect_enabled"):
        try:
            account = stripe.Account.retrieve(account_id)
            if not account.charges_enabled:
                raise HTTPException(
                    status_code=400,
                    detail="Stripe account not fully set up yet"
                )
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=str(e))

    try:
        inv_result = supabase.table("invoices")\
            .select("*")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not inv_result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice = inv_result.data

        # Return existing link if already created
        if invoice.get("payment_link"):
            return {
                "payment_link": invoice["payment_link"],
                "payment_link_id": invoice["payment_link_id"],
            }

        total_cents = int(float(invoice["total_incl_btw"]) * 100)
        invoice_number = invoice["invoice_number"]
        business_name = profile.get("business_name") or profile.get("full_name") or "BigDogg"

        product = stripe.Product.create(
            name=f"Factuur {invoice_number} — {business_name}",
            stripe_account=account_id,
        )

        price = stripe.Price.create(
            product=product.id,
            unit_amount=total_cents,
            currency="eur",
            stripe_account=account_id,
        )

        payment_link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            metadata={
                "invoice_id": invoice_id,
                "user_id": user_id,
                "invoice_number": invoice_number,
            },
            after_completion={
                "type": "hosted_confirmation",
                "hosted_confirmation": {
                    "custom_message": f"Bedankt voor je betaling van factuur {invoice_number}."
                }
            },
            stripe_account=account_id,
        )

        supabase.table("invoices")\
            .update({
                "payment_link": payment_link.url,
                "payment_link_id": payment_link.id,
            })\
            .eq("id", invoice_id)\
            .execute()

        return {
            "payment_link": payment_link.url,
            "payment_link_id": payment_link.id,
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook/connect")
async def connect_webhook(request: Request):
    """
    Handles Stripe Connect webhooks — payment completions on
    connected accounts. Register this URL in Stripe Dashboard:
    https://api.bigdogg.nl/api/v1/payments/webhook/connect
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        # Use connect webhook secret if set, fall back to main secret
        secret = settings.stripe_connect_webhook_secret or settings.stripe_webhook_secret
        if secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, secret
            )
        else:
            event = json.loads(payload)
    except stripe.error.SignatureVerificationError as e:
        print(f"Connect webhook signature error: {e}")
        return {"status": "ok"}
    except Exception as e:
        print(f"Connect webhook parse error: {e}")
        return {"status": "ok"}

    try:
        event_type = event["type"]
        data = event["data"]["object"]
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
        elif not isinstance(data, dict):
            data = dict(data)

        print(f"Connect webhook received: {event_type}")

        # checkout.session.completed fires when client pays via payment link
        if event_type == "checkout.session.completed":
            metadata = data.get("metadata") or {}
            invoice_id = metadata.get("invoice_id")
            payment_status = data.get("payment_status")
            print(f"Checkout completed — invoice_id={invoice_id}, payment_status={payment_status}")
            if invoice_id and payment_status == "paid":
                _mark_invoice_paid(invoice_id)

        # payment_intent.succeeded fires for direct payments
        elif event_type == "payment_intent.succeeded":
            metadata = data.get("metadata") or {}
            invoice_id = metadata.get("invoice_id")
            print(f"PaymentIntent succeeded — invoice_id={invoice_id}")
            if invoice_id:
                _mark_invoice_paid(invoice_id)

        # charge.succeeded as fallback
        elif event_type == "charge.succeeded":
            metadata = data.get("metadata") or {}
            invoice_id = metadata.get("invoice_id")
            print(f"Charge succeeded — invoice_id={invoice_id}")
            if invoice_id:
                _mark_invoice_paid(invoice_id)

    except Exception as e:
        print(f"Connect webhook processing error: {e}")

    return {"status": "ok"}


@router.post("/webhook")
async def main_webhook(request: Request):
    """
    Handles main Stripe webhooks — BigDogg subscription payments.
    This is the existing webhook for subscription management.
    Register this URL in Stripe Dashboard:
    https://api.bigdogg.nl/api/v1/payments/webhook
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if settings.stripe_webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        else:
            event = json.loads(payload)
    except stripe.error.SignatureVerificationError as e:
        print(f"Main webhook signature error: {e}")
        return {"status": "ok"}
    except Exception as e:
        print(f"Main webhook parse error: {e}")
        return {"status": "ok"}

    try:
        event_type = event["type"]
        data = event["data"]["object"]
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
        elif not isinstance(data, dict):
            data = dict(data)

        print(f"Main webhook received: {event_type}")

        if event_type == "checkout.session.completed":
            metadata = data.get("metadata") or {}
            user_id = metadata.get("user_id")
            invoice_id = metadata.get("invoice_id")

            # If this is an invoice payment (from connect), handle it
            if invoice_id:
                payment_status = data.get("payment_status")
                if payment_status == "paid":
                    _mark_invoice_paid(invoice_id)

            # If this is a BigDogg subscription payment
            elif user_id:
                from datetime import datetime, timezone, timedelta
                ends_at = datetime.now(timezone.utc) + timedelta(days=30)
                existing = supabase.table("subscriptions")\
                    .select("id")\
                    .eq("user_id", user_id)\
                    .execute()
                if existing.data:
                    supabase.table("subscriptions")\
                        .update({
                            "status": "active",
                            "stripe_customer_id": data.get("customer"),
                            "stripe_subscription_id": data.get("subscription"),
                            "subscription_ends_at": ends_at.isoformat(),
                        })\
                        .eq("user_id", user_id)\
                        .execute()
                else:
                    supabase.table("subscriptions").insert({
                        "user_id": user_id,
                        "status": "active",
                        "stripe_customer_id": data.get("customer"),
                        "stripe_subscription_id": data.get("subscription"),
                        "subscription_ends_at": ends_at.isoformat(),
                    }).execute()

        elif event_type == "invoice.payment_succeeded":
            customer_id = data.get("customer")
            if customer_id:
                from datetime import datetime, timezone, timedelta
                ends_at = datetime.now(timezone.utc) + timedelta(days=30)
                supabase.table("subscriptions")\
                    .update({
                        "status": "active",
                        "subscription_ends_at": ends_at.isoformat(),
                    })\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()

        elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
            customer_id = data.get("customer")
            if customer_id:
                supabase.table("subscriptions")\
                    .update({"status": "expired"})\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()

        elif event_type == "invoice.payment_failed":
            customer_id = data.get("customer")
            if customer_id:
                supabase.table("subscriptions")\
                    .update({"status": "expired"})\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()

    except Exception as e:
        print(f"Main webhook processing error: {e}")

    return {"status": "ok"}
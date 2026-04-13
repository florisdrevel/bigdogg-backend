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
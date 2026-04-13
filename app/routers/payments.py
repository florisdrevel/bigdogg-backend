from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.config import settings
import stripe

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


@router.post("/connect")
async def create_connect_link(request: Request):
    user_id = get_user_id(request)
    profile = get_profile(user_id)

    try:
        account_id = profile.get("stripe_connect_account_id")

        # Create account if doesn't exist
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

        # Create onboarding link
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
        # Update enabled status in DB
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
        # Check live status
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
        # Get invoice
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
        client_name = invoice.get("client_name") or "Client"
        business_name = profile.get("business_name") or profile.get("full_name") or "BigDogg"

        # Create product on connected account
        product = stripe.Product.create(
            name=f"Factuur {invoice_number} — {business_name}",
            stripe_account=account_id,
        )

        # Create price
        price = stripe.Price.create(
            product=product.id,
            unit_amount=total_cents,
            currency="eur",
            stripe_account=account_id,
        )

        # Create payment link
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

        # Save to invoice
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
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if settings.stripe_webhook_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        else:
            import json
            event = json.loads(payload)
    except Exception as e:
        print(f"Connect webhook error: {e}")
        return {"status": "ok"}

    try:
        event_type = event["type"]
        data = event["data"]["object"]
        if hasattr(data, 'to_dict'):
            data = data.to_dict()

        print(f"Connect webhook: {event_type}")

        if event_type == "payment_link.completed" or event_type == "checkout.session.completed":
            metadata = data.get("metadata") or {}
            invoice_id = metadata.get("invoice_id")
            if invoice_id:
                supabase.table("invoices")\
                    .update({"status": "paid"})\
                    .eq("id", invoice_id)\
                    .execute()
                print(f"Invoice {invoice_id} marked as paid via payment link")

    except Exception as e:
        print(f"Connect webhook processing error: {e}")

    return {"status": "ok"}
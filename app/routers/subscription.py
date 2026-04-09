from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.config import settings
from datetime import datetime, timezone, timedelta
import stripe

router = APIRouter()
stripe.api_key = settings.stripe_secret_key

APP_URL = "https://bigdogg.nl"
PRICE_AMOUNT = 1200
PRICE_CURRENCY = "eur"


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


def get_user_email(user_id: str) -> str:
    try:
        user = supabase.auth.admin.get_user_by_id(user_id)
        return user.user.email
    except Exception:
        return ""


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
async def create_checkout(request: Request):
    user_id = get_user_id(request)
    try:
        email = get_user_email(user_id)

        session = stripe.checkout.Session.create(
            payment_method_types=["card", "ideal"],
            line_items=[{
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
            mode="subscription",
            customer_email=email,
            success_url=f"{APP_URL}/#/dashboard?payment=success",
            cancel_url=f"{APP_URL}/#/dashboard",
            metadata={"user_id": user_id},
        )

        return {"checkout_url": session.url, "session_id": session.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except Exception:
        return {"status": "ok"}

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")

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
                        "subscription_ends_at": ends_at.isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    })\
                    .eq("user_id", user_id)\
                    .execute()
            else:
                supabase.table("subscriptions").insert({
                    "user_id": user_id,
                    "status": "active",
                    "subscription_ends_at": ends_at.isoformat(),
                }).execute()

    return {"status": "ok"}
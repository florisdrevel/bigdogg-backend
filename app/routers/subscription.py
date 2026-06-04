from fastapi import APIRouter, HTTPException, Request
from app.services.cron_auth import require_cron_secret
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
PRICE_CURRENCY = "eur"

# Subscription tiers (cents).
PRICE_MONTHLY = 1199   # €11.99 / month
PRICE_YEARLY = 11988   # €119.88 / year — exactly 12 × €9.99 so marketing
                       # can keep "from €9,99/maand" on the yearly plan.

# Legacy alias — older code paths still reference PRICE_AMOUNT for the
# monthly recurring price (e.g. referral-bonus Stripe credits).
PRICE_AMOUNT = PRICE_MONTHLY

# BigDogg subscription expense (€11.99 incl. 21% BTW)
BIGDOGG_AMOUNT_EX_BTW = 9.91
BIGDOGG_BTW_AMOUNT = 2.08
BIGDOGG_BTW_RATE = 21

# BigDogg yearly subscription expense (€119.88 incl. 21% BTW)
BIGDOGG_YEAR_AMOUNT_EX_BTW = 99.07
BIGDOGG_YEAR_BTW_AMOUNT = 20.81

ALLOWED_PLANS = {"monthly", "yearly"}


class CheckoutRequest(BaseModel):
    # 'monthly' | 'yearly'. Defaults to monthly so legacy clients that
    # don't pass a plan keep working unchanged.
    plan: Optional[str] = "monthly"
    email: Optional[str] = None


ALLOWED_CANCEL_REASONS = {
    "too_expensive",
    "not_using",
    "missing_feature",
    "found_alternative",
    "stopped_freelancing",
    "other",
}
# Reasons that get a retention save offer. Skipped for users who stopped
# freelancing (no point retaining a non-customer) and for missing-feature
# (their signal is the feature request itself, not a discount).
REASONS_WITH_OFFER = {
    "too_expensive",
    "not_using",
    "found_alternative",
    "other",
}
RETENTION_OFFER_MONTHS = 3
RETENTION_COOLDOWN_DAYS = 365  # 1 offer per user per year


class CancelRequest(BaseModel):
    reason: str
    comment: Optional[str] = None
    accept_offer: bool = False


def _user_has_recent_offer(user_id: str) -> bool:
    """Has this user accepted a retention offer in the last
    RETENTION_COOLDOWN_DAYS? If yes, the next cancel attempt skips the
    offer step — prevents farming free months in a loop.
    """
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=RETENTION_COOLDOWN_DAYS)
    ).isoformat()
    result = supabase.table("subscription_cancellation_events")\
        .select("id")\
        .eq("user_id", user_id)\
        .eq("outcome", "offer_accepted")\
        .gte("happened_at", cutoff)\
        .limit(1)\
        .execute()
    return bool(result.data)


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
    """Raises 403 if the user has no usable subscription.

    "Active" covers monthly and yearly subscribers plus the
    referral-bonus grace period.
    """
    result = supabase.table("subscriptions")\
        .select("status, bonus_active_until")\
        .eq("user_id", user_id)\
        .execute()
    if not result.data:
        raise HTTPException(status_code=403, detail="paid_tier_required")
    row = result.data[0]
    if row.get("status") == "active":
        return
    bonus_until = row.get("bonus_active_until")
    if bonus_until:
        try:
            until = datetime.fromisoformat(
                bonus_until.replace("Z", "+00:00")
            )
            if until > datetime.now(timezone.utc):
                return
        except Exception:
            pass
    raise HTTPException(status_code=403, detail="paid_tier_required")


def get_user_plan(user_id: str) -> Optional[str]:
    """Returns the current plan slug ('monthly' | 'yearly') or None if
    the user has no subscription row."""
    result = supabase.table("subscriptions")\
        .select("plan")\
        .eq("user_id", user_id)\
        .execute()
    if not result.data:
        return None
    return result.data[0].get("plan")




# ─── Referral bonus granting ──────────────────────────────
# Pyramid-style: per 2 successful signups via the user's referral code,
# the user earns 1 free pro month. Capped at 3 lifetime bonuses.
REFERRAL_BONUS_PER_N_SIGNUPS = 2
REFERRAL_BONUS_MAX_GRANTS = 3
REFERRAL_BONUS_DAYS = 30


def maybe_grant_referral_bonus(referrer_user_id: str) -> dict:
    """Recomputes the referrer's bonus eligibility and grants any owed.

    Returns a dict with the resulting state for callers to surface in /stats:
        {
            "signups": int,
            "eligible": int,        # bonuses owed in total (capped at 3)
            "applied": int,         # bonuses we have now applied
            "newly_granted": int,   # how many we just granted in this call
            "bonus_active_until": Optional[isoformat],
        }

    Idempotent: calling twice in a row only grants new bonuses on the first call.
    Failures are logged and the function returns gracefully without raising.
    """
    state = {
        "signups": 0,
        "eligible": 0,
        "applied": 0,
        "newly_granted": 0,
        "bonus_active_until": None,
    }
    try:
        ref_row = supabase.table("referrals")\
            .select("code")\
            .eq("referrer_user_id", referrer_user_id)\
            .execute()
        if not ref_row.data:
            return state
        code = ref_row.data[0]["code"]

        signups_result = supabase.table("referral_signups")\
            .select("id")\
            .eq("referrer_code", code)\
            .execute()
        signup_count = len(signups_result.data or [])
        eligible = min(
            REFERRAL_BONUS_MAX_GRANTS,
            signup_count // REFERRAL_BONUS_PER_N_SIGNUPS,
        )

        sub = supabase.table("subscriptions")\
            .select(
                "status, bonus_active_until, bonus_months_applied, "
                "stripe_customer_id"
            )\
            .eq("user_id", referrer_user_id)\
            .execute()
        if not sub.data:
            return state
        sub_row = sub.data[0]
        applied = sub_row.get("bonus_months_applied") or 0
        current_until = sub_row.get("bonus_active_until")
        state["signups"] = signup_count
        state["eligible"] = eligible
        state["applied"] = applied
        state["bonus_active_until"] = current_until

        if eligible <= applied:
            return state

        bonuses_to_grant = eligible - applied
        status = sub_row.get("status")

        # Strategy: paid users get a Stripe credit (saves them money on the
        # next invoice). If the Stripe call fails for any reason — bad
        # customer_id, test/live mismatch, transient API error — we fall
        # back to extending bonus_active_until so the tracking is never lost
        # and the user always sees the counter advance.
        stripe_credit_applied = False
        if status == "active":
            customer_id = sub_row.get("stripe_customer_id")
            if customer_id:
                try:
                    stripe.Customer.create_balance_transaction(
                        customer_id,
                        amount=-PRICE_AMOUNT * bonuses_to_grant,
                        currency=PRICE_CURRENCY,
                        description=(
                            f"BigDogg referral bonus: "
                            f"{bonuses_to_grant} maand(en) gratis"
                        ),
                    )
                    stripe_credit_applied = True
                    print(
                        f"[referral-bonus] granted {bonuses_to_grant} Stripe "
                        f"credit(s) to paid user {referrer_user_id}"
                    )
                except Exception as stripe_err:
                    print(
                        f"[referral-bonus] Stripe credit failed for "
                        f"{referrer_user_id}: {stripe_err}. "
                        "Falling back to bonus_active_until extension."
                    )
            else:
                print(
                    f"[referral-bonus] paid user {referrer_user_id} has no "
                    "stripe_customer_id; falling back to "
                    "bonus_active_until extension."
                )

        if not stripe_credit_applied:
            # Trial users, paid-but-broken-Stripe users, expired users —
            # extend bonus_active_until so the bonus is always tracked.
            now = datetime.now(timezone.utc)
            base = now
            if current_until:
                try:
                    cu = datetime.fromisoformat(
                        current_until.replace("Z", "+00:00")
                    )
                    if cu > base:
                        base = cu
                except Exception:
                    pass
            new_until = base + timedelta(
                days=REFERRAL_BONUS_DAYS * bonuses_to_grant
            )
            supabase.table("subscriptions")\
                .update({"bonus_active_until": new_until.isoformat()})\
                .eq("user_id", referrer_user_id)\
                .execute()
            state["bonus_active_until"] = new_until.isoformat()
            print(
                f"[referral-bonus] extended bonus_active_until to "
                f"{new_until.isoformat()} (+{bonuses_to_grant} month(s)) "
                f"for {referrer_user_id}"
            )

        # Persist applied count regardless of which path applied the bonus
        supabase.table("subscriptions")\
            .update({"bonus_months_applied": eligible})\
            .eq("user_id", referrer_user_id)\
            .execute()

        state["applied"] = eligible
        state["newly_granted"] = bonuses_to_grant
    except Exception as e:
        print(
            f"[referral-bonus] grant error for {referrer_user_id}: "
            f"{type(e).__name__}: {e}"
        )
    return state


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

        plan = sub.get('plan')

        if sub['status'] == 'trial':
            # Only parse trial_ends_at on trial rows. Active/expired rows
            # may have it as null after an upgrade, and `.replace()` on
            # None throws AttributeError before the status branch returns.
            trial_ends_raw = sub.get('trial_ends_at')
            if not trial_ends_raw:
                return {"status": "trial", "is_active": False, "days_left": 0, "plan": plan}
            trial_ends = datetime.fromisoformat(trial_ends_raw.replace('Z', '+00:00'))
            days_left = (trial_ends - now).days
            is_active = now < trial_ends
            return {
                "status": "trial",
                "is_active": is_active,
                "days_left": max(0, days_left),
                "trial_ends_at": trial_ends_raw,
                "plan": plan,
            }
        elif sub['status'] == 'active':
            return {
                "status": "active",
                "is_active": True,
                "days_left": None,
                "subscription_ends_at": sub.get('subscription_ends_at'),
                "plan": plan,
            }
        else:
            return {
                "status": "expired",
                "is_active": False,
                "days_left": 0,
                "plan": plan,
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/activated")
async def check_activation(request: Request):
    """Lightweight subscription-status probe used by the mobile app
    after the in-app web view closes. The native client polls this once
    webhook processing has had a moment to land so it can auto-dismiss
    the paywall and grant full access without an app restart.

    Returns:
        {"active": true|false, "plan": "monthly"|None}

    Authenticated only — user_id is derived from the verified JWT, not
    from a query parameter. The pre-fix version accepted ?user_id=…
    with no auth, which let anyone enumerate paying customers by walking
    UUIDs.
    """
    user_id = get_user_id(request)
    try:
        result = supabase.table("subscriptions")\
            .select("status, bonus_active_until")\
            .eq("user_id", user_id)\
            .execute()
        if not result.data:
            return {"active": False, "plan": None}
        row = result.data[0]
        if row.get("status") == "active":
            return {"active": True, "plan": "monthly"}
        # A referral bonus counts as active for entitlement purposes —
        # match the rule used by require_active_paid().
        bonus_until = row.get("bonus_active_until")
        if bonus_until:
            try:
                until = datetime.fromisoformat(
                    bonus_until.replace("Z", "+00:00")
                )
                if until > datetime.now(timezone.utc):
                    return {"active": True, "plan": "monthly"}
            except Exception:
                pass
        return {"active": False, "plan": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkout")
async def create_checkout(request: Request, data: CheckoutRequest = None):
    """Create a Stripe Checkout session for the chosen recurring plan.

    Plan branches:
      - monthly: €11.99/month recurring
      - yearly:  €119.99/year recurring (~2 months free vs monthly)
    """
    user_id = get_user_id(request)
    plan = (data.plan if data and data.plan else "monthly").lower()
    if plan not in ALLOWED_PLANS:
        raise HTTPException(status_code=400, detail="Unknown plan")

    if plan == "monthly":
        unit_amount = PRICE_MONTHLY
        interval = "month"
        product_name = "BigDogg Pro — Maandelijks"
        product_desc = (
            "Maandabonnement — onbeperkt facturen, AI, kosten en meer"
        )
    else:  # yearly
        unit_amount = PRICE_YEARLY
        interval = "year"
        product_name = "BigDogg Pro — Jaarlijks"
        product_desc = (
            "Jaarabonnement — onbeperkt facturen, AI, kosten en meer "
            "(2 maanden korting t.o.v. maandelijks)"
        )

    # If this user already has an active Stripe subscription, cancel it
    # immediately before creating the new one. Otherwise switching plans
    # (monthly → yearly or vice versa) creates a *second* subscription
    # while the old one keeps billing — the user thinks they're on
    # yearly but Stripe is still charging them monthly. Pro-rate so they
    # get refunded for unused time on the old plan.
    existing = supabase.table("subscriptions")\
        .select("stripe_subscription_id")\
        .eq("user_id", user_id)\
        .execute()
    if existing.data:
        old_sub_id = existing.data[0].get("stripe_subscription_id")
        if old_sub_id:
            try:
                stripe.Subscription.delete(old_sub_id, prorate=True)
                print(
                    f"Cancelled existing Stripe subscription {old_sub_id} "
                    f"for {user_id} before creating new {plan} sub"
                )
            except stripe.error.InvalidRequestError as e:
                # Already cancelled / unknown id — safe to ignore.
                print(f"Old sub cancel skipped (non-fatal): {e}")
            except stripe.error.StripeError as e:
                # Don't block the new sub on a Stripe hiccup, but log it.
                print(f"Old sub cancel failed (non-fatal): {e}")

    try:
        email = data.email if data and data.email else None
        session_params = {
            "line_items": [{
                "price_data": {
                    "currency": PRICE_CURRENCY,
                    "product_data": {
                        "name": product_name,
                        "description": product_desc,
                    },
                    "unit_amount": unit_amount,
                    "recurring": {"interval": interval},
                },
                "quantity": 1,
            }],
            "mode": "subscription",
            "success_url": f"{APP_URL}/#/payment-success?kind=subscription",
            "cancel_url": f"{APP_URL}/#/pricing",
            "metadata": {"user_id": user_id, "plan": plan},
            # Also tag the resulting subscription itself (not just the
            # session) so future invoice-renewal webhooks can read the
            # plan without re-reading our DB.
            "subscription_data": {
                "metadata": {"user_id": user_id, "plan": plan},
            },
        }
        if email:
            session_params["customer_email"] = email

        session = stripe.checkout.Session.create(**session_params)
        return {
            "plan": plan,
            "checkout_url": session.url,
            "session_id": session.id,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/portal")
async def create_portal_session(request: Request):
    """Stripe Billing Portal handoff for monthly/yearly subscribers.

    Returns one of:
      - {"url": "<stripe portal URL>"}          → web redirects to Stripe
      - {"url": null, "status": "legacy_active",
         "plan": "monthly"|"yearly"|None}       → user is active but has
        no Stripe customer record (e.g. admin-flipped row or pre-Stripe
        signup). Web surfaces a "subscription active, contact support
        to manage billing" status page rather than steering them to
        upgrade — they're already paid up.

    404 when there's no subscription row at all.
    """
    user_id = get_user_id(request)
    result = supabase.table("subscriptions")\
        .select("stripe_customer_id, plan, status")\
        .eq("user_id", user_id)\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="No subscription found")
    row = result.data[0]
    customer_id = row.get("stripe_customer_id")
    status = row.get("status")
    plan = row.get("plan")

    if not customer_id:
        # Legacy / admin-activated row. Don't 400 — just tell the web
        # layer the user is active without a Stripe customer so it can
        # render the right status page.
        return {
            "url": None,
            "status": "legacy_active" if status == "active" else (status or "unknown"),
            "plan": plan,
        }
    try:
        portal = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{APP_URL}/#/dashboard",
        )
        return {"url": portal.url, "status": status, "plan": plan}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")


@router.get("/usage-summary")
async def get_usage_summary(request: Request):
    """Stats shown on step 1 of the cancel flow ("don't go yet"). Keeps
    the payload small — just enough to remind the user what they've
    built in BigDogg before they give it up.
    """
    user_id = get_user_id(request)
    try:
        invoices = supabase.table("invoices")\
            .select("id, total_incl_btw, status, invoice_date", count="exact")\
            .eq("user_id", user_id)\
            .neq("status", "draft")\
            .execute()
        invoice_rows = invoices.data or []
        invoices_count = invoices.count if invoices.count is not None else len(invoice_rows)
        revenue_tracked = sum(
            float(row.get("total_incl_btw") or 0) for row in invoice_rows
        )

        clients = supabase.table("clients")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        clients_count = clients.count if clients.count is not None else len(
            clients.data or []
        )

        expenses = supabase.table("expenses")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        expenses_count = expenses.count if expenses.count is not None else len(
            expenses.data or []
        )

        # Member-since date: earliest of subscription created_at and the
        # user's first invoice. We don't expose the auth user object here
        # so we approximate.
        sub = supabase.table("subscriptions")\
            .select("created_at")\
            .eq("user_id", user_id)\
            .execute()
        member_since = (
            sub.data[0].get("created_at") if sub.data else None
        )

        return {
            "invoices_count": invoices_count,
            "clients_count": clients_count,
            "expenses_count": expenses_count,
            "revenue_tracked": round(revenue_tracked, 2),
            "member_since": member_since,
            "offer_available": not _user_has_recent_offer(user_id),
            "offer_months": RETENTION_OFFER_MONTHS,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(request: Request, data: CancelRequest):
    """Cancel the user's subscription OR apply the retention save offer
    (3 months free) depending on `accept_offer`. Idempotent for offer
    acceptance — the cooldown check prevents double-granting.

    Outcomes:
      - accept_offer=True with offer available
          • monthly: a 3 × €11.99 Stripe customer-balance credit (eaten
            by the next three invoices)
          • yearly: subscription_ends_at extended by 90 days
        Returns {"outcome": "offer_accepted", ...}.
      - accept_offer=True with offer not available (cooldown active)
          Falls through to full cancellation — the UI is supposed to
          skip the offer step in that case, but we never gift a second
          one even if a client misbehaves.
      - accept_offer=False
          Stripe: cancel_at_period_end=True so the user keeps access
          until the end of the current billing cycle. Legacy active
          (no stripe customer): flips status='expired' immediately.
        Returns {"outcome": "cancelled", "access_until": ...}.
    """
    user_id = get_user_id(request)
    reason = (data.reason or "").strip().lower()
    if reason not in ALLOWED_CANCEL_REASONS:
        raise HTTPException(status_code=400, detail="Unknown reason")

    sub_result = supabase.table("subscriptions")\
        .select(
            "id, status, plan, stripe_subscription_id, stripe_customer_id, "
            "subscription_ends_at, bonus_active_until"
        )\
        .eq("user_id", user_id)\
        .execute()
    if not sub_result.data:
        raise HTTPException(status_code=404, detail="No subscription found")
    sub = sub_result.data[0]
    plan = sub.get("plan")
    stripe_sub_id = sub.get("stripe_subscription_id")
    stripe_cust_id = sub.get("stripe_customer_id")

    now = datetime.now(timezone.utc)

    # ── Save-offer path ──
    if (
        data.accept_offer
        and reason in REASONS_WITH_OFFER
        and not _user_has_recent_offer(user_id)
    ):
        stripe_reference = None
        new_ends_at = None
        try:
            if plan == "yearly":
                # Extend access by 90 days. Use subscription_ends_at as
                # the truth, falling back to now() if it's null.
                cur_raw = sub.get("subscription_ends_at")
                base = now
                if cur_raw:
                    try:
                        cur = datetime.fromisoformat(
                            cur_raw.replace("Z", "+00:00")
                        )
                        if cur > base:
                            base = cur
                    except Exception:
                        pass
                new_ends_at = base + timedelta(days=30 * RETENTION_OFFER_MONTHS)
                supabase.table("subscriptions")\
                    .update({
                        "subscription_ends_at": new_ends_at.isoformat(),
                    })\
                    .eq("user_id", user_id)\
                    .execute()
                stripe_reference = f"yearly_extension_{new_ends_at.date()}"
            else:
                # Monthly (or legacy active treated as monthly). Drop a
                # negative customer-balance txn so the next three monthly
                # invoices are eaten by it. If there's no Stripe customer
                # (legacy active row), fall back to a 90-day bonus window
                # extension so the user still sees the value.
                credit_cents = PRICE_MONTHLY * RETENTION_OFFER_MONTHS
                if stripe_cust_id:
                    try:
                        txn = stripe.Customer.create_balance_transaction(
                            stripe_cust_id,
                            amount=-credit_cents,
                            currency=PRICE_CURRENCY,
                            description=(
                                f"BigDogg retention offer — "
                                f"{RETENTION_OFFER_MONTHS} maanden gratis"
                            ),
                        )
                        stripe_reference = getattr(txn, "id", None) or "credit_applied"
                    except stripe.error.StripeError as e:
                        # Fall back to bonus_active_until extension if
                        # Stripe rejects the credit (rare — mismatched
                        # mode, deleted customer, etc.).
                        print(f"Retention credit failed, extending bonus instead: {e}")
                        stripe_reference = None
                if not stripe_reference:
                    cur_raw = sub.get("bonus_active_until")
                    base = now
                    if cur_raw:
                        try:
                            cur = datetime.fromisoformat(
                                cur_raw.replace("Z", "+00:00")
                            )
                            if cur > base:
                                base = cur
                        except Exception:
                            pass
                    new_until = base + timedelta(
                        days=30 * RETENTION_OFFER_MONTHS
                    )
                    supabase.table("subscriptions")\
                        .update({"bonus_active_until": new_until.isoformat()})\
                        .eq("user_id", user_id)\
                        .execute()
                    stripe_reference = (
                        f"bonus_extension_{new_until.date()}"
                    )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        supabase.table("subscription_cancellation_events").insert({
            "user_id": user_id,
            "reason": reason,
            "comment": data.comment,
            "outcome": "offer_accepted",
            "stripe_reference": stripe_reference,
            "plan_at_event": plan,
        }).execute()

        return {
            "outcome": "offer_accepted",
            "months_free": RETENTION_OFFER_MONTHS,
            "plan": plan,
            "extended_until": new_ends_at.isoformat() if new_ends_at else None,
        }

    # ── Full cancel path ──
    access_until_iso = None
    if stripe_sub_id:
        try:
            updated = stripe.Subscription.modify(
                stripe_sub_id, cancel_at_period_end=True
            )
            # Stripe returns the period end as a unix timestamp.
            ts = getattr(updated, "current_period_end", None)
            if ts:
                access_until_iso = datetime.fromtimestamp(
                    ts, tz=timezone.utc
                ).isoformat()
                supabase.table("subscriptions")\
                    .update({"subscription_ends_at": access_until_iso})\
                    .eq("user_id", user_id)\
                    .execute()
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=500, detail=f"Stripe error: {e}")
    else:
        # Legacy active or PAYG-from-removed-flow: no Stripe sub to
        # cancel. Flip status straight to expired so the user enters
        # read-only mode on next session refresh.
        supabase.table("subscriptions")\
            .update({"status": "expired"})\
            .eq("user_id", user_id)\
            .execute()
        access_until_iso = now.isoformat()

    supabase.table("subscription_cancellation_events").insert({
        "user_id": user_id,
        "reason": reason,
        "comment": data.comment,
        "outcome": "cancelled",
        "stripe_reference": stripe_sub_id,
        "plan_at_event": plan,
    }).execute()

    return {
        "outcome": "cancelled",
        "access_until": access_until_iso,
        "plan": plan,
    }


@router.post("/reactivate")
async def reactivate_subscription(request: Request):
    """Undo a pending cancellation. Useful if the user changes their
    mind on the cancellation-confirmation screen.
    """
    user_id = get_user_id(request)
    sub_result = supabase.table("subscriptions")\
        .select("plan, stripe_subscription_id, status")\
        .eq("user_id", user_id)\
        .execute()
    if not sub_result.data:
        raise HTTPException(status_code=404, detail="No subscription found")
    sub = sub_result.data[0]
    stripe_sub_id = sub.get("stripe_subscription_id")
    if not stripe_sub_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe subscription to reactivate",
        )
    try:
        stripe.Subscription.modify(stripe_sub_id, cancel_at_period_end=False)
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")

    supabase.table("subscription_cancellation_events").insert({
        "user_id": user_id,
        "reason": "other",
        "comment": "reactivated via portal",
        "outcome": "reactivated",
        "stripe_reference": stripe_sub_id,
        "plan_at_event": sub.get("plan"),
    }).execute()

    # Welcome-back email — fire and forget so a Resend hiccup never
    # blocks the actual reactivation.
    try:
        _send_welcome_back_email(user_id, sub.get("plan"))
    except Exception as e:
        print(f"Welcome-back email error (non-fatal): {e}")

    return {"outcome": "reactivated"}


def _send_welcome_back_email(user_id: str, plan: Optional[str]) -> None:
    try:
        user_data = supabase.auth.admin.get_user_by_id(user_id)
        email = user_data.user.email if user_data.user else None
    except Exception:
        email = None
    if not email:
        return
    profile_result = supabase.table("user_profiles")\
        .select("full_name, business_name")\
        .eq("id", user_id)\
        .execute()
    profile = profile_result.data[0] if profile_result.data else {}
    name = (
        profile.get("full_name")
        or profile.get("business_name")
        or email.split("@")[0]
    )
    plan_label = (
        "jaarlijks abonnement" if plan == "yearly" else "maandelijks abonnement"
    )
    resend.Emails.send({
        "from": "BigDogg <info@bigdogg.nl>",
        "to": [email],
        "subject": "Welkom terug bij BigDogg 🎉",
        "html": f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <tr><td style="background:#1B3A4B;padding:28px 40px;text-align:center;">
          <div style="font-size:26px;font-weight:900;color:#C9A96E;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:12px;margin-top:4px;">Slim boekhouden voor ZZP'ers</div>
        </td></tr>
        <tr><td style="background:#166534;padding:18px 40px;text-align:center;border-bottom:1px solid #E2DDD6;">
          <div style="font-size:30px;">🎉</div>
          <div style="color:#ffffff;font-size:17px;font-weight:bold;margin-top:6px;">Welkom terug!</div>
        </td></tr>
        <tr><td style="padding:36px 40px;">
          <p style="color:#1B3A4B;font-size:16px;margin:0 0 12px 0;">Hoi {name},</p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 20px 0;">
            Goed je terug te zien. Je <strong>{plan_label}</strong> is heractiveerd — al je toegang werkt weer normaal: facturen versturen, BTW-aangiftes, jaarrapporten, alles.
          </p>
          <p style="color:#4A6572;font-size:14px;line-height:1.6;margin:0 0 24px 0;">
            Heb je nog feedback over wat we kunnen verbeteren? Antwoord gewoon op deze mail — ik lees alles persoonlijk.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="https://bigdogg.nl" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:bold;font-size:15px;">Open BigDogg</a>
            </td></tr>
          </table>
        </td></tr>
        <tr><td style="background:#f5f3ef;padding:20px 40px;text-align:center;border-top:1px solid #E2DDD6;">
          <div style="color:#4A6572;font-size:12px;">BigDogg · <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a></div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>""",
    })


@router.post("/cron/cancellation-reminders")
async def send_cancellation_reminders(request: Request):
    """Daily cron — emails users 7 days before their cancelled
    subscription's access window ends. Targets users whose latest
    cancellation_event has outcome='cancelled' (filtering out the
    normal-renewal-cycle false positives) and whose subscription_ends_at
    is exactly 7 days from now.

    Header: x-cron-secret. Suggested: daily at 09:00 Europe/Amsterdam.
    """
    require_cron_secret(request)

    now = datetime.now(timezone.utc)
    sent = 0
    errors = 0

    try:
        # Cancelled-but-still-in-grace subs have status='active' with a
        # fixed subscription_ends_at (no renewal will push it forward).
        active = supabase.table("subscriptions")\
            .select("user_id, plan, subscription_ends_at, stripe_subscription_id")\
            .eq("status", "active")\
            .not_.is_("subscription_ends_at", "null")\
            .execute()
        for row in (active.data or []):
            try:
                ends_raw = row.get("subscription_ends_at")
                if not ends_raw:
                    continue
                ends_at = datetime.fromisoformat(
                    ends_raw.replace("Z", "+00:00")
                )
                days_left = (ends_at - now).days
                if days_left != 7:
                    continue
                # Confirm this is really a cancellation, not a normal
                # renewal cycle ending: the latest event for this user
                # must be 'cancelled'.
                user_id = row["user_id"]
                events = supabase.table("subscription_cancellation_events")\
                    .select("outcome")\
                    .eq("user_id", user_id)\
                    .order("happened_at", desc=True)\
                    .limit(1)\
                    .execute()
                if not events.data:
                    continue
                if events.data[0].get("outcome") != "cancelled":
                    continue

                user_data = supabase.auth.admin.get_user_by_id(user_id)
                email = user_data.user.email if user_data.user else None
                if not email:
                    continue
                profile_result = supabase.table("user_profiles")\
                    .select("full_name, business_name")\
                    .eq("id", user_id)\
                    .execute()
                profile = profile_result.data[0] if profile_result.data else {}
                name = (
                    profile.get("full_name")
                    or profile.get("business_name")
                    or email.split("@")[0]
                )
                end_date_label = ends_at.strftime("%d-%m-%Y")
                _send_cancellation_reminder_email(email, name, end_date_label)
                sent += 1
            except Exception as e:
                errors += 1
                print(f"Cancellation reminder error for {row.get('user_id')}: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"sent": sent, "errors": errors}


def _send_cancellation_reminder_email(email: str, name: str, end_date_label: str) -> None:
    resend.Emails.send({
        "from": "BigDogg <info@bigdogg.nl>",
        "to": [email],
        "subject": f"Je BigDogg toegang loopt af op {end_date_label}",
        "html": f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <tr><td style="background:#1B3A4B;padding:28px 40px;text-align:center;">
          <div style="font-size:26px;font-weight:900;color:#C9A96E;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:12px;margin-top:4px;">Slim boekhouden voor ZZP'ers</div>
        </td></tr>
        <tr><td style="background:#FEF3C7;padding:16px 40px;text-align:center;border-bottom:1px solid #E2DDD6;">
          <div style="font-size:28px;">⏰</div>
          <div style="color:#92400E;font-size:17px;font-weight:bold;margin-top:6px;">Toegang eindigt op {end_date_label}</div>
        </td></tr>
        <tr><td style="padding:36px 40px;">
          <p style="color:#1B3A4B;font-size:16px;margin:0 0 12px 0;">Hoi {name},</p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 20px 0;">
            Over <strong>7 dagen</strong> verloopt je BigDogg toegang. Je gegevens blijven bewaard — je kunt ze altijd inkijken — maar nieuwe facturen, BTW-aangiftes en jaarrapporten zijn dan niet meer mogelijk.
          </p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 24px 0;">
            Bedacht je je nog? Eén klik en je gaat gewoon door — geen nieuw plan, geen nieuwe creditcard, gewoon weer aan.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="https://bigdogg.nl/#/subscription" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:bold;font-size:15px;">Heractiveer met één klik</a>
            </td></tr>
          </table>
          <p style="color:#8FA8B4;font-size:12px;line-height:1.6;margin:24px 0 0 0;text-align:center;font-style:italic;">
            Geen actie nodig als je het zo wilt laten. Je toegang stopt vanzelf op {end_date_label}.
          </p>
        </td></tr>
        <tr><td style="background:#f5f3ef;padding:20px 40px;text-align:center;border-top:1px solid #E2DDD6;">
          <div style="color:#4A6572;font-size:12px;">BigDogg · <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a></div>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body></html>""",
    })


@router.get("/admin/churn-stats")
async def admin_churn_stats(request: Request, since: Optional[str] = None):
    """Solo-founder churn dashboard data. Protected by x-cron-secret so
    no extra env var is needed. Returns:

      - reason_breakdown: {reason → {cancelled, offer_accepted, reactivated}}
      - monthly: list of {month, cancelled, offer_accepted, reactivated}
      - recent_comments: latest 20 entries with non-empty comments
      - totals: aggregate counts

    Pass ?since=YYYY-MM-DD to bound the window (defaults to 90 days).
    """
    require_cron_secret(request)

    if since:
        try:
            since_dt = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
        except Exception:
            raise HTTPException(
                status_code=400, detail="since must be YYYY-MM-DD"
            )
    else:
        since_dt = datetime.now(timezone.utc) - timedelta(days=90)

    try:
        events = supabase.table("subscription_cancellation_events")\
            .select("reason, comment, outcome, happened_at, plan_at_event")\
            .gte("happened_at", since_dt.isoformat())\
            .order("happened_at", desc=True)\
            .execute()
        rows = events.data or []

        reason_breakdown: dict = {}
        monthly_map: dict = {}
        totals = {"cancelled": 0, "offer_accepted": 0, "reactivated": 0}
        recent_comments = []

        for r in rows:
            reason = r.get("reason") or "other"
            outcome = r.get("outcome") or ""
            if outcome in totals:
                totals[outcome] += 1
            rb = reason_breakdown.setdefault(
                reason,
                {"cancelled": 0, "offer_accepted": 0, "reactivated": 0},
            )
            if outcome in rb:
                rb[outcome] += 1
            try:
                hd = datetime.fromisoformat(
                    r["happened_at"].replace("Z", "+00:00")
                )
                month_key = f"{hd.year:04d}-{hd.month:02d}"
            except Exception:
                month_key = "unknown"
            mm = monthly_map.setdefault(
                month_key,
                {
                    "month": month_key,
                    "cancelled": 0,
                    "offer_accepted": 0,
                    "reactivated": 0,
                },
            )
            if outcome in mm:
                mm[outcome] += 1
            if (r.get("comment") or "").strip() and len(recent_comments) < 20:
                recent_comments.append({
                    "happened_at": r.get("happened_at"),
                    "reason": reason,
                    "outcome": outcome,
                    "plan": r.get("plan_at_event"),
                    "comment": r.get("comment"),
                })

        monthly_list = sorted(monthly_map.values(), key=lambda m: m["month"])
        # Save-rate = offer_accepted / (offer_accepted + cancelled)
        offered = totals["offer_accepted"] + totals["cancelled"]
        save_rate = (
            round(100 * totals["offer_accepted"] / offered, 1) if offered else 0.0
        )
        return {
            "since": since_dt.date().isoformat(),
            "totals": totals,
            "save_rate_pct": save_rate,
            "reason_breakdown": reason_breakdown,
            "monthly": monthly_list,
            "recent_comments": recent_comments,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _insert_bigdogg_expense(user_id: str, label: str, plan: str = "monthly") -> None:
    """Insert BigDogg Pro subscription as a bookkeeping expense for the
    user. The amount tracks the plan they're on so yearly subscribers
    don't get under-booked by 12×."""
    if plan == "yearly":
        amount_ex = BIGDOGG_YEAR_AMOUNT_EX_BTW
        btw_amount = BIGDOGG_YEAR_BTW_AMOUNT
        description = "BigDogg Pro abonnement (jaarlijks)"
    else:
        amount_ex = BIGDOGG_AMOUNT_EX_BTW
        btw_amount = BIGDOGG_BTW_AMOUNT
        description = "BigDogg Pro abonnement"
    supabase.table("expenses").insert({
        "user_id": user_id,
        "description": description,
        "amount_ex_btw": amount_ex,
        "btw_amount": btw_amount,
        "btw_rate": BIGDOGG_BTW_RATE,
        "expense_date": str(date.today()),
        "category": "Software & abonnementen",
    }).execute()
    print(f"BigDogg expense inserted for user {user_id} ({label}, {plan})")


REFERRAL_LINK = "https://www.bigdogg.nl/#/subscription"
SUBSCRIBE_LINK = "https://www.bigdogg.nl/#/pricing"


def _send_trial_expiry_email(email: str, name: str, days_left: int) -> None:
    """Trial expiry warning — referral CTA first, subscribe second.

    Thresholds: 7-day (friendly nudge, yellow banner) and 3-day (urgent,
    red banner with "access will be limited" framing).
    """
    if days_left == 7:
        subject = "Nog 7 dagen gratis — jouw BigDogg proefperiode loopt bijna af"
        subject_en = "7 days left — your BigDogg trial is ending soon"
        urgency_color = "#92400E"
        urgency_bg = "#FEF3C7"
        urgency_icon = "⏰"
        urgency_text = "Nog 7 dagen!"
        heading = "Nog 7 dagen!"
        intro = (
            "Je gratis proefperiode van BigDogg loopt over 7 dagen af. "
            "Tot die tijd heb je volledige toegang tot alle functies."
        )
        urgency_close = ""
    else:  # 3 days
        subject = "Nog 3 dagen! Blokkering nadert — verleng nu of verwijs vrienden"
        subject_en = "3 days left! Access ending soon — subscribe or refer friends"
        urgency_color = "#991B1B"
        urgency_bg = "#FEE2E2"
        urgency_icon = "🚨"
        urgency_text = "Nog 3 dagen!"
        heading = "Nog maar 3 dagen!"
        intro = (
            "Over 3 dagen verloopt je proefperiode. Daarna kun je nog "
            "steeds inloggen en je gegevens bekijken, maar nieuwe "
            "facturen maken en andere functies worden geblokkeerd."
        )
        urgency_close = (
            '<p style="color:#4A6572;font-size:13px;line-height:1.6;'
            'margin:20px 0 0 0;text-align:center;font-style:italic;">'
            "Jouw gegevens blijven altijd veilig bewaard — ook na de "
            "proefperiode.</p>"
        )

    # Subject is the NL line per existing pattern; EN clients usually
    # render the NL one fine. (Existing emails on the system also send
    # NL-only; we keep that convention.)
    _ = subject_en  # kept for future i18n if we go bilingual

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
          <h2 style="color:#1B3A4B;font-size:22px;font-weight:800;margin:0 0 12px 0;letter-spacing:-0.3px;">{heading}</h2>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 24px 0;">{intro}</p>

          <!-- Referral CTA (primary) -->
          <h3 style="color:#1B3A4B;font-size:17px;font-weight:700;margin:0 0 8px 0;">Wil je gratis verder?</h3>
          <p style="color:#4A6572;font-size:14.5px;line-height:1.6;margin:0 0 16px 0;">
            Verwijs 2 vrienden naar BigDogg en je krijgt een gratis maand cadeau — tot maximaal 3 gratis maanden.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:24px;">
            <tr><td align="center">
              <a href="{REFERRAL_LINK}" style="display:inline-block;background:#C9A96E;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:10px;font-weight:bold;font-size:15px;">
                Vrienden uitnodigen
              </a>
            </td></tr>
          </table>

          <hr style="border:none;border-top:1px solid #E2DDD6;margin:8px 0 20px 0;">

          <!-- Subscribe CTA (secondary) -->
          <h3 style="color:#1B3A4B;font-size:17px;font-weight:700;margin:0 0 8px 0;">Of start direct je abonnement</h3>
          <p style="color:#4A6572;font-size:14.5px;line-height:1.6;margin:0 0 16px 0;">
            Vanaf €9,99 per maand (jaarlijks) of €11,99 per maand. Alles inbegrepen. Geen verrassingen.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="{SUBSCRIBE_LINK}" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:10px;font-weight:bold;font-size:15px;">
                Abonnement starten
              </a>
            </td></tr>
          </table>

          {urgency_close}
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
    """Daily cron — emails trial users at 7 days and 3 days remaining.

    Dedupe via the `trial_warning_emails` table: one row per
    (user_id, threshold_days), so a retry of the same day is a no-op.

    Header: x-cron-secret. Schedule: daily at 09:00 Europe/Amsterdam.
    """
    require_cron_secret(request)

    now = datetime.now(timezone.utc)
    sent_7 = 0
    sent_3 = 0
    errors = 0
    skipped_already_sent = 0

    try:
        result = supabase.table("subscriptions")\
            .select("user_id, trial_ends_at")\
            .eq("status", "trial")\
            .execute()

        trial_subs = result.data or []
        print(f"Trial expiry cron: checking {len(trial_subs)} trial users")

        for sub in trial_subs:
            try:
                user_id = sub["user_id"]
                if not sub.get("trial_ends_at"):
                    continue
                trial_ends = datetime.fromisoformat(
                    sub["trial_ends_at"].replace("Z", "+00:00")
                )
                days_left = (trial_ends - now).days

                if days_left not in (7, 3):
                    continue

                # Dedupe: skip if we've already emailed this threshold.
                already = supabase.table("trial_warning_emails")\
                    .select("user_id")\
                    .eq("user_id", user_id)\
                    .eq("threshold_days", days_left)\
                    .limit(1)\
                    .execute()
                if already.data:
                    skipped_already_sent += 1
                    continue

                user_data = supabase.auth.admin.get_user_by_id(user_id)
                email = user_data.user.email if user_data.user else None
                if not email:
                    continue

                profile_result = supabase.table("user_profiles")\
                    .select("full_name, business_name")\
                    .eq("id", user_id)\
                    .execute()
                profile = profile_result.data[0] if profile_result.data else {}
                name = (
                    profile.get("full_name")
                    or profile.get("business_name")
                    or email.split("@")[0]
                )

                _send_trial_expiry_email(email, name, days_left)

                # Record the send so we don't double-fire on rerun.
                try:
                    supabase.table("trial_warning_emails").insert({
                        "user_id": user_id,
                        "threshold_days": days_left,
                    }).execute()
                except Exception as dedupe_err:
                    # Don't fail the run if dedupe insert fails — worst
                    # case the next rerun re-sends, which is rare since
                    # the day-of detection narrows the window already.
                    print(f"trial_warning_emails insert error: {dedupe_err}")

                if days_left == 7:
                    sent_7 += 1
                else:
                    sent_3 += 1

                print(f"Trial expiry email sent to {email} ({days_left} days left)")

            except Exception as e:
                errors += 1
                print(f"Trial expiry email error for user {sub.get('user_id')}: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "sent_7_day": sent_7,
        "sent_3_day": sent_3,
        "errors": errors,
        "skipped_already_sent": skipped_already_sent,
        "checked": len(trial_subs),
    }


# ─── BTW deadline reminders ─────────────────────────────────
# Dutch quarterly VAT (BTW) deadlines: month, day, label
BTW_DEADLINES = [
    (4, 30, "Q1"),   # 30 april
    (7, 31, "Q2"),   # 31 juli
    (10, 31, "Q3"),  # 31 oktober
    (1, 31, "Q4"),   # 31 januari (vorig jaar)
]
BTW_REMINDER_DAYS_BEFORE = 7

_DUTCH_MONTHS = {
    1: "januari", 2: "februari", 3: "maart", 4: "april",
    5: "mei", 6: "juni", 7: "juli", 8: "augustus",
    9: "september", 10: "oktober", 11: "november", 12: "december",
}
_EN_MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def _format_dutch_date(d: date) -> str:
    return f"{d.day} {_DUTCH_MONTHS[d.month]} {d.year}"


def _format_english_date(d: date) -> str:
    return f"{_EN_MONTHS[d.month]} {d.day}, {d.year}"


def _send_btw_reminder_email(
    email: str,
    name: str,
    quarter: str,
    deadline: date,
    language: str,
) -> None:
    """Send a BTW deadline reminder in the user's language (nl or en)."""
    if language == "en":
        deadline_text = _format_english_date(deadline)
        subject = f"Don't forget your VAT return — deadline {deadline_text}"
        tagline = "Accounting for Dutch freelancers"
        urgency = f"{quarter} VAT · {deadline_text}"
        greeting = f"Hi {name},"
        intro = (
            f"Just a heads-up: your <strong>{quarter}</strong> VAT return is due "
            f"on <strong>{deadline_text}</strong> — that's 7 days from now."
        )
        ready = "Your BTW report PDF is already waiting for you in BigDogg."
        instructions = (
            "Open BigDogg, go to the <strong>Overzicht</strong> tab, pick the right "
            "quarter, and download the PDF. Then submit it via the Belastingdienst "
            "portal before the deadline."
        )
        cta = "Open BigDogg"
        footer_note = (
            f"Friendly reminder — the {quarter} VAT return itself is your own "
            "responsibility. BigDogg does the prep, you submit."
        )
    else:
        deadline_text = _format_dutch_date(deadline)
        subject = f"Vergeet je BTW-aangifte niet — deadline {deadline_text}"
        tagline = "Boekhouden voor ZZP'ers"
        urgency = f"{quarter} BTW · {deadline_text}"
        greeting = f"Hoi {name},"
        intro = (
            f"Even een seintje: je <strong>{quarter}</strong> BTW-aangifte moet "
            f"uiterlijk <strong>{deadline_text}</strong> binnen zijn — over 7 dagen dus."
        )
        ready = "Je BTW-aangifte PDF staat al voor je klaar in BigDogg."
        instructions = (
            "Open BigDogg, ga naar het <strong>Overzicht</strong> tabblad, kies het "
            "juiste kwartaal en download de PDF. Dien hem dan in via het "
            "Belastingdienst portaal vóór de deadline."
        )
        cta = "Open BigDogg"
        footer_note = (
            f"Vriendelijke herinnering — de {quarter} aangifte zelf is je eigen "
            "verantwoordelijkheid. BigDogg doet het voorwerk, jij dient hem in."
        )

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr><td style="background:#1B3A4B;padding:28px 40px;text-align:center;">
          <div style="font-size:26px;font-weight:900;color:#C9A96E;font-family:Arial,sans-serif;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:12px;margin-top:4px;">{tagline}</div>
        </td></tr>

        <!-- Deadline banner -->
        <tr><td style="background:#FEF3C7;padding:16px 40px;text-align:center;border-bottom:1px solid #E2DDD6;">
          <div style="font-size:28px;">📅</div>
          <div style="color:#92400E;font-size:18px;font-weight:bold;margin-top:6px;">{urgency}</div>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:36px 40px;">
          <p style="color:#1B3A4B;font-size:16px;margin:0 0 12px 0;">{greeting}</p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 20px 0;">{intro}</p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 24px 0;"><strong>{ready}</strong> {instructions}</p>

          <!-- CTA -->
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="https://bigdogg.nl" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:bold;font-size:15px;">{cta}</a>
            </td></tr>
          </table>

          <p style="color:#8FA8B4;font-size:12px;line-height:1.6;margin:28px 0 0 0;text-align:center;font-style:italic;">{footer_note}</p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="background:#f5f3ef;padding:20px 40px;text-align:center;border-top:1px solid #E2DDD6;">
          <div style="color:#4A6572;font-size:12px;">BigDogg &middot; <a href="https://bigdogg.nl" style="color:#1B3A4B;">bigdogg.nl</a></div>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    resend.Emails.send({
        "from": "BigDogg <info@bigdogg.nl>",
        "to": [email],
        "subject": subject,
        "html": html_body,
    })


@router.post("/cron/btw-reminders")
async def send_btw_reminders(request: Request):
    """
    Daily cron — sends a BTW deadline reminder 7 days before each quarterly
    deadline (30 april, 31 juli, 31 oktober, 31 januari) to all users with
    subscription status 'trial' or 'active'. Uses the user's profile.language
    field for NL/EN. Localised email content + branded template.

    Header: x-cron-secret: <your_cron_secret>
    Schedule: daily at 09:00 Europe/Amsterdam (cron-job.org)
    """
    require_cron_secret(request)

    today = datetime.now(timezone.utc).date()

    # Find a deadline exactly BTW_REMINDER_DAYS_BEFORE days from today.
    matched = None
    for month, day, quarter in BTW_DEADLINES:
        # Same calendar year (handles 30 april, 31 juli, 31 oktober, and Q4 31 januari of current year)
        try:
            d = date(today.year, month, day)
            if (d - today).days == BTW_REMINDER_DAYS_BEFORE:
                matched = (d, quarter)
                break
        except ValueError:
            continue

    if not matched:
        return {
            "sent": 0,
            "errors": 0,
            "checked": 0,
            "matched_deadline": None,
            "message": "No BTW deadline 7 days from today",
        }

    deadline_date, quarter = matched
    print(f"BTW reminder cron: {quarter} deadline on {deadline_date}, sending to trial+active users")

    sent = 0
    errors = 0
    user_count = 0

    try:
        # Subscriptions where status in (trial, active)
        result = supabase.table("subscriptions")\
            .select("user_id, status")\
            .in_("status", ["trial", "active"])\
            .execute()
        subs = result.data or []
        user_count = len(subs)

        for sub in subs:
            try:
                user_id = sub["user_id"]
                user_data = supabase.auth.admin.get_user_by_id(user_id)
                email = user_data.user.email if user_data.user else None
                if not email:
                    continue

                profile_result = supabase.table("user_profiles")\
                    .select("full_name, business_name, language")\
                    .eq("id", user_id)\
                    .execute()
                profile = profile_result.data[0] if profile_result.data else {}
                name = (
                    profile.get("full_name")
                    or profile.get("business_name")
                    or email.split("@")[0]
                )
                language = (profile.get("language") or "nl").lower()
                if language not in ("nl", "en"):
                    language = "nl"

                _send_btw_reminder_email(email, name, quarter, deadline_date, language)
                sent += 1
                print(f"BTW reminder sent to {email} ({language}, {quarter})")
            except Exception as e:
                errors += 1
                print(f"BTW reminder error for user {sub.get('user_id')}: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "sent": sent,
        "errors": errors,
        "checked": user_count,
        "matched_deadline": deadline_date.isoformat(),
        "quarter": quarter,
    }


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # Fail-closed: never process an unsigned event. If the secret is
    # missing or still set to the placeholder, return 500 so Stripe
    # retries while we fix env — DO NOT fall back to json.loads(payload)
    # which would let an attacker POST a forged event with
    # metadata.user_id=<victim> and silently flip them to status='active'.
    if (
        not settings.stripe_webhook_secret
        or settings.stripe_webhook_secret == "whsec_placeholder"
    ):
        print("Stripe webhook secret missing/placeholder — refusing to process")
        raise HTTPException(
            status_code=500, detail="webhook_secret_missing",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret,
        )
    except stripe.error.SignatureVerificationError as e:
        print(f"Webhook signature error: {str(e)}")
        raise HTTPException(status_code=400, detail="invalid_signature")
    except Exception as e:
        print(f"Webhook parse error: {str(e)}")
        raise HTTPException(status_code=400, detail="invalid_payload")

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
                # Subscription purchase (monthly or yearly). Plan comes
                # from session metadata; default to 'monthly' for legacy
                # sessions that pre-date the column.
                plan = metadata.get("plan", "monthly")
                if plan not in ("monthly", "yearly"):
                    plan = "monthly"
                # Recurring window — 30 days for monthly, 365 for yearly.
                # The invoice.payment_succeeded handler refreshes this on
                # each renewal cycle so the value stays accurate.
                days = 365 if plan == "yearly" else 30
                ends_at = datetime.now(timezone.utc) + timedelta(days=days)
                existing = supabase.table("subscriptions")\
                    .select("id")\
                    .eq("user_id", user_id)\
                    .execute()

                if existing.data:
                    supabase.table("subscriptions")\
                        .update({
                            "status": "active",
                            "plan": plan,
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
                        "plan": plan,
                        "stripe_customer_id": session.get("customer"),
                        "stripe_subscription_id": session.get("subscription"),
                        "subscription_ends_at": ends_at.isoformat(),
                    }).execute()

                # Insert first month's (or year's) BigDogg expense.
                try:
                    _insert_bigdogg_expense(user_id, "initial checkout", plan)
                except Exception as e:
                    print(f"BigDogg expense insert error (non-fatal): {e}")

                # Referral conversion: if this user signed up via someone's
                # referral code, mark their signup as converted (for stats
                # display only). Bonuses are granted on signup, not on
                # conversion, so we don't touch the referrer here.
                try:
                    ref_lookup = supabase.table("referral_signups")\
                        .select("id, converted")\
                        .eq("new_user_id", user_id)\
                        .execute()
                    if ref_lookup.data and not ref_lookup.data[0].get("converted"):
                        supabase.table("referral_signups")\
                            .update({
                                "converted": True,
                                "converted_at": datetime.now(timezone.utc).isoformat(),
                            })\
                            .eq("id", ref_lookup.data[0]["id"])\
                            .execute()
                except Exception as ref_err:
                    print(f"Referral converted-flag error (non-fatal): {ref_err}")

        elif event_type == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            if hasattr(invoice, 'to_dict'):
                invoice = invoice.to_dict()
            elif not isinstance(invoice, dict):
                invoice = dict(invoice)

            customer_id = invoice.get("customer")
            billing_reason = invoice.get("billing_reason", "")

            if customer_id:
                # Read the plan from the existing row so we can extend
                # the window by the right number of days (yearly = 365,
                # monthly = 30) and book the renewal expense correctly.
                sub_row = supabase.table("subscriptions")\
                    .select("user_id, plan")\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()
                user_plan = "monthly"
                user_id_for_expense = None
                if sub_row.data:
                    user_plan = sub_row.data[0].get("plan") or "monthly"
                    user_id_for_expense = sub_row.data[0].get("user_id")
                days = 365 if user_plan == "yearly" else 30
                ends_at = datetime.now(timezone.utc) + timedelta(days=days)
                supabase.table("subscriptions")\
                    .update({
                        "status": "active",
                        "subscription_ends_at": ends_at.isoformat(),
                    })\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()

                # Insert expense on renewal only (initial handled by checkout.session.completed)
                if billing_reason == "subscription_cycle" and user_id_for_expense:
                    try:
                        _insert_bigdogg_expense(
                            user_id_for_expense, "renewal", user_plan
                        )
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
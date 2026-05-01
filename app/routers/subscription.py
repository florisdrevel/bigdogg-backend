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
    """Raises 403 if user is not on active paid tier OR a referral bonus."""
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
    auth = request.headers.get("x-cron-secret", "")
    if auth != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
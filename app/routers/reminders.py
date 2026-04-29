from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.config import settings
from datetime import datetime, timezone, timedelta
import resend

router = APIRouter()
resend.api_key = settings.resend_api_key


def _format_eur(value) -> str:
    """Format a number as European-style euros, e.g. 3025.0 -> '3.025,00'."""
    try:
        n = float(value or 0)
    except (TypeError, ValueError):
        n = 0.0
    s = f"{n:,.2f}"  # 3,025.00
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _send_overdue_notification(
    user_email: str,
    user_name: str,
    invoice_number: str,
    client_name: str,
    total_eur: str,
    days_overdue: int,
    language: str,
) -> None:
    """Notify the ZZP'er (the BigDogg user) that an invoice is unpaid.
    Does NOT email the client — the user decides whether to chase.
    """
    if language == "en":
        subject = f"Invoice {invoice_number} is still unpaid by {client_name}"
        tagline = "Accounting for Dutch freelancers"
        urgency = (
            f"Unpaid for {days_overdue} days"
        )
        greeting = f"Hi {user_name},"
        intro = (
            f"Heads-up: invoice <strong>{invoice_number}</strong> to "
            f"<strong>{client_name}</strong> for <strong>€ {total_eur}</strong> "
            f"is still unpaid {days_overdue} days after the invoice date."
        )
        question = "Want to send a reminder?"
        instructions = (
            "Open BigDogg, find the invoice in the list and tap "
            "<strong>Stuur herinnering</strong>. We won't email the client "
            "without you saying so."
        )
        cta = "Open BigDogg"
        footer = "We never email your clients automatically. You're in charge."
    else:
        subject = f"Factuur {invoice_number} staat nog open bij {client_name}"
        tagline = "Boekhouden voor ZZP'ers"
        urgency = f"{days_overdue} dagen openstaand"
        greeting = f"Hoi {user_name},"
        intro = (
            f"Even een seintje: factuur <strong>{invoice_number}</strong> aan "
            f"<strong>{client_name}</strong> voor <strong>€ {total_eur}</strong> "
            f"staat al {days_overdue} dagen open."
        )
        question = "Wil je een herinnering sturen?"
        instructions = (
            "Open BigDogg, zoek de factuur op en tik op "
            "<strong>Stuur herinnering</strong>. We mailen je klant nooit zomaar zelf."
        )
        cta = "Open BigDogg"
        footer = (
            "We mailen je klanten nooit automatisch. Jij bepaalt of er een "
            "herinnering uitgaat."
        )

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f5f3ef;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f3ef;padding:40px 20px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <tr><td style="background:#1B3A4B;padding:28px 40px;text-align:center;">
          <div style="font-size:26px;font-weight:900;color:#C9A96E;font-family:Arial,sans-serif;">BigDogg.</div>
          <div style="color:#ffffff;opacity:0.7;font-size:12px;margin-top:4px;">{tagline}</div>
        </td></tr>

        <tr><td style="background:#FEF3C7;padding:16px 40px;text-align:center;border-bottom:1px solid #E2DDD6;">
          <div style="font-size:28px;">⏳</div>
          <div style="color:#92400E;font-size:18px;font-weight:bold;margin-top:6px;">{urgency}</div>
        </td></tr>

        <tr><td style="padding:36px 40px;">
          <p style="color:#1B3A4B;font-size:16px;margin:0 0 12px 0;">{greeting}</p>
          <p style="color:#4A6572;font-size:15px;line-height:1.6;margin:0 0 16px 0;">{intro}</p>
          <p style="color:#1B3A4B;font-size:16px;line-height:1.6;margin:0 0 8px 0;font-weight:bold;">{question}</p>
          <p style="color:#4A6572;font-size:14px;line-height:1.6;margin:0 0 24px 0;">{instructions}</p>

          <table width="100%" cellpadding="0" cellspacing="0">
            <tr><td align="center">
              <a href="https://bigdogg.nl" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:bold;font-size:15px;">{cta}</a>
            </td></tr>
          </table>

          <p style="color:#8FA8B4;font-size:12px;line-height:1.6;margin:28px 0 0 0;text-align:center;font-style:italic;">{footer}</p>
        </td></tr>

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
        "to": [user_email],
        "subject": subject,
        "html": html_body,
    })


def _notify_for_invoice(invoice: dict, days_overdue: int) -> bool:
    """Look up user info and send the overdue notification. Returns True on send."""
    user_id = invoice.get("user_id")
    if not user_id:
        return False

    user_data = supabase.auth.admin.get_user_by_id(user_id)
    user_email = user_data.user.email if user_data.user else None
    if not user_email:
        return False

    profile_result = supabase.table("user_profiles")\
        .select("full_name, business_name, language")\
        .eq("id", user_id)\
        .execute()
    profile = profile_result.data[0] if profile_result.data else {}
    user_name = (
        profile.get("full_name")
        or profile.get("business_name")
        or user_email.split("@")[0]
    )
    language = (profile.get("language") or "nl").lower()
    if language not in ("nl", "en"):
        language = "nl"

    _send_overdue_notification(
        user_email=user_email,
        user_name=user_name,
        invoice_number=str(invoice.get("invoice_number") or ""),
        client_name=str(invoice.get("client_name") or "?"),
        total_eur=_format_eur(invoice.get("total_incl_btw")),
        days_overdue=days_overdue,
        language=language,
    )
    return True


@router.post("/cron/payment-reminders")
async def payment_reminders_cron(request: Request):
    """
    Daily cron — internal nudges to the ZZP'er for unpaid invoices.

    Triggers:
      - invoice_date == today - 14 AND reminder_count == 0
      - invoice_date == today - 30 AND reminder_count == 1

    The cron does NOT email the client. It only emails the BigDogg user
    (the ZZP'er) so they decide whether to chase. The existing
    POST /api/v1/invoices/{id}/reminder endpoint is the one that actually
    emails the client when the user clicks "Stuur herinnering".

    Header: x-cron-secret: <your_cron_secret>
    Schedule: daily at 09:00 Europe/Amsterdam.
    """
    auth = request.headers.get("x-cron-secret", "")
    if auth != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    today = datetime.now(timezone.utc).date()
    target_14 = today - timedelta(days=14)
    target_30 = today - timedelta(days=30)

    sent_14 = 0
    sent_30 = 0
    errors = 0

    try:
        # Day-14 unpaid, no reminders sent yet
        r14 = supabase.table("invoices")\
            .select("id, user_id, invoice_number, client_name, total_incl_btw, invoice_date, reminder_count, status")\
            .eq("status", "sent")\
            .eq("invoice_date", target_14.isoformat())\
            .execute()
        for inv in r14.data or []:
            if (inv.get("reminder_count") or 0) != 0:
                continue
            try:
                if _notify_for_invoice(inv, days_overdue=14):
                    sent_14 += 1
            except Exception as e:
                errors += 1
                print(f"14-day reminder error for invoice {inv.get('id')}: {e}")

        # Day-30 unpaid, exactly one reminder already sent
        r30 = supabase.table("invoices")\
            .select("id, user_id, invoice_number, client_name, total_incl_btw, invoice_date, reminder_count, status")\
            .eq("status", "sent")\
            .eq("invoice_date", target_30.isoformat())\
            .execute()
        for inv in r30.data or []:
            if (inv.get("reminder_count") or 0) != 1:
                continue
            try:
                if _notify_for_invoice(inv, days_overdue=30):
                    sent_30 += 1
            except Exception as e:
                errors += 1
                print(f"30-day reminder error for invoice {inv.get('id')}: {e}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "sent_14_day": sent_14,
        "sent_30_day": sent_30,
        "errors": errors,
        "checked_14": len(r14.data or []),
        "checked_30": len(r30.data or []),
    }

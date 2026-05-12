"""Accountant portal — token-gated read-only access to one BigDogg user's
administration.

New simpler model: the token in the email link IS the credential. The
accountant does NOT create a BigDogg account; they just open the link
and see the data. Validity is 14 days; the owner can revoke or
regenerate the link.

Endpoints (all under /api/v1/accountants):

  Owner — auth required (Bearer access_token in Authorization):
    POST   /invite                      create a fresh access link
    GET    /invites                     list this owner's links
    DELETE /invites/{token}             revoke a single link
    POST   /invites/{token}/extend      bump expiry +14 days

  Accountant — public (token in URL path, no auth header needed):
    GET    /portal/{token}              meta: owner name, expiry
    GET    /portal/{token}/overview     yearly revenue / expense / BTW totals
    GET    /portal/{token}/invoices     list invoices
    GET    /portal/{token}/expenses     list expenses
    GET    /portal/{token}/invoices/{invoice_id}/pdf   download PDF
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from datetime import datetime, timezone, timedelta
from app.database import supabase
from app.config import settings
import resend

router = APIRouter()
resend.api_key = settings.resend_api_key


# ─── Auth helpers ────────────────────────────────────────────
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


def _resolve_portal_token(token: str) -> dict:
    """Validate an accountant portal token and return its row. Raises:

      404 — token does not exist
      410 — token expired (Gone)
      403 — token revoked
    """
    result = supabase.table("accountant_invites")\
        .select("token, user_id, email, used, expires_at, created_at")\
        .eq("token", token).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="link_not_found")
    row = result.data[0]

    # `used=true` is repurposed for "revoked by owner" in this model.
    if row.get("used"):
        raise HTTPException(status_code=403, detail="link_revoked")

    expires_raw = row.get("expires_at")
    if expires_raw:
        try:
            exp = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) >= exp:
                raise HTTPException(status_code=410, detail="link_expired")
        except HTTPException:
            raise
        except Exception:
            pass
    return row


# ─── Owner: create / list / revoke / extend links ────────────
@router.post("/invite")
async def invite_accountant(request: Request):
    user_id = get_user_id(request)
    body = await request.json()
    email = (body or {}).get("email", "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="invalid_email")

    insert = supabase.table("accountant_invites").insert({
        "user_id": user_id,
        "email":   email,
        "used":    False,
    }).execute()
    if not insert.data:
        raise HTTPException(status_code=400, detail="invite_failed")

    token = insert.data[0]["token"]

    profile = supabase.table("user_profiles")\
        .select("business_name, full_name")\
        .eq("id", user_id).limit(1).execute()
    inviter = "Een BigDogg-gebruiker"
    if profile.data:
        p = profile.data[0]
        inviter = (p.get("business_name") or p.get("full_name") or inviter).strip()

    accept_url = f"{settings.share_link_origin}/a/{token}"

    email_sent = False
    email_error: str | None = None
    try:
        if not settings.resend_api_key:
            email_error = "resend_api_key_missing"
        else:
            subject = f"{inviter} geeft je toegang tot zijn BigDogg-boekhouding"
            html_body = _invite_email_html(
                inviter=inviter,
                recipient_email=email,
                accept_url=accept_url,
            )
            text_body = (
                f"Hallo,\n\n"
                f"{inviter} geeft je 14 dagen lang alleen-lezen toegang tot "
                f"zijn BigDogg-boekhouding — facturen, kosten en BTW-overzicht.\n\n"
                f"Open de portal: {accept_url}\n\n"
                f"Er is geen account nodig — open de link en je zit erin.\n\n"
                f"---\nDit bericht is verzonden via BigDogg · bigdogg.nl\n"
            )
            resend.Emails.send({
                "from": "BigDogg <info@bigdogg.nl>",
                "to":   [email],
                "subject": subject,
                "text": text_body,
                "html": html_body,
            })
            email_sent = True
    except Exception as e:
        email_error = str(e)
        print(f"[accountants] invite email failed: {e}")

    return {
        "success":     True,
        "token":       token,
        "accept_url":  accept_url,
        "email_sent":  email_sent,
        "email_error": email_error,
    }


def _invite_email_html(*, inviter: str, recipient_email: str, accept_url: str) -> str:
    safe_inviter = (
        inviter.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f"""<!DOCTYPE html>
<html lang="nl">
<body style="margin:0;padding:0;background:#F5F3EF;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1B3A4B;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F3EF;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;border:1px solid #E2DDD6;overflow:hidden;">
        <tr><td align="center" style="padding:28px 28px 4px 28px;background:#1B3A4B;">
          <img src="https://bigdogg.nl/icons/Icon-512.png" alt="BigDogg" width="64" height="64" style="display:block;border-radius:12px;"/>
          <h1 style="margin:12px 0 0 0;color:#C9A96E;font-size:22px;letter-spacing:-0.3px;font-weight:700;">BigDogg.</h1>
          <p style="margin:4px 0 16px 0;color:#F5F3EF;font-size:12px;letter-spacing:1px;text-transform:uppercase;">Accountantsportaal</p>
        </td></tr>
        <tr><td style="padding:28px 28px 8px 28px;">
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">Hallo,</p>
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">
            <strong style="color:#1B3A4B;">{safe_inviter}</strong> geeft je <strong>14 dagen</strong>
            alleen-lezen toegang tot zijn BigDogg-boekhouding.
          </p>
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">
            Klik op de knop om de portal te openen — geen account nodig, geen wachtwoord.
            Bekijk en download facturen, kosten en het BTW-overzicht.
          </p>
        </td></tr>
        <tr><td align="center" style="padding:8px 28px 4px 28px;">
          <a href="{accept_url}" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;margin:6px;">Portal openen</a>
        </td></tr>
        <tr><td align="center" style="padding:0 28px 24px 28px;">
          <p style="margin:12px 0 0 0;font-size:12px;color:#4A6572;">
            of plak deze link in je browser:<br>
            <a href="{accept_url}" style="color:#1B3A4B;word-break:break-all;">{accept_url}</a>
          </p>
        </td></tr>
        <tr><td style="padding:0 28px 24px 28px;border-top:1px solid #E2DDD6;">
          <p style="margin:16px 0 6px 0;font-size:13px;line-height:1.6;color:#4A6572;">
            <strong>Hoe werkt het?</strong><br>
            Open de link op je telefoon of desktop. De portal toont een leesbaar
            overzicht en je kunt PDF's van facturen downloaden. De link is 14
            dagen geldig en kan op elk moment door {safe_inviter} worden ingetrokken.
          </p>
          <p style="margin:16px 0 0 0;font-size:12px;line-height:1.6;color:#4A6572;">
            Heb je de link niet aangevraagd? Negeer deze e-mail.
          </p>
        </td></tr>
      </table>
      <p style="margin:16px 0 0 0;font-size:11px;color:#9CA3AF;">Verzonden via BigDogg · bigdogg.nl</p>
    </td></tr>
  </table>
</body>
</html>"""


@router.get("/invites")
async def list_invites(request: Request):
    user_id = get_user_id(request)
    result = supabase.table("accountant_invites")\
        .select("token, email, used, expires_at, created_at")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True).execute()
    return {"invites": result.data or []}


@router.delete("/invites/{token}")
async def cancel_invite(token: str, request: Request):
    """Revoke a link. We soft-revoke by setting used=true so the row stays
    around for audit + so the token can never be reused."""
    user_id = get_user_id(request)
    supabase.table("accountant_invites").update({"used": True})\
        .eq("user_id", user_id).eq("token", token).execute()
    return {"success": True}


@router.post("/invites/{token}/extend")
async def extend_invite(token: str, request: Request):
    """Push expires_at out by another 14 days."""
    user_id = get_user_id(request)
    new_expiry = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    supabase.table("accountant_invites").update({
        "expires_at": new_expiry,
        "used": False,
    }).eq("user_id", user_id).eq("token", token).execute()
    return {"success": True, "expires_at": new_expiry}


# ─── Accountant portal — public, token-gated ─────────────────
@router.get("/portal/{token}")
async def portal_meta(token: str):
    """Public landing info — owner name, expiry, link status."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    inviter_name = ""
    business_name = ""
    kvk = ""
    btw = ""
    try:
        prof = supabase.table("user_profiles")\
            .select("business_name, full_name, kvk_number, btw_number")\
            .eq("id", owner_id).limit(1).execute()
        if prof.data:
            p = prof.data[0]
            business_name = (p.get("business_name") or "").strip()
            inviter_name = (
                business_name
                or (p.get("full_name") or "").strip()
                or "BigDogg-gebruiker"
            )
            kvk = (p.get("kvk_number") or "").strip()
            btw = (p.get("btw_number") or "").strip()
    except Exception:
        pass
    return {
        "owner_name":     inviter_name,
        "business_name":  business_name,
        "kvk_number":     kvk,
        "btw_number":     btw,
        "invite_email":   row.get("email"),
        "expires_at":     row.get("expires_at"),
        "created_at":     row.get("created_at"),
    }


@router.get("/portal/{token}/overview")
async def portal_overview(token: str):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    year = datetime.now().year
    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"

    inv = supabase.table("invoices")\
        .select("total_excl_btw, total_incl_btw, btw_amount, status, issue_date")\
        .eq("user_id", owner_id)\
        .gte("issue_date", year_start).lte("issue_date", year_end).execute()
    exp = supabase.table("expenses")\
        .select("amount_excl_btw, amount_incl_btw, btw_amount, expense_date")\
        .eq("user_id", owner_id)\
        .gte("expense_date", year_start).lte("expense_date", year_end).execute()

    revenue_excl = sum(float(r.get("total_excl_btw") or 0) for r in (inv.data or []))
    revenue_incl = sum(float(r.get("total_incl_btw") or 0) for r in (inv.data or []))
    btw_collected = sum(float(r.get("btw_amount") or 0) for r in (inv.data or []))
    paid_count = sum(1 for r in (inv.data or []) if (r.get("status") or "").lower() == "paid")

    expense_excl = sum(float(r.get("amount_excl_btw") or 0) for r in (exp.data or []))
    expense_incl = sum(float(r.get("amount_incl_btw") or 0) for r in (exp.data or []))
    btw_paid = sum(float(r.get("btw_amount") or 0) for r in (exp.data or []))

    return {
        "year":          year,
        "revenue_excl":  round(revenue_excl, 2),
        "revenue_incl":  round(revenue_incl, 2),
        "btw_collected": round(btw_collected, 2),
        "expense_excl":  round(expense_excl, 2),
        "expense_incl":  round(expense_incl, 2),
        "btw_paid":      round(btw_paid, 2),
        "btw_payable":   round(btw_collected - btw_paid, 2),
        "profit_excl":   round(revenue_excl - expense_excl, 2),
        "invoice_count": len(inv.data or []),
        "paid_count":    paid_count,
        "expense_count": len(exp.data or []),
    }


@router.get("/portal/{token}/invoices")
async def portal_invoices(token: str):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    rows = supabase.table("invoices")\
        .select("id, invoice_number, client_name, client_company, "
                "total_incl_btw, total_excl_btw, btw_amount, "
                "issue_date, due_date, status")\
        .eq("user_id", owner_id)\
        .order("issue_date", desc=True).execute()
    return {"invoices": rows.data or []}


@router.get("/portal/{token}/expenses")
async def portal_expenses(token: str):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    rows = supabase.table("expenses")\
        .select("id, vendor, description, amount_incl_btw, "
                "amount_excl_btw, btw_amount, category, "
                "expense_date, payment_method, receipt_url")\
        .eq("user_id", owner_id)\
        .order("expense_date", desc=True).execute()
    return {"expenses": rows.data or []}


@router.get("/portal/{token}/invoices/{invoice_id}/pdf")
async def portal_invoice_pdf(token: str, invoice_id: str):
    """Generate the invoice PDF on demand, scoped to the link's owner."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]

    invoice_result = supabase.table("invoices")\
        .select("*, clients(*)")\
        .eq("id", invoice_id)\
        .eq("user_id", owner_id)\
        .single().execute()
    if not invoice_result.data:
        raise HTTPException(status_code=404, detail="invoice_not_found")

    lines_result = supabase.table("invoice_lines")\
        .select("*").eq("invoice_id", invoice_id).execute()

    profile_result = supabase.table("user_profiles")\
        .select("*").eq("id", owner_id).execute()

    invoice = invoice_result.data
    lines = lines_result.data
    profile = profile_result.data[0] if profile_result.data else {}
    client = invoice.get("clients") or {
        "contact_name":  invoice.get("client_name", ""),
        "email":         invoice.get("client_email", ""),
        "company_name":  invoice.get("client_company", ""),
    }

    # Re-use the same PDF generator the owner-facing endpoint uses.
    from app.routers.pdf import _generate_pdf
    sender_email = ""
    try:
        owner_email = supabase.auth.admin.get_user_by_id(owner_id)
        sender_email = (owner_email.user.email or "")
    except Exception:
        pass

    pdf_bytes = _generate_pdf(invoice, lines, profile, client, sender_email)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename={invoice['invoice_number']}.pdf"
        },
    )

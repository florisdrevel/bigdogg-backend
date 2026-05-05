from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.config import settings
from app.routers.pdf import _generate_pdf
from app.routers.quotes import _generate_quote_pdf
from datetime import datetime, timezone
import resend
import base64

router = APIRouter()
resend.api_key = settings.resend_api_key


def get_user_id_and_email(request: Request):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id, user.user.email or ''
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/invoice/{invoice_id}")
async def send_invoice_email(invoice_id: str, request: Request):
    user_id, sender_email = get_user_id_and_email(request)

    try:
        invoice_result = supabase.table("invoices")\
            .select("*, clients(*)")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not invoice_result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")

        lines_result = supabase.table("invoice_lines")\
            .select("*")\
            .eq("invoice_id", invoice_id)\
            .execute()

        profile_result = supabase.table("user_profiles")\
            .select("*")\
            .eq("id", user_id)\
            .execute()

        invoice = invoice_result.data
        lines = lines_result.data
        profile = profile_result.data[0] if profile_result.data else {}

        client = invoice.get("clients") or {
            "contact_name": invoice.get("client_name", ""),
            "email": invoice.get("client_email", ""),
            "company_name": invoice.get("client_company", ""),
        }

        client_email = client.get("email") or invoice.get("client_email", "")
        if not client_email:
            raise HTTPException(
                status_code=400, detail="Client has no email address"
            )

        pdf_bytes = _generate_pdf(invoice, lines, profile, client, sender_email)
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

        sender_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
        invoice_number = invoice['invoice_number']
        total = invoice['total_incl_btw']
        due_date = invoice['due_date']
        client_name = client.get('contact_name', '')
        iban = profile.get('iban', '')
        payment_link = invoice.get('payment_link')

        subject = f"Factuur {invoice_number} — {sender_name}"

        # Build payment section based on whether link exists
        if payment_link:
            payment_section = f"""Wij verzoeken u vriendelijk het bedrag vóór {due_date} te voldoen.

U kunt direct online betalen via de onderstaande betaallink:

👉 {payment_link}

Of maak het bedrag over naar:
IBAN: {iban}
Ten name van: {sender_name}
Onder vermelding van: {invoice_number}"""
        else:
            payment_section = f"""Wij verzoeken u vriendelijk het bedrag vóór {due_date} over te maken naar:

IBAN: {iban}
Ten name van: {sender_name}
Onder vermelding van: {invoice_number}"""

        body = f"""Beste {client_name},

Hierbij ontvangt u factuur {invoice_number} voor een totaalbedrag van € {total}.

{payment_section}

De factuur is als PDF bijgevoegd bij deze e-mail.

Heeft u vragen over deze factuur? Neem dan contact op via {sender_email}.

Met vriendelijke groet,

{sender_name}
{sender_email}

---
Dit bericht is verzonden via BigDogg · bigdogg.nl
"""

        resend.Emails.send({
            "from": f"{sender_name} <info@bigdogg.nl>",
            "to": [client_email],
            "subject": subject,
            "text": body,
            "attachments": [
                {
                    "filename": f"{invoice_number}.pdf",
                    "content": pdf_base64,
                }
            ],
        })

        supabase.table("invoices")\
            .update({"status": "sent"})\
            .eq("id", invoice_id)\
            .execute()

        return {"message": "Invoice sent successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Email error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/quote/{quote_id}")
async def send_quote_email(quote_id: str, request: Request):
    """
    Email a quote PDF (OFFERTE) to the client. Mirrors send_invoice_email
    but uses the quote PDF generator and Dutch quote-specific email body.
    Sets the quote status to 'sent' on success.
    """
    user_id, sender_email = get_user_id_and_email(request)

    try:
        quote_result = supabase.table("quotes")\
            .select("*, clients(*)")\
            .eq("id", quote_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not quote_result.data:
            raise HTTPException(status_code=404, detail="Quote not found")

        lines_result = supabase.table("quote_lines")\
            .select("*")\
            .eq("quote_id", quote_id)\
            .execute()

        profile_result = supabase.table("user_profiles")\
            .select("*")\
            .eq("id", user_id)\
            .execute()

        quote = quote_result.data
        lines = lines_result.data or []
        profile = profile_result.data[0] if profile_result.data else {}

        client = quote.get("clients") or {
            "contact_name": quote.get("client_name", ""),
            "email": quote.get("client_email", ""),
            "company_name": quote.get("client_company", ""),
        }

        client_email = client.get("email") or quote.get("client_email", "")
        if not client_email:
            raise HTTPException(
                status_code=400, detail="Client has no email address"
            )

        pdf_bytes = _generate_quote_pdf(quote, lines, profile, client, sender_email)
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

        sender_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
        quote_number = quote['quote_number']
        total = quote['total_incl_btw']
        valid_until = quote.get('valid_until') or ''
        client_name = client.get('contact_name', '')

        # Public landing-page URL — recipient can view + accept/decline
        # without a BigDogg account. share_token is auto-generated by the
        # quotes_share_token migration; backfill on the fly if it's null.
        share_token = quote.get("share_token")
        if not share_token:
            import uuid as _uuid
            share_token = str(_uuid.uuid4())
            supabase.table("quotes")\
                .update({"share_token": share_token})\
                .eq("id", quote_id)\
                .execute()
        # Backend share-link domain so WhatsApp / email clients show a
        # personalized preview ("Offerte X van Y") instead of the
        # generic bigdogg.nl landing page.
        share_url = f"https://bigdogg-production.up.railway.app/q/{share_token}"

        subject = f"Offerte {quote_number} — {sender_name}"

        validity_line = (
            f"Deze offerte is geldig tot {valid_until}." if valid_until else
            "Deze offerte is vrijblijvend."
        )

        text_body = f"""Beste {client_name},

Hierbij ontvangt u onze offerte {quote_number} voor een totaalbedrag van € {total}.

{validity_line}

Bekijk de offerte online en accepteer of wijs af met één klik:
{share_url}

De offerte is ook als PDF bijgevoegd bij deze e-mail.

Heeft u vragen? Neem dan contact op via {sender_email}.

Met vriendelijke groet,

{sender_name}
{sender_email}

---
Dit bericht is verzonden via BigDogg · bigdogg.nl
"""

        # HTML version — gives the recipient real Accept / Decline buttons.
        # The buttons are just styled links to the public landing page; the
        # actual state change happens after they confirm on that page.
        html_body = f"""<!DOCTYPE html>
<html lang="nl">
<body style="margin:0;padding:0;background:#F5F3EF;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1B3A4B;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F3EF;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;border:1px solid #E2DDD6;overflow:hidden;">
        <tr><td style="padding:24px 28px 8px 28px;">
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">Beste {client_name},</p>
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">
            Hierbij ontvangt u onze offerte
            <strong style="color:#1B3A4B;">{quote_number}</strong>
            voor een totaalbedrag van
            <strong>€ {total}</strong>.
          </p>
          <p style="margin:0 0 24px 0;font-size:14px;line-height:1.6;color:#4A6572;">{validity_line}</p>
        </td></tr>
        <tr><td align="center" style="padding:8px 28px 4px 28px;">
          <a href="{share_url}" style="display:inline-block;background:#10B981;color:#ffffff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;margin:6px;">Accepteer offerte</a>
          <a href="{share_url}" style="display:inline-block;background:#ffffff;color:#1B3A4B;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;border:1.5px solid #E2DDD6;margin:6px;">Bekijk online</a>
        </td></tr>
        <tr><td align="center" style="padding:0 28px 24px 28px;">
          <p style="margin:12px 0 0 0;font-size:12px;color:#4A6572;">
            of plak deze link in uw browser:<br>
            <a href="{share_url}" style="color:#1B3A4B;word-break:break-all;">{share_url}</a>
          </p>
        </td></tr>
        <tr><td style="padding:0 28px 24px 28px;border-top:1px solid #E2DDD6;">
          <p style="margin:16px 0 0 0;font-size:14px;line-height:1.6;color:#4A6572;">
            De offerte is ook als PDF bijgevoegd. Heeft u vragen? Neem contact op via <a href="mailto:{sender_email}" style="color:#1B3A4B;">{sender_email}</a>.
          </p>
          <p style="margin:16px 0 0 0;font-size:14px;line-height:1.6;color:#1B3A4B;">
            Met vriendelijke groet,<br>
            <strong>{sender_name}</strong>
          </p>
        </td></tr>
      </table>
      <p style="margin:16px 0 0 0;font-size:11px;color:#9CA3AF;">Verzonden via BigDogg · bigdogg.nl</p>
    </td></tr>
  </table>
</body>
</html>"""

        resend.Emails.send({
            "from": f"{sender_name} <info@bigdogg.nl>",
            "to": [client_email],
            "subject": subject,
            "text": text_body,
            "html": html_body,
            "attachments": [
                {
                    "filename": f"{quote_number}.pdf",
                    "content": pdf_base64,
                }
            ],
        })

        # Bump status to 'sent' if it was still a draft.
        if quote.get("status") == "draft":
            supabase.table("quotes")\
                .update({
                    "status": "sent",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })\
                .eq("id", quote_id)\
                .execute()

        return {"message": "Quote sent successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Quote email error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
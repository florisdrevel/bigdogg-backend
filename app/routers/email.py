from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from app.config import settings
from app.routers.pdf import _generate_pdf
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

router = APIRouter()


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


@router.post("/invoice/{invoice_id}")
async def send_invoice_email(invoice_id: str, request: Request):
    user_id = get_user_id(request)

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
        client = invoice.get("clients", {})

        client_email = client.get("email")
        if not client_email:
            raise HTTPException(status_code=400, detail="Client has no email address")

        pdf_bytes = _generate_pdf(invoice, lines, profile, client)

        sender_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
        invoice_number = invoice['invoice_number']
        total = invoice['total_incl_btw']
        due_date = invoice['due_date']
        client_name = client.get('contact_name', '')
        iban = profile.get('iban', '')

        subject = f"Factuur {invoice_number} — {sender_name}"

        body = f"""Beste {client_name},

Hierbij ontvangt u factuur {invoice_number} voor een totaalbedrag van € {total}.

Wij verzoeken u vriendelijk het bedrag vóór {due_date} over te maken naar:

IBAN: {iban}
Ten name van: {sender_name}
Onder vermelding van: {invoice_number}

De factuur is als PDF bijgevoegd bij deze e-mail.

Heeft u vragen over deze factuur? Neem dan gerust contact met ons op.

Met vriendelijke groet,

{sender_name}

---
Dit bericht is verzonden via BigDogg · bigdogg.nl
"""

        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{settings.gmail_user}>"
        msg['To'] = client_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(pdf_bytes)
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename="{invoice_number}.pdf"')
        msg.attach(attachment)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, client_email, msg.as_string())

        supabase.table("invoices")\
            .update({"status": "sent"})\
            .eq("id", invoice_id)\
            .execute()

        return {"message": "Invoice sent successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
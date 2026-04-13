from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from app.database import supabase
from app.config import settings
from datetime import date, timedelta
import resend

router = APIRouter()
resend.api_key = settings.resend_api_key


class InvoiceLine(BaseModel):
    description: str
    quantity: float
    unit_price_ex_btw: float
    btw_rate: int = 21


class InvoiceCreate(BaseModel):
    client_id: str
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    lines: List[InvoiceLine]
    notes: Optional[str] = None


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


def generate_invoice_number(user_id: str) -> str:
    year = date.today().year
    result = supabase.table("invoices")\
        .select("invoice_number")\
        .eq("user_id", user_id)\
        .like("invoice_number", f"{year}-%")\
        .order("invoice_number", desc=True)\
        .limit(1)\
        .execute()
    if result.data:
        last_num = int(result.data[0]["invoice_number"].split("-")[1])
        return f"{year}-{str(last_num + 1).zfill(6)}"
    return f"{year}-000001"


@router.get("/")
async def get_invoices(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("invoices")\
            .select("*, clients(contact_name, company_name, email)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return {"invoices": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        invoice = supabase.table("invoices")\
            .select("*, clients(*)")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        lines = supabase.table("invoice_lines")\
            .select("*")\
            .eq("invoice_id", invoice_id)\
            .execute()
        return {"invoice": invoice.data, "lines": lines.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_invoice(invoice: InvoiceCreate, request: Request):
    user_id = get_user_id(request)
    try:
        invoice_number = generate_invoice_number(user_id)
        invoice_date = invoice.invoice_date or date.today().isoformat()
        due_date = invoice.due_date or (date.today() + timedelta(days=30)).isoformat()

        subtotal = sum(l.quantity * l.unit_price_ex_btw for l in invoice.lines)
        btw_amount = sum(l.quantity * l.unit_price_ex_btw * l.btw_rate / 100 for l in invoice.lines)
        total = subtotal + btw_amount

        client_result = supabase.table("clients")\
            .select("contact_name, email, company_name")\
            .eq("id", invoice.client_id)\
            .single()\
            .execute()
        client_data = client_result.data or {}

        invoice_response = supabase.table("invoices").insert({
            "user_id": user_id,
            "client_id": invoice.client_id,
            "client_name": client_data.get("contact_name", ""),
            "client_email": client_data.get("email", ""),
            "client_company": client_data.get("company_name", ""),
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "status": "draft",
            "subtotal_ex_btw": round(subtotal, 2),
            "btw_amount": round(btw_amount, 2),
            "total_incl_btw": round(total, 2),
            "notes": invoice.notes,
        }).execute()

        invoice_id = invoice_response.data[0]['id']

        lines_data = [{
            "invoice_id": invoice_id,
            "description": l.description,
            "quantity": l.quantity,
            "unit_price_ex_btw": l.unit_price_ex_btw,
            "btw_rate": l.btw_rate,
            "line_total_ex_btw": round(l.quantity * l.unit_price_ex_btw, 2),
        } for l in invoice.lines]
        supabase.table("invoice_lines").insert(lines_data).execute()

        # Auto-generate payment link if Stripe is connected
        payment_link_url = None
        try:
            profile_result = supabase.table("user_profiles")\
                .select("stripe_connect_account_id, stripe_connect_enabled, business_name, full_name")\
                .eq("id", user_id)\
                .execute()
            profile = profile_result.data[0] if profile_result.data else {}
            account_id = profile.get("stripe_connect_account_id")

            if account_id and profile.get("stripe_connect_enabled"):
                import stripe as stripe_lib
                stripe_lib.api_key = settings.stripe_secret_key

                business_name = profile.get("business_name") or profile.get("full_name") or "BigDogg"
                total_cents = int(round(total, 2) * 100)

                product = stripe_lib.Product.create(
                    name=f"Factuur {invoice_number} — {business_name}",
                    stripe_account=account_id,
                )
                price = stripe_lib.Price.create(
                    product=product.id,
                    unit_amount=total_cents,
                    currency="eur",
                    stripe_account=account_id,
                )
                payment_link = stripe_lib.PaymentLink.create(
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
                payment_link_url = payment_link.url

                supabase.table("invoices").update({
                    "payment_link": payment_link_url,
                    "payment_link_id": payment_link.id,
                }).eq("id", invoice_id).execute()

                print(f"Auto-generated payment link for invoice {invoice_number}")
        except Exception as e:
            print(f"Auto payment link failed (non-fatal): {e}")

        return {
            "invoice": invoice_response.data[0],
            "invoice_number": invoice_number,
            "payment_link": payment_link_url,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{invoice_id}/status")
async def update_status(invoice_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
        status = body.get("status")
        supabase.table("invoices")\
            .update({"status": status})\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .execute()
        return {"message": "Status updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{invoice_id}/reminder")
async def send_reminder(invoice_id: str, request: Request):
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

        profile_result = supabase.table("user_profiles")\
            .select("*")\
            .eq("id", user_id)\
            .execute()

        invoice = invoice_result.data
        client = invoice.get("clients") or {}
        profile = profile_result.data[0] if profile_result.data else {}

        sender_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
        client_name = client.get('contact_name') or invoice.get('client_name', '')
        client_email = client.get('email') or invoice.get('client_email', '')
        invoice_number = invoice['invoice_number']
        total = invoice['total_incl_btw']
        due_date = invoice['due_date']
        iban = profile.get('iban', '')
        reminder_count = (invoice.get("reminder_count") or 0) + 1

        if reminder_count == 1:
            subject = f"Herinnering: Factuur {invoice_number} — {sender_name}"
            intro = "Wij willen u vriendelijk herinneren aan de onderstaande openstaande factuur."
        else:
            subject = f"2e Herinnering: Factuur {invoice_number} — {sender_name}"
            intro = f"Dit is onze {reminder_count}e herinnering voor de onderstaande openstaande factuur. Wij verzoeken u dringend het bedrag zo spoedig mogelijk te voldoen."

        body = f"""Beste {client_name},

{intro}

Factuurnummer: {invoice_number}
Bedrag: € {total}
Vervaldatum: {due_date}

Wij verzoeken u het bedrag over te maken naar:
IBAN: {iban}
Ten name van: {sender_name}
Onder vermelding van: {invoice_number}

Heeft u al betaald? Dan kunt u deze herinnering als niet verzonden beschouwen.
Heeft u vragen? Neem dan contact met ons op.

Met vriendelijke groet,

{sender_name}

---
Dit bericht is verzonden via BigDogg · bigdogg.nl
"""

        if client_email and settings.resend_api_key:
            resend.Emails.send({
                "from": f"{sender_name} <info@bigdogg.nl>",
                "to": [client_email],
                "subject": subject,
                "text": body,
            })

        supabase.table("invoices")\
            .update({"reminder_count": reminder_count})\
            .eq("id", invoice_id)\
            .execute()

        return {
            "message": "Reminder sent",
            "client_email": client_email,
            "invoice_number": invoice_number,
            "reminder_count": reminder_count,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        invoice = supabase.table("invoices")\
            .select("status")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        if not invoice.data:
            raise HTTPException(status_code=404, detail="Invoice not found")
        if invoice.data["status"] != "draft":
            raise HTTPException(status_code=400, detail="Only draft invoices can be deleted")
        supabase.table("invoice_lines").delete().eq("invoice_id", invoice_id).execute()
        supabase.table("invoices").delete().eq("id", invoice_id).eq("user_id", user_id).execute()
        return {"message": "Invoice deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
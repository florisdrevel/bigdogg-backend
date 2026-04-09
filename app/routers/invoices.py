from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, timedelta
from app.database import supabase

router = APIRouter()


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


def get_next_invoice_number(user_id: str) -> str:
    year = date.today().year
    result = supabase.table("invoices")\
        .select("invoice_number")\
        .eq("user_id", user_id)\
        .like("invoice_number", f"{year}-%")\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()
    if not result.data:
        return f"{year}-000001"
    last = result.data[0]['invoice_number']
    last_num = int(last.split("-")[1])
    return f"{year}-{str(last_num + 1).zfill(6)}"


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
        invoice_number = get_next_invoice_number(user_id)
        invoice_date = invoice.invoice_date or str(date.today())
        due_date = invoice.due_date or str(date.today() + timedelta(days=30))

        subtotal = sum(l.quantity * l.unit_price_ex_btw for l in invoice.lines)
        btw_amount = sum(
            l.quantity * l.unit_price_ex_btw * l.btw_rate / 100
            for l in invoice.lines
        )
        total = subtotal + btw_amount

        invoice_response = supabase.table("invoices").insert({
            "user_id": user_id,
            "client_id": invoice.client_id,
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

        return {"invoice": invoice_response.data[0], "invoice_number": invoice_number}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{invoice_id}/status")
async def update_status(invoice_id: str, request: Request):
    user_id = get_user_id(request)
    body = await request.json()
    status = body.get("status")
    if status not in ["draft", "sent", "paid", "overdue"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    try:
        update_data = {"status": status}
        if status == "paid":
            from datetime import datetime
            update_data["paid_at"] = datetime.utcnow().isoformat()
        supabase.table("invoices")\
            .update(update_data)\
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
        invoice = supabase.table("invoices")\
            .select("*, clients(*)")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not invoice.data:
            raise HTTPException(status_code=404, detail="Invoice not found")

        supabase.table("invoices")\
            .update({
                "reminder_count": (invoice.data.get("reminder_count") or 0) + 1,
                "last_reminder_at": date.today().isoformat()
            })\
            .eq("id", invoice_id)\
            .execute()

        return {
            "message": "Reminder sent",
            "client_email": invoice.data["clients"]["email"],
            "invoice_number": invoice.data["invoice_number"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
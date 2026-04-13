from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from typing import List
from datetime import date, datetime
from app.database import supabase
from app.config import settings
import anthropic
import base64
import json
import re

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


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text.strip())


async def _parse_invoice_pdf(content: bytes, filename: str) -> dict:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    base64_data = base64.standard_b64encode(content).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64_data,
                    },
                },
                {
                    "type": "text",
                    "text": """Extract the key financial data from this invoice.
Return ONLY a JSON object, no markdown fences:
{
  "invoice_number": "invoice number or null",
  "invoice_date": "YYYY-MM-DD or null",
  "client_name": "client/company name",
  "description": "brief description of services/products, max 80 chars",
  "subtotal_ex_btw": 0.00,
  "btw_amount": 0.00,
  "total_incl_btw": 0.00,
  "btw_rate": 21
}

Rules:
- All amounts as numbers
- btw_rate: 21, 9, or 0
- Use today's date if invoice_date not found
- Keep description concise"""
                }
            ],
        }],
    )

    raw = message.content[0].text.strip()
    return _extract_json(raw)


@router.post("/import-invoices")
async def import_invoices(
    request: Request,
    files: List[UploadFile] = File(...),
):
    user_id = get_user_id(request)

    imported = []
    failed = []

    for file in files:
        try:
            content = await file.read()
            filename = file.filename or "invoice.pdf"
            print(f"IMPORTING: {filename}, size={len(content)}")

            parsed = await _parse_invoice_pdf(content, filename)

            invoice_date = parsed.get("invoice_date") or str(date.today())
            subtotal = float(parsed.get("subtotal_ex_btw") or 0)
            btw_amount = float(parsed.get("btw_amount") or 0)
            total = float(parsed.get("total_incl_btw") or subtotal + btw_amount)
            btw_rate = int(parsed.get("btw_rate") or 21)

            # Recalculate if amounts seem off
            if subtotal == 0 and total > 0:
                subtotal = round(total / (1 + btw_rate / 100), 2)
                btw_amount = round(total - subtotal, 2)

            invoice_number = parsed.get("invoice_number") or f"IMP-{filename[:20]}"
            client_name = parsed.get("client_name") or "Unknown"
            description = parsed.get("description") or filename

            result = supabase.table("invoices").insert({
                "user_id": user_id,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "client_name": client_name,
                "subtotal_ex_btw": subtotal,
                "btw_amount": btw_amount,
                "total_incl_btw": total,
                "btw_rate": btw_rate,
                "status": "paid",
                "is_imported": True,
                "notes": description,
            }).execute()

            imported.append({
                "filename": filename,
                "invoice_number": invoice_number,
                "client_name": client_name,
                "total": total,
                "date": invoice_date,
            })

        except Exception as e:
            print(f"IMPORT ERROR for {file.filename}: {e}")
            failed.append({"filename": file.filename, "error": str(e)})

    return {
        "imported": imported,
        "failed": failed,
        "total_imported": len(imported),
        "total_failed": len(failed),
    }
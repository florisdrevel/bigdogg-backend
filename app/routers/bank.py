"""
Bank statement PDF parser — dedicated multi-transaction endpoint.

Unlike /expenses/parse-receipt (which is built for a single receipt and
returns one transaction), this endpoint is meant for a full bank
statement PDF that contains many lines. It sends the PDF to Claude as a
`document` content block and asks for every transaction back as a JSON
array.

  POST /api/v1/bank/parse-statement   (multipart/form-data, field "file")
    → { "transactions": [...], "count": N, "bank": "ING" | "unknown" }
    → on no transactions: { "error": "...", "transactions": [], "count": 0 }

The frontend shows the parsed list with checkboxes; selected rows are
imported as expenses via POST /expenses/.
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from app.database import supabase
from app.config import settings
from app.services.ai_quota import require_ai_quota, record_ai_usage
import anthropic
import base64
import json

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


_PROMPT = """You are reading a Dutch bank statement (bankafschrift) PDF.

Extract EVERY transaction line. Return ONLY a raw JSON object — no
markdown, no code fences, no commentary. Start with { and end with }.

Shape:
{
  "bank": "detected bank name (ING, Rabobank, ABN AMRO, SNS, ASN, Triodos, bunq, Knab, Revolut, N26) or 'unknown'",
  "transactions": [
    {
      "date": "YYYY-MM-DD",
      "description": "counterparty + payment reference / mededeling",
      "amount": -45.67
    }
  ]
}

Rules:
- amount is SIGNED: money OUT (debit / af / bij betaling) is NEGATIVE,
  money IN (credit / bij) is POSITIVE.
- Include every transaction row, even small ones.
- Convert any date format (e.g. 14-05-2026, 14 mei 2026) to YYYY-MM-DD.
- description: the counterparty name plus the reference/mededeling if
  present, trimmed to something readable.
- Skip opening/closing balance rows, subtotals, page headers/footers.
- If you cannot find any transactions, return an empty "transactions"
  array.
"""


def _strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        # Drop the first fence line and any trailing fence.
        t = t.split("```", 2)
        # ["", "json\n{...}", ""] or ["", "{...}", ""]
        t = t[1] if len(t) > 1 else text
        if t.lower().startswith("json"):
            t = t[4:]
        t = t.strip()
        if t.endswith("```"):
            t = t[:-3].strip()
    return t


@router.post("/parse-statement")
async def parse_statement(request: Request, file: UploadFile = File(...)):
    user_id = get_user_id(request)
    require_ai_quota(user_id, "parse-statement")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty_file")
    if raw[:5] != b"%PDF-":
        # Be lenient: some browsers send PDFs without a clean header on
        # re-encode, but flag obviously-wrong types.
        if file.content_type and "pdf" not in (file.content_type or "").lower():
            return {
                "error": "Dit lijkt geen PDF te zijn.",
                "transactions": [],
                "count": 0,
                "bank": "unknown",
            }

    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ai_not_configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    b64 = base64.standard_b64encode(raw).decode("utf-8")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": _PROMPT},
                ],
            }],
        )
    except Exception as e:
        print(f"[bank] Claude call failed: {e}")
        raise HTTPException(status_code=502, detail="ai_request_failed")

    record_ai_usage(user_id, "parse-statement", message)
    raw_text = _strip_fences(message.content[0].text)

    try:
        parsed = json.loads(raw_text)
    except Exception as e:
        print(f"[bank] JSON parse failed: {e} — head: {raw_text[:200]}")
        return {
            "error": "Geen transacties gevonden in dit document",
            "transactions": [],
            "count": 0,
            "bank": "unknown",
        }

    bank = "unknown"
    rows = []
    if isinstance(parsed, dict):
        bank = (parsed.get("bank") or "unknown").strip() or "unknown"
        rows = parsed.get("transactions") or []
    elif isinstance(parsed, list):
        rows = parsed

    transactions = []
    for tx in rows:
        if not isinstance(tx, dict):
            continue
        date_str = (tx.get("date") or "").strip()
        description = (tx.get("description") or "").strip()
        try:
            amount = round(float(tx.get("amount") or 0), 2)
        except (TypeError, ValueError):
            amount = 0.0
        if not description and amount == 0.0:
            continue
        transactions.append({
            "date": date_str,
            "description": description,
            "amount": amount,
        })

    if not transactions:
        return {
            "error": "Geen transacties gevonden in dit document",
            "transactions": [],
            "count": 0,
            "bank": bank,
        }

    return {
        "transactions": transactions,
        "count": len(transactions),
        "bank": bank,
    }

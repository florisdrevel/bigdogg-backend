from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from typing import List, Optional
from datetime import date, timedelta
from app.database import supabase
from app.config import settings
from app.routers.subscription import require_active_paid
import anthropic
import base64
import json
import re

router = APIRouter()

# Frontend asset deploy marker — bumped to force Railway redeploy.
_DEPLOY_MARKER = "2026-05-02-walkthrough-toggles"


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
    text = text.strip()
    text = re.sub(r'"\s*\n\s*"', '",\n  "', text)
    text = re.sub(r'(\d)\s*\n\s*"', r'\1,\n  "', text)
    return json.loads(text)


def _log_file_import(
    user_id: str,
    filename: str,
    import_type: str,
    *,
    imported: int = 0,
    duplicates: int = 0,
    failed: int = 0,
    error: Optional[str] = None,
) -> None:
    """
    Records one row in file_imports per uploaded file. Status is derived:
      - failed   → file errored out before any record was written
      - success  → at least one record imported, nothing else went wrong
      - partial  → mixed (e.g. duplicates, or some succeeded some failed)

    All errors are swallowed: if the file_imports table doesn't exist yet
    (migration not applied) we do NOT want to break the user's import flow.
    """
    if failed > 0 and imported == 0 and duplicates == 0:
        status = "failed"
    elif imported > 0 and (duplicates > 0 or failed > 0):
        status = "partial"
    elif imported > 0:
        status = "success"
    elif duplicates > 0 and failed == 0:
        # Pure duplicate — nothing imported, nothing failed.
        status = "partial"
    else:
        status = "failed"

    try:
        supabase.table("file_imports").insert({
            "user_id": user_id,
            "filename": filename,
            "import_type": import_type,
            "records_imported": imported,
            "records_duplicate": duplicates,
            "records_failed": failed,
            "status": status,
            "error_message": error,
        }).execute()
    except Exception as e:
        print(f"[file_imports] log skipped ({type(e).__name__}): {e}")


async def _parse_invoice_file(content: bytes, filename: str, content_type: str) -> dict:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    base64_data = base64.standard_b64encode(content).decode("utf-8")

    ext = filename.lower().split(".")[-1]
    is_pdf = ext == "pdf" or content_type == "application/pdf"

    prompt_text = """Extract the key financial data from this invoice or screenshot.
Return ONLY a valid JSON object, no markdown fences, no missing commas:
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
- Keep description concise
- Ensure valid JSON with commas between all fields"""

    if is_pdf:
        content_block = {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64_data,
            },
        }
    else:
        media_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "heic": "image/jpeg",
            "heif": "image/jpeg",
        }
        media_type = media_type_map.get(ext, "image/jpeg")
        if content_type.startswith("image/") and ext not in media_type_map:
            media_type = content_type

        if len(content) > 4 * 1024 * 1024:
            try:
                from PIL import Image as PILImage
                import io
                img = PILImage.open(io.BytesIO(content))
                img.thumbnail((1920, 1920))
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=75)
                content = buf.getvalue()
                base64_data = base64.standard_b64encode(content).decode("utf-8")
                media_type = "image/jpeg"
            except Exception as e:
                print(f"RESIZE ERROR: {e}")

        content_block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_data,
            },
        }

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                content_block,
                {"type": "text", "text": prompt_text}
            ],
        }],
    )

    raw = message.content[0].text.strip()
    print(f"IMPORT PARSE RESPONSE: {raw}")
    return _extract_json(raw)


@router.post("/import-invoices")
async def import_invoices(
    request: Request,
    files: List[UploadFile] = File(...),
):
    user_id = get_user_id(request)
    require_active_paid(user_id)

    imported = []
    failed = []
    duplicates = []

    for file in files:
        filename = file.filename or "invoice.pdf"
        try:
            content = await file.read()
            content_type = file.content_type or "application/pdf"
            print(f"IMPORTING: {filename}, type={content_type}, size={len(content)}")

            parsed = await _parse_invoice_file(content, filename, content_type)

            invoice_date = parsed.get("invoice_date") or str(date.today())
            subtotal = float(parsed.get("subtotal_ex_btw") or 0)
            btw_amount = float(parsed.get("btw_amount") or 0)
            total = float(parsed.get("total_incl_btw") or subtotal + btw_amount)
            btw_rate = int(parsed.get("btw_rate") or 21)

            if subtotal == 0 and total > 0:
                subtotal = round(total / (1 + btw_rate / 100), 2)
                btw_amount = round(total - subtotal, 2)

            invoice_number = parsed.get("invoice_number") or f"IMP-{filename[:20]}"
            client_name = parsed.get("client_name") or "Unknown"
            description = parsed.get("description") or filename

            existing_by_number = supabase.table("invoices")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("invoice_number", invoice_number)\
                .execute()

            if existing_by_number.data:
                duplicates.append({
                    "filename": filename,
                    "invoice_number": invoice_number,
                    "reason": "Invoice number already exists"
                })
                _log_file_import(user_id, filename, "invoice", duplicates=1)
                continue

            existing_by_amount = supabase.table("invoices")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("invoice_date", invoice_date)\
                .eq("total_incl_btw", total)\
                .execute()

            if existing_by_amount.data:
                duplicates.append({
                    "filename": filename,
                    "invoice_number": invoice_number,
                    "reason": "Same date and amount already exists"
                })
                _log_file_import(user_id, filename, "invoice", duplicates=1)
                continue

            try:
                inv_date = date.fromisoformat(invoice_date)
                due_date = str(inv_date + timedelta(days=30))
            except Exception:
                due_date = str(date.today() + timedelta(days=30))

            supabase.table("invoices").insert({
                "user_id": user_id,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "due_date": due_date,
                "client_name": client_name,
                "subtotal_ex_btw": subtotal,
                "btw_amount": btw_amount,
                "total_incl_btw": total,
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
            _log_file_import(user_id, filename, "invoice", imported=1)

        except Exception as e:
            print(f"IMPORT ERROR for {filename}: {e}")
            failed.append({"filename": filename, "error": str(e)})
            _log_file_import(user_id, filename, "invoice", failed=1, error=str(e))

    return {
        "imported": imported,
        "failed": failed,
        "duplicates": duplicates,
        "total_imported": len(imported),
        "total_failed": len(failed),
        "total_duplicates": len(duplicates),
    }


@router.get("/imported")
async def get_imported_invoices(request: Request):
    user_id = get_user_id(request)
    try:
        result = supabase.table("invoices")\
            .select("id, invoice_number, invoice_date, client_name, subtotal_ex_btw, btw_amount, total_incl_btw, notes")\
            .eq("user_id", user_id)\
            .eq("is_imported", True)\
            .order("invoice_date", desc=True)\
            .execute()
        return {"invoices": result.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/imported/{invoice_id}")
async def delete_imported_invoice(invoice_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("invoices")\
            .delete()\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .eq("is_imported", True)\
            .execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import-expenses")
async def import_expenses(
    request: Request,
    files: List[UploadFile] = File(...),
):
    user_id = get_user_id(request)
    require_active_paid(user_id)

    imported = []
    failed = []
    duplicates = []

    for file in files:
        filename = file.filename or "expense.pdf"
        try:
            content = await file.read()
            content_type = file.content_type or "application/pdf"
            print(f"IMPORTING EXPENSE: {filename}, type={content_type}, size={len(content)}")

            parsed = await _parse_invoice_file(content, filename, content_type)

            expense_date = parsed.get("invoice_date") or str(date.today())
            total = float(parsed.get("total_incl_btw") or 0)
            btw_rate = int(parsed.get("btw_rate") or 21)
            btw_amount = float(parsed.get("btw_amount") or 0)
            amount_ex_btw = float(parsed.get("subtotal_ex_btw") or 0)

            if amount_ex_btw == 0 and total > 0:
                amount_ex_btw = round(total / (1 + btw_rate / 100), 2)
                btw_amount = round(total - amount_ex_btw, 2)

            description = parsed.get("description") or filename
            client_name = parsed.get("client_name") or "Unknown"
            full_description = f"{description} ({client_name})"

            existing = supabase.table("expenses")\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("expense_date", expense_date)\
                .eq("amount_ex_btw", amount_ex_btw)\
                .execute()

            if existing.data:
                duplicates.append({
                    "filename": filename,
                    "description": full_description,
                    "reason": "Same date and amount already exists"
                })
                _log_file_import(user_id, filename, "expense", duplicates=1)
                continue

            supabase.table("expenses").insert({
                "user_id": user_id,
                "description": full_description,
                "amount_ex_btw": amount_ex_btw,
                "btw_amount": btw_amount,
                "btw_rate": btw_rate,
                "expense_date": expense_date,
                "category": "general",
            }).execute()

            imported.append({
                "filename": filename,
                "description": description,
                "total": total,
                "date": expense_date,
            })
            _log_file_import(user_id, filename, "expense", imported=1)

        except Exception as e:
            print(f"IMPORT EXPENSE ERROR for {filename}: {e}")
            failed.append({"filename": filename, "error": str(e)})
            _log_file_import(user_id, filename, "expense", failed=1, error=str(e))

    return {
        "imported": imported,
        "failed": failed,
        "duplicates": duplicates,
        "total_imported": len(imported),
        "total_failed": len(failed),
        "total_duplicates": len(duplicates),
    }


@router.get("/file-imports")
async def list_file_imports(request: Request):
    """
    Unified history of every file the user has uploaded through either
    the invoice import or expense import flow. Powers the "Imported files"
    section on the profile screen.
    """
    user_id = get_user_id(request)
    try:
        result = supabase.table("file_imports")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("imported_at", desc=True)\
            .limit(200)\
            .execute()
        return {"file_imports": result.data or []}
    except Exception as e:
        # Most likely cause: migration not yet applied. Surface gracefully.
        print(f"[file_imports] list failed: {e}")
        return {"file_imports": [], "warning": "file_imports table missing"}


@router.delete("/file-imports/{record_id}")
async def delete_file_import(record_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("file_imports")\
            .delete()\
            .eq("id", record_id)\
            .eq("user_id", user_id)\
            .execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import supabase
from app.config import settings
from app.routers.banking import schedule_reconcile
from app.services.ai_quota import require_ai_quota, record_ai_usage
from app.services.tenant_db import require_owned_id, delete_owned
import anthropic
import base64
import json
import re

router = APIRouter()


class ExpenseCreate(BaseModel):
    description: str
    amount_ex_btw: float
    btw_rate: int = 21
    expense_date: Optional[str] = None
    category: str = "general"
    project_id: Optional[str] = None


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


_SIGNED_URL_TTL = 3600  # 1 hour — long enough for the app to render the
                       # image, short enough to keep blast radius small.


def _signed_receipt_url(receipt_value):
    """Mint a short-lived signed URL for a stored receipt. Accepts both
    the new path format ("<user_id>/<expense_id>.<ext>") and legacy
    public URLs (extracts the path after "/receipts/"). Returns None on
    any failure — callers fall back to whatever was stored.
    """
    if not receipt_value:
        return None
    if receipt_value.startswith("http"):
        marker = "/receipts/"
        idx = receipt_value.find(marker)
        if idx == -1:
            return None
        path = receipt_value[idx + len(marker):]
    else:
        path = receipt_value
    try:
        result = supabase.storage.from_("receipts").create_signed_url(
            path, _SIGNED_URL_TTL,
        )
        return result.get("signedURL") or result.get("signedUrl") or None
    except Exception as e:
        print(f"[receipts] signed URL failed for {path}: {e}")
        return None


@router.get("/")
async def get_expenses(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("expenses")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("expense_date", desc=True)\
            .execute()
        rows = response.data or []
        for exp in rows:
            if exp.get("receipt_url"):
                signed = _signed_receipt_url(exp["receipt_url"])
                if signed:
                    exp["receipt_url"] = signed
        return {"expenses": rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_expense(expense: ExpenseCreate, request: Request):
    user_id = get_user_id(request)
    from app.routers.subscription import require_active_paid
    require_active_paid(user_id)
    try:
        btw_amount = round(expense.amount_ex_btw * expense.btw_rate / 100, 2)
        expense_date = expense.expense_date or str(date.today())
        # Finding #8: verify the project belongs to the caller before linking.
        if expense.project_id:
            require_owned_id("projects", expense.project_id, user_id)
        response = supabase.table("expenses").insert({
            "user_id": user_id,
            "description": expense.description,
            "amount_ex_btw": expense.amount_ex_btw,
            "btw_amount": btw_amount,
            "btw_rate": expense.btw_rate,
            "expense_date": expense_date,
            "category": expense.category,
            **({"project_id": expense.project_id} if expense.project_id else {}),
        }).execute()
        # Fire-and-forget: re-run the bank-tx matcher. If a recently-
        # imported tx corresponds to this fresh expense, the user gets
        # an instant notification + auto-link.
        schedule_reconcile(user_id)
        return {"expense": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _extract_json(text: str) -> dict:
    """Extract JSON from Claude response, handling markdown code fences."""
    # Strip markdown fences if present
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    return json.loads(text)


@router.post("/parse-receipt")
async def parse_receipt(request: Request, file: UploadFile = File(...)):
    user_id = get_user_id(request)
    require_ai_quota(user_id, "parse-receipt")
    try:
        content = await file.read()

        filename = file.filename or "receipt.jpg"
        ext = filename.lower().split(".")[-1]
        content_type = file.content_type or "image/jpeg"

        # Sanitize extension — mobile sometimes sends long numeric filenames
        if len(ext) > 5 or not ext.isalpha():
            # Try to detect from content_type
            ct_map = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/webp": "webp",
                "image/gif": "gif",
                "application/pdf": "pdf",
            }
            ext = ct_map.get(content_type, "jpg")

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        prompt_text = """Analyze this receipt or invoice and extract the expense information.
Return ONLY a JSON object with these exact fields, nothing else, no markdown code fences:
{
  "description": "short description of what was purchased",
  "amount_ex_btw": 0.00,
  "btw_rate": 21,
  "btw_amount": 0.00,
  "expense_date": "YYYY-MM-DD",
  "category": "general"
}

Rules:
- amount_ex_btw: the amount EXCLUDING VAT/BTW. If only total is shown, calculate ex BTW based on btw_rate
- btw_rate: 21, 9, or 0 (default 21 if unclear)
- btw_amount: the VAT/BTW amount
- expense_date: date on receipt in YYYY-MM-DD format, use today if not visible
- category: one of: travel, materials, software, food, office, other, general
- description: concise, max 60 chars
- All amounts as numbers, not strings
- Do NOT wrap the response in markdown code fences"""

        if ext == "pdf" or content_type == "application/pdf":
            base64_data = base64.standard_b64encode(content).decode("utf-8")
            message = client.messages.create(
                model=settings.anthropic_model,
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
                        {"type": "text", "text": prompt_text}
                    ],
                }],
            )
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
                    media_type = "image/jpeg"
                except Exception as resize_err:
                    print(f"RESIZE FAILED: {resize_err}")

            base64_data = base64.standard_b64encode(content).decode("utf-8")
            message = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_data,
                            },
                        },
                        {"type": "text", "text": prompt_text}
                    ],
                }],
            )

        record_ai_usage(user_id, "parse-receipt", message)
        raw = message.content[0].text.strip()
        parsed = _extract_json(raw)

        return {
            "success": True,
            "description": str(parsed.get("description", ""))[:60],
            "amount_ex_btw": float(parsed.get("amount_ex_btw", 0)),
            "btw_rate": int(parsed.get("btw_rate", 21)),
            "btw_amount": float(parsed.get("btw_amount", 0)),
            "expense_date": str(parsed.get("expense_date", str(date.today()))),
            "category": str(parsed.get("category", "general")),
        }

    except json.JSONDecodeError as e:
        print(f"JSON PARSE ERROR: {e}")
        raise HTTPException(status_code=422, detail="Could not parse receipt")
    except Exception as e:
        print(f"PARSE RECEIPT ERROR: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-receipt/{expense_id}")
async def upload_receipt(expense_id: str, request: Request, file: UploadFile = File(...)):
    user_id = get_user_id(request)

    # Verify the expense belongs to the caller BEFORE writing to storage,
    # so we never burn quota on files that can't be linked to a row.
    owner_check = supabase.table("expenses")\
        .select("id").eq("id", expense_id).eq("user_id", user_id)\
        .single().execute()
    if not owner_check.data:
        raise HTTPException(status_code=404, detail="Expense not found")

    try:
        content = await file.read()
        filename = file.filename or "receipt.jpg"
        content_type = file.content_type or "image/jpeg"

        # Sanitize extension
        ext = filename.lower().split(".")[-1]
        if len(ext) > 5 or not ext.isalpha():
            ct_map = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/webp": "webp",
                "image/gif": "gif",
                "application/pdf": "pdf",
            }
            ext = ct_map.get(content_type, "jpg")

        file_path = f"{user_id}/{expense_id}.{ext}"

        # Try upload — if file exists, remove and re-upload
        try:
            supabase.storage.from_("receipts").upload(
                file_path,
                content,
                {"content-type": content_type}
            )
        except Exception:
            supabase.storage.from_("receipts").remove([file_path])
            supabase.storage.from_("receipts").upload(
                file_path,
                content,
                {"content-type": content_type}
            )

        # Store the path, not the URL — the bucket is private now, and we
        # mint signed URLs at read time so each rendering call gets a
        # fresh, time-limited token.
        supabase.table("expenses")\
            .update({"receipt_url": file_path})\
            .eq("id", expense_id)\
            .eq("user_id", user_id)\
            .execute()

        return {"receipt_url": _signed_receipt_url(file_path)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"UPLOAD RECEIPT ERROR: {type(e).__name__}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{expense_id}")
async def delete_expense(expense_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        # Finding #10: 404 on a foreign/missing id instead of silent 200.
        delete_owned("expenses", expense_id, user_id)
        return {"message": "Expense deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import supabase
from app.config import settings
import anthropic
import base64
import json

router = APIRouter()


class ExpenseCreate(BaseModel):
    description: str
    amount_ex_btw: float
    btw_rate: int = 21
    expense_date: Optional[str] = None
    category: str = "general"


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


@router.get("/")
async def get_expenses(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("expenses")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("expense_date", desc=True)\
            .execute()
        return {"expenses": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_expense(expense: ExpenseCreate, request: Request):
    user_id = get_user_id(request)
    try:
        btw_amount = round(expense.amount_ex_btw * expense.btw_rate / 100, 2)
        expense_date = expense.expense_date or str(date.today())
        response = supabase.table("expenses").insert({
            "user_id": user_id,
            "description": expense.description,
            "amount_ex_btw": expense.amount_ex_btw,
            "btw_amount": btw_amount,
            "btw_rate": expense.btw_rate,
            "expense_date": expense_date,
            "category": expense.category,
        }).execute()
        return {"expense": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/parse-receipt")
async def parse_receipt(request: Request, file: UploadFile = File(...)):
    get_user_id(request)
    try:
        content = await file.read()
        base64_image = base64.standard_b64encode(content).decode("utf-8")
        media_type = file.content_type or "image/jpeg"

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": """Analyze this receipt image and extract the expense information.
Return ONLY a JSON object with these exact fields, nothing else, no markdown:
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
- All amounts as numbers, not strings"""
                        }
                    ],
                }
            ],
        )

        raw = message.content[0].text.strip()
        parsed = json.loads(raw)

        # Validate and sanitize
        return {
            "success": True,
            "description": str(parsed.get("description", ""))[:60],
            "amount_ex_btw": float(parsed.get("amount_ex_btw", 0)),
            "btw_rate": int(parsed.get("btw_rate", 21)),
            "btw_amount": float(parsed.get("btw_amount", 0)),
            "expense_date": str(parsed.get("expense_date", str(date.today()))),
            "category": str(parsed.get("category", "general")),
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Could not parse receipt")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload-receipt/{expense_id}")
async def upload_receipt(expense_id: str, request: Request, file: UploadFile = File(...)):
    user_id = get_user_id(request)
    try:
        content = await file.read()
        file_ext = file.filename.split(".")[-1]
        file_path = f"{user_id}/{expense_id}.{file_ext}"

        supabase.storage.from_("receipts").upload(
            file_path,
            content,
            {"content-type": file.content_type}
        )

        signed_url = supabase.storage.from_("receipts").create_signed_url(file_path, 86400)

        supabase.table("expenses")\
            .update({"receipt_url": signed_url["signedURL"]})\
            .eq("id", expense_id)\
            .eq("user_id", user_id)\
            .execute()

        return {"receipt_url": signed_url["signedURL"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{expense_id}")
async def delete_expense(expense_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("expenses")\
            .delete()\
            .eq("id", expense_id)\
            .eq("user_id", user_id)\
            .execute()
        return {"message": "Expense deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
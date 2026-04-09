from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import supabase
import uuid

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
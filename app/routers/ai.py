from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from anthropic import Anthropic
from app.database import supabase
from app.config import settings
import json

router = APIRouter()
client = Anthropic(api_key=settings.anthropic_api_key)


class PromptRequest(BaseModel):
    prompt: str


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


@router.post("/parse-invoice")
async def parse_invoice_prompt(data: PromptRequest, request: Request):
    user_id = get_user_id(request)

    products = supabase.table("products")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("is_active", True)\
        .execute()

    clients = supabase.table("clients")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    products_list = json.dumps([{
        "id": p["id"],
        "name": p["name"],
        "unit_price": p["unit_price"],
        "btw_rate": p["btw_rate"],
        "unit": p["unit"],
        "description": p.get("description", "")
    } for p in products.data])

    clients_list = json.dumps([{
        "id": c["id"],
        "name": c.get("company_name") or c["contact_name"],
        "contact_name": c["contact_name"],
        "email": c["email"]
    } for c in clients.data])

    system_prompt = f"""You are an invoice assistant for a Dutch freelancer.
Your job is to parse natural language invoice requests and return structured invoice data.

The user has these products:
{products_list}

The user has these clients:
{clients_list}

When the user describes an invoice, extract:
1. Which client it is for (match by name, partial match is fine). If no client is mentioned pick the first one.
2. Which line items (match to products where possible, create custom lines if needed)
3. Quantities for each line item

You MUST return ONLY a raw JSON object. No markdown. No code blocks. No explanation. No text before or after.
Start your response with {{ and end with }}

Use this exact format:
{{"client_id": "uuid", "client_name": "name", "lines": [{{"description": "text", "quantity": 1, "unit_price_ex_btw": 0.00, "btw_rate": 21}}], "confidence": "high", "notes": ""}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": data.prompt}
            ],
            system=system_prompt
        )
        response_text = message.content[0].text.strip()
        print(f"RAW RESPONSE: {repr(response_text)}")

        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        parsed = json.loads(response_text)
        return {
            "success": True,
            "parsed": parsed,
            "original_prompt": data.prompt
        }
    except json.JSONDecodeError as e:
        print(f"JSON ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        print(f"AI ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
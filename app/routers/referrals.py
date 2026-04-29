from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
import secrets
import string

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


# Avoid easily-confused chars: O/0, I/1
_ALPHABET = (
    (string.ascii_uppercase + string.digits)
    .replace("O", "")
    .replace("0", "")
    .replace("I", "")
    .replace("1", "")
)


def _generate_code(length: int = 8) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


@router.post("/generate")
async def generate_referral(request: Request):
    """Returns the user's existing referral code, or creates one if missing."""
    user_id = get_user_id(request)
    try:
        existing = supabase.table("referrals")\
            .select("code")\
            .eq("referrer_user_id", user_id)\
            .execute()
        if existing.data:
            return {"code": existing.data[0]["code"]}

        # Try a few times to handle the rare uniqueness collision
        for _ in range(8):
            code = _generate_code()
            try:
                supabase.table("referrals").insert({
                    "referrer_user_id": user_id,
                    "code": code,
                }).execute()
                return {"code": code}
            except Exception as e:
                msg = str(e).lower()
                if "duplicate" in msg or "unique" in msg:
                    continue
                raise

        raise HTTPException(
            status_code=500, detail="Could not generate a unique code"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def referral_stats(request: Request):
    """Returns the user's code and counts of signups + paid conversions."""
    user_id = get_user_id(request)
    try:
        code_result = supabase.table("referrals")\
            .select("code")\
            .eq("referrer_user_id", user_id)\
            .execute()
        if not code_result.data:
            return {"code": None, "signups": 0, "converted": 0}
        code = code_result.data[0]["code"]

        signups_result = supabase.table("referral_signups")\
            .select("converted")\
            .eq("referrer_code", code)\
            .execute()
        rows = signups_result.data or []
        signups = len(rows)
        converted = sum(1 for r in rows if r.get("converted"))

        return {"code": code, "signups": signups, "converted": converted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

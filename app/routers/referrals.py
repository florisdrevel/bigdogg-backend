from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
import secrets
import string
import traceback

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
        last_err: Exception | None = None
        for _ in range(8):
            code = _generate_code()
            try:
                supabase.table("referrals").insert({
                    "referrer_user_id": user_id,
                    "code": code,
                }).execute()
                return {"code": code}
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if "duplicate" in msg or "unique" in msg:
                    continue
                # Non-uniqueness error — surface it
                print(f"[referrals.generate] insert error for user {user_id}: {type(e).__name__}: {e}")
                traceback.print_exc()
                raise HTTPException(
                    status_code=500,
                    detail=f"insert failed: {type(e).__name__}: {e}",
                )

        # Eight collisions in a row is essentially impossible — surface as 500
        raise HTTPException(
            status_code=500,
            detail=f"could not generate a unique code (last error: {last_err})",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[referrals.generate] unhandled error for user {user_id}: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"{type(e).__name__}: {e}"
        )


@router.get("/stats")
async def referral_stats(request: Request):
    """Returns the user's code, signup + conversion counts, and their
    earned/applied bonus state. Also opportunistically grants any owed
    bonus so the user sees up-to-date numbers when they open Settings.
    """
    user_id = get_user_id(request)
    try:
        # Trigger any pending bonus first so the response reflects reality
        try:
            from app.routers.subscription import maybe_grant_referral_bonus
            maybe_grant_referral_bonus(user_id)
        except Exception as bonus_err:
            print(f"[referrals.stats] grant probe error: {bonus_err}")

        code_result = supabase.table("referrals")\
            .select("code")\
            .eq("referrer_user_id", user_id)\
            .execute()
        if not code_result.data:
            return {
                "code": None,
                "signups": 0,
                "converted": 0,
                "bonus_months_earned": 0,
                "bonus_months_max": 3,
                "bonus_active_until": None,
            }
        code = code_result.data[0]["code"]

        signups_result = supabase.table("referral_signups")\
            .select("converted")\
            .eq("referrer_code", code)\
            .execute()
        rows = signups_result.data or []
        signups = len(rows)
        converted = sum(1 for r in rows if r.get("converted"))

        # Pull the bonus columns from subscriptions
        sub_result = supabase.table("subscriptions")\
            .select("bonus_months_applied, bonus_active_until")\
            .eq("user_id", user_id)\
            .execute()
        bonus_applied = 0
        bonus_active_until = None
        if sub_result.data:
            sub_row = sub_result.data[0]
            bonus_applied = sub_row.get("bonus_months_applied") or 0
            bonus_active_until = sub_row.get("bonus_active_until")

        return {
            "code": code,
            "signups": signups,
            "converted": converted,
            "bonus_months_earned": bonus_applied,
            "bonus_months_max": 3,
            "bonus_active_until": bonus_active_until,
        }
    except Exception as e:
        print(f"[referrals.stats] error for user {user_id}: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"{type(e).__name__}: {e}"
        )

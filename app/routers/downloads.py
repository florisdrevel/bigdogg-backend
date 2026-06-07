"""Issues short-lived signed download tokens (finding #7).

The client calls this with its normal Authorization: Bearer header (so the
account JWT never rides in a URL), gets back a tiny scoped token, and then
opens the actual PDF/report GET with `?dt=<token>`. The download routes
verify the token and re-scope every query by its user id, so a leaked
token expires in minutes and only authorises that one resource.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.database import supabase
from app.services.download_token import issue, DEFAULT_TTL_SECONDS

router = APIRouter()


class TokenRequest(BaseModel):
    scope: str


@router.post("/token")
async def create_download_token(body: TokenRequest, request: Request):
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        user = supabase.auth.get_user(auth.replace("Bearer ", "").strip())
        if not user.user:
            raise ValueError("no user")
        user_id = user.user.id
        email = user.user.email or ""
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    scope = (body.scope or "").strip()
    if not scope:
        raise HTTPException(status_code=400, detail="scope required")

    return {
        "token": issue(user_id, email, scope),
        "expires_in": DEFAULT_TTL_SECONDS,
    }

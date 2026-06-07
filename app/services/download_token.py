"""Short-lived, scoped, signed download tokens (finding #7).

Browser-opened PDF/report links can't carry an Authorization header, so
the app historically appended the full account JWT as `?token=`. That JWT
then leaked into Railway access logs, the browser history and the Referer
header — and it grants *full account access* for its whole lifetime.

This module mints a tiny HMAC-signed token instead:
  * short-lived (default 5 min),
  * bound to a single resource scope (e.g. "invoice_pdf:<id>"),
  * carries only the user id + email, not account credentials.

Even if one leaks into a log it expires in minutes and only authorises a
single download. The GET routes additionally re-scope every query by the
token's user id, so a token can never reach another tenant's data.

`resolve_download_identity()` is the single entry point the download
routes call. It accepts, in priority order:
  1. an Authorization: Bearer header (no leak — preferred),
  2. a signed `dt` query token (the new browser-safe path),
  3. a legacy `?token=` account JWT (DEPRECATED — kept only so older
     mobile builds keep working; remove once they age out).
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import time

from fastapi import HTTPException, Request

from app.config import settings
from app.database import supabase

_PURPOSE = b"bigdogg-dl-token-v1"
DEFAULT_TTL_SECONDS = 300


def _key() -> bytes:
    """Derive a signing key from an always-present server secret so no new
    env var is required. Prefers SECRET_KEY; falls back to the Supabase
    service key (never leaves the backend). The derived key — not the raw
    secret — is what signs tokens."""
    base = settings.secret_key
    if not base or base == "fallback_secret":
        base = settings.supabase_service_key or "bigdogg-dev-insecure"
    return hmac.new(base.encode(), _PURPOSE, hashlib.sha256).digest()


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(body: str) -> str:
    return _b64e(hmac.new(_key(), body.encode(), hashlib.sha256).digest())


def issue(user_id: str, email: str, scope: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    """Mint a signed token for `scope`, valid for `ttl_seconds`."""
    if not user_id or not scope:
        raise HTTPException(status_code=400, detail="user_id and scope required")
    payload = {
        "u": user_id,
        "m": email or "",
        "s": scope,
        "e": int(time.time()) + ttl_seconds,
    }
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign(body)}"


def verify(token: str, expected_scope: str) -> tuple[str, str]:
    """Validate signature, expiry and scope. Returns (user_id, email).
    Raises 401 on a bad/expired token, 403 on a scope mismatch."""
    try:
        body, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body)):
            raise ValueError("bad signature")
        payload = json.loads(_b64d(body))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid download token")
    if int(payload.get("e", 0)) < int(time.time()):
        raise HTTPException(status_code=401, detail="Download link expired")
    if payload.get("s") != expected_scope:
        raise HTTPException(status_code=403, detail="Download token scope mismatch")
    return payload.get("u", ""), payload.get("m", "")


def _from_jwt(token: str) -> tuple[str, str]:
    try:
        user = supabase.auth.get_user(token)
        if not user.user:
            raise ValueError("no user")
        return user.user.id, (user.user.email or "")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def resolve_download_identity(
    request: Request,
    *,
    scope: str,
    legacy_jwt: str | None = None,
) -> tuple[str, str]:
    """Resolve (user_id, email) for a download route. See module docstring
    for the priority order."""
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth:
        return _from_jwt(auth.replace("Bearer ", "").strip())
    dt = request.query_params.get("dt")
    if dt:
        return verify(dt, scope)
    if legacy_jwt:
        return _from_jwt(legacy_jwt)
    raise HTTPException(status_code=401, detail="Authorization required")

"""
Tink bank connection — Tink Money / Account Aggregation flow (NL only).

End-to-end flow:
  1. App calls POST /api/v1/banking/connect.
  2. Backend authenticates with Tink (client_credentials), creates a Tink
     user for this BigDogg user if one doesn't exist yet, mints a one-time
     authorization code, and returns a Tink Link URL.
  3. App opens that URL. User picks their bank, authenticates via the
     bank's hosted UI, and Tink redirects to:
        GET /api/v1/banking/callback?code=...&credentials=...&state=...
  4. Backend validates the state, exchanges the callback code for a
     user access_token + refresh_token, stores them on user_profiles,
     and 302s the user back into the app.
  5. App calls GET /api/v1/banking/transactions to pull recent activity.
     Tokens are auto-refreshed via the refresh_token when they expire.

Required environment variables (Railway):
  - TINK_CLIENT_ID
  - TINK_CLIENT_SECRET

Required Supabase columns on user_profiles (see SQL block at the bottom
of this file's deployment notes):
  tink_user_id              text
  tink_access_token         text
  tink_refresh_token        text
  tink_token_expires_at     timestamptz
  tink_credentials_id       text
  tink_connected_at         timestamptz
  tink_link_state           text

The redirect URI registered in the Tink console must be exactly:
  https://bigdogg-production.up.railway.app/api/v1/banking/callback
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode
import secrets
import httpx

from app.database import supabase
from app.config import settings


router = APIRouter()

# ─── Tink endpoints ─────────────────────────────────────────────
TINK_API_BASE = "https://api.tink.com"
TINK_LINK_BASE = "https://link.tink.com/1.0"

TOKEN_ENDPOINT = f"{TINK_API_BASE}/api/v1/oauth/token"
USER_CREATE_ENDPOINT = f"{TINK_API_BASE}/api/v1/user/create"
AUTHORIZATION_GRANT_ENDPOINT = f"{TINK_API_BASE}/api/v1/oauth/authorization-grant"
ACCOUNTS_ENDPOINT = f"{TINK_API_BASE}/data/v2/accounts"
TRANSACTIONS_ENDPOINT = f"{TINK_API_BASE}/data/v2/transactions"
TINK_LINK_CONNECT_URL = f"{TINK_LINK_BASE}/transactions/connect-accounts"

REDIRECT_URI = "https://bigdogg-production.up.railway.app/api/v1/banking/callback"
APP_RETURN_OK = "https://bigdogg.nl/#/dashboard?bank=success"
APP_RETURN_ERR = "https://bigdogg.nl/#/dashboard?bank_error="

MARKET = "NL"
LOCALE = "en_US"

# Scopes the user grants when connecting their bank. Tink Link's
# connect-accounts flow needs the WRITE scopes (credentials:write,
# credentials:refresh, providers:read, authorization:read) to actually
# create credentials — read-only scopes triggered the Link UI error
# REQUEST_FAILED_FETCH_EXISTING_USER on freshly-created users.
USER_SCOPES = (
    "transactions:read,"
    "accounts:read,"
    "credentials:read,"
    "credentials:write,"
    "credentials:refresh,"
    "providers:read,"
    "authorization:read,"
    "user:read"
)

# Scopes used when authenticating the app itself (client_credentials).
APP_SCOPES = "user:create,user:read,authorization:grant"

HTTP_TIMEOUT = 20.0


# ─── Auth helper ────────────────────────────────────────────────
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


def _ensure_credentials_configured() -> None:
    if not settings.tink_client_id or not settings.tink_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Tink credentials missing (TINK_CLIENT_ID / TINK_CLIENT_SECRET).",
        )


# ─── App-level (client_credentials) authentication ──────────────
async def _get_app_access_token(scope: str = APP_SCOPES) -> str:
    _ensure_credentials_configured()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            TOKEN_ENDPOINT,
            data={
                "client_id": settings.tink_client_id,
                "client_secret": settings.tink_client_secret,
                "grant_type": "client_credentials",
                "scope": scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if r.status_code >= 400:
        print(f"[tink] app token error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="Tink app authentication failed")
    return r.json()["access_token"]


async def _create_tink_user(bigdogg_user_id: str) -> str:
    """Create a fresh Tink user, persist its id, return it."""
    app_token = await _get_app_access_token()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            USER_CREATE_ENDPOINT,
            json={
                "market": MARKET,
                "locale": LOCALE,
                "external_user_id": bigdogg_user_id,
            },
            headers={
                "Authorization": f"Bearer {app_token}",
                "Content-Type": "application/json",
            },
        )
    if r.status_code >= 400:
        print(f"[tink] user create error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="Tink user creation failed")
    tink_user_id = r.json()["user_id"]

    profile_result = supabase.table("user_profiles")\
        .select("id").eq("id", bigdogg_user_id).execute()
    if profile_result.data:
        supabase.table("user_profiles")\
            .update({"tink_user_id": tink_user_id})\
            .eq("id", bigdogg_user_id).execute()
    else:
        supabase.table("user_profiles")\
            .insert({"id": bigdogg_user_id, "tink_user_id": tink_user_id})\
            .execute()
    return tink_user_id


async def _get_or_create_tink_user(bigdogg_user_id: str) -> str:
    """Return the persistent Tink user_id, creating it once if needed."""
    profile_result = supabase.table("user_profiles")\
        .select("tink_user_id")\
        .eq("id", bigdogg_user_id)\
        .execute()
    profile = profile_result.data[0] if profile_result.data else None
    if profile and profile.get("tink_user_id"):
        return profile["tink_user_id"]
    return await _create_tink_user(bigdogg_user_id)


async def _generate_authorization_code(tink_user_id: str, hint: str) -> Tuple[Optional[str], Optional[dict]]:
    """Mint a one-time authorization code that Tink Link will consume.

    Returns (code, error_payload). On success, error_payload is None.
    On failure, returns (None, parsed JSON or {"_status": code, "_text": text}).

    Uses /authorization-grant — the same-app permanent users flow Tink Link's
    connect-accounts URL expects.
    """
    app_token = await _get_app_access_token()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            AUTHORIZATION_GRANT_ENDPOINT,
            data={
                "user_id": tink_user_id,
                "id_hint": hint,
                "scope": USER_SCOPES,
            },
            headers={
                "Authorization": f"Bearer {app_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    if r.status_code >= 400:
        print(f"[tink] auth-grant error: {r.status_code} {r.text}")
        try:
            err = r.json()
        except Exception:
            err = {"_status": r.status_code, "_text": r.text}
        err.setdefault("_status", r.status_code)
        return None, err
    return r.json()["code"], None


# ─── User access-token management ───────────────────────────────
async def _get_user_access_token(bigdogg_user_id: str) -> str:
    """Return a fresh user access_token, refreshing via refresh_token if needed."""
    profile_result = supabase.table("user_profiles")\
        .select("tink_access_token, tink_refresh_token, tink_token_expires_at")\
        .eq("id", bigdogg_user_id)\
        .execute()
    if not profile_result.data:
        raise HTTPException(status_code=404, detail="No bank connection")
    profile = profile_result.data[0]
    access_token = profile.get("tink_access_token")
    refresh_token = profile.get("tink_refresh_token")
    expires_at_raw = profile.get("tink_token_expires_at")
    if not access_token or not refresh_token:
        raise HTTPException(status_code=404, detail="No bank connection")

    needs_refresh = True
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(
                expires_at_raw.replace("Z", "+00:00")
            )
            needs_refresh = datetime.now(timezone.utc) >= expires_at
        except Exception:
            needs_refresh = True
    if not needs_refresh:
        return access_token

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            TOKEN_ENDPOINT,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.tink_client_id,
                "client_secret": settings.tink_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if r.status_code >= 400:
        print(f"[tink] refresh error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="Tink refresh failed; reconnect bank")

    payload = r.json()
    new_access = payload.get("access_token")
    new_refresh = payload.get("refresh_token") or refresh_token
    expires_in = int(payload.get("expires_in") or 3600)
    new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)

    supabase.table("user_profiles")\
        .update({
            "tink_access_token": new_access,
            "tink_refresh_token": new_refresh,
            "tink_token_expires_at": new_expires_at.isoformat(),
        })\
        .eq("id", bigdogg_user_id)\
        .execute()
    return new_access


# ─── Endpoints ─────────────────────────────────────────────────
@router.post("/connect")
async def connect_bank(request: Request):
    """Returns a Tink Link URL the app should open in a browser/webview.

    Uses Tink's one-time-user flow (no client-side user/create or
    authorization-grant). This is the same shape Tink Console's
    "Create a URL" feature generates, and avoids the Tink Link UI
    error REQUEST_FAILED_FETCH_EXISTING_USER which fires when the
    permanent-user flow points at a freshly-minted user with no
    attached credentials yet.

    Tink Link will spin up a temporary user on its side, run the
    bank-picker → bank-login → consent flow, then redirect back to
    /banking/callback with `code` + `credentials` + our `state`. The
    callback exchanges `code` for a long-lived access/refresh token
    pair, so subsequent transaction fetches still work without
    re-auth — the only thing we lose vs. the permanent-user flow is
    the ability to read other previously-created credentials in one
    Link UI session, which we never used anyway.
    """
    bigdogg_user_id = get_user_id(request)
    _ensure_credentials_configured()

    state = secrets.token_urlsafe(32)
    supabase.table("user_profiles")\
        .update({"tink_link_state": state})\
        .eq("id", bigdogg_user_id)\
        .execute()

    qs = urlencode({
        "client_id": settings.tink_client_id,
        "redirect_uri": REDIRECT_URI,
        "market": MARKET,
        "locale": LOCALE,
        "state": state,
    })
    link_url = f"{TINK_LINK_CONNECT_URL}/?{qs}"
    cid = settings.tink_client_id or ""
    cid_masked = f"{cid[:4]}...{cid[-4:]}" if len(cid) >= 8 else "<missing>"
    print(
        f"[tink] connect (one-time flow): client_id={cid_masked} "
        f"redirect_uri={REDIRECT_URI} market={MARKET}"
    )
    return {"link_url": link_url}


@router.get("/callback")
async def banking_callback(
    code: Optional[str] = Query(None),
    credentials_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_message: Optional[str] = Query(None),
):
    """Tink redirects here after the user finishes (or cancels) the flow."""
    if error or not code or not state:
        msg = error_message or error or "missing_code"
        return RedirectResponse(url=f"{APP_RETURN_ERR}{msg}")

    state_lookup = supabase.table("user_profiles")\
        .select("id")\
        .eq("tink_link_state", state)\
        .limit(1)\
        .execute()
    if not state_lookup.data:
        return RedirectResponse(url=f"{APP_RETURN_ERR}invalid_state")
    bigdogg_user_id = state_lookup.data[0]["id"]

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": settings.tink_client_id,
                "client_secret": settings.tink_client_secret,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if r.status_code >= 400:
        print(f"[tink] code-exchange error: {r.status_code} {r.text}")
        return RedirectResponse(url=f"{APP_RETURN_ERR}exchange_failed")

    payload = r.json()
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    expires_in = int(payload.get("expires_in") or 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)

    supabase.table("user_profiles")\
        .update({
            "tink_access_token": access_token,
            "tink_refresh_token": refresh_token,
            "tink_token_expires_at": expires_at.isoformat(),
            "tink_credentials_id": credentials_id,
            "tink_connected_at": datetime.now(timezone.utc).isoformat(),
            "tink_link_state": None,
        })\
        .eq("id", bigdogg_user_id)\
        .execute()

    return RedirectResponse(url=APP_RETURN_OK)


def _normalize_tink_transaction(tx: dict) -> dict:
    """Flatten Tink's verbose transaction shape into the fields BigDogg
    cares about. Returns positive amounts for incoming and negative for
    outgoing, in the natural decimal form (so 12.34 not "1234"/"100")."""
    amount_obj = tx.get("amount") or {}
    value_obj = amount_obj.get("value") or {}
    try:
        unscaled = int(value_obj.get("unscaledValue") or "0")
        scale = int(value_obj.get("scale") or "0")
        decimal_amount = unscaled / (10 ** scale) if scale else float(unscaled)
    except Exception:
        decimal_amount = 0.0

    descriptions = tx.get("descriptions") or {}
    dates = tx.get("dates") or {}
    merchant_info = tx.get("merchantInformation") or {}

    return {
        "id": tx.get("id"),
        "date": dates.get("booked") or dates.get("value"),
        "description": descriptions.get("display") or descriptions.get("original") or "",
        "merchant": merchant_info.get("merchantName"),
        "amount": decimal_amount,
        "currency": amount_obj.get("currencyCode") or "EUR",
        "type": (tx.get("types") or {}).get("type"),
        "status": tx.get("status"),
    }


@router.get("/transactions")
async def get_transactions(
    request: Request,
    page_size: int = Query(100, ge=1, le=500),
    page_token: Optional[str] = Query(None),
):
    bigdogg_user_id = get_user_id(request)
    access_token = await _get_user_access_token(bigdogg_user_id)

    params: dict = {"pageSize": page_size}
    if page_token:
        params["pageToken"] = page_token

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            TRANSACTIONS_ENDPOINT,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if r.status_code >= 400:
        print(f"[tink] transactions error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="Could not fetch transactions")

    raw = r.json()
    items = raw.get("transactions") or []
    normalized = [_normalize_tink_transaction(t) for t in items]
    normalized.sort(key=lambda t: t.get("date") or "", reverse=True)
    return {
        "transactions": normalized,
        "next_page_token": raw.get("nextPageToken"),
    }


@router.get("/accounts")
async def get_accounts(request: Request):
    bigdogg_user_id = get_user_id(request)
    access_token = await _get_user_access_token(bigdogg_user_id)

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.get(
            ACCOUNTS_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if r.status_code >= 400:
        print(f"[tink] accounts error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="Could not fetch accounts")
    return r.json()


@router.get("/status")
async def banking_status(request: Request):
    bigdogg_user_id = get_user_id(request)
    profile_result = supabase.table("user_profiles")\
        .select("tink_user_id, tink_credentials_id, tink_connected_at, tink_token_expires_at")\
        .eq("id", bigdogg_user_id)\
        .execute()
    if not profile_result.data:
        return {"connected": False}
    profile = profile_result.data[0]
    return {
        "connected": bool(profile.get("tink_credentials_id")),
        "tink_user_id": profile.get("tink_user_id"),
        "credentials_id": profile.get("tink_credentials_id"),
        "connected_at": profile.get("tink_connected_at"),
        "token_expires_at": profile.get("tink_token_expires_at"),
    }


@router.delete("/disconnect")
async def banking_disconnect(request: Request):
    bigdogg_user_id = get_user_id(request)
    supabase.table("user_profiles")\
        .update({
            "tink_access_token": None,
            "tink_refresh_token": None,
            "tink_token_expires_at": None,
            "tink_credentials_id": None,
            "tink_connected_at": None,
            "tink_link_state": None,
        })\
        .eq("id", bigdogg_user_id)\
        .execute()
    return {"success": True}

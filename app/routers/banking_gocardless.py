"""
Bank connection — GoCardless Bank Account Data (formerly Nordigen).

Why we pivoted: Tink's sandbox kept failing on permanent-user flows
(REQUEST_FAILED_FETCH_EXISTING_USER) and production access requires a
sales conversation. GoCardless BAD is self-serve, free for low volume,
and supports every NL bank out of the box (PSD2 license is theirs).

Sign-up:
  1. Register at https://bankaccountdata.gocardless.com (free).
  2. Generate secret_id + secret_key in the dashboard.
  3. Set Railway env vars:
        GOCARDLESS_SECRET_ID
        GOCARDLESS_SECRET_KEY
  4. Add the redirect URL in the GoCardless dashboard:
        https://bigdogg-production.up.railway.app/api/v1/banking/callback

End-to-end flow:
  1. App: GET /banking/institutions   → list of NL banks (id, name, logo)
  2. User taps a bank.
  3. App: POST /banking/connect {institution_id}
                                → backend creates a requisition,
                                  stores requisition_id on user_profiles,
                                  returns the link_url to open.
  4. App opens link_url in browser.
  5. User picks the bank, authenticates, consents to PSD2 access.
  6. GoCardless redirects to /banking/callback?ref=<state>.
  7. Callback marks the user connected, fetches account ids, redirects
     back into the app.
  8. App: GET /banking/transactions   → all transactions across the
                                  user's connected accounts (booked).

Tokens:
  - GoCardless access tokens are app-level, 24h lifetime. We cache
    them in-process and refresh on demand. No per-user token storage.
  - Per-account access is valid for `access_valid_for_days` (default
    90). After that, the user has to re-link.

Required columns on user_profiles (see migrations/gocardless_columns.sql):
  gc_requisition_id   text
  gc_account_ids      jsonb
  gc_institution_id   text
  gc_connected_at     timestamptz
  gc_link_state       text
"""

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import secrets
import httpx

from app.database import supabase
from app.config import settings


router = APIRouter()

# ─── GoCardless endpoints ───────────────────────────────────────
GC_API_BASE = "https://bankaccountdata.gocardless.com/api/v2"

GC_TOKEN_NEW = f"{GC_API_BASE}/token/new/"
GC_TOKEN_REFRESH = f"{GC_API_BASE}/token/refresh/"
GC_INSTITUTIONS = f"{GC_API_BASE}/institutions/"
GC_AGREEMENTS = f"{GC_API_BASE}/agreements/enduser/"
GC_REQUISITIONS = f"{GC_API_BASE}/requisitions/"

REDIRECT_URI = "https://bigdogg-production.up.railway.app/api/v1/banking/callback"
APP_RETURN_OK = "https://bigdogg.nl/#/dashboard?bank=success"
APP_RETURN_ERR = "https://bigdogg.nl/#/dashboard?bank_error="

COUNTRY = "nl"
USER_LANGUAGE = "NL"
ACCESS_VALID_DAYS = 90       # PSD2 max
MAX_HISTORICAL_DAYS = 90     # most NL banks cap at 90

HTTP_TIMEOUT = 20.0

# Module-level access-token cache (app-wide, 24h lifetime).
_token_cache: Dict[str, Any] = {"access": None, "expires_at": None, "refresh": None, "refresh_expires_at": None}


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
    if not settings.gocardless_secret_id or not settings.gocardless_secret_key:
        raise HTTPException(
            status_code=500,
            detail="GoCardless credentials missing (GOCARDLESS_SECRET_ID / GOCARDLESS_SECRET_KEY).",
        )


# ─── Token management ──────────────────────────────────────────
async def _new_token() -> None:
    _ensure_credentials_configured()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            GC_TOKEN_NEW,
            json={
                "secret_id": settings.gocardless_secret_id,
                "secret_key": settings.gocardless_secret_key,
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
    if r.status_code >= 400:
        print(f"[gocardless] token/new error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="GoCardless authentication failed")
    payload = r.json()
    now = datetime.now(timezone.utc)
    _token_cache["access"] = payload["access"]
    _token_cache["expires_at"] = now + timedelta(seconds=int(payload.get("access_expires", 86400)) - 30)
    _token_cache["refresh"] = payload.get("refresh")
    _token_cache["refresh_expires_at"] = now + timedelta(seconds=int(payload.get("refresh_expires", 2592000)) - 30)


async def _refresh_token() -> None:
    refresh = _token_cache.get("refresh")
    if not refresh:
        return await _new_token()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            GC_TOKEN_REFRESH,
            json={"refresh": refresh},
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
    if r.status_code >= 400:
        return await _new_token()
    payload = r.json()
    now = datetime.now(timezone.utc)
    _token_cache["access"] = payload["access"]
    _token_cache["expires_at"] = now + timedelta(seconds=int(payload.get("access_expires", 86400)) - 30)


async def _get_access_token() -> str:
    expires_at = _token_cache.get("expires_at")
    if not _token_cache.get("access") or not expires_at or datetime.now(timezone.utc) >= expires_at:
        refresh_exp = _token_cache.get("refresh_expires_at")
        if _token_cache.get("refresh") and refresh_exp and datetime.now(timezone.utc) < refresh_exp:
            await _refresh_token()
        else:
            await _new_token()
    return _token_cache["access"]


async def _gc_get(path: str, params: Optional[dict] = None) -> Any:
    token = await _get_access_token()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
    if r.status_code == 401:
        await _new_token()
        token = _token_cache["access"]
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(
                path,
                params=params,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
    if r.status_code >= 400:
        print(f"[gocardless] GET {path} error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail=f"GoCardless GET failed: {r.status_code}")
    return r.json()


async def _gc_post(path: str, body: dict) -> Any:
    token = await _get_access_token()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            path,
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
    if r.status_code == 401:
        await _new_token()
        token = _token_cache["access"]
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.post(
                path,
                json=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
    if r.status_code >= 400:
        print(f"[gocardless] POST {path} error: {r.status_code} {r.text}")
        try:
            err = r.json()
            detail = err.get("detail") or err.get("summary") or str(err)
        except Exception:
            detail = r.text
        raise HTTPException(status_code=502, detail=f"GoCardless: {detail}")
    return r.json()


async def _gc_delete(path: str) -> None:
    token = await _get_access_token()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.delete(
            path,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
    if r.status_code >= 400 and r.status_code != 404:
        print(f"[gocardless] DELETE {path} error: {r.status_code} {r.text}")


# ─── Endpoints ─────────────────────────────────────────────────
@router.get("/institutions")
async def list_institutions(request: Request, country: str = Query(COUNTRY)):
    """Returns a sorted list of banks available for the country (default NL)."""
    get_user_id(request)
    data = await _gc_get(GC_INSTITUTIONS, params={"country": country})
    items: List[Dict[str, Any]] = []
    for inst in data:
        items.append({
            "id": inst.get("id"),
            "name": inst.get("name"),
            "bic": inst.get("bic"),
            "logo": inst.get("logo"),
            "transaction_total_days": inst.get("transaction_total_days"),
        })
    items.sort(key=lambda x: (x.get("name") or "").lower())
    return {"institutions": items}


@router.post("/connect")
async def connect_bank(request: Request):
    """Create a requisition and return the GoCardless link URL.

    Body: { "institution_id": "ING_INGBNL2A" }
    """
    bigdogg_user_id = get_user_id(request)
    _ensure_credentials_configured()

    try:
        body = await request.json()
    except Exception:
        body = {}
    institution_id = (body or {}).get("institution_id")
    if not institution_id:
        raise HTTPException(status_code=400, detail="institution_id required")

    # If the user already has a pending/linked requisition for the same
    # institution, cancel it before creating a new one — otherwise GC
    # complains about duplicates and we'd accumulate dead requisitions.
    profile_result = supabase.table("user_profiles")\
        .select("gc_requisition_id")\
        .eq("id", bigdogg_user_id).execute()
    profile = profile_result.data[0] if profile_result.data else None
    old_req_id = profile.get("gc_requisition_id") if profile else None
    if old_req_id:
        try:
            await _gc_delete(f"{GC_REQUISITIONS}{old_req_id}/")
        except Exception as e:
            print(f"[gocardless] old requisition cleanup skipped: {e}")

    state = secrets.token_urlsafe(24)

    requisition = await _gc_post(GC_REQUISITIONS, {
        "redirect": REDIRECT_URI,
        "institution_id": institution_id,
        "reference": state,
        "user_language": USER_LANGUAGE,
    })

    requisition_id = requisition.get("id")
    link = requisition.get("link")
    if not requisition_id or not link:
        raise HTTPException(status_code=502, detail="GoCardless returned no link")

    update = {
        "gc_requisition_id": requisition_id,
        "gc_institution_id": institution_id,
        "gc_link_state": state,
    }
    if profile:
        supabase.table("user_profiles").update(update).eq("id", bigdogg_user_id).execute()
    else:
        supabase.table("user_profiles").insert({"id": bigdogg_user_id, **update}).execute()

    print(f"[gocardless] connect: user={bigdogg_user_id[:8]}… inst={institution_id} req={requisition_id}")
    return {"link_url": link}


@router.get("/callback")
async def banking_callback(
    ref: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    details: Optional[str] = Query(None),
):
    """GoCardless redirects here once the user finishes the bank flow.

    `ref` is the `reference` we passed when creating the requisition, so
    we can look the user up and check the linked accounts.
    """
    if error or not ref:
        msg = details or error or "missing_ref"
        return RedirectResponse(url=f"{APP_RETURN_ERR}{msg}")

    state_lookup = supabase.table("user_profiles")\
        .select("id, gc_requisition_id")\
        .eq("gc_link_state", ref)\
        .limit(1).execute()
    if not state_lookup.data:
        return RedirectResponse(url=f"{APP_RETURN_ERR}invalid_state")
    bigdogg_user_id = state_lookup.data[0]["id"]
    requisition_id = state_lookup.data[0].get("gc_requisition_id")
    if not requisition_id:
        return RedirectResponse(url=f"{APP_RETURN_ERR}missing_requisition")

    try:
        requisition = await _gc_get(f"{GC_REQUISITIONS}{requisition_id}/")
    except HTTPException:
        return RedirectResponse(url=f"{APP_RETURN_ERR}requisition_lookup_failed")

    accounts = requisition.get("accounts") or []
    status_str = requisition.get("status") or ""

    if not accounts:
        # User probably cancelled at the bank. Don't mark as connected.
        supabase.table("user_profiles").update({
            "gc_link_state": None,
        }).eq("id", bigdogg_user_id).execute()
        return RedirectResponse(url=f"{APP_RETURN_ERR}{status_str.lower() or 'no_accounts'}")

    supabase.table("user_profiles").update({
        "gc_account_ids": accounts,
        "gc_connected_at": datetime.now(timezone.utc).isoformat(),
        "gc_link_state": None,
    }).eq("id", bigdogg_user_id).execute()

    print(f"[gocardless] callback: user={bigdogg_user_id[:8]}… status={status_str} accounts={len(accounts)}")
    return RedirectResponse(url=APP_RETURN_OK)


@router.get("/status")
async def banking_status(request: Request):
    bigdogg_user_id = get_user_id(request)
    profile_result = supabase.table("user_profiles")\
        .select("gc_requisition_id, gc_institution_id, gc_account_ids, gc_connected_at")\
        .eq("id", bigdogg_user_id).execute()
    if not profile_result.data:
        return {"connected": False}
    profile = profile_result.data[0]
    accounts = profile.get("gc_account_ids") or []
    return {
        "connected": bool(accounts),
        "requisition_id": profile.get("gc_requisition_id"),
        "institution_id": profile.get("gc_institution_id"),
        "account_count": len(accounts),
        "connected_at": profile.get("gc_connected_at"),
    }


@router.get("/accounts")
async def get_accounts(request: Request):
    bigdogg_user_id = get_user_id(request)
    profile_result = supabase.table("user_profiles")\
        .select("gc_account_ids")\
        .eq("id", bigdogg_user_id).execute()
    if not profile_result.data:
        raise HTTPException(status_code=404, detail="No bank connection")
    accounts: List[str] = profile_result.data[0].get("gc_account_ids") or []
    if not accounts:
        return {"accounts": []}

    enriched: List[Dict[str, Any]] = []
    for account_id in accounts:
        try:
            details = await _gc_get(f"{GC_API_BASE}/accounts/{account_id}/details/")
            inner = details.get("account") or {}
            enriched.append({
                "id": account_id,
                "iban": inner.get("iban"),
                "name": inner.get("name") or inner.get("ownerName"),
                "currency": inner.get("currency"),
                "product": inner.get("product"),
            })
        except Exception as e:
            print(f"[gocardless] details failed for {account_id}: {e}")
            enriched.append({"id": account_id})
    return {"accounts": enriched}


@router.get("/transactions")
async def get_transactions(request: Request, page_size: int = Query(200, ge=1, le=500)):
    """Aggregates booked transactions across all of the user's connected accounts."""
    bigdogg_user_id = get_user_id(request)
    profile_result = supabase.table("user_profiles")\
        .select("gc_account_ids")\
        .eq("id", bigdogg_user_id).execute()
    if not profile_result.data:
        raise HTTPException(status_code=404, detail="No bank connection")
    accounts: List[str] = profile_result.data[0].get("gc_account_ids") or []
    if not accounts:
        return {"transactions": []}

    aggregated: List[Dict[str, Any]] = []
    for account_id in accounts:
        try:
            data = await _gc_get(f"{GC_API_BASE}/accounts/{account_id}/transactions/")
        except Exception as e:
            print(f"[gocardless] transactions failed for {account_id}: {e}")
            continue
        booked = ((data.get("transactions") or {}).get("booked")) or []
        for tx in booked:
            tx["account_id"] = account_id
            aggregated.append(tx)

    aggregated.sort(
        key=lambda t: t.get("bookingDate") or t.get("valueDate") or "",
        reverse=True,
    )
    return {"transactions": aggregated[:page_size]}


@router.delete("/disconnect")
async def banking_disconnect(request: Request):
    bigdogg_user_id = get_user_id(request)
    profile_result = supabase.table("user_profiles")\
        .select("gc_requisition_id")\
        .eq("id", bigdogg_user_id).execute()
    profile = profile_result.data[0] if profile_result.data else None
    requisition_id = profile.get("gc_requisition_id") if profile else None
    if requisition_id:
        try:
            await _gc_delete(f"{GC_REQUISITIONS}{requisition_id}/")
        except Exception as e:
            print(f"[gocardless] disconnect cleanup failed (non-fatal): {e}")

    supabase.table("user_profiles").update({
        "gc_requisition_id": None,
        "gc_account_ids": None,
        "gc_institution_id": None,
        "gc_connected_at": None,
        "gc_link_state": None,
    }).eq("id", bigdogg_user_id).execute()
    return {"success": True}

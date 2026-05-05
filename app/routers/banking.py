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
    """Return a fresh user access_token.

    The one-time-user flow returns an access_token but NO refresh_token
    (there is no persistent user to refresh against). The permanent-user
    flow returns both. We support both: if a refresh_token is present
    and the access_token has expired we refresh; otherwise we use the
    stored access_token directly. If no access_token at all, the user
    has not connected a bank yet (or needs to reconnect).
    """
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
    if not access_token:
        raise HTTPException(status_code=404, detail="No bank connection")

    expired = False
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(
                expires_at_raw.replace("Z", "+00:00")
            )
            expired = datetime.now(timezone.utc) >= expires_at
        except Exception:
            expired = False  # if we can't parse, trust the token until Tink rejects it

    if not expired or not refresh_token:
        # Either still valid, OR no refresh_token to swap (one-time flow):
        # return whatever we have and let the upstream call surface a 401
        # if Tink has actually expired the token server-side.
        return access_token

    # Have a refresh_token AND token is expired: refresh.
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
        # Refresh failed: fall back to the stored access_token. Tink may
        # have rotated it on their side; the next API call will surface
        # the actual error to the user.
        return access_token

    payload = r.json()
    new_access = payload.get("access_token") or access_token
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


# ─── Auto-matching: tx → invoice / expense ─────────────────────
# Confidence thresholds. Above AUTO we mark the link without asking;
# between SUGGEST and AUTO we attach the match as a hint the user can
# confirm in one tap. Below SUGGEST we show nothing.
MATCH_AUTO_SCORE = 80
MATCH_SUGGEST_SCORE = 55

# Stripe fee model used to predict the amount that arrives in the
# freelancer's bank account when a customer pays a BigDogg invoice via
# Stripe. Using their published European-card schedule:
#   - 1.5% + €0.25 for European cards / iDEAL / SEPA
#   - 2.9% + €0.25 for international/non-European cards
# We probe both rates so a transaction that lines up with EITHER counts
# as a Stripe-fee match.
STRIPE_FEE_VARIANTS = [
    (0.015, 0.25),   # European card / iDEAL / SEPA
    (0.029, 0.25),   # International / non-European
]


def _amount_close(a: float, b: float, tol: float = 0.01) -> bool:
    return abs(a - b) <= tol


def _looks_like_stripe_payout(haystack: str) -> bool:
    """Best-effort detection of a Stripe payout in a transaction description.
    Stripe's bank-statement strings vary by country and processor — we
    catch the common variants seen on Dutch ZZP accounts."""
    if not haystack:
        return False
    lower = haystack.lower()
    needles = ("stripe", "str.pe", "stripe.com")
    return any(n in lower for n in needles)


def _stripe_fee_match(tx_amount: float, invoice_total: float) -> Optional[float]:
    """If the transaction amount could be the after-fee net of `invoice_total`
    via Stripe, return how close it is (in EUR, abs). Else None.

    A "match" here means the actual received amount is within €0.10 of
    one of Stripe's fee-adjusted predictions. €0.10 absorbs rounding +
    edge cases like Stripe Tax surcharge or partial captures.
    """
    if invoice_total <= 0:
        return None
    best_diff: Optional[float] = None
    for rate, fixed in STRIPE_FEE_VARIANTS:
        predicted_net = invoice_total * (1 - rate) - fixed
        diff = abs(tx_amount - predicted_net)
        if diff <= 0.10 and (best_diff is None or diff < best_diff):
            best_diff = diff
    return best_diff


def _score_invoice_match(tx: dict, invoice: dict) -> int:
    """Returns a confidence score 0-100 for tx → invoice (income only).

    Scoring components (additive, capped at 100):
      Invoice number in tx description           +90  (near-certain)
      Exact amount match (≤ €0.01)               +60
      Within 0.5% of invoice total               +50
      Looks like Stripe-fee net of invoice       +55  (+10 if "Stripe"
                                                      is in description)
      Within 5% (catch-all rounding window)      +20
      Client name / company in description       +25
      Date proximity:
        ≤  7 days                                +10
        ≤ 30 days                                 +5
        ≤ 60 days                                 +2
    """
    if (tx.get("amount") or 0) <= 0:
        return 0
    if (invoice.get("status") or "").lower() == "paid":
        return 0  # ignore already-paid invoices

    score = 0
    desc = (tx.get("description") or "").lower()
    merchant = (tx.get("merchant") or "").lower()
    haystack = f"{desc} {merchant}".strip()
    is_stripe = _looks_like_stripe_payout(haystack)

    # 1) Invoice number explicitly mentioned: highest signal we have.
    inv_num = (invoice.get("invoice_number") or "").lower()
    if inv_num and inv_num in haystack:
        score += 90

    # 2) Amount matching with Stripe-fee tolerance.
    inv_total = float(invoice.get("total_incl_btw") or 0)
    tx_amount = float(tx.get("amount") or 0)
    if inv_total > 0:
        diff = abs(tx_amount - inv_total)
        diff_pct = diff / inv_total
        if diff <= 0.01:
            score += 60                                         # exact
        elif diff_pct <= 0.005:
            score += 50                                         # within 0.5%
        else:
            # Probe the Stripe-fee shape. Only useful when the received
            # amount is *less* than the invoice (fees subtract, never add).
            stripe_diff = _stripe_fee_match(tx_amount, inv_total) if tx_amount < inv_total else None
            if stripe_diff is not None:
                score += 55
                if is_stripe:
                    score += 10                                 # extra confidence
            elif diff_pct <= 0.05:
                score += 20                                     # rough match

    # 3) Client name / company.
    for key in ("client_name", "client_company"):
        cand = (invoice.get(key) or "").strip().lower()
        if cand and len(cand) >= 3 and cand in haystack:
            score += 25
            break

    # 4) Date proximity. Banks usually settle within a week of invoice
    # date for prompt payers; longer gaps still possible but weaker.
    inv_date = invoice.get("invoice_date") or ""
    tx_date = tx.get("date") or ""
    if inv_date and tx_date:
        try:
            id_d = datetime.strptime(inv_date, "%Y-%m-%d").date()
            tx_d = datetime.strptime(tx_date, "%Y-%m-%d").date()
            days = abs((tx_d - id_d).days)
            if days <= 7:
                score += 10
            elif days <= 30:
                score += 5
            elif days <= 60:
                score += 2
        except Exception:
            pass

    return min(score, 100)


def _score_expense_match(tx: dict, expense: dict) -> int:
    """Returns a confidence score 0-100 for tx → expense (outgoing only)."""
    if (tx.get("amount") or 0) >= 0:
        return 0

    score = 0
    tx_amount = abs(float(tx.get("amount") or 0))
    ex_total = float(expense.get("amount_ex_btw") or 0) + float(expense.get("btw_amount") or 0)
    ex_ex = float(expense.get("amount_ex_btw") or 0)

    if ex_total > 0 and _amount_close(tx_amount, ex_total, 0.01):
        score += 60
    elif ex_ex > 0 and _amount_close(tx_amount, ex_ex, 0.01):
        score += 50

    desc_tx = (tx.get("description") or "").lower()
    merchant = (tx.get("merchant") or "").lower()
    desc_ex = (expense.get("description") or "").lower()
    if desc_ex and len(desc_ex) >= 3:
        if desc_ex in desc_tx or desc_ex in merchant:
            score += 30
        elif merchant and merchant in desc_ex:
            score += 20

    ex_date = expense.get("expense_date") or ""
    tx_date = tx.get("date") or ""
    if ex_date and tx_date:
        try:
            ed = datetime.strptime(ex_date, "%Y-%m-%d").date()
            td = datetime.strptime(tx_date, "%Y-%m-%d").date()
            days = abs((td - ed).days)
            if days <= 1:
                score += 10
            elif days <= 7:
                score += 5
            else:
                # Outside the typical bank-settlement window: probably
                # a different transaction altogether.
                score -= 15
        except Exception:
            pass

    return max(0, min(score, 100))


def _enrich_transaction_with_link(
    tx: dict,
    existing_links: dict,
    invoices: list,
    expenses: list,
    user_id: str,
) -> dict:
    """Attach a `link` field to `tx`. If a manual link exists, use it as-is.
    Otherwise compute the best automatic match and persist firm/suggested
    links to the bank_transaction_links table.
    """
    tx_id = tx.get("id")
    if not tx_id:
        tx["link"] = None
        return tx

    existing = existing_links.get(tx_id)
    if existing:
        tx["link"] = _hydrate_link(existing, invoices, expenses)
        return tx

    # No prior link — run the matcher.
    if (tx.get("amount") or 0) > 0:
        # Income → match against unpaid invoices.
        best = (0, None)
        for inv in invoices:
            s = _score_invoice_match(tx, inv)
            if s > best[0]:
                best = (s, inv)
        score, inv = best
        if inv and score >= MATCH_AUTO_SCORE:
            _persist_link(user_id, tx_id, "invoice", inv["id"], auto=True)
            _mark_invoice_paid(inv["id"])
            tx["link"] = {
                "type": "invoice",
                "linked_id": inv["id"],
                "linked_label": inv.get("invoice_number") or "Factuur",
                "auto": True,
                "confidence": score,
            }
            return tx
        if inv and score >= MATCH_SUGGEST_SCORE:
            _persist_link(user_id, tx_id, "suggested_invoice", inv["id"], auto=True)
            tx["link"] = {
                "type": "suggested_invoice",
                "linked_id": inv["id"],
                "linked_label": inv.get("invoice_number") or "Factuur",
                "auto": True,
                "confidence": score,
            }
            return tx
    elif (tx.get("amount") or 0) < 0:
        # Outgoing → match against existing expenses.
        best = (0, None)
        for ex in expenses:
            s = _score_expense_match(tx, ex)
            if s > best[0]:
                best = (s, ex)
        score, ex = best
        if ex and score >= MATCH_AUTO_SCORE:
            _persist_link(user_id, tx_id, "expense", ex["id"], auto=True)
            tx["link"] = {
                "type": "expense",
                "linked_id": ex["id"],
                "linked_label": (ex.get("description") or "Kosten")[:40],
                "auto": True,
                "confidence": score,
            }
            return tx
        if ex and score >= MATCH_SUGGEST_SCORE:
            _persist_link(user_id, tx_id, "suggested_expense", ex["id"], auto=True)
            tx["link"] = {
                "type": "suggested_expense",
                "linked_id": ex["id"],
                "linked_label": (ex.get("description") or "Kosten")[:40],
                "auto": True,
                "confidence": score,
            }
            return tx

    tx["link"] = None
    return tx


def _hydrate_link(link_row: dict, invoices: list, expenses: list) -> dict:
    """Convert a bank_transaction_links row into the shape the frontend
    wants, looking up the linked record's display label."""
    link_type = link_row.get("link_type")
    linked_id = link_row.get("linked_id")
    label = ""
    if link_type in ("invoice", "suggested_invoice") and linked_id:
        match = next((i for i in invoices if i.get("id") == linked_id), None)
        if match:
            label = match.get("invoice_number") or "Factuur"
    elif link_type in ("expense", "suggested_expense") and linked_id:
        match = next((e for e in expenses if e.get("id") == linked_id), None)
        if match:
            label = (match.get("description") or "Kosten")[:40]
    elif link_type == "private":
        label = "Privé"
    return {
        "type": link_type,
        "linked_id": linked_id,
        "linked_label": label,
        "auto": bool(link_row.get("auto")),
    }


def _persist_link(user_id: str, tx_id: str, link_type: str, linked_id: Optional[str], auto: bool) -> None:
    try:
        supabase.table("bank_transaction_links").upsert({
            "user_id": user_id,
            "tx_id": tx_id,
            "link_type": link_type,
            "linked_id": linked_id,
            "auto": auto,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="user_id,tx_id").execute()
    except Exception as e:
        print(f"[banking] link upsert failed (non-fatal): {e}")


def _mark_invoice_paid(invoice_id: str) -> None:
    try:
        supabase.table("invoices").update({
            "status": "paid",
        }).eq("id", invoice_id).execute()
    except Exception as e:
        print(f"[banking] invoice paid-mark failed (non-fatal): {e}")


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
    # Diagnostic: surface what is actually stored, so a 404 on the
    # _get_user_access_token call points at the missing field instead
    # of looking like a routing bug.
    diag = supabase.table("user_profiles")\
        .select("tink_access_token, tink_refresh_token, tink_token_expires_at, tink_credentials_id")\
        .eq("id", bigdogg_user_id).execute()
    if diag.data:
        d = diag.data[0]
        has_at = "yes" if d.get("tink_access_token") else "NO"
        has_rt = "yes" if d.get("tink_refresh_token") else "NO"
        has_cid = "yes" if d.get("tink_credentials_id") else "NO"
        exp = d.get("tink_token_expires_at") or "—"
        print(f"[tink] /transactions diag user={bigdogg_user_id[:8]}… "
              f"access_token={has_at} refresh_token={has_rt} credentials_id={has_cid} expires_at={exp}")
    else:
        print(f"[tink] /transactions diag user={bigdogg_user_id[:8]}… NO PROFILE ROW")
    access_token = await _get_user_access_token(bigdogg_user_id)

    # Tink data/v2/transactions caps pageSize at 100. Clamp so callers
    # asking for more do not 400 — we still return the (smaller) page
    # rather than failing the whole request.
    params: dict = {"pageSize": min(page_size, 100)}
    if page_token:
        params["pageToken"] = page_token

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            TRANSACTIONS_ENDPOINT,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if r.status_code == 401:
        # Token died on Tink's side — most common in sandbox after the
        # ~1h one-time-flow lifetime. Surface a structured error so the
        # frontend can show a "reconnect" CTA instead of a generic 502.
        print(f"[tink] transactions 401 (session expired): {r.text}")
        raise HTTPException(status_code=401, detail="bank_session_expired")
    if r.status_code >= 400:
        print(f"[tink] transactions error: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="Could not fetch transactions")

    raw = r.json()
    items = raw.get("transactions") or []
    normalized = [_normalize_tink_transaction(t) for t in items]
    normalized.sort(key=lambda t: t.get("date") or "", reverse=True)

    # Auto-match each transaction against existing invoices/expenses.
    invoices_result = supabase.table("invoices")\
        .select("id, invoice_number, total_incl_btw, status, client_name, client_company, invoice_date")\
        .eq("user_id", bigdogg_user_id).execute()
    invoices = invoices_result.data or []

    expenses_result = supabase.table("expenses")\
        .select("id, description, amount_ex_btw, btw_amount, expense_date")\
        .eq("user_id", bigdogg_user_id).execute()
    expenses = expenses_result.data or []

    tx_ids = [t.get("id") for t in normalized if t.get("id")]
    existing_links: dict = {}
    if tx_ids:
        try:
            links_result = supabase.table("bank_transaction_links")\
                .select("tx_id, link_type, linked_id, auto")\
                .eq("user_id", bigdogg_user_id)\
                .in_("tx_id", tx_ids).execute()
            for row in (links_result.data or []):
                existing_links[row["tx_id"]] = row
        except Exception as e:
            # Migration not run yet — degrade gracefully to no-link mode.
            print(f"[banking] link lookup failed (likely missing table): {e}")

    enriched = [
        _enrich_transaction_with_link(t, existing_links, invoices, expenses, bigdogg_user_id)
        for t in normalized
    ]
    return {
        "transactions": enriched,
        "next_page_token": raw.get("nextPageToken"),
    }


@router.post("/transactions/{tx_id}/link")
async def set_transaction_link(tx_id: str, request: Request):
    """Confirm or change a transaction link.

    Body:
      { "link_type": "invoice" | "expense" | "private" | null, "linked_id": "<uuid|null>" }

    - "invoice"  : also marks the invoice as paid.
    - "expense"  : just records the link.
    - "private"  : ignores the transaction (no linked record).
    - null       : removes any existing link. If we previously auto-marked
                   an invoice as paid because of this link, revert it.
    """
    user_id = get_user_id(request)
    body = await request.json()
    link_type = (body or {}).get("link_type")
    linked_id = (body or {}).get("linked_id")

    # Look up the existing link first so we can revert side-effects.
    prev_result = supabase.table("bank_transaction_links")\
        .select("link_type, linked_id, auto")\
        .eq("user_id", user_id).eq("tx_id", tx_id).execute()
    prev = prev_result.data[0] if prev_result.data else None

    if link_type is None:
        # Unlink. If the previous link was an auto-marked invoice, flip it back to 'sent'.
        if prev and prev.get("link_type") == "invoice" and prev.get("auto") and prev.get("linked_id"):
            try:
                supabase.table("invoices").update({
                    "status": "sent",
                }).eq("id", prev["linked_id"]).execute()
            except Exception as e:
                print(f"[banking] invoice paid-revert failed (non-fatal): {e}")
        try:
            supabase.table("bank_transaction_links")\
                .delete().eq("user_id", user_id).eq("tx_id", tx_id).execute()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"success": True, "link": None}

    if link_type not in ("invoice", "expense", "private"):
        raise HTTPException(status_code=400, detail="link_type must be invoice|expense|private|null")
    if link_type in ("invoice", "expense") and not linked_id:
        raise HTTPException(status_code=400, detail="linked_id required for invoice/expense links")

    _persist_link(user_id, tx_id, link_type, linked_id, auto=False)
    if link_type == "invoice":
        _mark_invoice_paid(linked_id)

    return {"success": True, "link": {"type": link_type, "linked_id": linked_id, "auto": False}}


class _CreateExpenseFromTx(dict):
    pass


@router.post("/transactions/{tx_id}/create-expense")
async def create_expense_from_transaction(tx_id: str, request: Request):
    """Create an expense from a transaction and link it.

    Body:
      { "description": "...", "amount_ex_btw": 12.34, "btw_rate": 21,
        "expense_date": "YYYY-MM-DD", "category": "general" }
    """
    user_id = get_user_id(request)
    body = await request.json()
    description = (body or {}).get("description") or "Bank transactie"
    amount_ex_btw = float((body or {}).get("amount_ex_btw") or 0)
    btw_rate = float((body or {}).get("btw_rate") or 21)
    expense_date = (body or {}).get("expense_date") or datetime.now(timezone.utc).date().isoformat()
    category = (body or {}).get("category") or "general"
    btw_amount = round(amount_ex_btw * btw_rate / 100, 2)

    insert = supabase.table("expenses").insert({
        "user_id": user_id,
        "description": description,
        "amount_ex_btw": amount_ex_btw,
        "btw_amount": btw_amount,
        "btw_rate": btw_rate,
        "expense_date": expense_date,
        "category": category,
    }).execute()
    if not insert.data:
        raise HTTPException(status_code=400, detail="Could not create expense")
    expense_id = insert.data[0]["id"]

    _persist_link(user_id, tx_id, "expense", expense_id, auto=False)

    return {
        "success": True,
        "expense": insert.data[0],
        "link": {"type": "expense", "linked_id": expense_id, "auto": False},
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
        .select("tink_user_id, tink_credentials_id, tink_connected_at, "
                "tink_token_expires_at, tink_refresh_token, tink_access_token")\
        .eq("id", bigdogg_user_id)\
        .execute()
    if not profile_result.data:
        return {"connected": False}
    profile = profile_result.data[0]

    has_credentials = bool(profile.get("tink_credentials_id"))
    has_access_token = bool(profile.get("tink_access_token"))
    has_refresh_token = bool(profile.get("tink_refresh_token"))
    expires_at_raw = profile.get("tink_token_expires_at")
    expired = False
    if has_access_token and not has_refresh_token and expires_at_raw:
        try:
            exp = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
            expired = datetime.now(timezone.utc) >= exp
        except Exception:
            expired = False

    return {
        # Only treat as "connected" if we still have a usable token. A
        # one-time-flow token that has aged past its expires_at can no
        # longer fetch transactions, so the UI should prompt to reconnect.
        "connected": has_credentials and not expired,
        "expired": expired,
        "tink_user_id": profile.get("tink_user_id"),
        "credentials_id": profile.get("tink_credentials_id"),
        "connected_at": profile.get("tink_connected_at"),
        "token_expires_at": expires_at_raw,
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

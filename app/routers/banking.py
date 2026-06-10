"""
TrueLayer Open Banking Data — NL bank connection + transaction sync.

Why TrueLayer: polished hosted bank-picker UI, broad NL coverage
(ING, Rabobank, ABN AMRO, SNS, ASN, Triodos, bunq, Knab, Revolut,
N26, …) via the Open Banking PSD2 license. One-step "connect" flow
where the user picks their bank inside TrueLayer's UI — no separate
institutions endpoint needed on our side.

End-to-end flow:
  1. App calls POST /api/v1/banking/connect.
  2. Backend mints a random state, stores it on user_profiles, and
     returns the TrueLayer auth URL.
  3. App opens that URL externally. User picks their bank, authenticates
     via the bank's hosted UI, and TrueLayer redirects to:
        GET /api/v1/banking/callback?code=...&state=...
  4. Backend validates the state, exchanges the authorization code for
     access + refresh tokens, stores them on user_profiles, and 302s the
     user back into the app with `?bank=success`.
  5. App calls GET /api/v1/banking/transactions to pull recent activity.
     Tokens are auto-refreshed via the refresh_token when they expire
     (TrueLayer access tokens last ~1 hour, refresh tokens last 90 days).

Required environment variables (Railway):
  - TRUELAYER_CLIENT_ID
  - TRUELAYER_CLIENT_SECRET
  - TRUELAYER_USE_SANDBOX ("true" / "false") — defaults to sandbox

Required Supabase columns on user_profiles (see migrations/truelayer_columns.sql):
  tl_access_token       text
  tl_refresh_token      text
  tl_token_expires_at   timestamptz
  tl_connected_at       timestamptz
  tl_link_state         text
  tl_provider_id        text

The redirect URI registered in the TrueLayer Console must be exactly:
  https://bigdogg-production.up.railway.app/api/v1/banking/callback
"""

from fastapi import APIRouter, HTTPException, Request, Query, UploadFile, File
from fastapi.responses import RedirectResponse, Response
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlencode
import base64
import json as _json
import secrets
import httpx
from cryptography.fernet import Fernet, InvalidToken

from app.database import supabase
from app.config import settings
from app.routers.notifications import create_notification
from app.services.bank_statement_parser import parse_statement
from app.services.tenant_db import require_owned_id, update_owned


router = APIRouter()


# ─── TrueLayer endpoints ────────────────────────────────────────
def _is_sandbox() -> bool:
    return (settings.truelayer_use_sandbox or "").strip().lower() in (
        "1", "true", "yes", "y",
    )


def _auth_base() -> str:
    return ("https://auth.truelayer-sandbox.com" if _is_sandbox()
            else "https://auth.truelayer.com")


def _api_base() -> str:
    return ("https://api.truelayer-sandbox.com" if _is_sandbox()
            else "https://api.truelayer.com")


REDIRECT_URI = "https://bigdogg-production.up.railway.app/api/v1/banking/callback"
APP_RETURN_OK = "https://bigdogg.nl/#/dashboard?bank=success"
APP_RETURN_ERR = "https://bigdogg.nl/#/dashboard?bank_error="

# TrueLayer scopes for AIS (read-only account data).
# `offline_access` is what gives us a refresh_token.
SCOPES = "info accounts balance transactions offline_access"


def _provider_filter() -> str:
    """Which TrueLayer providers to surface in the hosted picker.

    Sandbox includes `uk-cs-mock` so we can test against TrueLayer's mock
    bank without real credentials. `nl-ob-all` is the catch-all that
    enables every NL Open Banking provider TrueLayer supports.

    TrueLayer expects SPACE-separated provider IDs in this param.
    Comma-separated yields a hosted-UI "Bad Request error" on
    login.truelayer(-sandbox).com/providers.
    """
    if _is_sandbox():
        return "uk-cs-mock uk-ob-all nl-ob-all"
    return "nl-ob-all"


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
    if not settings.truelayer_client_id or not settings.truelayer_client_secret:
        raise HTTPException(
            status_code=500,
            detail="TrueLayer credentials missing (TRUELAYER_CLIENT_ID / TRUELAYER_CLIENT_SECRET).",
        )


# ─── Feature flag ──────────────────────────────────────────────
def _live_enabled(user_id: str) -> bool:
    """Whether this user may use the LIVE bank-connect flow.

    Default-OPEN (launched state): with BANK_LIVE_USER_IDS unset or empty
    the flow is available to everyone. Set the env to a comma-separated
    list of Supabase user_ids to RESTRICT it to just those accounts — e.g.
    to re-gate during an incident or run a closed beta. A literal "*" also
    means everyone. Driven entirely by env so the gate flips without a
    code deploy.
    """
    allow = {
        x.strip() for x in (settings.bank_live_user_ids or "").split(",") if x.strip()
    }
    if not allow or "*" in allow:
        return True
    return bool(user_id) and user_id in allow


def _has_cached_transactions(user_id: str) -> bool:
    """True if the user has any rows in the bank_transactions cache
    (live-synced OR file-imported). Drives the 'View transactions' entry
    point in the app even when no bank is connected."""
    try:
        res = supabase.table("bank_transactions")\
            .select("external_id").eq("user_id", user_id).limit(1).execute()
        return bool(res.data)
    except Exception:
        return False


# ─── Token encryption at rest ──────────────────────────────────
def _fernet() -> Optional[Fernet]:
    key = (settings.tl_token_enc_key or "").strip()
    if not key:
        return None
    return Fernet(key.encode())


def _encrypt_token(plain: Optional[str]) -> Optional[str]:
    """Encrypt a TrueLayer token before persisting. Fail closed: if no key
    is configured we refuse to store a plaintext bank token."""
    if plain is None:
        return None
    f = _fernet()
    if f is None:
        raise HTTPException(
            status_code=500,
            detail="TL_TOKEN_ENC_KEY not configured — cannot store bank tokens.",
        )
    return f.encrypt(plain.encode()).decode()


def _decrypt_token(stored: Optional[str]) -> Optional[str]:
    """Decrypt a stored TrueLayer token. Tolerant of legacy plaintext rows
    written before encryption existed: if the value isn't a valid Fernet
    token, return it unchanged so a pre-existing connection still works
    until its next refresh re-encrypts it."""
    if not stored:
        return stored
    f = _fernet()
    if f is None:
        return stored
    try:
        return f.decrypt(stored.encode()).decode()
    except InvalidToken:
        return stored


# ─── Token management ──────────────────────────────────────────
def _build_auth_url(state: str) -> str:
    """Construct the TrueLayer hosted-auth URL the user opens in browser.

    TrueLayer's hosted UI shows a list of supported providers (banks),
    handles all the PSD2 consent screens, and finally 302s back to our
    REDIRECT_URI with `?code=...&state=...`.
    """
    params = {
        "response_type": "code",
        "client_id": settings.truelayer_client_id,
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "providers": _provider_filter(),
        "state": state,
    }
    return f"{_auth_base()}/?" + urlencode(params)


async def _exchange_code(code: str) -> dict:
    """Authorization code → { access_token, refresh_token, expires_in }."""
    _ensure_credentials_configured()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            f"{_auth_base()}/connect/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.truelayer_client_id,
                "client_secret": settings.truelayer_client_secret,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if r.status_code >= 400:
        print(f"[truelayer] code exchange failed: {r.status_code} {r.text}")
        raise HTTPException(status_code=502, detail="TrueLayer code exchange failed")
    return r.json()


async def _refresh_user_token(refresh_token: str) -> dict:
    """refresh_token → fresh { access_token, refresh_token, expires_in }."""
    _ensure_credentials_configured()
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        r = await client.post(
            f"{_auth_base()}/connect/token",
            data={
                "grant_type": "refresh_token",
                "client_id": settings.truelayer_client_id,
                "client_secret": settings.truelayer_client_secret,
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if r.status_code >= 400:
        print(f"[truelayer] refresh failed: {r.status_code} {r.text}")
        raise HTTPException(status_code=401, detail="TrueLayer refresh failed")
    return r.json()


async def _get_user_access_token(bigdogg_user_id: str) -> str:
    """Fetch the user's TrueLayer access token, refreshing if needed.

    Refresh kicks in when the cached token has under 60 seconds of life
    left, so a slow-running request that started near the boundary won't
    end up sending an expired token.
    """
    profile_result = supabase.table("user_profiles")\
        .select("tl_access_token, tl_refresh_token, tl_token_expires_at")\
        .eq("id", bigdogg_user_id).execute()
    if not profile_result.data:
        raise HTTPException(status_code=404, detail="No bank connection")
    profile = profile_result.data[0]
    access_token = _decrypt_token(profile.get("tl_access_token"))
    refresh = _decrypt_token(profile.get("tl_refresh_token"))
    expires_at_raw = profile.get("tl_token_expires_at")
    if not access_token:
        raise HTTPException(status_code=404, detail="No bank connection")

    needs_refresh = False
    if expires_at_raw:
        try:
            exp = datetime.fromisoformat(expires_at_raw.replace("Z", "+00:00"))
            if (exp - datetime.now(timezone.utc)).total_seconds() < 60:
                needs_refresh = True
        except Exception:
            needs_refresh = True
    else:
        needs_refresh = True

    if needs_refresh and refresh:
        try:
            tokens = await _refresh_user_token(refresh)
        except HTTPException:
            # Refresh chain is broken — surface to caller, which will
            # bubble up to the frontend as "reconnect needed".
            raise
        access_token = tokens["access_token"]
        new_refresh = tokens.get("refresh_token", refresh)
        expires_in = int(tokens.get("expires_in", 3600))
        new_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)
        supabase.table("user_profiles").update({
            "tl_access_token": _encrypt_token(access_token),
            "tl_refresh_token": _encrypt_token(new_refresh),
            "tl_token_expires_at": new_expires.isoformat(),
        }).eq("id", bigdogg_user_id).execute()

    return access_token


# ─── Connect / callback ────────────────────────────────────────
@router.post("/connect")
async def connect_bank(request: Request):
    """Mint a fresh TrueLayer auth URL and return it to the caller.

    The app should open this URL in an external browser (mobile) or a
    new tab (web). TrueLayer's hosted UI handles bank picker + PSD2
    consent flow; on completion, TrueLayer redirects to /callback.
    """
    bigdogg_user_id = get_user_id(request)
    # Flag gate: the live PSD2 flow is dark for everyone except the
    # allowlisted founder account until rollout. The Flutter overlay
    # enforces this in the UI; this is the server-side backstop so a
    # direct API call can't bypass it.
    if not _live_enabled(bigdogg_user_id):
        raise HTTPException(status_code=403, detail="bank_live_not_enabled")
    _ensure_credentials_configured()

    state = secrets.token_urlsafe(24)

    profile_check = supabase.table("user_profiles")\
        .select("id").eq("id", bigdogg_user_id).execute()
    if profile_check.data:
        supabase.table("user_profiles").update({
            "tl_link_state": state,
        }).eq("id", bigdogg_user_id).execute()
    else:
        supabase.table("user_profiles").insert({
            "id": bigdogg_user_id,
            "tl_link_state": state,
        }).execute()

    return {"link_url": _build_auth_url(state)}


@router.get("/callback")
async def banking_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """TrueLayer redirects here after the user finishes the bank flow.

    On success we exchange the authorization code for tokens, persist
    them, and redirect back into the app. Errors are funneled through
    `?bank_error=<reason>` so the dashboard can surface them.
    """
    if error or not code or not state:
        msg = error_description or error or "missing_code"
        return RedirectResponse(url=f"{APP_RETURN_ERR}{msg}")

    state_lookup = supabase.table("user_profiles")\
        .select("id, tl_link_state")\
        .eq("tl_link_state", state)\
        .limit(1).execute()
    if not state_lookup.data:
        return RedirectResponse(url=f"{APP_RETURN_ERR}invalid_state")
    bigdogg_user_id = state_lookup.data[0]["id"]

    try:
        tokens = await _exchange_code(code)
    except HTTPException:
        return RedirectResponse(url=f"{APP_RETURN_ERR}token_exchange_failed")

    expires_in = int(tokens.get("expires_in", 3600))
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)

    # Best-effort: ask /data/v1/me which provider the user just connected
    # to, so we can show "Bank: ING" on the Settings card. Non-fatal.
    provider_id: Optional[str] = None
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(
                f"{_api_base()}/data/v1/me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
        if r.status_code == 200:
            me_results = (r.json() or {}).get("results", [])
            if me_results:
                provider_id = ((me_results[0] or {}).get("provider") or {}).get("provider_id")
    except Exception as e:
        print(f"[truelayer] /me lookup failed (non-fatal): {e}")

    supabase.table("user_profiles").update({
        "tl_access_token": _encrypt_token(tokens["access_token"]),
        "tl_refresh_token": _encrypt_token(tokens.get("refresh_token")),
        "tl_token_expires_at": expires_at.isoformat(),
        "tl_connected_at": datetime.now(timezone.utc).isoformat(),
        "tl_link_state": None,
        "tl_provider_id": provider_id,
    }).eq("id", bigdogg_user_id).execute()

    print(f"[truelayer] connected: user={bigdogg_user_id[:8]}… provider={provider_id}")
    return RedirectResponse(url=APP_RETURN_OK)


# ─── Matcher constants ─────────────────────────────────────────
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


# ─── Matcher ───────────────────────────────────────────────────
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


def _score_investment_match(tx: dict, investment: dict) -> int:
    """Returns a confidence score 0-100 for tx → investment (outgoing only).

    Investments are large purchases that get depreciated over multiple
    years. Matching is amount-driven — a single fixed total stored on the
    investment row — with description and date as secondary signals.
    """
    if (tx.get("amount") or 0) >= 0:
        return 0

    score = 0
    tx_amount = abs(float(tx.get("amount") or 0))
    inv_amount = float(investment.get("amount") or 0)

    if inv_amount > 0 and abs(tx_amount - inv_amount) <= 0.01:
        score += 60
    elif inv_amount > 0 and abs(tx_amount - inv_amount) / inv_amount <= 0.005:
        score += 50

    desc_tx = (tx.get("description") or "").lower()
    merchant = (tx.get("merchant") or "").lower()
    desc_inv = (investment.get("description") or "").lower()
    if desc_inv and len(desc_inv) >= 3:
        if desc_inv in desc_tx or desc_inv in merchant:
            score += 30
        elif merchant and merchant in desc_inv:
            score += 20

    inv_date = investment.get("purchase_date") or ""
    tx_date = tx.get("date") or ""
    if inv_date and tx_date:
        try:
            id_d = datetime.strptime(inv_date, "%Y-%m-%d").date()
            tx_d = datetime.strptime(tx_date, "%Y-%m-%d").date()
            days = abs((tx_d - id_d).days)
            if days <= 1:
                score += 10
            elif days <= 7:
                score += 5
            else:
                score -= 15
        except Exception:
            pass

    return max(0, min(score, 100))


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


def _format_amount_eur(amount: float) -> str:
    return f"€ {abs(amount):.2f}".replace(".", ",")


# ─── Link persistence + hydration ─────────────────────────────
def _confirmed_taken_ids(existing_links: dict) -> set:
    """IDs of invoices/expenses/investments already linked to a transaction,
    fed to the matcher so it never double-links a target (one-to-one)."""
    return {
        r["linked_id"] for r in existing_links.values()
        if r.get("link_type") in ("invoice", "expense", "investment")
        and r.get("linked_id")
    }


def _enrich_transaction_with_link(
    tx: dict,
    existing_links: dict,
    invoices: list,
    expenses: list,
    investments: list,
    user_id: str,
    taken_ids: Optional[set] = None,
) -> dict:
    """Attach a `link` field to `tx`. If a manual link exists, use it as-is.
    Otherwise compute the best automatic match and persist firm/suggested
    links to the bank_transaction_links table.

    Outgoing tx are matched against BOTH expenses and investments; we
    pick whichever scores highest. Auto-links also fire an in-app
    notification so the user can see what happened (and revert if
    wrong) without having to open the Transactions screen.
    """
    tx_id = tx.get("id")
    if not tx_id:
        tx["link"] = None
        return tx

    existing = existing_links.get(tx_id)
    if existing:
        tx["link"] = _hydrate_link(existing, invoices, expenses, investments)
        return tx

    amount = float(tx.get("amount") or 0)

    # ── Income → invoices ──
    if amount > 0:
        best_inv = (0, None)
        for inv in invoices:
            if taken_ids and inv.get("id") in taken_ids:
                continue  # already linked to another transaction
            s = _score_invoice_match(tx, inv)
            if s > best_inv[0]:
                best_inv = (s, inv)
        score, inv = best_inv
        if inv and score >= MATCH_AUTO_SCORE:
            _persist_link(user_id, tx_id, "invoice", inv["id"], auto=True)
            _mark_invoice_paid(inv["id"], user_id)
            inv_label = inv.get("invoice_number") or "Factuur"
            _notify_match(
                user_id, kind="auto",
                title=f"Betaling gekoppeld aan {inv_label}",
                body=f"{_format_amount_eur(amount)} ontvangen en automatisch gekoppeld aan factuur {inv_label}. Klopt het niet? Open de transactie om te ontkoppelen.",
                link_type="invoice", linked_id=inv["id"], tx_id=tx_id,
            )
            tx["link"] = {
                "type": "invoice", "linked_id": inv["id"],
                "linked_label": inv_label, "auto": True, "confidence": score,
            }
            return tx
        if inv and score >= MATCH_SUGGEST_SCORE:
            _persist_link(user_id, tx_id, "suggested_invoice", inv["id"], auto=True)
            inv_label = inv.get("invoice_number") or "Factuur"
            _notify_match(
                user_id, kind="suggest",
                title=f"Betaling ontvangen — is dit factuur {inv_label}?",
                body=f"{_format_amount_eur(amount)} binnen. Wij denken dat dit factuur {inv_label} betreft. Tik om te bevestigen of een andere factuur te kiezen.",
                link_type="invoice", linked_id=inv["id"], tx_id=tx_id,
            )
            tx["link"] = {
                "type": "suggested_invoice", "linked_id": inv["id"],
                "linked_label": inv_label, "auto": True, "confidence": score,
            }
            return tx

    # ── Outgoing → expenses + investments (best wins) ──
    elif amount < 0:
        best_ex = (0, None)
        for ex in expenses:
            if taken_ids and ex.get("id") in taken_ids:
                continue  # already linked to another transaction
            s = _score_expense_match(tx, ex)
            if s > best_ex[0]:
                best_ex = (s, ex)

        best_iv = (0, None)
        for iv in investments:
            if taken_ids and iv.get("id") in taken_ids:
                continue  # already linked to another transaction
            s = _score_investment_match(tx, iv)
            if s > best_iv[0]:
                best_iv = (s, iv)

        if best_iv[0] > best_ex[0]:
            score, target, link_kind = best_iv[0], best_iv[1], "investment"
        else:
            score, target, link_kind = best_ex[0], best_ex[1], "expense"

        if target and score >= MATCH_AUTO_SCORE:
            label = (target.get("description") or
                     ("Investering" if link_kind == "investment" else "Kosten"))[:40]
            _persist_link(user_id, tx_id, link_kind, target["id"], auto=True)
            kind_nl = "investering" if link_kind == "investment" else "kosten"
            _notify_match(
                user_id, kind="auto",
                title=f"Uitgave gekoppeld aan {kind_nl} · {label}",
                body=f"{_format_amount_eur(amount)} automatisch gekoppeld aan {kind_nl} · {label}. Klopt het niet? Open de transactie om te ontkoppelen.",
                link_type=link_kind, linked_id=target["id"], tx_id=tx_id,
            )
            tx["link"] = {
                "type": link_kind, "linked_id": target["id"],
                "linked_label": label, "auto": True, "confidence": score,
            }
            return tx
        if target and score >= MATCH_SUGGEST_SCORE:
            suggested_kind = f"suggested_{link_kind}"
            label = (target.get("description") or
                     ("Investering" if link_kind == "investment" else "Kosten"))[:40]
            kind_nl = "investering" if link_kind == "investment" else "kosten"
            _persist_link(user_id, tx_id, suggested_kind, target["id"], auto=True)
            _notify_match(
                user_id, kind="suggest",
                title=f"Uitgave gezien — is dit {kind_nl} · {label}?",
                body=f"{_format_amount_eur(amount)} afgeschreven. Wij denken dat dit {kind_nl} · {label} betreft. Tik om te bevestigen of een andere optie te kiezen.",
                link_type=link_kind, linked_id=target["id"], tx_id=tx_id,
            )
            tx["link"] = {
                "type": suggested_kind, "linked_id": target["id"],
                "linked_label": label, "auto": True, "confidence": score,
            }
            return tx

    tx["link"] = None
    return tx


def _hydrate_link(link_row: dict, invoices: list, expenses: list, investments: list) -> dict:
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
    elif link_type in ("investment", "suggested_investment") and linked_id:
        match = next((i for i in investments if i.get("id") == linked_id), None)
        if match:
            label = (match.get("description") or "Investering")[:40]
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


def _mark_invoice_paid(invoice_id: str, user_id: str) -> None:
    """Mark an invoice paid, scoped to its owner.

    IMPORTANT: `user_id` must be the authenticated caller. The owner-scoped
    UPDATE is what prevents the prior IDOR — without it, any user could
    pass a victim's invoice_id and silently flip its status. Failures are
    swallowed (this is called from auto-match where a 404 is unexpected
    but never user-visible)."""
    try:
        update_owned("invoices", invoice_id, user_id, {"status": "paid"})
    except Exception as e:
        print(f"[banking] invoice paid-mark failed (non-fatal): {e}")


def _notify_match(
    user_id: str,
    *,
    kind: str,                 # "auto" or "suggest"
    title: str,
    body: str,
    link_type: str,            # "invoice" | "expense" | "investment"
    linked_id: str,
    tx_id: str,
) -> None:
    """In-app notification surfaced via the existing bell icon.

    Two flavours, sharing the same plumbing so the frontend can route on
    `notification_type`:

      bank_auto_link  — high-confidence link already applied; user can
                        revert by tapping into the transaction.
      bank_suggest    — medium-confidence guess waiting for confirmation;
                        tapping the notification opens the transaction
                        with the yellow "Klopt? / Anders" sheet ready.

    Stays silent on failure — a notification must never break a
    /transactions fetch.
    """
    notification_type = "bank_auto_link" if kind == "auto" else "bank_suggest"
    try:
        create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data={
                "link_type": link_type,
                "linked_id": linked_id,
                "tx_id": tx_id,
                "kind": kind,
            },
        )
    except Exception as e:
        print(f"[banking] notification skipped: {e}")


# ─── TrueLayer transaction normalization ──────────────────────
def _normalize_truelayer_transaction(tx: dict, account_id: str) -> dict:
    """Flatten TrueLayer's transaction shape to the internal fields the
    matcher expects: positive amount for incoming, negative for outgoing,
    natural decimal form, lowercase-friendly strings.

    TrueLayer schema reference:
      https://docs.truelayer.com/reference/datav1transactions
    """
    raw_amount = float(tx.get("amount") or 0)
    tx_type = (tx.get("transaction_type") or "").upper()
    if tx_type == "DEBIT":
        amount = -abs(raw_amount)
    elif tx_type == "CREDIT":
        amount = abs(raw_amount)
    else:
        # Fallback to whatever TL gave us (some providers omit type).
        amount = raw_amount

    timestamp = tx.get("timestamp") or ""
    tx_date = timestamp[:10] if timestamp else ""

    return {
        "id": tx.get("transaction_id") or "",
        "amount": amount,
        "currency": tx.get("currency") or "EUR",
        "description": tx.get("description") or "",
        "merchant": tx.get("merchant_name") or "",
        "date": tx_date,
        "account_id": account_id,
        "raw": tx,
    }


async def _fetch_truelayer_transactions(
    access_token: str,
) -> List[dict]:
    """Aggregate booked transactions across every account on this
    connection. Best-effort — failures on one account don't abort the
    others. Returns the internal-shape list (already normalized)."""
    aggregated: List[dict] = []

    # 1. List accounts
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(
                f"{_api_base()}/data/v1/accounts",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if r.status_code != 200:
            print(f"[truelayer] /accounts failed: {r.status_code} {r.text}")
            return []
        accounts = (r.json() or {}).get("results", []) or []
    except Exception as e:
        print(f"[truelayer] /accounts failed: {e}")
        return []

    # 2. For each account, pull transactions
    for acc in accounts:
        account_id = acc.get("account_id")
        if not account_id:
            continue
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                r = await client.get(
                    f"{_api_base()}/data/v1/accounts/{account_id}/transactions",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
            if r.status_code != 200:
                print(f"[truelayer] /transactions for {account_id} failed: {r.status_code}")
                continue
            results = (r.json() or {}).get("results", []) or []
            for tx in results:
                aggregated.append(_normalize_truelayer_transaction(tx, account_id))
        except Exception as e:
            print(f"[truelayer] transactions fetch for {account_id} failed: {e}")
            continue

    aggregated.sort(key=lambda t: t.get("date") or "", reverse=True)
    return aggregated


def _cache_transactions(user_id: str, normalized: List[dict]) -> None:
    """Upsert the just-fetched live transactions into the bank_transactions
    cache. The unique index on (user_id, external_id) makes repeated calls
    a no-op. Source is tagged `truelayer` so the file-import (MT940/CAMT)
    rows remain distinguishable."""
    if not normalized:
        return
    rows = []
    for tx in normalized:
        if not tx.get("id"):
            continue
        rows.append({
            "user_id": user_id,
            "external_id": tx["id"],
            "source": "truelayer",
            "date": tx.get("date") or None,
            "amount": tx.get("amount"),
            "currency": tx.get("currency") or "EUR",
            "description": tx.get("description") or "",
            "merchant": tx.get("merchant") or "",
            "account_iban": None,
            "raw": tx.get("raw"),
        })
    if not rows:
        return
    try:
        supabase.table("bank_transactions").upsert(
            rows, on_conflict="user_id,external_id"
        ).execute()
    except Exception as e:
        print(f"[truelayer] cache upsert failed: {e}")


# ─── Reconcile (background) ────────────────────────────────────
def schedule_reconcile(user_id: str) -> None:
    """Fire-and-forget kickoff for the matcher. Safe to call from any
    request handler — never raises, never blocks."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(reconcile_user_transactions(user_id))
    except RuntimeError:
        # No running loop (e.g. sync context) — drop the request.
        # Reconcile will run next time /banking/transactions is called.
        pass
    except Exception as e:
        print(f"[banking] reconcile schedule failed (non-fatal): {e}")


async def reconcile_user_transactions(user_id: str) -> None:
    """Re-run the matcher across the user's recent bank transactions.

    Called as a FastAPI background task whenever the user creates an
    invoice, expense, or investment — so a freshly-added entry that
    happens to correspond to an existing bank transaction gets linked
    immediately (and the user gets a notification) instead of waiting
    until they next open the Transactions screen.

    Silent on every kind of failure. Reconciliation must never break
    the upstream POST that triggered it.
    """
    try:
        # Skip silently if no bank connection.
        profile_result = supabase.table("user_profiles")\
            .select("tl_access_token, tl_refresh_token, tl_token_expires_at")\
            .eq("id", user_id).execute()
        if not profile_result.data:
            return
        profile = profile_result.data[0]
        if not profile.get("tl_access_token"):
            return

        try:
            access_token = await _get_user_access_token(user_id)
        except HTTPException:
            return  # refresh chain broken — surface on next user-driven fetch
        except Exception as e:
            print(f"[banking] reconcile token fetch failed: {e}")
            return

        normalized = await _fetch_truelayer_transactions(access_token)
        if not normalized:
            return
        _cache_transactions(user_id, normalized)

        invoices = (supabase.table("invoices").select(
            "id, invoice_number, total_incl_btw, status, client_name, "
            "client_company, invoice_date").eq("user_id", user_id).execute().data) or []
        expenses = (supabase.table("expenses").select(
            "id, description, amount_ex_btw, btw_amount, expense_date"
        ).eq("user_id", user_id).execute().data) or []
        investments = (supabase.table("investments").select(
            "id, description, amount, purchase_date, category"
        ).eq("user_id", user_id).execute().data) or []

        tx_ids = [t.get("id") for t in normalized if t.get("id")]
        existing_links: dict = {}
        if tx_ids:
            try:
                links_result = supabase.table("bank_transaction_links")\
                    .select("tx_id, link_type, linked_id, auto")\
                    .eq("user_id", user_id)\
                    .in_("tx_id", tx_ids).execute()
                for row in (links_result.data or []):
                    existing_links[row["tx_id"]] = row
            except Exception as e:
                print(f"[banking] reconcile link lookup failed: {e}")

        # Only run the matcher on transactions that aren't already
        # linked. Auto-linking + notifications happen inside
        # _enrich_transaction_with_link as a side effect.
        taken_ids = _confirmed_taken_ids(existing_links)
        new_matches = 0
        for tx in normalized:
            if existing_links.get(tx.get("id")):
                continue
            before = tx.get("link")
            _enrich_transaction_with_link(
                tx, existing_links, invoices, expenses, investments, user_id, taken_ids,
            )
            link = tx.get("link")
            if link and link.get("type") in ("invoice", "expense", "investment") and link.get("linked_id"):
                taken_ids.add(link["linked_id"])
            if link and link != before:
                new_matches += 1
        print(f"[banking] reconcile: user={user_id[:8]}… "
              f"checked={len(normalized)} new_matches={new_matches}")
    except Exception as e:
        print(f"[banking] reconcile error (non-fatal): {e}")


# ─── Transactions endpoint ─────────────────────────────────────
async def _enriched_transactions_for_user(
    user_id: str, page_size: int
) -> Tuple[List[dict], bool]:
    """Fetch + enrich a user's transactions. Shared by GET /transactions and
    GET /report so both show IDENTICAL data (the report bug was reading only
    the cache while the screen showed live data).

    Live-fetches when a bank is connected (and caches); otherwise serves the
    bank_transactions cache (file imports). Each tx gets its invoice/expense/
    investment link via the matcher. Returns (enriched, reconnect_required).
    """
    profile_result = supabase.table("user_profiles")\
        .select("tl_access_token")\
        .eq("id", user_id).execute()
    has_connection = bool(
        profile_result.data and profile_result.data[0].get("tl_access_token")
    )

    normalized: List[dict] = []
    if has_connection:
        try:
            access_token = await _get_user_access_token(user_id)
        except HTTPException as e:
            if e.status_code == 401:
                return [], True
            raise
        normalized = await _fetch_truelayer_transactions(access_token)
        if normalized:
            _cache_transactions(user_id, normalized)

    invoices = (supabase.table("invoices").select(
        "id, invoice_number, total_incl_btw, status, client_name, "
        "client_company, invoice_date").eq("user_id", user_id).execute().data) or []
    expenses = (supabase.table("expenses").select(
        "id, description, amount_ex_btw, btw_amount, expense_date"
    ).eq("user_id", user_id).execute().data) or []
    investments = (supabase.table("investments").select(
        "id, description, amount, purchase_date, category"
    ).eq("user_id", user_id).execute().data) or []

    # No live rows (no connection, or transient error) → serve the cache so
    # the screen/report isn't blank and file imports show.
    combined = normalized
    if not combined:
        try:
            cache_result = supabase.table("bank_transactions")\
                .select("external_id, date, amount, currency, description, merchant")\
                .eq("user_id", user_id)\
                .order("date", desc=True)\
                .limit(page_size).execute()
            for row in (cache_result.data or []):
                combined.append({
                    "id": row["external_id"],
                    "amount": float(row.get("amount") or 0),
                    "currency": row.get("currency") or "EUR",
                    "description": row.get("description") or "",
                    "merchant": row.get("merchant") or "",
                    "date": (row.get("date") or "")[:10] if row.get("date") else "",
                    "account_id": None,
                    "raw": None,
                })
        except Exception as e:
            print(f"[banking] cache fallback failed: {e}")

    tx_ids = [t.get("id") for t in combined if t.get("id")]
    existing_links: dict = {}
    if tx_ids:
        try:
            links_result = supabase.table("bank_transaction_links")\
                .select("tx_id, link_type, linked_id, auto")\
                .eq("user_id", user_id)\
                .in_("tx_id", tx_ids).execute()
            for row in (links_result.data or []):
                existing_links[row["tx_id"]] = row
        except Exception:
            pass

    taken_ids = _confirmed_taken_ids(existing_links)
    enriched = []
    for t in combined[:page_size]:
        _enrich_transaction_with_link(
            t, existing_links, invoices, expenses, investments, user_id, taken_ids
        )
        link = t.get("link")
        if link and link.get("type") in ("invoice", "expense", "investment") and link.get("linked_id"):
            taken_ids.add(link["linked_id"])
        enriched.append(t)
    return enriched, False


@router.get("/transactions")
async def get_transactions(
    request: Request,
    page_size: int = Query(100, ge=1, le=500),
):
    """Aggregate booked transactions across all connected accounts.

    Flow:
      1. Refresh the user's TrueLayer access token if needed.
      2. Live-fetch transactions from TrueLayer (all accounts).
      3. Upsert them into the bank_transactions cache so the matcher
         and file-import paths see the same data.
      4. Look up existing links + run the matcher to auto-link / suggest.
      5. Return enriched list to the frontend.

    Falls back to the cache (read-only) if TrueLayer returns an error
    state — so a temporary aggregator outage doesn't blank the screen.
    """
    bigdogg_user_id = get_user_id(request)
    enriched, reconnect_required = await _enriched_transactions_for_user(
        bigdogg_user_id, page_size
    )
    if reconnect_required:
        return {"transactions": [], "reconnect_required": True}
    return {"transactions": enriched}


# ─── Link / create-from-tx endpoints ───────────────────────────
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
        # Unlink. If the previous link was an auto-marked invoice, flip it
        # back to 'sent' — but only if the invoice still belongs to the
        # caller. (Historical state before the IDOR fix could contain a
        # link whose linked_id points at someone else's invoice; soft-fail
        # in that case rather than touching a foreign row.)
        if prev and prev.get("link_type") == "invoice" and prev.get("auto") and prev.get("linked_id"):
            try:
                update_owned(
                    "invoices", prev["linked_id"], user_id,
                    {"status": "sent"},
                )
            except Exception as e:
                print(f"[banking] invoice paid-revert skipped (non-fatal): {e}")
        try:
            supabase.table("bank_transaction_links")\
                .delete().eq("user_id", user_id).eq("tx_id", tx_id).execute()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"success": True, "link": None}

    if link_type not in ("invoice", "expense", "investment", "private"):
        raise HTTPException(status_code=400, detail="link_type must be invoice|expense|investment|private|null")
    if link_type in ("invoice", "expense", "investment") and not linked_id:
        raise HTTPException(status_code=400, detail="linked_id required for invoice/expense/investment links")

    # Verify the linked resource belongs to the caller BEFORE persisting
    # the link or applying side-effects. Without this, a user could pass
    # any victim's invoice_id and flip its status (the original IDOR).
    if link_type == "invoice":
        require_owned_id("invoices", linked_id, user_id)
    elif link_type == "expense":
        require_owned_id("expenses", linked_id, user_id)
    elif link_type == "investment":
        require_owned_id("investments", linked_id, user_id)

    # One-to-one: an invoice/expense/investment may be linked to at most one
    # transaction. Reject if a DIFFERENT transaction already links this target.
    if link_type in ("invoice", "expense", "investment"):
        already = False
        try:
            dup = supabase.table("bank_transaction_links")\
                .select("tx_id")\
                .eq("user_id", user_id)\
                .eq("linked_id", linked_id)\
                .neq("tx_id", tx_id)\
                .in_("link_type", ["invoice", "expense", "investment"])\
                .limit(1).execute()
            already = bool(dup.data)
        except Exception as e:
            print(f"[banking] duplicate-link check failed (allowing): {e}")
        if already:
            raise HTTPException(
                status_code=409,
                detail="already_linked_to_other_transaction",
            )

    _persist_link(user_id, tx_id, link_type, linked_id, auto=False)
    if link_type == "invoice":
        _mark_invoice_paid(linked_id, user_id)

    return {"success": True, "link": {"type": link_type, "linked_id": linked_id, "auto": False}}


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


@router.post("/transactions/{tx_id}/create-investment")
async def create_investment_from_transaction(tx_id: str, request: Request):
    """Create an investment from a transaction and link it.

    Body:
      { "description": "...", "amount": 2499.00,
        "purchase_date": "YYYY-MM-DD", "depreciation_years": 5,
        "category": "general" }
    """
    user_id = get_user_id(request)
    body = await request.json()
    description = (body or {}).get("description") or "Bank transactie"
    amount = float((body or {}).get("amount") or 0)
    purchase_date = (body or {}).get("purchase_date") or datetime.now(timezone.utc).date().isoformat()
    depreciation_years = int((body or {}).get("depreciation_years") or 5)
    category = (body or {}).get("category") or "general"

    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")

    insert = supabase.table("investments").insert({
        "user_id": user_id,
        "description": description,
        "amount": amount,
        "purchase_date": purchase_date,
        "depreciation_years": depreciation_years,
        "category": category,
    }).execute()
    if not insert.data:
        raise HTTPException(status_code=400, detail="Could not create investment")
    inv_id = insert.data[0]["id"]

    _persist_link(user_id, tx_id, "investment", inv_id, auto=False)

    return {
        "success": True,
        "investment": insert.data[0],
        "link": {"type": "investment", "linked_id": inv_id, "auto": False},
    }


# ─── Manual statement upload (MT940 / CAMT.053 / PDF) ───────────
async def _parse_pdf_statement(raw: bytes) -> Tuple[str, List[dict]]:
    """Extract transactions from a PDF bank statement using Claude vision.

    Most NL banks let users download a monthly statement as a PDF
    (ING "rekeningoverzicht", Rabobank "rekeningafschrift", etc).
    We send the PDF bytes to Claude with a tight extraction prompt and
    parse the JSON it returns. The output matches the MT940 / CAMT
    parsers' shape so the cache write + matcher path stays identical.
    """
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ai_not_configured")
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    b64 = base64.standard_b64encode(raw).decode("utf-8")
    prompt = """Extract every transaction from this bank statement PDF.

Return ONLY a raw JSON array (no markdown, no code fences). Each item:
{
  "date": "YYYY-MM-DD",
  "amount": -45.67,
  "currency": "EUR",
  "description": "...",
  "merchant": "..."
}

Rules:
- amount is SIGNED: outgoing/debit/af NEGATIVE, incoming/credit/bij POSITIVE
- include EVERY transaction shown, even small ones
- description: payment reference / free-text / mededeling from the bank
- merchant: counterparty name (creditor for outgoing, debtor for incoming)
- skip opening/closing balance rows, totals, page headers
- convert any date format (e.g. 14-05-2026) to YYYY-MM-DD
- if currency isn't shown, default to EUR
- return [] if no transactions are found"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw_text = msg.content[0].text.strip()
    # Strip markdown fencing if Claude returned any despite the prompt.
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed_txs = _json.loads(raw_text)
    except Exception as e:
        print(f"[banking] pdf json parse failed: {e} — head: {raw_text[:200]}")
        return "pdf", []
    if not isinstance(parsed_txs, list):
        return "pdf", []

    result: List[dict] = []
    for i, tx in enumerate(parsed_txs):
        if not isinstance(tx, dict):
            continue
        date_str = (tx.get("date") or "").strip() or None
        try:
            amount = float(tx.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        currency = (tx.get("currency") or "EUR").strip() or "EUR"
        description = (tx.get("description") or "").strip()
        merchant = (tx.get("merchant") or "").strip()
        # Synthetic external_id — same scheme as MT940/CAMT for dedupe
        # on repeat uploads. Include the row index so two rows with
        # identical date/amount/description don't collide.
        ext_id = f"pdf:{date_str}:{amount}:{description[:40]}:{i}"
        result.append({
            "id": ext_id,
            "date": date_str,
            "amount": amount,
            "currency": currency,
            "description": description,
            "merchant": merchant,
            "type": "BOOKING",
            "status": "BOOKED",
        })
    return "pdf", result


@router.post("/import")
async def import_bank_statement(request: Request, file: UploadFile = File(...)):
    """Parse an uploaded bank statement (MT940, CAMT.053, or PDF),
    persist its entries into the `bank_transactions` cache, and run the
    matcher against the user's invoices/expenses/investments. Returns a
    summary the frontend can show in a snackbar.

    No PSD2 connection needed — this is the file-import alternative to
    the live TrueLayer flow. Banks export to one of:
      * MT940 (SWIFT legacy) — parsed locally via mt-940 library
      * CAMT.053 (ISO 20022 XML) — parsed locally via stdlib xml
      * PDF (rekeningoverzicht) — parsed via Claude vision
    """
    user_id = get_user_id(request)
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty_file")

    # PDF magic bytes — try Claude vision before falling through to the
    # local MT940/CAMT detection (those text formats never start with %PDF).
    if raw[:5] == b"%PDF-":
        try:
            fmt, parsed = await _parse_pdf_statement(raw)
        except HTTPException:
            raise
        except Exception as e:
            print(f"[banking] pdf parse failed: {e}")
            raise HTTPException(status_code=400, detail="pdf_parse_failed")
    else:
        fmt, parsed = parse_statement(raw)
    if fmt == "unknown":
        raise HTTPException(status_code=400, detail="unrecognised_format")
    if not parsed:
        return {
            "format": fmt,
            "imported": 0,
            "auto_linked": 0,
            "suggested": 0,
            "message": "Geen transacties gevonden in dit bestand.",
        }

    # Upsert every parsed transaction into bank_transactions. Repeated
    # imports of the same file are a no-op thanks to the unique index
    # on (user_id, external_id).
    rows = []
    for tx in parsed:
        rows.append({
            "user_id": user_id,
            "external_id": tx["id"],
            "source": fmt,
            "date": tx.get("date"),
            "amount": tx.get("amount"),
            "currency": tx.get("currency") or "EUR",
            "description": tx.get("description") or "",
            "merchant": tx.get("merchant") or "",
            "raw": {"description": tx.get("description"), "type": tx.get("type")},
        })
    imported = 0
    try:
        supabase.table("bank_transactions").upsert(
            rows, on_conflict="user_id,external_id"
        ).execute()
        imported = len(rows)
    except Exception as e:
        print(f"[banking] import upsert failed: {e}")
        raise HTTPException(status_code=500, detail=f"import_failed: {e}")

    # Run the matcher. We use the same _enrich_transaction_with_link
    # that the live TrueLayer path uses; auto-matches fire notifications
    # via the existing bell-icon flow.
    invoices = (supabase.table("invoices").select(
        "id, invoice_number, total_incl_btw, status, client_name, client_company, invoice_date"
    ).eq("user_id", user_id).execute().data) or []
    expenses = (supabase.table("expenses").select(
        "id, description, amount_ex_btw, btw_amount, expense_date"
    ).eq("user_id", user_id).execute().data) or []
    investments = (supabase.table("investments").select(
        "id, description, amount, purchase_date, category"
    ).eq("user_id", user_id).execute().data) or []

    tx_ids = [t.get("id") for t in parsed if t.get("id")]
    existing_links: dict = {}
    if tx_ids:
        try:
            links_result = supabase.table("bank_transaction_links")\
                .select("tx_id, link_type, linked_id, auto")\
                .eq("user_id", user_id)\
                .in_("tx_id", tx_ids).execute()
            for row in (links_result.data or []):
                existing_links[row["tx_id"]] = row
        except Exception as e:
            print(f"[banking] import link lookup failed: {e}")

    taken_ids = _confirmed_taken_ids(existing_links)
    auto_linked = 0
    suggested = 0
    for tx in parsed:
        if existing_links.get(tx.get("id")):
            continue
        _enrich_transaction_with_link(
            tx, existing_links, invoices, expenses, investments, user_id, taken_ids,
        )
        link = tx.get("link") or {}
        if link.get("type") in ("invoice", "expense", "investment") and link.get("linked_id"):
            taken_ids.add(link["linked_id"])
        link_type = link.get("type") or ""
        if link_type in ("invoice", "expense", "investment"):
            auto_linked += 1
        elif link_type.startswith("suggested_"):
            suggested += 1

    return {
        "format": fmt,
        "imported": imported,
        "auto_linked": auto_linked,
        "suggested": suggested,
    }


# ─── Status / accounts / disconnect ───────────────────────────
@router.get("/accounts")
async def get_accounts(request: Request):
    """List the accounts attached to this user's TrueLayer connection.

    Returns the IBAN, display name, currency, and account type so the
    settings card can show e.g. "ING Betaalrekening · NL12RABO…".
    """
    bigdogg_user_id = get_user_id(request)
    try:
        access_token = await _get_user_access_token(bigdogg_user_id)
    except HTTPException:
        return {"accounts": []}

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get(
                f"{_api_base()}/data/v1/accounts",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if r.status_code != 200:
            return {"accounts": []}
        results = (r.json() or {}).get("results", []) or []
    except Exception as e:
        print(f"[truelayer] /accounts failed: {e}")
        return {"accounts": []}

    out = []
    for acc in results:
        acc_num = acc.get("account_number") or {}
        provider = acc.get("provider") or {}
        out.append({
            "id": acc.get("account_id"),
            "iban": acc_num.get("iban"),
            "name": acc.get("display_name") or provider.get("display_name"),
            "currency": acc.get("currency"),
            "product": acc.get("account_type"),
        })
    return {"accounts": out}


@router.get("/status")
async def banking_status(request: Request):
    """Whether the user has a connected bank, plus enough metadata for
    the Settings card to render."""
    bigdogg_user_id = get_user_id(request)
    live_enabled = _live_enabled(bigdogg_user_id)
    has_transactions = _has_cached_transactions(bigdogg_user_id)
    profile_result = supabase.table("user_profiles")\
        .select("tl_access_token, tl_connected_at, tl_token_expires_at, tl_provider_id")\
        .eq("id", bigdogg_user_id).execute()
    if not profile_result.data:
        return {
            "connected": False,
            "live_enabled": live_enabled,
            "has_transactions": has_transactions,
        }
    profile = profile_result.data[0]
    return {
        "connected": bool(profile.get("tl_access_token")),
        "connected_at": profile.get("tl_connected_at"),
        "token_expires_at": profile.get("tl_token_expires_at"),
        "provider_id": profile.get("tl_provider_id"),
        "live_enabled": live_enabled,
        "has_transactions": has_transactions,
    }


# ─── Linked-transactions report (PDF) ──────────────────────────
_REPORT_MATCHED_TYPES = ("invoice", "expense", "investment")


def _report_link_label(link: Optional[dict], lang: str = "nl") -> str:
    """Human label for the linked-to column (localised)."""
    en = lang == "en"
    if not link:
        return "—"
    t = link.get("type")
    lbl = (link.get("linked_label") or "").strip()
    if t == "invoice":
        return (f"Invoice {lbl}" if en else f"Factuur {lbl}").strip()
    if t == "expense":
        return (f"Expense · {lbl}" if en else f"Kosten · {lbl}").strip()
    if t == "investment":
        return (f"Investment · {lbl}" if en else f"Investering · {lbl}").strip()
    if t == "private":
        return "Private" if en else "Privé"
    if t and t.startswith("suggested_"):
        return (f"Suggestion · {lbl}" if en else f"Voorstel · {lbl}").strip()
    return "—"


def _report_rows_from_enriched(
    enriched: List[dict], matched_only: bool, lang: str = "nl"
) -> Tuple[List[dict], Dict[str, float]]:
    """Build report rows from the SAME enriched transactions the screen
    shows. When matched_only is set, unmatched + private rows are dropped so
    the export carries no personal transactions."""
    rows: List[dict] = []
    totals = {"in": 0.0, "out": 0.0}
    for tx in enriched:
        link = tx.get("link")
        is_matched = (link or {}).get("type") in _REPORT_MATCHED_TYPES
        if matched_only and not is_matched:
            continue
        amount = float(tx.get("amount") or 0)
        if is_matched:
            totals["in" if amount >= 0 else "out"] += amount
        rows.append({
            "date": (tx.get("date") or "")[:10],
            "amount": amount,
            "desc": (tx.get("merchant") or tx.get("description") or "").strip(),
            "link_label": _report_link_label(link, lang),
        })
    return rows, totals


def _build_report_pdf(
    rows: List[dict], totals: Dict[str, float], matched_only: bool,
    profile: Optional[dict] = None, lang: str = "nl",
) -> bytes:
    """Branded PDF matching the annual/VAT report letterhead (business-name
    header + gold rule + teal tables + footer). Localised via `lang`."""
    from io import BytesIO
    from datetime import datetime as _dt
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
    )
    from app.routers.pdf import TEAL, GOLD, LIGHT_GREY, MID_GREY, TEXT_SECONDARY

    profile = profile or {}
    business_name = (profile.get("business_name")
                     or profile.get("full_name") or "BigDogg")

    def eur(v: float) -> str:
        sign = "-" if v < 0 else "+"
        return f"{sign} € {abs(v):.2f}".replace(".", ",")

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    page_width = A4[0] - 40 * mm

    name_style = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=20, textColor=TEAL)
    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=14, textColor=TEAL, alignment=TA_RIGHT, leading=18)
    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=9, textColor=TEXT_SECONDARY, leading=14)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=10, textColor=TEAL, leading=14)
    total_style = ParagraphStyle('Total', fontName='Helvetica-Bold', fontSize=11, textColor=TEAL, leading=17)
    footer_style = ParagraphStyle('Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER)

    en = lang == "en"
    title = "Transaction overview" if en else "Transactieoverzicht"
    if matched_only:
        subtitle = "Matched transactions only" if en else "Alleen gekoppelde transacties"
    else:
        subtitle = "All transactions" if en else "Alle transacties"
    story = [
        Table(
            [[Paragraph(business_name, name_style),
              Paragraph(f"{title}<br/>{subtitle}", title_style)]],
            colWidths=[page_width * 0.55, page_width * 0.45],
            style=TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]),
        ),
        Spacer(1, 2 * mm),
        HRFlowable(width="100%", thickness=3, color=GOLD, spaceAfter=4 * mm),
        Table(
            [[[Paragraph('NAME' if en else 'NAAM', label_style), Paragraph(profile.get('full_name', '—') or '—', value_style)],
              [Paragraph('COUNT' if en else 'AANTAL', label_style), Paragraph(str(len(rows)), value_style)],
              [Paragraph('GENERATED' if en else 'GEGENEREERD', label_style), Paragraph(_dt.now().strftime('%d-%m-%Y'), value_style)]]],
            colWidths=[page_width / 3] * 3,
            style=TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]),
        ),
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4 * mm),
    ]

    data = [(["Date", "Amount", "Description", "Linked to"] if en
             else ["Datum", "Bedrag", "Omschrijving", "Gekoppeld aan"])]
    for r in rows:
        data.append([
            r["date"], eur(r["amount"]),
            (r["desc"] or "")[:48], (r["link_label"] or "—")[:40],
        ])
    if len(data) == 1:
        data.append(["—", "—", "No transactions" if en else "Geen transacties", "—"])

    table = Table(data, colWidths=[22 * mm, 28 * mm, 73 * mm, 47 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.25, MID_GREY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    if matched_only:
        story.append(Spacer(1, 6 * mm))
        in_lbl = "Total received (matched)" if en else "Totaal ontvangen (gekoppeld)"
        out_lbl = "Total spent (matched)" if en else "Totaal uitgegeven (gekoppeld)"
        out_amt = f"€ {abs(totals['out']):.2f}".replace(".", ",")
        story.append(Paragraph(f"{in_lbl}: {eur(totals['in']).replace('+ ', '')}", total_style))
        story.append(Paragraph(f"{out_lbl}: {out_amt}", total_style))

    story.append(Spacer(1, 10 * mm))
    gen_by = "Generated by BigDogg" if en else "Gegenereerd door BigDogg"
    story.append(Paragraph(
        f"{gen_by} · bigdogg.nl · {_dt.now().strftime('%d-%m-%Y')}",
        footer_style))

    doc.build(story)
    return buf.getvalue()


@router.get("/report")
async def banking_report(
    request: Request,
    matched_only: bool = Query(False),
    lang: str = Query("nl"),
):
    """Branded PDF of bank transactions and what each is linked to
    (invoice / expense / investment), built from the SAME data as the
    Transactions screen. Localised via `lang` (nl/en). With matched_only=true,
    unmatched and private rows are excluded — no personal transactions."""
    user_id = get_user_id(request)
    enriched, _ = await _enriched_transactions_for_user(user_id, 2000)
    rows, totals = _report_rows_from_enriched(enriched, matched_only, lang)

    profile = {}
    try:
        pr = supabase.table("user_profiles")\
            .select("business_name, full_name")\
            .eq("id", user_id).limit(1).execute()
        if pr.data:
            profile = pr.data[0]
    except Exception:
        pass

    pdf = _build_report_pdf(rows, totals, matched_only, profile, lang)
    if lang == "en":
        fname = "bigdogg-transactions-matched.pdf" if matched_only else "bigdogg-transactions.pdf"
    else:
        fname = "bigdogg-transacties-gekoppeld.pdf" if matched_only else "bigdogg-transacties.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.delete("/disconnect")
async def banking_disconnect(request: Request):
    """Revoke the TrueLayer connection and clear local state."""
    bigdogg_user_id = get_user_id(request)

    # Best-effort revoke at TrueLayer. Their /api/delete endpoint
    # invalidates the access token and the corresponding consent.
    profile_result = supabase.table("user_profiles")\
        .select("tl_access_token").eq("id", bigdogg_user_id).execute()
    access_token = (_decrypt_token(profile_result.data[0].get("tl_access_token"))
                    if profile_result.data else None)
    if access_token:
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                await client.post(
                    f"{_auth_base()}/api/delete",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except Exception as e:
            print(f"[truelayer] revoke failed (non-fatal): {e}")

    supabase.table("user_profiles").update({
        "tl_access_token": None,
        "tl_refresh_token": None,
        "tl_token_expires_at": None,
        "tl_connected_at": None,
        "tl_link_state": None,
        "tl_provider_id": None,
    }).eq("id", bigdogg_user_id).execute()
    return {"success": True}

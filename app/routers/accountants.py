"""Accountant portal — token-gated read-only access to one BigDogg user's
administration.

New simpler model: the token in the email link IS the credential. The
accountant does NOT create a BigDogg account; they just open the link
and see the data. Validity is 14 days; the owner can revoke or
regenerate the link.

Endpoints (all under /api/v1/accountants):

  Owner — auth required (Bearer access_token in Authorization):
    POST   /invite                      create a fresh access link
    GET    /invites                     list this owner's links
    DELETE /invites/{token}             revoke a single link
    POST   /invites/{token}/extend      bump expiry +14 days

  Accountant — public (token in URL path, no auth header needed):
    GET    /portal/{token}              meta: owner name, expiry
    GET    /portal/{token}/overview     yearly revenue / expense / BTW totals
    GET    /portal/{token}/invoices     list invoices
    GET    /portal/{token}/expenses     list expenses
    GET    /portal/{token}/invoices/{invoice_id}/pdf   download PDF
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, PlainTextResponse
from datetime import datetime, timezone, timedelta, date
from app.database import supabase
from app.config import settings
import resend
import csv
import io

router = APIRouter()
resend.api_key = settings.resend_api_key


# ─── Auth helpers ────────────────────────────────────────────
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


def _resolve_portal_token(token: str) -> dict:
    """Validate an accountant portal token and return its row. Raises:

      404 — token does not exist
      410 — token expired (Gone)
      403 — token revoked
    """
    result = supabase.table("accountant_invites")\
        .select("token, user_id, email, used, expires_at, created_at")\
        .eq("token", token).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="link_not_found")
    row = result.data[0]

    # `used=true` is repurposed for "revoked by owner" in this model.
    if row.get("used"):
        raise HTTPException(status_code=403, detail="link_revoked")

    expires_raw = row.get("expires_at")
    if expires_raw:
        try:
            exp = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) >= exp:
                raise HTTPException(status_code=410, detail="link_expired")
        except HTTPException:
            raise
        except Exception:
            pass
    return row


# ─── Owner: create / list / revoke / extend links ────────────
@router.post("/invite")
async def invite_accountant(request: Request):
    user_id = get_user_id(request)
    body = await request.json()
    email = (body or {}).get("email", "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="invalid_email")

    insert = supabase.table("accountant_invites").insert({
        "user_id": user_id,
        "email":   email,
        "used":    False,
    }).execute()
    if not insert.data:
        raise HTTPException(status_code=400, detail="invite_failed")

    token = insert.data[0]["token"]

    profile = supabase.table("user_profiles")\
        .select("business_name, full_name")\
        .eq("id", user_id).limit(1).execute()
    inviter = "Een BigDogg-gebruiker"
    if profile.data:
        p = profile.data[0]
        inviter = (p.get("business_name") or p.get("full_name") or inviter).strip()

    accept_url = f"{settings.share_link_origin}/a/{token}"

    email_sent = False
    email_error: str | None = None
    try:
        if not settings.resend_api_key:
            email_error = "resend_api_key_missing"
        else:
            subject = f"{inviter} geeft je toegang tot zijn BigDogg-boekhouding"
            html_body = _invite_email_html(
                inviter=inviter,
                recipient_email=email,
                accept_url=accept_url,
            )
            text_body = (
                f"Hallo,\n\n"
                f"{inviter} geeft je 14 dagen lang alleen-lezen toegang tot "
                f"zijn BigDogg-boekhouding — facturen, kosten en BTW-overzicht.\n\n"
                f"Open de portal: {accept_url}\n\n"
                f"Er is geen account nodig — open de link en je zit erin.\n\n"
                f"---\nDit bericht is verzonden via BigDogg · bigdogg.nl\n"
            )
            resend.Emails.send({
                "from": "BigDogg <info@bigdogg.nl>",
                "to":   [email],
                "subject": subject,
                "text": text_body,
                "html": html_body,
            })
            email_sent = True
    except Exception as e:
        email_error = str(e)
        print(f"[accountants] invite email failed: {e}")

    return {
        "success":     True,
        "token":       token,
        "accept_url":  accept_url,
        "email_sent":  email_sent,
        "email_error": email_error,
    }


def _invite_email_html(*, inviter: str, recipient_email: str, accept_url: str) -> str:
    safe_inviter = (
        inviter.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f"""<!DOCTYPE html>
<html lang="nl">
<body style="margin:0;padding:0;background:#F5F3EF;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1B3A4B;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F3EF;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;border:1px solid #E2DDD6;overflow:hidden;">
        <tr><td align="center" style="padding:28px 28px 4px 28px;background:#1B3A4B;">
          <img src="https://bigdogg.nl/icons/Icon-512.png" alt="BigDogg" width="64" height="64" style="display:block;border-radius:12px;"/>
          <h1 style="margin:12px 0 0 0;color:#C9A96E;font-size:22px;letter-spacing:-0.3px;font-weight:700;">BigDogg.</h1>
          <p style="margin:4px 0 16px 0;color:#F5F3EF;font-size:12px;letter-spacing:1px;text-transform:uppercase;">Accountantsportaal</p>
        </td></tr>
        <tr><td style="padding:28px 28px 8px 28px;">
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">Hallo,</p>
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">
            <strong style="color:#1B3A4B;">{safe_inviter}</strong> geeft je <strong>14 dagen</strong>
            alleen-lezen toegang tot zijn BigDogg-boekhouding.
          </p>
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">
            Klik op de knop om de portal te openen — geen account nodig, geen wachtwoord.
            Bekijk en download facturen, kosten en het BTW-overzicht.
          </p>
        </td></tr>
        <tr><td align="center" style="padding:8px 28px 4px 28px;">
          <a href="{accept_url}" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;margin:6px;">Portal openen</a>
        </td></tr>
        <tr><td align="center" style="padding:0 28px 24px 28px;">
          <p style="margin:12px 0 0 0;font-size:12px;color:#4A6572;">
            of plak deze link in je browser:<br>
            <a href="{accept_url}" style="color:#1B3A4B;word-break:break-all;">{accept_url}</a>
          </p>
        </td></tr>
        <tr><td style="padding:0 28px 24px 28px;border-top:1px solid #E2DDD6;">
          <p style="margin:16px 0 6px 0;font-size:13px;line-height:1.6;color:#4A6572;">
            <strong>Hoe werkt het?</strong><br>
            Open de link op je telefoon of desktop. De portal toont een leesbaar
            overzicht en je kunt PDF's van facturen downloaden. De link is 14
            dagen geldig en kan op elk moment door {safe_inviter} worden ingetrokken.
          </p>
          <p style="margin:16px 0 0 0;font-size:12px;line-height:1.6;color:#4A6572;">
            Heb je de link niet aangevraagd? Negeer deze e-mail.
          </p>
        </td></tr>
      </table>
      <p style="margin:16px 0 0 0;font-size:11px;color:#9CA3AF;">Verzonden via BigDogg · bigdogg.nl</p>
    </td></tr>
  </table>
</body>
</html>"""


@router.get("/invites")
async def list_invites(request: Request):
    user_id = get_user_id(request)
    result = supabase.table("accountant_invites")\
        .select("token, email, used, expires_at, created_at")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True).execute()
    return {"invites": result.data or []}


@router.delete("/invites/{token}")
async def cancel_invite(token: str, request: Request):
    """Revoke a link. Hard-delete the row so it disappears from the
    owner's Settings → My accountant list. Previously we soft-revoked
    via used=true, but the accountant_invites table only has SELECT/
    INSERT/DELETE RLS policies — UPDATE silently no-ops — so the row
    kept reappearing. Hard delete also matches user expectation: tap
    Revoke → it's gone."""
    user_id = get_user_id(request)
    try:
        result = supabase.table("accountant_invites").delete()\
            .eq("user_id", user_id).eq("token", token).execute()
    except Exception as e:
        print(f"[accountants] revoke failed for token={token}: {e}")
        raise HTTPException(status_code=400, detail="revoke_failed")
    deleted = len(result.data or [])
    if deleted == 0:
        # Either the token doesn't exist, or it belongs to a different
        # user. Don't 404 — the desired end state ("no longer in my
        # list") is already true.
        return {"success": True, "deleted": 0}
    return {"success": True, "deleted": deleted}


@router.post("/invites/{token}/extend")
async def extend_invite(token: str, request: Request):
    """Push expires_at out by another 14 days."""
    user_id = get_user_id(request)
    new_expiry = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    supabase.table("accountant_invites").update({
        "expires_at": new_expiry,
        "used": False,
    }).eq("user_id", user_id).eq("token", token).execute()
    return {"success": True, "expires_at": new_expiry}


# ─── Accountant portal — public, token-gated ─────────────────
@router.get("/portal/{token}")
async def portal_meta(token: str):
    """Public landing info — owner name, expiry, link status."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    inviter_name = ""
    business_name = ""
    kvk = ""
    btw = ""
    try:
        prof = supabase.table("user_profiles")\
            .select("business_name, full_name, kvk_number, btw_number")\
            .eq("id", owner_id).limit(1).execute()
        if prof.data:
            p = prof.data[0]
            business_name = (p.get("business_name") or "").strip()
            inviter_name = (
                business_name
                or (p.get("full_name") or "").strip()
                or "BigDogg-gebruiker"
            )
            kvk = (p.get("kvk_number") or "").strip()
            btw = (p.get("btw_number") or "").strip()
    except Exception:
        pass
    return {
        "owner_name":     inviter_name,
        "business_name":  business_name,
        "kvk_number":     kvk,
        "btw_number":     btw,
        "invite_email":   row.get("email"),
        "expires_at":     row.get("expires_at"),
        "created_at":     row.get("created_at"),
    }


_KOR_THRESHOLD = 20000.0
_URENCRITERIUM = 1225
_DEPRECIATION_THRESHOLD = 450.0


def _quarter_bounds(year: int):
    return [
        (1, f"{year}-01-01", f"{year}-03-31"),
        (2, f"{year}-04-01", f"{year}-06-30"),
        (3, f"{year}-07-01", f"{year}-09-30"),
        (4, f"{year}-10-01", f"{year}-12-31"),
    ]


def _resolve_year(year: int | None) -> tuple[int, str, str]:
    y = year or datetime.now().year
    return y, f"{y}-01-01", f"{y}-12-31"


def _depreciation_for_year(amount: float, purchase_date: str,
                            years: int, target_year: int) -> dict:
    """Returns {annual, this_year, cumulative_at_year_end, book_value_at_year_end}."""
    try:
        purchase_year = int((purchase_date or "")[:4] or 0)
    except Exception:
        purchase_year = target_year
    annual = round(amount / max(years, 1), 2)
    end_year = purchase_year + years - 1
    if target_year < purchase_year:
        return {"annual": annual, "this_year": 0.0,
                "cumulative": 0.0, "book_value": round(amount, 2)}
    if target_year > end_year:
        return {"annual": annual, "this_year": 0.0,
                "cumulative": round(amount, 2), "book_value": 0.0}
    years_so_far = target_year - purchase_year + 1
    cumulative = round(annual * years_so_far, 2)
    return {
        "annual":     annual,
        "this_year":  annual,
        "cumulative": cumulative,
        "book_value": round(max(amount - cumulative, 0.0), 2),
    }


@router.get("/portal/{token}/years")
async def portal_years(token: str):
    """Distinct years that contain any invoice or expense row, for the
    year-selector dropdown on the portal."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    inv = supabase.table("invoices")\
        .select("invoice_date").eq("user_id", owner_id).execute()
    exp = supabase.table("expenses")\
        .select("expense_date").eq("user_id", owner_id).execute()
    years: set[int] = set()
    for r in (inv.data or []):
        d = (r.get("invoice_date") or "")[:4]
        if d.isdigit():
            years.add(int(d))
    for r in (exp.data or []):
        d = (r.get("expense_date") or "")[:4]
        if d.isdigit():
            years.add(int(d))
    years.add(datetime.now().year)
    return {"years": sorted(years, reverse=True)}


@router.get("/portal/{token}/overview")
async def portal_overview(token: str, year: int | None = None):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    y, y_start, y_end = _resolve_year(year)

    inv = supabase.table("invoices")\
        .select("subtotal_ex_btw, total_incl_btw, btw_amount, status, invoice_date")\
        .eq("user_id", owner_id)\
        .gte("invoice_date", y_start).lte("invoice_date", y_end)\
        .neq("status", "draft").execute()
    exp = supabase.table("expenses")\
        .select("amount_ex_btw, btw_amount, category, expense_date")\
        .eq("user_id", owner_id)\
        .gte("expense_date", y_start).lte("expense_date", y_end).execute()

    rev_ex = round(sum(float(r.get("subtotal_ex_btw") or 0) for r in (inv.data or [])), 2)
    rev_incl = round(sum(float(r.get("total_incl_btw") or 0) for r in (inv.data or [])), 2)
    btw_collected = round(sum(float(r.get("btw_amount") or 0) for r in (inv.data or [])), 2)
    paid_count = sum(1 for r in (inv.data or []) if (r.get("status") or "").lower() == "paid")

    exp_ex = round(sum(float(r.get("amount_ex_btw") or 0) for r in (exp.data or [])), 2)
    btw_paid = round(sum(float(r.get("btw_amount") or 0) for r in (exp.data or [])), 2)
    exp_incl = round(exp_ex + btw_paid, 2)

    # Per-quarter (for BTW filings)
    quarters = []
    for q, q_start, q_end in _quarter_bounds(y):
        qi = [r for r in (inv.data or [])
              if q_start <= (r.get("invoice_date") or "") <= q_end]
        qe = [r for r in (exp.data or [])
              if q_start <= (r.get("expense_date") or "") <= q_end]
        q_rev_ex = round(sum(float(r.get("subtotal_ex_btw") or 0) for r in qi), 2)
        q_btw_c = round(sum(float(r.get("btw_amount") or 0) for r in qi), 2)
        q_exp_ex = round(sum(float(r.get("amount_ex_btw") or 0) for r in qe), 2)
        q_btw_p = round(sum(float(r.get("btw_amount") or 0) for r in qe), 2)
        quarters.append({
            "quarter":        q,
            "revenue_ex":     q_rev_ex,
            "btw_collected":  q_btw_c,
            "expense_ex":     q_exp_ex,
            "btw_paid":       q_btw_p,
            "btw_payable":    round(q_btw_c - q_btw_p, 2),
            "invoice_count":  len(qi),
        })

    # Expense categories
    cats: dict[str, dict] = {}
    for r in (exp.data or []):
        c = (r.get("category") or "general").strip() or "general"
        slot = cats.setdefault(c, {"category": c, "amount_ex": 0.0, "count": 0})
        slot["amount_ex"] += float(r.get("amount_ex_btw") or 0)
        slot["count"] += 1
    categories = sorted(
        ({"category": c["category"],
          "amount_ex": round(c["amount_ex"], 2),
          "count": c["count"]} for c in cats.values()),
        key=lambda r: r["amount_ex"], reverse=True,
    )

    return {
        "year":          y,
        "revenue_ex":    rev_ex,
        "revenue_incl":  rev_incl,
        "expense_ex":    exp_ex,
        "expense_incl":  exp_incl,
        "btw_collected": btw_collected,
        "btw_paid":      btw_paid,
        "btw_payable":   round(btw_collected - btw_paid, 2),
        "profit_ex":     round(rev_ex - exp_ex, 2),
        "invoice_count": len(inv.data or []),
        "paid_count":    paid_count,
        "expense_count": len(exp.data or []),
        "kor_threshold": _KOR_THRESHOLD,
        "kor_ratio":     round(min(rev_ex / _KOR_THRESHOLD, 1.0), 4) if _KOR_THRESHOLD else 0,
        "quarters":      quarters,
        "categories":    categories,
    }


@router.get("/portal/{token}/invoices")
async def portal_invoices(token: str, year: int | None = None):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    y, y_start, y_end = _resolve_year(year)

    rows = supabase.table("invoices")\
        .select("id, invoice_number, client_name, client_company, "
                "total_incl_btw, subtotal_ex_btw, btw_amount, "
                "invoice_date, due_date, status")\
        .eq("user_id", owner_id)\
        .gte("invoice_date", y_start).lte("invoice_date", y_end)\
        .order("invoice_date", desc=True).execute()

    invoices = rows.data or []
    if invoices:
        ids = [i["id"] for i in invoices if i.get("id")]
        lines = supabase.table("invoice_lines")\
            .select("invoice_id, description, quantity, unit_price_ex_btw, "
                    "btw_rate, line_total_ex_btw, unit")\
            .in_("invoice_id", ids).execute()
        by_id: dict[str, list] = {}
        for ln in (lines.data or []):
            by_id.setdefault(ln["invoice_id"], []).append(ln)
        for inv in invoices:
            inv["lines"] = by_id.get(inv["id"], [])

    return {"year": y, "invoices": invoices}


@router.get("/portal/{token}/expenses")
async def portal_expenses(token: str, year: int | None = None):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    y, y_start, y_end = _resolve_year(year)
    # NOTE: do not select payment_method — column does not exist on the
    # expenses table and including it causes postgrest to 500.
    rows = supabase.table("expenses")\
        .select("id, description, amount_ex_btw, btw_amount, btw_rate, "
                "category, expense_date, receipt_url")\
        .eq("user_id", owner_id)\
        .gte("expense_date", y_start).lte("expense_date", y_end)\
        .order("expense_date", desc=True).execute()
    out = []
    for r in (rows.data or []):
        ex = float(r.get("amount_ex_btw") or 0)
        btw = float(r.get("btw_amount") or 0)
        out.append({**r, "amount_incl_btw": round(ex + btw, 2)})
    return {"year": y, "expenses": out}


# ── BTW aangifte breakdown ──────────────────────────────────
def _btw_breakdown_for_year(owner_id: str, year: int) -> dict:
    """For the BTW aangifte card: per-quarter revenue split by rate
    (21% → 1a, 9% → 1b, 0% → 1c) and total voorbelasting (5b)."""
    y_start = f"{year}-01-01"
    y_end = f"{year}-12-31"

    inv = supabase.table("invoices")\
        .select("id, invoice_date, status")\
        .eq("user_id", owner_id)\
        .gte("invoice_date", y_start).lte("invoice_date", y_end)\
        .neq("status", "draft").execute()
    invoices = inv.data or []
    by_id = {i["id"]: i for i in invoices}

    lines: list[dict] = []
    if invoices:
        ln = supabase.table("invoice_lines")\
            .select("invoice_id, quantity, unit_price_ex_btw, "
                    "btw_rate, line_total_ex_btw")\
            .in_("invoice_id", [i["id"] for i in invoices]).execute()
        for line in (ln.data or []):
            inv_row = by_id.get(line["invoice_id"])
            if not inv_row:
                continue
            ex = float(line.get("line_total_ex_btw") or
                       (float(line.get("quantity") or 0) *
                        float(line.get("unit_price_ex_btw") or 0)))
            rate = int(line.get("btw_rate") or 0)
            btw = round(ex * rate / 100, 2)
            lines.append({
                "invoice_date": inv_row.get("invoice_date") or "",
                "ex":           ex,
                "btw":          btw,
                "rate":         rate,
            })

    exp = supabase.table("expenses")\
        .select("amount_ex_btw, btw_amount, expense_date")\
        .eq("user_id", owner_id)\
        .gte("expense_date", y_start).lte("expense_date", y_end).execute()
    expenses = exp.data or []

    def _bucket():
        return {
            "rate_21":      {"ex": 0.0, "btw": 0.0},
            "rate_9":       {"ex": 0.0, "btw": 0.0},
            "rate_0":       {"ex": 0.0, "btw": 0.0},
            "voorbelasting": 0.0,
        }

    quarters = {q: _bucket() for q in range(1, 5)}
    year_total = _bucket()

    for line in lines:
        d = line["invoice_date"]
        if not d:
            continue
        try:
            m = int(d[5:7])
        except Exception:
            continue
        q = (m - 1) // 3 + 1
        if line["rate"] == 21:
            key = "rate_21"
        elif line["rate"] == 9:
            key = "rate_9"
        elif line["rate"] == 0:
            key = "rate_0"
        else:
            continue
        quarters[q][key]["ex"] += line["ex"]
        quarters[q][key]["btw"] += line["btw"]
        year_total[key]["ex"] += line["ex"]
        year_total[key]["btw"] += line["btw"]

    for e in expenses:
        d = (e.get("expense_date") or "")
        if not d:
            continue
        try:
            m = int(d[5:7])
        except Exception:
            continue
        q = (m - 1) // 3 + 1
        btw = float(e.get("btw_amount") or 0)
        quarters[q]["voorbelasting"] += btw
        year_total["voorbelasting"] += btw

    def _finalize(b):
        b = {k: ({"ex": round(v["ex"], 2), "btw": round(v["btw"], 2)}
                  if isinstance(v, dict) else round(v, 2))
             for k, v in b.items()}
        total_btw_out = (b["rate_21"]["btw"] + b["rate_9"]["btw"]
                          + b["rate_0"]["btw"])
        b["btw_owed"] = round(total_btw_out, 2)
        b["btw_payable"] = round(total_btw_out - b["voorbelasting"], 2)
        return b

    return {
        "quarters": {str(q): _finalize(v) for q, v in quarters.items()},
        "year":     _finalize(year_total),
    }


@router.get("/portal/{token}/btw-breakdown")
async def portal_btw_breakdown(token: str, year: int | None = None):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    y, _, _ = _resolve_year(year)
    return {"year": y, **_btw_breakdown_for_year(owner_id, y)}


# ── Debiteuren aging ────────────────────────────────────────
@router.get("/portal/{token}/aging")
async def portal_aging(token: str):
    """Aging buckets of outstanding (non-paid) invoices, based on due_date
    relative to today. Returns 4 buckets + a totals/items rollup."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]

    inv = supabase.table("invoices")\
        .select("id, invoice_number, client_name, client_company, "
                "invoice_date, due_date, total_incl_btw, status")\
        .eq("user_id", owner_id)\
        .neq("status", "paid").neq("status", "draft").execute()

    today = date.today()
    buckets = {
        "0-30":  {"label": "0–30 dagen",  "total": 0.0, "count": 0, "items": []},
        "31-60": {"label": "31–60 dagen", "total": 0.0, "count": 0, "items": []},
        "61-90": {"label": "61–90 dagen", "total": 0.0, "count": 0, "items": []},
        "90+":   {"label": "90+ dagen",   "total": 0.0, "count": 0, "items": []},
    }
    grand_total = 0.0
    grand_count = 0

    for r in (inv.data or []):
        due_raw = r.get("due_date") or ""
        if not due_raw:
            continue
        try:
            due = datetime.fromisoformat(due_raw[:10]).date()
        except Exception:
            continue
        days_overdue = (today - due).days
        if days_overdue < 0:
            continue  # not yet due — not "aging"
        if days_overdue <= 30:
            key = "0-30"
        elif days_overdue <= 60:
            key = "31-60"
        elif days_overdue <= 90:
            key = "61-90"
        else:
            key = "90+"
        amount = float(r.get("total_incl_btw") or 0)
        item = {
            "id":             r["id"],
            "invoice_number": r.get("invoice_number"),
            "client":         (r.get("client_name") or
                                r.get("client_company") or "—"),
            "invoice_date":   r.get("invoice_date"),
            "due_date":       due_raw,
            "days_overdue":   days_overdue,
            "amount":         amount,
        }
        buckets[key]["items"].append(item)
        buckets[key]["total"] += amount
        buckets[key]["count"] += 1
        grand_total += amount
        grand_count += 1

    for v in buckets.values():
        v["total"] = round(v["total"], 2)
        v["items"].sort(key=lambda i: i["days_overdue"], reverse=True)

    return {
        "today":           today.isoformat(),
        "grand_total":     round(grand_total, 2),
        "grand_count":     grand_count,
        "buckets":         buckets,
        "buckets_order":   ["0-30", "31-60", "61-90", "90+"],
    }


def _depreciation_schedule(amount: float, purchase_date: str,
                            years: int) -> list[dict]:
    """Full year-by-year schedule for one asset."""
    try:
        purchase_year = int((purchase_date or "")[:4] or 0)
    except Exception:
        purchase_year = datetime.now().year
    if years < 1:
        years = 1
    annual = round(amount / years, 2)
    schedule = []
    cumulative = 0.0
    for i in range(years):
        year = purchase_year + i
        cumulative = round(cumulative + annual, 2)
        # On the last year, absorb any rounding drift into the last row
        if i == years - 1:
            cumulative = round(amount, 2)
            this_year = round(amount - sum(s["amount"] for s in schedule), 2)
        else:
            this_year = annual
        book_value = round(max(amount - cumulative, 0.0), 2)
        schedule.append({
            "year":       year,
            "amount":     this_year,
            "cumulative": cumulative,
            "book_value": book_value,
        })
    return schedule


@router.get("/portal/{token}/investments")
async def portal_investments(token: str, year: int | None = None):
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    y, _, _ = _resolve_year(year)

    rows = supabase.table("investments")\
        .select("id, description, purchase_date, amount, "
                "depreciation_years, category, receipt_url")\
        .eq("user_id", owner_id)\
        .order("purchase_date", desc=True).execute()

    items = []
    total_this_year = 0.0
    for r in (rows.data or []):
        amount = float(r.get("amount") or 0)
        years = int(r.get("depreciation_years") or 5)
        purchase = r.get("purchase_date") or ""
        dep = _depreciation_for_year(amount, purchase, years, y)
        schedule = _depreciation_schedule(amount, purchase, years)
        total_this_year += dep["this_year"]
        items.append({
            **r,
            "annual_depreciation":     dep["annual"],
            "this_year_depreciation":  dep["this_year"],
            "cumulative_depreciation": dep["cumulative"],
            "book_value":              dep["book_value"],
            "schedule":                schedule,
        })
    return {
        "year":                 y,
        "investments":          items,
        "total_this_year":      round(total_this_year, 2),
        "depreciation_threshold": _DEPRECIATION_THRESHOLD,
    }


# ── CSV export ──────────────────────────────────────────────
# Default grootboekrekening mapping. Accountants can re-map in their own
# software; this just gives them a populated column to start from.
_LEDGER_INVOICES = {
    21: "8000",  # Omzet 21%
    9:  "8001",  # Omzet 9%
    0:  "8002",  # Omzet 0% / vrijgesteld
}
_LEDGER_EXPENSES = {
    "travel":    "4350",
    "materials": "4400",
    "software":  "4410",
    "food":      "4360",
    "office":    "4500",
    "general":   "4900",
    "other":     "4900",
}


@router.get("/portal/{token}/export.csv")
async def portal_export_csv(token: str, year: int | None = None):
    """CSV dump combining invoice lines + expenses for the year. Columns
    match what accountants typically import into Exact/AFAS/Twinfield."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    y, y_start, y_end = _resolve_year(year)

    inv = supabase.table("invoices")\
        .select("id, invoice_number, invoice_date, status, client_name, client_company")\
        .eq("user_id", owner_id)\
        .gte("invoice_date", y_start).lte("invoice_date", y_end)\
        .neq("status", "draft").execute()
    invoices = inv.data or []
    by_id = {i["id"]: i for i in invoices}

    lines = []
    if invoices:
        ln = supabase.table("invoice_lines")\
            .select("invoice_id, description, quantity, unit_price_ex_btw, "
                    "btw_rate, line_total_ex_btw")\
            .in_("invoice_id", [i["id"] for i in invoices]).execute()
        lines = ln.data or []

    exp = supabase.table("expenses")\
        .select("expense_date, description, amount_ex_btw, btw_amount, btw_rate, category")\
        .eq("user_id", owner_id)\
        .gte("expense_date", y_start).lte("expense_date", y_end)\
        .order("expense_date", desc=False).execute()
    expenses = exp.data or []

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow([
        "Type", "Datum", "Factuurnummer", "Relatie", "Omschrijving",
        "Bedrag excl. BTW", "BTW%", "BTW bedrag", "Bedrag incl. BTW",
        "Grootboekrekening",
    ])

    # Invoice line items as revenue
    for line in lines:
        inv_row = by_id.get(line["invoice_id"]) or {}
        ex = float(line.get("line_total_ex_btw") or
                   (float(line.get("quantity") or 0) *
                    float(line.get("unit_price_ex_btw") or 0)))
        rate = int(line.get("btw_rate") or 0)
        btw = round(ex * rate / 100, 2)
        incl = round(ex + btw, 2)
        client = (inv_row.get("client_name")
                  or inv_row.get("client_company") or "")
        writer.writerow([
            "Verkoop",
            inv_row.get("invoice_date") or "",
            inv_row.get("invoice_number") or "",
            client,
            line.get("description") or "",
            f"{ex:.2f}".replace(".", ","),
            f"{rate}%",
            f"{btw:.2f}".replace(".", ","),
            f"{incl:.2f}".replace(".", ","),
            _LEDGER_INVOICES.get(rate, "8000"),
        ])

    # Expenses as costs
    for e in expenses:
        ex = float(e.get("amount_ex_btw") or 0)
        btw = float(e.get("btw_amount") or 0)
        rate = int(e.get("btw_rate") or 0)
        cat = (e.get("category") or "general").strip() or "general"
        writer.writerow([
            "Inkoop",
            e.get("expense_date") or "",
            "",
            "",
            e.get("description") or "",
            f"{ex:.2f}".replace(".", ","),
            f"{rate}%",
            f"{btw:.2f}".replace(".", ","),
            f"{ex + btw:.2f}".replace(".", ","),
            _LEDGER_EXPENSES.get(cat.lower(), "4900"),
        ])

    return PlainTextResponse(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=bigdogg-export-{y}.csv",
        },
    )


_HOURS_PER_DAY = 9.0


def _invoice_derived_hours(owner_id: str, y_start: str, y_end: str) -> tuple[float, list[dict]]:
    """Same logic as the user-facing /api/v1/hours endpoint:
    invoice_lines with unit='day' count as quantity*9 hours, unit='hour'
    as quantity*1 hour. Anything else (fixed, piece, km) yields 0.

    Returning both the total and a per-line breakdown so the portal can
    surface it alongside manually-logged hours.
    """
    try:
        inv = supabase.table("invoices")\
            .select("id, invoice_date, invoice_number, project_id, status")\
            .eq("user_id", owner_id)\
            .neq("status", "draft")\
            .gte("invoice_date", y_start).lte("invoice_date", y_end)\
            .execute()
        invoices = inv.data or []
        if not invoices:
            return 0.0, []
        inv_map = {i["id"]: i for i in invoices}
        ln = supabase.table("invoice_lines")\
            .select("invoice_id, description, quantity, unit, product_id")\
            .in_("invoice_id", [i["id"] for i in invoices]).execute()

        # Lookup maps: product_id → unit (firmest), name → unit (legacy
        # fallback for lines without product_id). Same resolution order
        # as /api/v1/hours so the accountant sees identical numbers.
        product_unit_by_id: dict[str, str] = {}
        product_unit_by_name: dict[str, str] = {}
        try:
            prod = supabase.table("products")\
                .select("id, name, unit").eq("user_id", owner_id).execute()
            for p in (prod.data or []):
                pid = (p.get("id") or "").strip()
                name = (p.get("name") or "").strip().lower()
                u = (p.get("unit") or "").strip().lower()
                if not u:
                    continue
                if pid:
                    product_unit_by_id[pid] = u
                if name:
                    product_unit_by_name[name] = u
        except Exception as e:
            print(f"[accountants] product unit map load failed: {e}")

        total = 0.0
        breakdown: list[dict] = []
        for line in (ln.data or []):
            raw_unit = (line.get("unit") or "fixed").lower()
            description = line.get("description", "") or ""
            product_id = line.get("product_id")

            unit = None
            if product_id and product_id in product_unit_by_id:
                unit = product_unit_by_id[product_id]
            if unit is None and product_unit_by_name:
                desc_lower = description.lower().strip()
                if desc_lower in product_unit_by_name:
                    unit = product_unit_by_name[desc_lower]
                else:
                    for name in sorted(product_unit_by_name.keys(), key=len, reverse=True):
                        if name and name in desc_lower:
                            unit = product_unit_by_name[name]
                            break
            if unit is None:
                unit = raw_unit
            qty = float(line.get("quantity") or 0)
            if unit == "day":
                hrs = qty * _HOURS_PER_DAY
            elif unit == "hour":
                hrs = qty
            else:
                continue
            if hrs <= 0:
                continue
            total += hrs
            inv_row = inv_map.get(line["invoice_id"], {})
            breakdown.append({
                "source":         "invoice",
                "invoice_number": inv_row.get("invoice_number", ""),
                "invoice_id":     line["invoice_id"],
                "project_id":     inv_row.get("project_id"),
                "description":    description,
                "quantity":       qty,
                "unit":           unit,
                "hours":          round(hrs, 2),
                "date":           inv_row.get("invoice_date", ""),
            })
        return round(total, 2), breakdown
    except Exception as e:
        print(f"[accountants] _invoice_derived_hours failed: {e}")
        return 0.0, []


@router.get("/portal/{token}/hours")
async def portal_hours(token: str, year: int | None = None):
    """Total hours for the year — matches the user's own /api/v1/hours
    screen exactly (manual entries + invoice-derived: day*9, hour*1).
    Also returns a per-month breakdown for the table the portal renders."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]
    y, y_start, y_end = _resolve_year(year)

    rows = supabase.table("hours")\
        .select("id, hours, date, description, project_id")\
        .eq("user_id", owner_id)\
        .gte("date", y_start).lte("date", y_end)\
        .order("date", desc=True).execute()
    manual_entries = rows.data or []

    # Invoice-derived hours (parity with /api/v1/hours)
    invoice_hours, invoice_breakdown = _invoice_derived_hours(
        owner_id, y_start, y_end,
    )

    # Look up project names for both manual entries AND invoice-derived
    # rows. Without including the invoice side, hours attached to a
    # project_id via an invoice would render as "Onbekend project".
    project_ids = list({
        *(r.get("project_id") for r in manual_entries if r.get("project_id")),
        *(ib.get("project_id") for ib in invoice_breakdown if ib.get("project_id")),
    })
    project_names: dict[str, str] = {}
    if project_ids:
        try:
            p = supabase.table("projects")\
                .select("id, name").in_("id", project_ids).execute()
            for r in (p.data or []):
                project_names[r["id"]] = r.get("name") or ""
        except Exception:
            pass

    # Per-project totals — include invoice-derived rows that have a
    # project_id attached at the invoice level. Hours without a project
    # roll up under the "Geen project" bucket.
    by_project: dict[str, float] = {}
    manual_total = 0.0
    for r in manual_entries:
        h = float(r.get("hours") or 0)
        manual_total += h
        pid = r.get("project_id") or "_none"
        by_project[pid] = by_project.get(pid, 0.0) + h
    for ib in invoice_breakdown:
        pid = ib.get("project_id") or "_none"
        by_project[pid] = by_project.get(pid, 0.0) + ib["hours"]

    project_summary = [
        {
            "project_id":   None if pid == "_none" else pid,
            "project_name": "Geen project" if pid == "_none"
                            else (project_names.get(pid, "Onbekend project")),
            "hours":        round(h, 2),
        }
        for pid, h in sorted(by_project.items(), key=lambda kv: kv[1], reverse=True)
    ]

    # Per-month breakdown for the table on the Uren tab.
    monthly_manual = [0.0] * 12
    monthly_invoice = [0.0] * 12
    for r in manual_entries:
        d = (r.get("date") or "")
        try:
            m = int(d[5:7])
            if 1 <= m <= 12:
                monthly_manual[m - 1] += float(r.get("hours") or 0)
        except Exception:
            continue
    for ib in invoice_breakdown:
        d = ib.get("date") or ""
        try:
            m = int(d[5:7])
            if 1 <= m <= 12:
                monthly_invoice[m - 1] += ib["hours"]
        except Exception:
            continue
    monthly = [
        {
            "month":         i + 1,
            "manual_hours":  round(monthly_manual[i], 2),
            "invoice_hours": round(monthly_invoice[i], 2),
            "total_hours":   round(monthly_manual[i] + monthly_invoice[i], 2),
        }
        for i in range(12)
    ]

    total_hours = round(manual_total + invoice_hours, 2)

    return {
        "year":                  y,
        "entries":               manual_entries,
        "invoice_breakdown":     invoice_breakdown,
        "project_summary":       project_summary,
        "monthly":               monthly,
        "manual_hours":          round(manual_total, 2),
        "invoice_hours":         round(invoice_hours, 2),
        "total_hours":           total_hours,
        "urencriterium":         _URENCRITERIUM,
        "urencriterium_met":     total_hours >= _URENCRITERIUM,
        "urencriterium_ratio":   round(min(total_hours / _URENCRITERIUM, 1.0), 4),
    }


@router.get("/portal/{token}/annual-report.pdf")
async def portal_annual_report_pdf(
    token: str,
    year: int | None = None,
    lang: str = "nl",
):
    """The same annual PDF the user themselves can download — including
    the AI-generated tax tips. Reuses `get_year_data` + `get_ai_tax_tips`
    + `_generate_annual_pdf` from the annual_report router; no logic
    duplication. The accountant token authorises access for the owner;
    `require_active_paid` is enforced identically to the user-facing
    endpoint so free-tier owners can't grant their accountant the PDF
    either."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]

    # Import lazily to avoid a circular import at module load time.
    from app.routers.annual_report import (
        get_year_data, get_ai_tax_tips, _generate_annual_pdf,
    )
    from app.routers.subscription import require_active_paid

    require_active_paid(owner_id)

    y = year or (datetime.now().year - 1)

    profile_result = supabase.table("user_profiles")\
        .select("*").eq("id", owner_id).execute()
    profile = profile_result.data[0] if profile_result.data else {}

    data_current = get_year_data(owner_id, y)
    data_prev = get_year_data(owner_id, y - 1)

    if lang == "en":
        fallback_tips = (
            "1. Check if you qualify for the self-employed deduction (zelfstandigenaftrek).\n"
            "2. Apply the SME profit exemption (MKB-winstvrijstelling).\n"
            "3. Review all business costs for deductibility.\n"
            "4. Consider a pension reserve (FOR) to reduce taxable profit.\n"
            "5. Ensure all invoices are in your administration."
        )
    else:
        fallback_tips = (
            "1. Controleer of je in aanmerking komt voor de zelfstandigenaftrek.\n"
            "2. Pas de MKB-winstvrijstelling toe op je winst.\n"
            "3. Bekijk alle zakelijke kosten op aftrekbaarheid.\n"
            "4. Overweeg een fiscale oudedagsreserve (FOR) om belastbare winst te verlagen.\n"
            "5. Zorg dat alle facturen in je administratie zitten."
        )
    import asyncio
    try:
        tax_tips = await asyncio.wait_for(
            get_ai_tax_tips(data_current, data_prev, profile, lang),
            timeout=25.0,
        )
    except Exception:
        tax_tips = fallback_tips

    pdf_bytes = _generate_annual_pdf(
        data_current, data_prev, profile, tax_tips, lang,
    )

    # Filename: BigDogg_Jaarrapport_<KvK or business slug>_<year>.pdf
    kvk = (profile.get("kvk_number") or "").strip()
    business = (
        profile.get("business_name")
        or profile.get("full_name")
        or "client"
    ).strip()
    base = kvk if kvk else business
    safe = "".join(
        c if c.isalnum() or c in ("-", "_") else "-" for c in base
    )[:48].strip("-") or "client"
    filename = f"BigDogg_Jaarrapport_{safe}_{y}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/portal/{token}/invoices/{invoice_id}/pdf")
async def portal_invoice_pdf(token: str, invoice_id: str):
    """Generate the invoice PDF on demand, scoped to the link's owner."""
    row = _resolve_portal_token(token)
    owner_id = row["user_id"]

    invoice_result = supabase.table("invoices")\
        .select("*, clients(*)")\
        .eq("id", invoice_id)\
        .eq("user_id", owner_id)\
        .single().execute()
    if not invoice_result.data:
        raise HTTPException(status_code=404, detail="invoice_not_found")

    lines_result = supabase.table("invoice_lines")\
        .select("*").eq("invoice_id", invoice_id).execute()

    profile_result = supabase.table("user_profiles")\
        .select("*").eq("id", owner_id).execute()

    invoice = invoice_result.data
    lines = lines_result.data
    profile = profile_result.data[0] if profile_result.data else {}
    client = invoice.get("clients") or {
        "contact_name":  invoice.get("client_name", ""),
        "email":         invoice.get("client_email", ""),
        "company_name":  invoice.get("client_company", ""),
    }

    # Re-use the same PDF generator the owner-facing endpoint uses.
    from app.routers.pdf import _generate_pdf
    sender_email = ""
    try:
        owner_email = supabase.auth.admin.get_user_by_id(owner_id)
        sender_email = (owner_email.user.email or "")
    except Exception:
        pass

    pdf_bytes = _generate_pdf(invoice, lines, profile, client, sender_email)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename={invoice['invoice_number']}.pdf"
        },
    )

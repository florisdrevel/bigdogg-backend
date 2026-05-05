"""Public short-URL handler for share links (client onboarding,
quotes, etc).

Why this exists: the BigDogg frontend is a Flutter SPA whose meta
tags are baked into the static index.html. WhatsApp / Facebook /
Slack scrape pages WITHOUT executing JavaScript, so any link to
`bigdogg.nl/#/onboard/<token>` shows the generic landing-page
preview. Bad UX for invitations.

This module serves a tiny HTML stub at `/o/<token>` (and friends)
with:

  * Personalized OpenGraph + Twitter Card tags so the link preview
    reads "Floris Drevel nodigt je uit op BigDogg" rather than the
    generic homepage blurb.
  * `<meta http-equiv="refresh">` AND a JS redirect, so a human
    clicking the link is bounced into the SPA at the actual
    onboarding screen within <1 second.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.database import supabase

router = APIRouter()


SPA_ORIGIN = "https://bigdogg.nl"
LOGO_URL = "https://bigdogg.nl/icons/Icon-512.png"


def _esc(value: str) -> str:
    """Minimal HTML attribute/text escape for OG tag values."""
    return (
        value.replace("&", "&amp;")
             .replace('"', "&quot;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
    )


def _render(*, title: str, description: str, redirect_to: str) -> str:
    safe_title = _esc(title)
    safe_desc = _esc(description)
    safe_redirect = _esc(redirect_to)
    return f"""<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{safe_title}</title>
  <meta name="description" content="{safe_desc}"/>

  <meta property="og:type" content="website"/>
  <meta property="og:title" content="{safe_title}"/>
  <meta property="og:description" content="{safe_desc}"/>
  <meta property="og:image" content="{LOGO_URL}"/>
  <meta property="og:url" content="{safe_redirect}"/>

  <meta name="twitter:card" content="summary_large_image"/>
  <meta name="twitter:title" content="{safe_title}"/>
  <meta name="twitter:description" content="{safe_desc}"/>
  <meta name="twitter:image" content="{LOGO_URL}"/>

  <meta http-equiv="refresh" content="0; url={safe_redirect}"/>
  <script>window.location.replace("{safe_redirect}");</script>
  <style>
    html,body{{margin:0;padding:0;background:#F5F3EF;font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#1B3A4B;}}
    .wrap{{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;text-align:center;padding:24px;}}
    h1{{font-size:20px;margin:16px 0 6px 0;}}
    p{{font-size:14px;color:#4A6572;margin:0;}}
    a{{color:#1B3A4B;font-weight:600;text-decoration:underline;}}
  </style>
</head>
<body>
  <div class="wrap">
    <img src="{LOGO_URL}" alt="BigDogg" width="96" height="96"/>
    <h1>{safe_title}</h1>
    <p>{safe_desc}</p>
    <p style="margin-top:16px"><a href="{safe_redirect}">Doorgaan &rarr;</a></p>
  </div>
</body>
</html>"""


@router.get("/o/{token}", response_class=HTMLResponse)
async def onboard_link(token: str, request: Request):
    """Personalized onboarding-link preview that redirects into the SPA."""
    title = "Je bent uitgenodigd op BigDogg"
    description = "Vul kort je bedrijfs- en factuurgegevens in zodat we facturen naar je kunnen versturen."
    try:
        invite = supabase.table("client_invites")\
            .select("user_id, used")\
            .eq("token", token).limit(1).execute()
        if invite.data:
            row = invite.data[0]
            inviter_id = row.get("user_id")
            if inviter_id:
                profile = supabase.table("user_profiles")\
                    .select("business_name, full_name")\
                    .eq("id", inviter_id).limit(1).execute()
                if profile.data:
                    p = profile.data[0]
                    inviter_name = (p.get("business_name") or p.get("full_name") or "").strip()
                    if inviter_name:
                        title = f"{inviter_name} nodigt je uit op BigDogg"
                        description = (
                            f"Klik om je in te schrijven als klant van {inviter_name}. "
                            "BigDogg gebruikt je gegevens alleen om correcte facturen op te stellen."
                        )
            if row.get("used"):
                title = "Deze uitnodiging is al gebruikt"
                description = "Je hoeft niets meer te doen — de uitnodiging is al voltooid."
    except Exception as e:
        print(f"[share] onboard preview lookup failed: {e}")

    redirect_to = f"{SPA_ORIGIN}/#/onboard/{token}"
    return HTMLResponse(content=_render(
        title=title, description=description, redirect_to=redirect_to,
    ))


@router.get("/a/{token}", response_class=HTMLResponse)
async def accountant_invite_link(token: str, request: Request):
    """Personalized accountant-invite preview that redirects into the
    SPA where the accountant can log in and accept."""
    title = "Je bent uitgenodigd als accountant"
    description = "Klik om in te loggen en de boekhouding van je klant in te zien (alleen-lezen)."
    try:
        invite = supabase.table("accountant_invites")\
            .select("user_id, used")\
            .eq("token", token).limit(1).execute()
        if invite.data:
            row = invite.data[0]
            owner_id = row.get("user_id")
            if owner_id:
                profile = supabase.table("user_profiles")\
                    .select("business_name, full_name")\
                    .eq("id", owner_id).limit(1).execute()
                if profile.data:
                    p = profile.data[0]
                    owner_name = (p.get("business_name") or p.get("full_name") or "").strip()
                    if owner_name:
                        title = f"{owner_name} nodigt je uit als accountant"
                        description = (
                            f"Je krijgt alleen-lezen toegang tot de boekhouding van {owner_name}. "
                            "Log in op BigDogg om de uitnodiging te accepteren."
                        )
            if row.get("used"):
                title = "Deze uitnodiging is al gebruikt"
                description = "De uitnodiging is al geaccepteerd."
    except Exception as e:
        print(f"[share] accountant preview lookup failed: {e}")

    redirect_to = f"{SPA_ORIGIN}/#/accountant/accept/{token}"
    return HTMLResponse(content=_render(
        title=title, description=description, redirect_to=redirect_to,
    ))


@router.get("/q/{token}", response_class=HTMLResponse)
async def quote_link(token: str, request: Request):
    """Personalized quote-link preview (the green Accepteer offerte
    flow). Same shape as the onboarding stub."""
    title = "Offerte van een BigDogg-gebruiker"
    description = "Bekijk en accepteer de offerte met één klik."
    try:
        quote = supabase.table("quotes")\
            .select("user_id, quote_number, total_incl_btw, status")\
            .eq("share_token", token).limit(1).execute()
        if quote.data:
            row = quote.data[0]
            inviter_id = row.get("user_id")
            quote_num = row.get("quote_number") or "Offerte"
            total = row.get("total_incl_btw")
            status = (row.get("status") or "").lower()
            inviter_name = ""
            if inviter_id:
                profile = supabase.table("user_profiles")\
                    .select("business_name, full_name")\
                    .eq("id", inviter_id).limit(1).execute()
                if profile.data:
                    p = profile.data[0]
                    inviter_name = (p.get("business_name") or p.get("full_name") or "").strip()
            who = inviter_name or "Een BigDogg-gebruiker"
            title = f"Offerte {quote_num} van {who}"
            if total is not None:
                description = f"Totaal € {float(total):.2f} — bekijk en accepteer met één klik."
            else:
                description = "Bekijk en accepteer met één klik."
            if status in ("accepted", "declined", "converted"):
                description = "Deze offerte is al verwerkt — je hoeft niets meer te doen."
    except Exception as e:
        print(f"[share] quote preview lookup failed: {e}")

    redirect_to = f"{SPA_ORIGIN}/#/q/{token}"
    return HTMLResponse(content=_render(
        title=title, description=description, redirect_to=redirect_to,
    ))

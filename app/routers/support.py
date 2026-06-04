from fastapi import APIRouter, HTTPException, Body, Request
from app.config import settings
from app.services.rate_limit import SlidingWindowLimiter, client_ip
import os
import resend
import html
import traceback

router = APIRouter()
resend.api_key = settings.resend_api_key

# Finding #11: /support is public and sends email — cap it per IP so it
# can't be turned into an email-bomb relay. 5 messages / 10 minutes is
# generous for a real user, hostile to a script.
_support_limiter = SlidingWindowLimiter(max_hits=5, window_seconds=600)

# Default to info@bigdogg.nl, but let the operator override via env var.
# Comma-separated list also supported, e.g. "info@bigdogg.nl,founder@gmail.com".
_DEFAULT_SUPPORT_INBOX = "info@bigdogg.nl"


def _support_recipients() -> list[str]:
    raw = os.getenv("SUPPORT_INBOX", _DEFAULT_SUPPORT_INBOX)
    parts = [e.strip() for e in raw.split(",") if e.strip()]
    return parts or [_DEFAULT_SUPPORT_INBOX]


@router.post("")
async def submit_support(request: Request, payload: dict = Body(...)):
    _support_limiter.check(client_ip(request))

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    message = (payload.get("message") or "").strip()
    preferred_contact = (payload.get("preferred_contact") or "email").strip().lower()

    if not name or not email or not message:
        raise HTTPException(
            status_code=400, detail="name, email and message are required"
        )
    if "@" not in email or "." not in email or len(email) < 5 or len(email) > 200:
        raise HTTPException(status_code=400, detail="invalid email")
    if len(name) > 200:
        raise HTTPException(status_code=400, detail="name too long")
    if len(message) > 5000:
        raise HTTPException(status_code=400, detail="message too long")

    contact_label = (
        "Video call" if preferred_contact == "video" else "Email"
    )

    safe_name = html.escape(name)
    safe_email = html.escape(email)
    safe_message = html.escape(message)

    subject = f"Support — {name} ({contact_label})"
    text_body = (
        f"New support request via bigdogg.nl\n\n"
        f"From: {name} <{email}>\n"
        f"Preferred contact: {contact_label}\n\n"
        f"Message:\n{message}\n\n"
        f"---\n"
        f"Reply directly to this email to respond to the customer.\n"
    )
    html_body = (
        f"<h2>New support request</h2>"
        f"<p><strong>From:</strong> {safe_name} &lt;<a href=\"mailto:{safe_email}\">{safe_email}</a>&gt;</p>"
        f"<p><strong>Preferred contact:</strong> {contact_label}</p>"
        f"<h3>Message</h3>"
        f"<p style=\"white-space:pre-wrap\">{safe_message}</p>"
        f"<hr><p><small>Reply directly to this email to respond to the customer.</small></p>"
    )

    recipients = _support_recipients()
    try:
        result = resend.Emails.send(
            {
                "from": "BigDogg Support <info@bigdogg.nl>",
                "to": recipients,
                "reply_to": email,
                "subject": subject,
                "text": text_body,
                "html": html_body,
            }
        )
        # Log so we can confirm delivery via Railway logs.
        print(
            f"[support] sent to={recipients} reply_to={email} "
            f"resend_id={result.get('id') if isinstance(result, dict) else result}"
        )
        return {"success": True, "to": recipients}
    except Exception as e:
        print(f"[support] error: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Could not send message: {e}")

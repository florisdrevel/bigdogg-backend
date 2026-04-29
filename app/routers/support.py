from fastapi import APIRouter, HTTPException, Body
from app.config import settings
import resend
import html

router = APIRouter()
resend.api_key = settings.resend_api_key


@router.post("")
async def submit_support(payload: dict = Body(...)):
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

    try:
        resend.Emails.send(
            {
                "from": "BigDogg Support <info@bigdogg.nl>",
                "to": ["info@bigdogg.nl"],
                "reply_to": email,
                "subject": subject,
                "text": text_body,
                "html": html_body,
            }
        )
        return {"success": True}
    except Exception as e:
        print(f"Support email error: {e}")
        raise HTTPException(status_code=500, detail="Could not send message")

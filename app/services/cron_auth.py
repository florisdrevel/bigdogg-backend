"""Constant-time x-cron-secret check for cron-protected routes.

`!=` comparison leaks the secret one byte at a time to an attacker who
can measure response time precisely. `hmac.compare_digest` is the
standard fix — runs in constant time regardless of where the mismatch
falls.
"""
import hmac
from fastapi import HTTPException, Request
from app.config import settings


def require_cron_secret(request: Request) -> None:
    """Raise 401 if the x-cron-secret header doesn't match the configured
    secret. Constant-time compare. Refuses to authorize if the secret is
    unset or still set to the legacy hard-coded default — fail-closed
    on misconfiguration is safer than fail-open.
    """
    configured = (settings.cron_secret or "").strip()
    if not configured or configured == "bigdogg-cron-2026":
        # The literal default was leaked in git history and must never
        # be honored. Refuse to authorize any request so a forgotten env
        # var doesn't leave a wide-open backdoor.
        raise HTTPException(
            status_code=503, detail="cron_secret_not_configured",
        )
    supplied = request.headers.get("x-cron-secret", "")
    if not hmac.compare_digest(supplied.encode("utf-8"), configured.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Unauthorized")

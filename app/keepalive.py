"""Railway keepalive — pings /health every 10 minutes so the free-tier
container never spins down to cold-start latency.

Started from the FastAPI lifespan in main.py; shut down cleanly when
the app exits.
"""
import logging
import os

import httpx
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings

logger = logging.getLogger(__name__)


def _resolve_app_url() -> str:
    """Where to ping. Railway injects RAILWAY_PUBLIC_DOMAIN as the
    hostname only (no scheme); fall back to the share-link origin which
    we already keep in settings for share URLs.
    """
    railway_domain = (os.getenv("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if railway_domain:
        # Railway only gives the bare hostname, not a full URL.
        if railway_domain.startswith("http"):
            return railway_domain.rstrip("/")
        return f"https://{railway_domain}".rstrip("/")
    return settings.share_link_origin.rstrip("/")


def _ping_health(url: str) -> None:
    try:
        resp = httpx.get(f"{url}/health", timeout=10)
        logger.info("keepalive ping %s/health → %s", url, resp.status_code)
    except Exception as exc:  # noqa: BLE001 — never let the scheduler die
        logger.warning("keepalive ping failed: %s", exc)


def start_keepalive() -> BackgroundScheduler:
    """Construct and start the scheduler. Caller is responsible for
    holding the returned reference (we attach it to FastAPI app.state
    in main.py) so it doesn't get garbage-collected mid-tick.
    """
    url = _resolve_app_url()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _ping_health,
        "interval",
        minutes=10,
        args=[url],
        id="keepalive",
        # Skip a run if the previous one is still in-flight (rare, but
        # avoids stacking pings when Railway is the one that's slow).
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("keepalive scheduler started — pinging %s/health every 10m", url)
    return scheduler


def stop_keepalive(scheduler: BackgroundScheduler) -> None:
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        pass

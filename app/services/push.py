"""Firebase Cloud Messaging (HTTP v1) — OS-level push notifications.

This module is best-effort: if `FCM_SERVICE_ACCOUNT_JSON` /
`FCM_PROJECT_ID` env vars are missing we silently no-op so the rest
of the app keeps working before Firebase is configured.

Auth uses google-auth's service-account credentials → short-lived
OAuth token → bearer auth on https://fcm.googleapis.com/v1/projects/
{project_id}/messages:send.

The FCM legacy server-key API was retired in 2024, so HTTP v1 is the
only supported path.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Optional

import httpx

_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_FCM_HOST = "https://fcm.googleapis.com"


# google-auth is loaded lazily so the module imports cleanly even
# without the dependency available (e.g. in a test environment).
_creds_lock = threading.Lock()
_cached_creds = None


def _load_credentials():
    """Returns google-auth Credentials, or None if not configured."""
    global _cached_creds
    if _cached_creds is not None:
        return _cached_creds
    raw = os.getenv("FCM_SERVICE_ACCOUNT_JSON")
    if not raw:
        return None
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        # Sometimes pasted with smart-quotes or escaped — try literal
        # unescape as a last resort.
        try:
            info = json.loads(raw.encode("utf-8").decode("unicode_escape"))
        except Exception:
            print("[push] FCM_SERVICE_ACCOUNT_JSON is not valid JSON")
            return None

    try:
        from google.oauth2 import service_account
    except Exception as e:
        print(f"[push] google-auth not installed: {e}")
        return None

    with _creds_lock:
        if _cached_creds is None:
            _cached_creds = service_account.Credentials.from_service_account_info(
                info, scopes=[_FCM_SCOPE]
            )
    return _cached_creds


def _project_id() -> Optional[str]:
    """FCM project id, sourced from env or the service-account JSON."""
    pid = os.getenv("FCM_PROJECT_ID")
    if pid:
        return pid
    raw = os.getenv("FCM_SERVICE_ACCOUNT_JSON")
    if not raw:
        return None
    try:
        return json.loads(raw).get("project_id")
    except Exception:
        return None


def _get_access_token() -> Optional[str]:
    creds = _load_credentials()
    if creds is None:
        return None
    try:
        from google.auth.transport.requests import Request as GAuthRequest
        # Refresh if needed; google-auth caches internally.
        if not creds.valid:
            creds.refresh(GAuthRequest())
        return creds.token
    except Exception as e:
        print(f"[push] token refresh failed: {e}")
        return None


def is_configured() -> bool:
    return bool(os.getenv("FCM_SERVICE_ACCOUNT_JSON")) and bool(_project_id())


def send_push_to_token(
    fcm_token: str,
    *,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """Send a single push to one FCM token. Returns True on 200 OK.

    All `data` values must be strings — FCM rejects non-string values
    in the data payload, so we coerce here.
    """
    if not is_configured():
        return False
    access_token = _get_access_token()
    project = _project_id()
    if not access_token or not project:
        return False

    payload = {
        "message": {
            "token": fcm_token,
            "notification": {"title": title, "body": body},
            "data": {k: str(v) for k, v in (data or {}).items()},
            "android": {
                "priority": "HIGH",
                "notification": {"sound": "default"},
            },
            "apns": {
                "payload": {"aps": {"sound": "default", "badge": 1}},
            },
        }
    }
    url = f"{_FCM_HOST}/v1/projects/{project}/messages:send"
    try:
        r = httpx.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8",
            },
            timeout=10.0,
        )
    except Exception as e:
        print(f"[push] send failed: {e}")
        return False

    if r.status_code == 200:
        return True

    # 404 / UNREGISTERED / NotRegistered → token died, caller should
    # delete it from device_tokens. We surface that distinction by
    # returning False and logging.
    if r.status_code in (400, 403, 404):
        print(f"[push] {r.status_code} {r.text}")
    else:
        print(f"[push] unexpected {r.status_code}: {r.text[:200]}")
    return False


def send_push_to_user(
    user_id: str,
    *,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> int:
    """Fan-out: send to every registered device of a user. Returns count
    of successful sends. Silent no-op if FCM is not configured.

    Looks up tokens via the supabase client; isolated import to avoid a
    cycle when this module is loaded by the app.
    """
    if not is_configured():
        print(f"[push] skip user={user_id[:8]}… (FCM_SERVICE_ACCOUNT_JSON not set)")
        return 0
    try:
        from app.database import supabase
    except Exception as e:
        print(f"[push] supabase import failed: {e}")
        return 0

    try:
        result = supabase.table("fcm_device_tokens")\
            .select("id, fcm_token")\
            .eq("user_id", user_id).execute()
        rows = result.data or []
    except Exception as e:
        print(f"[push] token lookup failed: {e}")
        return 0

    if not rows:
        print(f"[push] user={user_id[:8]}… has no registered tokens")
        return 0

    sent = 0
    dead_ids: list = []
    for row in rows:
        token = row.get("fcm_token")
        if not token:
            continue
        ok = send_push_to_token(token, title=title, body=body, data=data)
        if ok:
            sent += 1
        else:
            dead_ids.append(row.get("id"))

    print(f"[push] user={user_id[:8]}… tokens={len(rows)} sent={sent} dead={len(dead_ids)}")

    # Clean up tokens that failed — Firebase will keep returning 404 on
    # uninstalled apps, no point keeping them.
    if dead_ids:
        try:
            for did in dead_ids:
                supabase.table("fcm_device_tokens").delete().eq("id", did).execute()
        except Exception as e:
            print(f"[push] dead-token cleanup failed: {e}")

    return sent

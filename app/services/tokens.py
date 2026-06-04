"""Helpers for share-link / invite token lifetimes (finding #9).

Public quote share_tokens and client-onboarding invite tokens used to
live forever. These helpers stamp an expiry at issue time and check it at
use time. Legacy rows whose expiry column is NULL are treated as
non-expiring so existing links keep working until they are re-issued.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone

# Default lifetimes per the audit's finding #9 recommendation.
QUOTE_SHARE_TTL_DAYS = 30
CLIENT_INVITE_TTL_DAYS = 14


def expiry_in_days(days: int) -> str:
    """ISO-8601 UTC timestamp `days` from now, for storing in a
    timestamptz column."""
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def is_expired(value) -> bool:
    """True if `value` (an ISO timestamp string from Supabase, or None)
    is in the past. NULL/blank → False (legacy non-expiring token)."""
    if not value:
        return False
    if isinstance(value, datetime):
        dt = value
    else:
        # Supabase returns e.g. "2026-06-04T10:00:00+00:00" or "...Z".
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            # Unparseable → fail open (treat as non-expiring) rather than
            # locking a user out of a legitimate link over a format quirk.
            return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) > dt

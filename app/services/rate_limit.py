"""Tiny in-memory per-key sliding-window rate limiter.

Deliberately dependency-free: the backend runs as a single Railway
instance, so a process-local window is sufficient to stop abuse of the
unauthenticated endpoints (e.g. /support email-bombing, finding #11). If
the deployment ever scales horizontally, swap the backing store for Redis
behind the same `check()` signature.

Not constant-memory: keys are pruned lazily on each call, so a flood of
distinct keys is bounded by the request rate, not retained forever.
"""
from __future__ import annotations
import time
from collections import deque

from fastapi import HTTPException, Request


class SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: float):
        self.max_hits = max_hits
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}

    def check(self, key: str) -> None:
        """Record one hit for `key`; raise HTTP 429 if it exceeds the
        window allowance. Empty/blank keys are not rate-limited (caller
        should fall back to a sensible default key)."""
        if not key:
            return
        now = time.monotonic()
        cutoff = now - self.window
        bucket = self._hits.get(key)
        if bucket is None:
            bucket = deque()
            self._hits[key] = bucket
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.max_hits:
            retry = int(self.window - (now - bucket[0])) + 1
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(max(retry, 1))},
            )
        bucket.append(now)
        # Lazy prune of fully-expired buckets to bound memory growth.
        if len(self._hits) > 1024:
            for k in [k for k, b in self._hits.items() if not b or b[-1] < cutoff]:
                self._hits.pop(k, None)


def client_ip(request: Request) -> str:
    """Best-effort client IP behind Railway's proxy. Trusts the first hop
    in X-Forwarded-For, falling back to the socket peer."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

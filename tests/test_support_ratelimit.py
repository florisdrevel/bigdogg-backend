"""Regression tests for finding #11 — unauthenticated /support had no rate
limit, making it an email-bomb relay. The limiter caps hits per IP."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from app.services.rate_limit import SlidingWindowLimiter, client_ip
from app.routers import support as support_router


def _req(ip="1.2.3.4", fwd=None):
    headers = {}
    if fwd is not None:
        headers["x-forwarded-for"] = fwd
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=ip))


def test_limiter_blocks_after_allowance():
    lim = SlidingWindowLimiter(max_hits=3, window_seconds=600)
    for _ in range(3):
        lim.check("k")  # first 3 OK
    with pytest.raises(HTTPException) as exc:
        lim.check("k")
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_limiter_isolates_keys():
    lim = SlidingWindowLimiter(max_hits=1, window_seconds=600)
    lim.check("a")
    lim.check("b")  # different key, not blocked
    with pytest.raises(HTTPException):
        lim.check("a")


def test_client_ip_prefers_forwarded_header():
    assert client_ip(_req(ip="10.0.0.1", fwd="203.0.113.9, 10.0.0.1")) == "203.0.113.9"
    assert client_ip(_req(ip="10.0.0.1")) == "10.0.0.1"


async def test_support_route_429s_after_burst(monkeypatch):
    # Fresh, tiny limiter so the test is deterministic.
    monkeypatch.setattr(support_router, "_support_limiter",
                        SlidingWindowLimiter(max_hits=2, window_seconds=600))
    monkeypatch.setattr(support_router.resend.Emails, "send",
                        lambda *_a, **_kw: {"id": "fake"})
    body = {"name": "A", "email": "a@b.com", "message": "hi"}

    assert (await support_router.submit_support(_req(), body))["success"] is True
    assert (await support_router.submit_support(_req(), body))["success"] is True
    with pytest.raises(HTTPException) as exc:
        await support_router.submit_support(_req(), body)
    assert exc.value.status_code == 429


async def test_support_other_ip_not_blocked(monkeypatch):
    monkeypatch.setattr(support_router, "_support_limiter",
                        SlidingWindowLimiter(max_hits=1, window_seconds=600))
    monkeypatch.setattr(support_router.resend.Emails, "send",
                        lambda *_a, **_kw: {"id": "fake"})
    body = {"name": "A", "email": "a@b.com", "message": "hi"}

    await support_router.submit_support(_req(ip="1.1.1.1"), body)
    # Second IP still allowed.
    assert (await support_router.submit_support(_req(ip="2.2.2.2"), body))["success"] is True

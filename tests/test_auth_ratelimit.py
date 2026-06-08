"""Phase 2 auth-hardening regression tests.

Covers:
  * finding #1 — rate limiting on the unauthenticated auth endpoints
    (login per-IP AND per-email, reset, register). Auth is proxied
    through this backend, so GoTrue's per-IP limits can't isolate an
    attacker; these app-level limiters are the real brute-force defense.
  * finding #4 — register/reset must not leak raw internal error text,
    and reset must stay generic to avoid account enumeration.
"""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from app.routers import auth as auth_router
from app.services.rate_limit import SlidingWindowLimiter


def _req(ip="1.2.3.4"):
    return SimpleNamespace(headers={}, client=SimpleNamespace(host=ip))


def _fake_supabase(**auth_methods):
    return SimpleNamespace(auth=SimpleNamespace(**auth_methods))


def _raiser(msg):
    def _f(*_a, **_kw):
        raise Exception(msg)
    return _f


# ── finding #1: rate limiting ───────────────────────────────────

async def test_login_rate_limited_per_ip(monkeypatch):
    monkeypatch.setattr(auth_router, "_login_ip_limiter",
                        SlidingWindowLimiter(max_hits=2, window_seconds=300))
    monkeypatch.setattr(auth_router, "_login_email_limiter",
                        SlidingWindowLimiter(max_hits=100, window_seconds=900))
    monkeypatch.setattr(auth_router, "supabase",
                        _fake_supabase(sign_in_with_password=_raiser("bad creds")))
    body = auth_router.LoginRequest(email="a@b.com", password="x")

    for _ in range(2):  # within allowance → reaches the (failed) auth path
        with pytest.raises(HTTPException) as exc:
            await auth_router.login(body, _req())
        assert exc.value.status_code == 401
    with pytest.raises(HTTPException) as exc:  # 3rd from same IP → blocked
        await auth_router.login(body, _req())
    assert exc.value.status_code == 429


async def test_login_rate_limited_per_email_across_ips(monkeypatch):
    """A distributed attack (rotating IPs, one victim email) is still
    caught by the per-email limiter."""
    monkeypatch.setattr(auth_router, "_login_ip_limiter",
                        SlidingWindowLimiter(max_hits=100, window_seconds=300))
    monkeypatch.setattr(auth_router, "_login_email_limiter",
                        SlidingWindowLimiter(max_hits=2, window_seconds=900))
    monkeypatch.setattr(auth_router, "supabase",
                        _fake_supabase(sign_in_with_password=_raiser("bad creds")))
    body = auth_router.LoginRequest(email="victim@b.com", password="x")

    for ip in ("1.1.1.1", "2.2.2.2"):  # different IPs, same email
        with pytest.raises(HTTPException) as exc:
            await auth_router.login(body, _req(ip=ip))
        assert exc.value.status_code == 401
    with pytest.raises(HTTPException) as exc:  # new IP, same email → 429
        await auth_router.login(body, _req(ip="3.3.3.3"))
    assert exc.value.status_code == 429


async def test_reset_rate_limited(monkeypatch):
    monkeypatch.setattr(auth_router, "_reset_limiter",
                        SlidingWindowLimiter(max_hits=2, window_seconds=3600))
    monkeypatch.setattr(auth_router, "supabase",
                        _fake_supabase(reset_password_email=lambda _e: None))
    body = auth_router.ResetPasswordRequest(email="a@b.com")

    for _ in range(2):
        assert (await auth_router.reset_password(body, _req()))["message"] == "Reset email sent"
    with pytest.raises(HTTPException) as exc:
        await auth_router.reset_password(body, _req())
    assert exc.value.status_code == 429


async def test_register_rate_limited(monkeypatch):
    monkeypatch.setattr(auth_router, "_register_ip_limiter",
                        SlidingWindowLimiter(max_hits=1, window_seconds=3600))
    ok_user = SimpleNamespace(id="u1", identities=[object()], user_metadata={})
    monkeypatch.setattr(auth_router, "supabase",
                        _fake_supabase(sign_up=lambda _d: SimpleNamespace(user=ok_user)))
    body = auth_router.RegisterRequest(email="a@b.com", password="secret12", full_name="A")

    await auth_router.register(body, _req())          # first allowed
    with pytest.raises(HTTPException) as exc:          # second same IP → 429
        await auth_router.register(body, _req())
    assert exc.value.status_code == 429


# ── finding #4: no internal-error / enumeration leaks ───────────

async def test_register_error_is_generic(monkeypatch):
    monkeypatch.setattr(auth_router, "_register_ip_limiter",
                        SlidingWindowLimiter(max_hits=100, window_seconds=3600))
    monkeypatch.setattr(auth_router, "supabase",
                        _fake_supabase(sign_up=_raiser("SECRET supabase connstring leak")))
    body = auth_router.RegisterRequest(email="a@b.com", password="secret12", full_name="A")

    with pytest.raises(HTTPException) as exc:
        await auth_router.register(body, _req())
    assert exc.value.status_code == 400
    assert "SECRET" not in str(exc.value.detail)
    assert "supabase" not in str(exc.value.detail).lower()


async def test_reset_swallows_error_and_stays_generic(monkeypatch):
    monkeypatch.setattr(auth_router, "_reset_limiter",
                        SlidingWindowLimiter(max_hits=100, window_seconds=3600))
    monkeypatch.setattr(auth_router, "supabase",
                        _fake_supabase(reset_password_email=_raiser("internal: lookup failed for unknown@x.com")))
    body = auth_router.ResetPasswordRequest(email="unknown@x.com")

    result = await auth_router.reset_password(body, _req())
    assert result == {"message": "Reset email sent"}

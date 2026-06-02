"""Per-user AI quota guard.

A leaked access token shouldn't be able to drain the Anthropic budget.
Every AI-calling endpoint must call `require_ai_quota(user_id, endpoint)`
before invoking Claude and `record_ai_usage(user_id, endpoint, message)`
after a successful call.

Limits are deliberately generous — they bound a malicious blast radius,
not throttle legitimate users. If a real user hits them they should be
contacting support, not silently failing.
"""
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.database import supabase

DAILY_CALL_LIMIT = 200
# 1M output tokens/day ≈ €5/day at current Claude Sonnet 4 output rates.
DAILY_TOKEN_LIMIT = 1_000_000


def require_ai_quota(user_id: str, endpoint: str) -> None:
    """Raise 429 if the user has exhausted their 24-hour AI budget."""
    if not user_id:
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    rows = supabase.table("ai_usage")\
        .select("completion_tokens", count="exact")\
        .eq("user_id", user_id)\
        .gte("created_at", cutoff)\
        .execute()
    count = rows.count if rows.count is not None else len(rows.data or [])
    if count >= DAILY_CALL_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"daily_ai_call_limit_exceeded ({DAILY_CALL_LIMIT}/day)",
        )
    token_total = sum(
        int(r.get("completion_tokens") or 0) for r in (rows.data or [])
    )
    if token_total >= DAILY_TOKEN_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="daily_ai_token_limit_exceeded",
        )


def record_ai_usage(user_id: str, endpoint: str, message) -> None:
    """Log a completed Claude call. Best-effort — failures never bubble.
    Pulls prompt/completion token counts and the model id off the
    Anthropic Message object.
    """
    if not user_id:
        return
    try:
        usage = getattr(message, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        completion_tokens = (
            getattr(usage, "output_tokens", 0) if usage else 0
        )
        model = getattr(message, "model", "") or ""
        supabase.table("ai_usage").insert({
            "user_id":           user_id,
            "endpoint":          endpoint,
            "model":             model,
            "prompt_tokens":     int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
        }).execute()
    except Exception as e:
        print(f"[ai_quota] record failed: {e}")

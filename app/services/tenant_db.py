"""Owner-scoped data access helpers.

Every tenant-scoped read / update / delete that takes a row id from the
client should go through one of these helpers. Each helper applies
`.eq("user_id", caller_user_id)` by construction, so a missing scope
filter at a call site is impossible — the helper will raise 404 instead
of silently operating on a foreign-tenant row.

404 (not 403) is intentional: distinguishing "exists but not yours" from
"doesn't exist" leaks resource existence to an attacker probing UUIDs.

Helpers raise `fastapi.HTTPException(404, "not_found")` on miss. Callers
catch the exception only when they need to return a different error
shape; otherwise they let FastAPI propagate it.
"""
from fastapi import HTTPException
from app.database import supabase


_NOT_FOUND = "not_found"


def get_owned(
    table: str,
    row_id: str,
    user_id: str,
    *,
    select: str = "*",
) -> dict:
    """Fetch a single row by id, scoped to its owner. Raises 404 if the
    row doesn't exist OR doesn't belong to `user_id`."""
    if not row_id or not user_id:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    result = supabase.table(table)\
        .select(select)\
        .eq("id", row_id)\
        .eq("user_id", user_id)\
        .limit(1)\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    return result.data[0]


def update_owned(
    table: str,
    row_id: str,
    user_id: str,
    patch: dict,
) -> dict:
    """Update a row by id, scoped to its owner. Raises 404 if the row
    doesn't exist OR doesn't belong to `user_id`. Returns the updated row.
    """
    if not row_id or not user_id:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    if not patch:
        # No-op update — still verify ownership so callers get a 404
        # rather than a silent empty result.
        return get_owned(table, row_id, user_id)
    result = supabase.table(table)\
        .update(patch)\
        .eq("id", row_id)\
        .eq("user_id", user_id)\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    return result.data[0]


def delete_owned(
    table: str,
    row_id: str,
    user_id: str,
) -> None:
    """Delete a row by id, scoped to its owner. Raises 404 if the row
    doesn't exist OR doesn't belong to `user_id`."""
    if not row_id or not user_id:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)
    result = supabase.table(table)\
        .delete()\
        .eq("id", row_id)\
        .eq("user_id", user_id)\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=_NOT_FOUND)


def require_owned_id(
    table: str,
    row_id: str,
    user_id: str,
) -> str:
    """Cheap ownership probe — verify the row exists AND belongs to the
    caller without paying for column data. Returns row_id on success,
    raises 404 on miss. Use before destructive side-effects on related
    rows (e.g. marking an invoice paid via a bank link).
    """
    get_owned(table, row_id, user_id, select="id")
    return row_id

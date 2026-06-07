"""In-memory Supabase fake that ACTUALLY applies filters.

The accountant test file already has a `_FakeQuery` that ignores `.eq()`
— useful for testing pure-Python math, useless for testing tenant
isolation. This fake honours `.eq()`, `.neq()`, `.in_()`, `.gte()`,
`.lte()`, `.limit()`, `.single()`, `.update()`, `.delete()`, `.insert()`,
`.select()`, and `.order()` so cross-tenant access can be asserted
end-to-end.

Usage:

    tables = {
        "invoices": [
            {"id": "inv-A", "user_id": "user-A", "status": "sent"},
            {"id": "inv-B", "user_id": "user-B", "status": "sent"},
        ],
    }
    fake = FakeSupabase(tables)
    monkeypatch.setattr(some_router, "supabase", fake)

    # then call the route; the fake will filter as PostgREST would.
"""
from __future__ import annotations
from types import SimpleNamespace
from typing import Any


class _Query:
    def __init__(self, rows: list[dict]):
        self._rows = rows
        # ops applied in order
        self._filters: list[tuple[str, Any, str]] = []  # (col, value, op)
        self._select_cols: str = "*"
        self._limit: int | None = None
        self._is_single: bool = False
        self._is_delete: bool = False
        self._update_patch: dict | None = None
        self._insert_data: dict | list[dict] | None = None
        self._upsert_data: dict | None = None
        self._upsert_on_conflict: str | None = None
        self._order_col: str | None = None
        self._order_desc: bool = False

    # ── chainable builder methods ─────────────────────────────
    def select(self, cols: str = "*", *_, **__) -> "_Query":
        self._select_cols = cols
        return self

    def eq(self, col: str, value: Any) -> "_Query":
        self._filters.append((col, value, "eq"))
        return self

    def neq(self, col: str, value: Any) -> "_Query":
        self._filters.append((col, value, "neq"))
        return self

    def gte(self, col: str, value: Any) -> "_Query":
        self._filters.append((col, value, "gte"))
        return self

    def lte(self, col: str, value: Any) -> "_Query":
        self._filters.append((col, value, "lte"))
        return self

    def in_(self, col: str, values: list) -> "_Query":
        self._filters.append((col, list(values), "in"))
        return self

    def is_(self, col: str, value: Any) -> "_Query":
        self._filters.append((col, value, "is"))
        return self

    def like(self, col: str, pattern: str) -> "_Query":
        self._filters.append((col, pattern, "like"))
        return self

    def limit(self, n: int) -> "_Query":
        self._limit = n
        return self

    def single(self) -> "_Query":
        self._is_single = True
        self._limit = 1
        return self

    def order(self, col: str, desc: bool = False) -> "_Query":
        self._order_col = col
        self._order_desc = desc
        return self

    def update(self, patch: dict) -> "_Query":
        self._update_patch = dict(patch)
        return self

    def insert(self, data: dict | list[dict]) -> "_Query":
        self._insert_data = data
        return self

    def upsert(self, data: dict, on_conflict: str | None = None) -> "_Query":
        self._upsert_data = data
        self._upsert_on_conflict = on_conflict
        return self

    def delete(self) -> "_Query":
        self._is_delete = True
        return self

    # ── terminal ─────────────────────────────────────────────
    def _matches(self) -> list[dict]:
        out = list(self._rows)
        for col, val, op in self._filters:
            if op == "eq":
                out = [r for r in out if r.get(col) == val]
            elif op == "neq":
                out = [r for r in out if r.get(col) != val]
            elif op == "gte":
                out = [r for r in out if r.get(col) is not None and r.get(col) >= val]
            elif op == "lte":
                out = [r for r in out if r.get(col) is not None and r.get(col) <= val]
            elif op == "in":
                vs = set(val)
                out = [r for r in out if r.get(col) in vs]
            elif op == "is":
                if val is None or (isinstance(val, str) and val.lower() == "null"):
                    out = [r for r in out if r.get(col) is None]
                else:
                    out = [r for r in out if r.get(col) is val]
            elif op == "like":
                # Best-effort glob: PostgREST `%` wildcard.
                prefix = val.replace("%", "")
                out = [
                    r for r in out
                    if isinstance(r.get(col), str) and prefix in r.get(col, "")
                ]
        if self._order_col:
            out.sort(
                key=lambda r: (r.get(self._order_col) is None, r.get(self._order_col)),
                reverse=self._order_desc,
            )
        if self._limit is not None:
            out = out[: self._limit]
        return out

    def execute(self):
        if self._insert_data is not None:
            inserted = (
                [dict(d) for d in self._insert_data]
                if isinstance(self._insert_data, list)
                else [dict(self._insert_data)]
            )
            self._rows.extend(inserted)
            return SimpleNamespace(data=inserted, count=None)
        if self._upsert_data is not None:
            d = dict(self._upsert_data)
            conflict_cols = (
                [c.strip() for c in self._upsert_on_conflict.split(",")]
                if self._upsert_on_conflict
                else ["id"]
            )
            existing = next(
                (
                    r
                    for r in self._rows
                    if all(r.get(c) == d.get(c) for c in conflict_cols)
                ),
                None,
            )
            if existing:
                existing.update(d)
                return SimpleNamespace(data=[existing], count=None)
            self._rows.append(d)
            return SimpleNamespace(data=[d], count=None)
        if self._is_delete:
            matches = self._matches()
            for m in matches:
                if m in self._rows:
                    self._rows.remove(m)
            return SimpleNamespace(data=matches, count=None)
        if self._update_patch is not None:
            matches = self._matches()
            for m in matches:
                m.update(self._update_patch)
            return SimpleNamespace(data=matches, count=None)
        # plain SELECT
        matches = self._matches()
        if self._is_single:
            return SimpleNamespace(data=(matches[0] if matches else None))
        return SimpleNamespace(data=matches, count=len(self._matches()))


class _Storage:
    """Minimal stub — most tests don't touch storage."""
    def from_(self, _bucket):
        return self
    def upload(self, *_a, **_kw): return None
    def remove(self, *_a, **_kw): return None
    def get_public_url(self, path): return f"http://fake/{path}"
    def create_signed_url(self, path, _ttl): return {"signedURL": f"http://fake/{path}?sig=stub"}


class _Auth:
    """Minimal stub — tests that exercise auth.get_user should monkeypatch
    `get_user_id` directly instead of going through this."""
    def get_user(self, _token): return SimpleNamespace(user=None)
    def sign_in_with_password(self, _payload): return SimpleNamespace(user=None, session=None)
    def admin(self): return self
    def get_user_by_id(self, _uid): return SimpleNamespace(user=None)


class FakeSupabase:
    def __init__(self, tables: dict[str, list[dict]] | None = None):
        self._tables: dict[str, list[dict]] = tables or {}
        self.storage = _Storage()
        self.auth = _Auth()

    def table(self, name: str) -> _Query:
        rows = self._tables.setdefault(name, [])
        return _Query(rows)

    # introspection for tests
    def rows(self, table: str) -> list[dict]:
        return self._tables.setdefault(table, [])

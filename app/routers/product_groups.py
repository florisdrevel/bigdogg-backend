from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from app.database import supabase

router = APIRouter()


class GroupItemIn(BaseModel):
    product_id: str
    default_quantity: float = 1


class GroupCreate(BaseModel):
    name: str
    items: List[GroupItemIn] = []


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    # When present, fully replaces the group's items.
    items: Optional[List[GroupItemIn]] = None


def get_user_id(request: Request) -> str:
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        token = auth_header.replace("Bearer ", "")
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def _load_groups_with_items(user_id: str) -> list:
    """Return the user's active groups, each with its items joined to the
    current product details so the app can build invoice lines in one
    round-trip. Items whose product was soft-deleted are dropped."""
    groups_res = supabase.table("product_groups")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("is_active", True)\
        .order("created_at", desc=False)\
        .execute()
    groups = groups_res.data or []
    if not groups:
        return []

    group_ids = [g["id"] for g in groups]
    items_res = supabase.table("product_group_items")\
        .select("*")\
        .in_("group_id", group_ids)\
        .order("position", desc=False)\
        .execute()
    items = items_res.data or []

    products_res = supabase.table("products")\
        .select("id, name, description, unit_price, btw_rate, unit, is_active")\
        .eq("user_id", user_id)\
        .execute()
    product_map = {p["id"]: p for p in (products_res.data or [])}

    items_by_group: dict = {}
    for it in items:
        prod = product_map.get(it["product_id"])
        if not prod or prod.get("is_active") is False:
            continue
        items_by_group.setdefault(it["group_id"], []).append({
            "product_id": it["product_id"],
            "default_quantity": it.get("default_quantity", 1),
            "position": it.get("position", 0),
            "name": prod.get("name"),
            "description": prod.get("description"),
            "unit_price": prod.get("unit_price"),
            "btw_rate": prod.get("btw_rate"),
            "unit": prod.get("unit"),
        })

    for g in groups:
        g["items"] = items_by_group.get(g["id"], [])
    return groups


def _replace_items(group_id: str, items: List[GroupItemIn]) -> None:
    supabase.table("product_group_items").delete().eq("group_id", group_id).execute()
    if items:
        rows = [{
            "group_id": group_id,
            "product_id": it.product_id,
            "default_quantity": it.default_quantity,
            "position": idx,
        } for idx, it in enumerate(items)]
        supabase.table("product_group_items").insert(rows).execute()


@router.get("/")
async def get_groups(request: Request):
    user_id = get_user_id(request)
    try:
        return {"groups": _load_groups_with_items(user_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def create_group(group: GroupCreate, request: Request):
    user_id = get_user_id(request)
    try:
        res = supabase.table("product_groups").insert({
            "user_id": user_id,
            "name": group.name,
        }).execute()
        group_id = res.data[0]["id"]
        _replace_items(group_id, group.items)
        groups = _load_groups_with_items(user_id)
        created = next((g for g in groups if g["id"] == group_id), None)
        return {"group": created}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{group_id}")
async def update_group(group_id: str, group: GroupUpdate, request: Request):
    user_id = get_user_id(request)
    try:
        owned = supabase.table("product_groups")\
            .select("id")\
            .eq("id", group_id)\
            .eq("user_id", user_id)\
            .execute()
        if not owned.data:
            raise HTTPException(status_code=404, detail="Group not found")

        if group.name is not None:
            supabase.table("product_groups")\
                .update({"name": group.name})\
                .eq("id", group_id)\
                .eq("user_id", user_id)\
                .execute()

        if group.items is not None:
            _replace_items(group_id, group.items)

        groups = _load_groups_with_items(user_id)
        updated = next((g for g in groups if g["id"] == group_id), None)
        return {"group": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}")
async def delete_group(group_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        res = supabase.table("product_groups")\
            .update({"is_active": False})\
            .eq("id", group_id)\
            .eq("user_id", user_id)\
            .execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Group not found")
        return {"message": "Group deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

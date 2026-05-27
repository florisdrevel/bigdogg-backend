from fastapi import APIRouter, HTTPException, Request
from app.database import supabase
from datetime import date

router = APIRouter()

HOURS_PER_DAY = 9.0


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


def _build_product_maps(products: list) -> tuple:
    """From a products list build the three lookup maps used to resolve
    an invoice line's billing unit:

      by_id    : product_id        -> unit
      by_name  : lower(name)       -> unit
      by_price : unit_price (2dp)  -> unit, ONLY for prices that uniquely
                 identify a day/hour product (no other unit shares that
                 price). This is what recovers legacy lines that have no
                 product_id and a description that doesn't match the
                 product name — e.g. a line 'dagfee' billed at the exact
                 'dayfee' day-rate still resolves to 'day'.
    """
    by_id: dict[str, str] = {}
    by_name: dict[str, str] = {}
    price_units: dict[float, set] = {}
    for p in (products or []):
        pid = (p.get("id") or "").strip()
        name = (p.get("name") or "").strip().lower()
        unit = (p.get("unit") or "").strip().lower()
        if not unit:
            continue
        if pid:
            by_id[pid] = unit
        if name:
            by_name[name] = unit
        try:
            price = round(float(p.get("unit_price") or 0), 2)
        except (TypeError, ValueError):
            price = 0.0
        if price > 0:
            price_units.setdefault(price, set()).add(unit)
    by_price: dict[float, str] = {}
    for price, units in price_units.items():
        if len(units) == 1:
            u = next(iter(units))
            if u in ("day", "hour"):
                by_price[price] = u
    return by_id, by_name, by_price


def _resolve_unit(line: dict, by_id: dict, by_name: dict, by_price: dict) -> tuple:
    """Resolve an invoice/quote line's effective billing unit.

    Order: product_id → description (exact, then substring) → unit_price
    match to a unique day/hour product → line.unit. Returns (unit, via)
    where `via` is a short string naming which signal won (for logging).
    """
    raw_unit = (line.get("unit") or "fixed").lower()
    description = (line.get("description") or "")
    product_id = line.get("product_id")

    if product_id and product_id in by_id:
        return by_id[product_id], "product_id"

    if by_name:
        desc_lower = description.lower().strip()
        if desc_lower in by_name:
            return by_name[desc_lower], "name"
        # Longest first so a 'fee' product doesn't shadow 'dayfee'.
        for name in sorted(by_name.keys(), key=len, reverse=True):
            if name and name in desc_lower:
                return by_name[name], "substr"

    # Price fallback — only resolves to day/hour, only for unambiguous
    # prices. Lets existing invoices count without re-creating them.
    try:
        lp = round(float(line.get("unit_price_ex_btw") or 0), 2)
    except (TypeError, ValueError):
        lp = 0.0
    if lp in by_price:
        return by_price[lp], "price"

    return raw_unit, "line.unit"


def _calc_invoice_hours(user_id: str, year_start: str, year_end: str) -> tuple:
    """
    Calculate hours from invoice lines.

    Unit resolution order (see _resolve_unit):
      1. line.product_id → products.unit  (firm link, new invoices)
      2. line.description → product name   (exact then substring)
      3. line.unit_price  → unique day/hour product price  (recovers
         legacy lines with no product_id and a non-matching description)
      4. line.unit                          (whatever was saved)

    Scoring: 'day' → qty*9h, 'hour' → qty*1h, else 0.
    """
    try:
        inv_result = supabase.table("invoices")\
            .select("id, invoice_date, invoice_number, project_id, status")\
            .eq("user_id", user_id)\
            .neq("status", "draft")\
            .gte("invoice_date", year_start)\
            .lte("invoice_date", year_end)\
            .execute()
        invoices = inv_result.data or []
        if not invoices:
            return 0.0, []

        inv_ids = [i["id"] for i in invoices]
        inv_map = {i["id"]: i for i in invoices}

        # Select includes product_id + unit_price_ex_btw; retry without
        # product_id if that column doesn't exist yet (migration not run).
        try:
            lines = (supabase.table("invoice_lines")
                     .select("invoice_id, description, quantity, unit, unit_price_ex_btw, product_id")
                     .in_("invoice_id", inv_ids).execute().data) or []
        except Exception as e:
            print(f"[hours] product_id column missing — falling back: {e}")
            lines = (supabase.table("invoice_lines")
                     .select("invoice_id, description, quantity, unit, unit_price_ex_btw")
                     .in_("invoice_id", inv_ids).execute().data) or []

        products = []
        try:
            products = (supabase.table("products")
                        .select("id, name, unit, unit_price")
                        .eq("user_id", user_id).execute().data) or []
        except Exception as e:
            print(f"[hours] product load failed: {e}")
        by_id, by_name, by_price = _build_product_maps(products)

        total = 0.0
        breakdown = []
        for line in lines:
            unit, via = _resolve_unit(line, by_id, by_name, by_price)
            qty = float(line.get("quantity", 0) or 0)
            inv = inv_map.get(line["invoice_id"], {})

            if unit == "day":
                hrs = qty * HOURS_PER_DAY
            elif unit == "hour":
                hrs = qty
            else:
                continue
            if hrs <= 0:
                continue

            total += hrs
            breakdown.append({
                "source": "invoice",
                "invoice_number": inv.get("invoice_number", ""),
                "invoice_id": line["invoice_id"],
                "project_id": inv.get("project_id"),
                "description": line.get("description", "") or "",
                "quantity": qty,
                "unit": unit,
                "hours": hrs,
                "date": inv.get("invoice_date", ""),
            })
        return round(total, 2), breakdown
    except Exception as e:
        print(f"Error calculating invoice hours: {e}")
        return 0.0, []


@router.get("/")
async def get_hours(request: Request, year: int = None, quarter: int = None):
    user_id = get_user_id(request)
    today = date.today()
    if year is None:
        year = today.year
    try:
        query = supabase.table("hours").select("*").eq("user_id", user_id)
        if quarter is not None:
            quarters = {1: ("01-01", "03-31"), 2: ("04-01", "06-30"),
                        3: ("07-01", "09-30"), 4: ("10-01", "12-31")}
            start, end = quarters[quarter]
            query = query.gte("date", f"{year}-{start}").lte("date", f"{year}-{end}")
        else:
            query = query.gte("date", f"{year}-01-01").lte("date", f"{year}-12-31")
        result = query.order("date", desc=True).execute()
        entries = result.data or []
        manual_year = sum(float(e["hours"]) for e in entries)

        inv_year_hrs, inv_breakdown = _calc_invoice_hours(user_id, f"{year}-01-01", f"{year}-12-31")
        total_year = manual_year + inv_year_hrs

        current_quarter = (today.month - 1) // 3 + 1
        q_ends = {1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}
        q_starts = {1: "01", 2: "04", 3: "07", 4: "10"}
        q_start_str = f"{today.year}-{q_starts[current_quarter]}-01"
        q_end_str = f"{today.year}-{q_ends[current_quarter]}"

        q_result = supabase.table("hours").select("hours").eq("user_id", user_id)\
            .gte("date", q_start_str).lte("date", q_end_str).execute()
        manual_quarter = sum(float(e["hours"]) for e in (q_result.data or []))
        inv_q_hrs, _ = _calc_invoice_hours(user_id, q_start_str, q_end_str)
        total_quarter = manual_quarter + inv_q_hrs

        return {
            "entries": entries,
            "invoice_hours_breakdown": inv_breakdown[:20],
            "total_year": round(total_year, 2),
            "total_quarter": round(total_quarter, 2),
            "manual_year": round(manual_year, 2),
            "invoice_year": round(inv_year_hrs, 2),
            "year": year,
            "urencriterium": 1225,
            "urencriterium_progress": round(min(total_year / 1225 * 100, 100), 1),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def add_hours(request: Request):
    user_id = get_user_id(request)
    try:
        body = await request.json()
        hours_val = float(body.get("hours", 0))
        if hours_val <= 0:
            raise HTTPException(status_code=400, detail="Hours must be greater than 0")
        data = {
            "user_id": user_id,
            "hours": hours_val,
            "date": body.get("date", date.today().isoformat()),
            "description": body.get("description", ""),
        }
        if body.get("project_id"):
            data["project_id"] = body["project_id"]
        result = supabase.table("hours").insert(data).execute()
        return {"success": True, "entry": result.data[0] if result.data else {}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}")
async def delete_hours(entry_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        supabase.table("hours").delete().eq("id", entry_id).eq("user_id", user_id).execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from app.database import supabase
from app.config import settings
from datetime import date, timedelta, datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER
import io
import urllib.request
import resend

router = APIRouter()

TEAL = colors.HexColor('#1B3A4B')
GOLD = colors.HexColor('#C9A96E')
LIGHT_GREY = colors.HexColor('#F5F3EF')
MID_GREY = colors.HexColor('#E2DDD6')
TEXT_SECONDARY = colors.HexColor('#4A6572')


class QuoteLine(BaseModel):
    description: str
    quantity: float
    unit_price_ex_btw: float
    btw_rate: int = 21
    unit: str = "fixed"
    # When the user picks a product from the dropdown, the frontend
    # sends its id. Carried through to invoice on conversion so the
    # hours calculation can resolve the unit reliably.
    product_id: Optional[str] = None


class QuoteCreate(BaseModel):
    client_id: str
    quote_date: Optional[str] = None
    valid_until: Optional[str] = None
    lines: List[QuoteLine]
    notes: Optional[str] = None
    project_id: Optional[str] = None


class QuoteUpdate(BaseModel):
    client_id: Optional[str] = None
    quote_date: Optional[str] = None
    valid_until: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    project_id: Optional[str] = None
    lines: Optional[List[QuoteLine]] = None


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


def generate_quote_number(user_id: str) -> str:
    """
    New quote numbers use the full word OFFERTE- as prefix so emails read
    naturally ("onze offerte OFFERTE-2026-000007" beats the old
    "onze offerte OFF-2026-000007" which looked like a typo).

    Existing OFF-YYYY-... numbers stay as they are. The search counts ANY
    quote in the current year so the OFFERTE- sequence picks up where the
    legacy OFF- numbering left off — no duplicate sequence values.
    """
    year = date.today().year
    new_prefix = f"OFFERTE-{year}-"

    # Highest existing sequence this year, regardless of prefix.
    result = supabase.table("quotes")\
        .select("quote_number")\
        .eq("user_id", user_id)\
        .or_(f"quote_number.like.OFFERTE-{year}-%,quote_number.like.OFF-{year}-%")\
        .execute()

    next_seq = 1
    for row in (result.data or []):
        try:
            seq = int(row["quote_number"].split("-")[-1])
            if seq + 1 > next_seq:
                next_seq = seq + 1
        except (ValueError, IndexError):
            continue

    return f"{new_prefix}{str(next_seq).zfill(6)}"


def _compute_totals(lines: List[QuoteLine]) -> tuple[float, float, float]:
    subtotal = sum(l.quantity * l.unit_price_ex_btw for l in lines)
    btw = sum(l.quantity * l.unit_price_ex_btw * l.btw_rate / 100 for l in lines)
    return round(subtotal, 2), round(btw, 2), round(subtotal + btw, 2)


# ── List ────────────────────────────────────────────────────
@router.get("/")
async def list_quotes(request: Request):
    user_id = get_user_id(request)
    try:
        response = supabase.table("quotes")\
            .select("*, clients(contact_name, company_name, email)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return {"quotes": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Single ──────────────────────────────────────────────────
@router.get("/{quote_id}")
async def get_quote(quote_id: str, request: Request):
    user_id = get_user_id(request)
    try:
        quote = supabase.table("quotes")\
            .select("*, clients(*)")\
            .eq("id", quote_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        lines = supabase.table("quote_lines")\
            .select("*")\
            .eq("quote_id", quote_id)\
            .execute()
        return {"quote": quote.data, "lines": lines.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Create ──────────────────────────────────────────────────
@router.post("/")
async def create_quote(quote: QuoteCreate, request: Request):
    user_id = get_user_id(request)
    try:
        quote_number = generate_quote_number(user_id)
        quote_date = quote.quote_date or date.today().isoformat()
        valid_until = quote.valid_until or (date.today() + timedelta(days=30)).isoformat()

        subtotal, btw_amount, total = _compute_totals(quote.lines)

        client_result = supabase.table("clients")\
            .select("contact_name, email, company_name")\
            .eq("id", quote.client_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        if not client_result.data:
            raise HTTPException(status_code=404, detail="Client not found")
        client_data = client_result.data

        quote_response = supabase.table("quotes").insert({
            "user_id": user_id,
            "client_id": quote.client_id,
            "client_name": client_data.get("contact_name", ""),
            "client_email": client_data.get("email", ""),
            "client_company": client_data.get("company_name", ""),
            "quote_number": quote_number,
            "quote_date": quote_date,
            "valid_until": valid_until,
            "project_id": quote.project_id,
            "status": "draft",
            "subtotal_ex_btw": subtotal,
            "btw_amount": btw_amount,
            "total_incl_btw": total,
            "notes": quote.notes,
        }).execute()

        quote_id = quote_response.data[0]["id"]

        # Look up unit per product, mirroring invoices behavior.
        products_result = supabase.table("products")\
            .select("name, unit").eq("user_id", user_id).execute()
        product_unit_map = {
            p["name"].lower(): p["unit"] for p in (products_result.data or [])
        }

        lines_data = []
        for l in quote.lines:
            row = {
                "quote_id": quote_id,
                "description": l.description,
                "quantity": l.quantity,
                "unit_price_ex_btw": l.unit_price_ex_btw,
                "btw_rate": l.btw_rate,
                "line_total_ex_btw": round(l.quantity * l.unit_price_ex_btw, 2),
                "unit": l.unit if l.unit not in ("fixed", None, "") else
                    product_unit_map.get(l.description.lower(), "fixed"),
            }
            if l.product_id:
                row["product_id"] = l.product_id
            lines_data.append(row)
        supabase.table("quote_lines").insert(lines_data).execute()

        return {"quote": quote_response.data[0], "quote_number": quote_number}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Update ──────────────────────────────────────────────────
@router.put("/{quote_id}")
async def update_quote(quote_id: str, body: QuoteUpdate, request: Request):
    user_id = get_user_id(request)

    existing = supabase.table("quotes")\
        .select("id, status")\
        .eq("id", quote_id)\
        .eq("user_id", user_id)\
        .single()\
        .execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Quote not found")

    update: dict = {}
    if body.client_id is not None:
        client_result = supabase.table("clients")\
            .select("contact_name, email, company_name")\
            .eq("id", body.client_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()
        if not client_result.data:
            raise HTTPException(status_code=404, detail="Client not found")
        update["client_id"] = body.client_id
        update["client_name"] = client_result.data.get("contact_name", "")
        update["client_email"] = client_result.data.get("email", "")
        update["client_company"] = client_result.data.get("company_name", "")
    if body.quote_date is not None:
        update["quote_date"] = body.quote_date
    if body.valid_until is not None:
        update["valid_until"] = body.valid_until
    if body.status is not None:
        if body.status not in ("draft", "sent", "accepted", "declined", "converted"):
            raise HTTPException(status_code=400, detail="invalid status")
        update["status"] = body.status
    if body.notes is not None:
        update["notes"] = body.notes
    if body.project_id is not None:
        update["project_id"] = body.project_id

    # If new lines were provided, recompute totals and replace line items.
    if body.lines is not None:
        subtotal, btw_amount, total = _compute_totals(body.lines)
        update["subtotal_ex_btw"] = subtotal
        update["btw_amount"] = btw_amount
        update["total_incl_btw"] = total

        supabase.table("quote_lines").delete().eq("quote_id", quote_id).execute()

        products_result = supabase.table("products")\
            .select("name, unit").eq("user_id", user_id).execute()
        product_unit_map = {
            p["name"].lower(): p["unit"] for p in (products_result.data or [])
        }
        lines_data = []
        for l in body.lines:
            row = {
                "quote_id": quote_id,
                "description": l.description,
                "quantity": l.quantity,
                "unit_price_ex_btw": l.unit_price_ex_btw,
                "btw_rate": l.btw_rate,
                "line_total_ex_btw": round(l.quantity * l.unit_price_ex_btw, 2),
                "unit": l.unit if l.unit not in ("fixed", None, "") else
                    product_unit_map.get(l.description.lower(), "fixed"),
            }
            if l.product_id:
                row["product_id"] = l.product_id
            lines_data.append(row)
        supabase.table("quote_lines").insert(lines_data).execute()

    if update:
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        supabase.table("quotes").update(update)\
            .eq("id", quote_id).eq("user_id", user_id).execute()

    return {"success": True}


# ── Delete ──────────────────────────────────────────────────
@router.delete("/{quote_id}")
async def delete_quote(quote_id: str, request: Request):
    user_id = get_user_id(request)
    existing = supabase.table("quotes")\
        .select("id, status")\
        .eq("id", quote_id)\
        .eq("user_id", user_id)\
        .single()\
        .execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    if existing.data["status"] == "converted":
        raise HTTPException(
            status_code=400,
            detail="Converted quotes cannot be deleted; the linked invoice keeps the audit trail.",
        )
    supabase.table("quote_lines").delete().eq("quote_id", quote_id).execute()
    supabase.table("quotes").delete()\
        .eq("id", quote_id).eq("user_id", user_id).execute()
    return {"success": True}


# ── Convert to invoice ──────────────────────────────────────
@router.post("/{quote_id}/convert")
async def convert_quote(quote_id: str, request: Request):
    user_id = get_user_id(request)

    quote_result = supabase.table("quotes")\
        .select("*").eq("id", quote_id).eq("user_id", user_id).single().execute()
    if not quote_result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    quote = quote_result.data
    if quote["status"] == "converted" and quote.get("converted_invoice_id"):
        return {
            "success": True,
            "invoice_id": quote["converted_invoice_id"],
            "already_converted": True,
        }

    lines_result = supabase.table("quote_lines")\
        .select("*").eq("quote_id", quote_id).execute()
    lines = lines_result.data or []

    # Reuse the existing invoice numbering scheme.
    from app.routers.invoices import generate_invoice_number
    invoice_number = generate_invoice_number(user_id)
    invoice_date = date.today().isoformat()
    due_date = (date.today() + timedelta(days=30)).isoformat()

    invoice_response = supabase.table("invoices").insert({
        "user_id": user_id,
        "client_id": quote.get("client_id"),
        "client_name": quote.get("client_name"),
        "client_email": quote.get("client_email"),
        "client_company": quote.get("client_company"),
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "project_id": quote.get("project_id"),
        "status": "draft",
        "subtotal_ex_btw": quote.get("subtotal_ex_btw") or 0,
        "btw_amount": quote.get("btw_amount") or 0,
        "total_incl_btw": quote.get("total_incl_btw") or 0,
        "notes": quote.get("notes"),
    }).execute()
    invoice_id = invoice_response.data[0]["id"]

    if lines:
        invoice_lines = []
        for l in lines:
            row = {
                "invoice_id": invoice_id,
                "description": l.get("description"),
                "quantity": l.get("quantity"),
                "unit_price_ex_btw": l.get("unit_price_ex_btw"),
                "btw_rate": l.get("btw_rate"),
                "line_total_ex_btw": l.get("line_total_ex_btw"),
                "unit": l.get("unit") or "fixed",
            }
            if l.get("product_id"):
                row["product_id"] = l["product_id"]
            invoice_lines.append(row)
        supabase.table("invoice_lines").insert(invoice_lines).execute()

    supabase.table("quotes").update({
        "status": "converted",
        "converted_invoice_id": invoice_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", quote_id).execute()

    return {
        "success": True,
        "invoice_id": invoice_id,
        "invoice_number": invoice_number,
    }


# ── PDF ─────────────────────────────────────────────────────
# Both POST (spec) and GET (so url_launcher can hit it with ?token= like the
# invoice PDF endpoint).
@router.post("/{quote_id}/pdf")
@router.get("/{quote_id}/pdf")
async def quote_pdf(quote_id: str, request: Request, token: str = Query(None)):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header:
        token = auth_header.replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        sender_email = user.user.email or ""
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    quote_result = supabase.table("quotes")\
        .select("*, clients(*)").eq("id", quote_id).eq("user_id", user_id)\
        .single().execute()
    if not quote_result.data:
        raise HTTPException(status_code=404, detail="Quote not found")

    lines_result = supabase.table("quote_lines")\
        .select("*").eq("quote_id", quote_id).execute()

    profile_result = supabase.table("user_profiles")\
        .select("*").eq("id", user_id).execute()

    quote = quote_result.data
    lines = lines_result.data or []
    profile = profile_result.data[0] if profile_result.data else {}

    client = quote.get("clients") or {
        "contact_name": quote.get("client_name", ""),
        "email": quote.get("client_email", ""),
        "company_name": quote.get("client_company", ""),
    }

    pdf_bytes = _generate_quote_pdf(quote, lines, profile, client, sender_email)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={quote['quote_number']}.pdf"
        },
    )


def _safe_hex(hex_str, fallback):
    """Parse a user-supplied #RRGGBB hex; fall back on anything malformed."""
    if not hex_str:
        return fallback
    s = str(hex_str).strip()
    if not s.startswith('#'):
        s = '#' + s
    try:
        return colors.HexColor(s)
    except Exception:
        return fallback


def _generate_quote_pdf(quote, lines, profile, client, sender_email=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    story = []

    # User-customisable accent colors. Default = BigDogg teal/gold.
    primary = _safe_hex(profile.get('invoice_primary_color'), TEAL)
    accent  = _safe_hex(profile.get('invoice_accent_color'),  GOLD)

    subtitle_style = ParagraphStyle('Subtitle', fontName='Helvetica', fontSize=10, textColor=TEXT_SECONDARY, spaceAfter=1*mm)
    label_style    = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=8, textColor=TEXT_SECONDARY, spaceAfter=1*mm, leading=12)
    value_style    = ParagraphStyle('Value', fontName='Helvetica', fontSize=10, textColor=primary, spaceAfter=1*mm, leading=14)
    value_bold_style = ParagraphStyle('ValueBold', fontName='Helvetica-Bold', fontSize=10, textColor=primary, spaceAfter=1*mm, leading=14)
    number_style   = ParagraphStyle('Number', fontName='Helvetica-Bold', fontSize=20, textColor=primary, spaceAfter=2*mm)

    page_width = A4[0] - 40*mm

    display_name = profile.get('business_name') or ''
    if len(display_name) <= 15:
        name_font_size = 28
    elif len(display_name) <= 22:
        name_font_size = 22
    elif len(display_name) <= 30:
        name_font_size = 18
    else:
        name_font_size = 14
    name_style = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=name_font_size, textColor=primary, spaceAfter=2*mm)

    logo_url = profile.get('logo_url')
    logo_img = None
    if logo_url:
        try:
            from reportlab.platypus import Image as RLImage
            req = urllib.request.Request(logo_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                logo_bytes = resp.read()
            import io as _io
            logo_img = RLImage(_io.BytesIO(logo_bytes), width=40*mm, height=40*mm)
            logo_img.hAlign = 'LEFT'
        except Exception:
            logo_img = None

    if logo_img:
        header_data = [[logo_img, Paragraph(quote['quote_number'], number_style)]]
    else:
        header_data = [[Paragraph(display_name, name_style), Paragraph(quote['quote_number'], number_style)]]
    header_table = Table(header_data, colWidths=[page_width * 0.6, page_width * 0.4])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2*mm))

    # OFFERTE label – this is what makes the PDF read as a quote.
    story.append(Paragraph(
        'OFFERTE',
        ParagraphStyle('QuoteLabel', fontName='Helvetica-Bold', fontSize=14,
                       textColor=accent, spaceAfter=2*mm, alignment=TA_CENTER),
    ))
    story.append(HRFlowable(width="100%", thickness=3, color=accent, spaceAfter=6*mm))

    sender_lines = []
    if profile.get('full_name'):
        sender_lines.append(Paragraph(profile['full_name'], value_bold_style))
    if profile.get('address'):
        sender_lines.append(Paragraph(profile['address'], value_style))
    if profile.get('postcode') or profile.get('city'):
        sender_lines.append(Paragraph(
            f"{profile.get('postcode', '')} {profile.get('city', '')}".strip(), value_style))
    if profile.get('kvk_number'):
        sender_lines.append(Paragraph(f"KVK: {profile['kvk_number']}", subtitle_style))
    if profile.get('btw_number'):
        sender_lines.append(Paragraph(f"BTW: {profile['btw_number']}", subtitle_style))
    if profile.get('iban'):
        sender_lines.append(Paragraph(f"IBAN: {profile['iban']}", subtitle_style))
    if sender_email:
        sender_lines.append(Paragraph(sender_email, subtitle_style))

    client_lines = []
    if client.get('company_name'):
        client_lines.append(Paragraph(client['company_name'], value_bold_style))
    if client.get('contact_name'):
        client_lines.append(Paragraph(client['contact_name'], value_style))
    if client.get('address'):
        client_lines.append(Paragraph(client['address'], value_style))
    if client.get('postcode') or client.get('city'):
        client_lines.append(Paragraph(
            f"{client.get('postcode', '')} {client.get('city', '')}".strip(), value_style))
    if client.get('email'):
        client_lines.append(Paragraph(client['email'], subtitle_style))

    date_lines = [
        Paragraph('OFFERTEDATUM', label_style),
        Paragraph(quote.get('quote_date', ''), value_style),
        Spacer(1, 3*mm),
        Paragraph('GELDIG TOT', label_style),
        Paragraph(quote.get('valid_until', '') or '-', value_style),
        Spacer(1, 3*mm),
        Paragraph('STATUS', label_style),
        Paragraph(quote.get('status', '').upper(), value_bold_style),
    ]

    info_data = [[
        [Paragraph('VAN', label_style)] + sender_lines,
        [Paragraph('AAN', label_style)] + client_lines,
        date_lines,
    ]]
    info_table = Table(info_data, colWidths=[page_width * 0.35, page_width * 0.35, page_width * 0.30])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8*mm))

    line_header = ['OMSCHRIJVING', 'AANTAL', 'PRIJS EX BTW', 'BTW', 'TOTAAL EX BTW']
    table_data = [line_header]
    for line in lines:
        table_data.append([
            line.get('description', ''),
            str(line.get('quantity', '')),
            f"€ {float(line.get('unit_price_ex_btw') or 0):.2f}",
            f"{line.get('btw_rate', 0)}%",
            f"€ {float(line.get('line_total_ex_btw') or 0):.2f}",
        ])

    col_widths = [page_width*0.40, page_width*0.10, page_width*0.18, page_width*0.10, page_width*0.22]
    lines_table = Table(table_data, colWidths=col_widths)
    lines_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('LEFTPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('TEXTCOLOR', (0, 1), (-1, -1), primary),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('LINEBELOW', (0, -1), (-1, -1), 1, MID_GREY),
    ]))
    story.append(lines_table)
    story.append(Spacer(1, 6*mm))

    subtotal = float(quote.get('subtotal_ex_btw', 0) or 0)
    btw_amount = float(quote.get('btw_amount', 0) or 0)
    total = float(quote.get('total_incl_btw', 0) or 0)
    totals_data = [
        ['', 'Subtotaal ex BTW', f"€ {subtotal:.2f}"],
        ['', 'BTW', f"€ {btw_amount:.2f}"],
        ['', 'TOTAAL INCL BTW', f"€ {total:.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[page_width*0.60, page_width*0.22, page_width*0.18])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), primary),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, 2), (-1, 2), 1.5, accent),
        ('BACKGROUND', (1, 2), (-1, 2), LIGHT_GREY),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 10*mm))

    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    footer_text = "Bedankt voor uw aanvraag. Deze offerte is vrijblijvend."
    if quote.get('valid_until'):
        footer_text += f" Geldig tot {quote['valid_until']}."
    if sender_email:
        footer_text += f" Bij vragen kunt u contact opnemen via {sender_email}."

    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER,
    )))

    doc.build(story)
    return buffer.getvalue()


# ─── Public quote endpoints (no auth — token-gated) ────────────
# These three endpoints power the recipient-facing landing page at
# https://bigdogg.nl/#/q/<share_token>. The token is an unguessable UUID
# stored on the quotes row; possession of the URL implies authorization
# to view and act on the quote.

def _public_quote_payload(quote: dict, lines: list, profile: dict) -> dict:
    """Return only the fields safe to expose to a non-authenticated client."""
    return {
        "quote_number":   quote.get("quote_number"),
        "quote_date":     quote.get("quote_date"),
        "valid_until":    quote.get("valid_until"),
        "status":         quote.get("status"),
        "subtotal_ex_btw": quote.get("subtotal_ex_btw"),
        "btw_amount":     quote.get("btw_amount"),
        "total_incl_btw": quote.get("total_incl_btw"),
        "notes":          quote.get("notes"),
        "client_name":    quote.get("client_name"),
        "client_company": quote.get("client_company"),
        "from_business":  profile.get("business_name") or profile.get("full_name") or "",
        "from_email":     profile.get("email") or "",
        "from_address":   profile.get("address"),
        "from_postcode":  profile.get("postcode"),
        "from_city":      profile.get("city"),
        "from_kvk":       profile.get("kvk_number"),
        "from_btw":       profile.get("btw_number"),
        "from_iban":      profile.get("iban"),
        "from_logo_url":  profile.get("logo_url"),
        "lines": [
            {
                "description":      l.get("description"),
                "quantity":         l.get("quantity"),
                "unit_price_ex_btw": l.get("unit_price_ex_btw"),
                "btw_rate":         l.get("btw_rate"),
                "line_total_ex_btw": l.get("line_total_ex_btw"),
                "unit":             l.get("unit"),
            }
            for l in lines
        ],
    }


def _lookup_quote_by_token(token: str) -> dict:
    quote_result = supabase.table("quotes")\
        .select("*").eq("share_token", token).limit(1).execute()
    if not quote_result.data:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote_result.data[0]


def _esc_html(value) -> str:
    s = '' if value is None else str(value)
    return (
        s.replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
         .replace('"', '&quot;')
    )


def _freelancer_notify_html(*, first_name: str,
                             client_name: str, quote_number: str,
                             total: str, accepted: bool) -> str:
    """Branded HTML body for the email to the freelancer when their
    client accepts or declines an offerte."""
    badge = "Geaccepteerd" if accepted else "Afgewezen"
    headline = (
        f"<strong>{_esc_html(client_name)}</strong> heeft je offerte "
        f"<strong>{_esc_html(quote_number)}</strong> "
        f"(€ {_esc_html(total)}) "
        + ("<strong style='color:#10B981;'>geaccepteerd</strong>."
           if accepted else
           "<strong style='color:#B91C1C;'>afgewezen</strong>.")
    )
    follow_up = (
        "Je kunt 'm nu in BigDogg met één tik omzetten naar een factuur."
        if accepted else
        "Geen zorgen — je kunt altijd een nieuwe offerte sturen."
    )
    cta_label = (
        "Open BigDogg" if accepted else "Nieuwe offerte maken"
    )
    return f"""<!DOCTYPE html>
<html lang="nl">
<body style="margin:0;padding:0;background:#F5F3EF;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#1B3A4B;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F3EF;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:12px;border:1px solid #E2DDD6;overflow:hidden;">
        <tr><td align="center" style="padding:28px 28px 18px 28px;background:#1B3A4B;">
          <img src="https://bigdogg.nl/icons/Icon-512.png" alt="BigDogg" width="64" height="64" style="display:block;border-radius:12px;"/>
          <h1 style="margin:12px 0 0 0;color:#C9A96E;font-size:22px;letter-spacing:-0.3px;font-weight:700;">BigDogg.</h1>
          <p style="margin:4px 0 0 0;color:#F5F3EF;font-size:12px;letter-spacing:1px;text-transform:uppercase;">Offerte {badge.lower()}</p>
        </td></tr>
        <tr><td style="padding:24px 28px 6px 28px;">
          <p style="margin:0 0 14px 0;font-size:15px;line-height:1.6;">Hoi {_esc_html(first_name)},</p>
          <p style="margin:0 0 16px 0;font-size:15px;line-height:1.6;">{headline}</p>
          <p style="margin:0 0 16px 0;font-size:14px;line-height:1.6;color:#4A6572;">{follow_up}</p>
        </td></tr>
        <tr><td align="center" style="padding:6px 28px 22px 28px;">
          <a href="https://bigdogg.nl/#/dashboard" style="display:inline-block;background:#1B3A4B;color:#ffffff;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;">{cta_label}</a>
        </td></tr>
        <tr><td style="padding:0 28px 24px 28px;border-top:1px solid #E2DDD6;">
          <p style="margin:14px 0 0 0;font-size:13px;line-height:1.6;color:#4A6572;">
            Met vriendelijke groet,<br>
            <strong>Team BigDogg</strong>
          </p>
        </td></tr>
      </table>
      <p style="margin:14px 0 0 0;font-size:11px;color:#9CA3AF;">Verzonden via BigDogg · bigdogg.nl</p>
    </td></tr>
  </table>
</body>
</html>"""


def _notify_freelancer(quote: dict, decision: str) -> None:
    """Email the freelancer (quote author) when the client accepts/declines."""
    if not settings.resend_api_key:
        return
    try:
        user_id = quote.get("user_id")
        # Auth user has the email
        try:
            user_resp = supabase.auth.admin.get_user_by_id(user_id)
            freelancer_email = (user_resp.user.email if user_resp and user_resp.user else "") or ""
        except Exception:
            freelancer_email = ""
        if not freelancer_email:
            return

        profile_result = supabase.table("user_profiles")\
            .select("business_name, full_name").eq("id", user_id).execute()
        profile = profile_result.data[0] if profile_result.data else {}
        sender_name = profile.get("business_name") or profile.get("full_name") or "BigDogg"
        first_name = (
            (profile.get("full_name") or "").strip().split()[0]
            if (profile.get("full_name") or "").strip()
            else sender_name.split()[0]
        )
        client_name = quote.get("client_name") or "je klant"
        quote_number = quote.get("quote_number") or "?"
        total = quote.get("total_incl_btw") or 0
        accepted = decision == "accepted"

        if accepted:
            subject = f"{client_name} heeft offerte {quote_number} geaccepteerd"
            text_body = (
                f"Hoi {first_name},\n\n"
                f"Goed nieuws — {client_name} heeft je offerte {quote_number} "
                f"(€ {total}) geaccepteerd.\n\n"
                f"Je kunt 'm nu in BigDogg met één tik omzetten naar een factuur.\n\n"
                f"Met vriendelijke groet,\nTeam BigDogg\n\n---\nbigdogg.nl"
            )
        else:
            subject = f"{client_name} heeft offerte {quote_number} afgewezen"
            text_body = (
                f"Hoi {first_name},\n\n"
                f"{client_name} heeft je offerte {quote_number} "
                f"(€ {total}) afgewezen.\n\n"
                f"Geen zorgen — je kunt altijd een nieuwe offerte sturen.\n\n"
                f"Met vriendelijke groet,\nTeam BigDogg\n\n---\nbigdogg.nl"
            )

        html_body = _freelancer_notify_html(
            first_name=first_name,
            client_name=client_name,
            quote_number=quote_number,
            total=str(total),
            accepted=accepted,
        )

        resend.api_key = settings.resend_api_key
        resend.Emails.send({
            "from": "BigDogg <info@bigdogg.nl>",
            "to": [freelancer_email],
            "subject": subject,
            "text": text_body,
            "html": html_body,
        })
    except Exception as e:
        # Don't let a missing notification break the accept/decline flow.
        print(f"[quotes] freelancer notification failed: {e}")


@router.get("/public/{token}")
async def public_quote(token: str):
    """Read-only quote view for the recipient landing page."""
    quote = _lookup_quote_by_token(token)
    lines_result = supabase.table("quote_lines")\
        .select("*").eq("quote_id", quote["id"]).execute()
    profile_result = supabase.table("user_profiles")\
        .select("*").eq("id", quote["user_id"]).execute()
    profile = profile_result.data[0] if profile_result.data else {}
    return _public_quote_payload(quote, lines_result.data or [], profile)


@router.post("/public/{token}/accept")
async def public_quote_accept(token: str):
    quote = _lookup_quote_by_token(token)
    if quote["status"] in ("accepted", "converted"):
        return {"success": True, "status": quote["status"], "already": True}
    if quote["status"] == "declined":
        raise HTTPException(status_code=409, detail="Deze offerte is al afgewezen.")
    supabase.table("quotes")\
        .update({
            "status": "accepted",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })\
        .eq("id", quote["id"]).execute()
    quote["status"] = "accepted"
    _notify_freelancer(quote, "accepted")
    from app.routers.notifications import create_notification
    create_notification(
        user_id=quote.get("user_id"),
        notification_type="quote_accepted",
        title="Offerte geaccepteerd 🎉",
        body=f"{quote.get('client_name') or 'Je klant'} heeft offerte {quote.get('quote_number')} geaccepteerd.",
        data={"quote_id": quote["id"], "quote_number": quote.get("quote_number")},
    )
    return {"success": True, "status": "accepted"}


@router.post("/public/{token}/decline")
async def public_quote_decline(token: str):
    quote = _lookup_quote_by_token(token)
    if quote["status"] == "declined":
        return {"success": True, "status": "declined", "already": True}
    if quote["status"] in ("accepted", "converted"):
        raise HTTPException(status_code=409, detail="Deze offerte is al geaccepteerd.")
    supabase.table("quotes")\
        .update({
            "status": "declined",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })\
        .eq("id", quote["id"]).execute()
    quote["status"] = "declined"
    _notify_freelancer(quote, "declined")
    from app.routers.notifications import create_notification
    create_notification(
        user_id=quote.get("user_id"),
        notification_type="quote_declined",
        title="Offerte afgewezen",
        body=f"{quote.get('client_name') or 'Je klant'} heeft offerte {quote.get('quote_number')} afgewezen.",
        data={"quote_id": quote["id"], "quote_number": quote.get("quote_number")},
    )
    return {"success": True, "status": "declined"}

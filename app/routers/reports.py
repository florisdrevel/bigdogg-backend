from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from datetime import date
from pydantic import BaseModel
from app.database import supabase
from app.routers.overview import get_quarter_dates, get_user_id
from app.routers.pdf import TEAL, GOLD, LIGHT_GREY, MID_GREY, TEXT_SECONDARY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
import io

router = APIRouter()


def compute_financials(user_id: str, start_date: str, end_date: str) -> dict:
    invoices = supabase.table("invoices").select("subtotal_ex_btw, btw_amount, btw_rate, total_incl_btw, status").eq("user_id", user_id).gte("invoice_date", start_date).lte("invoice_date", end_date).neq("status", "draft").execute()
    expenses = supabase.table("expenses").select("amount_ex_btw, btw_amount").eq("user_id", user_id).gte("expense_date", start_date).lte("expense_date", end_date).execute()
    # Split revenue by BTW rate: 1a = taxed (>0%), 3a = buitenland (0%)
    revenue_1a = sum(float(i["subtotal_ex_btw"] or 0) for i in invoices.data if float(i.get("btw_rate") or 0) > 0)
    revenue_3a = sum(float(i["subtotal_ex_btw"] or 0) for i in invoices.data if float(i.get("btw_rate") or 0) == 0)
    revenue_ex_btw = round(revenue_1a + revenue_3a, 2)
    revenue_btw = sum(float(i["btw_amount"] or 0) for i in invoices.data)
    expenses_ex_btw = sum(float(e["amount_ex_btw"] or 0) for e in expenses.data)
    expenses_btw = sum(float(e["btw_amount"] or 0) for e in expenses.data)
    return {
        "revenue_ex_btw": round(revenue_ex_btw, 2),
        "revenue_1a": round(revenue_1a, 2),
        "revenue_3a": round(revenue_3a, 2),
        "revenue_btw": round(revenue_btw, 2),
        "expenses_ex_btw": round(expenses_ex_btw, 2),
        "expenses_btw": round(expenses_btw, 2),
        "btw_to_pay": round(revenue_btw - expenses_btw, 2),
    }


def validate_token(token: str) -> str:
    try:
        user = supabase.auth.get_user(token)
        if not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user.user.id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_profile(user_id: str) -> dict:
    try:
        resp = (
            supabase.table("user_profiles")
            .select("*")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        return (resp.data or [{}])[0]
    except Exception:
        return {}


def _generate_btw_pdf(profile: dict, financials: dict, year: int, quarter: int) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    story = []

    page_width = A4[0] - 40*mm

    label_style  = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=8,  textColor=TEXT_SECONDARY, leading=12)
    value_style  = ParagraphStyle('Value', fontName='Helvetica',      fontSize=10, textColor=TEAL, leading=14)
    value_bold   = ParagraphStyle('VBold', fontName='Helvetica-Bold', fontSize=10, textColor=TEAL, leading=14)
    section_style = ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=12, textColor=TEAL, spaceBefore=4*mm, spaceAfter=3*mm)

    business_name = profile.get("business_name") or profile.get("full_name") or ""
    btw_number    = profile.get("btw_number") or "-"
    today_str     = date.today().strftime("%d-%m-%Y")

    q_starts = {1: "01 januari", 2: "01 april",   3: "01 juli",      4: "01 oktober"}
    q_ends   = {1: "31 maart",   2: "30 juni",     3: "30 september", 4: "31 december"}
    deadline_months = {1: "30 april", 2: "31 juli", 3: "31 oktober",  4: "31 januari"}
    deadline_year   = year if quarter < 4 else year + 1
    period_str   = f"{q_starts[quarter]} {year} — {q_ends[quarter]} {year}"
    deadline_str = f"{deadline_months[quarter]} {deadline_year}"

    # ── Header ────────────────────────────────────────────────────────────────
    name_len = len(business_name)
    name_font_size = 28 if name_len <= 15 else 22 if name_len <= 22 else 18 if name_len <= 30 else 14
    name_style   = ParagraphStyle('Name',   fontName='Helvetica-Bold', fontSize=name_font_size, textColor=TEAL)
    number_style = ParagraphStyle('Number', fontName='Helvetica-Bold', fontSize=14,             textColor=TEAL)

    header_data = [[
        Paragraph(business_name, name_style),
        Paragraph(f"BTW Aangifte Q{quarter} {year}", number_style),
    ]]
    header_table = Table(header_data, colWidths=[page_width * 0.6, page_width * 0.4])
    header_table.setStyle(TableStyle([
        ('ALIGN',  (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=3, color=GOLD, spaceAfter=5*mm))

    # ── Meta row ──────────────────────────────────────────────────────────────
    meta_data = [[
        [Paragraph("PERIODE",           label_style), Paragraph(period_str,   value_style)],
        [Paragraph("BTW-NUMMER",        label_style), Paragraph(btw_number,   value_style)],
        [Paragraph("AANGIFTE DEADLINE", label_style), Paragraph(deadline_str, value_bold)],
    ]]
    meta_table = Table(meta_data, colWidths=[page_width/3, page_width/3, page_width/3])
    meta_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(meta_table)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=5*mm))

    # ── Sectie 1: Omzet ───────────────────────────────────────────────────────
    story.append(Paragraph("Sectie 1 — Omzet binnenland", section_style))

    omzet_data = [
        ["Rubriek", "Omschrijving", "Omzet ex BTW", "VAT/BTW"],
        ["1a",
         'Leveringen/diensten belast met 21%\nVul dit in bij "Omzet" op belastingdienst.nl',
         f"\u20ac {financials['revenue_1a']:,.2f}",
         f"\u20ac {financials['revenue_btw']:,.2f}"],
        ["3a",
         'Leveringen/diensten buiten NL (0% BTW)\nBijv. export naar EU of buiten EU - geen BTW verschuldigd',
         f"\u20ac {financials['revenue_3a']:,.2f}",
         f"\u20ac 0,00"],
    ]
    omzet_table = Table(omzet_data, colWidths=[page_width*0.10, page_width*0.50, page_width*0.20, page_width*0.20])
    omzet_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [LIGHT_GREY]),
        ('ALIGN',         (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN',         (0, 0), (1, -1), 'LEFT'),
        ('TEXTCOLOR',     (0, 1), (-1, -1), TEAL),
        ('GRID',          (0, 0), (-1, -1), 0.5, MID_GREY),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(omzet_table)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<i>Rubriek 1a: Totale omzet exclusief BTW voor 21% diensten/producten. "
        "Rubriek 1b: Voor producten/diensten met 9% BTW (bijv. voedsel, boeken). "
        "Rubriek 3a: Leveringen buiten Nederland — geen BTW verschuldigd.</i>",
        ParagraphStyle('Exp1', fontName='Helvetica-Oblique', fontSize=8, textColor=TEXT_SECONDARY, leading=12)
    ))

    # ── Sectie 5: Voorbelasting ───────────────────────────────────────────────
    story.append(Paragraph("Sectie 5 — Voorbelasting (aftrekbare BTW)", section_style))

    voor_data = [
        ["Rubriek", "Omschrijving", "Bedrag"],
        ["5b",
         'Voorbelasting — BTW op zakelijke kosten\nVul dit in bij "Voorbelasting" op belastingdienst.nl',
         f"\u20ac {financials['expenses_btw']:,.2f}"],
    ]
    voor_table = Table(voor_data, colWidths=[page_width*0.10, page_width*0.70, page_width*0.20])
    voor_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [LIGHT_GREY]),
        ('ALIGN',         (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN',         (0, 0), (1, -1), 'LEFT'),
        ('TEXTCOLOR',     (0, 1), (-1, -1), TEAL),
        ('GRID',          (0, 0), (-1, -1), 0.5, MID_GREY),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(voor_table)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "<i>Rubriek 5b: BTW die jij hebt betaald op zakelijke inkopen en kosten. "
        "Dit bedrag mag je aftrekken van de BTW die je hebt ontvangen van klanten.</i>",
        ParagraphStyle('Exp2', fontName='Helvetica-Oblique', fontSize=8, textColor=TEXT_SECONDARY, leading=12)
    ))

    # ── Te betalen BTW ────────────────────────────────────────────────────────
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    btw_color = colors.HexColor('#CC2200') if financials['btw_to_pay'] > 0 else colors.HexColor('#166534')

    totals_data = [
        ["BTW ontvangen (1a)",         f"\u20ac {financials['revenue_btw']:,.2f}"],
        ["Aftrekbare BTW kosten (5b)", f"- \u20ac {financials['expenses_btw']:,.2f}"],
        ["Te betalen BTW",             f"\u20ac {financials['btw_to_pay']:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[page_width*0.70, page_width*0.30])
    totals_table.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME',      (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 1), 10),
        ('FONTSIZE',      (0, 2), (-1, 2), 13),
        ('TEXTCOLOR',     (0, 0), (-1, 1), TEAL),
        ('TEXTCOLOR',     (0, 2), (-1, 2), btw_color),
        ('ALIGN',         (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN',         (0, 0), (0, -1), 'LEFT'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE',     (0, 2), (-1, 2), 1.5, GOLD),
        ('BACKGROUND',    (0, 2), (-1, 2), LIGHT_GREY),
    ]))
    story.append(totals_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))
    story.append(Paragraph(
        f"Gegenereerd door BigDogg \u00b7 bigdogg.nl \u00b7 {today_str} \u00b7 "
        "Dit rapport is indicatief. Raadpleeg een belastingadviseur voor je definitieve BTW-aangifte.",
        ParagraphStyle('Footer', fontName='Helvetica', fontSize=8, textColor=TEXT_SECONDARY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buffer.getvalue()


@router.get("/btw/pdf")
async def download_btw_report(
    token: str = Query(...),
    quarter: int = Query(None),
    year: int = Query(None),
):
    user_id = validate_token(token)
    today = date.today()
    if year is None:
        year = today.year
    if quarter is None:
        quarter = (today.month - 1) // 3 + 1

    start_date, end_date = get_quarter_dates(year, quarter)
    financials = compute_financials(user_id, start_date, end_date)
    profile = get_profile(user_id)

    try:
        pdf_bytes = _generate_btw_pdf(profile, financials, year, quarter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="btw-aangifte-Q{quarter}-{year}.pdf"'
        },
    )


@router.get("/quarter-detail")
async def get_quarter_detail(
    request: Request,
    quarter: int = Query(..., ge=1, le=4),
    year: int = Query(...),
):
    user_id = get_user_id(request)
    start_date, end_date = get_quarter_dates(year, quarter)

    invoices_resp = (
        supabase.table("invoices")
        .select(
            "id, invoice_number, invoice_date, status, total_incl_btw, client_name, "
            "subtotal_ex_btw, btw_amount, pdf_url, clients(contact_name, company_name)"
        )
        .eq("user_id", user_id)
        .gte("invoice_date", start_date)
        .lte("invoice_date", end_date)
        .order("invoice_date", desc=True)
        .execute()
    )

    expenses_resp = (
        supabase.table("expenses")
        .select("id, description, category, expense_date, amount_ex_btw, btw_rate, receipt_url")
        .eq("user_id", user_id)
        .gte("expense_date", start_date)
        .lte("expense_date", end_date)
        .order("expense_date", desc=True)
        .execute()
    )

    invoices = invoices_resp.data or []
    expenses = expenses_resp.data or []

    for exp in expenses:
        amount_ex = float(exp.get("amount_ex_btw") or 0)
        rate = float(exp.get("btw_rate") or 0)
        exp["total_incl_btw"] = round(amount_ex * (1 + rate / 100), 2)
        exp["amount"] = round(amount_ex, 2)

    return {"invoices": invoices, "expenses": expenses}


class GenerateReportRequest(BaseModel):
    year: int
    lang: str = "nl"


@router.post("/annual/generate")
async def generate_annual_report_async(
    request: Request,
    body: GenerateReportRequest,
):
    return {"success": True, "message": "Report generation queued"}
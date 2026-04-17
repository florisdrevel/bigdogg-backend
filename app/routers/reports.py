from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from datetime import date
from pydantic import BaseModel
from app.database import supabase
from app.routers.overview import get_quarter_dates, get_user_id
from fpdf import FPDF

router = APIRouter()


def compute_financials(user_id: str, start_date: str, end_date: str) -> dict:
    invoices = supabase.table("invoices").select("subtotal_ex_btw, btw_amount, total_incl_btw, status").eq("user_id", user_id).gte("invoice_date", start_date).lte("invoice_date", end_date).neq("status", "draft").execute()
    expenses = supabase.table("expenses").select("amount_ex_btw, btw_amount").eq("user_id", user_id).gte("expense_date", start_date).lte("expense_date", end_date).execute()
    revenue_ex_btw = sum(i["subtotal_ex_btw"] for i in invoices.data)
    revenue_btw = sum(i["btw_amount"] for i in invoices.data)
    expenses_ex_btw = sum(e["amount_ex_btw"] for e in expenses.data)
    expenses_btw = sum(e["btw_amount"] for e in expenses.data)
    return {
        "revenue_ex_btw": round(revenue_ex_btw, 2),
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
            supabase.table("profiles")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return (resp.data or [{}])[0]
    except Exception:
        return {}


# ── Colours ───────────────────────────────────────────────────────────────────
TEAL   = (15, 76, 92)    # #0f4c5c
WHITE  = (255, 255, 255)
LIGHT  = (245, 245, 245)
RED    = (204, 34, 0)
GREY   = (100, 100, 100)
BLACK  = (26, 26, 26)


def _money(v: float) -> str:
    return f"EUR {v:,.2f}"


def _btw_pdf(profile: dict, financials: dict, year: int, quarter: int) -> bytes:
    business_name = profile.get("business_name") or profile.get("full_name", "") or "-"
    btw_number    = profile.get("btw_number") or "-"
    address       = profile.get("address", "")
    postcode      = profile.get("postcode", "")
    city          = profile.get("city", "")
    today_str     = date.today().strftime("%d-%m-%Y")
    period        = f"Q{quarter} {year}"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header bar
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(20, 8)
    pdf.cell(0, 10, "BTW Aangifte", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, 19)
    pdf.cell(0, 6, f"Periode: {period}", ln=True)

    # Business info
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(20, 36)
    pdf.cell(0, 6, business_name, ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    if address:
        pdf.set_x(20); pdf.cell(0, 5, f"{address}, {postcode} {city}", ln=True)
    pdf.set_x(20); pdf.cell(0, 5, f"BTW-nummer: {btw_number}", ln=True)
    pdf.set_x(20); pdf.cell(0, 5, f"Aangemaakt op: {today_str}", ln=True)

    pdf.ln(6)

    def section_header(title: str):
        pdf.set_fill_color(*TEAL)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(20)
        pdf.cell(170, 8, title, ln=True, fill=True)

    def row(label: str, value: str, highlight: bool = False):
        if highlight:
            pdf.set_fill_color(*RED)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 11)
        else:
            pdf.set_fill_color(*LIGHT)
            pdf.set_text_color(*BLACK)
            pdf.set_font("Helvetica", "", 10)
        pdf.set_x(20)
        pdf.cell(120, 7, label, fill=highlight, border="B")
        pdf.cell(50,  7, value, fill=highlight, border="B", align="R", ln=True)

    section_header("Omzet")
    row("Omzet ex BTW",   _money(financials["revenue_ex_btw"]))
    row("BTW ontvangen",  _money(financials["revenue_btw"]))
    pdf.ln(2)

    section_header("Kosten")
    row("Kosten ex BTW",          _money(financials["expenses_ex_btw"]))
    row("BTW betaald op kosten",  _money(financials["expenses_btw"]))
    pdf.ln(2)

    section_header("BTW Berekening")
    row("BTW ontvangen",        _money(financials["revenue_btw"]))
    row("Aftrekbare BTW (kosten)", _money(financials["expenses_btw"]))
    row("Te betalen BTW",       _money(financials["btw_to_pay"]), highlight=True)
    pdf.ln(8)

    # Footer
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GREY)
    pdf.set_x(20)
    pdf.multi_cell(170, 5,
        "Dit rapport is indicatief. Raadpleeg een belastingadviseur voor je definitieve BTW-aangifte.")

    return pdf.output()


def _annual_pdf(profile: dict, annual: dict, year: int) -> bytes:
    business_name = profile.get("business_name") or profile.get("full_name", "") or "-"
    btw_number    = profile.get("btw_number") or "-"
    kvk_number    = profile.get("kvk_number") or "-"
    address       = profile.get("address", "")
    postcode      = profile.get("postcode", "")
    city          = profile.get("city", "")
    today_str     = date.today().strftime("%d-%m-%Y")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)

    # Header bar
    pdf.set_fill_color(*TEAL)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(20, 8)
    pdf.cell(0, 10, f"Jaarrapport {year}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, 19)
    pdf.cell(0, 6, "Jaaroverzicht voor belastingaangifte", ln=True)

    # Business info
    pdf.set_text_color(*BLACK)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(20, 36)
    pdf.cell(0, 6, business_name, ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    if address:
        pdf.set_x(20); pdf.cell(0, 5, f"{address}, {postcode} {city}", ln=True)
    pdf.set_x(20); pdf.cell(0, 5, f"KVK-nummer: {kvk_number}", ln=True)
    pdf.set_x(20); pdf.cell(0, 5, f"BTW-nummer: {btw_number}", ln=True)
    pdf.set_x(20); pdf.cell(0, 5, f"Aangemaakt op: {today_str}", ln=True)

    pdf.ln(6)

    # Quarter table header
    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(20)
    col_w = [30, 38, 38, 32, 32]
    headers = ["Kwartaal", "Omzet ex BTW", "Kosten ex BTW", "Winst", "BTW"]
    for w, h in zip(col_w, headers):
        pdf.cell(w, 8, h, fill=True, border=0)
    pdf.ln()

    # Quarter rows
    pdf.set_font("Helvetica", "", 9)
    for i, q in enumerate(annual["quarters"]):
        profit = q["revenue_ex_btw"] - q["expenses_ex_btw"]
        fill = i % 2 == 0
        pdf.set_fill_color(248, 248, 248) if fill else pdf.set_fill_color(*WHITE)
        pdf.set_text_color(*BLACK)
        pdf.set_x(20)
        vals = [
            f"Q{q['quarter']} {year}",
            _money(q["revenue_ex_btw"]),
            _money(q["expenses_ex_btw"]),
            _money(profit),
            _money(q["btw_to_pay"]),
        ]
        for w, v in zip(col_w, vals):
            pdf.cell(w, 7, v, fill=fill, border="B")
        pdf.ln()

    # Totals row
    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(20)
    totals = [
        f"Totaal {year}",
        _money(annual["total_revenue_ex_btw"]),
        _money(annual["total_expenses_ex_btw"]),
        _money(annual["net_profit_indicative"]),
        _money(annual["total_btw_to_pay"]),
    ]
    for w, v in zip(col_w, totals):
        pdf.cell(w, 8, v, fill=True)
    pdf.ln(12)

    # Summary
    pdf.set_fill_color(*TEAL)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(20)
    pdf.cell(170, 8, "Samenvatting", fill=True, ln=True)

    def sum_row(label, value, highlight=False):
        if highlight:
            pdf.set_fill_color(232, 244, 247)
            pdf.set_text_color(*TEAL)
            pdf.set_font("Helvetica", "B", 11)
        else:
            pdf.set_fill_color(*LIGHT)
            pdf.set_text_color(*BLACK)
            pdf.set_font("Helvetica", "", 10)
        pdf.set_x(20)
        pdf.cell(120, 7, label, fill=highlight, border="B")
        pdf.cell(50,  7, value, fill=highlight, border="B", align="R", ln=True)

    sum_row("Totale omzet ex BTW",    _money(annual["total_revenue_ex_btw"]))
    sum_row("Totale kosten ex BTW",   _money(annual["total_expenses_ex_btw"]))
    sum_row("Totale BTW te betalen",  _money(annual["total_btw_to_pay"]))
    sum_row("Netto winst (indicatief)", _money(annual["net_profit_indicative"]), highlight=True)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GREY)
    pdf.set_x(20)
    pdf.multi_cell(170, 5,
        "Dit rapport is indicatief en berekend op basis van gefactureerde bedragen. "
        "Raadpleeg een belastingadviseur voor je definitieve belastingaangifte.")

    return pdf.output()


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
        pdf_bytes = _btw_pdf(profile, financials, year, quarter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return Response(
        content=bytes(pdf_bytes),
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
            "id, invoice_number, invoice_date, status, total_incl_btw, "
            "amount_ex_btw, btw_amount, pdf_url, clients(contact_name, company_name)"
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
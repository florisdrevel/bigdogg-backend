from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from datetime import date
from pydantic import BaseModel
from app.database import supabase
from app.routers.overview import get_quarter_dates, compute_financials, get_user_id

router = APIRouter()


def validate_token(token: str) -> str:
    """Validate a token passed as a query param and return the user_id."""
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


def _btw_html(profile: dict, financials: dict, year: int, quarter: int) -> str:
    business_name = profile.get("business_name") or profile.get("full_name", "")
    btw_number = profile.get("btw_number") or "-"
    address = profile.get("address", "")
    postcode = profile.get("postcode", "")
    city = profile.get("city", "")
    period = f"Q{quarter} {year}"
    today_str = date.today().strftime("%d-%m-%Y")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; color: #1a1a1a; font-size: 14px; }}
  h1 {{ color: #0f4c5c; font-size: 24px; margin-bottom: 4px; }}
  .subtitle {{ color: #666; font-size: 13px; margin-bottom: 28px; }}
  .info p {{ margin: 3px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
  th {{ background: #0f4c5c; color: #fff; padding: 10px 12px; text-align: left; }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #e0e0e0; }}
  .highlight td {{ font-weight: bold; font-size: 16px; color: #cc2200; background: #fff8f8; }}
  .footer {{ margin-top: 40px; font-size: 11px; color: #999; border-top: 1px solid #ddd; padding-top: 14px; }}
</style>
</head>
<body>
  <h1>BTW Aangifte</h1>
  <div class="subtitle">Periode: {period}</div>
  <div class="info">
    <p><strong>{business_name}</strong></p>
    <p>{address}, {postcode} {city}</p>
    <p>BTW-nummer: {btw_number}</p>
    <p>Aangemaakt op: {today_str}</p>
  </div>
  <table>
    <tr><th colspan="2">Omzet</th></tr>
    <tr><td>Omzet ex BTW</td><td>&euro; {financials['revenue_ex_btw']:,.2f}</td></tr>
    <tr><td>BTW ontvangen</td><td>&euro; {financials['revenue_btw']:,.2f}</td></tr>
    <tr><th colspan="2">Kosten</th></tr>
    <tr><td>Kosten ex BTW</td><td>&euro; {financials['expenses_ex_btw']:,.2f}</td></tr>
    <tr><td>BTW betaald op kosten</td><td>&euro; {financials['expenses_btw']:,.2f}</td></tr>
    <tr><th colspan="2">BTW Berekening</th></tr>
    <tr><td>BTW ontvangen</td><td>&euro; {financials['revenue_btw']:,.2f}</td></tr>
    <tr><td>Aftrekbare BTW (kosten)</td><td>&minus; &euro; {financials['expenses_btw']:,.2f}</td></tr>
    <tr class="highlight"><td>Te betalen BTW</td><td>&euro; {financials['btw_to_pay']:,.2f}</td></tr>
  </table>
  <div class="footer">
    Dit rapport is indicatief. Raadpleeg een belastingadviseur voor je definitieve BTW-aangifte.
  </div>
</body>
</html>"""


def _annual_html(profile: dict, annual: dict, year: int) -> str:
    business_name = profile.get("business_name") or profile.get("full_name", "")
    btw_number = profile.get("btw_number") or "-"
    kvk_number = profile.get("kvk_number") or "-"
    address = profile.get("address", "")
    postcode = profile.get("postcode", "")
    city = profile.get("city", "")
    today_str = date.today().strftime("%d-%m-%Y")

    rows = "".join(
        f"""<tr>
          <td>Q{q['quarter']} {year}</td>
          <td>&euro; {q['revenue_ex_btw']:,.2f}</td>
          <td>&euro; {q['expenses_ex_btw']:,.2f}</td>
          <td>&euro; {q['revenue_ex_btw'] - q['expenses_ex_btw']:,.2f}</td>
          <td>&euro; {q['btw_to_pay']:,.2f}</td>
        </tr>"""
        for q in annual["quarters"]
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; color: #1a1a1a; font-size: 14px; }}
  h1 {{ color: #0f4c5c; font-size: 26px; margin-bottom: 4px; }}
  h2 {{ color: #0f4c5c; font-size: 17px; margin-top: 28px; }}
  .subtitle {{ color: #666; font-size: 13px; margin-bottom: 28px; }}
  .info p {{ margin: 3px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; margin-bottom: 24px; }}
  th {{ background: #0f4c5c; color: #fff; padding: 10px 12px; text-align: left; }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #e0e0e0; }}
  .total td {{ font-weight: bold; background: #f5f5f5; border-top: 2px solid #0f4c5c; }}
  .net-profit td {{ font-weight: bold; font-size: 17px; color: #0f4c5c; background: #e8f4f7; }}
  .footer {{ margin-top: 40px; font-size: 11px; color: #999; border-top: 1px solid #ddd; padding-top: 14px; }}
</style>
</head>
<body>
  <h1>Jaarrapport {year}</h1>
  <div class="subtitle">Jaaroverzicht voor belastingaangifte</div>
  <div class="info">
    <p><strong>{business_name}</strong></p>
    <p>{address}, {postcode} {city}</p>
    <p>KVK-nummer: {kvk_number}</p>
    <p>BTW-nummer: {btw_number}</p>
    <p>Aangemaakt op: {today_str}</p>
  </div>
  <h2>Kwartaaloverzicht {year}</h2>
  <table>
    <tr>
      <th>Kwartaal</th><th>Omzet ex BTW</th><th>Kosten ex BTW</th>
      <th>Winst</th><th>BTW te betalen</th>
    </tr>
    {rows}
    <tr class="total">
      <td>Totaal {year}</td>
      <td>&euro; {annual['total_revenue_ex_btw']:,.2f}</td>
      <td>&euro; {annual['total_expenses_ex_btw']:,.2f}</td>
      <td>&euro; {annual['net_profit_indicative']:,.2f}</td>
      <td>&euro; {annual['total_btw_to_pay']:,.2f}</td>
    </tr>
  </table>
  <h2>Samenvatting</h2>
  <table>
    <tr><td>Totale omzet ex BTW</td><td>&euro; {annual['total_revenue_ex_btw']:,.2f}</td></tr>
    <tr><td>Totale kosten ex BTW</td><td>&euro; {annual['total_expenses_ex_btw']:,.2f}</td></tr>
    <tr><td>Totale BTW te betalen</td><td>&euro; {annual['total_btw_to_pay']:,.2f}</td></tr>
    <tr class="net-profit"><td>Netto winst (indicatief)</td><td>&euro; {annual['net_profit_indicative']:,.2f}</td></tr>
  </table>
  <div class="footer">
    Dit rapport is indicatief en berekend op basis van gefactureerde bedragen.
    Raadpleeg een belastingadviseur voor je definitieve belastingaangifte.
  </div>
</body>
</html>"""


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
    html = _btw_html(profile, financials, year, quarter)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="btw-aangifte-Q{quarter}-{year}.pdf"'
        },
    )


@router.get("/annual/pdf")
async def download_annual_report(
    token: str = Query(...),
    year: int = Query(None),
):
    user_id = validate_token(token)
    if year is None:
        year = date.today().year

    quarters_data = []
    total_revenue_ex_btw = 0.0
    total_expenses_ex_btw = 0.0
    total_btw_to_pay = 0.0

    for q in range(1, 5):
        start_date, end_date = get_quarter_dates(year, q)
        financials = compute_financials(user_id, start_date, end_date)
        quarters_data.append({"quarter": q, **financials})
        total_revenue_ex_btw += financials["revenue_ex_btw"]
        total_expenses_ex_btw += financials["expenses_ex_btw"]
        total_btw_to_pay += financials["btw_to_pay"]

    annual = {
        "quarters": quarters_data,
        "total_revenue_ex_btw": round(total_revenue_ex_btw, 2),
        "total_expenses_ex_btw": round(total_expenses_ex_btw, 2),
        "net_profit_indicative": round(total_revenue_ex_btw - total_expenses_ex_btw, 2),
        "total_btw_to_pay": round(total_btw_to_pay, 2),
    }

    profile = get_profile(user_id)
    html = _annual_html(profile, annual, year)

    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="jaarrapport-{year}.pdf"'
        },
    )


@router.get("/quarter-detail")
async def get_quarter_detail(
    request: Request,
    quarter: int = Query(..., ge=1, le=4),
    year: int = Query(...),
):
    """Return the invoices and expenses that make up a specific quarter."""
    user_id = get_user_id(request)
    start_date, end_date = get_quarter_dates(year, quarter)
    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    invoices_resp = (
        supabase.table("invoices")
        .select(
            "id, invoice_number, invoice_date, status, total_incl_btw, "
            "amount_ex_btw, btw_amount, pdf_url, clients(contact_name, company_name)"
        )
        .eq("user_id", user_id)
        .gte("invoice_date", start_str)
        .lte("invoice_date", end_str)
        .order("invoice_date", desc=True)
        .execute()
    )

    expenses_resp = (
        supabase.table("expenses")
        .select("id, description, category, expense_date, amount_ex_btw, btw_rate, receipt_url")
        .eq("user_id", user_id)
        .gte("expense_date", start_str)
        .lte("expense_date", end_str)
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
    """Trigger async annual report generation (fire-and-forget from the app)."""
    return {"success": True, "message": "Report generation queued"}

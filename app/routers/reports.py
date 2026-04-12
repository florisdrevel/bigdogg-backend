from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from app.database import supabase
from app.config import settings
from app.routers.pdf import TEAL, GOLD, LIGHT_GREY, MID_GREY, TEXT_SECONDARY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
from datetime import date, datetime
import resend
import base64
import io

router = APIRouter()
resend.api_key = settings.resend_api_key


def _t(nl, en, lang):
    return en if lang == 'en' else nl


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


def get_current_quarter():
    today = date.today()
    q = (today.month - 1) // 3 + 1
    year = today.year
    if q == 1:
        start = date(year, 1, 1)
        end = date(year, 3, 31)
    elif q == 2:
        start = date(year, 4, 1)
        end = date(year, 6, 30)
    elif q == 3:
        start = date(year, 7, 1)
        end = date(year, 9, 30)
    else:
        start = date(year, 10, 1)
        end = date(year, 12, 31)
    return q, year, start, end


def get_previous_quarter():
    today = date.today()
    q = (today.month - 1) // 3 + 1
    year = today.year
    if q == 1:
        return 4, year - 1, date(year - 1, 10, 1), date(year - 1, 12, 31)
    elif q == 2:
        return 1, year, date(year, 1, 1), date(year, 3, 31)
    elif q == 3:
        return 2, year, date(year, 4, 1), date(year, 6, 30)
    else:
        return 3, year, date(year, 7, 1), date(year, 9, 30)


def _get_deadline(quarter, year, lang='nl'):
    if lang == 'en':
        deadlines = {
            1: f"April 30, {year}",
            2: f"July 31, {year}",
            3: f"October 31, {year}",
            4: f"January 31, {year + 1}",
        }
    else:
        deadlines = {
            1: f"30 april {year}",
            2: f"31 juli {year}",
            3: f"31 oktober {year}",
            4: f"31 januari {year + 1}",
        }
    return deadlines.get(quarter, "—")


def _get_quarter_dates(quarter, year):
    if quarter == 1:
        return date(year, 1, 1), date(year, 3, 31)
    elif quarter == 2:
        return date(year, 4, 1), date(year, 6, 30)
    elif quarter == 3:
        return date(year, 7, 1), date(year, 9, 30)
    else:
        return date(year, 10, 1), date(year, 12, 31)


@router.get("/btw/pdf")
async def download_btw_report(
    request: Request,
    token: str = Query(None),
    quarter: int = Query(None),
    year: int = Query(None),
    lang: str = Query('nl'),
):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header:
        token = auth_header.replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if quarter and year:
        start, end = _get_quarter_dates(quarter, year)
    else:
        quarter, year, start, end = get_current_quarter()

    pdf_bytes = await _generate_btw_pdf(user_id, quarter, year, start, end, lang)

    filename = f"VAT-Return-Q{quarter}-{year}.pdf" if lang == 'en' else f"BTW-aangifte-Q{quarter}-{year}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


async def _generate_btw_pdf(user_id, quarter, year, start, end, lang='nl'):
    invoices_result = supabase.table("invoices")\
        .select("id, subtotal_ex_btw, btw_amount, status, invoice_date")\
        .eq("user_id", user_id)\
        .in_("status", ["paid", "sent", "overdue"])\
        .gte("invoice_date", start.isoformat())\
        .lte("invoice_date", end.isoformat())\
        .execute()

    invoice_ids = [inv['id'] for inv in invoices_result.data]

    lines_21 = []
    lines_9 = []
    lines_0 = []

    if invoice_ids:
        lines_result = supabase.table("invoice_lines")\
            .select("*")\
            .in_("invoice_id", invoice_ids)\
            .execute()

        for line in lines_result.data:
            rate = line.get('btw_rate', 21)
            if rate == 21:
                lines_21.append(line)
            elif rate == 9:
                lines_9.append(line)
            else:
                lines_0.append(line)

    rev_21_ex = sum(float(l['line_total_ex_btw'] or 0) for l in lines_21)
    rev_21_btw = sum(float(l['line_total_ex_btw'] or 0) * 0.21 for l in lines_21)
    rev_9_ex = sum(float(l['line_total_ex_btw'] or 0) for l in lines_9)
    rev_9_btw = sum(float(l['line_total_ex_btw'] or 0) * 0.09 for l in lines_9)
    rev_0_ex = sum(float(l['line_total_ex_btw'] or 0) for l in lines_0)

    revenue_btw_total = round(rev_21_btw + rev_9_btw, 2)

    expenses_result = supabase.table("expenses")\
        .select("*")\
        .eq("user_id", user_id)\
        .gte("expense_date", start.isoformat())\
        .lte("expense_date", end.isoformat())\
        .execute()

    expenses_btw = round(sum(float(exp.get('btw_amount') or 0) for exp in expenses_result.data), 2)
    btw_to_pay = round(revenue_btw_total - expenses_btw, 2)

    profile_result = supabase.table("user_profiles")\
        .select("*")\
        .eq("id", user_id)\
        .execute()
    profile = profile_result.data[0] if profile_result.data else {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    story = []

    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=9, textColor=TEXT_SECONDARY, leading=14)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=10, textColor=TEAL, leading=14)
    value_bold = ParagraphStyle('ValueBold', fontName='Helvetica-Bold', fontSize=11, textColor=TEAL, leading=14)
    section_style = ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=13, textColor=TEAL, spaceBefore=6*mm, spaceAfter=3*mm)
    explain_style = ParagraphStyle('Explain', fontName='Helvetica-Oblique', fontSize=9, textColor=TEXT_SECONDARY, leading=13)
    footer_style = ParagraphStyle('Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER)
    name_style = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=22, textColor=TEAL, spaceAfter=2*mm)
    number_style = ParagraphStyle('Number', fontName='Helvetica-Bold', fontSize=16, textColor=TEAL, spaceAfter=2*mm, alignment=1)

    page_width = A4[0] - 40*mm
    business_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
    btw_number = profile.get('btw_number') or '—'

    # Header
    report_title = _t(f"BTW Aangifte\nQ{quarter} {year}", f"VAT Return\nQ{quarter} {year}", lang)
    header_data = [[
        Paragraph(business_name, name_style),
        Paragraph(report_title, number_style),
    ]]
    header_table = Table(header_data, colWidths=[page_width * 0.6, page_width * 0.4])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width="100%", thickness=3, color=GOLD, spaceAfter=4*mm))

    # Meta
    meta_data = [[
        [Paragraph(_t('PERIODE', 'PERIOD', lang), label_style),
         Paragraph(f"{start.strftime('%d %B %Y')} — {end.strftime('%d %B %Y')}", value_style)],
        [Paragraph(_t('BTW-NUMMER', 'VAT NUMBER', lang), label_style),
         Paragraph(btw_number, value_style)],
        [Paragraph(_t('AANGIFTE DEADLINE', 'FILING DEADLINE', lang), label_style),
         Paragraph(_get_deadline(quarter, year, lang), value_style)],
    ]]
    meta_table = Table(meta_data, colWidths=[page_width/3, page_width/3, page_width/3])
    meta_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(meta_table)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    # Section 1
    story.append(Paragraph(
        _t("Sectie 1 — Omzet binnenland", "Section 1 — Domestic Revenue", lang),
        section_style
    ))

    rubriek_rows = [[
        _t('Rubriek', 'Field', lang),
        _t('Omschrijving', 'Description', lang),
        _t('Omzet ex BTW', 'Revenue ex VAT', lang),
        'VAT/BTW'
    ]]

    rubriek_rows.append([
        Paragraph('1a', value_bold),
        Paragraph(
            _t('Leveringen/diensten belast met 21%\nVul dit in bij "Omzet" op belastingdienst.nl',
               'Supplies/services taxed at 21%\nEnter this under "Revenue" on belastingdienst.nl', lang),
            value_style
        ),
        Paragraph(f"€ {rev_21_ex:,.2f}", value_bold),
        Paragraph(f"€ {rev_21_btw:,.2f}", value_bold),
    ])

    if rev_9_ex > 0:
        rubriek_rows.append([
            Paragraph('1b', value_bold),
            Paragraph(
                _t('Leveringen/diensten belast met 9%\nVul dit in bij "Omzet laag tarief" op belastingdienst.nl',
                   'Supplies/services taxed at 9%\nEnter this under "Low rate revenue" on belastingdienst.nl', lang),
                value_style
            ),
            Paragraph(f"€ {rev_9_ex:,.2f}", value_bold),
            Paragraph(f"€ {rev_9_btw:,.2f}", value_bold),
        ])

    if rev_0_ex > 0:
        rubriek_rows.append([
            Paragraph('3a', value_bold),
            Paragraph(
                _t('Leveringen/diensten buiten NL (0% BTW)\nBijv. export naar EU of buiten EU — geen BTW verschuldigd',
                   'Supplies/services outside NL (0% VAT)\nE.g. export to EU or outside EU — no VAT due', lang),
                value_style
            ),
            Paragraph(f"€ {rev_0_ex:,.2f}", value_bold),
            Paragraph('€ 0,00', value_bold),
        ])

    r_table = Table(rubriek_rows, colWidths=[page_width*0.10, page_width*0.48, page_width*0.21, page_width*0.21])
    r_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(r_table)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        _t(
            "💡 Rubriek 1a: Totale omzet exclusief BTW voor 21% diensten/producten. "
            "Rubriek 1b: Voor producten/diensten met 9% BTW (bijv. voedsel, boeken). "
            "Rubriek 3a: Leveringen buiten Nederland — geen BTW verschuldigd.",
            "💡 Field 1a: Total revenue excluding VAT for 21% services/products. "
            "Field 1b: For products/services at 9% VAT (e.g. food, books). "
            "Field 3a: Supplies outside the Netherlands — no VAT due.",
            lang
        ),
        explain_style
    ))

    # Section 5
    story.append(Paragraph(
        _t("Sectie 5 — Voorbelasting (aftrekbare BTW)", "Section 5 — Input Tax (deductible VAT)", lang),
        section_style
    ))

    v_rows = [
        [_t('Rubriek', 'Field', lang), _t('Omschrijving', 'Description', lang), _t('Bedrag', 'Amount', lang)],
        [
            Paragraph('5b', value_bold),
            Paragraph(
                _t(
                    'Voorbelasting — BTW op zakelijke kosten\nVul dit in bij "Voorbelasting" op belastingdienst.nl',
                    'Input tax — VAT on business expenses\nEnter this under "Input tax" on belastingdienst.nl',
                    lang
                ),
                value_style
            ),
            Paragraph(f"€ {expenses_btw:,.2f}", value_bold),
        ],
    ]

    v_table = Table(v_rows, colWidths=[page_width*0.10, page_width*0.68, page_width*0.22])
    v_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY]),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(v_table)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        _t(
            "💡 Rubriek 5b: BTW die jij hebt betaald op zakelijke inkopen en kosten. "
            "Dit bedrag mag je aftrekken van de BTW die je hebt ontvangen van klanten.",
            "💡 Field 5b: VAT you paid on business purchases and costs. "
            "You can deduct this from the VAT you received from clients.",
            lang
        ),
        explain_style
    ))

    # Summary
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))
    story.append(Paragraph(
        _t("Te betalen / te ontvangen BTW", "VAT payable / receivable", lang),
        section_style
    ))

    color_btw = colors.HexColor('#DC2626') if btw_to_pay > 0 else colors.HexColor('#16A34A')
    if lang == 'en':
        label_btw = "Payable to Tax Authority" if btw_to_pay > 0 else "Receivable from Tax Authority"
    else:
        label_btw = "Te betalen aan Belastingdienst" if btw_to_pay > 0 else "Te ontvangen van Belastingdienst"

    summary_rows = [
        [_t('BTW ontvangen (1a + 1b)', 'VAT received (1a + 1b)', lang), f"€ {revenue_btw_total:,.2f}"],
        [_t('Voorbelasting (5b)', 'Input tax (5b)', lang), f"- € {expenses_btw:,.2f}"],
        [label_btw, f"€ {abs(btw_to_pay):,.2f}"],
    ]

    sum_table = Table(summary_rows, colWidths=[page_width*0.65, page_width*0.35])
    sum_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 11),
        ('FONTSIZE', (0, 2), (-1, 2), 13),
        ('TEXTCOLOR', (0, 0), (-1, 1), TEAL),
        ('TEXTCOLOR', (0, 2), (-1, 2), color_btw),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, 2), (-1, 2), 1.5, GOLD),
        ('BACKGROUND', (0, 2), (-1, 2), LIGHT_GREY),
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        _t(
            "💡 Dit is het bedrag dat je invult bij 'Te betalen' of 'Te ontvangen' op belastingdienst.nl. "
            "Zorg dat je de aangifte op tijd indient. De deadline is " + _get_deadline(quarter, year, lang) + ".",
            "💡 This is the amount you enter under 'Payable' or 'Receivable' on belastingdienst.nl. "
            "Make sure to file on time. The deadline is " + _get_deadline(quarter, year, lang) + ".",
            lang
        ),
        explain_style
    ))

    # Footer
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))
    story.append(Paragraph(
        _t(
            f"Gegenereerd door BigDogg · bigdogg.nl · {datetime.now().strftime('%d-%m-%Y')} · "
            "Dit rapport is indicatief. Raadpleeg een belastingadviseur bij twijfel.",
            f"Generated by BigDogg · bigdogg.nl · {datetime.now().strftime('%d-%m-%Y')} · "
            "This report is indicative. Consult a tax advisor if in doubt.",
            lang
        ),
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()


@router.post("/cron/quarterly")
async def send_quarterly_reports(request: Request):
    auth = request.headers.get("x-cron-secret", "")
    if auth != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    quarter, year, start, end = get_previous_quarter()
    users = supabase.auth.admin.list_users()

    sent = 0
    for user in users:
        try:
            user_id = user.id
            email = user.email
            if not email:
                continue

            profile_result = supabase.table("user_profiles")\
                .select("*")\
                .eq("id", user_id)\
                .execute()
            profile = profile_result.data[0] if profile_result.data else {}
            name = profile.get('full_name') or email

            pdf_bytes = await _generate_btw_pdf(user_id, quarter, year, start, end, 'nl')
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

            resend.Emails.send({
                "from": "BigDogg <info@bigdogg.nl>",
                "to": [email],
                "subject": f"Je BTW aangifte Q{quarter} {year} staat klaar",
                "text": f"""Hallo {name},

Je BTW aangifte voor Q{quarter} {year} is klaar.

Je vindt het rapport als bijlage in deze e-mail.
Je kunt het ook downloaden via het Overzicht in de app.

De aangifte deadline is {_get_deadline(quarter, year, 'nl')}.

Log in op bigdogg.nl voor meer details.

Met vriendelijke groet,
Team BigDogg

---
bigdogg.nl
""",
                "attachments": [{
                    "filename": f"BTW-aangifte-Q{quarter}-{year}.pdf",
                    "content": pdf_b64,
                }]
            })
            sent += 1
        except Exception as e:
            print(f"Error sending to {user.email}: {e}")

    return {"sent": sent, "quarter": quarter, "year": year}
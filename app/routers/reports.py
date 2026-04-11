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
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import date, datetime, timezone
import resend
import io

router = APIRouter()
resend.api_key = settings.resend_api_key


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
        return 4, year - 1, date(year - 1, 10, 1), date(year - 1, 12, 31)
    elif q == 2:
        return 1, year, date(year, 1, 1), date(year, 3, 31)
    elif q == 3:
        return 2, year, date(year, 4, 1), date(year, 6, 30)
    else:
        return 3, year, date(year, 7, 1), date(year, 9, 30)


@router.get("/btw/pdf")
async def download_btw_report(request: Request, token: str = Query(None)):
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

    quarter, year, start, end = get_current_quarter()
    pdf_bytes = await _generate_btw_pdf(user_id, quarter, year, start, end)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=BTW-aangifte-Q{quarter}-{year}.pdf"
        }
    )


async def _generate_btw_pdf(user_id, quarter, year, start, end):
    # Get invoices for period
    invoices = supabase.table("invoices")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("status", "paid")\
        .gte("invoice_date", start.isoformat())\
        .lte("invoice_date", end.isoformat())\
        .execute()

    # Get expenses for period
    expenses = supabase.table("expenses")\
        .select("*")\
        .eq("user_id", user_id)\
        .gte("expense_date", start.isoformat())\
        .lte("expense_date", end.isoformat())\
        .execute()

    # Get profile
    profile_result = supabase.table("user_profiles")\
        .select("*")\
        .eq("id", user_id)\
        .execute()
    profile = profile_result.data[0] if profile_result.data else {}

    # Calculate totals
    revenue_ex_btw = sum(float(inv['subtotal_ex_btw'] or 0) for inv in invoices.data)
    revenue_btw = sum(float(inv['btw_amount'] or 0) for inv in invoices.data)
    expenses_btw = sum(float(exp['btw_amount'] or 0) for exp in expenses.data)
    btw_to_pay = round(revenue_btw - expenses_btw, 2)

    # Split by BTW rate
    btw_21 = sum(float(inv['subtotal_ex_btw'] or 0) for inv in invoices.data)
    btw_21_amount = sum(float(inv['btw_amount'] or 0) for inv in invoices.data)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    story = []

    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=22, textColor=TEAL, spaceAfter=2*mm)
    subtitle_style = ParagraphStyle('Sub', fontName='Helvetica', fontSize=10, textColor=TEXT_SECONDARY, spaceAfter=1*mm)
    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=9, textColor=TEXT_SECONDARY, leading=14)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=10, textColor=TEAL, leading=14)
    value_bold = ParagraphStyle('ValueBold', fontName='Helvetica-Bold', fontSize=11, textColor=TEAL, leading=14)
    section_style = ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=13, textColor=TEAL, spaceBefore=6*mm, spaceAfter=3*mm)
    explain_style = ParagraphStyle('Explain', fontName='Helvetica-Oblique', fontSize=9, textColor=TEXT_SECONDARY, leading=13)
    footer_style = ParagraphStyle('Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER)

    page_width = A4[0] - 40*mm

    business_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
    btw_number = profile.get('btw_number') or '—'

    # Header
    header_data = [[
        Paragraph(business_name, title_style),
        Paragraph(f"BTW Aangifte\nQ{quarter} {year}", ParagraphStyle('Right', fontName='Helvetica-Bold', fontSize=16, textColor=TEAL, alignment=1)),
    ]]
    header_table = Table(header_data, colWidths=[page_width * 0.6, page_width * 0.4])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width="100%", thickness=3, color=GOLD, spaceAfter=4*mm))

    # Meta info
    meta_data = [[
        [Paragraph('PERIODE', label_style),
         Paragraph(f"{start.strftime('%d %B %Y')} — {end.strftime('%d %B %Y')}", value_style)],
        [Paragraph('BTW-NUMMER', label_style),
         Paragraph(btw_number, value_style)],
        [Paragraph('AANGIFTE DEADLINE', label_style),
         Paragraph(_get_deadline(quarter, year), value_style)],
    ]]
    meta_table = Table(meta_data, colWidths=[page_width/3, page_width/3, page_width/3])
    meta_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(meta_table)
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    # Section 1: Omzet
    story.append(Paragraph("Sectie 1 — Omzet binnenland", section_style))

    rubriek_data = [
        ['Rubriek', 'Omschrijving', 'Bedrag', 'BTW'],
        [
            Paragraph('1a', value_bold),
            Paragraph(
                'Leveringen/diensten belast met 21%\n'
                'Vul dit in bij "Omzet" op belastingdienst.nl',
                value_style
            ),
            Paragraph(f"€ {revenue_ex_btw:,.2f}", value_bold),
            Paragraph(f"€ {btw_21_amount:,.2f}", value_bold),
        ],
    ]

    r_table = Table(rubriek_data, colWidths=[page_width*0.10, page_width*0.50, page_width*0.20, page_width*0.20])
    r_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY]),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(r_table)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "💡 Rubriek 1a: Dit is je totale omzet exclusief BTW voor diensten/producten belast met 21%. "
        "Op de aangifte vul je bij 'omzet' het bedrag in de linkerkolom in en de BTW in de rechterkolom.",
        explain_style
    ))

    # Section 5: Voorbelasting
    story.append(Paragraph("Sectie 5 — Voorbelasting (aftrekbare BTW)", section_style))

    voorbelasting_data = [
        ['Rubriek', 'Omschrijving', 'Bedrag'],
        [
            Paragraph('5b', value_bold),
            Paragraph(
                'Voorbelasting — BTW op zakelijke kosten\n'
                'Vul dit in bij "Voorbelasting" op belastingdienst.nl',
                value_style
            ),
            Paragraph(f"€ {expenses_btw:,.2f}", value_bold),
        ],
    ]

    v_table = Table(voorbelasting_data, colWidths=[page_width*0.10, page_width*0.70, page_width*0.20])
    v_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY]),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(v_table)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "💡 Rubriek 5b: Dit is de BTW die jij hebt betaald op zakelijke inkopen en kosten. "
        "Dit bedrag mag je aftrekken van de BTW die je hebt ontvangen.",
        explain_style
    ))

    # Summary box
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))
    story.append(Paragraph("Te betalen / te ontvangen BTW", section_style))

    color_btw = colors.HexColor('#DC2626') if btw_to_pay > 0 else colors.HexColor('#16A34A')
    label_btw = "Te betalen aan Belastingdienst" if btw_to_pay > 0 else "Te ontvangen van Belastingdienst"

    summary_data = [
        ['BTW ontvangen (1a)', f"€ {revenue_btw:,.2f}"],
        ['Voorbelasting (5b)', f"- € {expenses_btw:,.2f}"],
        [label_btw, f"€ {abs(btw_to_pay):,.2f}"],
    ]

    sum_table = Table(summary_data, colWidths=[page_width*0.65, page_width*0.35])
    sum_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (-1, 1), TEAL),
        ('TEXTCOLOR', (0, 2), (-1, 2), color_btw),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, 2), (-1, 2), 1.5, GOLD),
        ('BACKGROUND', (0, 2), (-1, 2), LIGHT_GREY),
        ('FONTSIZE', (0, 2), (-1, 2), 13),
    ]))
    story.append(sum_table)

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        "💡 Dit is het bedrag dat je invult bij 'Te betalen' of 'Te ontvangen' op belastingdienst.nl. "
        "Zorg dat je de aangifte op tijd indient om boetes te voorkomen.",
        explain_style
    ))

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))
    story.append(Paragraph(
        f"Gegenereerd door BigDogg · bigdogg.nl · {datetime.now().strftime('%d-%m-%Y')} · "
        "Dit rapport is indicatief. Raadpleeg een belastingadviseur bij twijfel.",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()


def _get_deadline(quarter, year):
    deadlines = {
        1: f"30 april {year}",
        2: f"31 juli {year}",
        3: f"31 oktober {year}",
        4: f"31 januari {year + 1}",
    }
    return deadlines.get(quarter, "—")


@router.post("/cron/quarterly")
async def send_quarterly_reports(request: Request):
    # Simple security check
    auth = request.headers.get("x-cron-secret", "")
    if auth != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    quarter, year, start, end = get_current_quarter()

    # Get all users with subscriptions
    users = supabase.auth.admin.list_users()

    sent = 0
    for user in users:
        try:
            user_id = user.id
            email = user.email

            profile_result = supabase.table("user_profiles")\
                .select("*")\
                .eq("id", user_id)\
                .execute()
            profile = profile_result.data[0] if profile_result.data else {}
            name = profile.get('full_name') or email

            pdf_bytes = await _generate_btw_pdf(user_id, quarter, year, start, end)

            import base64
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

            resend.Emails.send({
                "from": "BigDogg <info@bigdogg.nl>",
                "to": [email],
                "subject": f"Je BTW aangifte Q{quarter} {year} staat klaar",
                "text": f"""Hallo {name},

Je BTW aangifte voor Q{quarter} {year} is klaar.

Je vindt het rapport als bijlage in deze e-mail.

De aangifte deadline is {_get_deadline(quarter, year)}.

Log in op bigdogg.nl om je overzicht te bekijken en het rapport opnieuw te downloaden.

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
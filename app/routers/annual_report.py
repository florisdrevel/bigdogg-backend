from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from app.database import supabase
from app.config import settings
from app.routers.pdf import TEAL, GOLD, LIGHT_GREY, MID_GREY, TEXT_SECONDARY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import date, datetime
import anthropic
import resend
import base64
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


def get_year_data(user_id: str, year: int):
    quarters = []
    for q in range(1, 5):
        if q == 1:
            start, end = f"{year}-01-01", f"{year}-03-31"
        elif q == 2:
            start, end = f"{year}-04-01", f"{year}-06-30"
        elif q == 3:
            start, end = f"{year}-07-01", f"{year}-09-30"
        else:
            start, end = f"{year}-10-01", f"{year}-12-31"

        invoices = supabase.table("invoices")\
            .select("subtotal_ex_btw, btw_amount, total_incl_btw, status")\
            .eq("user_id", user_id)\
            .gte("invoice_date", start)\
            .lte("invoice_date", end)\
            .neq("status", "draft")\
            .execute()

        expenses = supabase.table("expenses")\
            .select("amount_ex_btw, btw_amount, category")\
            .eq("user_id", user_id)\
            .gte("expense_date", start)\
            .lte("expense_date", end)\
            .execute()

        rev_ex = round(sum(float(i["subtotal_ex_btw"] or 0) for i in invoices.data), 2)
        rev_btw = round(sum(float(i["btw_amount"] or 0) for i in invoices.data), 2)
        exp_ex = round(sum(float(e["amount_ex_btw"] or 0) for e in expenses.data), 2)
        exp_btw = round(sum(float(e["btw_amount"] or 0) for e in expenses.data), 2)

        quarters.append({
            "quarter": q,
            "revenue_ex_btw": rev_ex,
            "revenue_btw": rev_btw,
            "expenses_ex_btw": exp_ex,
            "expenses_btw": exp_btw,
            "profit": round(rev_ex - exp_ex, 2),
            "btw_to_pay": round(rev_btw - exp_btw, 2),
            "invoice_count": len(invoices.data),
        })

    # Expense categories
    all_expenses = supabase.table("expenses")\
        .select("amount_ex_btw, category")\
        .eq("user_id", user_id)\
        .gte("expense_date", f"{year}-01-01")\
        .lte("expense_date", f"{year}-12-31")\
        .execute()

    category_totals = {}
    for exp in all_expenses.data:
        cat = exp.get('category', 'general')
        category_totals[cat] = category_totals.get(cat, 0) + float(exp['amount_ex_btw'] or 0)

    total_rev = sum(q['revenue_ex_btw'] for q in quarters)
    total_exp = sum(q['expenses_ex_btw'] for q in quarters)
    total_btw = sum(q['btw_to_pay'] for q in quarters)
    total_profit = round(total_rev - total_exp, 2)

    return {
        "year": year,
        "quarters": quarters,
        "total_revenue": round(total_rev, 2),
        "total_expenses": round(total_exp, 2),
        "total_btw": round(total_btw, 2),
        "total_profit": total_profit,
        "category_totals": category_totals,
        "invoice_count": sum(q['invoice_count'] for q in quarters),
    }


async def get_ai_tax_tips(data_current, data_prev, profile):
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = f"""Je bent een Nederlandse belastingadviseur gespecialiseerd in ZZP'ers.
Geef op basis van de financiële cijfers hieronder 5-6 concrete, persoonlijke belastingtips voor deze ZZP'er.
Focus op legale aftrekposten, IB aangifte tips, en vergelijkingen met het vorige jaar.
Schrijf in het Nederlands. Wees concreet en noem specifieke bedragen waar mogelijk.
Geef geen juridisch advies maar praktische tips.

Jaar {data_current['year']}:
- Omzet: €{data_current['total_revenue']}
- Kosten: €{data_current['total_expenses']}
- Winst: €{data_current['total_profit']}
- Totale BTW: €{data_current['total_btw']}
- Aantal facturen: {data_current['invoice_count']}
- Kostencategorieën: {data_current['category_totals']}

Jaar {data_prev['year']}:
- Omzet: €{data_prev['total_revenue']}
- Winst: €{data_prev['total_profit']}

Naam: {profile.get('full_name', 'ZZP\'er')}
KVK: {profile.get('kvk_number', 'onbekend')}

Geef de tips als een genummerde lijst (1. 2. 3. etc.), elk tip op een nieuwe regel.
Maximaal 800 woorden totaal."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def _generate_annual_pdf(data_current, data_prev, profile, tax_tips, sender_email=''):
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
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=10, textColor=TEAL, leading=15)
    tip_style = ParagraphStyle('Tip', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, leading=14, leftIndent=4*mm)
    footer_style = ParagraphStyle('Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER)
    name_style = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=20, textColor=TEAL)
    number_style = ParagraphStyle('Number', fontName='Helvetica-Bold', fontSize=14, textColor=TEAL, alignment=1)

    page_width = A4[0] - 40*mm
    business_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
    year = data_current['year']

    # Header
    header_data = [[
        Paragraph(business_name, name_style),
        Paragraph(f"Jaarrapport {year}\nInkomstenbelasting", number_style),
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
        [Paragraph('NAAM', label_style),
         Paragraph(profile.get('full_name', '—'), value_style)],
        [Paragraph('KVK', label_style),
         Paragraph(profile.get('kvk_number', '—'), value_style)],
        [Paragraph('AANGIFTE PERIODE', label_style),
         Paragraph(f"1 maart — 30 april {year + 1}", value_style)],
    ]]
    meta_table = Table(meta_data, colWidths=[page_width/3, page_width/3, page_width/3])
    meta_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(meta_table)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    # Year summary
    story.append(Paragraph(f"Jaaroverzicht {year}", section_style))

    GREEN = colors.HexColor('#16A34A')
    RED = colors.HexColor('#DC2626')

    summary_rows = [
        ['', f'{year}', f'{data_prev["year"]}', 'Verschil'],
        ['Omzet ex BTW',
         f"€ {data_current['total_revenue']:,.2f}",
         f"€ {data_prev['total_revenue']:,.2f}",
         _diff(data_current['total_revenue'], data_prev['total_revenue'])],
        ['Kosten ex BTW',
         f"€ {data_current['total_expenses']:,.2f}",
         f"€ {data_prev['total_expenses']:,.2f}",
         _diff(data_current['total_expenses'], data_prev['total_expenses'])],
        ['Winst (indicatief)',
         f"€ {data_current['total_profit']:,.2f}",
         f"€ {data_prev['total_profit']:,.2f}",
         _diff(data_current['total_profit'], data_prev['total_profit'])],
        ['Totale BTW',
         f"€ {data_current['total_btw']:,.2f}",
         f"€ {data_prev['total_btw']:,.2f}",
         _diff(data_current['total_btw'], data_prev['total_btw'])],
    ]

    sum_table = Table(summary_rows, colWidths=[page_width*0.35, page_width*0.22, page_width*0.22, page_width*0.21])
    sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEAL),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F0FDF4')),
    ]))
    story.append(sum_table)

    # Quarter breakdown
    story.append(Paragraph(f"Kwartaaloverzicht {year}", section_style))

    q_rows = [['Kwartaal', 'Omzet', 'Kosten', 'Winst', 'BTW']]
    for q in data_current['quarters']:
        q_rows.append([
            f"Q{q['quarter']}",
            f"€ {q['revenue_ex_btw']:,.2f}",
            f"€ {q['expenses_ex_btw']:,.2f}",
            f"€ {q['profit']:,.2f}",
            f"€ {q['btw_to_pay']:,.2f}",
        ])

    q_table = Table(q_rows, colWidths=[page_width*0.12, page_width*0.22, page_width*0.22, page_width*0.22, page_width*0.22])
    q_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEAL),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(q_table)

    # Expense categories
    if data_current['category_totals']:
        story.append(Paragraph("Kostenverdeling", section_style))
        cat_labels = {
            'travel': 'Reizen', 'materials': 'Materialen', 'software': 'Software',
            'food': 'Eten & Drinken', 'office': 'Kantoor', 'other': 'Overig', 'general': 'Algemeen'
        }
        cat_rows = [['Categorie', 'Bedrag ex BTW', '% van totaal']]
        total_exp = data_current['total_expenses'] or 1
        for cat, amount in sorted(data_current['category_totals'].items(), key=lambda x: x[1], reverse=True):
            pct = round(amount / total_exp * 100, 1)
            cat_rows.append([
                cat_labels.get(cat, cat.title()),
                f"€ {amount:,.2f}",
                f"{pct}%",
            ])

        cat_table = Table(cat_rows, colWidths=[page_width*0.50, page_width*0.30, page_width*0.20])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TEAL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('TEXTCOLOR', (0, 1), (-1, -1), TEAL),
            ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
        ]))
        story.append(cat_table)

    # IB aangifte guidance
    story.append(Paragraph("IB Aangifte — Wat invullen?", section_style))
    ib_data = [
        ['Rubriek', 'Omschrijving', 'Jouw bedrag'],
        ['Omzet', 'Totale omzet exclusief BTW', f"€ {data_current['total_revenue']:,.2f}"],
        ['Kosten', 'Zakelijke kosten exclusief BTW', f"€ {data_current['total_expenses']:,.2f}"],
        ['Winst', 'Omzet minus kosten (winst uit onderneming)', f"€ {data_current['total_profit']:,.2f}"],
    ]
    ib_table = Table(ib_data, colWidths=[page_width*0.25, page_width*0.50, page_width*0.25])
    ib_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_GREY, colors.white]),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 1), (-1, -1), TEAL),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 3), (-1, 3), LIGHT_GREY),
    ]))
    story.append(ib_table)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "💡 Vul de winst in bij 'Winst uit onderneming' in je IB aangifte op belastingdienst.nl. "
        "Vergeet niet de zelfstandigenaftrek (€5.030 in 2026) en eventuele MKB-winstvrijstelling (14%) toe te passen.",
        ParagraphStyle('Explain', fontName='Helvetica-Oblique', fontSize=9, textColor=TEXT_SECONDARY, leading=13)
    ))

    # AI Tax tips
    story.append(Paragraph("Persoonlijke belastingtips voor jou", section_style))
    story.append(Paragraph(
        "Op basis van jouw cijfers heeft BigDogg de volgende tips voor je:",
        body_style
    ))
    story.append(Spacer(1, 3*mm))

    for line in tax_tips.split('\n'):
        line = line.strip()
        if line:
            story.append(Paragraph(line, tip_style))
            story.append(Spacer(1, 2*mm))

    # Footer
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))
    story.append(Paragraph(
        f"Gegenereerd door BigDogg · bigdogg.nl · {datetime.now().strftime('%d-%m-%Y')} · "
        "Dit rapport is indicatief. Raadpleeg een belastingadviseur voor je definitieve aangifte inkomstenbelasting.",
        footer_style
    ))

    doc.build(story)
    return buffer.getvalue()


def _diff(current, prev):
    if prev == 0:
        return '—'
    diff = current - prev
    pct = round(diff / prev * 100, 1)
    sign = '+' if diff >= 0 else ''
    return f"{sign}{pct}%"


@router.get("/annual/pdf")
async def download_annual_report(
    request: Request,
    token: str = Query(None),
    year: int = Query(None)
):
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header:
        token = auth_header.replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Authorization required")
    try:
        user = supabase.auth.get_user(token)
        user_id = user.user.id
        sender_email = user.user.email or ''
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not year:
        year = datetime.now().year - 1

    profile_result = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
    profile = profile_result.data[0] if profile_result.data else {}

    data_current = get_year_data(user_id, year)
    data_prev = get_year_data(user_id, year - 1)
    tax_tips = await get_ai_tax_tips(data_current, data_prev, profile)
    pdf_bytes = _generate_annual_pdf(data_current, data_prev, profile, tax_tips, sender_email)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Jaarrapport-{year}.pdf"
        }
    )


@router.post("/cron/annual")
async def send_annual_reports(request: Request):
    auth = request.headers.get("x-cron-secret", "")
    if auth != settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    year = datetime.now().year - 1
    users = supabase.auth.admin.list_users()

    sent = 0
    for user in users:
        try:
            user_id = user.id
            email = user.email
            if not email:
                continue

            profile_result = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
            profile = profile_result.data[0] if profile_result.data else {}
            name = profile.get('full_name') or email

            data_current = get_year_data(user_id, year)
            data_prev = get_year_data(user_id, year - 1)
            tax_tips = await get_ai_tax_tips(data_current, data_prev, profile)
            pdf_bytes = _generate_annual_pdf(data_current, data_prev, profile, tax_tips)
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

            resend.Emails.send({
                "from": "BigDogg <info@bigdogg.nl>",
                "to": [email],
                "subject": f"Je jaarrapport {year} staat klaar — met persoonlijke belastingtips",
                "text": f"""Hallo {name},

Je jaarrapport voor {year} is klaar. We hebben het voor je samengesteld inclusief:

- Volledig jaaroverzicht met kwartaalverdeling
- Vergelijking met {year - 1}
- Kostenverdeling per categorie
- IB aangifte rubriek guidance
- Persoonlijke belastingtips op basis van jouw cijfers

Je vindt het volledige rapport als bijlage in deze e-mail.

De IB aangifte deadline is 30 april {year + 1}.

Met vriendelijke groet,
Team BigDogg

---
bigdogg.nl · Dit rapport is indicatief. Raadpleeg een belastingadviseur bij twijfel.
""",
                "attachments": [{
                    "filename": f"Jaarrapport-{year}.pdf",
                    "content": pdf_b64,
                }]
            })
            sent += 1
        except Exception as e:
            print(f"Error sending to {email}: {e}")

    return {"sent": sent, "year": year}
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from app.database import supabase
from app.config import settings
from app.routers.pdf import TEAL, GOLD, LIGHT_GREY, MID_GREY, TEXT_SECONDARY
from app.routers.subscription import require_active_paid
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
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

    # ── Hours: manual + invoice-derived ──────────────────────────────────────
    manual_hrs_result = supabase.table("hours").select("hours")\
        .eq("user_id", user_id)\
        .gte("date", f"{year}-01-01")\
        .lte("date", f"{year}-12-31")\
        .execute()
    manual_hours = round(sum(float(h["hours"]) for h in (manual_hrs_result.data or [])), 2)

    inv_ids_result = supabase.table("invoices").select("id")\
        .eq("user_id", user_id).neq("status", "draft")\
        .gte("invoice_date", f"{year}-01-01")\
        .lte("invoice_date", f"{year}-12-31").execute()
    inv_ids = [i["id"] for i in (inv_ids_result.data or [])]
    invoice_hours = 0.0
    if inv_ids:
        lines = supabase.table("invoice_lines").select("quantity, unit")\
            .in_("invoice_id", inv_ids).execute()
        for line in (lines.data or []):
            unit = (line.get("unit") or "fixed").lower()
            qty = float(line.get("quantity", 0) or 0)
            if unit == "day":
                invoice_hours += qty * 9.0
            elif unit == "hour":
                invoice_hours += qty
    invoice_hours = round(invoice_hours, 2)
    total_hours = round(manual_hours + invoice_hours, 2)

    # ── Depreciation ──────────────────────────────────────────────────────────
    investments = supabase.table("investments").select("*")\
        .eq("user_id", user_id).execute()
    total_depreciation = 0.0
    depreciation_items = []
    for inv in (investments.data or []):
        dep_years = inv.get("depreciation_years", 5) or 5
        purchase_year = int((inv.get("purchase_date") or f"{year}-01-01")[:4])
        if purchase_year <= year < purchase_year + dep_years:
            annual_dep = round(float(inv.get("amount", 0)) / dep_years, 2)
            total_depreciation += annual_dep
            depreciation_items.append({
                "description": inv.get("description", ""),
                "amount": annual_dep,
                "purchase_date": inv.get("purchase_date", ""),
            })
    total_depreciation = round(total_depreciation, 2)

    return {
        "year": year,
        "quarters": quarters,
        "total_revenue": round(total_rev, 2),
        "total_expenses": round(total_exp, 2),
        "total_btw": round(total_btw, 2),
        "total_profit": total_profit,
        "category_totals": category_totals,
        "invoice_count": sum(q['invoice_count'] for q in quarters),
        "total_hours": total_hours,
        "manual_hours": manual_hours,
        "invoice_hours": invoice_hours,
        "total_depreciation": total_depreciation,
        "depreciation_items": depreciation_items,
    }

async def get_ai_tax_tips(data_current, data_prev, profile, lang='nl'):
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    if lang == 'en':
        prompt = f"""You are a Dutch tax advisor specializing in self-employed freelancers (ZZP'ers).
Based on the financial figures below, provide 5-6 concrete, personal tax tips for this Dutch freelancer.
Focus on legal deductions, income tax return tips, and comparisons with the previous year.
Write in English. Be specific and mention actual amounts where possible.
Give practical tips, not legal advice.

IMPORTANT accuracy rules:
- Home office deductions: only mention if workspace is completely self-contained with own entrance and sanitary facilities. Do NOT suggest partial home deductions — these are NOT allowed for Dutch ZZP'ers under current law.
- All tips must be accurate under current Dutch tax law.
- Always recommend consulting a tax advisor for the final return.

Year {data_current['year']}:
- Revenue: €{data_current['total_revenue']}
- Costs: €{data_current['total_expenses']}
- Profit: €{data_current['total_profit']}
- Total VAT: €{data_current['total_btw']}
- Invoice count: {data_current['invoice_count']}
- Expense categories: {data_current['category_totals']}
- Total hours worked: {data_current['total_hours']} (criterion: 1,225 hrs)
- Total depreciation: €{data_current['total_depreciation']}

Year {data_prev['year']}:
- Revenue: €{data_prev['total_revenue']}
- Profit: €{data_prev['total_profit']}

Name: {profile.get('full_name', 'Freelancer')}

Provide tips as a numbered list (1. 2. 3. etc.), each on a new line. Max 800 words."""
    else:
        prompt = f"""Je bent een Nederlandse belastingadviseur gespecialiseerd in ZZP'ers.
Geef op basis van de financiële cijfers hieronder 5-6 concrete, persoonlijke belastingtips voor deze ZZP'er.
Focus op legale aftrekposten, IB aangifte tips, en vergelijkingen met het vorige jaar.
Schrijf in het Nederlands. Wees concreet en noem specifieke bedragen waar mogelijk.
Geef geen juridisch advies maar praktische tips.

BELANGRIJKE nauwkeurigheidsregels:
- Thuiswerkplek aftrek: vermeld dit ALLEEN als de werkruimte volledig zelfstandig is met eigen ingang en eigen sanitair. Suggereer GEEN gedeeltelijke thuisaftrek — dit is onder de huidige Nederlandse wet voor ZZP'ers NIET toegestaan.
- Alle tips moeten correct zijn onder de huidige Nederlandse belastingwet.
- Adviseer altijd een belastingadviseur te raadplegen voor de definitieve aangifte.

Jaar {data_current['year']}:
- Omzet: €{data_current['total_revenue']}
- Kosten: €{data_current['total_expenses']}
- Winst: €{data_current['total_profit']}
- Totale BTW: €{data_current['total_btw']}
- Aantal facturen: {data_current['invoice_count']}
- Kostencategorieën: {data_current['category_totals']}
- Totaal gewerkte uren: {data_current['total_hours']} (criterium: 1.225 uur)
- Totale afschrijvingen: €{data_current['total_depreciation']}

Jaar {data_prev['year']}:
- Omzet: €{data_prev['total_revenue']}
- Winst: €{data_prev['total_profit']}

Naam: {profile.get('full_name', "ZZP'er")}
KVK: {profile.get('kvk_number', 'onbekend')}

Geef de tips als een genummerde lijst (1. 2. 3. etc.), elk op een nieuwe regel. Max 800 woorden."""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def _t(nl, en, lang):
    return en if lang == 'en' else nl

def _generate_annual_pdf(data_current, data_prev, profile, tax_tips, lang='nl'):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    story = []

    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=9, textColor=TEXT_SECONDARY, leading=14)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=10, textColor=TEAL, leading=14)
    section_style = ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=13, textColor=TEAL, spaceBefore=6*mm, spaceAfter=3*mm)
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=10, textColor=TEAL, leading=15)
    tip_style = ParagraphStyle('Tip', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, leading=14, leftIndent=4*mm)
    footer_style = ParagraphStyle('Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER)
    explain_style = ParagraphStyle('Explain', fontName='Helvetica-Oblique', fontSize=9, textColor=TEXT_SECONDARY, leading=13)
    name_style = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=20, textColor=TEAL)
    number_style = ParagraphStyle('Number', fontName='Helvetica-Bold', fontSize=14, textColor=TEAL, alignment=1)

    page_width = A4[0] - 40*mm
    business_name = profile.get('business_name') or profile.get('full_name') or 'BigDogg'
    year = data_current['year']

    header_data = [[
        Paragraph(business_name, name_style),
        Paragraph(f"{_t('Jaarrapport', 'Annual Report', lang)} {year}\n{_t('Inkomstenbelasting', 'Income Tax', lang)}", number_style),
    ]]
    header_table = Table(header_data, colWidths=[page_width * 0.6, page_width * 0.4])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 2*mm))
    story.append(HRFlowable(width="100%", thickness=3, color=GOLD, spaceAfter=4*mm))

    meta_data = [[
        [Paragraph(_t('NAAM', 'NAME', lang), label_style),
         Paragraph(profile.get('full_name', '—'), value_style)],
        [Paragraph('KVK', label_style),
         Paragraph(profile.get('kvk_number', '—'), value_style)],
        [Paragraph(_t('AANGIFTE PERIODE', 'FILING PERIOD', lang), label_style),
         Paragraph(f"1 {_t('maart', 'March', lang)} — 30 {_t('april', 'April', lang)} {year + 1}", value_style)],
    ]]
    meta_table = Table(meta_data, colWidths=[page_width/3, page_width/3, page_width/3])
    meta_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    story.append(meta_table)
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    # ── Year Summary ──────────────────────────────────────────────────────────
    story.append(Paragraph(f"{_t('Jaaroverzicht', 'Year Summary', lang)} {year}", section_style))

    summary_rows = [
        ['', f'{year}', f'{data_prev["year"]}', _t('Verschil', 'Change', lang)],
        [_t('Omzet ex BTW', 'Revenue ex VAT', lang),
         f"€ {data_current['total_revenue']:,.2f}",
         f"€ {data_prev['total_revenue']:,.2f}",
         _diff(data_current['total_revenue'], data_prev['total_revenue'])],
        [_t('Kosten ex BTW', 'Costs ex VAT', lang),
         f"€ {data_current['total_expenses']:,.2f}",
         f"€ {data_prev['total_expenses']:,.2f}",
         _diff(data_current['total_expenses'], data_prev['total_expenses'])],
        [_t('Winst (indicatief)', 'Profit (indicative)', lang),
         f"€ {data_current['total_profit']:,.2f}",
         f"€ {data_prev['total_profit']:,.2f}",
         _diff(data_current['total_profit'], data_prev['total_profit'])],
        [_t('Totale BTW', 'Total VAT', lang),
         f"€ {data_current['total_btw']:,.2f}",
         f"€ {data_prev['total_btw']:,.2f}",
         _diff(data_current['total_btw'], data_prev['total_btw'])],
    ]

    sum_table = Table(summary_rows, colWidths=[page_width*0.35, page_width*0.22, page_width*0.22, page_width*0.21])
    sum_table.setStyle(TableStyle([
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
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#F0FDF4')),
    ]))
    story.append(sum_table)

    # ── Quarterly Overview ────────────────────────────────────────────────────
    story.append(Paragraph(f"{_t('Kwartaaloverzicht', 'Quarterly Overview', lang)} {year}", section_style))

    q_rows = [[_t('Kwartaal', 'Quarter', lang), _t('Omzet', 'Revenue', lang),
               _t('Kosten', 'Costs', lang), _t('Winst', 'Profit', lang), 'BTW/VAT']]
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

    # ── Expense Breakdown ─────────────────────────────────────────────────────
    if data_current['category_totals']:
        story.append(Paragraph(_t('Kostenverdeling', 'Expense Breakdown', lang), section_style))
        cat_labels_nl = {
            'travel': 'Reizen', 'materials': 'Materialen', 'software': 'Software',
            'food': 'Eten & Drinken', 'office': 'Kantoor', 'other': 'Overig', 'general': 'Algemeen'
        }
        cat_labels_en = {
            'travel': 'Travel', 'materials': 'Materials', 'software': 'Software',
            'food': 'Food & Drinks', 'office': 'Office', 'other': 'Other', 'general': 'General'
        }
        cat_labels = cat_labels_en if lang == 'en' else cat_labels_nl

        cat_rows = [[_t('Categorie', 'Category', lang),
                     _t('Bedrag ex BTW', 'Amount ex VAT', lang),
                     _t('% van totaal', '% of total', lang)]]
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

    # ── Hours Summary ─────────────────────────────────────────────────────────
    story.append(Paragraph(_t('Urenregistratie', 'Hours Overview', lang), section_style))

    total_hours = data_current.get('total_hours', 0)
    manual_hours = data_current.get('manual_hours', 0)
    invoice_hours = data_current.get('invoice_hours', 0)
    urencriterium = 1225
    pct_hours = min(round(total_hours / urencriterium * 100, 1), 100) if total_hours > 0 else 0.0
    criterium_met = _t('Ja', 'Yes', lang) if total_hours >= urencriterium else _t('Nee', 'No', lang)

    hours_rows = [
        [_t('Omschrijving', 'Description', lang), _t('Uren', 'Hours', lang)],
        [_t('Handmatig geregistreerd', 'Manually logged', lang), f"{manual_hours:.1f} u"],
        [_t('Vanuit facturen (uur/dag)', 'From invoices (hour/day)', lang), f"{invoice_hours:.1f} u"],
        [_t('Totaal gewerkte uren', 'Total hours worked', lang), f"{total_hours:.1f} u"],
        [_t('Urencriterium (1.225 u)', 'Hour criterion (1,225 hrs)', lang), f"{pct_hours:.1f}% — {criterium_met}"],
    ]
    hours_table = Table(hours_rows, colWidths=[page_width * 0.65, page_width * 0.35])
    hours_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 1), (0, -1), TEXT_SECONDARY),
        ('TEXTCOLOR', (1, 1), (1, -1), TEAL),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [LIGHT_GREY, colors.white]),
        ('LINEBELOW', (0, -2), (-1, -2), 0.5, MID_GREY),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(hours_table)

    if total_hours >= urencriterium:
        hours_note = _t(
            f"✓ Je hebt het urencriterium van 1.225 uur gehaald ({total_hours:.0f} uur). "
            "Je komt in aanmerking voor de zelfstandigenaftrek.",
            f"✓ You have met the hour criterion of 1,225 hours ({total_hours:.0f} hours). "
            "You qualify for the self-employed deduction.",
            lang
        )
    else:
        remaining = max(0, urencriterium - total_hours)
        hours_note = _t(
            f"Je hebt {total_hours:.0f} van de benodigde 1.225 uur geregistreerd "
            f"({remaining:.0f} uur te gaan). Het urencriterium is vereist voor de zelfstandigenaftrek.",
            f"You have logged {total_hours:.0f} of the required 1,225 hours "
            f"({remaining:.0f} hours remaining). The hour criterion is required for the self-employed deduction.",
            lang
        )
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(hours_note, explain_style))

    # ── Depreciation ──────────────────────────────────────────────────────────
    total_dep = data_current.get('total_depreciation', 0)
    dep_items = data_current.get('depreciation_items', [])

    if total_dep > 0 and dep_items:
        story.append(Paragraph(_t('Afschrijvingen', 'Depreciation', lang), section_style))

        dep_rows = [
            [_t('Investering', 'Investment', lang),
             _t('Aankoopdatum', 'Purchase date', lang),
             _t('Jaarlijkse afschrijving', 'Annual depreciation', lang)],
        ]
        for item in dep_items:
            dep_rows.append([
                item["description"],
                item["purchase_date"],
                f"€ {item['amount']:,.2f}",
            ])
        dep_rows.append([
            _t('Totaal afschrijving dit jaar', 'Total depreciation this year', lang),
            '',
            f"€ {total_dep:,.2f}",
        ])

        dep_table = Table(dep_rows, colWidths=[page_width*0.45, page_width*0.25, page_width*0.30])
        dep_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TEAL),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [LIGHT_GREY, colors.white]),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, 1), (-1, -2), TEXT_SECONDARY),
            ('TEXTCOLOR', (2, 1), (2, -1), TEAL),
            ('LINEBELOW', (0, -2), (-1, -2), 0.5, MID_GREY),
            ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
        ]))
        story.append(dep_table)
        story.append(Spacer(1, 2*mm))
        dep_note = _t(
            f"Afschrijvingen verlagen je belastbare winst. Totaal dit jaar: €{total_dep:,.2f}. "
            "Zorg dat investeringen correct zijn geregistreerd in je administratie.",
            f"Depreciation reduces your taxable profit. Total this year: €{total_dep:,.2f}. "
            "Ensure all investments are properly documented in your records.",
            lang
        )
        story.append(Paragraph(dep_note, explain_style))

    # ── IB Return Guidance ────────────────────────────────────────────────────
    story.append(Paragraph(_t('IB Aangifte — Wat invullen?', 'Income Tax Return — What to fill in?', lang), section_style))
    ib_data = [
        [_t('Rubriek', 'Field', lang), _t('Omschrijving', 'Description', lang), _t('Jouw bedrag', 'Your amount', lang)],
        [_t('Omzet', 'Revenue', lang), _t('Totale omzet exclusief BTW', 'Total revenue excluding VAT', lang), f"€ {data_current['total_revenue']:,.2f}"],
        [_t('Kosten', 'Costs', lang), _t('Zakelijke kosten exclusief BTW', 'Business costs excluding VAT', lang), f"€ {data_current['total_expenses']:,.2f}"],
        [_t('Afschrijvingen', 'Depreciation', lang), _t('Jaarlijkse afschrijving investeringen', 'Annual investment depreciation', lang), f"€ {total_dep:,.2f}"],
        [_t('Winst', 'Profit', lang), _t('Omzet minus kosten minus afschrijvingen', 'Revenue minus costs minus depreciation', lang), f"€ {round(data_current['total_profit'] - total_dep, 2):,.2f}"],
    ]
    ib_table = Table(ib_data, colWidths=[page_width*0.25, page_width*0.50, page_width*0.25])
    ib_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0FDF4')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [LIGHT_GREY, colors.white]),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (1, -1), 'LEFT'),
        ('TEXTCOLOR', (0, 1), (-1, -2), TEAL),
        ('GRID', (0, 0), (-1, -1), 0.5, MID_GREY),
    ]))
    story.append(ib_table)
    story.append(Spacer(1, 2*mm))

    if lang == 'en':
        ib_note = ("💡 Enter your profit under 'Profit from business' in your income tax return on belastingdienst.nl. "
                   "Don't forget to apply the self-employed deduction (€5,030 in 2026) and the SME profit exemption (14%).")
    else:
        ib_note = ("💡 Vul de winst in bij 'Winst uit onderneming' in je IB aangifte op belastingdienst.nl. "
                   "Vergeet niet de zelfstandigenaftrek (€5.030 in 2026) en eventuele MKB-winstvrijstelling (14%) toe te passen.")
    story.append(Paragraph(ib_note, explain_style))

    # ── AI Tax Tips ───────────────────────────────────────────────────────────
    story.append(Paragraph(_t('Persoonlijke belastingtips voor jou', 'Personal tax tips for you', lang), section_style))
    story.append(Paragraph(_t('Op basis van jouw cijfers heeft BigDogg de volgende tips voor je:', 'Based on your figures, BigDogg has the following tips for you:', lang), body_style))
    story.append(Spacer(1, 3*mm))

    for line in tax_tips.split('\n'):
        line = line.strip()
        if line:
            story.append(Paragraph(line, tip_style))
            story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    if lang == 'en':
        footer_text = (f"Generated by BigDogg · bigdogg.nl · {datetime.now().strftime('%d-%m-%Y')} · "
                       "This report is indicative. Consult a tax advisor for your final income tax return.")
    else:
        footer_text = (f"Gegenereerd door BigDogg · bigdogg.nl · {datetime.now().strftime('%d-%m-%Y')} · "
                       "Dit rapport is indicatief. Raadpleeg een belastingadviseur voor je definitieve aangifte inkomstenbelasting.")

    story.append(Paragraph(footer_text, footer_style))
    doc.build(story)
    return buffer.getvalue()

def _diff(current, prev):
    if prev == 0:
        return '—'
    diff = current - prev
    pct = round(diff / prev * 100, 1)
    sign = '+' if diff >= 0 else ''
    return f"{sign}{pct}%"

@router.api_route("/annual/pdf", methods=["GET", "HEAD"])
async def download_annual_report(
    request: Request,
    token: str = Query(None),
    year: int = Query(None),
    lang: str = Query('nl')
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

    require_active_paid(user_id)

    if not year:
        year = datetime.now().year - 1

    profile_result = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
    profile = profile_result.data[0] if profile_result.data else {}

    data_current = get_year_data(user_id, year)
    data_prev = get_year_data(user_id, year - 1)
    import asyncio
    if lang == 'en':
        fallback_tips = "1. Check if you qualify for the self-employed deduction (zelfstandigenaftrek).\n2. Apply the SME profit exemption (MKB-winstvrijstelling) of 14%.\n3. Review all business costs for deductibility.\n4. Consider a pension reserve (FOR) to reduce taxable profit.\n5. Ensure all invoices are in your administration."
    else:
        fallback_tips = "1. Controleer of je in aanmerking komt voor de zelfstandigenaftrek.\n2. Pas de MKB-winstvrijstelling van 14% toe op je winst.\n3. Bekijk alle zakelijke kosten op aftrekbaarheid.\n4. Overweeg een fiscale oudedagsreserve (FOR) om belastbare winst te verlagen.\n5. Zorg dat alle facturen in je administratie zitten."
    try:
        tax_tips = await asyncio.wait_for(get_ai_tax_tips(data_current, data_prev, profile, lang), timeout=25.0)
    except Exception:
        tax_tips = fallback_tips
    pdf_bytes = _generate_annual_pdf(data_current, data_prev, profile, tax_tips, lang)

    filename = f"Annual-Report-{year}.pdf" if lang == 'en' else f"Jaarrapport-{year}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
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
            tax_tips = await get_ai_tax_tips(data_current, data_prev, profile, 'nl')
            pdf_bytes = _generate_annual_pdf(data_current, data_prev, profile, tax_tips, 'nl')
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
- Urenregistratie overzicht en urencriterium status
- Afschrijvingen overzicht
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
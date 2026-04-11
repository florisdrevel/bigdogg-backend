from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from app.database import supabase
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
import io

router = APIRouter()

TEAL = colors.HexColor('#1B3A4B')
GOLD = colors.HexColor('#C9A96E')
LIGHT_GREY = colors.HexColor('#F5F3EF')
MID_GREY = colors.HexColor('#E2DDD6')
TEXT_SECONDARY = colors.HexColor('#4A6572')


@router.get("/{invoice_id}")
async def generate_invoice_pdf(invoice_id: str, request: Request, token: str = Query(None)):
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

    try:
        invoice_result = supabase.table("invoices")\
            .select("*, clients(*)")\
            .eq("id", invoice_id)\
            .eq("user_id", user_id)\
            .single()\
            .execute()

        if not invoice_result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")

        lines_result = supabase.table("invoice_lines")\
            .select("*")\
            .eq("invoice_id", invoice_id)\
            .execute()

        profile_result = supabase.table("user_profiles")\
            .select("*")\
            .eq("id", user_id)\
            .execute()

        invoice = invoice_result.data
        lines = lines_result.data
        profile = profile_result.data[0] if profile_result.data else {}

        client = invoice.get("clients") or {
            "contact_name": invoice.get("client_name", ""),
            "email": invoice.get("client_email", ""),
            "company_name": invoice.get("client_company", ""),
        }

        pdf_bytes = _generate_pdf(invoice, lines, profile, client, sender_email)

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={invoice['invoice_number']}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _generate_pdf(invoice, lines, profile, client, sender_email=''):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    story = []

    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=28, textColor=TEAL, spaceAfter=2*mm)
    subtitle_style = ParagraphStyle('Subtitle', fontName='Helvetica', fontSize=10, textColor=TEXT_SECONDARY, spaceAfter=1*mm)
    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=8, textColor=TEXT_SECONDARY, spaceAfter=1*mm, leading=12)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=10, textColor=TEAL, spaceAfter=1*mm, leading=14)
    value_bold_style = ParagraphStyle('ValueBold', fontName='Helvetica-Bold', fontSize=10, textColor=TEAL, spaceAfter=1*mm, leading=14)
    number_style = ParagraphStyle('Number', fontName='Helvetica-Bold', fontSize=20, textColor=TEAL, spaceAfter=2*mm)

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

    name_style = ParagraphStyle('Name', fontName='Helvetica-Bold', fontSize=name_font_size, textColor=TEAL, spaceAfter=2*mm)

    header_data = [[
        Paragraph(display_name, name_style),
        Paragraph(invoice['invoice_number'], number_style),
    ]]
    header_table = Table(header_data, colWidths=[page_width * 0.6, page_width * 0.4])
    header_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=3, color=GOLD, spaceAfter=6*mm))

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
        Paragraph('FACTUURDATUM', label_style),
        Paragraph(invoice.get('invoice_date', ''), value_style),
        Spacer(1, 3*mm),
        Paragraph('VERVALDATUM', label_style),
        Paragraph(invoice.get('due_date', ''), value_style),
        Spacer(1, 3*mm),
        Paragraph('STATUS', label_style),
        Paragraph(invoice.get('status', '').upper(), value_bold_style),
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
            line['description'],
            str(line['quantity']),
            f"€ {float(line['unit_price_ex_btw']):.2f}",
            f"{line['btw_rate']}%",
            f"€ {float(line['line_total_ex_btw']):.2f}",
        ])

    col_widths = [page_width*0.40, page_width*0.10, page_width*0.18, page_width*0.10, page_width*0.22]
    lines_table = Table(table_data, colWidths=col_widths)
    lines_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
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
        ('TEXTCOLOR', (0, 1), (-1, -1), TEAL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('LINEBELOW', (0, -1), (-1, -1), 1, MID_GREY),
    ]))
    story.append(lines_table)
    story.append(Spacer(1, 6*mm))

    subtotal = float(invoice.get('subtotal_ex_btw', 0))
    btw_amount = float(invoice.get('btw_amount', 0))
    total = float(invoice.get('total_incl_btw', 0))

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
        ('TEXTCOLOR', (0, 0), (-1, -1), TEAL),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, 2), (-1, 2), 1.5, GOLD),
        ('BACKGROUND', (1, 2), (-1, 2), LIGHT_GREY),
        ('FONTSIZE', (0, 2), (-1, 2), 12),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 10*mm))

    story.append(HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=4*mm))

    footer_text = "Bedankt voor uw opdracht."
    if profile.get('iban'):
        footer_text += f" Gelieve het bedrag over te maken op IBAN {profile['iban']}."
    if sender_email:
        footer_text += f" Bij vragen kunt u contact opnemen via {sender_email}."
    else:
        footer_text += " Bij vragen kunt u contact opnemen via e-mail."

    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER,
    )))

    doc.build(story)
    return buffer.getvalue()
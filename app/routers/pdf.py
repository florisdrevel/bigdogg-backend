from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response
from app.database import supabase
from app.services.download_token import resolve_download_identity
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
import io
import urllib.request
from xml.sax.saxutils import escape as xml_escape

router = APIRouter()

TEAL = colors.HexColor('#1B3A4B')
GOLD = colors.HexColor('#C9A96E')
LIGHT_GREY = colors.HexColor('#F5F3EF')
MID_GREY = colors.HexColor('#E2DDD6')
TEXT_SECONDARY = colors.HexColor('#4A6572')


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


@router.get("/{invoice_id}")
async def generate_invoice_pdf(invoice_id: str, request: Request, token: str = Query(None)):
    # Finding #7: prefer Bearer header / signed ?dt= token; the raw account
    # JWT in ?token= is the deprecated legacy path for older app builds.
    user_id, sender_email = resolve_download_identity(
        request, scope=f"invoice_pdf:{invoice_id}", legacy_jwt=token)

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

    # User-customisable accent colors. Default = BigDogg teal/gold.
    primary = _safe_hex(profile.get('invoice_primary_color'), TEAL)
    accent  = _safe_hex(profile.get('invoice_accent_color'),  GOLD)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    story = []

    subtitle_style = ParagraphStyle('Subtitle', fontName='Helvetica', fontSize=10, textColor=TEXT_SECONDARY, spaceAfter=1*mm)
    label_style = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=8, textColor=TEXT_SECONDARY, spaceAfter=1*mm, leading=12)
    value_style = ParagraphStyle('Value', fontName='Helvetica', fontSize=10, textColor=primary, spaceAfter=1*mm, leading=14)
    value_bold_style = ParagraphStyle('ValueBold', fontName='Helvetica-Bold', fontSize=10, textColor=primary, spaceAfter=1*mm, leading=14)
    number_style = ParagraphStyle('Number', fontName='Helvetica-Bold', fontSize=20, textColor=primary, spaceAfter=2*mm)

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

    # Try to load logo
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
        header_data = [[
            logo_img,
            Paragraph(invoice['invoice_number'], number_style),
        ]]
    else:
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
    if profile.get('bic'):
        sender_lines.append(Paragraph(f"BIC: {profile['bic']}", subtitle_style))
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
    if client.get('kvk_number'):
        client_lines.append(Paragraph(f"KVK: {client['kvk_number']}", subtitle_style))
    if client.get('btw_number'):
        client_lines.append(Paragraph(f"BTW: {client['btw_number']}", subtitle_style))

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

    footer_text = "Bedankt voor uw opdracht."
    if profile.get('iban'):
        bic_suffix = f" (BIC: {profile['bic']})" if profile.get('bic') else ""
        footer_text += f" Gelieve het bedrag over te maken op IBAN {profile['iban']}{bic_suffix}."
    if sender_email:
        footer_text += f" Bij vragen kunt u contact opnemen via {sender_email}."
    else:
        footer_text += " Bij vragen kunt u contact opnemen via e-mail."

    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY, alignment=TA_CENTER,
    )))

    # User-defined footer note, appended below the standard payment line.
    # Free text, so escape reportlab markup and keep the user's line breaks.
    custom_footer = (profile.get('invoice_footer') or '').strip()
    if custom_footer:
        safe_footer = xml_escape(custom_footer).replace('\n', '<br/>')
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(safe_footer, ParagraphStyle(
            'CustomFooter', fontName='Helvetica', fontSize=9, textColor=TEXT_SECONDARY,
            alignment=TA_CENTER, leading=13,
        )))

    doc.build(story)
    return buffer.getvalue()
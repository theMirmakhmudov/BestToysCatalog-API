from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import requests


def load_image_from_url(url, width, height):
    """URL orqali rasmni yuklash"""
    try:
        response = requests.get(url, timeout=5)
        img = Image(BytesIO(response.content), width=width, height=height)
        return img
    except:
        return Paragraph("<font size=8>[Rasm]</font>", getSampleStyleSheet()['Normal'])


def generate_order_pdf(order: dict) -> bytes:
    """
    Order dict uchun PDF yaratadi.
    order dict struktura:
    {
      "order_id": 1,
      "customer_name": "Obidov Ibrohim",
      "phone_number": "+998 99 471 11 12",
      "shipping_address": "Uzbekistan, Namangan",
      "date": "04.11.2025",
      "time": "09:02:09",
      "items": [
        {"name": "Mak-55 LEGO (97)", "category": "Konstruktor", "price": 39000, "quantity": 2, "subtotal": 78000, "image_url": "https://..."},
        ...
      ],
      "subtotal": 228000,
      "shipping": 100000,
      "tax": "12%",
      "total": 367360
    }
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm,
                            leftMargin=20*mm, rightMargin=20*mm)
    elements = []

    # Stillar
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=colors.black,
        spaceAfter=3,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=42
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=24
    )

    info_bold_style = ParagraphStyle(
        'InfoBold',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=16
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        leading=13
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName='Helvetica',
        alignment=TA_CENTER,
        leading=12
    )

    table_cell_left_style = ParagraphStyle(
        'TableCellLeft',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName='Helvetica',
        alignment=TA_LEFT,
        leading=12
    )

    summary_style_left = ParagraphStyle(
        'SummaryLeft',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=18,
        alignment=TA_LEFT
    )

    summary_style_right = ParagraphStyle(
        'SummaryRight',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        fontName='Helvetica',
        leading=18,
        alignment=TA_RIGHT
    )

    summary_style_right_bold = ParagraphStyle(
        'SummaryRightBold',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=18,
        alignment=TA_RIGHT
    )

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=14
    )

    # === HEADER ===
    title = Paragraph("Obidov Toys", title_style)
    elements.append(title)

    subtitle = Paragraph("Buyurtma cheki", subtitle_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 10 * mm))

    # === ORDER INFO ===
    info_data = [
        [Paragraph(f"<b>Chek raqami:</b> #{order.get('order_id', '-')}", info_bold_style),
         Paragraph(f"<b>Mijoz:</b> {order.get('customer_name', '-')}", info_bold_style)],
        [Paragraph(f"<b>Sana:</b> {order.get('date', '-')}", info_bold_style),
         Paragraph(f"<b>Telefon:</b> {order.get('phone_number', '-')}", info_bold_style)],
        [Paragraph(f"<b>Vaqt:</b> {order.get('time', '-')}", info_bold_style),
         Paragraph(f"<b>Manzil:</b> {order.get('shipping_address', '-')}", info_bold_style)]
    ]

    info_table = Table(info_data, colWidths=[85 * mm, 85 * mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10 * mm))

    # === PRODUCTS TABLE ===
    products_data = [
        [Paragraph("<b>Maxsulot nomi</b>", table_header_style),
         Paragraph("<b>Kategoriya</b>", table_header_style),
         Paragraph("<b>Narxi (so'm)</b>", table_header_style),
         Paragraph("<b>Soni</b>", table_header_style),
         Paragraph("<b>Rasm</b>", table_header_style),
         Paragraph("<b>Umumiy<br/>(so'm)</b>", table_header_style)]
    ]

    for item in order.get("items", []):
        products_data.append([
            Paragraph(item.get("name", "-"), table_cell_style),
            Paragraph(item.get("category", "-"), table_cell_style),
            Paragraph(f"{int(item.get('price', 0)):,}", table_cell_style),
            Paragraph(str(item.get("quantity", 1)), table_cell_style),
            load_image_from_url(item.get("image_url"), width=20 * mm, height=20 * mm),
            Paragraph(f"{int(item.get('subtotal', 0)):,}", table_cell_style)
        ])

    # Jami qator
    products_data.append([
        Paragraph("<b>Jami</b>", table_header_style),
        "", "", "", "",
        Paragraph(f"<b>{int(order.get('subtotal', 0)):,}</b>", table_header_style)
    ])

    products_table = Table(products_data, colWidths=[40 * mm, 28 * mm, 28 * mm, 16 * mm, 24 * mm, 34 * mm])
    products_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(products_table)
    elements.append(Spacer(1, 10 * mm))

    # === SUMMARY ===
    summary_data = [
        [Paragraph("<b>Mahsulotlar jami:</b>", summary_style_left),
         Paragraph(f"{int(order.get('subtotal', 0)):,} so'm", summary_style_right)],
        [Paragraph("<b>Yetkazib berish:</b>", summary_style_left),
         Paragraph(f"{int(order.get('shipping', 0)):,} so'm", summary_style_right)],
        [Paragraph("<b>Soliq:</b>", summary_style_left),
         Paragraph(f"{order.get('tax', '12%')}", summary_style_right)],
        [Paragraph("<b>Umumiy summa:</b>", summary_style_left),
         Paragraph(f"<b>{int(order.get('total', 0)):,} so'm</b>", summary_style_right_bold)]
    ]

    summary_table = Table(summary_data, colWidths=[120 * mm, 50 * mm])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('TOPPADDING', (0, -1), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15 * mm))

    # === FOOTER ===
    footer_text = """
    <b>ObidovToys</b> — <u>doim</u> siz bilan.<br/>
    www.obidovtoys.uz | +998 99 471 11 12 | Telegram: @obidovtoys
    """
    footer = Paragraph(footer_text, footer_style)
    elements.append(footer)

    # PDF yaratish
    doc.build(elements)
    pdf = buf.getvalue()
    buf.close()
    return pdf
import os
from datetime import datetime
from io import BytesIO

from babel.numbers import format_currency
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def format_brl(value):
    return format_currency(value, "BRL", locale="pt_BR")


def add_subtitle(text, style, elements):
    elements.append(Spacer(1, 0.2 * inch))
    subtitle_para = Paragraph(text, style)
    elements.append(subtitle_para)
    elements.append(Spacer(1, 0.2 * inch))


def generate_pdf(budget):
    buffer = BytesIO()

    document = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()

    small_style = ParagraphStyle(
        "SmallStyle", parent=styles["Normal"], fontSize=9, leading=10
    )

    subtitle_style = ParagraphStyle(
        name="Subtitle",
        fontSize=14,
        leading=16,
        fontName="Helvetica-Bold",
    )

    company_details = [
        "NR ELÉTRICAS ME",
        "Nilcio Rodrigues",
        "nilcio.r@hotmail.com",
        "09.635.118/0001-60",
        "Rua Lydio Fernandes da Costa, 71",
        "Suzano",
        "08625-325",
        "(11) 98641-8719",
    ]

    company_details_content = "<br/>".join(
        [
            f"<b>{company_details[0]}</b>",
            f"Responsável: {company_details[1]}",
            f"E-mail: {company_details[2]}",
            f"CNPJ: {company_details[3]}",
            f"{company_details[4]}",
            f"{company_details[5]} - SP - CEP: {company_details[6]}",
            f"Telefone: {company_details[7]}",
        ]
    )
    company_details_paragraph = Paragraph(company_details_content, small_style)

    logo_path = "images/logo_nr.png"
    logo = (
        Image(logo_path, width=2 * inch, height=2 * inch)
        if os.path.exists(logo_path)
        else Spacer(1, 2 * inch)
    )

    header_data = [[logo, company_details_paragraph]]
    header_table = Table(header_data, colWidths=[2 * inch, 5 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (1, 0), (1, 0), 14),
            ]
        )
    )

    elements = [header_table, Spacer(1, 0.1 * inch)]

    # Title
    title = f"Orçamento de Serviços Nº {budget.id}"
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))

    # Section 1: Dados do Orçamento
    add_subtitle("1. Dados do Orçamento", subtitle_style, elements)

    formatted_budget_date = budget.budget_date.strftime("%d/%m/%Y")
    details_budget = [
        f"<b>Data:</b> {formatted_budget_date}",
        f"<b>Validade:</b> {budget.validity_days} dias",
    ]
    if budget.service_description:
        details_budget.append(f"<b>Descrição:</b> {budget.service_description}")
    if budget.notes:
        details_budget.append(f"<b>Observações:</b> {budget.notes}")
    for detail in details_budget:
        elements.append(Paragraph(detail, styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))

    # Section 2: Dados do Cliente
    add_subtitle("2. Dados do Cliente", subtitle_style, elements)

    details_client = [
        f"<b>Razão Social:</b> {budget.client.name}",
        f"<b>CNPJ:</b> {budget.client.document}",
        f"<b>Endereço:</b> {budget.client.address}",
    ]
    for detail in details_client:
        elements.append(Paragraph(detail, styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))

    # Section 3: Itens
    items = budget.items.all()

    add_subtitle("3. Itens", subtitle_style, elements)

    data = [["Item", "Nome", "Quantidade", "Preço Unitário", "Preço Total"]]
    for item_number, item in enumerate(items, 1):
        data.append(
            [
                str(item_number),
                item.description,
                item.quantity,
                format_brl(item.unit_price),
                format_brl(item.total_price),
            ]
        )

    table = Table(
        data,
        colWidths=[0.5 * inch, 3 * inch, 1.25 * inch, 1.25 * inch, 1.25 * inch],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#16423C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), HexColor("#C4DAD2")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
            ]
        )
    )
    elements.append(table)

    # Section 4: Valores
    add_subtitle("4. Valores", subtitle_style, elements)

    details_values = []

    if budget.workforce > 0:
        details_values.append(f"<b>Mão de Obra:</b> {format_brl(budget.workforce)}")
        details_values.append(f"<b>Subtotal Itens:</b> {format_brl(budget.total_items)}")
        details_values.append(f"<b>Total Geral:</b> {format_brl(budget.total_amount)}")
    else:
        details_values.append(f"<b>Total Geral:</b> {format_brl(budget.total_amount)}")

    for detail in details_values:
        elements.append(Paragraph(detail, styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))

    # Build and Save the Document
    document.build(elements)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    client_name = budget.client.name.replace(" ", "_")
    budget.pdf_file.save(
        f"ORCAMENTO_{budget.id}_{client_name}_{timestamp}.pdf",
        ContentFile(buffer.getvalue()),
    )
    buffer.close()

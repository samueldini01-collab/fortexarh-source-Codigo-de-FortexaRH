"""
PDF Invoice Generation Service for FortexaRH
"""
import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_invoice_pdf(invoice_data: dict, company_data: dict = None) -> bytes:
    """
    Generate a professional PDF invoice.
    
    Args:
        invoice_data: Invoice details from database
        company_data: Company information
    
    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        textColor=colors.HexColor('#1e3a5f'),
        alignment=TA_LEFT
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_RIGHT
    )
    
    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#888888'),
    )
    
    value_style = ParagraphStyle(
        'ValueStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'NormalCustom',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
    )
    
    story = []
    
    # Header with company info and invoice number
    invoice_number = invoice_data.get('invoice_number', 'N/A')
    company_name = company_data.get('name', '') if company_data else invoice_data.get('company_name', '')
    
    # Title row
    header_data = [
        [
            Paragraph('<b>FortexaRH</b>', title_style),
            Paragraph(f'<b>FACTURA</b><br/>{invoice_number}', header_style)
        ]
    ]
    
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Invoice info section
    created_at = invoice_data.get('created_at', '')
    if created_at:
        try:
            if isinstance(created_at, str):
                date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                date_obj = created_at
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_date = created_at[:10] if len(created_at) >= 10 else created_at
    else:
        formatted_date = 'N/A'
    
    paid_at = invoice_data.get('paid_at', '')
    if paid_at and paid_at != 'N/A':
        try:
            if isinstance(paid_at, str) and len(paid_at) > 10:
                paid_date_obj = datetime.fromisoformat(paid_at.replace('Z', '+00:00'))
                paid_formatted = paid_date_obj.strftime('%d/%m/%Y')
            else:
                paid_formatted = paid_at
        except:
            paid_formatted = paid_at
    else:
        paid_formatted = formatted_date
    
    # Two column layout for bill to and invoice details
    bill_to_content = f'''
    <b>Facturado a:</b><br/>
    {company_name}<br/>
    '''
    
    invoice_details = f'''
    <b>Fecha:</b> {formatted_date}<br/>
    <b>Fecha de Pago:</b> {paid_formatted}<br/>
    <b>Estado:</b> {'Pagada' if invoice_data.get('status') == 'paid' else 'Pendiente'}
    '''
    
    info_data = [
        [
            Paragraph(bill_to_content, normal_style),
            Paragraph(invoice_details, normal_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Line items table
    plan_name = invoice_data.get('plan_name', 'Suscripción')
    base_price = float(invoice_data.get('base_price', 0))
    employee_count = int(invoice_data.get('employee_count', 1))
    employee_price = float(invoice_data.get('employee_price', 0))
    employee_total = employee_count * employee_price
    total = float(invoice_data.get('total', base_price + employee_total))
    
    # Table header
    table_data = [
        [
            Paragraph('<b>Descripción</b>', normal_style),
            Paragraph('<b>Cantidad</b>', normal_style),
            Paragraph('<b>Precio Unit.</b>', normal_style),
            Paragraph('<b>Total</b>', normal_style)
        ],
        [
            Paragraph(f'Plan {plan_name} - Tarifa Base', normal_style),
            '1',
            f'${base_price:.2f}',
            f'${base_price:.2f}'
        ],
    ]
    
    if employee_count > 0 and employee_price > 0:
        table_data.append([
            Paragraph(f'Empleados Adicionales', normal_style),
            str(employee_count),
            f'${employee_price:.2f}',
            f'${employee_total:.2f}'
        ])
    
    items_table = Table(table_data, colWidths=[3.5*inch, 1*inch, 1.25*inch, 1.25*inch])
    items_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        
        # Alignment
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#1e3a5f')),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Totals section
    totals_data = [
        ['', '', Paragraph('<b>Subtotal:</b>', normal_style), f'${total:.2f}'],
        ['', '', Paragraph('<b>ITBIS (0%):</b>', normal_style), '$0.00'],
        ['', '', Paragraph('<b>TOTAL USD:</b>', value_style), f'${total:.2f}'],
    ]
    
    totals_table = Table(totals_data, colWidths=[3.5*inch, 1*inch, 1.25*inch, 1.25*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (2, -1), (-1, -1), 1, colors.HexColor('#1e3a5f')),
        ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#f0f7ff')),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#888888'),
        alignment=TA_CENTER
    )
    
    story.append(Paragraph('Gracias por su preferencia', footer_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph('FortexaRH - Sistema de Recursos Humanos y Nómina', footer_style))
    story.append(Paragraph('www.fortexaerp.com | soporte@fortexaerp.com', footer_style))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def invoice_pdf_to_base64(invoice_data: dict, company_data: dict = None) -> str:
    """
    Generate invoice PDF and return as base64 string.
    """
    pdf_bytes = generate_invoice_pdf(invoice_data, company_data)
    return base64.b64encode(pdf_bytes).decode('utf-8')

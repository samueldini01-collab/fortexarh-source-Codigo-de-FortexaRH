"""Payroll exports — IIF (QuickBooks) + Payslip PDF."""
from __future__ import annotations

import io
from datetime import datetime

from fastapi import Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import db
from utils.auth import get_current_user
from services.payslip_lines import (
    build_earnings_lines,
    build_deductions_lines,
    total_deductions as compute_total_deductions,
)

from . import router
from ._helpers import format_currency_pdf


@router.get("/periods/{period_id}/export/iif")
async def export_period_iif(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export payroll journal entry as IIF file for QuickBooks Desktop import."""
    company_id = current_user.get("company_id")

    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id}, {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Periodo no encontrado")

    je_id = period.get("journal_entry_id")
    je = None
    if je_id:
        je = await db.journal_entries.find_one(
            {"entry_id": je_id, "company_id": company_id}, {"_id": 0}
        )

    if not je or not je.get("lines"):
        raise HTTPException(status_code=400, detail="No hay asiento contable generado para este periodo. Apruebe o pague la nomina primero.")

    # Parse entry_date -> MM/DD/YYYY for IIF
    raw_date = je.get("entry_date", "")
    try:
        if "T" in str(raw_date):
            raw_date = str(raw_date).split("T")[0]
        parts = str(raw_date).split("-")
        iif_date = f"{parts[1]}/{parts[2]}/{parts[0]}" if len(parts) == 3 else raw_date
    except Exception:
        iif_date = raw_date

    reference = je.get("reference", f"NOM-{period_id[-6:]}")
    memo_base = je.get("description", "Asiento de Nomina")

    # Build IIF content
    lines_out = []
    # Header rows
    lines_out.append("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO")
    lines_out.append("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO")
    lines_out.append("!ENDTRNS")

    je_lines = je["lines"]
    first = True
    for jl in je_lines:
        debit = jl.get("debit", 0)
        credit = jl.get("credit", 0)
        if debit == 0 and credit == 0:
            continue
        amount = round(debit - credit, 2)
        acct_name = jl.get("account_name", "")
        line_memo = jl.get("description", memo_base)
        row_type = "TRNS" if first else "SPL"
        lines_out.append(f"{row_type}\t\tGENERAL JOURNAL\t{iif_date}\t{acct_name}\t\t\t{amount}\t{reference}\t{line_memo}")
        first = False

    lines_out.append("ENDTRNS")

    iif_content = "\r\n".join(lines_out) + "\r\n"

    period_desc = period.get("description", period_id)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in period_desc).strip().replace(" ", "_")
    filename = f"FortexaRH_JE_{safe_name}.iif"

    return Response(
        content=iif_content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )




# ===================== PAYSLIP PDF GENERATION (ADMIN) =====================

from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


@router.get("/payslip/{entry_id}/pdf")
async def generate_payslip_pdf(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Generate a payslip PDF for a specific payroll entry (admin access)"""
    company_id = current_user.get("company_id")

    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada de nómina no encontrada")

    # Get company info
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1, "company_name": 1, "rnc": 1, "address": 1}
    )
    company_name = (company or {}).get("company_name", (company or {}).get("name", "Empresa"))
    company_rnc = (company or {}).get("rnc", "")

    # Get employee info
    employee = await db.employees.find_one(
        {"employee_id": entry.get("employee_id")},
        {"_id": 0, "first_name": 1, "last_name": 1, "document_number": 1, "position": 1, "department": 1}
    )
    emp_name = f"{(employee or {}).get('first_name', '')} {(employee or {}).get('last_name', '')}"

    # Get period info
    period = await db.payroll_periods.find_one(
        {"period_id": entry.get("period_id")},
        {"_id": 0, "description": 1, "start_date": 1, "end_date": 1}
    )
    period_desc = (period or {}).get("description", entry.get("period_id", ""))

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, spaceAfter=4)

    # Header
    elements.append(Paragraph(company_name, title_style))
    if company_rnc:
        elements.append(Paragraph(f"RNC: {company_rnc}", subtitle_style))
    elements.append(Paragraph("RECIBO DE NÓMINA", title_style))
    elements.append(Spacer(1, 15))

    # Employee Info Table
    emp_info = [
        ["DATOS DEL EMPLEADO", "", "", ""],
        ["Nombre:", emp_name, "Cédula:", (employee or {}).get('document_number', 'N/A')],
        ["Cargo:", (employee or {}).get('position', 'N/A'), "Departamento:", (employee or {}).get('department', 'N/A')],
        ["Período:", period_desc, "Fecha:", datetime.now().strftime('%d/%m/%Y')],
    ]

    emp_table = Table(emp_info, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    emp_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (3, 0)),
        ('BACKGROUND', (0, 0), (3, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (3, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 15))

    # Earnings
    earnings_lines = build_earnings_lines(entry)
    earnings_data = [["INGRESOS", "MONTO"]]
    earnings_data.extend([label, format_currency_pdf(amount)] for label, amount in earnings_lines)
    earnings_data.append(["TOTAL INGRESOS", format_currency_pdf(entry.get('gross_salary', 0))])

    earnings_table = Table(earnings_data, colWidths=[4*inch, 2*inch])
    earnings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4edda')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(earnings_table)
    elements.append(Spacer(1, 10))

    # Deductions (legal + additional + novelties)
    deductions_lines = build_deductions_lines(entry)
    deductions_data = [["DEDUCCIONES", "MONTO"]]
    deductions_data.extend([label, format_currency_pdf(amount)] for label, amount in deductions_lines)
    total_deductions = compute_total_deductions(entry)
    deductions_data.append(["TOTAL DEDUCCIONES", format_currency_pdf(total_deductions)])

    deductions_table = Table(deductions_data, colWidths=[4*inch, 2*inch])
    deductions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8d7da')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(deductions_table)
    elements.append(Spacer(1, 15))

    # Net Pay
    net_data = [["SALARIO NETO A PAGAR", format_currency_pdf(entry.get('net_salary', 0))]]
    net_table = Table(net_data, colWidths=[4*inch, 2*inch])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(net_table)

    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} — FortexaRH | www.fortexarh.com"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))

    doc.build(elements)
    buffer.seek(0)

    safe_name = emp_name.replace(' ', '_')
    filename = f"recibo_{safe_name}_{period_desc.replace(' ', '_')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

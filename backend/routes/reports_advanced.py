"""
Advanced Reports Router - FortexaRH
PDF/Excel generation for Payroll, Attendance, and Evaluations reports
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from typing import Callable, Optional
from datetime import datetime, timezone, timedelta
import io
import uuid

# PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

router = APIRouter(prefix="/reports-advanced", tags=["Advanced Reports"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


def format_currency(value):
    """Format value as Dominican Peso"""
    return f"RD${value:,.2f}" if value else "RD$0.00"


def format_date(date_str):
    """Format ISO date string to readable format"""
    if not date_str:
        return "N/A"
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = date_str
        return dt.strftime("%d/%m/%Y")
    except:
        return str(date_str)[:10] if date_str else "N/A"


# ============== PAYROLL DETAILED REPORT ==============

@router.get("/payroll/{period_id}/pdf")
async def generate_payroll_pdf(
    period_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate detailed PDF report for a payroll period"""
    company_id = current_user.get("company_id")
    
    # Get period info
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Get company info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1, "rnc": 1})
    company_name = company.get("name", "Empresa") if company else "Empresa"
    company_rnc = company.get("rnc", "") if company else ""
    
    # Get payroll entries
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=12)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=6)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=10, alignment=TA_LEFT)
    
    # Header
    elements.append(Paragraph(company_name, title_style))
    if company_rnc:
        elements.append(Paragraph(f"RNC: {company_rnc}", subtitle_style))
    elements.append(Paragraph(f"REPORTE DE NÓMINA - {period.get('description', '')}", subtitle_style))
    elements.append(Paragraph(f"Período: {period.get('start_date')} al {period.get('end_date')}", subtitle_style))
    elements.append(Paragraph(f"Estado: {period.get('status', '').upper()}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Summary section
    summary_data = [
        ["RESUMEN DE NÓMINA", "", "", ""],
        ["Total Empleados:", str(period.get('employee_count', 0)), "Total Bruto:", format_currency(period.get('total_gross', 0))],
        ["Total Deducciones:", format_currency(period.get('total_gross', 0) - period.get('total_net', 0)), "Total Neto:", format_currency(period.get('total_net', 0))],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (3, 0)),
        ('BACKGROUND', (0, 0), (3, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (3, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Detail table header
    table_data = [
        ["#", "Empleado", "Departamento", "Salario Base", "Hrs. Extra", "Bonos", "SFS", "AFP", "ISR", "Otros", "Neto"]
    ]
    
    # Add entries
    for i, entry in enumerate(entries, 1):
        bonuses = entry.get('bonuses', 0) + entry.get('commissions', 0)
        other_ded = entry.get('other_deductions', 0) + entry.get('loan_deduction', 0)
        
        table_data.append([
            str(i),
            entry.get('employee_name', 'N/A')[:20],
            (entry.get('department', '') or 'N/A')[:12],
            format_currency(entry.get('base_salary', 0)),
            format_currency(entry.get('overtime_pay', 0)),
            format_currency(bonuses),
            format_currency(entry.get('sfs_employee', 0)),
            format_currency(entry.get('afp_employee', 0)),
            format_currency(entry.get('isr', 0)),
            format_currency(other_ded),
            format_currency(entry.get('net_salary', 0))
        ])
    
    # Totals row
    total_base = sum(e.get('base_salary', 0) for e in entries)
    total_overtime = sum(e.get('overtime_pay', 0) for e in entries)
    total_bonuses = sum(e.get('bonuses', 0) + e.get('commissions', 0) for e in entries)
    total_sfs = sum(e.get('sfs_employee', 0) for e in entries)
    total_afp = sum(e.get('afp_employee', 0) for e in entries)
    total_isr = sum(e.get('isr', 0) for e in entries)
    total_other = sum(e.get('other_deductions', 0) + e.get('loan_deduction', 0) for e in entries)
    total_net = sum(e.get('net_salary', 0) for e in entries)
    
    table_data.append([
        "", "TOTALES", "",
        format_currency(total_base),
        format_currency(total_overtime),
        format_currency(total_bonuses),
        format_currency(total_sfs),
        format_currency(total_afp),
        format_currency(total_isr),
        format_currency(total_other),
        format_currency(total_net)
    ])
    
    # Create table
    col_widths = [0.3*inch, 1.5*inch, 1*inch, 0.9*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.9*inch]
    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(detail_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} por {current_user.get('email', 'Usuario')}"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"nomina_{period_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============== ATTENDANCE REPORT ==============

@router.get("/attendance/pdf")
async def generate_attendance_pdf(
    start_date: str,
    end_date: str,
    department: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate PDF report for attendance"""
    company_id = current_user.get("company_id")
    
    # Get company info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1})
    company_name = company.get("name", "Empresa") if company else "Empresa"
    
    # Build query
    query = {"company_id": company_id, "date": {"$gte": start_date, "$lte": end_date}}
    if department:
        # Get employees in department
        emps = await db.employees.find(
            {"company_id": company_id, "department": department},
            {"_id": 0, "employee_id": 1}
        ).to_list(500)
        emp_ids = [e["employee_id"] for e in emps]
        query["employee_id"] = {"$in": emp_ids}
    
    # Get attendance records
    records = await db.attendances.find(query, {"_id": 0}).sort("date", 1).to_list(1000)
    
    # Get employee names
    emp_ids = list(set(r.get("employee_id") for r in records))
    employees = await db.employees.find(
        {"employee_id": {"$in": emp_ids}},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1}
    ).to_list(500)
    emp_map = {e["employee_id"]: e for e in employees}
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=12)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=6)
    
    # Header
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph("REPORTE DE ASISTENCIA", subtitle_style))
    elements.append(Paragraph(f"Período: {start_date} al {end_date}", subtitle_style))
    if department:
        elements.append(Paragraph(f"Departamento: {department}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Summary
    total_records = len(records)
    on_time = sum(1 for r in records if r.get("status") == "on_time")
    late = sum(1 for r in records if r.get("status") == "late")
    absent = sum(1 for r in records if r.get("status") == "absent")
    total_hours = sum(r.get("hours_worked", 0) for r in records)
    total_overtime = sum(r.get("overtime_hours", 0) for r in records)
    
    summary_data = [
        ["RESUMEN", "", "", "", ""],
        ["Total Registros:", str(total_records), "A Tiempo:", str(on_time), f"({(on_time/total_records*100):.1f}%)" if total_records else "0%"],
        ["Tardanzas:", str(late), "Ausencias:", str(absent), ""],
        ["Horas Trabajadas:", f"{total_hours:.1f}h", "Horas Extra:", f"{total_overtime:.1f}h", ""],
    ]
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (4, 0)),
        ('BACKGROUND', (0, 0), (4, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (4, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Detail table
    table_data = [["Fecha", "Empleado", "Departamento", "Entrada", "Salida", "Horas", "Extras", "Estado"]]
    
    status_map = {"on_time": "A Tiempo", "late": "Tardanza", "absent": "Ausente", "early": "Temprano"}
    
    for r in records:
        emp = emp_map.get(r.get("employee_id"), {})
        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip() or "N/A"
        
        table_data.append([
            r.get("date", "N/A"),
            emp_name[:25],
            (emp.get("department", "") or "N/A")[:15],
            r.get("check_in", "-")[:5] if r.get("check_in") else "-",
            r.get("check_out", "-")[:5] if r.get("check_out") else "-",
            f"{r.get('hours_worked', 0):.1f}h",
            f"{r.get('overtime_hours', 0):.1f}h",
            status_map.get(r.get("status"), r.get("status", "N/A"))
        ])
    
    col_widths = [0.9*inch, 2*inch, 1.2*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.9*inch]
    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (3, 1), (6, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(detail_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"asistencia_{start_date}_{end_date}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============== EVALUATIONS REPORT ==============

@router.get("/evaluations/pdf")
async def generate_evaluations_pdf(
    cycle_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate PDF report for evaluations"""
    company_id = current_user.get("company_id")
    
    # Get company info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1})
    company_name = company.get("name", "Empresa") if company else "Empresa"
    
    # Build query
    query = {"company_id": company_id}
    if cycle_id:
        query["cycle_id"] = cycle_id
    if employee_id:
        query["employee_id"] = employee_id
    
    # Get evaluations
    evaluations = await db.evaluations.find(query, {"_id": 0}).to_list(200)
    
    if not evaluations:
        raise HTTPException(status_code=404, detail="No se encontraron evaluaciones")
    
    # Get employee info
    emp_ids = list(set(e.get("employee_id") for e in evaluations))
    employees = await db.employees.find(
        {"employee_id": {"$in": emp_ids}},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1, "position": 1}
    ).to_list(200)
    emp_map = {e["employee_id"]: e for e in employees}
    
    # Get cycle info if provided
    cycle_name = "Todas las Evaluaciones"
    if cycle_id:
        cycle = await db.evaluation_cycles.find_one({"cycle_id": cycle_id}, {"_id": 0, "name": 1})
        cycle_name = cycle.get("name", cycle_id) if cycle else cycle_id
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=12)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, spaceAfter=6)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, spaceAfter=10, spaceBefore=15)
    
    # Header
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph("REPORTE DE EVALUACIONES DE DESEMPEÑO", subtitle_style))
    elements.append(Paragraph(f"Ciclo: {cycle_name}", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Summary
    avg_score = sum(e.get("overall_score", 0) for e in evaluations) / len(evaluations) if evaluations else 0
    completed = sum(1 for e in evaluations if e.get("status") == "completed")
    pending = sum(1 for e in evaluations if e.get("status") == "pending")
    
    summary_data = [
        ["RESUMEN GENERAL", "", ""],
        ["Total Evaluaciones:", str(len(evaluations)), ""],
        ["Completadas:", str(completed), f"({(completed/len(evaluations)*100):.1f}%)" if evaluations else "0%"],
        ["Pendientes:", str(pending), ""],
        ["Promedio General:", f"{avg_score:.1f}/5", ""],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (2, 0)),
        ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, 0), (2, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Detail table
    elements.append(Paragraph("Detalle de Evaluaciones", section_style))
    
    table_data = [["Empleado", "Departamento", "Cargo", "Puntuación", "Estado", "Fecha"]]
    
    status_map = {"completed": "Completada", "pending": "Pendiente", "in_progress": "En Progreso"}
    
    for ev in evaluations:
        emp = emp_map.get(ev.get("employee_id"), {})
        emp_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip() or "N/A"
        
        score = ev.get("overall_score", 0)
        score_color = "green" if score >= 4 else "orange" if score >= 3 else "red"
        
        table_data.append([
            emp_name[:25],
            (emp.get("department", "") or "N/A")[:15],
            (emp.get("position", "") or "N/A")[:15],
            f"{score:.1f}/5",
            status_map.get(ev.get("status"), ev.get("status", "N/A")),
            format_date(ev.get("evaluation_date", ev.get("created_at")))
        ])
    
    col_widths = [2*inch, 1.3*inch, 1.3*inch, 0.8*inch, 1*inch, 0.9*inch]
    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(detail_table)
    
    # Competencies breakdown if available
    if evaluations and evaluations[0].get("competencies"):
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Promedio por Competencia", section_style))
        
        # Aggregate competencies
        comp_scores = {}
        for ev in evaluations:
            for comp in ev.get("competencies", []):
                name = comp.get("name", "N/A")
                if name not in comp_scores:
                    comp_scores[name] = []
                comp_scores[name].append(comp.get("score", 0))
        
        comp_data = [["Competencia", "Promedio", "Evaluaciones"]]
        for name, scores in comp_scores.items():
            avg = sum(scores) / len(scores) if scores else 0
            comp_data.append([name[:30], f"{avg:.2f}/5", str(len(scores))])
        
        comp_table = Table(comp_data, colWidths=[3*inch, 1.5*inch, 1.2*inch])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(comp_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"evaluaciones_{cycle_id or 'todas'}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============== LIST AVAILABLE REPORTS ==============

@router.get("/available")
async def get_available_reports(current_user: dict = Depends(get_current_user)):
    """Get list of available reports"""
    company_id = current_user.get("company_id")
    
    # Get payroll periods for report options
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0, "period_id": 1, "description": 1, "year": 1, "month": 1, "status": 1}
    ).sort([("year", -1), ("month", -1)]).limit(24).to_list(24)
    
    # Get evaluation cycles
    cycles = await db.evaluation_cycles.find(
        {"company_id": company_id},
        {"_id": 0, "cycle_id": 1, "name": 1, "status": 1}
    ).sort("start_date", -1).limit(12).to_list(12)
    
    # Get departments for filters
    departments = await db.employees.distinct("department", {"company_id": company_id, "status": "active"})
    
    return {
        "reports": [
            {
                "id": "payroll",
                "name": "Reporte de Nómina Detallado",
                "description": "PDF con desglose por empleado, deducciones y totales",
                "endpoint": "/reports-advanced/payroll/{period_id}/pdf",
                "requires": "period_id",
                "options": periods
            },
            {
                "id": "attendance",
                "name": "Reporte de Asistencia",
                "description": "PDF con horas trabajadas, tardanzas y extras",
                "endpoint": "/reports-advanced/attendance/pdf",
                "requires": "date_range",
                "filters": {"departments": departments}
            },
            {
                "id": "evaluations",
                "name": "Reporte de Evaluaciones",
                "description": "PDF con scores, competencias y planes de mejora",
                "endpoint": "/reports-advanced/evaluations/pdf",
                "requires": "optional_cycle_id",
                "options": cycles
            }
        ],
        "filters": {
            "departments": [d for d in departments if d],
            "payroll_periods": periods,
            "evaluation_cycles": cycles
        }
    }

"""
Advanced Reports System - FortexaRH
Comprehensive reporting system with 30+ reports, custom filters, 
saved configurations, and multiple export formats.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import io
import uuid
import json

# PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

router = APIRouter(prefix="/reports-system", tags=["Reports System"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func: Callable = None


def init_router(database, auth_dependency: Callable):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_dependency


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


# ============== REPORT DEFINITIONS ==============

REPORT_CATEGORIES = {
    "nomina": {
        "name": "Nómina",
        "icon": "dollar-sign",
        "color": "emerald"
    },
    "empleados": {
        "name": "Empleados",
        "icon": "users",
        "color": "blue"
    },
    "asistencia": {
        "name": "Asistencia",
        "icon": "clock",
        "color": "amber"
    },
    "vacaciones": {
        "name": "Vacaciones y Permisos",
        "icon": "calendar",
        "color": "purple"
    },
    "evaluaciones": {
        "name": "Evaluaciones",
        "icon": "target",
        "color": "indigo"
    },
    "financiero": {
        "name": "Financiero/Contable",
        "icon": "wallet",
        "color": "rose"
    }
}

REPORT_DEFINITIONS = {
    # ========== NÓMINA (8 reports) ==========
    "nomina_resumen": {
        "id": "nomina_resumen",
        "name": "Resumen de Nómina por Período",
        "description": "Vista general de la nómina con totales por concepto",
        "category": "nomina",
        "filters": ["period", "department", "status"],
        "columns": ["employee", "department", "base_salary", "bonuses", "deductions", "net_pay"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_detalle_empleado": {
        "id": "nomina_detalle_empleado",
        "name": "Detalle de Nómina por Empleado",
        "description": "Desglose completo de cada empleado con todos los conceptos",
        "category": "nomina",
        "filters": ["period", "employee", "department"],
        "columns": ["concept", "type", "amount", "percentage"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_comparativo": {
        "id": "nomina_comparativo",
        "name": "Comparativo de Nómina",
        "description": "Comparación mes a mes de costos de nómina",
        "category": "nomina",
        "filters": ["date_range", "department"],
        "columns": ["month", "total_employees", "gross_pay", "deductions", "net_pay", "variation"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_deducciones": {
        "id": "nomina_deducciones",
        "name": "Deducciones por Tipo",
        "description": "Resumen de deducciones (SFS, AFP, ISR, préstamos)",
        "category": "nomina",
        "filters": ["period", "deduction_type", "department"],
        "columns": ["employee", "sfs", "afp", "isr", "loans", "other", "total"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_horas_extras": {
        "id": "nomina_horas_extras",
        "name": "Horas Extras y Bonificaciones",
        "description": "Detalle de horas extras y bonos pagados",
        "category": "nomina",
        "filters": ["period", "employee", "department"],
        "columns": ["employee", "regular_hours", "overtime_35", "overtime_100", "bonuses", "total_extra"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_historico": {
        "id": "nomina_historico",
        "name": "Histórico de Pagos por Empleado",
        "description": "Historial completo de pagos de un empleado",
        "category": "nomina",
        "filters": ["employee", "date_range"],
        "columns": ["period", "gross_pay", "deductions", "net_pay", "payment_date"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_costos_departamento": {
        "id": "nomina_costos_departamento",
        "name": "Costos Laborales por Departamento",
        "description": "Análisis de costos por área organizacional",
        "category": "nomina",
        "filters": ["period", "department"],
        "columns": ["department", "employees", "salaries", "benefits", "taxes", "total_cost", "percentage"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_proyeccion": {
        "id": "nomina_proyeccion",
        "name": "Proyección de Nómina",
        "description": "Estimación de costos futuros basado en tendencias",
        "category": "nomina",
        "filters": ["months_ahead", "include_increases"],
        "columns": ["month", "projected_gross", "projected_deductions", "projected_net", "confidence"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== EMPLEADOS (6 reports) ==========
    "empleados_listado": {
        "id": "empleados_listado",
        "name": "Listado General de Empleados",
        "description": "Lista completa con datos básicos de todos los empleados",
        "category": "empleados",
        "filters": ["status", "department", "position"],
        "columns": ["cedula", "name", "department", "position", "hire_date", "salary", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_departamento": {
        "id": "empleados_departamento",
        "name": "Empleados por Departamento",
        "description": "Distribución de personal por área",
        "category": "empleados",
        "filters": ["department", "status"],
        "columns": ["department", "total", "active", "inactive", "avg_salary", "total_cost"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_antiguedad": {
        "id": "empleados_antiguedad",
        "name": "Antigüedad de Empleados",
        "description": "Análisis de tiempo de servicio del personal",
        "category": "empleados",
        "filters": ["department", "years_range"],
        "columns": ["name", "department", "hire_date", "years", "months", "vacation_days"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_rotacion": {
        "id": "empleados_rotacion",
        "name": "Rotación de Personal",
        "description": "Índice de rotación y análisis de bajas",
        "category": "empleados",
        "filters": ["date_range", "department"],
        "columns": ["month", "hires", "terminations", "rotation_rate", "avg_tenure"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_cumpleanos": {
        "id": "empleados_cumpleanos",
        "name": "Cumpleaños del Mes",
        "description": "Lista de empleados que cumplen años en el período",
        "category": "empleados",
        "filters": ["month"],
        "columns": ["name", "department", "birth_date", "age", "years_service"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_contratos": {
        "id": "empleados_contratos",
        "name": "Contratos por Vencer",
        "description": "Contratos que expiran próximamente",
        "category": "empleados",
        "filters": ["days_ahead", "contract_type"],
        "columns": ["name", "department", "contract_type", "start_date", "end_date", "days_remaining"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== ASISTENCIA (5 reports) ==========
    "asistencia_diaria": {
        "id": "asistencia_diaria",
        "name": "Resumen de Asistencia Diaria",
        "description": "Estado de asistencia del día actual o fecha específica",
        "category": "asistencia",
        "filters": ["date", "department"],
        "columns": ["name", "department", "shift", "check_in", "check_out", "hours", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_tardanzas": {
        "id": "asistencia_tardanzas",
        "name": "Tardanzas y Ausencias",
        "description": "Registro de llegadas tarde y faltas",
        "category": "asistencia",
        "filters": ["date_range", "employee", "department"],
        "columns": ["name", "date", "expected", "actual", "delay_minutes", "type", "justified"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_horas_empleado": {
        "id": "asistencia_horas_empleado",
        "name": "Horas Trabajadas por Empleado",
        "description": "Acumulado de horas por empleado en el período",
        "category": "asistencia",
        "filters": ["date_range", "employee", "department"],
        "columns": ["name", "regular_hours", "overtime", "absences", "total_hours", "efficiency"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_horas_extras": {
        "id": "asistencia_horas_extras",
        "name": "Horas Extras Acumuladas",
        "description": "Detalle de horas extras por empleado",
        "category": "asistencia",
        "filters": ["date_range", "department"],
        "columns": ["name", "department", "ot_35", "ot_100", "total_ot", "estimated_cost"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_tendencia": {
        "id": "asistencia_tendencia",
        "name": "Tendencia de Asistencia Mensual",
        "description": "Evolución de indicadores de asistencia",
        "category": "asistencia",
        "filters": ["date_range", "department"],
        "columns": ["month", "attendance_rate", "punctuality_rate", "absence_rate", "overtime_avg"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== VACACIONES Y PERMISOS (4 reports) ==========
    "vacaciones_balance": {
        "id": "vacaciones_balance",
        "name": "Balance de Vacaciones",
        "description": "Días acumulados, usados y disponibles por empleado",
        "category": "vacaciones",
        "filters": ["department", "status"],
        "columns": ["name", "department", "hire_date", "accrued", "used", "pending", "available"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "vacaciones_pendientes": {
        "id": "vacaciones_pendientes",
        "name": "Solicitudes Pendientes",
        "description": "Solicitudes de vacaciones/permisos por aprobar",
        "category": "vacaciones",
        "filters": ["type", "department"],
        "columns": ["name", "type", "start_date", "end_date", "days", "status", "requested_at"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "vacaciones_historico": {
        "id": "vacaciones_historico",
        "name": "Histórico de Permisos",
        "description": "Registro histórico de todos los permisos otorgados",
        "category": "vacaciones",
        "filters": ["date_range", "employee", "type"],
        "columns": ["name", "type", "start_date", "end_date", "days", "approved_by", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "vacaciones_calendario": {
        "id": "vacaciones_calendario",
        "name": "Calendario de Ausencias",
        "description": "Vista de ausencias programadas por período",
        "category": "vacaciones",
        "filters": ["date_range", "department"],
        "columns": ["date", "employee", "department", "type", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== EVALUACIONES (4 reports) ==========
    "evaluaciones_ciclo": {
        "id": "evaluaciones_ciclo",
        "name": "Resultados por Ciclo",
        "description": "Resumen de evaluaciones de un ciclo específico",
        "category": "evaluaciones",
        "filters": ["cycle", "department"],
        "columns": ["name", "department", "evaluator", "score", "rating", "status", "date"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "evaluaciones_comparativo": {
        "id": "evaluaciones_comparativo",
        "name": "Comparativo de Desempeño",
        "description": "Comparación de resultados entre períodos",
        "category": "evaluaciones",
        "filters": ["employee", "date_range"],
        "columns": ["period", "score", "rating", "strengths", "areas_improvement", "variation"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "evaluaciones_objetivos": {
        "id": "evaluaciones_objetivos",
        "name": "Objetivos y KPIs",
        "description": "Estado de cumplimiento de objetivos",
        "category": "evaluaciones",
        "filters": ["cycle", "employee", "department"],
        "columns": ["employee", "objective", "target", "current", "progress", "due_date", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "evaluaciones_planes": {
        "id": "evaluaciones_planes",
        "name": "Planes de Mejora",
        "description": "Seguimiento de planes de desarrollo",
        "category": "evaluaciones",
        "filters": ["status", "department"],
        "columns": ["employee", "plan", "actions", "progress", "supervisor", "due_date"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== FINANCIERO/CONTABLE (5 reports) ==========
    "financiero_prestamos": {
        "id": "financiero_prestamos",
        "name": "Préstamos Activos",
        "description": "Estado de préstamos a empleados",
        "category": "financiero",
        "filters": ["status", "employee", "department"],
        "columns": ["employee", "amount", "installments", "paid", "remaining", "monthly", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_gastos": {
        "id": "financiero_gastos",
        "name": "Gastos y Viáticos",
        "description": "Reporte de gastos y reembolsos",
        "category": "financiero",
        "filters": ["date_range", "type", "department", "status"],
        "columns": ["employee", "date", "type", "description", "amount", "status", "approved_by"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_provisiones": {
        "id": "financiero_provisiones",
        "name": "Provisiones Laborales",
        "description": "Cálculo de provisiones (vacaciones, cesantía, preaviso)",
        "category": "financiero",
        "filters": ["department", "as_of_date"],
        "columns": ["employee", "salary", "vacation_prov", "severance_prov", "notice_prov", "total"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_asientos": {
        "id": "financiero_asientos",
        "name": "Asientos Contables",
        "description": "Asientos generados por nómina",
        "category": "financiero",
        "filters": ["date_range", "type"],
        "columns": ["date", "account", "description", "debit", "credit", "reference"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_dgii": {
        "id": "financiero_dgii",
        "name": "Reportes DGII (TSS, IR-17)",
        "description": "Reportes para la Dirección General de Impuestos",
        "category": "financiero",
        "filters": ["period", "report_type"],
        "columns": ["cedula", "name", "salary", "sfs_employee", "sfs_employer", "afp_employee", "afp_employer", "isr"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    }
}


# ============== MODELS ==============

class ReportFilter(BaseModel):
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, contains, in, between
    value: Any


class ReportRequest(BaseModel):
    report_id: str
    filters: Optional[List[Dict[str, Any]]] = []
    columns: Optional[List[str]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    page: Optional[int] = 1
    page_size: Optional[int] = 50


class SavedReportConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    report_id: str
    filters: List[Dict[str, Any]] = []
    columns: Optional[List[str]] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"
    is_favorite: Optional[bool] = False


# ============== HELPER FUNCTIONS ==============

def format_currency(value):
    """Format value as Dominican Peso"""
    try:
        return f"RD${float(value):,.2f}" if value else "RD$0.00"
    except:
        return "RD$0.00"


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


def calculate_years_months(start_date):
    """Calculate years and months from a start date"""
    if not start_date:
        return 0, 0
    try:
        if isinstance(start_date, str):
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        else:
            start = start_date
        
        now = datetime.now(timezone.utc)
        diff = now - start.replace(tzinfo=timezone.utc) if start.tzinfo is None else now - start
        years = diff.days // 365
        months = (diff.days % 365) // 30
        return years, months
    except:
        return 0, 0


# ============== ENDPOINTS ==============

@router.get("/catalog")
async def get_report_catalog(current_user: dict = Depends(get_current_user)):
    """Get full catalog of available reports organized by category"""
    catalog = {}
    
    for cat_id, cat_info in REPORT_CATEGORIES.items():
        catalog[cat_id] = {
            **cat_info,
            "reports": []
        }
    
    for report_id, report in REPORT_DEFINITIONS.items():
        category = report["category"]
        if category in catalog:
            catalog[category]["reports"].append({
                "id": report["id"],
                "name": report["name"],
                "description": report["description"],
                "filters": report["filters"],
                "supports_preview": report.get("supports_preview", True),
                "supports_pdf": report.get("supports_pdf", True),
                "supports_excel": report.get("supports_excel", True)
            })
    
    return {
        "categories": catalog,
        "total_reports": len(REPORT_DEFINITIONS)
    }


@router.get("/definition/{report_id}")
async def get_report_definition(report_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed definition of a specific report"""
    if report_id not in REPORT_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    return REPORT_DEFINITIONS[report_id]


@router.post("/preview")
async def preview_report(request: ReportRequest, current_user: dict = Depends(get_current_user)):
    """Generate preview data for a report"""
    if request.report_id not in REPORT_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    company_id = current_user.get("company_id")
    report_def = REPORT_DEFINITIONS[request.report_id]
    
    # Build filter dict from request
    filters = {}
    for f in request.filters:
        filters[f.get("field")] = f.get("value")
    
    # Generate data based on report type
    data = await generate_report_data(
        request.report_id, 
        company_id, 
        filters, 
        request.page, 
        request.page_size,
        request.sort_by,
        request.sort_order
    )
    
    return {
        "report_id": request.report_id,
        "report_name": report_def["name"],
        "filters_applied": filters,
        "columns": request.columns or report_def["columns"],
        "data": data["rows"],
        "totals": data.get("totals", {}),
        "summary": data.get("summary", {}),
        "pagination": {
            "page": request.page,
            "page_size": request.page_size,
            "total_rows": data.get("total_count", len(data["rows"])),
            "total_pages": (data.get("total_count", len(data["rows"])) + request.page_size - 1) // request.page_size
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/export/pdf")
async def export_report_pdf(request: ReportRequest, current_user: dict = Depends(get_current_user)):
    """Export report as PDF"""
    if request.report_id not in REPORT_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    company_id = current_user.get("company_id")
    report_def = REPORT_DEFINITIONS[request.report_id]
    
    # Get company info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "name": 1, "rnc": 1})
    company_name = company.get("name", "FortexaRH") if company else "FortexaRH"
    
    # Build filters
    filters = {}
    for f in request.filters:
        filters[f.get("field")] = f.get("value")
    
    # Get all data for PDF (no pagination)
    data = await generate_report_data(request.report_id, company_id, filters, 1, 10000, request.sort_by, request.sort_order)
    
    # Generate PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=12)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.gray)
    
    elements = []
    
    # Title
    elements.append(Paragraph(f"<b>{company_name}</b>", title_style))
    elements.append(Paragraph(report_def["name"], styles['Heading2']))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Filters applied
    if filters:
        filter_text = " | ".join([f"{k}: {v}" for k, v in filters.items() if v])
        if filter_text:
            elements.append(Paragraph(f"<b>Filtros:</b> {filter_text}", styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
    
    # Table
    columns = request.columns or report_def["columns"]
    
    # Create header row
    header_row = [col.replace("_", " ").title() for col in columns]
    table_data = [header_row]
    
    # Add data rows
    for row in data["rows"]:
        table_row = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                if "salary" in col or "amount" in col or "cost" in col or "pay" in col:
                    value = format_currency(value)
                else:
                    value = f"{value:.2f}"
            elif isinstance(value, bool):
                value = "Sí" if value else "No"
            table_row.append(str(value) if value is not None else "")
        table_data.append(table_row)
    
    # Create table
    col_widths = [1.2*inch] * len(columns)
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(table)
    
    # Totals if available
    if data.get("totals"):
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("<b>Totales</b>", styles['Heading3']))
        totals_text = " | ".join([f"{k}: {format_currency(v) if isinstance(v, (int, float)) else v}" for k, v in data["totals"].items()])
        elements.append(Paragraph(totals_text, styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Total de registros: {len(data['rows'])}", subtitle_style))
    elements.append(Paragraph(f"Generado por: {current_user.get('name', 'Usuario')}", subtitle_style))
    
    doc.build(elements)
    buffer.seek(0)
    
    # Record report generation for traceability
    await record_report_generation(company_id, current_user, request.report_id, filters, "pdf", len(data["rows"]))
    
    filename = f"{report_def['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/excel")
async def export_report_excel(request: ReportRequest, current_user: dict = Depends(get_current_user)):
    """Export report as Excel"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl no está instalado")
    
    if request.report_id not in REPORT_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    company_id = current_user.get("company_id")
    report_def = REPORT_DEFINITIONS[request.report_id]
    
    # Build filters
    filters = {}
    for f in request.filters:
        filters[f.get("field")] = f.get("value")
    
    # Get all data
    data = await generate_report_data(request.report_id, company_id, filters, 1, 10000, request.sort_by, request.sort_order)
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = report_def["name"][:31]  # Excel limit
    
    # Styles
    header_fill = PatternFill(start_color="1e40af", end_color="1e40af", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Title
    ws['A1'] = report_def["name"]
    ws['A1'].font = Font(size=14, bold=True)
    ws['A2'] = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    
    columns = request.columns or report_def["columns"]
    
    # Headers
    for col_idx, col in enumerate(columns, 1):
        cell = ws.cell(row=4, column=col_idx, value=col.replace("_", " ").title())
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = border
    
    # Data
    for row_idx, row in enumerate(data["rows"], 5):
        for col_idx, col in enumerate(columns, 1):
            value = row.get(col, "")
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = border
            if isinstance(value, (int, float)):
                cell.alignment = Alignment(horizontal='right')
    
    # Auto-adjust column widths
    for col_idx, col in enumerate(columns, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 15
    
    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    # Record for traceability
    await record_report_generation(company_id, current_user, request.report_id, filters, "excel", len(data["rows"]))
    
    filename = f"{report_def['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/csv")
async def export_report_csv(request: ReportRequest, current_user: dict = Depends(get_current_user)):
    """Export report as CSV"""
    import csv
    
    if request.report_id not in REPORT_DEFINITIONS:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    company_id = current_user.get("company_id")
    report_def = REPORT_DEFINITIONS[request.report_id]
    
    # Build filters
    filters = {}
    for f in request.filters:
        filters[f.get("field")] = f.get("value")
    
    # Get all data
    data = await generate_report_data(request.report_id, company_id, filters, 1, 10000, request.sort_by, request.sort_order)
    
    columns = request.columns or report_def["columns"]
    
    # Create CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    
    # Header
    writer.writerow([col.replace("_", " ").title() for col in columns])
    
    # Data
    for row in data["rows"]:
        writer.writerow([row.get(col, "") for col in columns])
    
    # Record for traceability
    await record_report_generation(company_id, current_user, request.report_id, filters, "csv", len(data["rows"]))
    
    filename = f"{report_def['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    output = io.BytesIO(buffer.getvalue().encode('utf-8-sig'))
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============== SAVED REPORTS ==============

@router.post("/saved")
async def save_report_config(config: SavedReportConfig, current_user: dict = Depends(get_current_user)):
    """Save a custom report configuration"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    saved_report = {
        "saved_report_id": f"sr_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": user_id,
        "name": config.name,
        "description": config.description,
        "report_id": config.report_id,
        "filters": config.filters,
        "columns": config.columns,
        "sort_by": config.sort_by,
        "sort_order": config.sort_order,
        "is_favorite": config.is_favorite,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.saved_reports.insert_one(saved_report)
    
    return {"message": "Configuración guardada", "saved_report_id": saved_report["saved_report_id"]}


@router.get("/saved")
async def get_saved_reports(current_user: dict = Depends(get_current_user)):
    """Get all saved report configurations for the user"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    saved = await db.saved_reports.find(
        {"company_id": company_id, "user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with report names
    for s in saved:
        if s["report_id"] in REPORT_DEFINITIONS:
            s["report_name"] = REPORT_DEFINITIONS[s["report_id"]]["name"]
            s["report_category"] = REPORT_DEFINITIONS[s["report_id"]]["category"]
    
    return saved


@router.get("/saved/{saved_report_id}")
async def get_saved_report(saved_report_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific saved report configuration"""
    company_id = current_user.get("company_id")
    
    saved = await db.saved_reports.find_one(
        {"saved_report_id": saved_report_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not saved:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return saved


@router.delete("/saved/{saved_report_id}")
async def delete_saved_report(saved_report_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a saved report configuration"""
    company_id = current_user.get("company_id")
    
    result = await db.saved_reports.delete_one(
        {"saved_report_id": saved_report_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return {"message": "Configuración eliminada"}


# ============== TRACEABILITY ==============

@router.get("/history")
async def get_report_history(
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get history of generated reports for traceability"""
    company_id = current_user.get("company_id")
    
    history = await db.report_history.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("generated_at", -1).limit(limit).to_list(limit)
    
    # Enrich with report names
    for h in history:
        if h.get("report_id") in REPORT_DEFINITIONS:
            h["report_name"] = REPORT_DEFINITIONS[h["report_id"]]["name"]
    
    return history


async def record_report_generation(company_id: str, user: dict, report_id: str, filters: dict, format: str, row_count: int):
    """Record report generation for audit/traceability"""
    record = {
        "history_id": f"rh_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": user.get("user_id"),
        "user_name": user.get("name", "Usuario"),
        "report_id": report_id,
        "filters_applied": filters,
        "export_format": format,
        "row_count": row_count,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        await db.report_history.insert_one(record)
    except:
        pass  # Don't fail if history recording fails


# ============== DATA GENERATION FUNCTIONS ==============

async def generate_report_data(report_id: str, company_id: str, filters: dict, page: int, page_size: int, sort_by: str = None, sort_order: str = "asc"):
    """Generate data for a specific report"""
    
    # Route to specific generator based on report type
    generators = {
        # Nómina
        "nomina_resumen": generate_nomina_resumen,
        "nomina_detalle_empleado": generate_nomina_detalle,
        "nomina_comparativo": generate_nomina_comparativo,
        "nomina_deducciones": generate_nomina_deducciones,
        "nomina_horas_extras": generate_nomina_horas_extras,
        "nomina_historico": generate_nomina_historico,
        "nomina_costos_departamento": generate_nomina_costos_depto,
        "nomina_proyeccion": generate_nomina_proyeccion,
        # Empleados
        "empleados_listado": generate_empleados_listado,
        "empleados_departamento": generate_empleados_departamento,
        "empleados_antiguedad": generate_empleados_antiguedad,
        "empleados_rotacion": generate_empleados_rotacion,
        "empleados_cumpleanos": generate_empleados_cumpleanos,
        "empleados_contratos": generate_empleados_contratos,
        # Asistencia
        "asistencia_diaria": generate_asistencia_diaria,
        "asistencia_tardanzas": generate_asistencia_tardanzas,
        "asistencia_horas_empleado": generate_asistencia_horas,
        "asistencia_horas_extras": generate_asistencia_extras,
        "asistencia_tendencia": generate_asistencia_tendencia,
        # Vacaciones
        "vacaciones_balance": generate_vacaciones_balance,
        "vacaciones_pendientes": generate_vacaciones_pendientes,
        "vacaciones_historico": generate_vacaciones_historico,
        "vacaciones_calendario": generate_vacaciones_calendario,
        # Evaluaciones
        "evaluaciones_ciclo": generate_evaluaciones_ciclo,
        "evaluaciones_comparativo": generate_evaluaciones_comparativo,
        "evaluaciones_objetivos": generate_evaluaciones_objetivos,
        "evaluaciones_planes": generate_evaluaciones_planes,
        # Financiero
        "financiero_prestamos": generate_financiero_prestamos,
        "financiero_gastos": generate_financiero_gastos,
        "financiero_provisiones": generate_financiero_provisiones,
        "financiero_asientos": generate_financiero_asientos,
        "financiero_dgii": generate_financiero_dgii,
    }
    
    generator = generators.get(report_id)
    if generator:
        return await generator(company_id, filters, page, page_size, sort_by, sort_order)
    
    return {"rows": [], "total_count": 0}


# ============== REPORT GENERATORS ==============

async def generate_nomina_resumen(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payroll summary report"""
    query = {"company_id": company_id}
    
    if filters.get("period"):
        query["period_id"] = filters["period"]
    if filters.get("department"):
        query["department"] = filters["department"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(1000)
    
    rows = []
    totals = {"base_salary": 0, "bonuses": 0, "deductions": 0, "net_pay": 0}
    
    for entry in entries:
        row = {
            "employee": entry.get("employee_name", ""),
            "department": entry.get("department", ""),
            "base_salary": entry.get("base_salary", 0),
            "bonuses": entry.get("overtime_pay", 0) + entry.get("bonuses", 0),
            "deductions": entry.get("total_deductions", 0),
            "net_pay": entry.get("net_salary", 0)
        }
        rows.append(row)
        totals["base_salary"] += row["base_salary"]
        totals["bonuses"] += row["bonuses"]
        totals["deductions"] += row["deductions"]
        totals["net_pay"] += row["net_pay"]
    
    # Sort
    if sort_by and sort_by in rows[0] if rows else False:
        rows.sort(key=lambda x: x.get(sort_by, 0), reverse=(sort_order == "desc"))
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "rows": rows[start:end],
        "total_count": len(rows),
        "totals": totals
    }


async def generate_nomina_detalle(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate detailed payroll by employee"""
    query = {"company_id": company_id}
    
    if filters.get("employee"):
        query["employee_id"] = filters["employee"]
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(100)
    
    rows = []
    for entry in entries:
        # Add earnings
        rows.append({"concept": "Salario Base", "type": "Ingreso", "amount": entry.get("base_salary", 0), "percentage": ""})
        if entry.get("overtime_pay", 0) > 0:
            rows.append({"concept": "Horas Extras", "type": "Ingreso", "amount": entry.get("overtime_pay", 0), "percentage": ""})
        if entry.get("bonuses", 0) > 0:
            rows.append({"concept": "Bonificaciones", "type": "Ingreso", "amount": entry.get("bonuses", 0), "percentage": ""})
        
        # Add deductions
        if entry.get("sfs_employee", 0) > 0:
            rows.append({"concept": "SFS (Salud)", "type": "Deducción", "amount": entry.get("sfs_employee", 0), "percentage": "3.04%"})
        if entry.get("afp_employee", 0) > 0:
            rows.append({"concept": "AFP (Pensión)", "type": "Deducción", "amount": entry.get("afp_employee", 0), "percentage": "2.87%"})
        if entry.get("isr", 0) > 0:
            rows.append({"concept": "ISR", "type": "Deducción", "amount": entry.get("isr", 0), "percentage": "Variable"})
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_comparativo(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payroll comparison report"""
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("start_date", -1).limit(12).to_list(12)
    
    rows = []
    prev_net = None
    
    for period in reversed(periods):
        entries = await db.payroll_entries.find(
            {"company_id": company_id, "period_id": period["period_id"]},
            {"_id": 0}
        ).to_list(500)
        
        gross = sum(e.get("gross_salary", 0) for e in entries)
        deductions = sum(e.get("total_deductions", 0) for e in entries)
        net = sum(e.get("net_salary", 0) for e in entries)
        
        variation = ((net - prev_net) / prev_net * 100) if prev_net and prev_net > 0 else 0
        
        rows.append({
            "month": period.get("name", period["period_id"]),
            "total_employees": len(entries),
            "gross_pay": gross,
            "deductions": deductions,
            "net_pay": net,
            "variation": f"{variation:+.1f}%" if prev_net else "N/A"
        })
        prev_net = net
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_deducciones(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate deductions report"""
    query = {"company_id": company_id}
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    totals = {"sfs": 0, "afp": 0, "isr": 0, "loans": 0, "other": 0, "total": 0}
    
    for e in entries:
        sfs = e.get("sfs_employee", 0)
        afp = e.get("afp_employee", 0)
        isr = e.get("isr", 0)
        loans = e.get("loan_deduction", 0)
        other = e.get("other_deductions", 0)
        total = sfs + afp + isr + loans + other
        
        rows.append({
            "employee": e.get("employee_name", ""),
            "sfs": sfs,
            "afp": afp,
            "isr": isr,
            "loans": loans,
            "other": other,
            "total": total
        })
        
        totals["sfs"] += sfs
        totals["afp"] += afp
        totals["isr"] += isr
        totals["loans"] += loans
        totals["other"] += other
        totals["total"] += total
    
    return {"rows": rows, "total_count": len(rows), "totals": totals}


async def generate_nomina_horas_extras(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate overtime report"""
    query = {"company_id": company_id}
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for e in entries:
        if e.get("overtime_hours", 0) > 0 or e.get("bonuses", 0) > 0:
            rows.append({
                "employee": e.get("employee_name", ""),
                "regular_hours": e.get("regular_hours", 176),
                "overtime_35": e.get("overtime_hours_35", 0),
                "overtime_100": e.get("overtime_hours_100", 0),
                "bonuses": e.get("bonuses", 0),
                "total_extra": e.get("overtime_pay", 0) + e.get("bonuses", 0)
            })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_historico(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payment history for an employee"""
    query = {"company_id": company_id}
    if filters.get("employee"):
        query["employee_id"] = filters["employee"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    rows = []
    for e in entries:
        rows.append({
            "period": e.get("period_name", e.get("period_id", "")),
            "gross_pay": e.get("gross_salary", 0),
            "deductions": e.get("total_deductions", 0),
            "net_pay": e.get("net_salary", 0),
            "payment_date": format_date(e.get("payment_date"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_nomina_costos_depto(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate labor costs by department"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    dept_data = {}
    total_cost = 0
    
    for emp in employees:
        dept = emp.get("department", "Sin Departamento")
        salary = emp.get("salary", 0)
        
        if dept not in dept_data:
            dept_data[dept] = {"employees": 0, "salaries": 0, "benefits": 0, "taxes": 0}
        
        dept_data[dept]["employees"] += 1
        dept_data[dept]["salaries"] += salary
        dept_data[dept]["benefits"] += salary * 0.08  # Estimate
        dept_data[dept]["taxes"] += salary * 0.18  # Employer contributions
        total_cost += salary * 1.26
    
    rows = []
    for dept, data in dept_data.items():
        dept_total = data["salaries"] + data["benefits"] + data["taxes"]
        rows.append({
            "department": dept,
            "employees": data["employees"],
            "salaries": data["salaries"],
            "benefits": data["benefits"],
            "taxes": data["taxes"],
            "total_cost": dept_total,
            "percentage": f"{(dept_total / total_cost * 100):.1f}%" if total_cost > 0 else "0%"
        })
    
    return {"rows": rows, "total_count": len(rows), "totals": {"total_cost": total_cost}}


async def generate_nomina_proyeccion(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate payroll projection"""
    months_ahead = int(filters.get("months_ahead", 6))
    
    # Get last period total
    last_period = await db.payroll_periods.find_one(
        {"company_id": company_id},
        {"_id": 0},
        sort=[("start_date", -1)]
    )
    
    base_gross = 0
    base_deductions = 0
    
    if last_period:
        entries = await db.payroll_entries.find(
            {"company_id": company_id, "period_id": last_period["period_id"]},
            {"_id": 0}
        ).to_list(500)
        
        base_gross = sum(e.get("gross_salary", 0) for e in entries)
        base_deductions = sum(e.get("total_deductions", 0) for e in entries)
    
    rows = []
    growth_rate = 0.02  # 2% monthly growth estimate
    
    for i in range(1, months_ahead + 1):
        factor = (1 + growth_rate) ** i
        projected_gross = base_gross * factor
        projected_ded = base_deductions * factor
        
        future_date = datetime.now() + timedelta(days=30*i)
        rows.append({
            "month": future_date.strftime("%B %Y"),
            "projected_gross": projected_gross,
            "projected_deductions": projected_ded,
            "projected_net": projected_gross - projected_ded,
            "confidence": f"{max(95 - i*5, 70)}%"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_listado(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employee listing"""
    query = {"company_id": company_id}
    
    if filters.get("status"):
        query["status"] = filters["status"]
    if filters.get("department"):
        query["department"] = filters["department"]
    
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    
    rows = []
    for emp in employees:
        rows.append({
            "cedula": emp.get("cedula", ""),
            "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "department": emp.get("department", ""),
            "position": emp.get("position", ""),
            "hire_date": format_date(emp.get("hire_date")),
            "salary": emp.get("salary", 0),
            "status": emp.get("status", "active")
        })
    
    # Sort
    if sort_by:
        rows.sort(key=lambda x: x.get(sort_by, ""), reverse=(sort_order == "desc"))
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_departamento(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employees by department report"""
    employees = await db.employees.find({"company_id": company_id}, {"_id": 0}).to_list(500)
    
    dept_data = {}
    for emp in employees:
        dept = emp.get("department", "Sin Departamento")
        status = emp.get("status", "active")
        salary = emp.get("salary", 0)
        
        if dept not in dept_data:
            dept_data[dept] = {"total": 0, "active": 0, "inactive": 0, "salaries": []}
        
        dept_data[dept]["total"] += 1
        if status == "active":
            dept_data[dept]["active"] += 1
        else:
            dept_data[dept]["inactive"] += 1
        dept_data[dept]["salaries"].append(salary)
    
    rows = []
    for dept, data in dept_data.items():
        avg_salary = sum(data["salaries"]) / len(data["salaries"]) if data["salaries"] else 0
        rows.append({
            "department": dept,
            "total": data["total"],
            "active": data["active"],
            "inactive": data["inactive"],
            "avg_salary": avg_salary,
            "total_cost": sum(data["salaries"])
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_antiguedad(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employee tenure report"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        years, months = calculate_years_months(emp.get("hire_date"))
        vacation_days = min(14 + years, 18)  # Dominican law
        
        rows.append({
            "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "department": emp.get("department", ""),
            "hire_date": format_date(emp.get("hire_date")),
            "years": years,
            "months": months,
            "vacation_days": vacation_days
        })
    
    # Sort by years desc
    rows.sort(key=lambda x: (x["years"], x["months"]), reverse=True)
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_rotacion(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate employee rotation report"""
    # This would need historical data - using mock data for now
    rows = []
    months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
    
    for month in months:
        rows.append({
            "month": month,
            "hires": 2,
            "terminations": 1,
            "rotation_rate": "5.2%",
            "avg_tenure": "2.3 años"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_cumpleanos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate birthday report"""
    target_month = int(filters.get("month", datetime.now().month))
    
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        birth_date = emp.get("birth_date")
        if birth_date:
            try:
                if isinstance(birth_date, str):
                    bd = datetime.fromisoformat(birth_date.replace("Z", "+00:00"))
                else:
                    bd = birth_date
                
                if bd.month == target_month:
                    years, _ = calculate_years_months(emp.get("hire_date"))
                    age = datetime.now().year - bd.year
                    
                    rows.append({
                        "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                        "department": emp.get("department", ""),
                        "birth_date": format_date(birth_date),
                        "age": age,
                        "years_service": years
                    })
            except:
                pass
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_empleados_contratos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate expiring contracts report"""
    days_ahead = int(filters.get("days_ahead", 30))
    cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        contract_end = emp.get("contract_end_date")
        if contract_end:
            try:
                if isinstance(contract_end, str):
                    end_date = datetime.fromisoformat(contract_end.replace("Z", "+00:00"))
                else:
                    end_date = contract_end
                
                if end_date <= cutoff:
                    days_remaining = (end_date - datetime.now(timezone.utc)).days
                    rows.append({
                        "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                        "department": emp.get("department", ""),
                        "contract_type": emp.get("contract_type", "Indefinido"),
                        "start_date": format_date(emp.get("hire_date")),
                        "end_date": format_date(contract_end),
                        "days_remaining": max(0, days_remaining)
                    })
            except:
                pass
    
    rows.sort(key=lambda x: x["days_remaining"])
    return {"rows": rows, "total_count": len(rows)}


# Asistencia generators
async def generate_asistencia_diaria(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate daily attendance report"""
    date = filters.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    attendances = await db.attendances.find(
        {"company_id": company_id, "date": date},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for att in attendances:
        rows.append({
            "name": att.get("employee_name", ""),
            "department": att.get("department", ""),
            "shift": att.get("shift", "Regular"),
            "check_in": att.get("check_in", "-"),
            "check_out": att.get("check_out", "-"),
            "hours": att.get("hours_worked", 0),
            "status": att.get("status", "present")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_tardanzas(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate tardiness report"""
    attendances = await db.attendances.find(
        {"company_id": company_id, "status": {"$in": ["late", "absent"]}},
        {"_id": 0}
    ).sort("date", -1).to_list(500)
    
    rows = []
    for att in attendances:
        rows.append({
            "name": att.get("employee_name", ""),
            "date": att.get("date", ""),
            "expected": "08:00",
            "actual": att.get("check_in", "-"),
            "delay_minutes": att.get("delay_minutes", 0),
            "type": "Tardanza" if att.get("status") == "late" else "Ausencia",
            "justified": "Sí" if att.get("justified") else "No"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_horas(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate hours worked report"""
    attendances = await db.attendances.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Aggregate by employee
    emp_data = {}
    for att in attendances:
        emp_name = att.get("employee_name", "")
        if emp_name not in emp_data:
            emp_data[emp_name] = {"regular": 0, "overtime": 0, "absences": 0}
        
        emp_data[emp_name]["regular"] += att.get("hours_worked", 0)
        emp_data[emp_name]["overtime"] += att.get("overtime_hours", 0)
        if att.get("status") == "absent":
            emp_data[emp_name]["absences"] += 1
    
    rows = []
    for name, data in emp_data.items():
        total = data["regular"] + data["overtime"]
        efficiency = (data["regular"] / 176 * 100) if data["regular"] > 0 else 0
        rows.append({
            "name": name,
            "regular_hours": data["regular"],
            "overtime": data["overtime"],
            "absences": data["absences"],
            "total_hours": total,
            "efficiency": f"{efficiency:.1f}%"
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_extras(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate overtime hours report"""
    attendances = await db.attendances.find(
        {"company_id": company_id, "overtime_hours": {"$gt": 0}},
        {"_id": 0}
    ).to_list(500)
    
    # Aggregate
    emp_data = {}
    for att in attendances:
        emp_name = att.get("employee_name", "")
        dept = att.get("department", "")
        
        if emp_name not in emp_data:
            emp_data[emp_name] = {"department": dept, "ot_35": 0, "ot_100": 0}
        
        emp_data[emp_name]["ot_35"] += att.get("overtime_35", 0)
        emp_data[emp_name]["ot_100"] += att.get("overtime_100", 0)
    
    rows = []
    for name, data in emp_data.items():
        total_ot = data["ot_35"] + data["ot_100"]
        estimated_cost = data["ot_35"] * 150 + data["ot_100"] * 200  # Rough estimate
        rows.append({
            "name": name,
            "department": data["department"],
            "ot_35": data["ot_35"],
            "ot_100": data["ot_100"],
            "total_ot": total_ot,
            "estimated_cost": estimated_cost
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_asistencia_tendencia(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate attendance trend report"""
    rows = []
    months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]
    
    for month in months:
        rows.append({
            "month": month,
            "attendance_rate": "94.5%",
            "punctuality_rate": "89.2%",
            "absence_rate": "5.5%",
            "overtime_avg": "12.3 hrs"
        })
    
    return {"rows": rows, "total_count": len(rows)}


# Vacaciones generators
async def generate_vacaciones_balance(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate vacation balance report"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for emp in employees:
        years, _ = calculate_years_months(emp.get("hire_date"))
        accrued = min(14 + years, 18)
        used = emp.get("vacation_days_used", 0)
        pending = emp.get("vacation_days_pending", 0)
        
        rows.append({
            "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "department": emp.get("department", ""),
            "hire_date": format_date(emp.get("hire_date")),
            "accrued": accrued,
            "used": used,
            "pending": pending,
            "available": accrued - used - pending
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_vacaciones_pendientes(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate pending vacation requests report"""
    vacations = await db.vacations.find(
        {"company_id": company_id, "status": "pending"},
        {"_id": 0}
    ).to_list(100)
    
    rows = []
    for vac in vacations:
        rows.append({
            "name": vac.get("employee_name", ""),
            "type": vac.get("leave_type", "vacation"),
            "start_date": format_date(vac.get("start_date")),
            "end_date": format_date(vac.get("end_date")),
            "days": vac.get("days_requested", 0),
            "status": vac.get("status", "pending"),
            "requested_at": format_date(vac.get("created_at"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_vacaciones_historico(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate vacation history report"""
    vacations = await db.vacations.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    rows = []
    for vac in vacations:
        rows.append({
            "name": vac.get("employee_name", ""),
            "type": vac.get("leave_type", "vacation"),
            "start_date": format_date(vac.get("start_date")),
            "end_date": format_date(vac.get("end_date")),
            "days": vac.get("days_requested", 0),
            "approved_by": vac.get("approved_by", "-"),
            "status": vac.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_vacaciones_calendario(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate absence calendar report"""
    vacations = await db.vacations.find(
        {"company_id": company_id, "status": "approved"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for vac in vacations:
        rows.append({
            "date": f"{format_date(vac.get('start_date'))} - {format_date(vac.get('end_date'))}",
            "employee": vac.get("employee_name", ""),
            "department": vac.get("department", ""),
            "type": vac.get("leave_type", "vacation"),
            "status": vac.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


# Evaluaciones generators
async def generate_evaluaciones_ciclo(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate evaluation cycle report"""
    query = {"company_id": company_id}
    if filters.get("cycle"):
        query["cycle_id"] = filters["cycle"]
    
    evaluations = await db.evaluations.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for ev in evaluations:
        rows.append({
            "name": ev.get("employee_name", ""),
            "department": ev.get("department", ""),
            "evaluator": ev.get("evaluator_name", ""),
            "score": ev.get("overall_score", 0),
            "rating": ev.get("rating", ""),
            "status": ev.get("status", ""),
            "date": format_date(ev.get("created_at"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_evaluaciones_comparativo(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate evaluation comparison report"""
    query = {"company_id": company_id}
    if filters.get("employee"):
        query["employee_id"] = filters["employee"]
    
    evaluations = await db.evaluations.find(query, {"_id": 0}).sort("created_at", -1).to_list(10)
    
    rows = []
    prev_score = None
    for ev in reversed(evaluations):
        score = ev.get("overall_score", 0)
        variation = ((score - prev_score) / prev_score * 100) if prev_score else 0
        
        rows.append({
            "period": ev.get("cycle_name", ""),
            "score": score,
            "rating": ev.get("rating", ""),
            "strengths": ", ".join(ev.get("strengths", [])[:2]),
            "areas_improvement": ", ".join(ev.get("areas_improvement", [])[:2]),
            "variation": f"{variation:+.1f}%" if prev_score else "N/A"
        })
        prev_score = score
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_evaluaciones_objetivos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate objectives/KPIs report"""
    objectives = await db.objectives.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for obj in objectives:
        target = obj.get("target_value", 100)
        current = obj.get("current_value", 0)
        progress = (current / target * 100) if target > 0 else 0
        
        rows.append({
            "employee": obj.get("employee_name", ""),
            "objective": obj.get("title", ""),
            "target": target,
            "current": current,
            "progress": f"{progress:.1f}%",
            "due_date": format_date(obj.get("due_date")),
            "status": obj.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_evaluaciones_planes(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate improvement plans report"""
    plans = await db.improvement_plans.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    for plan in plans:
        rows.append({
            "employee": plan.get("employee_name", ""),
            "plan": plan.get("title", ""),
            "actions": len(plan.get("actions", [])),
            "progress": f"{plan.get('progress', 0)}%",
            "supervisor": plan.get("supervisor_name", ""),
            "due_date": format_date(plan.get("due_date"))
        })
    
    return {"rows": rows, "total_count": len(rows)}


# Financiero generators
async def generate_financiero_prestamos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate loans report"""
    query = {"company_id": company_id}
    if filters.get("status"):
        query["status"] = filters["status"]
    
    loans = await db.loans.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for loan in loans:
        amount = loan.get("amount", 0)
        paid = loan.get("total_paid", 0)
        remaining = amount - paid
        
        rows.append({
            "employee": loan.get("employee_name", ""),
            "amount": amount,
            "installments": loan.get("installments", 0),
            "paid": paid,
            "remaining": remaining,
            "monthly": loan.get("monthly_payment", 0),
            "status": loan.get("status", "")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_financiero_gastos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate expenses report"""
    query = {"company_id": company_id}
    if filters.get("status"):
        query["status"] = filters["status"]
    
    expenses = await db.expense_requests.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for exp in expenses:
        rows.append({
            "employee": exp.get("employee_name", ""),
            "date": format_date(exp.get("date")),
            "type": exp.get("expense_type", ""),
            "description": exp.get("description", ""),
            "amount": exp.get("amount", 0),
            "status": exp.get("status", ""),
            "approved_by": exp.get("approved_by", "-")
        })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_financiero_provisiones(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate provisions report"""
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    rows = []
    totals = {"vacation_prov": 0, "severance_prov": 0, "notice_prov": 0, "total": 0}
    
    for emp in employees:
        salary = emp.get("salary", 0)
        years, months = calculate_years_months(emp.get("hire_date"))
        
        # Dominican law calculations
        vacation_prov = (salary / 23.83) * min(14 + years, 18) / 12
        severance_prov = salary * min(years, 20) / 12 if years >= 1 else 0
        notice_prov = salary * (7 if years < 3 else (14 if years < 6 else 28)) / 365 / 12
        total = vacation_prov + severance_prov + notice_prov
        
        rows.append({
            "employee": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            "salary": salary,
            "vacation_prov": vacation_prov,
            "severance_prov": severance_prov,
            "notice_prov": notice_prov,
            "total": total
        })
        
        totals["vacation_prov"] += vacation_prov
        totals["severance_prov"] += severance_prov
        totals["notice_prov"] += notice_prov
        totals["total"] += total
    
    return {"rows": rows, "total_count": len(rows), "totals": totals}


async def generate_financiero_asientos(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate journal entries report"""
    entries = await db.journal_entries.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("date", -1).to_list(500)
    
    rows = []
    for entry in entries:
        for line in entry.get("lines", []):
            rows.append({
                "date": format_date(entry.get("date")),
                "account": line.get("account_code", ""),
                "description": line.get("description", entry.get("description", "")),
                "debit": line.get("debit", 0),
                "credit": line.get("credit", 0),
                "reference": entry.get("reference", "")
            })
    
    return {"rows": rows, "total_count": len(rows)}


async def generate_financiero_dgii(company_id: str, filters: dict, page: int, page_size: int, sort_by: str, sort_order: str):
    """Generate DGII report (TSS)"""
    query = {"company_id": company_id}
    if filters.get("period"):
        query["period_id"] = filters["period"]
    
    entries = await db.payroll_entries.find(query, {"_id": 0}).to_list(500)
    
    rows = []
    for e in entries:
        rows.append({
            "cedula": e.get("cedula", ""),
            "name": e.get("employee_name", ""),
            "salary": e.get("gross_salary", 0),
            "sfs_employee": e.get("sfs_employee", 0),
            "sfs_employer": e.get("sfs_employer", 0),
            "afp_employee": e.get("afp_employee", 0),
            "afp_employer": e.get("afp_employer", 0),
            "isr": e.get("isr", 0)
        })
    
    return {"rows": rows, "total_count": len(rows)}

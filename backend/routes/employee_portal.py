"""
Employee Self-Service Portal Routes for FortexaRH
Portal for employees to view their data, payslips, request vacations, etc.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import asyncio
import uuid
import logging
import math
import jwt
import bcrypt
import io

# PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

router = APIRouter(prefix="/employee-portal", tags=["Employee Portal"])

from config import db
from config import JWT_SECRET, JWT_ALGORITHM

logger = logging.getLogger(__name__)

from models.employee import (
    EmployeeLoginRequest, EmployeeUpdateRequest,
    PortalVacationRequestCreate as VacationRequestCreate,
    PortalLeaveRequestCreate as LeaveRequestCreate,
    MarkNotificationRead
)
from services.employee_notifications import (
    create_employee_notification as _create_notif,
    register_sse_connection,
    unregister_sse_connection,
)
import json


async def get_employee_from_token(request: Request):
    """Extract and verify employee from JWT token"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("portal_type") != "employee":
            raise HTTPException(status_code=401, detail="Token inválido para portal de empleados")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


# ===================== AUTHENTICATION =====================

@router.post("/login")
async def employee_login(data: EmployeeLoginRequest):
    """Login for employees using document number and password.

    Since the same document_number can exist across multiple companies
    (different tenants), iterate through all matches and authenticate against
    the one whose stored password verifies. This avoids the case where Mongo
    returns a non-matching duplicate first.
    """
    candidates = await db.employees.find(
        {"document_number": data.document_number},
        {"_id": 0}
    ).to_list(20)

    if not candidates:
        raise HTTPException(status_code=401, detail="Cédula o contraseña incorrecta")

    employee = None
    for emp in candidates:
        stored = emp.get("portal_password") or ""
        # First-login case (no password yet): allow if password equals the document_number
        if not stored:
            if data.password == data.document_number:
                hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
                await db.employees.update_one(
                    {"employee_id": emp["employee_id"], "company_id": emp["company_id"]},
                    {"$set": {"portal_password": hashed, "portal_enabled": True}}
                )
                employee = emp
                break
            continue
        # Existing password — check bcrypt
        try:
            if bcrypt.checkpw(data.password.encode(), stored.encode()):
                employee = emp
                break
        except (ValueError, TypeError):
            # Malformed hash — skip this candidate
            continue

    if not employee:
        raise HTTPException(status_code=401, detail="Cédula o contraseña incorrecta")

    # Ensure portal_enabled for the matched employee
    if not employee.get("portal_enabled", False):
        await db.employees.update_one(
            {"employee_id": employee["employee_id"], "company_id": employee["company_id"]},
            {"$set": {"portal_enabled": True}}
        )
    
    # Generate token
    token_payload = {
        "employee_id": employee["employee_id"],
        "company_id": employee["company_id"],
        "document_number": employee["document_number"],
        "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
        "portal_type": "employee",
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "token": token,
        "employee": {
            "employee_id": employee["employee_id"],
            "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
            "position": employee.get("position", ""),
            "department": employee.get("department", ""),
            "must_change_password": bool(employee.get("portal_must_change_password", False)),
        }
    }


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password")
async def change_employee_password(request: Request, data: ChangePasswordRequest):
    """Change employee password via JSON body"""
    emp_data = await get_employee_from_token(request)
    
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    stored_password = employee.get("portal_password", "")
    if stored_password and not bcrypt.checkpw(data.old_password.encode(), stored_password.encode()):
        raise HTTPException(status_code=401, detail="Contrasena actual incorrecta")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contrasena debe tener al menos 6 caracteres")
    
    hashed = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    await db.employees.update_one(
        {"employee_id": emp_data["employee_id"]},
        {"$set": {"portal_password": hashed, "portal_must_change_password": False}}
    )
    
    return {"message": "Contrasena actualizada"}


# ===================== PROFILE =====================

@router.get("/profile")
async def get_employee_profile(request: Request):
    """Get employee profile data"""
    emp_data = await get_employee_from_token(request)
    
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0, "portal_password": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Get company info
    company = await db.companies.find_one(
        {"company_id": emp_data["company_id"]},
        {"_id": 0, "name": 1, "logo_url": 1}
    )
    
    return {
        "employee": employee,
        "company": company
    }


@router.put("/profile")
async def update_employee_profile(data: EmployeeUpdateRequest, request: Request):
    """Update employee contact and bank info"""
    emp_data = await get_employee_from_token(request)
    
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.phone is not None:
        updates["phone"] = data.phone
    if data.address is not None:
        updates["address"] = data.address
    if data.email is not None:
        updates["personal_email"] = data.email
    if data.bank_name is not None:
        updates["bank_name"] = data.bank_name
    if data.bank_account is not None:
        updates["bank_account"] = data.bank_account
    if data.emergency_contact_name is not None:
        updates["emergency_contact_name"] = data.emergency_contact_name
    if data.emergency_contact_phone is not None:
        updates["emergency_contact_phone"] = data.emergency_contact_phone
    
    await db.employees.update_one(
        {"employee_id": emp_data["employee_id"]},
        {"$set": updates}
    )
    
    return {"message": "Datos actualizados"}


# ===================== PAYSLIPS =====================

@router.get("/payslips")
async def get_employee_payslips(request: Request, year: int = None):
    """Get employee payslips"""
    emp_data = await get_employee_from_token(request)
    
    query = {
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"]
    }
    
    if year:
        query["period"] = {"$regex": f"^{year}"}
    
    # Try payroll_v2 first (new format)
    payslips = await db.payroll_v2.find(
        query,
        {"_id": 0}
    ).sort("period", -1).to_list(24)
    
    # If no results, try old format
    if not payslips:
        payslips = await db.payroll_entries.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(24)
    
    return payslips


@router.get("/payslips/{payroll_id}")
async def get_payslip_detail(payroll_id: str, request: Request):
    """Get detailed payslip"""
    emp_data = await get_employee_from_token(request)
    
    # Try payroll_v2 first
    payslip = await db.payroll_v2.find_one(
        {
            "payroll_id": payroll_id,
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    )
    
    # If not found, try old format
    if not payslip:
        payslip = await db.payroll_entries.find_one(
            {
                "entry_id": payroll_id,
                "employee_id": emp_data["employee_id"],
                "company_id": emp_data["company_id"]
            },
            {"_id": 0}
        )
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Recibo no encontrado")
    
    return payslip


# ===================== VACATIONS =====================

@router.get("/vacations/balance")
async def get_vacation_balance(request: Request):
    """Get employee vacation balance"""
    emp_data = await get_employee_from_token(request)
    
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0, "hire_date": 1, "vacation_days_available": 1, "vacation_days_used": 1}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Calculate accrued days (1.17 days per month worked)
    hire_date = employee.get("hire_date")
    if hire_date:
        try:
            hire_dt = datetime.fromisoformat(hire_date.replace("Z", "+00:00"))
            months_worked = (datetime.now(timezone.utc) - hire_dt).days / 30
            accrued = round(months_worked * 1.17, 1)
        except:
            accrued = employee.get("vacation_days_available", 0)
    else:
        accrued = employee.get("vacation_days_available", 0)
    
    used = employee.get("vacation_days_used", 0)
    available = max(0, accrued - used)
    
    return {
        "accrued": round(accrued, 1),
        "used": used,
        "available": round(available, 1),
        "pending_requests": 0  # Will be calculated from vacation requests
    }


@router.get("/vacations/requests")
async def get_vacation_requests(request: Request):
    """Get employee vacation requests"""
    emp_data = await get_employee_from_token(request)
    
    requests = await db.vacations.find(
        {
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return requests


@router.post("/vacations/request")
async def create_vacation_request(data: VacationRequestCreate, request: Request):
    """Create a new vacation request"""
    emp_data = await get_employee_from_token(request)
    
    # Calculate days
    try:
        start = datetime.strptime(data.start_date, "%Y-%m-%d")
        end = datetime.strptime(data.end_date, "%Y-%m-%d")
        days = (end - start).days + 1
    except:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    
    if days <= 0:
        raise HTTPException(status_code=400, detail="La fecha de fin debe ser posterior a la de inicio")
    
    # Check balance
    balance = await get_vacation_balance(request)
    if days > balance["available"]:
        raise HTTPException(status_code=400, detail=f"No tiene suficientes días disponibles. Disponible: {balance['available']}")
    
    vacation_id = f"vac_{uuid.uuid4().hex[:8]}"
    vacation = {
        "vacation_id": vacation_id,
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days": days,
        "reason": data.reason,
        "status": "pending",
        "requested_via": "employee_portal",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.vacations.insert_one(vacation)
    
    return {
        "vacation_id": vacation_id,
        "message": "Solicitud enviada",
        "days": days
    }


# ===================== LOANS =====================

@router.get("/loans")
async def get_employee_loans(request: Request):
    """Get employee active loans"""
    emp_data = await get_employee_from_token(request)
    
    loans = await db.loans.find(
        {
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    # Calculate totals
    active_loans = [l for l in loans if l.get("status") == "active"]
    total_balance = sum(l.get("remaining_balance", 0) for l in active_loans)
    total_monthly = sum(l.get("monthly_payment", 0) for l in active_loans)
    
    return {
        "loans": loans,
        "summary": {
            "active_count": len(active_loans),
            "total_balance": round(total_balance, 2),
            "monthly_payment": round(total_monthly, 2)
        }
    }


@router.get("/loans/{loan_id}")
async def get_loan_detail(loan_id: str, request: Request):
    """Get loan detail with payment schedule"""
    emp_data = await get_employee_from_token(request)
    
    loan = await db.loans.find_one(
        {
            "loan_id": loan_id,
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    )
    
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    
    return loan


# ===================== DASHBOARD =====================

@router.get("/dashboard")
async def get_employee_dashboard(request: Request):
    """Get employee dashboard summary"""
    emp_data = await get_employee_from_token(request)
    
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0, "portal_password": 0}
    )
    
    # Get latest payslip from payroll_v2
    latest_payslip = await db.payroll_v2.find_one(
        {
            "employee_id": emp_data["employee_id"],
            "status": "paid"
        },
        {"_id": 0},
        sort=[("period", -1)]
    )
    
    # Fallback to old format if not found
    if not latest_payslip:
        latest_payslip = await db.payroll_entries.find_one(
            {
                "employee_id": emp_data["employee_id"],
                "status": "paid"
            },
            {"_id": 0},
            sort=[("created_at", -1)]
        )
    
    # Get vacation balance
    vacation_balance = await get_vacation_balance(request)
    
    # Get active loans
    active_loans = await db.loans.find(
        {
            "employee_id": emp_data["employee_id"],
            "status": "active"
        },
        {"_id": 0}
    ).to_list(10)
    
    loan_balance = sum(l.get("remaining_balance", 0) for l in active_loans)
    
    # Get pending vacation requests
    pending_vacations = await db.vacations.count_documents({
        "employee_id": emp_data["employee_id"],
        "status": "pending"
    })
    
    return {
        "employee": {
            "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
            "position": employee.get("position", ""),
            "department": employee.get("department", ""),
            "hire_date": employee.get("hire_date", ""),
            "photo_url": employee.get("photo_url", "")
        },
        "salary": {
            "latest_net": latest_payslip.get("net_salary", 0) if latest_payslip else 0,
            "latest_period": latest_payslip.get("period", "") if latest_payslip else "",
            "base_salary": employee.get("salary", 0)
        },
        "vacations": vacation_balance,
        "loans": {
            "active_count": len(active_loans),
            "total_balance": round(loan_balance, 2)
        },
        "pending_requests": pending_vacations
    }


# ===================== PAYSLIP PDF DOWNLOAD =====================

def format_currency(value):
    """Format value as Dominican Peso"""
    return f"RD${value:,.2f}" if value else "RD$0.00"


@router.get("/payslips/{payslip_id}/pdf")
async def download_payslip_pdf(payslip_id: str, request: Request):
    """Download payslip as PDF"""
    emp_data = await get_employee_from_token(request)
    
    # Get payslip - try payroll_v2 first, then legacy payroll_entries
    payslip = await db.payroll_v2.find_one(
        {
            "payroll_id": payslip_id,
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    )
    
    if not payslip:
        payslip = await db.payroll_entries.find_one(
            {
                "entry_id": payslip_id,
                "employee_id": emp_data["employee_id"],
                "company_id": emp_data["company_id"]
            },
            {"_id": 0}
        )
    
    if not payslip:
        raise HTTPException(status_code=404, detail="Recibo no encontrado")
    
    # Get company info
    company = await db.companies.find_one(
        {"company_id": emp_data["company_id"]},
        {"_id": 0, "name": 1, "rnc": 1, "address": 1}
    )
    company_name = company.get("name", "Empresa") if company else "Empresa"
    company_rnc = company.get("rnc", "") if company else ""
    
    # Get employee info
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0}
    )
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, spaceAfter=4)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=11, spaceAfter=8, spaceBefore=12)
    
    # Header
    elements.append(Paragraph(company_name, title_style))
    if company_rnc:
        elements.append(Paragraph(f"RNC: {company_rnc}", subtitle_style))
    elements.append(Paragraph("RECIBO DE NÓMINA", title_style))
    elements.append(Spacer(1, 15))
    
    # Employee Info
    emp_info = [
        ["DATOS DEL EMPLEADO", "", "", ""],
        ["Nombre:", f"{employee.get('first_name', '')} {employee.get('last_name', '')}", "Cédula:", employee.get('document_number', '')],
        ["Cargo:", employee.get('position', 'N/A'), "Departamento:", employee.get('department', 'N/A')],
        ["Período:", payslip.get('period', 'N/A'), "Fecha Pago:", payslip.get('payment_date', 'N/A')[:10] if payslip.get('payment_date') else 'N/A'],
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
    from services.payslip_lines import (
        build_earnings_lines,
        build_deductions_lines,
        total_deductions as compute_total_deductions,
    )
    earnings_lines = build_earnings_lines(payslip)
    earnings_data = [["INGRESOS", "MONTO"]]
    earnings_data.extend([label, format_currency(amount)] for label, amount in earnings_lines)
    earnings_data.append(["TOTAL INGRESOS", format_currency(payslip.get('gross_salary', 0))])
    
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
    deductions_lines = build_deductions_lines(payslip)
    deductions_data = [["DEDUCCIONES", "MONTO"]]
    deductions_data.extend([label, format_currency(amount)] for label, amount in deductions_lines)
    deductions_data.append(["TOTAL DEDUCCIONES", format_currency(compute_total_deductions(payslip))])
    
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
    net_data = [
        ["SALARIO NETO A PAGAR", format_currency(payslip.get('net_salary', 0))],
    ]
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
    footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} desde Portal de Empleados - http://fortexarh.com"
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    period = payslip.get('period', 'recibo').replace(' ', '_').replace('/', '-')
    filename = f"recibo_nomina_{period}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ===================== PERFORMANCE EVALUATIONS =====================

@router.get("/evaluations")
async def get_employee_evaluations(request: Request):
    """Get employee's performance evaluations"""
    emp_data = await get_employee_from_token(request)
    
    evaluations = await db.evaluations.find(
        {
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    ).sort("evaluation_date", -1).to_list(20)
    
    # Get cycle info for each evaluation
    for ev in evaluations:
        if ev.get("cycle_id"):
            cycle = await db.evaluation_cycles.find_one(
                {"cycle_id": ev["cycle_id"]},
                {"_id": 0, "name": 1}
            )
            ev["cycle_name"] = cycle.get("name") if cycle else "N/A"
    
    # Calculate averages
    completed = [e for e in evaluations if e.get("status") == "completed"]
    avg_score = sum(e.get("overall_score", 0) for e in completed) / len(completed) if completed else 0
    
    return {
        "evaluations": evaluations,
        "summary": {
            "total": len(evaluations),
            "completed": len(completed),
            "average_score": round(avg_score, 2),
            "pending": len([e for e in evaluations if e.get("status") == "pending"])
        }
    }


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation_detail(evaluation_id: str, request: Request):
    """Get detailed evaluation with competencies and feedback"""
    emp_data = await get_employee_from_token(request)
    
    evaluation = await db.evaluations.find_one(
        {
            "evaluation_id": evaluation_id,
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    )
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    
    # Get cycle info
    if evaluation.get("cycle_id"):
        cycle = await db.evaluation_cycles.find_one(
            {"cycle_id": evaluation["cycle_id"]},
            {"_id": 0, "name": 1, "description": 1}
        )
        evaluation["cycle_info"] = cycle
    
    # Get evaluator name if available
    if evaluation.get("evaluator_id"):
        evaluator = await db.users.find_one(
            {"user_id": evaluation["evaluator_id"]},
            {"_id": 0, "name": 1, "email": 1}
        )
        evaluation["evaluator_name"] = evaluator.get("name", evaluator.get("email")) if evaluator else "N/A"
    
    return evaluation


# ===================== LEAVE/PERMIT REQUESTS =====================

LEAVE_TYPES = {
    "sick": {"name": "Licencia por Enfermedad", "max_days": 3, "requires_doc": True},
    "personal": {"name": "Permiso Personal", "max_days": 1, "requires_doc": False},
    "bereavement": {"name": "Licencia por Duelo", "max_days": 3, "requires_doc": True},
    "maternity": {"name": "Licencia de Maternidad", "max_days": 84, "requires_doc": True},
    "paternity": {"name": "Licencia de Paternidad", "max_days": 2, "requires_doc": True},
    "medical_appointment": {"name": "Cita Médica", "max_days": 1, "requires_doc": True},
    "other": {"name": "Otro Permiso", "max_days": 1, "requires_doc": True},
}


@router.get("/leaves")
async def get_employee_leaves(request: Request):
    """Get employee's leave/permit requests"""
    emp_data = await get_employee_from_token(request)
    
    leaves = await db.leave_requests.find(
        {
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Add leave type names
    for leave in leaves:
        leave_info = LEAVE_TYPES.get(leave.get("leave_type"), {})
        leave["leave_type_name"] = leave_info.get("name", leave.get("leave_type"))
    
    # Summary
    pending = len([l for l in leaves if l.get("status") == "pending"])
    approved = len([l for l in leaves if l.get("status") == "approved"])
    
    return {
        "leaves": leaves,
        "summary": {
            "total": len(leaves),
            "pending": pending,
            "approved": approved,
            "rejected": len([l for l in leaves if l.get("status") == "rejected"])
        },
        "leave_types": LEAVE_TYPES
    }


@router.post("/leaves/request")
async def create_leave_request(data: LeaveRequestCreate, request: Request):
    """Create a new leave/permit request"""
    emp_data = await get_employee_from_token(request)
    
    # Validate leave type
    if data.leave_type not in LEAVE_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de permiso inválido")
    
    leave_info = LEAVE_TYPES[data.leave_type]
    
    # Calculate days
    try:
        start = datetime.strptime(data.start_date, "%Y-%m-%d")
        end = datetime.strptime(data.end_date, "%Y-%m-%d")
        days = (end - start).days + 1
    except:
        raise HTTPException(status_code=400, detail="Fechas inválidas")
    
    if days <= 0:
        raise HTTPException(status_code=400, detail="La fecha fin debe ser posterior a la fecha inicio")
    
    if days > leave_info["max_days"]:
        raise HTTPException(
            status_code=400, 
            detail=f"El máximo de días para {leave_info['name']} es {leave_info['max_days']}"
        )
    
    # Check if document is required
    if leave_info["requires_doc"] and not data.attachment_url and days > 1:
        # Only warn, don't block
        pass
    
    # Check for overlapping requests
    existing = await db.leave_requests.find_one({
        "employee_id": emp_data["employee_id"],
        "status": {"$in": ["pending", "approved"]},
        "$or": [
            {"start_date": {"$lte": data.end_date}, "end_date": {"$gte": data.start_date}},
        ]
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una solicitud para esas fechas")
    
    leave_id = f"leave_{uuid.uuid4().hex[:8]}"
    leave_request = {
        "leave_id": leave_id,
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
        "leave_type": data.leave_type,
        "leave_type_name": leave_info["name"],
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days": days,
        "reason": data.reason,
        "attachment_url": data.attachment_url,
        "status": "pending",
        "requested_via": "employee_portal",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.leave_requests.insert_one(leave_request)
    
    return {
        "leave_id": leave_id,
        "message": f"Solicitud de {leave_info['name']} enviada",
        "days": days
    }


# ===================== ATTENDANCE REGISTRATION =====================

@router.get("/attendance/today")
async def get_today_attendance(request: Request):
    """Get today's attendance record for employee"""
    emp_data = await get_employee_from_token(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    attendance = await db.attendances.find_one(
        {
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"],
            "date": today
        },
        {"_id": 0}
    )
    
    # Get employee's shift if any
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0, "shift_id": 1}
    )
    
    shift = None
    if employee and employee.get("shift_id"):
        shift = await db.shifts.find_one(
            {"shift_id": employee["shift_id"]},
            {"_id": 0}
        )

    # Geofence info for the portal UI: is enforcement active? which locations?
    company_id = emp_data["company_id"]
    has_locations = await db.geo_locations.find_one(
        {"company_id": company_id, "is_active": True},
        {"_id": 0, "location_id": 1},
    )
    geofence = {"required": bool(has_locations), "assigned_locations": []}
    if has_locations:
        assignments = await db.employee_locations.find(
            {"company_id": company_id, "employee_id": emp_data["employee_id"]},
            {"_id": 0, "location_id": 1},
        ).to_list(50)
        assigned_ids = [a["location_id"] for a in assignments]
        if assigned_ids:
            locs = await db.geo_locations.find(
                {
                    "company_id": company_id,
                    "location_id": {"$in": assigned_ids},
                    "is_active": True,
                },
                {"_id": 0, "location_id": 1, "name": 1, "address": 1,
                 "latitude": 1, "longitude": 1, "radius": 1},
            ).to_list(50)
            geofence["assigned_locations"] = locs

    return {
        "date": today,
        "attendance": attendance,
        "shift": shift,
        "can_check_in": attendance is None or not attendance.get("check_in"),
        "can_check_out": attendance is not None and attendance.get("check_in") and not attendance.get("check_out"),
        "geofence": geofence,
    }


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two GPS coordinates, in meters."""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


async def _validate_geofence_for_portal(
    company_id: str,
    employee_id: str,
    latitude: Optional[float],
    longitude: Optional[float],
):
    """Validate that the employee is within an allowed geofence.

    Strict policy (per product decision):
    - If the company has ANY active geo_locations, the employee MUST be assigned
      to at least one of them and MUST be inside its radius.
    - Without GPS coordinates from the client when enforcement applies, reject.
    - If the company has NO geo_locations at all, enforcement is OFF (back-compat).

    Returns: dict with location info ready to merge into the attendance record,
    or None if no enforcement applies.

    Raises HTTPException(403) with a clear message when validation fails.
    """
    has_locations = await db.geo_locations.find_one(
        {"company_id": company_id, "is_active": True},
        {"_id": 0, "location_id": 1},
    )
    if not has_locations:
        # Back-compat: company has not configured geofencing; allow.
        return None

    # GPS is required when enforcement applies
    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=403,
            detail=(
                "Tu empresa requiere ponchar con geolocalización activada. "
                "Habilita el permiso de ubicación en tu navegador o dispositivo."
            ),
        )

    # Employee MUST have at least one assignment (strict mode)
    assignments = await db.employee_locations.find(
        {"company_id": company_id, "employee_id": employee_id},
        {"_id": 0, "location_id": 1},
    ).to_list(50)
    assigned_ids = [a["location_id"] for a in assignments]

    if not assigned_ids:
        raise HTTPException(
            status_code=403,
            detail=(
                "No tienes una ubicación de trabajo asignada. "
                "Pídele a tu administrador que te asigne una ubicación para poder ponchar."
            ),
        )

    locations = await db.geo_locations.find(
        {
            "company_id": company_id,
            "location_id": {"$in": assigned_ids},
            "is_active": True,
        },
        {"_id": 0},
    ).to_list(50)

    if not locations:
        # All assigned locations are inactive or deleted
        raise HTTPException(
            status_code=403,
            detail=(
                "Tus ubicaciones asignadas no están activas. "
                "Contacta a tu administrador."
            ),
        )

    closest = None
    closest_distance = float("inf")
    for loc in locations:
        d = _haversine_meters(latitude, longitude, loc["latitude"], loc["longitude"])
        if d < closest_distance:
            closest_distance = d
            closest = loc
        if d <= loc.get("radius", 100):
            return {
                "latitude": latitude,
                "longitude": longitude,
                "geofence_location_id": loc["location_id"],
                "geofence_location_name": loc.get("name", ""),
                "geofence_distance_m": round(d, 2),
                "geofence_status": "within",
            }

    # Outside all assigned radii — hard block
    name = closest.get("name", "tu ubicación asignada") if closest else "tu ubicación asignada"
    radius = closest.get("radius", 0) if closest else 0
    raise HTTPException(
        status_code=403,
        detail=(
            f"Estás a {int(closest_distance)} m de {name} (radio permitido: {radius} m). "
            "Acércate a tu ubicación de trabajo para ponchar."
        ),
    )


class AttendanceCheckRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    selfie_base64: Optional[str] = None


async def _save_attendance_selfie(
    company_id: str,
    employee_id: str,
    mark_type: str,
    selfie_base64: Optional[str],
) -> Optional[str]:
    """Store the selfie in attendance_selfies collection. Returns selfie_id or None."""
    if not selfie_base64:
        return None
    # Basic sanity guard: reject payloads > ~4MB (base64 inflated)
    if len(selfie_base64) > 6_000_000:
        raise HTTPException(status_code=413, detail="La foto es demasiado grande. Intenta con una menor resolución.")
    selfie_id = f"selfie_{uuid.uuid4().hex[:12]}"
    await db.attendance_selfies.insert_one({
        "selfie_id": selfie_id,
        "company_id": company_id,
        "employee_id": employee_id,
        "mark_type": mark_type,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "image_data": selfie_base64,
        "source": "employee_portal",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return selfie_id


@router.post("/attendance/check-in")
async def employee_check_in(request: Request, data: Optional[AttendanceCheckRequest] = None):
    """Register employee check-in. Enforces geofence if the company has configured locations."""
    emp_data = await get_employee_from_token(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_time = datetime.now(timezone.utc).strftime("%H:%M:%S")

    payload = data or AttendanceCheckRequest()
    geo_info = await _validate_geofence_for_portal(
        emp_data["company_id"],
        emp_data["employee_id"],
        payload.latitude,
        payload.longitude,
    )

    # Check if already checked in
    existing = await db.attendances.find_one({
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
        "date": today
    })
    
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Ya registraste tu entrada hoy")
    
    # Get employee's shift to determine status
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0, "shift_id": 1}
    )
    
    status = "on_time"
    shift_start = "08:00:00"
    
    if employee and employee.get("shift_id"):
        shift = await db.shifts.find_one({"shift_id": employee["shift_id"]}, {"_id": 0})
        if shift:
            shift_start = shift.get("start_time", "08:00:00")
            # Allow 5 minutes grace period
            grace_time = datetime.strptime(shift_start, "%H:%M:%S") + timedelta(minutes=5)
            current_time = datetime.strptime(now_time, "%H:%M:%S")
            if current_time > grace_time:
                status = "late"
    
    attendance_id = f"att_{uuid.uuid4().hex[:8]}"

    base_update = {
        "check_in": now_time,
        "check_in_source": "employee_portal",
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if geo_info:
        base_update.update({
            "check_in_latitude": geo_info["latitude"],
            "check_in_longitude": geo_info["longitude"],
            "check_in_accuracy": payload.accuracy,
            "check_in_location_id": geo_info["geofence_location_id"],
            "check_in_location_name": geo_info["geofence_location_name"],
            "check_in_distance_m": geo_info["geofence_distance_m"],
        })

    selfie_id = await _save_attendance_selfie(
        emp_data["company_id"], emp_data["employee_id"], "entry", payload.selfie_base64,
    )
    if selfie_id:
        base_update["check_in_selfie_id"] = selfie_id

    if existing:
        # Update existing record
        await db.attendances.update_one(
            {"attendance_id": existing["attendance_id"]},
            {"$set": base_update}
        )
        attendance_id = existing["attendance_id"]
    else:
        # Create new record
        attendance = {
            "attendance_id": attendance_id,
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"],
            "date": today,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **base_update,
        }
        await db.attendances.insert_one(attendance)
    
    response = {
        "attendance_id": attendance_id,
        "message": "Entrada registrada correctamente",
        "check_in": now_time,
        "status": status,
        "status_message": "A tiempo" if status == "on_time" else "Tardanza registrada",
    }
    if geo_info:
        response["location"] = {
            "name": geo_info["geofence_location_name"],
            "distance_m": geo_info["geofence_distance_m"],
        }
    return response


@router.post("/attendance/check-out")
async def employee_check_out(request: Request, data: Optional[AttendanceCheckRequest] = None):
    """Register employee check-out. Enforces geofence if the company has configured locations."""
    emp_data = await get_employee_from_token(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_time = datetime.now(timezone.utc).strftime("%H:%M:%S")

    payload = data or AttendanceCheckRequest()
    geo_info = await _validate_geofence_for_portal(
        emp_data["company_id"],
        emp_data["employee_id"],
        payload.latitude,
        payload.longitude,
    )

    # Find today's attendance record
    attendance = await db.attendances.find_one({
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
        "date": today
    })
    
    if not attendance:
        raise HTTPException(status_code=400, detail="No tienes registro de entrada hoy")
    
    if attendance.get("check_out"):
        raise HTTPException(status_code=400, detail="Ya registraste tu salida hoy")
    
    # Calculate hours worked
    check_in = datetime.strptime(attendance["check_in"], "%H:%M:%S")
    check_out = datetime.strptime(now_time, "%H:%M:%S")
    hours_worked = (check_out - check_in).total_seconds() / 3600
    
    # Calculate overtime (assuming 8 hour workday)
    overtime_hours = max(0, hours_worked - 8)

    update_doc = {
        "check_out": now_time,
        "check_out_source": "employee_portal",
        "hours_worked": round(hours_worked, 2),
        "overtime_hours": round(overtime_hours, 2),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if geo_info:
        update_doc.update({
            "check_out_latitude": geo_info["latitude"],
            "check_out_longitude": geo_info["longitude"],
            "check_out_accuracy": payload.accuracy,
            "check_out_location_id": geo_info["geofence_location_id"],
            "check_out_location_name": geo_info["geofence_location_name"],
            "check_out_distance_m": geo_info["geofence_distance_m"],
        })

    selfie_id = await _save_attendance_selfie(
        emp_data["company_id"], emp_data["employee_id"], "exit", payload.selfie_base64,
    )
    if selfie_id:
        update_doc["check_out_selfie_id"] = selfie_id

    await db.attendances.update_one(
        {"attendance_id": attendance["attendance_id"]},
        {"$set": update_doc}
    )
    
    response = {
        "attendance_id": attendance["attendance_id"],
        "message": "Salida registrada correctamente",
        "check_out": now_time,
        "hours_worked": round(hours_worked, 2),
        "overtime_hours": round(overtime_hours, 2),
    }
    if geo_info:
        response["location"] = {
            "name": geo_info["geofence_location_name"],
            "distance_m": geo_info["geofence_distance_m"],
        }
    return response


@router.get("/attendance/history")
async def get_attendance_history(request: Request, month: Optional[str] = None):
    """Get attendance history for the employee"""
    emp_data = await get_employee_from_token(request)
    
    # Default to current month
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    # Build date range
    year, mon = month.split("-")
    start_date = f"{year}-{mon}-01"
    
    # Get last day of month
    if int(mon) == 12:
        end_date = f"{int(year)+1}-01-01"
    else:
        end_date = f"{year}-{int(mon)+1:02d}-01"
    
    records = await db.attendances.find(
        {
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"],
            "date": {"$gte": start_date, "$lt": end_date}
        },
        {"_id": 0}
    ).sort("date", -1).to_list(31)
    
    # Calculate summary
    total_hours = sum(r.get("hours_worked", 0) for r in records)
    total_overtime = sum(r.get("overtime_hours", 0) for r in records)
    on_time = len([r for r in records if r.get("status") == "on_time"])
    late = len([r for r in records if r.get("status") == "late"])
    
    return {
        "month": month,
        "records": records,
        "summary": {
            "days_worked": len(records),
            "total_hours": round(total_hours, 2),
            "total_overtime": round(total_overtime, 2),
            "on_time": on_time,
            "late": late,
            "attendance_rate": round((on_time / len(records) * 100), 1) if records else 0
        }
    }


# ===================== EMPLOYEE NOTIFICATIONS =====================

@router.get("/notifications")
async def get_employee_notifications(request: Request, limit: int = 50, unread_only: bool = False):
    """Get notifications for the employee"""
    emp_data = await get_employee_from_token(request)
    
    query = {
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"]
    }
    
    if unread_only:
        query["read"] = False
    
    notifications = await db.employee_notifications.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Count unread
    unread_count = await db.employee_notifications.count_documents({
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
        "read": False
    })
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, request: Request):
    """Mark a notification as read"""
    emp_data = await get_employee_from_token(request)
    
    result = await db.employee_notifications.update_one(
        {
            "notification_id": notification_id,
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"]
        },
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    
    return {"message": "Notificación marcada como leída"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(request: Request):
    """Mark all notifications as read"""
    emp_data = await get_employee_from_token(request)
    
    result = await db.employee_notifications.update_many(
        {
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"],
            "read": False
        },
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"{result.modified_count} notificaciones marcadas como leídas"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, request: Request):
    """Delete a notification"""
    emp_data = await get_employee_from_token(request)
    
    result = await db.employee_notifications.delete_one({
        "notification_id": notification_id,
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    
    return {"message": "Notificación eliminada"}


@router.get("/notifications/center")
async def get_notification_center(
    request: Request,
    category: str = None,
    search: str = None,
    skip: int = 0,
    limit: int = 20,
):
    """Get paginated, filtered notifications for the notification center."""
    emp_data = await get_employee_from_token(request)

    query = {
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
    }
    if category and category != "all":
        query["category"] = category
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"message": {"$regex": search, "$options": "i"}},
        ]

    total = await db.employee_notifications.count_documents(query)
    notifications = (
        await db.employee_notifications.find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    return {"notifications": notifications, "total": total, "skip": skip, "limit": limit}


@router.get("/notifications/categories")
async def get_notification_categories(request: Request):
    """Get distinct categories used in the employee's notifications."""
    emp_data = await get_employee_from_token(request)

    categories = await db.employee_notifications.distinct(
        "category",
        {"employee_id": emp_data["employee_id"], "company_id": emp_data["company_id"]},
    )
    return {"categories": categories}


@router.get("/notifications/export")
async def export_notifications_csv(request: Request, category: str = None, search: str = None):
    """Export notifications as CSV."""
    import csv
    import io
    from starlette.responses import StreamingResponse

    emp_data = await get_employee_from_token(request)

    query = {
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
    }
    if category and category != "all":
        query["category"] = category
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"message": {"$regex": search, "$options": "i"}},
        ]

    notifications = (
        await db.employee_notifications.find(query, {"_id": 0})
        .sort("created_at", -1)
        .to_list(500)
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Fecha", "Categoria", "Tipo", "Titulo", "Mensaje", "Leida"])
    for n in notifications:
        writer.writerow([
            n.get("created_at", ""),
            n.get("category", ""),
            n.get("type", ""),
            n.get("title", ""),
            n.get("message", ""),
            "Si" if n.get("read") else "No",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=notificaciones.csv"},
    )



# Helper function to create employee notifications (called from other routes)
async def create_employee_notification(
    employee_id: str,
    company_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    category: str = "general",
    action_url: str = None,
    metadata: dict = None,
):
    """Delegate to centralized service (keeps existing import path working)."""
    return await _create_notif(
        db, employee_id, company_id, title, message,
        notification_type, category, action_url, metadata,
    )


# ===================== SSE REAL-TIME STREAM =====================

@router.get("/notifications/stream")
async def notification_stream(request: Request, token: str = None):
    """SSE endpoint for real-time push notifications to employees.
    Accepts auth token as query param since EventSource doesn't support custom headers.
    """
    # Accept token from query param for SSE compatibility
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("portal_type") != "employee":
                raise HTTPException(status_code=401, detail="Token invalido")
            emp_data = payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token invalido")
    else:
        emp_data = await get_employee_from_token(request)

    employee_id = emp_data["employee_id"]

    queue = register_sse_connection(employee_id)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    notification = await asyncio.wait_for(queue.get(), timeout=30)
                    payload = {k: v for k, v in notification.items() if k != "_id"}
                    yield {
                        "event": "notification",
                        "data": json.dumps(payload, default=str),
                    }
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
        finally:
            unregister_sse_connection(employee_id, queue)

    return EventSourceResponse(event_generator())


# ===================== ANNOUNCEMENTS =====================

@router.get("/announcements")
async def get_company_announcements(request: Request):
    """Get company announcements for the employee"""
    emp_data = await get_employee_from_token(request)
    
    # Get announcements that are active and for all employees or this employee's department
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0, "department": 1}
    )
    
    now = datetime.now(timezone.utc).isoformat()
    emp_department = employee.get("department") if employee else None
    
    # Build query conditions
    query = {
        "company_id": emp_data["company_id"],
        "active": True,
        "$and": [
            {
                "$or": [
                    {"start_date": {"$lte": now}},
                    {"start_date": {"$exists": False}},
                    {"start_date": None}
                ]
            },
            {
                "$or": [
                    {"target_audience": "all"},
                    {"target_audience": {"$exists": False}},
                    {"target_audience": None},
                    {"target_departments": emp_department}
                ]
            }
        ]
    }
    
    announcements = await db.announcements.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {"announcements": announcements}


# ===================== PUSH NOTIFICATIONS =====================

@router.get("/push/vapid-key")
async def get_portal_vapid_key():
    """Return the VAPID public key for employee portal push subscription."""
    import os
    key = os.environ.get("VAPID_PUBLIC_KEY", "")
    return {"vapid_public_key": key}


@router.post("/push/subscribe")
async def portal_push_subscribe(request: Request):
    """Register a push subscription for an employee."""
    emp_data = await get_employee_from_token(request)
    body = await request.json()

    sub_data = {
        "user_id": emp_data['employee_id'],
        "company_id": emp_data.get("company_id"),
        "endpoint": body.get("endpoint"),
        "keys": body.get("keys", {}),
        "portal": "employee",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    await db.push_subscriptions.update_one(
        {"user_id": sub_data["user_id"], "endpoint": sub_data["endpoint"]},
        {"$set": sub_data},
        upsert=True
    )

    return {"message": "Suscripcion push registrada"}


@router.post("/push/unsubscribe")
async def portal_push_unsubscribe(request: Request):
    """Remove a push subscription for an employee."""
    emp_data = await get_employee_from_token(request)
    body = await request.json()
    endpoint = body.get("endpoint")

    await db.push_subscriptions.delete_one(
        {"user_id": emp_data['employee_id'], "endpoint": endpoint}
    )

    return {"message": "Suscripcion push eliminada"}


@router.get("/push/status")
async def portal_push_status(request: Request):
    """Check if employee has active push subscriptions."""
    emp_data = await get_employee_from_token(request)

    count = await db.push_subscriptions.count_documents(
        {"user_id": emp_data['employee_id']}
    )
    return {"subscribed": count > 0, "subscription_count": count}



# ===================== WORK LETTER & INCOME CERTIFICATE =====================

@router.get("/work-letter/pdf")
async def generate_work_letter(request: Request):
    """Generate a Work Letter (Carta de Trabajo) PDF"""
    emp_data = await get_employee_from_token(request)

    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]}, {"_id": 0}
    )
    company = await db.companies.find_one(
        {"company_id": emp_data["company_id"]},
        {"_id": 0, "name": 1, "company_name": 1, "rnc": 1, "address": 1}
    )
    company_name = (company or {}).get("company_name", (company or {}).get("name", "Empresa"))
    company_rnc = (company or {}).get("rnc", "")
    company_addr = (company or {}).get("address", "")

    emp_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
    hire_date = str(employee.get("hire_date", ""))[:10]
    position = employee.get("position", "N/A")
    department = employee.get("department", "N/A")
    doc_number = employee.get("document_number", "N/A")
    today = datetime.now(timezone.utc).strftime("%d de %B de %Y")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch, leftMargin=1*inch, rightMargin=1*inch)
    elements = []
    styles = getSampleStyleSheet()

    title_s = ParagraphStyle("T", parent=styles["Heading1"], fontSize=14, alignment=TA_CENTER, spaceAfter=20)
    body_s = ParagraphStyle("B", parent=styles["Normal"], fontSize=11, leading=18, spaceAfter=12, alignment=TA_LEFT)
    header_s = ParagraphStyle("H", parent=styles["Normal"], fontSize=11, alignment=TA_CENTER, spaceAfter=4)
    sign_s = ParagraphStyle("S", parent=styles["Normal"], fontSize=11, alignment=TA_LEFT, spaceBefore=40)

    # Header
    elements.append(Paragraph(f"<b>{company_name}</b>", header_s))
    if company_rnc:
        elements.append(Paragraph(f"RNC: {company_rnc}", header_s))
    if company_addr:
        elements.append(Paragraph(company_addr, header_s))
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("CARTA DE TRABAJO", title_s))
    elements.append(Spacer(1, 20))

    # Body
    elements.append(Paragraph("A QUIEN PUEDA INTERESAR:", body_s))
    elements.append(Spacer(1, 10))

    body_text = (
        f"Por medio de la presente, hacemos constar que el/la Sr(a). <b>{emp_name}</b>, "
        f"portador(a) de la cédula de identidad No. <b>{doc_number}</b>, labora en nuestra "
        f"empresa <b>{company_name}</b> desde el <b>{hire_date}</b>, desempeñando el cargo de "
        f"<b>{position}</b> en el departamento de <b>{department}</b>."
    )
    elements.append(Paragraph(body_text, body_s))

    elements.append(Paragraph(
        "Esta carta se expide a solicitud de la parte interesada, para los fines que estime conveniente.",
        body_s
    ))

    elements.append(Paragraph(f"Dada en la ciudad de Santo Domingo, a los {today}.", body_s))
    elements.append(Spacer(1, 40))

    elements.append(Paragraph("Atentamente,", sign_s))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_________________________________", sign_s))
    elements.append(Paragraph(f"<b>{company_name}</b>", sign_s))
    elements.append(Paragraph("Departamento de Recursos Humanos", sign_s))

    # Footer
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"Generado el {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} — FortexaRH",
        ParagraphStyle("F", fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    ))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="carta_trabajo_{emp_name.replace(" ","_")}.pdf"'}
    )


@router.get("/income-certificate/pdf")
async def generate_income_certificate(request: Request):
    """Generate an Income Certificate (Constancia de Ingresos) PDF"""
    emp_data = await get_employee_from_token(request)

    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]}, {"_id": 0}
    )
    company = await db.companies.find_one(
        {"company_id": emp_data["company_id"]},
        {"_id": 0, "name": 1, "company_name": 1, "rnc": 1, "address": 1}
    )
    company_name = (company or {}).get("company_name", (company or {}).get("name", "Empresa"))
    company_rnc = (company or {}).get("rnc", "")
    company_addr = (company or {}).get("address", "")

    emp_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
    doc_number = employee.get("document_number", "N/A")
    position = employee.get("position", "N/A")
    salary = employee.get("salary", 0)
    hire_date = str(employee.get("hire_date", ""))[:10]
    today = datetime.now(timezone.utc).strftime("%d de %B de %Y")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch, leftMargin=1*inch, rightMargin=1*inch)
    elements = []
    styles = getSampleStyleSheet()

    title_s = ParagraphStyle("T", parent=styles["Heading1"], fontSize=14, alignment=TA_CENTER, spaceAfter=20)
    body_s = ParagraphStyle("B", parent=styles["Normal"], fontSize=11, leading=18, spaceAfter=12, alignment=TA_LEFT)
    header_s = ParagraphStyle("H", parent=styles["Normal"], fontSize=11, alignment=TA_CENTER, spaceAfter=4)
    sign_s = ParagraphStyle("S", parent=styles["Normal"], fontSize=11, alignment=TA_LEFT, spaceBefore=40)

    elements.append(Paragraph(f"<b>{company_name}</b>", header_s))
    if company_rnc:
        elements.append(Paragraph(f"RNC: {company_rnc}", header_s))
    if company_addr:
        elements.append(Paragraph(company_addr, header_s))
    elements.append(Spacer(1, 30))

    elements.append(Paragraph("CONSTANCIA DE INGRESOS", title_s))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("A QUIEN PUEDA INTERESAR:", body_s))
    elements.append(Spacer(1, 10))

    salary_formatted = f"RD${salary:,.2f}"
    body_text = (
        f"Por medio de la presente, certificamos que el/la Sr(a). <b>{emp_name}</b>, "
        f"portador(a) de la cédula de identidad No. <b>{doc_number}</b>, labora en nuestra "
        f"empresa desde el <b>{hire_date}</b>, desempeñando el cargo de <b>{position}</b>, "
        f"devengando un salario mensual de <b>{salary_formatted}</b> (pesos dominicanos)."
    )
    elements.append(Paragraph(body_text, body_s))

    # Salary breakdown table
    monthly = salary
    biweekly = salary / 2
    daily = salary / 23.83
    annual = salary * 12

    sal_data = [
        ["DESGLOSE SALARIAL", "MONTO (RD$)"],
        ["Salario Mensual", f"{monthly:,.2f}"],
        ["Salario Quincenal", f"{biweekly:,.2f}"],
        ["Salario Diario", f"{daily:,.2f}"],
        ["Salario Anual", f"{annual:,.2f}"],
    ]

    sal_table = Table(sal_data, colWidths=[3.5*inch, 2*inch])
    sal_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(sal_table)
    elements.append(Spacer(1, 15))

    elements.append(Paragraph(
        "Esta constancia se expide a solicitud de la parte interesada, para los fines que estime conveniente.",
        body_s
    ))

    elements.append(Paragraph(f"Dada en la ciudad de Santo Domingo, a los {today}.", body_s))
    elements.append(Spacer(1, 40))

    elements.append(Paragraph("Atentamente,", sign_s))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("_________________________________", sign_s))
    elements.append(Paragraph(f"<b>{company_name}</b>", sign_s))
    elements.append(Paragraph("Departamento de Recursos Humanos", sign_s))

    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"Generado el {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')} — FortexaRH",
        ParagraphStyle("F", fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    ))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="constancia_ingresos_{emp_name.replace(" ","_")}.pdf"'}
    )


# ===================== EMPLOYEE CONTRACTS =====================

@router.get("/contracts")
async def get_employee_contracts(request: Request):
    """Get contracts for the current employee"""
    emp_data = await get_employee_from_token(request)

    contracts = await db.contracts.find(
        {"employee_id": emp_data["employee_id"], "company_id": emp_data["company_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)

    return {"contracts": contracts}


# ===================== PERMISSIONS / LICENSES =====================

class PermissionRequest(BaseModel):
    permission_type: str  # "medico", "personal", "duelo", "matrimonio", "paternidad", "maternidad", "otro"
    start_date: str
    end_date: str
    reason: str
    notes: Optional[str] = ""


@router.get("/permissions")
async def get_employee_permissions(request: Request):
    """Get permission/license requests for the current employee"""
    emp_data = await get_employee_from_token(request)

    permissions = await db.employee_permissions.find(
        {"employee_id": emp_data["employee_id"], "company_id": emp_data["company_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)

    return {"permissions": permissions}


@router.post("/permissions/request")
async def request_permission(data: PermissionRequest, request: Request):
    """Submit a permission/license request"""
    emp_data = await get_employee_from_token(request)

    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0, "first_name": 1, "last_name": 1, "department": 1}
    )
    emp_name = f"{(employee or {}).get('first_name', '')} {(employee or {}).get('last_name', '')}"

    # Calculate days
    try:
        start = datetime.strptime(data.start_date[:10], "%Y-%m-%d")
        end = datetime.strptime(data.end_date[:10], "%Y-%m-%d")
        days = (end - start).days + 1
    except (ValueError, TypeError):
        days = 1

    permission = {
        "permission_id": f"perm_{uuid.uuid4().hex[:12]}",
        "employee_id": emp_data["employee_id"],
        "company_id": emp_data["company_id"],
        "employee_name": emp_name,
        "department": (employee or {}).get("department", ""),
        "permission_type": data.permission_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days": days,
        "reason": data.reason,
        "notes": data.notes or "",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    await db.employee_permissions.insert_one(permission)

    return {"success": True, "permission_id": permission["permission_id"], "message": "Solicitud enviada"}

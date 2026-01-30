"""
Employee Self-Service Portal Routes for FortexaRH
Portal for employees to view their data, payslips, request vacations, etc.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid
import logging
import jwt
import bcrypt
import os
import io

# PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

router = APIRouter(prefix="/employee-portal", tags=["Employee Portal"])

db = None
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key")

logger = logging.getLogger(__name__)


class EmployeeLoginRequest(BaseModel):
    document_number: str  # Cédula
    password: str


class EmployeeUpdateRequest(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class VacationRequestCreate(BaseModel):
    start_date: str
    end_date: str
    reason: Optional[str] = None


def init_router(database):
    global db
    db = database


async def get_employee_from_token(request: Request):
    """Extract and verify employee from JWT token"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
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
    """Login for employees using document number and password"""
    # Find employee by document number
    employee = await db.employees.find_one(
        {"document_number": data.document_number},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=401, detail="Cédula o contraseña incorrecta")
    
    # Check if employee has portal access
    if not employee.get("portal_enabled", False):
        # Auto-enable and set default password (document number)
        default_password = bcrypt.hashpw(data.document_number.encode(), bcrypt.gensalt()).decode()
        await db.employees.update_one(
            {"employee_id": employee["employee_id"]},
            {"$set": {"portal_enabled": True, "portal_password": default_password}}
        )
        employee["portal_password"] = default_password
    
    # Verify password
    stored_password = employee.get("portal_password", "")
    if not stored_password:
        # First login - password is document number
        if data.password != data.document_number:
            raise HTTPException(status_code=401, detail="Cédula o contraseña incorrecta")
        # Set password
        hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        await db.employees.update_one(
            {"employee_id": employee["employee_id"]},
            {"$set": {"portal_password": hashed, "portal_enabled": True}}
        )
    else:
        if not bcrypt.checkpw(data.password.encode(), stored_password.encode()):
            raise HTTPException(status_code=401, detail="Cédula o contraseña incorrecta")
    
    # Generate token
    token_payload = {
        "employee_id": employee["employee_id"],
        "company_id": employee["company_id"],
        "document_number": employee["document_number"],
        "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
        "portal_type": "employee",
        "exp": datetime.now(timezone.utc) + timedelta(hours=8)
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
    
    return {
        "token": token,
        "employee": {
            "employee_id": employee["employee_id"],
            "name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
            "position": employee.get("position", ""),
            "department": employee.get("department", "")
        }
    }


@router.post("/change-password")
async def change_employee_password(request: Request, old_password: str, new_password: str):
    """Change employee password"""
    emp_data = await get_employee_from_token(request)
    
    employee = await db.employees.find_one(
        {"employee_id": emp_data["employee_id"]},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    stored_password = employee.get("portal_password", "")
    if stored_password and not bcrypt.checkpw(old_password.encode(), stored_password.encode()):
        raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
    
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    await db.employees.update_one(
        {"employee_id": emp_data["employee_id"]},
        {"$set": {"portal_password": hashed}}
    )
    
    return {"message": "Contraseña actualizada"}


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
    
    # Get payslip
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
    earnings_data = [
        ["INGRESOS", "MONTO"],
        ["Salario Base", format_currency(payslip.get('base_salary', 0))],
        ["Horas Extras", format_currency(payslip.get('overtime_pay', 0))],
        ["Bonificaciones", format_currency(payslip.get('bonuses', 0))],
        ["Comisiones", format_currency(payslip.get('commissions', 0))],
        ["Otros Ingresos", format_currency(payslip.get('other_income', 0))],
        ["TOTAL INGRESOS", format_currency(payslip.get('gross_salary', 0))],
    ]
    
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
    
    # Deductions
    deductions_data = [
        ["DEDUCCIONES", "MONTO"],
        ["SFS (Seguro Familiar de Salud)", format_currency(payslip.get('sfs_employee', 0))],
        ["AFP (Fondo de Pensiones)", format_currency(payslip.get('afp_employee', 0))],
        ["ISR (Impuesto Sobre la Renta)", format_currency(payslip.get('isr', 0))],
        ["Préstamos", format_currency(payslip.get('loan_deduction', 0))],
        ["Otras Deducciones", format_currency(payslip.get('other_deductions', 0))],
        ["TOTAL DEDUCCIONES", format_currency(
            (payslip.get('sfs_employee', 0) or 0) + 
            (payslip.get('afp_employee', 0) or 0) + 
            (payslip.get('isr', 0) or 0) + 
            (payslip.get('loan_deduction', 0) or 0) + 
            (payslip.get('other_deductions', 0) or 0)
        )],
    ]
    
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
    footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} desde Portal de Empleados"
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

class LeaveRequestCreate(BaseModel):
    leave_type: str  # sick, personal, bereavement, maternity, paternity, other
    start_date: str
    end_date: str
    reason: str
    attachment_url: Optional[str] = None


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
    
    return {
        "date": today,
        "attendance": attendance,
        "shift": shift,
        "can_check_in": attendance is None or not attendance.get("check_in"),
        "can_check_out": attendance is not None and attendance.get("check_in") and not attendance.get("check_out")
    }


@router.post("/attendance/check-in")
async def employee_check_in(request: Request):
    """Register employee check-in"""
    emp_data = await get_employee_from_token(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_time = datetime.now(timezone.utc).strftime("%H:%M:%S")
    
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
    
    if existing:
        # Update existing record
        await db.attendances.update_one(
            {"attendance_id": existing["attendance_id"]},
            {"$set": {
                "check_in": now_time,
                "check_in_source": "employee_portal",
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        attendance_id = existing["attendance_id"]
    else:
        # Create new record
        attendance = {
            "attendance_id": attendance_id,
            "employee_id": emp_data["employee_id"],
            "company_id": emp_data["company_id"],
            "date": today,
            "check_in": now_time,
            "check_in_source": "employee_portal",
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.attendances.insert_one(attendance)
    
    return {
        "attendance_id": attendance_id,
        "message": "Entrada registrada correctamente",
        "check_in": now_time,
        "status": status,
        "status_message": "A tiempo" if status == "on_time" else "Tardanza registrada"
    }


@router.post("/attendance/check-out")
async def employee_check_out(request: Request):
    """Register employee check-out"""
    emp_data = await get_employee_from_token(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_time = datetime.now(timezone.utc).strftime("%H:%M:%S")
    
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
    
    await db.attendances.update_one(
        {"attendance_id": attendance["attendance_id"]},
        {"$set": {
            "check_out": now_time,
            "check_out_source": "employee_portal",
            "hours_worked": round(hours_worked, 2),
            "overtime_hours": round(overtime_hours, 2),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "attendance_id": attendance["attendance_id"],
        "message": "Salida registrada correctamente",
        "check_out": now_time,
        "hours_worked": round(hours_worked, 2),
        "overtime_hours": round(overtime_hours, 2)
    }


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

class MarkNotificationRead(BaseModel):
    notification_id: str


@router.get("/notifications")
async def get_employee_notifications(request: Request, limit: int = 50, unread_only: bool = False):
    """Get notifications for the employee"""
    emp_data = await get_employee_from_token(request)
    
    logger.info(f"Fetching notifications for employee_id: {emp_data.get('employee_id')}, company_id: {emp_data.get('company_id')}")
    
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
    
    logger.info(f"Found {len(notifications)} notifications")
    
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


# Helper function to create employee notifications (called from other routes)
async def create_employee_notification(
    employee_id: str,
    company_id: str,
    title: str,
    message: str,
    notification_type: str = "info",  # info, success, warning, alert
    category: str = "general",  # payroll, vacation, attendance, announcement, document
    action_url: str = None,
    metadata: dict = None
):
    """Create a notification for an employee"""
    notification = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "employee_id": employee_id,
        "company_id": company_id,
        "title": title,
        "message": message,
        "type": notification_type,
        "category": category,
        "action_url": action_url,
        "metadata": metadata or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.employee_notifications.insert_one(notification)
    return notification


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

"""
Employee Self-Service Portal Routes for FortexaRH
Portal for employees to view their data, payslips, request vacations, etc.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid
import logging
import jwt
import bcrypt
import os

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

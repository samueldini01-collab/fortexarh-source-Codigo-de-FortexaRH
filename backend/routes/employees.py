"""
Employees Routes - FortexaRH
Handles employee CRUD operations
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/employees", tags=["Employees"])
security = HTTPBearer(auto_error=False)

# Will be initialized by init_router
db = None
_get_current_user_func = None
SUBSCRIPTION_PLANS = None


def init_router(database, auth_func, plans):
    global db, _get_current_user_func, SUBSCRIPTION_PLANS
    db = database
    _get_current_user_func = auth_func
    SUBSCRIPTION_PLANS = plans


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)



class EmployeeCreate(BaseModel):
    # Datos Principales
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    nationality: Optional[str] = "Dominicana"
    document_type: Optional[str] = "Cédula"
    document_number: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    marital_status: Optional[str] = "Soltero/a"
    blood_type: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    status: str = "active"
    address: Optional[str] = None
    city: Optional[str] = "Santo Domingo"
    photo_url: Optional[str] = None
    
    # Contrato
    position: str
    department: str
    hire_date: str
    contract_type: Optional[str] = "Indefinido"
    contract_end_date: Optional[str] = None
    salary: float
    supervisor: Optional[str] = None
    work_schedule: Optional[str] = "Lunes a Viernes 8:00 AM - 5:00 PM"
    exclude_from_payroll: bool = False
    last_raise_date: Optional[str] = None
    
    # Descuentos
    afp_discount: bool = True
    sfs_discount: bool = True
    isr_discount: bool = True
    additional_deductions: Optional[List[Dict[str, Any]]] = []
    
    # Forma de Pago
    payment_method: Optional[str] = "Transferencia Bancaria"
    payment_frequency: Optional[str] = "Quincenal"
    bank_name: Optional[str] = None
    account_type: Optional[str] = "Ahorros"
    account_number: Optional[str] = None
    
    # Contactos de Emergencia
    emergency_contacts: Optional[List[Dict[str, Any]]] = []


@router.get("")
async def get_employees(current_user: dict = Depends(get_current_user)):
    employees = await db.employees.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return employees


@router.post("")
async def create_employee(data: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Check subscription limit
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    plan = SUBSCRIPTION_PLANS.get(company.get("subscription_plan", "free"))
    current_count = company.get("employee_count", 0)
    
    if current_count >= plan["max_employees"]:
        raise HTTPException(status_code=403, detail=f"Plan limit reached. Upgrade to add more employees.")
    
    employee_id = f"emp_{uuid.uuid4().hex[:12]}"
    employee = {
        "employee_id": employee_id,
        "company_id": company_id,
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.employees.insert_one(employee)
    
    # Update employee count
    await db.companies.update_one(
        {"company_id": company_id},
        {"$inc": {"employee_count": 1}}
    )
    
    return {"employee_id": employee_id, "message": "Employee created successfully"}


@router.get("/{employee_id}")
async def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    result = await db.employees.update_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated successfully"}


@router.delete("/{employee_id}")
async def delete_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.employees.delete_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await db.companies.update_one(
        {"company_id": current_user.get("company_id")},
        {"$inc": {"employee_count": -1}}
    )
    return {"message": "Employee deleted successfully"}


@router.get("/{employee_id}/loans")
async def get_employee_loans(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get all loans for a specific employee"""
    company_id = current_user.get("company_id")
    loans = await db.loans.find(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(100)
    return loans

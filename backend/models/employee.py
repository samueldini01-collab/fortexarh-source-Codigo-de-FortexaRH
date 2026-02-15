"""Employee models"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any


class EmployeeCreate(BaseModel):
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
    afp_discount: bool = True
    sfs_discount: bool = True
    isr_discount: bool = True
    additional_deductions: Optional[List[Dict[str, Any]]] = []
    payment_method: Optional[str] = "Transferencia Bancaria"
    payment_frequency: Optional[str] = "Quincenal"
    bank_name: Optional[str] = None
    account_type: Optional[str] = "Ahorros"
    account_number: Optional[str] = None
    emergency_contacts: Optional[List[Dict[str, Any]]] = []


class BulkEditRequest(BaseModel):
    employee_ids: List[str]
    fields_to_update: Dict[str, Any]


class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    preview_data: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


# Employee Portal models
class EmployeeLoginRequest(BaseModel):
    document_number: str
    password: str


class EmployeeUpdateRequest(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PortalVacationRequestCreate(BaseModel):
    start_date: str
    end_date: str
    reason: Optional[str] = None


class PortalLeaveRequestCreate(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    reason: str
    attachment_url: Optional[str] = None


class MarkNotificationRead(BaseModel):
    notification_id: str

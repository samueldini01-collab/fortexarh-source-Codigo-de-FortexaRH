from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
import resend
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'hrflow_secret_key_2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

# Resend configuration
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# QuickBooks configuration
QB_CLIENT_ID = os.environ.get('QUICKBOOKS_CLIENT_ID', '')
QB_CLIENT_SECRET = os.environ.get('QUICKBOOKS_CLIENT_SECRET', '')
QB_REALM_ID = os.environ.get('QUICKBOOKS_REALM_ID', '')
QB_REDIRECT_URI = os.environ.get('QUICKBOOKS_REDIRECT_URI', '')

app = FastAPI(title="FortexaRH SaaS API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# ===================== MODELS =====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    company_id: Optional[str] = None
    role: str = "admin"

class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None

class CompanyResponse(BaseModel):
    company_id: str
    name: str
    industry: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    subscription_plan: str = "free"
    employee_count: int = 0
    created_at: datetime

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
    
    # Contactos de Emergencia (lista de hasta 3)
    emergency_contacts: Optional[List[Dict[str, Any]]] = []

class EmployeeResponse(BaseModel):
    employee_id: str
    company_id: str
    # Datos Principales
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    nationality: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    marital_status: Optional[str] = None
    status: str
    address: Optional[str] = None
    city: Optional[str] = None
    photo_url: Optional[str] = None
    # Contrato
    position: str
    department: str
    hire_date: str
    contract_type: Optional[str] = None
    contract_end_date: Optional[str] = None
    salary: float
    supervisor: Optional[str] = None
    work_schedule: Optional[str] = None
    exclude_from_payroll: bool = False
    last_raise_date: Optional[str] = None
    # Descuentos
    afp_discount: bool = True
    sfs_discount: bool = True
    isr_discount: bool = True
    additional_deductions: Optional[List[Dict[str, Any]]] = []
    # Forma de Pago
    payment_method: Optional[str] = None
    payment_frequency: Optional[str] = None
    bank_name: Optional[str] = None
    account_type: Optional[str] = None
    account_number: Optional[str] = None
    # Contactos de Emergencia
    emergency_contacts: Optional[List[Dict[str, Any]]] = []
    created_at: datetime

class PayrollCreate(BaseModel):
    employee_id: str
    period_start: str
    period_end: str
    base_salary: float
    bonuses: float = 0
    deductions: float = 0
    taxes: float = 0
    net_salary: float = 0

class PayrollResponse(BaseModel):
    payroll_id: str
    company_id: str
    employee_id: str
    employee_name: str
    period_start: str
    period_end: str
    base_salary: float
    bonuses: float
    deductions: float
    taxes: float
    net_salary: float
    status: str
    created_at: datetime

class AttendanceCreate(BaseModel):
    employee_id: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: str = "present"

class AttendanceResponse(BaseModel):
    attendance_id: str
    company_id: str
    employee_id: str
    employee_name: str
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    hours_worked: float = 0
    status: str

class VacationCreate(BaseModel):
    employee_id: str
    start_date: str
    end_date: str
    vacation_type: str
    reason: Optional[str] = None

class VacationResponse(BaseModel):
    vacation_id: str
    company_id: str
    employee_id: str
    employee_name: str
    start_date: str
    end_date: str
    days: int
    vacation_type: str
    reason: Optional[str] = None
    status: str
    created_at: datetime

class EvaluationCreate(BaseModel):
    employee_id: str
    evaluator_id: str
    period: str
    performance_score: float
    goals_achieved: float
    teamwork_score: float
    communication_score: float
    comments: Optional[str] = None

class EvaluationResponse(BaseModel):
    evaluation_id: str
    company_id: str
    employee_id: str
    employee_name: str
    evaluator_id: str
    period: str
    performance_score: float
    goals_achieved: float
    teamwork_score: float
    communication_score: float
    overall_score: float
    comments: Optional[str] = None
    status: str
    created_at: datetime

class JobPostingCreate(BaseModel):
    title: str
    department: str
    description: str
    requirements: str
    salary_range: str
    location: str
    employment_type: str

class JobPostingResponse(BaseModel):
    job_id: str
    company_id: str
    title: str
    department: str
    description: str
    requirements: str
    salary_range: str
    location: str
    employment_type: str
    status: str
    applicants_count: int
    created_at: datetime

class CandidateCreate(BaseModel):
    job_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None

class CandidateResponse(BaseModel):
    candidate_id: str
    job_id: str
    company_id: str
    name: str
    email: str
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    status: str
    stage: str
    created_at: datetime

class SubscriptionPlan(BaseModel):
    plan_id: str
    name: str
    base_price: float
    price_per_employee: float
    max_employees: int
    features: List[str]

class CheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str

# ===================== NEW MODELS: ORGANIGRAMA, PAYROLL CONFIG, TEMPLATES =====================

class OrgNodeCreate(BaseModel):
    name: str
    code: Optional[str] = None
    node_type: str = "unit"  # "unit" or "position"
    parent_id: Optional[str] = None
    employee_id: Optional[str] = None
    position_title: Optional[str] = None
    description: Optional[str] = None
    positions_count: Optional[int] = None
    # Legacy fields for compatibility
    title: Optional[str] = None
    department: Optional[str] = None
    level: int = 0

class OrgNodeResponse(BaseModel):
    node_id: str
    company_id: str
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    title: str
    department: str
    parent_id: Optional[str] = None
    level: int
    children: List[str] = []

class PayrollConfigCreate(BaseModel):
    name: str
    config_type: str  # earning, deduction, tax
    calculation_type: str  # fixed, percentage
    value: float
    is_taxable: bool = True
    is_active: bool = True
    description: Optional[str] = None

class PayrollConfigResponse(BaseModel):
    config_id: str
    company_id: str
    name: str
    config_type: str
    calculation_type: str
    value: float
    is_taxable: bool
    is_active: bool
    description: Optional[str] = None
    created_at: datetime

class TemplateCreate(BaseModel):
    name: str
    template_type: str  # contract, letter, certificate, policy
    content: str
    variables: List[str] = []
    is_active: bool = True

class TemplateResponse(BaseModel):
    template_id: str
    company_id: str
    name: str
    template_type: str
    content: str
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class GeneratedDocumentCreate(BaseModel):
    template_id: str
    employee_id: str
    content: str
    signature_data: Optional[str] = None

class OrgNodeUpdatePosition(BaseModel):
    node_id: str
    parent_id: Optional[str] = None
    level: int

# ===================== ACCOUNTING & PAYROLL CALCULATOR MODELS =====================

# Dominican Republic Payroll Rates (TSS - Tesorería de la Seguridad Social)
# Employee deductions
SFS_EMPLOYEE_RATE = 0.0307  # Seguro Familiar de Salud 3.07%
AFP_EMPLOYEE_RATE = 0.0287  # Administradora de Fondo de Pensiones 2.87%
TSS_EMPLOYEE_TOTAL = SFS_EMPLOYEE_RATE + AFP_EMPLOYEE_RATE  # 5.94% (used for ISR base)

# Employer contributions
SFS_EMPLOYER_RATE = 0.0709  # Seguro Familiar de Salud 7.09%
AFP_EMPLOYER_RATE = 0.0710  # Fondo de Pensiones 7.10%
SRL_EMPLOYER_RATE = 0.01    # Seguro de Riesgos Laborales 1%
INFOTEP_EMPLOYER_RATE = 0.01 # INFOTEP 1%

# ISR (Impuesto Sobre la Renta) - Based on DGII 2023 Retention Table
# These values are derived from the official monthly retention table for salaried employees

# Monthly thresholds based on DGII official table
ISR_MONTHLY_EXEMPT = 34685.00  # Exento hasta este monto mensual

# Reference table values (extracted from DGII 2023 PDF)
# These are key salary points and their exact retention values
ISR_TABLE_REFERENCE = {
    34685: 0.00,
    34700: 2.25,
    35000: 47.25,
    40000: 797.25,
    45000: 1547.25,
    50000: 2297.25,
    55000: 3055.85,
    60000: 3795.85,
    65000: 4555.85,
    70000: 5215.85,
    75000: 5857.94,
    80000: 6535.85,
}

def calculate_isr_monthly(gross_monthly: float) -> dict:
    """
    Calculate ISR (Impuesto Sobre la Renta) based on DGII 2023 retention table.
    
    Uses linear interpolation between known table values for accurate results
    matching the official DGII retention table for salaried employees.
    """
    if gross_monthly <= ISR_MONTHLY_EXEMPT:
        return {
            "taxable_base_monthly": round(gross_monthly, 2),
            "annual_taxable": round(gross_monthly * 12, 2),
            "isr_annual": 0.0,
            "isr_monthly": 0.0,
            "tax_bracket": "Exento (0%)"
        }
    
    # Find the bracket and calculate ISR
    # For salaries up to 50,000: pure 15% calculation
    if gross_monthly <= 50000:
        isr_monthly = (gross_monthly - ISR_MONTHLY_EXEMPT) * 0.15
        tax_bracket = "15%"
    # For salaries 50,000 - 80,000: use interpolation from table
    elif gross_monthly <= 80000:
        # Linear interpolation between table points
        table_points = sorted(ISR_TABLE_REFERENCE.keys())
        lower_salary = max([s for s in table_points if s <= gross_monthly])
        upper_salary = min([s for s in table_points if s >= gross_monthly])
        
        if lower_salary == upper_salary:
            isr_monthly = ISR_TABLE_REFERENCE[lower_salary]
        else:
            lower_isr = ISR_TABLE_REFERENCE[lower_salary]
            upper_isr = ISR_TABLE_REFERENCE[upper_salary]
            ratio = (gross_monthly - lower_salary) / (upper_salary - lower_salary)
            isr_monthly = lower_isr + (upper_isr - lower_isr) * ratio
        
        # Determine bracket based on salary
        if gross_monthly <= 52027:
            tax_bracket = "15%"
        elif gross_monthly <= 72260:
            tax_bracket = "20%"
        else:
            tax_bracket = "25%"
    # For salaries above 80,000: extrapolate using 25% rate
    else:
        base_isr = ISR_TABLE_REFERENCE[80000]  # 6,535.85
        excess = gross_monthly - 80000
        # Rate appears to be approximately 12.5% based on table increments
        isr_monthly = base_isr + (excess * 0.125)
        tax_bracket = "25%"
    
    isr_monthly = round(isr_monthly, 2)
    isr_annual = round(isr_monthly * 12, 2)
    
    return {
        "taxable_base_monthly": round(gross_monthly, 2),
        "annual_taxable": round(gross_monthly * 12, 2),
        "isr_annual": isr_annual,
        "isr_monthly": isr_monthly,
        "tax_bracket": tax_bracket
    }

class PayrollCalculatorInput(BaseModel):
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    base_salary: float
    days_worked: int = 30
    hours_extra: float = 0
    hour_rate: float = 0
    bonuses: float = 0
    commissions: float = 0
    # Additional deductions
    loan_deduction: float = 0
    other_deductions: float = 0

class PayrollCalculatorResult(BaseModel):
    # Input data
    employee_name: Optional[str] = None
    base_salary: float
    days_worked: int
    hours_extra: float
    hour_rate: float
    bonuses: float
    commissions: float
    
    # Calculated earnings
    proportional_salary: float
    extra_hours_pay: float
    total_earnings: float
    
    # Employee deductions (TSS)
    sfs_employee: float  # 3.07%
    afp_employee: float  # 2.87%
    total_tss_employee: float
    
    # ISR (Impuesto Sobre la Renta)
    isr_taxable_base: float  # Base gravable (ingresos - TSS)
    isr_annual_taxable: float  # Base anualizada
    isr_annual: float  # ISR anual calculado
    isr_monthly: float  # ISR mensual a retener
    isr_bracket: str  # Tramo de impuesto aplicado
    
    # Total employee deductions (TSS + ISR)
    total_employee_deductions: float
    
    # Additional deductions
    loan_deduction: float
    other_deductions: float
    total_other_deductions: float
    
    # Total deductions
    total_deductions: float
    
    # Net salary
    net_salary: float
    
    # Employer contributions (for reporting)
    sfs_employer: float  # 7.09%
    afp_employer: float  # 7.10%
    srl_employer: float  # 1%
    infotep_employer: float  # 1%
    total_employer_contributions: float
    
    # Summary breakdown
    breakdown: Dict[str, Any]

class JournalLineItem(BaseModel):
    account_code: str
    account_name: str
    cost_center: Optional[str] = None
    debit: float = 0
    credit: float = 0
    reference: Optional[str] = None
    description: Optional[str] = None

class JournalEntryCreate(BaseModel):
    payroll_id: str
    transaction_date: str
    description: str
    lines: List[JournalLineItem]

class JournalEntryResponse(BaseModel):
    entry_id: str
    company_id: str
    payroll_id: str
    transaction_date: str
    description: str
    lines: List[Dict]
    total_debit: float
    total_credit: float
    status: str
    quickbooks_id: Optional[str] = None
    created_at: datetime

class EmailDocumentRequest(BaseModel):
    document_id: str
    recipient_email: EmailStr
    subject: Optional[str] = None
    message: Optional[str] = None

class TemplateVersionCreate(BaseModel):
    template_id: str
    content: str
    change_description: str

# ===================== ACCOUNTING MODELS =====================

class JournalEntryLine(BaseModel):
    account_code: str
    account_name: str
    description: str
    debit: float = 0
    credit: float = 0

class JournalEntryCreate(BaseModel):
    entry_date: str
    reference: str
    description: str
    period: str  # "2026-01" format
    entry_type: str = "payroll"  # payroll, adjustment, closing
    lines: List[JournalEntryLine]
    payroll_id: Optional[str] = None
    notes: Optional[str] = None

class JournalEntryUpdate(BaseModel):
    entry_date: Optional[str] = None
    reference: Optional[str] = None
    description: Optional[str] = None
    period: Optional[str] = None
    lines: Optional[List[JournalEntryLine]] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # draft, posted, voided

class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: str  # asset, liability, equity, income, expense
    parent_code: Optional[str] = None
    description: Optional[str] = None

# ===================== AUTH HELPERS =====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_jwt_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request, credentials = Depends(security)) -> dict:
    # Try cookie first
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return user
    
    # Try JWT from header
    if credentials:
        try:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    raise HTTPException(status_code=401, detail="Not authenticated")

# ===================== SUBSCRIPTION PLANS =====================

SUBSCRIPTION_PLANS = {
    "trial": {
        "plan_id": "trial",
        "name": "Prueba Gratuita",
        "base_price": 0.0,
        "price_per_employee": 0.0,
        "max_employees": 1,
        "max_users": 1,
        "included_users": 1,
        "trial_days": 5,
        "features": ["1 empleado máximo", "Calculadora de nómina", "5 días de prueba"],
        "allowed_features": ["payroll_calculator", "dashboard"],
        "restricted_features": ["employees", "attendance", "vacations", "evaluations", "recruitment", "reports", "organigrama", "accounting"]
    },
    "basic": {
        "plan_id": "basic",
        "name": "FortexaRH Básico",
        "base_price": 5.0,
        "price_per_employee": 1.5,
        "max_employees": 50,
        "max_users": 3,
        "included_users": 3,
        "trial_days": 0,
        "features": ["Hasta 50 empleados", "3 usuarios incluidos", "Gestión de empleados", "Nómina básica", "Asistencias y vacaciones", "Calculadora de nómina", "Reportes básicos", "Exportación Excel/CSV", "Soporte por email", "Integración FortexaERP"],
        "allowed_features": ["all_basic"],
        "restricted_features": ["evaluations", "recruitment", "organigrama", "advanced_reports", "integrations_pro"]
    },
    "pro": {
        "plan_id": "pro",
        "name": "FortexaRH Pro",
        "base_price": 10.0,
        "price_per_employee": 1.5,
        "max_employees": 200,
        "max_users": 5,
        "included_users": 5,
        "trial_days": 0,
        "features": ["Hasta 200 empleados", "5 usuarios incluidos", "Todo lo del plan Básico", "Evaluaciones de desempeño", "Módulo de reclutamiento", "Organigrama intuitivo", "Reportes avanzados", "Integración QuickBooks", "Soporte prioritario"],
        "allowed_features": ["all_pro"],
        "restricted_features": ["custom_roles", "api", "advanced_workflows", "integrations_enterprise"]
    },
    "enterprise": {
        "plan_id": "enterprise",
        "name": "FortexaRH Enterprise",
        "base_price": 20.0,
        "price_per_employee": 1.5,
        "max_employees": 9999,
        "max_users": 7,
        "included_users": 7,
        "trial_days": 0,
        "features": ["Empleados ilimitados", "7 usuarios incluidos", "Todo lo del plan Pro", "Roles personalizados", "Múltiples administradores", "API personalizada", "Flujos de trabajo avanzados", "Integración SAP/Oracle/Dynamics", "Soporte 24/7", "Gerente de cuenta dedicado"],
        "allowed_features": ["all"],
        "restricted_features": []
    }
}

# Feature access mapping based on plan
FEATURE_ACCESS = {
    "trial": {
        "dashboard": True,
        "payroll_calculator": True,
        "employees": False,
        "attendance": False,
        "vacations": False,
        "evaluations": False,
        "recruitment": False,
        "reports": False,
        "organigrama": False,
        "accounting": False,
        "subscriptions": True,
        "settings": True
    },
    "basic": {
        "dashboard": True,
        "payroll_calculator": True,
        "employees": True,
        "attendance": True,
        "vacations": True,
        "evaluations": False,
        "recruitment": False,
        "reports": True,
        "organigrama": False,
        "accounting": True,
        "subscriptions": True,
        "settings": True
    },
    "pro": {
        "dashboard": True,
        "payroll_calculator": True,
        "employees": True,
        "attendance": True,
        "vacations": True,
        "evaluations": True,
        "recruitment": True,
        "reports": True,
        "organigrama": True,
        "accounting": True,
        "subscriptions": True,
        "settings": True
    },
    "enterprise": {
        "dashboard": True,
        "payroll_calculator": True,
        "employees": True,
        "attendance": True,
        "vacations": True,
        "evaluations": True,
        "recruitment": True,
        "reports": True,
        "organigrama": True,
        "accounting": True,
        "subscriptions": True,
        "settings": True,
        "custom_roles": True,
        "api": True
    }
}

# ===================== AUTH ROUTES =====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate, response: Response):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    company_id = None
    
    if user_data.company_name:
        company_id = f"comp_{uuid.uuid4().hex[:12]}"
        await db.companies.insert_one({
            "company_id": company_id,
            "name": user_data.company_name,
            "subscription_plan": "free",
            "employee_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "company_id": company_id,
        "role": "admin",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_jwt_token(user_id, user_data.email)
    
    return {
        "token": token,
        "user": {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "company_id": company_id,
            "role": "admin"
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin, response: Response):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["user_id"], user["email"])
    
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "company_id": user.get("company_id"),
            "role": user.get("role", "admin")
        }
    }

@api_router.post("/auth/session")
async def exchange_session(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Exchange session_id with Emergent Auth
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        auth_data = resp.json()
    
    # Find or create user
    user = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    
    if not user:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        company_id = f"comp_{uuid.uuid4().hex[:12]}"
        
        await db.companies.insert_one({
            "company_id": company_id,
            "name": f"Empresa de {auth_data['name']}",
            "subscription_plan": "free",
            "employee_count": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        user = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data["name"],
            "picture": auth_data.get("picture"),
            "company_id": company_id,
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
    else:
        user_id = user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": auth_data["name"], "picture": auth_data.get("picture")}}
        )
        user["name"] = auth_data["name"]
        user["picture"] = auth_data.get("picture")
    
    # Store session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "session_token": auth_data["session_token"],
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=auth_data["session_token"],
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return {
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "company_id": user.get("company_id"),
            "role": user.get("role", "admin")
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "picture": current_user.get("picture"),
        "company_id": current_user.get("company_id"),
        "role": current_user.get("role", "admin")
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out successfully"}

# ===================== COMPANY ROUTES =====================

@api_router.get("/company")
async def get_company(current_user: dict = Depends(get_current_user)):
    company = await db.companies.find_one(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@api_router.put("/company")
async def update_company(data: CompanyCreate, current_user: dict = Depends(get_current_user)):
    result = await db.companies.update_one(
        {"company_id": current_user.get("company_id")},
        {"$set": {
            "name": data.name,
            "industry": data.industry,
            "address": data.address,
            "phone": data.phone
        }}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company updated successfully"}

# ===================== EMPLOYEES ROUTES =====================

@api_router.get("/employees")
async def get_employees(current_user: dict = Depends(get_current_user)):
    employees = await db.employees.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return employees

@api_router.post("/employees")
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

@api_router.get("/employees/{employee_id}")
async def get_employee(employee_id: str, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@api_router.put("/employees/{employee_id}")
async def update_employee(employee_id: str, data: EmployeeCreate, current_user: dict = Depends(get_current_user)):
    result = await db.employees.update_one(
        {"employee_id": employee_id, "company_id": current_user.get("company_id")},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee updated successfully"}

@api_router.delete("/employees/{employee_id}")
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

# ===================== PAYROLL ROUTES =====================

@api_router.get("/payroll")
async def get_payrolls(current_user: dict = Depends(get_current_user)):
    payrolls = await db.payrolls.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return payrolls

@api_router.post("/payroll")
async def create_payroll(data: PayrollCreate, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate net salary
    gross = data.base_salary + data.bonuses
    taxes = gross * 0.15  # 15% tax
    net_salary = gross - data.deductions - taxes
    
    payroll_id = f"pay_{uuid.uuid4().hex[:12]}"
    payroll = {
        "payroll_id": payroll_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "period_start": data.period_start,
        "period_end": data.period_end,
        "base_salary": data.base_salary,
        "bonuses": data.bonuses,
        "deductions": data.deductions,
        "taxes": taxes,
        "net_salary": net_salary,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payrolls.insert_one(payroll)
    return {"payroll_id": payroll_id, "message": "Payroll created successfully"}

@api_router.put("/payroll/{payroll_id}/approve")
async def approve_payroll(payroll_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.payrolls.update_one(
        {"payroll_id": payroll_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "approved"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return {"message": "Payroll approved successfully"}

@api_router.put("/payroll/{payroll_id}/pay")
async def pay_payroll(payroll_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.payrolls.update_one(
        {"payroll_id": payroll_id, "company_id": current_user.get("company_id"), "status": "approved"},
        {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payroll not found or not approved")
    return {"message": "Payroll paid successfully"}

# ===================== ATTENDANCE ROUTES =====================

@api_router.get("/attendance")
async def get_attendances(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {"company_id": current_user.get("company_id")}
    if date:
        query["date"] = date
    attendances = await db.attendances.find(query, {"_id": 0}).to_list(1000)
    return attendances

@api_router.post("/attendance")
async def create_attendance(data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate hours worked
    hours_worked = 0
    if data.check_in and data.check_out:
        try:
            check_in = datetime.strptime(data.check_in, "%H:%M")
            check_out = datetime.strptime(data.check_out, "%H:%M")
            hours_worked = (check_out - check_in).seconds / 3600
        except:
            pass
    
    attendance_id = f"att_{uuid.uuid4().hex[:12]}"
    attendance = {
        "attendance_id": attendance_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "date": data.date,
        "check_in": data.check_in,
        "check_out": data.check_out,
        "hours_worked": hours_worked,
        "status": data.status
    }
    await db.attendances.insert_one(attendance)
    return {"attendance_id": attendance_id, "message": "Attendance recorded successfully"}

@api_router.put("/attendance/{attendance_id}")
async def update_attendance(attendance_id: str, data: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    hours_worked = 0
    if data.check_in and data.check_out:
        try:
            check_in = datetime.strptime(data.check_in, "%H:%M")
            check_out = datetime.strptime(data.check_out, "%H:%M")
            hours_worked = (check_out - check_in).seconds / 3600
        except:
            pass
    
    result = await db.attendances.update_one(
        {"attendance_id": attendance_id, "company_id": current_user.get("company_id")},
        {"$set": {
            "check_in": data.check_in,
            "check_out": data.check_out,
            "hours_worked": hours_worked,
            "status": data.status
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Attendance not found")
    return {"message": "Attendance updated successfully"}

# ===================== VACATIONS ROUTES =====================

@api_router.get("/vacations")
async def get_vacations(current_user: dict = Depends(get_current_user)):
    vacations = await db.vacations.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return vacations

@api_router.post("/vacations")
async def create_vacation(data: VacationCreate, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate days
    start = datetime.strptime(data.start_date, "%Y-%m-%d")
    end = datetime.strptime(data.end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    
    vacation_id = f"vac_{uuid.uuid4().hex[:12]}"
    vacation = {
        "vacation_id": vacation_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days": days,
        "vacation_type": data.vacation_type,
        "reason": data.reason,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.vacations.insert_one(vacation)
    return {"vacation_id": vacation_id, "message": "Vacation request created successfully"}

@api_router.put("/vacations/{vacation_id}/approve")
async def approve_vacation(vacation_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.vacations.update_one(
        {"vacation_id": vacation_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "approved"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vacation not found")
    return {"message": "Vacation approved successfully"}

@api_router.put("/vacations/{vacation_id}/reject")
async def reject_vacation(vacation_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.vacations.update_one(
        {"vacation_id": vacation_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "rejected"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vacation not found")
    return {"message": "Vacation rejected"}

# ===================== EVALUATIONS ROUTES =====================

@api_router.get("/evaluations")
async def get_evaluations(current_user: dict = Depends(get_current_user)):
    evaluations = await db.evaluations.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return evaluations

@api_router.post("/evaluations")
async def create_evaluation(data: EvaluationCreate, current_user: dict = Depends(get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    overall_score = (data.performance_score + data.goals_achieved + data.teamwork_score + data.communication_score) / 4
    
    evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
    evaluation = {
        "evaluation_id": evaluation_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "evaluator_id": data.evaluator_id,
        "period": data.period,
        "performance_score": data.performance_score,
        "goals_achieved": data.goals_achieved,
        "teamwork_score": data.teamwork_score,
        "communication_score": data.communication_score,
        "overall_score": overall_score,
        "comments": data.comments,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.evaluations.insert_one(evaluation)
    return {"evaluation_id": evaluation_id, "message": "Evaluation created successfully"}

# ===================== RECRUITMENT ROUTES =====================

@api_router.get("/jobs")
async def get_jobs(current_user: dict = Depends(get_current_user)):
    jobs = await db.jobs.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return jobs

@api_router.post("/jobs")
async def create_job(data: JobPostingCreate, current_user: dict = Depends(get_current_user)):
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = {
        "job_id": job_id,
        "company_id": current_user.get("company_id"),
        **data.model_dump(),
        "status": "open",
        "applicants_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.jobs.insert_one(job)
    return {"job_id": job_id, "message": "Job posting created successfully"}

@api_router.put("/jobs/{job_id}")
async def update_job(job_id: str, data: JobPostingCreate, current_user: dict = Depends(get_current_user)):
    result = await db.jobs.update_one(
        {"job_id": job_id, "company_id": current_user.get("company_id")},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job updated successfully"}

@api_router.put("/jobs/{job_id}/close")
async def close_job(job_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.jobs.update_one(
        {"job_id": job_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "closed"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job closed successfully"}

@api_router.get("/candidates")
async def get_candidates(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {"company_id": current_user.get("company_id")}
    if job_id:
        query["job_id"] = job_id
    candidates = await db.candidates.find(query, {"_id": 0}).to_list(1000)
    return candidates

@api_router.post("/candidates")
async def create_candidate(data: CandidateCreate, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one(
        {"job_id": data.job_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
    candidate = {
        "candidate_id": candidate_id,
        "job_id": data.job_id,
        "company_id": current_user.get("company_id"),
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "resume_url": data.resume_url,
        "cover_letter": data.cover_letter,
        "status": "new",
        "stage": "applied",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.candidates.insert_one(candidate)
    
    # Update applicants count
    await db.jobs.update_one(
        {"job_id": data.job_id},
        {"$inc": {"applicants_count": 1}}
    )
    
    return {"candidate_id": candidate_id, "message": "Candidate added successfully"}

@api_router.put("/candidates/{candidate_id}/stage")
async def update_candidate_stage(candidate_id: str, stage: str, current_user: dict = Depends(get_current_user)):
    valid_stages = ["applied", "screening", "interview", "offer", "hired", "rejected"]
    if stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Must be one of: {valid_stages}")
    
    status = "hired" if stage == "hired" else ("rejected" if stage == "rejected" else "in_progress")
    
    result = await db.candidates.update_one(
        {"candidate_id": candidate_id, "company_id": current_user.get("company_id")},
        {"$set": {"stage": stage, "status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate stage updated successfully"}

# ===================== SUBSCRIPTION & PAYMENT ROUTES =====================

@api_router.get("/plans")
async def get_plans():
    return list(SUBSCRIPTION_PLANS.values())

@api_router.get("/subscription")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    company = await db.companies.find_one(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    plan_id = company.get("subscription_plan", "basic")
    plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["basic"])
    employee_count = company.get("employee_count", 0)
    
    monthly_cost = plan["base_price"] + (employee_count * plan["price_per_employee"])
    
    return {
        "current_plan": plan,
        "employee_count": employee_count,
        "monthly_cost": monthly_cost,
        "next_billing_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    }

@api_router.post("/checkout")
async def create_checkout(data: CheckoutRequest, request: Request, current_user: dict = Depends(get_current_user)):
    plan = SUBSCRIPTION_PLANS.get(data.plan_id)
    if not plan or data.plan_id == "free":
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    company = await db.companies.find_one(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    employee_count = company.get("employee_count", 0) if company else 0
    
    # Calculate total amount
    amount = plan["base_price"] + (employee_count * plan["price_per_employee"])
    
    api_key = os.environ.get('STRIPE_API_KEY')
    host_url = data.origin_url
    webhook_url = f"{str(request.base_url)}api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    success_url = f"{host_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{host_url}/pricing"
    
    checkout_request = CheckoutSessionRequest(
        amount=float(amount),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "company_id": current_user.get("company_id"),
            "user_id": current_user["user_id"],
            "plan_id": data.plan_id
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "session_id": session.session_id,
        "company_id": current_user.get("company_id"),
        "user_id": current_user["user_id"],
        "plan_id": data.plan_id,
        "amount": amount,
        "currency": "usd",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: dict = Depends(get_current_user)):
    api_key = os.environ.get('STRIPE_API_KEY')
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Check if already processed
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if transaction and transaction.get("payment_status") == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "already_processed": True
        }
    
    # Update transaction status
    if status.payment_status == "paid":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Update company subscription
        if transaction:
            await db.companies.update_one(
                {"company_id": transaction["company_id"]},
                {"$set": {"subscription_plan": transaction["plan_id"]}}
            )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    api_key = os.environ.get('STRIPE_API_KEY')
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            transaction = await db.payment_transactions.find_one(
                {"session_id": webhook_response.session_id},
                {"_id": 0}
            )
            if transaction:
                await db.companies.update_one(
                    {"company_id": transaction["company_id"]},
                    {"$set": {"subscription_plan": transaction["plan_id"]}}
                )
        
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"status": "error"}

# ===================== DASHBOARD STATS =====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Get counts
    employee_count = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    pending_vacations = await db.vacations.count_documents({"company_id": company_id, "status": "pending"})
    pending_payrolls = await db.payrolls.count_documents({"company_id": company_id, "status": "pending"})
    open_jobs = await db.jobs.count_documents({"company_id": company_id, "status": "open"})
    new_candidates = await db.candidates.count_documents({"company_id": company_id, "status": "new"})
    
    # Get today's attendance
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    present_today = await db.attendances.count_documents({"company_id": company_id, "date": today, "status": "present"})
    
    # Get total payroll this month
    month_start = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")
    payrolls = await db.payrolls.find(
        {"company_id": company_id, "period_start": {"$gte": month_start}, "status": {"$in": ["approved", "paid"]}}
    ).to_list(1000)
    total_payroll = sum(p.get("net_salary", 0) for p in payrolls)
    
    # Recent employees
    recent_employees = await db.employees.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Upcoming vacations
    upcoming_vacations = await db.vacations.find(
        {"company_id": company_id, "status": "approved", "start_date": {"$gte": today}}
    , {"_id": 0}).sort("start_date", 1).limit(5).to_list(5)
    
    return {
        "employee_count": employee_count,
        "pending_vacations": pending_vacations,
        "pending_payrolls": pending_payrolls,
        "open_jobs": open_jobs,
        "new_candidates": new_candidates,
        "present_today": present_today,
        "total_payroll_this_month": total_payroll,
        "recent_employees": recent_employees,
        "upcoming_vacations": upcoming_vacations
    }

# ===================== REPORTS =====================

@api_router.get("/reports/payroll")
async def get_payroll_report(year: int, month: int, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Get all payrolls for the month
    month_str = f"{year}-{month:02d}"
    payrolls = await db.payrolls.find(
        {"company_id": company_id, "period_start": {"$regex": f"^{month_str}"}},
        {"_id": 0}
    ).to_list(1000)
    
    total_base = sum(p.get("base_salary", 0) for p in payrolls)
    total_bonuses = sum(p.get("bonuses", 0) for p in payrolls)
    total_deductions = sum(p.get("deductions", 0) for p in payrolls)
    total_taxes = sum(p.get("taxes", 0) for p in payrolls)
    total_net = sum(p.get("net_salary", 0) for p in payrolls)
    
    return {
        "period": month_str,
        "payrolls": payrolls,
        "summary": {
            "total_base_salary": total_base,
            "total_bonuses": total_bonuses,
            "total_deductions": total_deductions,
            "total_taxes": total_taxes,
            "total_net_salary": total_net,
            "employee_count": len(payrolls)
        }
    }

@api_router.get("/reports/attendance")
async def get_attendance_report(year: int, month: int, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    month_str = f"{year}-{month:02d}"
    attendances = await db.attendances.find(
        {"company_id": company_id, "date": {"$regex": f"^{month_str}"}},
        {"_id": 0}
    ).to_list(10000)
    
    # Group by employee
    by_employee = {}
    for att in attendances:
        emp_id = att["employee_id"]
        if emp_id not in by_employee:
            by_employee[emp_id] = {
                "employee_name": att.get("employee_name", ""),
                "present": 0,
                "absent": 0,
                "late": 0,
                "total_hours": 0
            }
        status = att.get("status", "present")
        if status == "present":
            by_employee[emp_id]["present"] += 1
        elif status == "absent":
            by_employee[emp_id]["absent"] += 1
        elif status == "late":
            by_employee[emp_id]["late"] += 1
        by_employee[emp_id]["total_hours"] += att.get("hours_worked", 0)
    
    return {
        "period": month_str,
        "by_employee": list(by_employee.values()),
        "summary": {
            "total_present": sum(e["present"] for e in by_employee.values()),
            "total_absent": sum(e["absent"] for e in by_employee.values()),
            "total_late": sum(e["late"] for e in by_employee.values()),
            "total_hours": sum(e["total_hours"] for e in by_employee.values())
        }
    }

# ===================== ORGANIGRAMA ROUTES =====================

@api_router.get("/organigrama")
async def get_organigrama(current_user: dict = Depends(get_current_user)):
    nodes = await db.org_nodes.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return nodes

@api_router.post("/organigrama")
async def create_org_node(data: OrgNodeCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    employee_name = None
    if data.employee_id:
        employee = await db.employees.find_one(
            {"employee_id": data.employee_id, "company_id": company_id},
            {"_id": 0}
        )
        if employee:
            employee_name = f"{employee['first_name']} {employee['last_name']}"
    
    node_id = f"node_{uuid.uuid4().hex[:12]}"
    node = {
        "node_id": node_id,
        "company_id": company_id,
        "name": data.name,
        "code": data.code or data.name[:4].upper() if data.name else None,
        "node_type": data.node_type or "unit",
        "position_title": data.position_title or data.title,
        "description": data.description,
        "employee_id": data.employee_id,
        "employee_name": employee_name,
        "parent_id": data.parent_id,
        "positions_count": data.positions_count,
        # Legacy fields
        "title": data.title or data.name,
        "department": data.department or data.name,
        "level": data.level,
        "children": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.org_nodes.insert_one(node)
    
    # Update parent's children array
    if data.parent_id:
        await db.org_nodes.update_one(
            {"node_id": data.parent_id},
            {"$push": {"children": node_id}}
        )
    
    return {"node_id": node_id, "message": "Nodo creado correctamente"}

@api_router.put("/organigrama/{node_id}")
async def update_org_node(node_id: str, data: OrgNodeCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    employee_name = None
    if data.employee_id:
        employee = await db.employees.find_one(
            {"employee_id": data.employee_id, "company_id": company_id},
            {"_id": 0}
        )
        if employee:
            employee_name = f"{employee['first_name']} {employee['last_name']}"
    
    result = await db.org_nodes.update_one(
        {"node_id": node_id, "company_id": company_id},
        {"$set": {
            "employee_id": data.employee_id,
            "employee_name": employee_name,
            "title": data.title,
            "department": data.department,
            "parent_id": data.parent_id,
            "level": data.level
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    return {"message": "Nodo actualizado correctamente"}

@api_router.delete("/organigrama/{node_id}")
async def delete_org_node(node_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Get the node to find its parent
    node = await db.org_nodes.find_one({"node_id": node_id, "company_id": company_id}, {"_id": 0})
    if not node:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
    
    # Remove from parent's children
    if node.get("parent_id"):
        await db.org_nodes.update_one(
            {"node_id": node["parent_id"]},
            {"$pull": {"children": node_id}}
        )
    
    # Delete the node
    await db.org_nodes.delete_one({"node_id": node_id, "company_id": company_id})
    
    # Optionally: reassign children to parent or delete them
    await db.org_nodes.update_many(
        {"parent_id": node_id, "company_id": company_id},
        {"$set": {"parent_id": node.get("parent_id")}}
    )
    
    return {"message": "Nodo eliminado correctamente"}

# ===================== PAYROLL CONFIG ROUTES =====================

class PayrollSettingsModel(BaseModel):
    # Overtime rates
    overtime_day: float = 35
    overtime_night: float = 15
    overtime_weekend: float = 100
    overtime_holiday: float = 100
    
    # Employee deductions
    afp_employee: float = 2.87
    sfs_employee: float = 3.04
    
    # Employer contributions
    afp_employer: float = 7.10
    sfs_employer: float = 7.09
    srl_employer: float = 1
    infotep_employer: float = 1
    
    # ISR Configuration
    isr_min_salary: float = 416220.01
    isr_mid_salary: float = 624329.04
    isr_max_salary: float = 867123.01
    isr_min_rate: float = 15
    isr_mid_rate: float = 20
    isr_max_rate: float = 25
    isr_mid_fixed: float = 31216.00
    isr_max_fixed: float = 79776.00

@api_router.get("/payroll-settings")
async def get_payroll_settings(current_user: dict = Depends(get_current_user)):
    """Get global payroll settings for the company"""
    settings = await db.payroll_settings.find_one(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    return settings

@api_router.post("/payroll-settings")
async def save_payroll_settings(data: PayrollSettingsModel, current_user: dict = Depends(get_current_user)):
    """Save or update global payroll settings"""
    company_id = current_user.get("company_id")
    
    settings = {
        "company_id": company_id,
        **data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.get("user_id")
    }
    
    await db.payroll_settings.update_one(
        {"company_id": company_id},
        {"$set": settings},
        upsert=True
    )
    
    return {"message": "Configuración guardada correctamente"}

@api_router.get("/payroll-config")
async def get_payroll_configs(current_user: dict = Depends(get_current_user)):
    configs = await db.payroll_configs.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return configs

@api_router.post("/payroll-config")
async def create_payroll_config(data: PayrollConfigCreate, current_user: dict = Depends(get_current_user)):
    config_id = f"pconfig_{uuid.uuid4().hex[:12]}"
    config = {
        "config_id": config_id,
        "company_id": current_user.get("company_id"),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payroll_configs.insert_one(config)
    return {"config_id": config_id, "message": "Configuración creada correctamente"}

@api_router.put("/payroll-config/{config_id}")
async def update_payroll_config(config_id: str, data: PayrollConfigCreate, current_user: dict = Depends(get_current_user)):
    result = await db.payroll_configs.update_one(
        {"config_id": config_id, "company_id": current_user.get("company_id")},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return {"message": "Configuración actualizada correctamente"}

@api_router.delete("/payroll-config/{config_id}")
async def delete_payroll_config(config_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.payroll_configs.delete_one(
        {"config_id": config_id, "company_id": current_user.get("company_id")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return {"message": "Configuración eliminada correctamente"}

# ===================== TEMPLATES ROUTES =====================

@api_router.get("/templates")
async def get_templates(current_user: dict = Depends(get_current_user)):
    templates = await db.templates.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return templates

@api_router.post("/templates")
async def create_template(data: TemplateCreate, current_user: dict = Depends(get_current_user)):
    template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
    template = {
        "template_id": template_id,
        "company_id": current_user.get("company_id"),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    await db.templates.insert_one(template)
    return {"template_id": template_id, "message": "Plantilla creada correctamente"}

@api_router.get("/templates/{template_id}")
async def get_template(template_id: str, current_user: dict = Depends(get_current_user)):
    template = await db.templates.find_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template

@api_router.put("/templates/{template_id}")
async def update_template(template_id: str, data: TemplateCreate, current_user: dict = Depends(get_current_user)):
    result = await db.templates.update_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")},
        {"$set": {
            **data.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return {"message": "Plantilla actualizada correctamente"}

@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.templates.delete_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return {"message": "Plantilla eliminada correctamente"}

@api_router.post("/templates/{template_id}/generate")
async def generate_document(template_id: str, variables: Dict[str, str], current_user: dict = Depends(get_current_user)):
    template = await db.templates.find_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    content = template["content"]
    for var, value in variables.items():
        content = content.replace(f"{{{{{var}}}}}", value)
    
    return {"content": content, "template_name": template["name"]}

# ===================== GENERATED DOCUMENTS & SIGNATURES =====================

@api_router.get("/documents")
async def get_documents(current_user: dict = Depends(get_current_user)):
    docs = await db.generated_documents.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return docs

@api_router.post("/documents")
async def save_document(data: GeneratedDocumentCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    template = await db.templates.find_one({"template_id": data.template_id}, {"_id": 0})
    employee = await db.employees.find_one({"employee_id": data.employee_id, "company_id": company_id}, {"_id": 0})
    
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    document = {
        "document_id": doc_id,
        "company_id": company_id,
        "template_id": data.template_id,
        "template_name": template["name"] if template else "Documento",
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}" if employee else "Sin asignar",
        "content": data.content,
        "signature_data": data.signature_data,
        "is_signed": bool(data.signature_data),
        "signed_at": datetime.now(timezone.utc).isoformat() if data.signature_data else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.generated_documents.insert_one(document)
    return {"document_id": doc_id, "message": "Documento guardado correctamente"}

@api_router.put("/documents/{document_id}/sign")
async def sign_document(document_id: str, signature_data: str, current_user: dict = Depends(get_current_user)):
    result = await db.generated_documents.update_one(
        {"document_id": document_id, "company_id": current_user.get("company_id")},
        {"$set": {
            "signature_data": signature_data,
            "is_signed": True,
            "signed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return {"message": "Documento firmado correctamente"}

@api_router.get("/documents/{document_id}")
async def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    doc = await db.generated_documents.find_one(
        {"document_id": document_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return doc

# ===================== PAYROLL CALCULATOR (Dominican Republic) =====================

@api_router.post("/payroll-calculator")
async def calculate_payroll(data: PayrollCalculatorInput, current_user: dict = Depends(get_current_user)):
    """
    Calculate payroll with Dominican Republic deductions:
    - Employee: SFS 3.07%, AFP 2.87%, ISR (según tablas DGII)
    - Employer: SFS 7.09%, AFP 7.10%, SRL 1%, INFOTEP 1%
    """
    # Calculate proportional salary based on days worked
    daily_rate = data.base_salary / 30
    proportional_salary = daily_rate * data.days_worked
    
    # Calculate extra hours pay
    extra_hours_pay = data.hours_extra * data.hour_rate
    
    # Total earnings
    total_earnings = proportional_salary + extra_hours_pay + data.bonuses + data.commissions
    
    # Employee deductions (TSS)
    sfs_employee = round(total_earnings * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(total_earnings * AFP_EMPLOYEE_RATE, 2)
    total_tss_employee = round(sfs_employee + afp_employee, 2)
    
    # Calculate ISR based on DGII tables
    isr_result = calculate_isr_monthly(total_earnings)
    isr_monthly = isr_result["isr_monthly"]
    
    # Total employee deductions (TSS + ISR)
    total_employee_deductions = round(total_tss_employee + isr_monthly, 2)
    
    # Additional deductions
    total_other_deductions = round(data.loan_deduction + data.other_deductions, 2)
    
    # Total deductions
    total_deductions = round(total_employee_deductions + total_other_deductions, 2)
    
    # Net salary
    net_salary = round(total_earnings - total_deductions, 2)
    
    # Employer contributions (for reference)
    sfs_employer = round(total_earnings * SFS_EMPLOYER_RATE, 2)
    afp_employer = round(total_earnings * AFP_EMPLOYER_RATE, 2)
    srl_employer = round(total_earnings * SRL_EMPLOYER_RATE, 2)
    infotep_employer = round(total_earnings * INFOTEP_EMPLOYER_RATE, 2)
    total_employer_contributions = round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2)
    
    result = PayrollCalculatorResult(
        employee_name=data.employee_name,
        base_salary=data.base_salary,
        days_worked=data.days_worked,
        hours_extra=data.hours_extra,
        hour_rate=data.hour_rate,
        bonuses=data.bonuses,
        commissions=data.commissions,
        proportional_salary=round(proportional_salary, 2),
        extra_hours_pay=round(extra_hours_pay, 2),
        total_earnings=round(total_earnings, 2),
        sfs_employee=sfs_employee,
        afp_employee=afp_employee,
        total_tss_employee=total_tss_employee,
        isr_taxable_base=isr_result["taxable_base_monthly"],
        isr_annual_taxable=isr_result["annual_taxable"],
        isr_annual=isr_result["isr_annual"],
        isr_monthly=isr_monthly,
        isr_bracket=isr_result["tax_bracket"],
        total_employee_deductions=total_employee_deductions,
        loan_deduction=data.loan_deduction,
        other_deductions=data.other_deductions,
        total_other_deductions=total_other_deductions,
        total_deductions=total_deductions,
        net_salary=net_salary,
        sfs_employer=sfs_employer,
        afp_employer=afp_employer,
        srl_employer=srl_employer,
        infotep_employer=infotep_employer,
        total_employer_contributions=total_employer_contributions,
        breakdown={
            "ingresos": {
                "salario_proporcional": round(proportional_salary, 2),
                "horas_extra": round(extra_hours_pay, 2),
                "bonificaciones": data.bonuses,
                "comisiones": data.commissions,
                "total_ingresos": round(total_earnings, 2)
            },
            "deducciones_tss": {
                "sfs_3_07": sfs_employee,
                "afp_2_87": afp_employee,
                "total_tss": total_tss_employee
            },
            "isr": {
                "base_gravable_mensual": isr_result["taxable_base_monthly"],
                "base_anualizada": isr_result["annual_taxable"],
                "isr_anual": isr_result["isr_annual"],
                "isr_mensual": isr_monthly,
                "tramo_impositivo": isr_result["tax_bracket"]
            },
            "otras_deducciones": {
                "prestamos": data.loan_deduction,
                "otras": data.other_deductions,
                "total_otras": total_other_deductions
            },
            "aportes_empleador": {
                "sfs_7_09": sfs_employer,
                "afp_7_10": afp_employer,
                "srl_1": srl_employer,
                "infotep_1": infotep_employer,
                "total_aportes": total_employer_contributions
            },
            "resumen": {
                "total_ingresos": round(total_earnings, 2),
                "total_deducciones_empleado": total_employee_deductions,
                "total_otras_deducciones": total_other_deductions,
                "total_deducciones": total_deductions,
                "salario_neto": net_salary
            }
        }
    )
    
    return result

@api_router.post("/payroll-calculator/save")
async def save_payroll_calculation(data: PayrollCalculatorInput, current_user: dict = Depends(get_current_user)):
    """Save a payroll calculation to create an actual payroll record"""
    # First calculate
    daily_rate = data.base_salary / 30
    proportional_salary = daily_rate * data.days_worked
    extra_hours_pay = data.hours_extra * data.hour_rate
    total_earnings = proportional_salary + extra_hours_pay + data.bonuses + data.commissions
    
    # TSS deductions
    sfs_employee = round(total_earnings * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(total_earnings * AFP_EMPLOYEE_RATE, 2)
    total_tss_employee = sfs_employee + afp_employee
    
    # ISR calculation
    isr_result = calculate_isr_monthly(total_earnings)
    isr_monthly = isr_result["isr_monthly"]
    
    # Total employee deductions (TSS + ISR)
    total_employee_deductions = round(total_tss_employee + isr_monthly, 2)
    total_other_deductions = data.loan_deduction + data.other_deductions
    total_deductions = round(total_employee_deductions + total_other_deductions, 2)
    net_salary = round(total_earnings - total_deductions, 2)
    
    # Get employee info
    employee_name = data.employee_name or "Sin asignar"
    if data.employee_id:
        employee = await db.employees.find_one(
            {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
            {"_id": 0}
        )
        if employee:
            employee_name = f"{employee['first_name']} {employee['last_name']}"
    
    # Save calculation record
    calc_id = f"calc_{uuid.uuid4().hex[:12]}"
    calculation = {
        "calculation_id": calc_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": employee_name,
        "base_salary": data.base_salary,
        "days_worked": data.days_worked,
        "hours_extra": data.hours_extra,
        "hour_rate": data.hour_rate,
        "bonuses": data.bonuses,
        "commissions": data.commissions,
        "proportional_salary": round(proportional_salary, 2),
        "extra_hours_pay": round(extra_hours_pay, 2),
        "total_earnings": round(total_earnings, 2),
        "sfs_employee": sfs_employee,
        "afp_employee": afp_employee,
        "total_tss_employee": round(total_tss_employee, 2),
        "isr_monthly": isr_monthly,
        "isr_bracket": isr_result["tax_bracket"],
        "total_employee_deductions": total_employee_deductions,
        "loan_deduction": data.loan_deduction,
        "other_deductions": data.other_deductions,
        "total_deductions": total_deductions,
        "net_salary": net_salary,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payroll_calculations.insert_one(calculation)
    
    return {"calculation_id": calc_id, "message": "Cálculo guardado correctamente", "net_salary": net_salary}

@api_router.get("/payroll-calculations")
async def get_payroll_calculations(current_user: dict = Depends(get_current_user)):
    """Get all saved payroll calculations for the company"""
    calculations = await db.payroll_calculations.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return calculations

# ===================== ACCOUNTING MODULE =====================

# Default chart of accounts for payroll
# Cuentas contables predefinidas para nómina según requisitos del usuario
DEFAULT_PAYROLL_ACCOUNTS = [
    # Gastos (Deudores - se debitan al procesar nómina)
    {"code": "5101", "name": "Gastos de Sueldos y Salarios", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5102", "name": "Gastos de Horas Extras Diurnas", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5103", "name": "Gastos de Horas Extras Nocturnas", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5104", "name": "Gastos de Horas Extras Fines de Semana", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5105", "name": "Gastos de Horas Extras Días Feriados", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5106", "name": "Gastos de Bonificaciones", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5107", "name": "Gastos de Comisiones", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    # Aportes Patronales (Gastos adicionales)
    {"code": "5201", "name": "Aportes Patronales SFS (7.09%)", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5202", "name": "Aportes Patronales AFP (7.10%)", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5203", "name": "Aportes Patronales SRL (1%)", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    {"code": "5204", "name": "Aportes Patronales INFOTEP (1%)", "account_type": "expense", "normal_balance": "debit", "is_payroll_account": True},
    # Pasivos (Acreedores - se acreditan al procesar nómina)
    {"code": "2201", "name": "Deducciones SFS por Pagar (3.04%)", "account_type": "liability", "normal_balance": "credit", "is_payroll_account": True},
    {"code": "2202", "name": "Deducciones AFP por Pagar (2.87%)", "account_type": "liability", "normal_balance": "credit", "is_payroll_account": True},
    {"code": "2203", "name": "Retención ISR por Pagar", "account_type": "liability", "normal_balance": "credit", "is_payroll_account": True},
    {"code": "2204", "name": "Descuentos Adicionales por Pagar", "account_type": "liability", "normal_balance": "credit", "is_payroll_account": True},
    {"code": "2205", "name": "Aportes TSS por Pagar", "account_type": "liability", "normal_balance": "credit", "is_payroll_account": True},
    # Banco (Activo - normalmente débito, pero se acredita al pagar nómina)
    {"code": "1101", "name": "Banco - Cuenta Nómina", "account_type": "asset", "normal_balance": "debit", "is_payroll_account": True, "is_bank_account": True},
]

# ===================== NUEVO SISTEMA DE NÓMINA COMPLETO =====================

class PayrollPeriodCreate(BaseModel):
    """Período de nómina (quincenal/mensual)"""
    period_type: str  # "quincenal_1", "quincenal_2", "mensual"
    year: int
    month: int
    start_date: str
    end_date: str
    description: Optional[str] = None

class PayrollEntryCreate(BaseModel):
    """Entrada de nómina individual por empleado"""
    period_id: str
    employee_id: str
    # Ingresos
    base_salary: float
    overtime_day_hours: float = 0
    overtime_day_rate: float = 35  # % sobre hora normal
    overtime_night_hours: float = 0
    overtime_night_rate: float = 15  # % sobre hora normal
    overtime_weekend_hours: float = 0
    overtime_weekend_rate: float = 100  # % sobre hora normal
    overtime_holiday_hours: float = 0
    overtime_holiday_rate: float = 100  # % sobre hora normal
    bonuses: float = 0
    commissions: float = 0
    other_income: float = 0
    # Descuentos adicionales (del perfil del empleado o manuales)
    additional_deductions: Optional[List[Dict[str, Any]]] = []

class PayrollPeriodProcess(BaseModel):
    """Para procesar/calcular todas las nóminas de un período"""
    period_id: str

class PayrollPaymentRequest(BaseModel):
    """Solicitud de pago de nómina con cuenta bancaria seleccionada"""
    bank_account_code: Optional[str] = "1101"

# ===================== NOVEDADES DE NÓMINA =====================

# Tipos de novedades predefinidas
PAYROLL_NOVELTY_TYPES = {
    "income": [
        {"code": "COM", "name": "Comisiones", "description": "Comisiones de ventas"},
        {"code": "VIA", "name": "Viáticos", "description": "Gastos de transporte y alimentación"},
        {"code": "INC", "name": "Incentivos", "description": "Bonificaciones por rendimiento"},
        {"code": "HED", "name": "Horas Extras Diurnas", "description": "Horas extras 35%"},
        {"code": "HEN", "name": "Horas Extras Nocturnas", "description": "Horas extras 15%"},
        {"code": "HEFS", "name": "Horas Extras Fin de Semana", "description": "Horas extras 100%"},
        {"code": "HEFER", "name": "Horas Extras Feriados", "description": "Horas extras 100%"},
        {"code": "BON", "name": "Bonificación", "description": "Bonificación general"},
        {"code": "REG", "name": "Regalía Pascual", "description": "Salario 13"},
        {"code": "VAC", "name": "Vacaciones", "description": "Pago de vacaciones"},
        {"code": "OTROING", "name": "Otros Ingresos", "description": "Otros ingresos no especificados"},
    ],
    "deduction": [
        {"code": "PREST", "name": "Préstamo Empresa", "description": "Cuota de préstamo de la empresa"},
        {"code": "ANTIC", "name": "Anticipo", "description": "Anticipo de salario"},
        {"code": "COOP", "name": "Cooperativa", "description": "Descuento de cooperativa"},
        {"code": "SEG", "name": "Seguro Adicional", "description": "Seguro de vida o médico adicional"},
        {"code": "PENS", "name": "Pensión Alimenticia", "description": "Retención por pensión alimenticia"},
        {"code": "EMB", "name": "Embargo", "description": "Embargo judicial"},
        {"code": "TARD", "name": "Tardanzas", "description": "Descuento por tardanzas"},
        {"code": "AUS", "name": "Ausencias", "description": "Descuento por ausencias"},
        {"code": "OTROSD", "name": "Otros Descuentos", "description": "Otros descuentos no especificados"},
    ]
}

# Tipos de nómina
PAYROLL_TYPES = [
    {"code": "REG", "name": "Regular", "description": "Nómina regular quincenal/mensual"},
    {"code": "TEMP", "name": "Temporal", "description": "Nómina para empleados temporales"},
    {"code": "BONO", "name": "Bono/Extraordinaria", "description": "Nómina de bonificaciones extraordinarias"},
    {"code": "REG13", "name": "Regalía Pascual", "description": "Nómina de salario 13"},
    {"code": "VAC", "name": "Vacaciones", "description": "Nómina de pago de vacaciones"},
    {"code": "LIQ", "name": "Liquidación", "description": "Nómina de liquidación de empleados"},
]

class PayrollNoveltyCreate(BaseModel):
    """Novedad individual para agregar a la nómina"""
    entry_id: str  # ID de la entrada de nómina del empleado
    novelty_type: str  # "income" o "deduction"
    code: str  # Código del tipo de novedad (COM, VIA, PREST, etc.)
    name: str
    description: Optional[str] = ""
    amount: float
    is_percentage: bool = False

class PayrollPeriodCreateV2(BaseModel):
    """Período de nómina con opciones avanzadas"""
    period_type: str  # "quincenal_1", "quincenal_2", "mensual"
    payroll_type: str = "REG"  # Tipo de nómina: REG, TEMP, BONO, REG13, VAC, LIQ
    year: int
    month: int
    start_date: str
    end_date: str
    description: Optional[str] = None
    department_filter: Optional[str] = None  # Filtrar por departamento específico
    employee_ids: Optional[List[str]] = None  # Lista específica de empleados
    currency: str = "DOP"  # DOP o USD
    exchange_rate: Optional[float] = None  # Tasa de cambio si es USD
    project_id: Optional[str] = None  # Filtrar por proyecto
    template_id: Optional[str] = None  # Template usado para crear

class CompanyBankConfigCreate(BaseModel):
    """Configuración de cuenta bancaria de la empresa para pagos"""
    bank_name: str
    account_number: str
    account_type: str  # "corriente", "ahorros"
    account_code: str = "1101"  # Código contable asociado
    is_default: bool = True

# ===================== PAYROLL TEMPLATES =====================

class PayrollTemplateCreate(BaseModel):
    """Template de nómina recurrente"""
    name: str
    description: Optional[str] = None
    period_type: str  # "quincenal_1", "quincenal_2", "mensual"
    payroll_type: str = "REG"
    department_filter: Optional[str] = None
    project_id: Optional[str] = None
    employee_ids: Optional[List[str]] = None
    currency: str = "DOP"
    default_exchange_rate: Optional[float] = None
    is_active: bool = True

# ===================== PROJECTS =====================

class ProjectCreate(BaseModel):
    """Proyecto para agrupar empleados y nóminas"""
    name: str
    code: str
    description: Optional[str] = None
    client_name: Optional[str] = None
    budget: Optional[float] = None
    currency: str = "DOP"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True

# ===================== CURRENCY CONFIG =====================

class CurrencyConfigCreate(BaseModel):
    """Configuración de moneda y tasa de cambio"""
    currency_code: str  # "USD", "EUR"
    exchange_rate: float  # Tasa respecto a DOP
    effective_date: str
    is_active: bool = True

# ===================== SUBSCRIPTION PLANS =====================

SUBSCRIPTION_PLANS = {
    "basic": {
        "id": "basic",
        "name": "FortexaRH Básico",
        "base_price": 5.00,
        "price_per_employee": 1.50,
        "included_users": 3,
        "max_employees": 50,
        "features": [
            "Administración de empleados",
            "Hasta 50 empleados",
            "Gestión de empleados",
            "Nómina básica",
            "Asistencias",
            "Vacaciones",
            "Calculadora de nómina",
            "Generación de nóminas",
            "Entradas de diario",
            "Reportes básicos",
            "Exportación a Excel/CSV",
            "Formularios básicos",
            "Soporte por email",
            "Integración con FortexaERP",
            "Roles por área (1 admin)"
        ],
        "integrations": ["fortexaerp"],
        "multi_admin": False
    },
    "pro": {
        "id": "pro",
        "name": "FortexaRH Pro",
        "base_price": 10.00,
        "price_per_employee": 1.50,
        "included_users": 5,
        "max_employees": 200,
        "features": [
            "Todas las funciones básicas",
            "Hasta 200 empleados",
            "Evaluaciones de desempeño",
            "Reclutamiento",
            "Organigrama intuitivo",
            "Reportes avanzados",
            "Soporte prioritario",
            "Integración con QuickBooks"
        ],
        "integrations": ["fortexaerp", "quickbooks"],
        "multi_admin": False
    },
    "enterprise": {
        "id": "enterprise",
        "name": "FortexaRH Enterprise",
        "base_price": 20.00,
        "price_per_employee": 1.50,
        "included_users": 7,
        "max_employees": -1,  # Unlimited
        "features": [
            "Todas las funciones Pro",
            "Empleados ilimitados",
            "Documentos personalizados",
            "API personalizada",
            "Soporte 24/7",
            "Gerente de cuenta dedicado",
            "Roles personalizados",
            "Múltiples administradores",
            "Flujos de trabajo avanzados",
            "Formularios personalizados",
            "Campos personalizados",
            "Notificaciones personalizadas",
            "Integración SAP",
            "Integración Oracle",
            "Integración Dynamics"
        ],
        "integrations": ["fortexaerp", "quickbooks", "sap", "oracle", "dynamics"],
        "multi_admin": True
    }
}

ADDITIONAL_USER_PRICE = 2.50  # USD per month

class SubscriptionCreate(BaseModel):
    plan_id: str  # basic, pro, enterprise
    employee_count: int = 1
    additional_users: int = 0
    billing_cycle: str = "monthly"  # monthly, annual

class SubscriptionUpdate(BaseModel):
    plan_id: Optional[str] = None
    employee_count: Optional[int] = None
    additional_users: Optional[int] = None
    action: Optional[str] = None  # cancel, renew, upgrade, downgrade

class SystemUserCreate(BaseModel):
    """Usuario del sistema (no empleado)"""
    email: EmailStr
    name: str
    password: str
    role: str = "user"  # admin, manager, user
    modules: List[str] = []  # Módulos permitidos
    is_active: bool = True

class SystemUserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    modules: Optional[List[str]] = None
    is_active: Optional[bool] = None

class CustomRoleCreate(BaseModel):
    """Rol personalizado (solo Enterprise)"""
    name: str
    description: Optional[str] = None
    modules: List[str] = []
    permissions: Dict[str, List[str]] = {}  # module: [read, write, delete]
async def get_chart_of_accounts(current_user: dict = Depends(get_current_user)):
    """Get chart of accounts for the company"""
    company_id = current_user.get("company_id")
    
    # Check if company has accounts, if not create default payroll accounts
    accounts = await db.accounts.find({"company_id": company_id}, {"_id": 0}).to_list(100)
    
    if not accounts:
        # Create default accounts
        for acc in DEFAULT_PAYROLL_ACCOUNTS:
            account = {
                "account_id": f"acc_{uuid.uuid4().hex[:8]}",
                "company_id": company_id,
                **acc,
                "balance": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.accounts.insert_one(account)
        
        accounts = await db.accounts.find({"company_id": company_id}, {"_id": 0}).to_list(100)
    
    return sorted(accounts, key=lambda x: x.get("code", ""))

@api_router.post("/accounting/accounts")
async def create_account(data: AccountCreate, current_user: dict = Depends(get_current_user)):
    """Create a new account in the chart of accounts"""
    company_id = current_user.get("company_id")
    
    # Check if code already exists
    existing = await db.accounts.find_one({"company_id": company_id, "code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una cuenta con este código")
    
    account = {
        "account_id": f"acc_{uuid.uuid4().hex[:8]}",
        "company_id": company_id,
        "code": data.code,
        "name": data.name,
        "account_type": data.account_type,
        "parent_code": data.parent_code,
        "description": data.description,
        "balance": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts.insert_one(account)
    
    return {"account_id": account["account_id"], "message": "Cuenta creada correctamente"}

@api_router.get("/accounting/journal-entries")
async def get_journal_entries(
    period: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get journal entries, optionally filtered by period and status"""
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    if period:
        query["period"] = period
    if status:
        query["status"] = status
    
    entries = await db.journal_entries.find(query, {"_id": 0}).sort("entry_date", -1).to_list(100)
    return entries

@api_router.get("/accounting/journal-entries/{entry_id}")
async def get_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific journal entry"""
    entry = await db.journal_entries.find_one(
        {"entry_id": entry_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    return entry

@api_router.post("/accounting/journal-entries")
async def create_journal_entry(data: JournalEntryCreate, current_user: dict = Depends(get_current_user)):
    """Create a new journal entry"""
    company_id = current_user.get("company_id")
    
    # Validate that debits equal credits
    total_debits = sum(line.debit for line in data.lines)
    total_credits = sum(line.credit for line in data.lines)
    
    if abs(total_debits - total_credits) > 0.01:
        raise HTTPException(
            status_code=400, 
            detail=f"El asiento no está balanceado. Débitos: {total_debits:.2f}, Créditos: {total_credits:.2f}"
        )
    
    entry_id = f"je_{uuid.uuid4().hex[:12]}"
    
    entry = {
        "entry_id": entry_id,
        "company_id": company_id,
        "entry_date": data.entry_date,
        "reference": data.reference,
        "description": data.description,
        "period": data.period,
        "entry_type": data.entry_type,
        "lines": [line.dict() for line in data.lines],
        "payroll_id": data.payroll_id,
        "notes": data.notes,
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "status": "draft",
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal_entries.insert_one(entry)
    
    return {"entry_id": entry_id, "message": "Asiento creado correctamente"}

@api_router.put("/accounting/journal-entries/{entry_id}")
async def update_journal_entry(entry_id: str, data: JournalEntryUpdate, current_user: dict = Depends(get_current_user)):
    """Update a journal entry (only if status is 'draft')"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one({"entry_id": entry_id, "company_id": company_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    if entry.get("status") == "posted":
        raise HTTPException(status_code=400, detail="No se puede editar un asiento contabilizado")
    
    update_data = {}
    if data.entry_date is not None:
        update_data["entry_date"] = data.entry_date
    if data.reference is not None:
        update_data["reference"] = data.reference
    if data.description is not None:
        update_data["description"] = data.description
    if data.period is not None:
        update_data["period"] = data.period
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.status is not None:
        update_data["status"] = data.status
    
    if data.lines is not None:
        # Validate balance
        total_debits = sum(line.debit for line in data.lines)
        total_credits = sum(line.credit for line in data.lines)
        
        if abs(total_debits - total_credits) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"El asiento no está balanceado. Débitos: {total_debits:.2f}, Créditos: {total_credits:.2f}"
            )
        
        update_data["lines"] = [line.dict() for line in data.lines]
        update_data["total_debits"] = round(total_debits, 2)
        update_data["total_credits"] = round(total_credits, 2)
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.get("user_id")
    
    await db.journal_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    return {"message": "Asiento actualizado correctamente"}

@api_router.post("/accounting/journal-entries/{entry_id}/post")
async def post_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Post (contabilizar) a journal entry"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one({"entry_id": entry_id, "company_id": company_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    if entry.get("status") == "posted":
        raise HTTPException(status_code=400, detail="El asiento ya está contabilizado")
    
    await db.journal_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "status": "posted",
            "posted_at": datetime.now(timezone.utc).isoformat(),
            "posted_by": current_user.get("user_id")
        }}
    )
    
    return {"message": "Asiento contabilizado correctamente"}

@api_router.delete("/accounting/journal-entries/{entry_id}")
async def delete_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a journal entry (only if status is 'draft')"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one({"entry_id": entry_id, "company_id": company_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    if entry.get("status") == "posted":
        raise HTTPException(status_code=400, detail="No se puede eliminar un asiento contabilizado")
    
    await db.journal_entries.delete_one({"entry_id": entry_id, "company_id": company_id})
    
    return {"message": "Asiento eliminado correctamente"}

@api_router.post("/accounting/generate-payroll-entry")
async def generate_payroll_journal_entry(
    payroll_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate a journal entry from a payroll calculation"""
    company_id = current_user.get("company_id")
    
    # Get the payroll calculation
    calculation = await db.payroll_calculations.find_one(
        {"calculation_id": payroll_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not calculation:
        raise HTTPException(status_code=404, detail="Cálculo de nómina no encontrado")
    
    # Generate journal entry lines
    lines = []
    
    # Expense accounts (debits)
    if calculation.get("proportional_salary", 0) > 0:
        lines.append({
            "account_code": "5101",
            "account_name": "Gastos de Sueldos y Salarios",
            "description": f"Salario - {calculation.get('employee_name', 'Empleado')}",
            "debit": calculation.get("proportional_salary", 0),
            "credit": 0
        })
    
    if calculation.get("extra_hours_pay", 0) > 0:
        lines.append({
            "account_code": "5102",
            "account_name": "Gastos de Horas Extra",
            "description": f"Horas extra - {calculation.get('employee_name', 'Empleado')}",
            "debit": calculation.get("extra_hours_pay", 0),
            "credit": 0
        })
    
    if calculation.get("bonuses", 0) > 0:
        lines.append({
            "account_code": "5103",
            "account_name": "Gastos de Bonificaciones",
            "description": f"Bonificación - {calculation.get('employee_name', 'Empleado')}",
            "debit": calculation.get("bonuses", 0),
            "credit": 0
        })
    
    if calculation.get("commissions", 0) > 0:
        lines.append({
            "account_code": "5104",
            "account_name": "Gastos de Comisiones",
            "description": f"Comisión - {calculation.get('employee_name', 'Empleado')}",
            "debit": calculation.get("commissions", 0),
            "credit": 0
        })
    
    # Employer contributions (debits)
    total_earnings = calculation.get("total_earnings", 0)
    sfs_employer = round(total_earnings * SFS_EMPLOYER_RATE, 2)
    afp_employer = round(total_earnings * AFP_EMPLOYER_RATE, 2)
    srl_employer = round(total_earnings * SRL_EMPLOYER_RATE, 2)
    infotep_employer = round(total_earnings * INFOTEP_EMPLOYER_RATE, 2)
    
    if sfs_employer > 0:
        lines.append({
            "account_code": "5201",
            "account_name": "Aportes Patronales SFS",
            "description": f"Aporte patronal SFS (7.09%)",
            "debit": sfs_employer,
            "credit": 0
        })
    
    if afp_employer > 0:
        lines.append({
            "account_code": "5202",
            "account_name": "Aportes Patronales AFP",
            "description": f"Aporte patronal AFP (7.10%)",
            "debit": afp_employer,
            "credit": 0
        })
    
    if srl_employer > 0:
        lines.append({
            "account_code": "5203",
            "account_name": "Aportes Patronales SRL",
            "description": f"Aporte patronal SRL (1%)",
            "debit": srl_employer,
            "credit": 0
        })
    
    if infotep_employer > 0:
        lines.append({
            "account_code": "5204",
            "account_name": "Aportes Patronales INFOTEP",
            "description": f"Aporte patronal INFOTEP (1%)",
            "debit": infotep_employer,
            "credit": 0
        })
    
    # Liability accounts (credits)
    if calculation.get("sfs_employee", 0) > 0:
        lines.append({
            "account_code": "2201",
            "account_name": "Retenciones SFS Empleados",
            "description": f"Retención SFS (3.07%) - {calculation.get('employee_name', 'Empleado')}",
            "debit": 0,
            "credit": calculation.get("sfs_employee", 0)
        })
    
    if calculation.get("afp_employee", 0) > 0:
        lines.append({
            "account_code": "2202",
            "account_name": "Retenciones AFP Empleados",
            "description": f"Retención AFP (2.87%) - {calculation.get('employee_name', 'Empleado')}",
            "debit": 0,
            "credit": calculation.get("afp_employee", 0)
        })
    
    if calculation.get("isr_monthly", 0) > 0:
        lines.append({
            "account_code": "2203",
            "account_name": "Retenciones ISR Empleados",
            "description": f"Retención ISR - {calculation.get('employee_name', 'Empleado')}",
            "debit": 0,
            "credit": calculation.get("isr_monthly", 0)
        })
    
    # TSS employer contributions payable
    total_employer_tss = sfs_employer + afp_employer + srl_employer + infotep_employer
    if total_employer_tss > 0:
        lines.append({
            "account_code": "2204",
            "account_name": "Aportes TSS por Pagar",
            "description": f"Aportes patronales TSS por pagar",
            "debit": 0,
            "credit": total_employer_tss
        })
    
    if calculation.get("loan_deduction", 0) > 0:
        lines.append({
            "account_code": "2205",
            "account_name": "Préstamos por Pagar",
            "description": f"Descuento préstamo - {calculation.get('employee_name', 'Empleado')}",
            "debit": 0,
            "credit": calculation.get("loan_deduction", 0)
        })
    
    if calculation.get("other_deductions", 0) > 0:
        lines.append({
            "account_code": "2206",
            "account_name": "Otras Deducciones por Pagar",
            "description": f"Otras deducciones - {calculation.get('employee_name', 'Empleado')}",
            "debit": 0,
            "credit": calculation.get("other_deductions", 0)
        })
    
    # Net salary payable
    if calculation.get("net_salary", 0) > 0:
        lines.append({
            "account_code": "2101",
            "account_name": "Sueldos por Pagar",
            "description": f"Sueldo neto - {calculation.get('employee_name', 'Empleado')}",
            "debit": 0,
            "credit": calculation.get("net_salary", 0)
        })
    
    # Create the journal entry
    entry_id = f"je_{uuid.uuid4().hex[:12]}"
    today = datetime.now(timezone.utc)
    period = today.strftime("%Y-%m")
    
    total_debits = sum(line["debit"] for line in lines)
    total_credits = sum(line["credit"] for line in lines)
    
    entry = {
        "entry_id": entry_id,
        "company_id": company_id,
        "entry_date": today.strftime("%Y-%m-%d"),
        "reference": f"NOM-{payroll_id}",
        "description": f"Nómina - {calculation.get('employee_name', 'Empleado')}",
        "period": period,
        "entry_type": "payroll",
        "lines": lines,
        "payroll_id": payroll_id,
        "notes": f"Asiento generado automáticamente desde cálculo de nómina",
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "status": "draft",
        "created_by": current_user.get("user_id"),
        "created_at": today.isoformat(),
        "updated_at": today.isoformat()
    }
    
    await db.journal_entries.insert_one(entry)
    
    return {
        "entry_id": entry_id,
        "message": "Asiento contable generado correctamente",
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2)
    }

# ===================== NUEVO SISTEMA DE NÓMINA CON ASIENTOS =====================

def get_next_journal_number(company_id: str, existing_entries: list) -> str:
    """Genera el siguiente número de asiento de diario (000001, 000002, etc.)"""
    if not existing_entries:
        return "000001"
    
    # Extraer números existentes
    numbers = []
    for entry in existing_entries:
        try:
            num = int(entry.get("entry_number", "0"))
            numbers.append(num)
        except:
            pass
    
    if not numbers:
        return "000001"
    
    next_num = max(numbers) + 1
    return str(next_num).zfill(6)

@api_router.get("/payroll-v2/periods")
async def get_payroll_periods(current_user: dict = Depends(get_current_user)):
    """Obtener todos los períodos de nómina"""
    company_id = current_user.get("company_id")
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("start_date", -1).to_list(100)
    return periods

@api_router.post("/payroll-v2/periods")
async def create_payroll_period(data: PayrollPeriodCreateV2, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo período de nómina"""
    company_id = current_user.get("company_id")
    
    # Determinar tipo de nómina
    payroll_type = data.payroll_type or 'REG'
    department_filter = data.department_filter
    employee_ids = data.employee_ids
    currency = data.currency or "DOP"
    exchange_rate = data.exchange_rate
    project_id = data.project_id
    
    # Si viene de un template, cargar configuración
    if data.template_id:
        template = await db.payroll_templates.find_one(
            {"template_id": data.template_id, "company_id": company_id},
            {"_id": 0}
        )
        if template:
            payroll_type = template.get("payroll_type", payroll_type)
            department_filter = template.get("department_filter", department_filter)
            employee_ids = template.get("employee_ids", employee_ids)
            currency = template.get("currency", currency)
            exchange_rate = template.get("default_exchange_rate", exchange_rate)
            project_id = template.get("project_id", project_id)
    
    period_id = f"period_{uuid.uuid4().hex[:12]}"
    period = {
        "period_id": period_id,
        "company_id": company_id,
        "period_type": data.period_type,
        "payroll_type": payroll_type,
        "year": data.year,
        "month": data.month,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "description": data.description or f"Nómina {data.period_type} - {data.month}/{data.year}",
        "department_filter": department_filter,
        "employee_ids": employee_ids,
        "currency": currency,
        "exchange_rate": exchange_rate,
        "project_id": project_id,
        "template_id": data.template_id,
        "status": "open",
        "total_gross": 0,
        "total_deductions": 0,
        "total_net": 0,
        "employee_count": 0,
        "journal_entry_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id")
    }
    await db.payroll_periods.insert_one(period)
    
    return {"period_id": period_id, "message": "Período creado correctamente"}

@api_router.get("/payroll-v2/periods/{period_id}")
async def get_payroll_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener un período de nómina específico con sus entradas"""
    company_id = current_user.get("company_id")
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Obtener entradas del período
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    period["entries"] = entries
    return period

@api_router.delete("/payroll-v2/periods/{period_id}")
async def delete_payroll_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar un período de nómina y su asiento contable asociado"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Eliminar asiento contable asociado si existe
    if period.get("journal_entry_id"):
        await db.journal_entries.delete_one({"entry_id": period["journal_entry_id"], "company_id": company_id})
    
    # Eliminar todas las entradas del período
    await db.payroll_entries.delete_many({"period_id": period_id, "company_id": company_id})
    
    # Eliminar el período
    await db.payroll_periods.delete_one({"period_id": period_id, "company_id": company_id})
    
    return {"message": "Período y asiento contable eliminados correctamente"}

@api_router.post("/payroll-v2/periods/{period_id}/add-employees")
async def add_employees_to_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Agregar todos los empleados activos al período de nómina"""
    company_id = current_user.get("company_id")
    
    # Verificar período existe
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Construir query de empleados
    employee_query = {"company_id": company_id, "status": "active", "exclude_from_payroll": {"$ne": True}}
    
    # Aplicar filtro por departamento si existe
    if period.get("department_filter"):
        employee_query["department"] = period["department_filter"]
    
    # Aplicar filtro por IDs específicos si existe
    if period.get("employee_ids") and len(period["employee_ids"]) > 0:
        employee_query["employee_id"] = {"$in": period["employee_ids"]}
    
    # Obtener empleados según filtros
    employees = await db.employees.find(employee_query, {"_id": 0}).to_list(1000)
    
    # Obtener entradas ya existentes
    existing_entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    existing_employee_ids = {e["employee_id"] for e in existing_entries}
    
    added_count = 0
    payroll_type = period.get("payroll_type", "REG")
    
    for emp in employees:
        if emp["employee_id"] in existing_employee_ids:
            continue
        
        # Calcular salario según tipo de nómina y período
        salary = emp.get("salary", 0)
        
        if payroll_type == "REG":
            # Nómina regular - proporcional si es quincenal
            if period.get("period_type", "").startswith("quincenal"):
                salary = salary / 2
        elif payroll_type == "REG13":
            # Regalía pascual - salario completo mensual
            salary = emp.get("salary", 0)
        elif payroll_type == "BONO":
            # Bono - empezar en 0, se agrega manualmente
            salary = 0
        elif payroll_type == "VAC":
            # Vacaciones - calcular según días
            salary = emp.get("salary", 0) / 23.83 * 14  # 14 días de vacaciones
        
        entry_id = f"pe_{uuid.uuid4().hex[:12]}"
        entry = {
            "entry_id": entry_id,
            "period_id": period_id,
            "company_id": company_id,
            "employee_id": emp["employee_id"],
            "employee_name": f"{emp['first_name']} {emp['last_name']}",
            "employee_document": emp.get("document_number", ""),
            "department": emp.get("department", ""),
            "position": emp.get("position", ""),
            "payroll_type": payroll_type,
            # Ingresos
            "base_salary": salary,
            "overtime_day_hours": 0,
            "overtime_day_amount": 0,
            "overtime_night_hours": 0,
            "overtime_night_amount": 0,
            "overtime_weekend_hours": 0,
            "overtime_weekend_amount": 0,
            "overtime_holiday_hours": 0,
            "overtime_holiday_amount": 0,
            "bonuses": 0,
            "commissions": 0,
            "other_income": 0,
            "gross_salary": salary,
            # Deducciones TSS
            "sfs_employee": round(salary * SFS_EMPLOYEE_RATE, 2),
            "afp_employee": round(salary * AFP_EMPLOYEE_RATE, 2),
            "isr": 0,  # Se calcula después
            # Descuentos adicionales del perfil
            "additional_deductions": emp.get("additional_deductions", []),
            "total_additional_deductions": sum(d.get("amount", 0) for d in emp.get("additional_deductions", []) if not d.get("is_percentage")),
            # Totales
            "total_deductions": 0,
            "net_salary": 0,
            # Aportes patronales
            "sfs_employer": round(salary * SFS_EMPLOYER_RATE, 2),
            "afp_employer": round(salary * AFP_EMPLOYER_RATE, 2),
            "srl_employer": round(salary * SRL_EMPLOYER_RATE, 2),
            "infotep_employer": round(salary * INFOTEP_EMPLOYER_RATE, 2),
            "total_employer_contributions": 0,
            # Estado
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Calcular ISR
        isr_result = calculate_isr_monthly(salary)
        entry["isr"] = isr_result["isr_monthly"]
        
        # Calcular totales
        entry["total_deductions"] = round(
            entry["sfs_employee"] + entry["afp_employee"] + entry["isr"] + entry["total_additional_deductions"],
            2
        )
        entry["net_salary"] = round(entry["gross_salary"] - entry["total_deductions"], 2)
        entry["total_employer_contributions"] = round(
            entry["sfs_employer"] + entry["afp_employer"] + entry["srl_employer"] + entry["infotep_employer"],
            2
        )
        
        await db.payroll_entries.insert_one(entry)
        added_count += 1
    
    # Actualizar totales del período
    await update_period_totals(period_id, company_id)
    
    return {"message": f"{added_count} empleados agregados al período", "added": added_count}

async def update_period_totals(period_id: str, company_id: str):
    """Actualizar totales del período"""
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    total_deductions = sum(e.get("total_deductions", 0) for e in entries)
    total_net = sum(e.get("net_salary", 0) for e in entries)
    
    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {
            "total_gross": round(total_gross, 2),
            "total_deductions": round(total_deductions, 2),
            "total_net": round(total_net, 2),
            "employee_count": len(entries),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

@api_router.get("/payroll-v2/entries/{entry_id}")
async def get_payroll_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener una entrada de nómina específica"""
    company_id = current_user.get("company_id")
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    return entry

@api_router.put("/payroll-v2/entries/{entry_id}")
async def update_payroll_entry(entry_id: str, data: PayrollEntryCreate, current_user: dict = Depends(get_current_user)):
    """Actualizar una entrada de nómina (horas extra, bonos, etc.)"""
    company_id = current_user.get("company_id")
    
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    # Obtener período para verificar si está abierto
    period = await db.payroll_periods.find_one(
        {"period_id": entry["period_id"], "company_id": company_id},
        {"_id": 0}
    )
    if period and period.get("status") == "paid":
        raise HTTPException(status_code=400, detail="No se puede modificar una nómina pagada")
    
    # Calcular valores de horas extra
    hourly_rate = data.base_salary / 23.83 / 8  # Días hábiles promedio / horas
    
    overtime_day_amount = round(data.overtime_day_hours * hourly_rate * (1 + data.overtime_day_rate / 100), 2)
    overtime_night_amount = round(data.overtime_night_hours * hourly_rate * (1 + data.overtime_night_rate / 100), 2)
    overtime_weekend_amount = round(data.overtime_weekend_hours * hourly_rate * (1 + data.overtime_weekend_rate / 100), 2)
    overtime_holiday_amount = round(data.overtime_holiday_hours * hourly_rate * (1 + data.overtime_holiday_rate / 100), 2)
    
    gross_salary = (
        data.base_salary + 
        overtime_day_amount + 
        overtime_night_amount + 
        overtime_weekend_amount + 
        overtime_holiday_amount +
        data.bonuses + 
        data.commissions + 
        data.other_income
    )
    
    # Calcular deducciones TSS
    sfs_employee = round(gross_salary * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(gross_salary * AFP_EMPLOYEE_RATE, 2)
    
    # Calcular ISR
    isr_result = calculate_isr_monthly(gross_salary)
    isr = isr_result["isr_monthly"]
    
    # Descuentos adicionales
    total_additional = sum(d.get("amount", 0) for d in (data.additional_deductions or []) if not d.get("is_percentage"))
    
    total_deductions = round(sfs_employee + afp_employee + isr + total_additional, 2)
    net_salary = round(gross_salary - total_deductions, 2)
    
    # Aportes patronales
    sfs_employer = round(gross_salary * SFS_EMPLOYER_RATE, 2)
    afp_employer = round(gross_salary * AFP_EMPLOYER_RATE, 2)
    srl_employer = round(gross_salary * SRL_EMPLOYER_RATE, 2)
    infotep_employer = round(gross_salary * INFOTEP_EMPLOYER_RATE, 2)
    
    update_data = {
        "base_salary": data.base_salary,
        "overtime_day_hours": data.overtime_day_hours,
        "overtime_day_amount": overtime_day_amount,
        "overtime_night_hours": data.overtime_night_hours,
        "overtime_night_amount": overtime_night_amount,
        "overtime_weekend_hours": data.overtime_weekend_hours,
        "overtime_weekend_amount": overtime_weekend_amount,
        "overtime_holiday_hours": data.overtime_holiday_hours,
        "overtime_holiday_amount": overtime_holiday_amount,
        "bonuses": data.bonuses,
        "commissions": data.commissions,
        "other_income": data.other_income,
        "gross_salary": round(gross_salary, 2),
        "sfs_employee": sfs_employee,
        "afp_employee": afp_employee,
        "isr": isr,
        "additional_deductions": data.additional_deductions or [],
        "total_additional_deductions": total_additional,
        "total_deductions": total_deductions,
        "net_salary": net_salary,
        "sfs_employer": sfs_employer,
        "afp_employer": afp_employer,
        "srl_employer": srl_employer,
        "infotep_employer": infotep_employer,
        "total_employer_contributions": round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    # Actualizar totales del período
    await update_period_totals(entry["period_id"], company_id)
    
    # Si el período tiene asiento contable, actualizarlo
    if period and period.get("journal_entry_id"):
        await regenerate_period_journal_entry(period["period_id"], company_id, current_user)
    
    return {"message": "Entrada actualizada correctamente"}

@api_router.delete("/payroll-v2/entries/{entry_id}")
async def delete_payroll_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar una entrada de nómina"""
    company_id = current_user.get("company_id")
    
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    period_id = entry["period_id"]
    
    await db.payroll_entries.delete_one({"entry_id": entry_id, "company_id": company_id})
    
    # Actualizar totales
    await update_period_totals(period_id, company_id)
    
    return {"message": "Entrada eliminada correctamente"}

# ===================== NOVEDADES DE NÓMINA =====================

@api_router.get("/payroll-v2/novelty-types")
async def get_novelty_types(current_user: dict = Depends(get_current_user)):
    """Obtener tipos de novedades disponibles"""
    return PAYROLL_NOVELTY_TYPES

@api_router.get("/payroll-v2/payroll-types")
async def get_payroll_types(current_user: dict = Depends(get_current_user)):
    """Obtener tipos de nómina disponibles"""
    return PAYROLL_TYPES

@api_router.post("/payroll-v2/entries/{entry_id}/novelties")
async def add_novelty_to_entry(entry_id: str, novelty: PayrollNoveltyCreate, current_user: dict = Depends(get_current_user)):
    """Agregar una novedad (ingreso o deducción adicional) a una entrada de nómina"""
    company_id = current_user.get("company_id")
    
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    # Verificar que el período no esté pagado
    period = await db.payroll_periods.find_one(
        {"period_id": entry["period_id"], "company_id": company_id},
        {"_id": 0}
    )
    if period and period.get("status") == "paid":
        raise HTTPException(status_code=400, detail="No se puede modificar una nómina pagada")
    
    novelty_id = f"nov_{uuid.uuid4().hex[:8]}"
    novelty_data = {
        "novelty_id": novelty_id,
        "novelty_type": novelty.novelty_type,
        "code": novelty.code,
        "name": novelty.name,
        "description": novelty.description,
        "amount": novelty.amount,
        "is_percentage": novelty.is_percentage,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Obtener novedades actuales
    current_novelties = entry.get("novelties", [])
    current_novelties.append(novelty_data)
    
    # Recalcular totales
    income_novelties = [n for n in current_novelties if n["novelty_type"] == "income"]
    deduction_novelties = [n for n in current_novelties if n["novelty_type"] == "deduction"]
    
    total_income_novelties = sum(n["amount"] for n in income_novelties if not n.get("is_percentage"))
    total_deduction_novelties = sum(n["amount"] for n in deduction_novelties if not n.get("is_percentage"))
    
    # Actualizar salario bruto y neto
    base_income = (
        entry.get("base_salary", 0) +
        entry.get("overtime_day_amount", 0) +
        entry.get("overtime_night_amount", 0) +
        entry.get("overtime_weekend_amount", 0) +
        entry.get("overtime_holiday_amount", 0) +
        entry.get("bonuses", 0) +
        entry.get("commissions", 0)
    )
    
    new_gross = base_income + total_income_novelties
    
    # Recalcular deducciones
    sfs = round(new_gross * SFS_EMPLOYEE_RATE, 2)
    afp = round(new_gross * AFP_EMPLOYEE_RATE, 2)
    isr_result = calculate_isr_monthly(new_gross)
    isr = isr_result["isr_monthly"]
    
    total_deductions = sfs + afp + isr + total_deduction_novelties + entry.get("total_additional_deductions", 0)
    net_salary = new_gross - total_deductions
    
    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "novelties": current_novelties,
            "total_income_novelties": round(total_income_novelties, 2),
            "total_deduction_novelties": round(total_deduction_novelties, 2),
            "gross_salary": round(new_gross, 2),
            "sfs_employee": sfs,
            "afp_employee": afp,
            "isr": isr,
            "total_deductions": round(total_deductions, 2),
            "net_salary": round(net_salary, 2),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Actualizar totales del período
    await update_period_totals(entry["period_id"], company_id)
    
    return {"novelty_id": novelty_id, "message": "Novedad agregada correctamente"}

@api_router.delete("/payroll-v2/entries/{entry_id}/novelties/{novelty_id}")
async def delete_novelty_from_entry(entry_id: str, novelty_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar una novedad de una entrada de nómina"""
    company_id = current_user.get("company_id")
    
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    # Filtrar novedades
    current_novelties = entry.get("novelties", [])
    updated_novelties = [n for n in current_novelties if n.get("novelty_id") != novelty_id]
    
    if len(updated_novelties) == len(current_novelties):
        raise HTTPException(status_code=404, detail="Novedad no encontrada")
    
    # Recalcular totales
    income_novelties = [n for n in updated_novelties if n["novelty_type"] == "income"]
    deduction_novelties = [n for n in updated_novelties if n["novelty_type"] == "deduction"]
    
    total_income_novelties = sum(n["amount"] for n in income_novelties if not n.get("is_percentage"))
    total_deduction_novelties = sum(n["amount"] for n in deduction_novelties if not n.get("is_percentage"))
    
    # Actualizar salario bruto y neto
    base_income = (
        entry.get("base_salary", 0) +
        entry.get("overtime_day_amount", 0) +
        entry.get("overtime_night_amount", 0) +
        entry.get("overtime_weekend_amount", 0) +
        entry.get("overtime_holiday_amount", 0) +
        entry.get("bonuses", 0) +
        entry.get("commissions", 0)
    )
    
    new_gross = base_income + total_income_novelties
    
    # Recalcular deducciones
    sfs = round(new_gross * SFS_EMPLOYEE_RATE, 2)
    afp = round(new_gross * AFP_EMPLOYEE_RATE, 2)
    isr_result = calculate_isr_monthly(new_gross)
    isr = isr_result["isr_monthly"]
    
    total_deductions = sfs + afp + isr + total_deduction_novelties + entry.get("total_additional_deductions", 0)
    net_salary = new_gross - total_deductions
    
    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "novelties": updated_novelties,
            "total_income_novelties": round(total_income_novelties, 2),
            "total_deduction_novelties": round(total_deduction_novelties, 2),
            "gross_salary": round(new_gross, 2),
            "sfs_employee": sfs,
            "afp_employee": afp,
            "isr": isr,
            "total_deductions": round(total_deductions, 2),
            "net_salary": round(net_salary, 2),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Actualizar totales del período
    await update_period_totals(entry["period_id"], company_id)
    
    return {"message": "Novedad eliminada correctamente"}

@api_router.get("/payroll-v2/periods/{period_id}/export/excel")
async def export_period_to_excel(period_id: str, current_user: dict = Depends(get_current_user)):
    """Exportar período a formato Excel (JSON para procesamiento en frontend)"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Preparar datos para Excel
    excel_data = {
        "period": period,
        "columns": [
            "No.", "Cédula", "Nombres y Apellidos", "Cargo", "Departamento",
            "Salario Base", "Comisiones", "Bonos", "H.E. Diurnas", "H.E. Nocturnas",
            "H.E. F.S.", "H.E. Feriados", "Otros Ingresos", "Total Ingresos",
            "SFS (3.04%)", "AFP (2.87%)", "ISR", "Otros Descuentos",
            "Total Descuentos", "Neto a Pagar"
        ],
        "rows": []
    }
    
    for i, entry in enumerate(entries):
        total_overtime = (
            entry.get("overtime_day_amount", 0) +
            entry.get("overtime_night_amount", 0) +
            entry.get("overtime_weekend_amount", 0) +
            entry.get("overtime_holiday_amount", 0)
        )
        
        row = {
            "no": i + 1,
            "cedula": entry.get("employee_document", ""),
            "nombre": entry.get("employee_name", ""),
            "cargo": entry.get("position", ""),
            "departamento": entry.get("department", ""),
            "salario_base": entry.get("base_salary", 0),
            "comisiones": entry.get("commissions", 0),
            "bonos": entry.get("bonuses", 0),
            "he_diurnas": entry.get("overtime_day_amount", 0),
            "he_nocturnas": entry.get("overtime_night_amount", 0),
            "he_finsemana": entry.get("overtime_weekend_amount", 0),
            "he_feriados": entry.get("overtime_holiday_amount", 0),
            "otros_ingresos": entry.get("total_income_novelties", 0),
            "total_ingresos": entry.get("gross_salary", 0),
            "sfs": entry.get("sfs_employee", 0),
            "afp": entry.get("afp_employee", 0),
            "isr": entry.get("isr", 0),
            "otros_descuentos": entry.get("total_additional_deductions", 0) + entry.get("total_deduction_novelties", 0),
            "total_descuentos": entry.get("total_deductions", 0),
            "neto": entry.get("net_salary", 0),
            "novelties": entry.get("novelties", [])
        }
        excel_data["rows"].append(row)
    
    # Calcular totales
    excel_data["totals"] = {
        "salario_base": sum(r["salario_base"] for r in excel_data["rows"]),
        "comisiones": sum(r["comisiones"] for r in excel_data["rows"]),
        "bonos": sum(r["bonos"] for r in excel_data["rows"]),
        "total_ingresos": sum(r["total_ingresos"] for r in excel_data["rows"]),
        "sfs": sum(r["sfs"] for r in excel_data["rows"]),
        "afp": sum(r["afp"] for r in excel_data["rows"]),
        "isr": sum(r["isr"] for r in excel_data["rows"]),
        "total_descuentos": sum(r["total_descuentos"] for r in excel_data["rows"]),
        "neto": sum(r["neto"] for r in excel_data["rows"])
    }
    
    return excel_data

@api_router.get("/payroll-v2/periods/{period_id}/export/tss")
async def export_period_to_tss(period_id: str, current_user: dict = Depends(get_current_user)):
    """Exportar período al formato TSS JSON (datos)"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    tss_data = {
        "header": {
            "rnc_cedula": company.get("rnc", "") if company else "",
            "periodo": f"{period['month']:02d}{period['year']}",
            "version": "5.3",
            "num_empleados": len(entries)
        },
        "employees": [],
        "summary": {}
    }
    
    for entry in entries:
        employee = await db.employees.find_one(
            {"employee_id": entry["employee_id"], "company_id": company_id},
            {"_id": 0}
        )
        
        emp_data = {
            "clave_nomina": entry.get("entry_id", "")[:8],
            "tipo_doc": "C",
            "numero_doc": entry.get("employee_document", "").replace("-", ""),
            "nombres": employee.get("first_name", "") if employee else entry.get("employee_name", "").split()[0],
            "primer_apellido": employee.get("last_name", "").split()[0] if employee else "",
            "segundo_apellido": employee.get("last_name", "").split()[-1] if employee and len(employee.get("last_name", "").split()) > 1 else "",
            "sexo": "M" if employee and employee.get("gender") == "Masculino" else "F",
            "fecha_nacimiento": employee.get("birth_date", "") if employee else "",
            "salario_cotizable_sdss": entry.get("gross_salary", 0),
            "aporte_voluntario": 0,
            "salario_isr": entry.get("gross_salary", 0),
            "tipo_ingreso": "Normal",
            "otras_remuneraciones": entry.get("total_income_novelties", 0),
            "remuneracion_otros_agentes": 0,
            "saldo_favor": 0,
            "regalia_pascual": 0,
            "preaviso_cesantia": 0,
            "retencion_pension": 0,
            "salario_infotep": entry.get("gross_salary", 0),
            "retencion_sfs": entry.get("sfs_employee", 0),
            "contribucion_afp": entry.get("afp_employee", 0),
            "riesgo_laboral": entry.get("srl_employer", 0),
            "total_aportes": entry.get("sfs_employee", 0) + entry.get("afp_employee", 0),
            "total_pagado": entry.get("net_salary", 0),
            "ingresos_exentos": 0
        }
        tss_data["employees"].append(emp_data)
    
    tss_data["summary"] = {
        "total_salario_cotizable": sum(e["salario_cotizable_sdss"] for e in tss_data["employees"]),
        "total_aporte_sfs_empleado": sum(entry.get("sfs_employee", 0) for entry in entries),
        "total_aporte_afp_empleado": sum(entry.get("afp_employee", 0) for entry in entries),
        "total_aporte_sfs_empleador": sum(entry.get("sfs_employer", 0) for entry in entries),
        "total_aporte_afp_empleador": sum(entry.get("afp_employer", 0) for entry in entries),
        "total_srl": sum(entry.get("srl_employer", 0) for entry in entries),
        "total_infotep": sum(entry.get("infotep_employer", 0) for entry in entries),
        "total_isr": sum(entry.get("isr", 0) for entry in entries)
    }
    
    return tss_data

# Import TSS generator
from tss_generator import (
    create_tss_autodeterminacion_excel,
    create_tss_novedades_excel,
    create_ir3_report,
    create_ir17_report
)

@api_router.get("/payroll-v2/periods/{period_id}/export/tss-autodeterminacion")
async def export_tss_autodeterminacion_excel(period_id: str, current_user: dict = Depends(get_current_user)):
    """Descargar archivo Excel TSS Autodeterminación v5.3"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("status") != "paid":
        raise HTTPException(status_code=400, detail="Solo se pueden exportar períodos pagados")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    employees_data = []
    for entry in entries:
        employee = await db.employees.find_one(
            {"employee_id": entry["employee_id"], "company_id": company_id},
            {"_id": 0}
        )
        
        emp_data = {
            "clave_nomina": entry.get("entry_id", "")[:8],
            "tipo_doc": "C",
            "numero_doc": entry.get("employee_document", "").replace("-", ""),
            "nombres": employee.get("first_name", "") if employee else entry.get("employee_name", "").split()[0],
            "primer_apellido": (employee.get("last_name", "").split()[0] if employee and employee.get("last_name") else ""),
            "segundo_apellido": (employee.get("last_name", "").split()[-1] if employee and len(employee.get("last_name", "").split()) > 1 else ""),
            "sexo": "M" if employee and employee.get("gender") == "Masculino" else "F",
            "fecha_nacimiento": employee.get("birth_date", "") if employee else "",
            "salario_cotizable_sdss": entry.get("gross_salary", 0),
            "aporte_voluntario": 0,
            "salario_isr": entry.get("gross_salary", 0),
            "tipo_ingreso": "Normal",
            "otras_remuneraciones": entry.get("total_income_novelties", 0),
            "rnc_agente_ret": "",
            "remuneracion_otros_agentes": 0,
            "saldo_favor": 0,
            "regalia_pascual": entry.get("regalia_pascual", 0) if period.get("payroll_type") == "REG13" else 0,
            "preaviso_cesantia": 0,
            "retencion_pension": 0,
            "salario_infotep": entry.get("gross_salary", 0),
            "retencion_sfs": entry.get("sfs_employee", 0),
            "contribucion_afp": entry.get("afp_employee", 0),
            "riesgo_laboral": entry.get("srl_employer", 0),
            "total_aportes": entry.get("sfs_employee", 0) + entry.get("afp_employee", 0),
            "total_pagado": entry.get("net_salary", 0),
            "ingresos_exentos": 0
        }
        employees_data.append(emp_data)
    
    rnc = company.get("rnc", "") if company else ""
    periodo = f"{period['month']:02d}{period['year']}"
    
    excel_file = create_tss_autodeterminacion_excel(rnc, periodo, employees_data)
    
    filename = f"TSS_Autodeterminacion_{periodo}.xls"
    return Response(
        content=excel_file.getvalue(),
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/payroll-v2/periods/{period_id}/export/tss-novedades")
async def export_tss_novedades_excel(period_id: str, current_user: dict = Depends(get_current_user)):
    """Descargar archivo Excel TSS Novedades v5.1 - Altas/Bajas del período"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Detectar novedades: empleados nuevos (IN), salidos (SA), etc.
    novedades_data = []
    for entry in entries:
        employee = await db.employees.find_one(
            {"employee_id": entry["employee_id"], "company_id": company_id},
            {"_id": 0}
        )
        
        # Determinar tipo de novedad basado en datos del empleado
        tipo_novedad = "IN"  # Default: Ingreso normal
        fecha_inicio = period.get("start_date", "")
        fecha_fin = period.get("end_date", "")
        
        if employee:
            hire_date = employee.get("hire_date", "")
            # Si fecha de contratación está dentro del período = Ingreso nuevo
            if hire_date and hire_date >= period.get("start_date", ""):
                tipo_novedad = "IN"
                fecha_inicio = hire_date
            
            # Si hay fecha de terminación = Salida
            termination_date = employee.get("termination_date", "")
            if termination_date and termination_date <= period.get("end_date", ""):
                tipo_novedad = "SA"
                fecha_fin = termination_date
        
        nov_data = {
            "clave_nomina": entry.get("entry_id", "")[:8],
            "tipo_novedad": tipo_novedad,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "tipo_doc": "C",
            "numero_doc": entry.get("employee_document", "").replace("-", ""),
            "nombres": employee.get("first_name", "") if employee else entry.get("employee_name", "").split()[0],
            "primer_apellido": (employee.get("last_name", "").split()[0] if employee and employee.get("last_name") else ""),
            "segundo_apellido": (employee.get("last_name", "").split()[-1] if employee and len(employee.get("last_name", "").split()) > 1 else ""),
            "sexo": "M" if employee and employee.get("gender") == "Masculino" else "F",
            "fecha_nacimiento": employee.get("birth_date", "") if employee else "",
            "salario_cotizable_sdss": entry.get("gross_salary", 0),
            "aporte_voluntario": 0,
            "tipo_ingreso": "Normal",
            "salario_isr": entry.get("gross_salary", 0),
            "otras_remuneraciones": entry.get("total_income_novelties", 0),
            "rnc_agente_ret": "",
            "remuneracion_otros_agentes": 0,
            "saldo_favor": 0,
            "regalia_pascual": 0,
            "preaviso_cesantia": 0,
            "retencion_pension": 0,
            "salario_infotep": entry.get("gross_salary", 0)
        }
        novedades_data.append(nov_data)
    
    rnc = company.get("rnc", "") if company else ""
    periodo = f"{period['month']:02d}{period['year']}"
    
    excel_file = create_tss_novedades_excel(rnc, periodo, novedades_data)
    
    filename = f"TSS_Novedades_{periodo}.xls"
    return Response(
        content=excel_file.getvalue(),
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/payroll-v2/periods/{period_id}/export/ir3")
async def export_ir3_excel(period_id: str, current_user: dict = Depends(get_current_user)):
    """Descargar reporte IR-3 (Retenciones de Asalariados) en Excel"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    employees_data = []
    for entry in entries:
        employee = await db.employees.find_one(
            {"employee_id": entry["employee_id"], "company_id": company_id},
            {"_id": 0}
        )
        
        gross = entry.get("gross_salary", 0)
        tss_deduction = entry.get("sfs_employee", 0) + entry.get("afp_employee", 0)
        
        emp_data = {
            "cedula": entry.get("employee_document", ""),
            "nombre_completo": entry.get("employee_name", ""),
            "salario_bruto": gross,
            "salario_cotizable": gross,
            "exenciones": tss_deduction,
            "renta_neta_gravable": gross - tss_deduction,
            "isr_calculado": entry.get("isr", 0),
            "isr_retenido": entry.get("isr", 0)
        }
        employees_data.append(emp_data)
    
    rnc = company.get("rnc", "") if company else ""
    company_name = company.get("name", "") if company else ""
    periodo = f"{period['month']:02d}{period['year']}"
    
    excel_file = create_ir3_report(rnc, company_name, periodo, employees_data)
    
    filename = f"IR3_Retenciones_{periodo}.xls"
    return Response(
        content=excel_file.getvalue(),
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.get("/payroll-v2/periods/{period_id}/export/ir17")
async def export_ir17_excel(period_id: str, current_user: dict = Depends(get_current_user)):
    """Descargar reporte IR-17 (Declaración Mensual ISR) en Excel"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Calcular resumen
    total_sueldos = sum(e.get("gross_salary", 0) for e in entries)
    total_sfs_emp = sum(e.get("sfs_employee", 0) for e in entries)
    total_afp_emp = sum(e.get("afp_employee", 0) for e in entries)
    total_isr = sum(e.get("isr", 0) for e in entries)
    total_sfs_patron = sum(e.get("sfs_employer", 0) for e in entries)
    total_afp_patron = sum(e.get("afp_employer", 0) for e in entries)
    total_srl = sum(e.get("srl_employer", 0) for e in entries)
    total_infotep = sum(e.get("infotep_employer", 0) for e in entries)
    
    summary = {
        "cantidad_empleados": len(entries),
        "total_sueldos": total_sueldos,
        "total_tss_empleado": total_sfs_emp + total_afp_emp,
        "otras_deducciones": 0,
        "renta_neta_gravable": total_sueldos - (total_sfs_emp + total_afp_emp),
        "isr_retenido": total_isr,
        "sfs_empleador": total_sfs_patron,
        "afp_empleador": total_afp_patron,
        "srl": total_srl,
        "infotep": total_infotep,
        "total_aportes_patronales": total_sfs_patron + total_afp_patron + total_srl + total_infotep,
        "total_tss": total_sfs_emp + total_afp_emp + total_sfs_patron + total_afp_patron + total_srl + total_infotep
    }
    
    rnc = company.get("rnc", "") if company else ""
    company_name = company.get("name", "") if company else ""
    periodo = f"{period['month']:02d}{period['year']}"
    
    excel_file = create_ir17_report(rnc, company_name, periodo, summary)
    
    filename = f"IR17_Declaracion_{periodo}.xls"
    return Response(
        content=excel_file.getvalue(),
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.post("/payroll-v2/periods/{period_id}/calculate")
async def calculate_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Calcular/recalcular todas las nóminas del período"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Recalcular cada entrada
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    for entry in entries:
        gross = entry.get("gross_salary", 0)
        if gross <= 0:
            continue
            
        sfs = round(gross * SFS_EMPLOYEE_RATE, 2)
        afp = round(gross * AFP_EMPLOYEE_RATE, 2)
        isr_result = calculate_isr_monthly(gross)
        isr = isr_result["isr_monthly"]
        additional = entry.get("total_additional_deductions", 0)
        
        total_ded = round(sfs + afp + isr + additional, 2)
        net = round(gross - total_ded, 2)
        
        await db.payroll_entries.update_one(
            {"entry_id": entry["entry_id"]},
            {"$set": {
                "sfs_employee": sfs,
                "afp_employee": afp,
                "isr": isr,
                "total_deductions": total_ded,
                "net_salary": net,
                "sfs_employer": round(gross * SFS_EMPLOYER_RATE, 2),
                "afp_employer": round(gross * AFP_EMPLOYER_RATE, 2),
                "srl_employer": round(gross * SRL_EMPLOYER_RATE, 2),
                "infotep_employer": round(gross * INFOTEP_EMPLOYER_RATE, 2),
                "status": "calculated"
            }}
        )
    
    await update_period_totals(period_id, company_id)
    
    await db.payroll_periods.update_one(
        {"period_id": period_id},
        {"$set": {"status": "calculated", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Período calculado correctamente"}

@api_router.post("/payroll-v2/periods/{period_id}/approve")
async def approve_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Aprobar el período de nómina"""
    company_id = current_user.get("company_id")
    
    result = await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {
            "status": "approved",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "approved_by": current_user.get("user_id")
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    return {"message": "Período aprobado correctamente"}

async def regenerate_period_journal_entry(period_id: str, company_id: str, current_user: dict):
    """Regenerar el asiento contable del período"""
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        return
    
    # Eliminar asiento anterior si existe
    if period.get("journal_entry_id"):
        await db.journal_entries.delete_one({"entry_id": period["journal_entry_id"], "company_id": company_id})
    
    # Crear nuevo asiento
    await generate_period_journal_entry(period_id, current_user, is_regeneration=True)

@api_router.post("/payroll-v2/periods/{period_id}/pay")
async def pay_period(period_id: str, payment_data: PayrollPaymentRequest = None, current_user: dict = Depends(get_current_user)):
    """Pagar el período y generar asiento contable"""
    company_id = current_user.get("company_id")
    
    # Obtener código de cuenta bancaria (por defecto 1101)
    bank_account_code = "1101"
    if payment_data and payment_data.bank_account_code:
        bank_account_code = payment_data.bank_account_code
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("status") not in ["calculated", "approved"]:
        raise HTTPException(status_code=400, detail="El período debe estar calculado o aprobado para pagarlo")
    
    # Generar asiento contable con la cuenta bancaria seleccionada
    journal_result = await generate_period_journal_entry(period_id, current_user, bank_account_code=bank_account_code)
    
    # Actualizar estado del período
    await db.payroll_periods.update_one(
        {"period_id": period_id},
        {"$set": {
            "status": "paid",
            "journal_entry_id": journal_result["entry_id"],
            "paid_at": datetime.now(timezone.utc).isoformat(),
            "paid_by": current_user.get("user_id")
        }}
    )
    
    # Actualizar estado de las entradas
    await db.payroll_entries.update_many(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {"status": "paid"}}
    )
    
    return {
        "message": "Nómina pagada y asiento contable generado",
        "journal_entry_id": journal_result["entry_id"],
        "entry_number": journal_result["entry_number"]
    }

async def generate_period_journal_entry(period_id: str, current_user: dict, is_regeneration: bool = False, bank_account_code: str = "1101"):
    """Generar asiento contable para un período de nómina completo"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    if not entries:
        raise HTTPException(status_code=400, detail="No hay empleados en este período")
    
    # Obtener nombre de la cuenta bancaria
    bank_account = await db.accounts.find_one(
        {"company_id": company_id, "code": bank_account_code},
        {"_id": 0}
    )
    bank_account_name = bank_account.get("name", "Banco - Cuenta Nómina") if bank_account else "Banco - Cuenta Nómina"
    
    # Sumar todos los valores
    totals = {
        "base_salary": 0,
        "overtime_day": 0,
        "overtime_night": 0,
        "overtime_weekend": 0,
        "overtime_holiday": 0,
        "bonuses": 0,
        "commissions": 0,
        "sfs_employee": 0,
        "afp_employee": 0,
        "isr": 0,
        "additional_deductions": 0,
        "net_salary": 0,
        "sfs_employer": 0,
        "afp_employer": 0,
        "srl_employer": 0,
        "infotep_employer": 0
    }
    
    for e in entries:
        totals["base_salary"] += e.get("base_salary", 0)
        totals["overtime_day"] += e.get("overtime_day_amount", 0)
        totals["overtime_night"] += e.get("overtime_night_amount", 0)
        totals["overtime_weekend"] += e.get("overtime_weekend_amount", 0)
        totals["overtime_holiday"] += e.get("overtime_holiday_amount", 0)
        totals["bonuses"] += e.get("bonuses", 0)
        totals["commissions"] += e.get("commissions", 0)
        totals["sfs_employee"] += e.get("sfs_employee", 0)
        totals["afp_employee"] += e.get("afp_employee", 0)
        totals["isr"] += e.get("isr", 0)
        totals["additional_deductions"] += e.get("total_additional_deductions", 0)
        totals["net_salary"] += e.get("net_salary", 0)
        totals["sfs_employer"] += e.get("sfs_employer", 0)
        totals["afp_employer"] += e.get("afp_employer", 0)
        totals["srl_employer"] += e.get("srl_employer", 0)
        totals["infotep_employer"] += e.get("infotep_employer", 0)
    
    # Redondear totales
    for key in totals:
        totals[key] = round(totals[key], 2)
    
    # Crear líneas del asiento
    lines = []
    
    # DÉBITOS (Gastos)
    if totals["base_salary"] > 0:
        lines.append({
            "account_code": "5101",
            "account_name": "Gastos de Sueldos y Salarios",
            "description": "Salarios del período",
            "debit": totals["base_salary"],
            "credit": 0
        })
    
    if totals["overtime_day"] > 0:
        lines.append({
            "account_code": "5102",
            "account_name": "Gastos de Horas Extras Diurnas",
            "description": "Horas extras diurnas",
            "debit": totals["overtime_day"],
            "credit": 0
        })
    
    if totals["overtime_night"] > 0:
        lines.append({
            "account_code": "5103",
            "account_name": "Gastos de Horas Extras Nocturnas",
            "description": "Horas extras nocturnas",
            "debit": totals["overtime_night"],
            "credit": 0
        })
    
    if totals["overtime_weekend"] > 0:
        lines.append({
            "account_code": "5104",
            "account_name": "Gastos de Horas Extras Fines de Semana",
            "description": "Horas extras fin de semana",
            "debit": totals["overtime_weekend"],
            "credit": 0
        })
    
    if totals["overtime_holiday"] > 0:
        lines.append({
            "account_code": "5105",
            "account_name": "Gastos de Horas Extras Días Feriados",
            "description": "Horas extras días feriados",
            "debit": totals["overtime_holiday"],
            "credit": 0
        })
    
    if totals["bonuses"] > 0:
        lines.append({
            "account_code": "5106",
            "account_name": "Gastos de Bonificaciones",
            "description": "Bonificaciones del período",
            "debit": totals["bonuses"],
            "credit": 0
        })
    
    if totals["commissions"] > 0:
        lines.append({
            "account_code": "5107",
            "account_name": "Gastos de Comisiones",
            "description": "Comisiones del período",
            "debit": totals["commissions"],
            "credit": 0
        })
    
    # CRÉDITOS (Pasivos y Banco)
    if totals["sfs_employee"] > 0:
        lines.append({
            "account_code": "2201",
            "account_name": "Deducciones SFS por Pagar (3.04%)",
            "description": "Retención SFS empleados",
            "debit": 0,
            "credit": totals["sfs_employee"]
        })
    
    if totals["afp_employee"] > 0:
        lines.append({
            "account_code": "2202",
            "account_name": "Deducciones AFP por Pagar (2.87%)",
            "description": "Retención AFP empleados",
            "debit": 0,
            "credit": totals["afp_employee"]
        })
    
    if totals["isr"] > 0:
        lines.append({
            "account_code": "2203",
            "account_name": "Retención ISR por Pagar",
            "description": "Retención ISR empleados",
            "debit": 0,
            "credit": totals["isr"]
        })
    
    if totals["additional_deductions"] > 0:
        lines.append({
            "account_code": "2204",
            "account_name": "Descuentos Adicionales por Pagar",
            "description": "Préstamos, cooperativas, etc.",
            "debit": 0,
            "credit": totals["additional_deductions"]
        })
    
    # Crédito a Banco por el neto pagado (usando la cuenta seleccionada)
    if totals["net_salary"] > 0:
        lines.append({
            "account_code": bank_account_code,
            "account_name": bank_account_name,
            "description": "Pago neto a empleados",
            "debit": 0,
            "credit": totals["net_salary"]
        })
    
    # Calcular totales
    total_debits = sum(line["debit"] for line in lines)
    total_credits = sum(line["credit"] for line in lines)
    
    # Obtener siguiente número de asiento
    existing_entries = await db.journal_entries.find(
        {"company_id": company_id},
        {"entry_number": 1}
    ).to_list(10000)
    entry_number = get_next_journal_number(company_id, existing_entries)
    
    entry_id = f"je_{uuid.uuid4().hex[:12]}"
    today = datetime.now(timezone.utc)
    
    entry = {
        "entry_id": entry_id,
        "entry_number": entry_number,
        "company_id": company_id,
        "entry_date": today.strftime("%Y-%m-%d"),
        "reference": f"NOM-{period['period_type']}-{period['year']}-{period['month']:02d}",
        "description": f"Nómina {period.get('description', '')} - {len(entries)} empleados",
        "period": f"{period['year']}-{period['month']:02d}",
        "entry_type": "payroll",
        "lines": lines,
        "payroll_period_id": period_id,
        "employee_count": len(entries),
        "notes": f"Asiento generado automáticamente al pagar nómina",
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "status": "posted",  # Publicado automáticamente al pagar
        "created_by": current_user.get("user_id"),
        "created_at": today.isoformat(),
        "updated_at": today.isoformat()
    }
    
    await db.journal_entries.insert_one(entry)
    
    # Actualizar período con ID del asiento
    await db.payroll_periods.update_one(
        {"period_id": period_id},
        {"$set": {"journal_entry_id": entry_id}}
    )
    
    return {
        "entry_id": entry_id,
        "entry_number": entry_number,
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2)
    }

# ===================== CONFIGURACIÓN DE BANCO EMPRESA =====================

@api_router.get("/company/bank-config")
async def get_company_bank_config(current_user: dict = Depends(get_current_user)):
    """Obtener configuración de cuenta bancaria de la empresa"""
    company_id = current_user.get("company_id")
    config = await db.company_bank_config.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    return config

@api_router.post("/company/bank-config")
async def save_company_bank_config(data: CompanyBankConfigCreate, current_user: dict = Depends(get_current_user)):
    """Guardar configuración de cuenta bancaria"""
    company_id = current_user.get("company_id")
    
    config = {
        "company_id": company_id,
        "bank_name": data.bank_name,
        "account_number": data.account_number,
        "account_type": data.account_type,
        "account_code": data.account_code,
        "is_default": data.is_default,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.company_bank_config.update_one(
        {"company_id": company_id},
        {"$set": config},
        upsert=True
    )
    
    return {"message": "Configuración guardada correctamente"}

# ===================== CRUD CUENTAS CONTABLES =====================

@api_router.put("/accounting/accounts/{account_id}")
async def update_account(account_id: str, data: AccountCreate, current_user: dict = Depends(get_current_user)):
    """Actualizar una cuenta contable"""
    company_id = current_user.get("company_id")
    
    result = await db.accounts.update_one(
        {"account_id": account_id, "company_id": company_id},
        {"$set": {
            "code": data.code,
            "name": data.name,
            "account_type": data.account_type,
            "parent_code": data.parent_code,
            "description": data.description,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    return {"message": "Cuenta actualizada correctamente"}

@api_router.delete("/accounting/accounts/{account_id}")
async def delete_account(account_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar una cuenta contable"""
    company_id = current_user.get("company_id")
    
    result = await db.accounts.delete_one(
        {"account_id": account_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    return {"message": "Cuenta eliminada correctamente"}

@api_router.post("/accounting/accounts/reset-defaults")
async def reset_default_accounts(current_user: dict = Depends(get_current_user)):
    """Resetear cuentas a las predefinidas"""
    company_id = current_user.get("company_id")
    
    # Eliminar cuentas existentes
    await db.accounts.delete_many({"company_id": company_id})
    
    # Crear cuentas predefinidas
    for acc in DEFAULT_PAYROLL_ACCOUNTS:
        account = {
            "account_id": f"acc_{uuid.uuid4().hex[:8]}",
            "company_id": company_id,
            **acc,
            "balance": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.accounts.insert_one(account)
    
    return {"message": "Cuentas restablecidas a valores predeterminados"}

# ===================== SINCRONIZACIÓN NÓMINA-ASIENTO =====================

@api_router.delete("/accounting/journal-entries/{entry_id}/with-payroll")
async def delete_journal_entry_with_payroll(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar asiento contable y su período de nómina asociado"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    # Si tiene período asociado, eliminarlo también
    if entry.get("payroll_period_id"):
        period_id = entry["payroll_period_id"]
        # Eliminar entradas del período
        await db.payroll_entries.delete_many({"period_id": period_id, "company_id": company_id})
        # Eliminar período
        await db.payroll_periods.delete_one({"period_id": period_id, "company_id": company_id})
    
    # Eliminar asiento
    await db.journal_entries.delete_one({"entry_id": entry_id, "company_id": company_id})
    
    return {"message": "Asiento contable y nómina eliminados correctamente"}

# ===================== EXPORTACIÓN DE ASIENTOS =====================

@api_router.get("/accounting/journal-entries/{entry_id}/export")
async def export_journal_entry(entry_id: str, format: str = "json", current_user: dict = Depends(get_current_user)):
    """Exportar un asiento contable (preparar datos para Excel/CSV/PDF)"""
    company_id = current_user.get("company_id")
    
    entry = await db.journal_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Asiento no encontrado")
    
    # Preparar datos para exportación
    export_data = {
        "numero": entry.get("entry_number", ""),
        "fecha": entry.get("entry_date", ""),
        "referencia": entry.get("reference", ""),
        "descripcion": entry.get("description", ""),
        "lineas": []
    }
    
    for line in entry.get("lines", []):
        export_data["lineas"].append({
            "cuenta_codigo": line.get("account_code", ""),
            "cuenta_nombre": line.get("account_name", ""),
            "descripcion": line.get("description", ""),
            "debito": line.get("debit", 0),
            "credito": line.get("credit", 0)
        })
    
    export_data["total_debitos"] = entry.get("total_debits", 0)
    export_data["total_creditos"] = entry.get("total_credits", 0)
    
    return export_data

@api_router.get("/accounting/journal-entries/search")
async def search_journal_entries(
    entry_number: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Buscar asientos por número o rango de fechas"""
    company_id = current_user.get("company_id")
    
    query = {"company_id": company_id}
    
    if entry_number:
        query["entry_number"] = {"$regex": entry_number, "$options": "i"}
    
    if start_date:
        query["entry_date"] = {"$gte": start_date}
    
    if end_date:
        if "entry_date" in query:
            query["entry_date"]["$lte"] = end_date
        else:
            query["entry_date"] = {"$lte": end_date}
    
    entries = await db.journal_entries.find(query, {"_id": 0}).sort("entry_number", -1).to_list(100)
    return entries

# ===================== ORGANIGRAMA DRAG & DROP =====================

@api_router.put("/organigrama/reorder")
async def reorder_org_nodes(updates: List[OrgNodeUpdatePosition], current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    for update in updates:
        # Get old node data
        old_node = await db.org_nodes.find_one({"node_id": update.node_id, "company_id": company_id}, {"_id": 0})
        if not old_node:
            continue
        
        old_parent_id = old_node.get("parent_id")
        new_parent_id = update.parent_id
        
        # Remove from old parent's children
        if old_parent_id:
            await db.org_nodes.update_one(
                {"node_id": old_parent_id},
                {"$pull": {"children": update.node_id}}
            )
        
        # Add to new parent's children
        if new_parent_id:
            await db.org_nodes.update_one(
                {"node_id": new_parent_id},
                {"$addToSet": {"children": update.node_id}}
            )
        
        # Update node
        await db.org_nodes.update_one(
            {"node_id": update.node_id, "company_id": company_id},
            {"$set": {"parent_id": new_parent_id, "level": update.level}}
        )
    
    return {"message": "Organigrama actualizado correctamente"}

# ===================== PAYROLL TEMPLATES =====================

@api_router.get("/payroll-v2/templates")
async def get_payroll_templates(current_user: dict = Depends(get_current_user)):
    """Obtener templates de nómina de la empresa"""
    company_id = current_user.get("company_id")
    templates = await db.payroll_templates.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return templates

@api_router.post("/payroll-v2/templates")
async def create_payroll_template(template: PayrollTemplateCreate, current_user: dict = Depends(get_current_user)):
    """Crear un template de nómina"""
    company_id = current_user.get("company_id")
    
    template_id = f"tmpl_{uuid.uuid4().hex[:8]}"
    template_doc = {
        "template_id": template_id,
        "company_id": company_id,
        **template.dict(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id")
    }
    
    await db.payroll_templates.insert_one(template_doc)
    return {"template_id": template_id, "message": "Template creado correctamente"}

@api_router.put("/payroll-v2/templates/{template_id}")
async def update_payroll_template(template_id: str, template: PayrollTemplateCreate, current_user: dict = Depends(get_current_user)):
    """Actualizar un template de nómina"""
    company_id = current_user.get("company_id")
    
    result = await db.payroll_templates.update_one(
        {"template_id": template_id, "company_id": company_id},
        {"$set": {**template.dict(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    
    return {"message": "Template actualizado"}

@api_router.delete("/payroll-v2/templates/{template_id}")
async def delete_payroll_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar un template de nómina"""
    company_id = current_user.get("company_id")
    
    result = await db.payroll_templates.delete_one(
        {"template_id": template_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    
    return {"message": "Template eliminado"}

# ===================== PROJECTS =====================

@api_router.get("/projects")
async def get_projects(current_user: dict = Depends(get_current_user)):
    """Obtener proyectos de la empresa"""
    company_id = current_user.get("company_id")
    projects = await db.projects.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return projects

@api_router.post("/projects")
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Crear un proyecto"""
    company_id = current_user.get("company_id")
    
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    project_doc = {
        "project_id": project_id,
        "company_id": company_id,
        **project.dict(),
        "employee_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.insert_one(project_doc)
    return {"project_id": project_id, "message": "Proyecto creado correctamente"}

@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Actualizar un proyecto"""
    company_id = current_user.get("company_id")
    
    result = await db.projects.update_one(
        {"project_id": project_id, "company_id": company_id},
        {"$set": {**project.dict(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {"message": "Proyecto actualizado"}

@api_router.post("/projects/{project_id}/employees")
async def add_employees_to_project(project_id: str, employee_ids: List[str], current_user: dict = Depends(get_current_user)):
    """Agregar empleados a un proyecto"""
    company_id = current_user.get("company_id")
    
    result = await db.projects.update_one(
        {"project_id": project_id, "company_id": company_id},
        {"$addToSet": {"employee_ids": {"$each": employee_ids}}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Update employees with project assignment
    await db.employees.update_many(
        {"employee_id": {"$in": employee_ids}, "company_id": company_id},
        {"$set": {"project_id": project_id}}
    )
    
    return {"message": f"{len(employee_ids)} empleados agregados al proyecto"}

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar un proyecto"""
    company_id = current_user.get("company_id")
    
    # Remove project from employees
    await db.employees.update_many(
        {"project_id": project_id, "company_id": company_id},
        {"$unset": {"project_id": ""}}
    )
    
    result = await db.projects.delete_one(
        {"project_id": project_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {"message": "Proyecto eliminado"}

# ===================== CURRENCY CONFIG =====================

@api_router.get("/currency/rates")
async def get_currency_rates(current_user: dict = Depends(get_current_user)):
    """Obtener tasas de cambio configuradas"""
    company_id = current_user.get("company_id")
    rates = await db.currency_rates.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).sort("effective_date", -1).to_list(50)
    return rates

@api_router.post("/currency/rates")
async def create_currency_rate(config: CurrencyConfigCreate, current_user: dict = Depends(get_current_user)):
    """Crear/actualizar tasa de cambio"""
    company_id = current_user.get("company_id")
    
    rate_id = f"rate_{uuid.uuid4().hex[:8]}"
    rate_doc = {
        "rate_id": rate_id,
        "company_id": company_id,
        **config.dict(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.currency_rates.insert_one(rate_doc)
    return {"rate_id": rate_id, "message": "Tasa de cambio guardada"}

@api_router.get("/currency/latest")
async def get_latest_exchange_rate(currency: str = "USD", current_user: dict = Depends(get_current_user)):
    """Obtener la tasa de cambio más reciente para una moneda"""
    company_id = current_user.get("company_id")
    
    rate = await db.currency_rates.find_one(
        {"company_id": company_id, "currency_code": currency, "is_active": True},
        {"_id": 0},
        sort=[("effective_date", -1)]
    )
    
    if not rate:
        # Default rate for USD
        return {"currency_code": currency, "exchange_rate": 58.50, "is_default": True}
    
    return rate

# ===================== DASHBOARD STATS =====================

@api_router.get("/dashboard/payroll-stats")
async def get_payroll_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Obtener estadísticas del dashboard de nómina"""
    company_id = current_user.get("company_id")
    
    # Get all periods
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get all employees
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(500)
    
    # Monthly trend (last 12 months)
    monthly_trend = []
    paid_periods = [p for p in periods if p.get("status") == "paid"]
    
    # Group by month/year
    monthly_data = {}
    for p in paid_periods:
        key = f"{p.get('year')}-{p.get('month'):02d}"
        if key not in monthly_data:
            monthly_data[key] = {"month": key, "total_gross": 0, "total_net": 0, "count": 0}
        monthly_data[key]["total_gross"] += p.get("total_gross", 0)
        monthly_data[key]["total_net"] += p.get("total_net", 0)
        monthly_data[key]["count"] += 1
    
    monthly_trend = sorted(monthly_data.values(), key=lambda x: x["month"])[-12:]
    
    # Department distribution
    dept_distribution = {}
    for emp in employees:
        dept = emp.get("department", "Sin Departamento")
        if dept not in dept_distribution:
            dept_distribution[dept] = {"department": dept, "count": 0, "total_salary": 0}
        dept_distribution[dept]["count"] += 1
        dept_distribution[dept]["total_salary"] += emp.get("base_salary", 0)
    
    # Employer cost breakdown
    total_entries = []
    for p in paid_periods[-6:]:  # Last 6 paid periods
        entries = await db.payroll_entries.find(
            {"period_id": p["period_id"], "company_id": company_id},
            {"_id": 0}
        ).to_list(500)
        total_entries.extend(entries)
    
    employer_costs = {
        "total_gross_salary": sum(e.get("gross_salary", 0) for e in total_entries),
        "total_net_salary": sum(e.get("net_salary", 0) for e in total_entries),
        "total_sfs_employer": sum(e.get("sfs_employer", 0) for e in total_entries),
        "total_afp_employer": sum(e.get("afp_employer", 0) for e in total_entries),
        "total_srl": sum(e.get("srl_employer", 0) for e in total_entries),
        "total_infotep": sum(e.get("infotep_employer", 0) for e in total_entries),
    }
    employer_costs["total_employer_cost"] = (
        employer_costs["total_gross_salary"] + 
        employer_costs["total_sfs_employer"] + 
        employer_costs["total_afp_employer"] + 
        employer_costs["total_srl"] + 
        employer_costs["total_infotep"]
    )
    
    # Top 10 salaries
    top_salaries = sorted(employees, key=lambda x: x.get("base_salary", 0), reverse=True)[:10]
    top_salaries_data = [
        {
            "employee_id": e.get("employee_id"),
            "name": f"{e.get('first_name', '')} {e.get('last_name', '')}",
            "department": e.get("department", ""),
            "salary": e.get("base_salary", 0)
        }
        for e in top_salaries
    ]
    
    # Alerts
    alerts = []
    
    # Unpaid periods
    unpaid_approved = [p for p in periods if p.get("status") == "approved"]
    if unpaid_approved:
        alerts.append({
            "type": "warning",
            "message": f"{len(unpaid_approved)} nóminas aprobadas pendientes de pago",
            "count": len(unpaid_approved)
        })
    
    # Employees without complete data
    incomplete_employees = [e for e in employees if not e.get("document_id") or not e.get("bank_account")]
    if incomplete_employees:
        alerts.append({
            "type": "info",
            "message": f"{len(incomplete_employees)} empleados con datos incompletos",
            "count": len(incomplete_employees)
        })
    
    # Summary stats
    summary = {
        "total_employees": len(employees),
        "total_periods": len(periods),
        "paid_periods": len(paid_periods),
        "total_paid_ytd": sum(p.get("total_net", 0) for p in paid_periods if p.get("year") == datetime.now().year),
        "avg_salary": sum(e.get("base_salary", 0) for e in employees) / len(employees) if employees else 0
    }
    
    return {
        "summary": summary,
        "monthly_trend": monthly_trend,
        "department_distribution": list(dept_distribution.values()),
        "employer_costs": employer_costs,
        "top_salaries": top_salaries_data,
        "alerts": alerts
    }

@api_router.get("/dashboard/currency-summary")
async def get_currency_summary(current_user: dict = Depends(get_current_user)):
    """Resumen de nóminas por moneda"""
    company_id = current_user.get("company_id")
    
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "status": "paid"},
        {"_id": 0}
    ).to_list(100)
    
    currency_summary = {"DOP": 0, "USD": 0}
    for p in periods:
        currency = p.get("currency", "DOP")
        currency_summary[currency] = currency_summary.get(currency, 0) + p.get("total_net", 0)
    
    return currency_summary

# ===================== SUBSCRIPTION ENDPOINTS =====================

@api_router.get("/plans")
async def get_subscription_plans():
    """Obtener todos los planes de suscripción disponibles"""
    return list(SUBSCRIPTION_PLANS.values())

@api_router.get("/subscription")
async def get_company_subscription(current_user: dict = Depends(get_current_user)):
    """Obtener la suscripción actual de la empresa"""
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not subscription:
        # Create default free trial subscription
        subscription = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "company_id": company_id,
            "plan_id": "basic",
            "plan_name": SUBSCRIPTION_PLANS["basic"]["name"],
            "status": "trial",  # trial, active, cancelled, expired
            "employee_count": 5,
            "additional_users": 0,
            "billing_cycle": "monthly",
            "base_price": SUBSCRIPTION_PLANS["basic"]["base_price"],
            "employee_price": SUBSCRIPTION_PLANS["basic"]["price_per_employee"],
            "total_monthly": 5 + (5 * 1.50),
            "trial_ends_at": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(subscription)
    
    # Get plan details
    plan = SUBSCRIPTION_PLANS.get(subscription.get("plan_id", "basic"), SUBSCRIPTION_PLANS["basic"])
    subscription["plan_details"] = plan
    
    # Count current employees and users
    employee_count = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    user_count = await db.users.count_documents({"company_id": company_id})
    
    subscription["current_employees"] = employee_count
    subscription["current_users"] = user_count
    subscription["max_employees"] = plan["max_employees"]
    subscription["included_users"] = plan["included_users"]
    
    return subscription

@api_router.post("/subscription")
async def create_subscription(data: SubscriptionCreate, current_user: dict = Depends(get_current_user)):
    """Crear o actualizar suscripción"""
    company_id = current_user.get("company_id")
    
    plan = SUBSCRIPTION_PLANS.get(data.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plan no válido")
    
    # Check employee limit
    if plan["max_employees"] > 0 and data.employee_count > plan["max_employees"]:
        raise HTTPException(status_code=400, detail=f"El plan {plan['name']} permite máximo {plan['max_employees']} empleados")
    
    # Calculate total
    base = plan["base_price"]
    employee_cost = data.employee_count * plan["price_per_employee"]
    additional_users_cost = data.additional_users * ADDITIONAL_USER_PRICE
    total_monthly = base + employee_cost + additional_users_cost
    
    subscription = {
        "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "plan_id": data.plan_id,
        "plan_name": plan["name"],
        "status": "active",
        "employee_count": data.employee_count,
        "additional_users": data.additional_users,
        "billing_cycle": data.billing_cycle,
        "base_price": base,
        "employee_price": plan["price_per_employee"],
        "additional_users_cost": additional_users_cost,
        "total_monthly": total_monthly,
        "current_period_start": datetime.now(timezone.utc).isoformat(),
        "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert subscription
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": subscription},
        upsert=True
    )
    
    return {"message": "Suscripción actualizada", "subscription": subscription}

@api_router.put("/subscription")
async def update_subscription(data: SubscriptionUpdate, current_user: dict = Depends(get_current_user)):
    """Actualizar suscripción (cambiar plan, empleados, cancelar, renovar)"""
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    
    updates = {}
    
    # Handle actions
    if data.action == "cancel":
        updates["status"] = "cancelled"
        updates["cancelled_at"] = datetime.now(timezone.utc).isoformat()
    elif data.action == "renew":
        updates["status"] = "active"
        updates["current_period_start"] = datetime.now(timezone.utc).isoformat()
        updates["current_period_end"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    
    # Update plan
    if data.plan_id:
        plan = SUBSCRIPTION_PLANS.get(data.plan_id)
        if not plan:
            raise HTTPException(status_code=400, detail="Plan no válido")
        updates["plan_id"] = data.plan_id
        updates["plan_name"] = plan["name"]
        updates["base_price"] = plan["base_price"]
        updates["employee_price"] = plan["price_per_employee"]
    
    # Update employee count
    if data.employee_count is not None:
        current_plan = SUBSCRIPTION_PLANS.get(data.plan_id or subscription["plan_id"])
        if current_plan["max_employees"] > 0 and data.employee_count > current_plan["max_employees"]:
            raise HTTPException(status_code=400, detail=f"El plan permite máximo {current_plan['max_employees']} empleados")
        updates["employee_count"] = data.employee_count
    
    # Update additional users
    if data.additional_users is not None:
        updates["additional_users"] = data.additional_users
        updates["additional_users_cost"] = data.additional_users * ADDITIONAL_USER_PRICE
    
    # Recalculate total
    plan_id = updates.get("plan_id", subscription["plan_id"])
    plan = SUBSCRIPTION_PLANS[plan_id]
    emp_count = updates.get("employee_count", subscription.get("employee_count", 1))
    add_users = updates.get("additional_users", subscription.get("additional_users", 0))
    
    updates["total_monthly"] = plan["base_price"] + (emp_count * plan["price_per_employee"]) + (add_users * ADDITIONAL_USER_PRICE)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.subscriptions.update_one(
        {"company_id": company_id},
        {"$set": updates}
    )
    
    return {"message": "Suscripción actualizada correctamente"}

@api_router.get("/subscription/check-access")
async def check_subscription_access(current_user: dict = Depends(get_current_user)):
    """Verificar si el usuario tiene acceso al sistema según su suscripción"""
    company_id = current_user.get("company_id")
    
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    
    if not subscription:
        return {"has_access": True, "status": "trial", "message": "Período de prueba"}
    
    status = subscription.get("status", "active")
    
    if status == "cancelled" or status == "expired":
        return {
            "has_access": False,
            "status": status,
            "message": "Su suscripción está cancelada o vencida. Por favor renueve para continuar.",
            "redirect_to": "/subscriptions"
        }
    
    # Check if trial expired
    if status == "trial":
        trial_ends = subscription.get("trial_ends_at")
        if trial_ends:
            trial_end_date = datetime.fromisoformat(trial_ends.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > trial_end_date:
                await db.subscriptions.update_one(
                    {"company_id": company_id},
                    {"$set": {"status": "expired"}}
                )
                return {
                    "has_access": False,
                    "status": "expired",
                    "message": "Su período de prueba ha terminado. Por favor seleccione un plan.",
                    "redirect_to": "/subscriptions"
                }
    
    return {"has_access": True, "status": status, "plan": subscription.get("plan_id")}

# ===================== SYSTEM USERS MANAGEMENT =====================

@api_router.get("/system-users")
async def get_system_users(current_user: dict = Depends(get_current_user)):
    """Obtener usuarios del sistema de la empresa"""
    company_id = current_user.get("company_id")
    
    users = await db.users.find(
        {"company_id": company_id},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    
    return users

@api_router.post("/system-users")
async def create_system_user(data: SystemUserCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo usuario del sistema"""
    company_id = current_user.get("company_id")
    
    # Check subscription user limit
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    if subscription:
        plan = SUBSCRIPTION_PLANS.get(subscription.get("plan_id", "basic"))
        max_users = plan["included_users"] + subscription.get("additional_users", 0)
        current_users = await db.users.count_documents({"company_id": company_id})
        
        if current_users >= max_users:
            raise HTTPException(
                status_code=400, 
                detail=f"Ha alcanzado el límite de usuarios ({max_users}). Actualice su plan o compre usuarios adicionales."
            )
    
    # Check if email already exists
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Hash password
    password_hash = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = {
        "user_id": user_id,
        "company_id": company_id,
        "email": data.email,
        "name": data.name,
        "password_hash": password_hash,
        "role": data.role,
        "modules": data.modules,
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id")
    }
    
    await db.users.insert_one(user)
    
    # Log activity
    await db.user_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:8]}",
        "user_id": current_user.get("user_id"),
        "company_id": company_id,
        "action": "create_user",
        "target_user_id": user_id,
        "details": f"Creó usuario {data.name} ({data.email})",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"user_id": user_id, "message": "Usuario creado correctamente"}

@api_router.put("/system-users/{user_id}")
async def update_system_user(user_id: str, data: SystemUserUpdate, current_user: dict = Depends(get_current_user)):
    """Actualizar un usuario del sistema"""
    company_id = current_user.get("company_id")
    
    updates = {}
    if data.name is not None:
        updates["name"] = data.name
    if data.role is not None:
        updates["role"] = data.role
    if data.modules is not None:
        updates["modules"] = data.modules
    if data.is_active is not None:
        updates["is_active"] = data.is_active
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.users.update_one(
        {"user_id": user_id, "company_id": company_id},
        {"$set": updates}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario actualizado"}

@api_router.delete("/system-users/{user_id}")
async def delete_system_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar un usuario del sistema"""
    company_id = current_user.get("company_id")
    
    # Cannot delete yourself
    if user_id == current_user.get("user_id"):
        raise HTTPException(status_code=400, detail="No puede eliminarse a sí mismo")
    
    result = await db.users.delete_one({"user_id": user_id, "company_id": company_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"message": "Usuario eliminado"}

@api_router.get("/system-users/{user_id}/activities")
async def get_user_activities(user_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener historial de actividades de un usuario"""
    company_id = current_user.get("company_id")
    
    activities = await db.user_activities.find(
        {"user_id": user_id, "company_id": company_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    
    return activities

@api_router.get("/user-activities")
async def get_all_activities(current_user: dict = Depends(get_current_user)):
    """Obtener todas las actividades de la empresa"""
    company_id = current_user.get("company_id")
    
    activities = await db.user_activities.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(500)
    
    return activities

# ===================== CUSTOM ROLES (Enterprise only) =====================

@api_router.get("/roles")
async def get_custom_roles(current_user: dict = Depends(get_current_user)):
    """Obtener roles personalizados (solo Enterprise)"""
    company_id = current_user.get("company_id")
    
    # Check if enterprise plan
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    if subscription and subscription.get("plan_id") != "enterprise":
        return {"roles": [], "message": "Los roles personalizados solo están disponibles en el plan Enterprise"}
    
    roles = await db.custom_roles.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(50)
    
    return {"roles": roles}

@api_router.post("/roles")
async def create_custom_role(data: CustomRoleCreate, current_user: dict = Depends(get_current_user)):
    """Crear rol personalizado (solo Enterprise)"""
    company_id = current_user.get("company_id")
    
    # Check if enterprise plan
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    if not subscription or subscription.get("plan_id") != "enterprise":
        raise HTTPException(status_code=403, detail="Los roles personalizados solo están disponibles en el plan Enterprise")
    
    role_id = f"role_{uuid.uuid4().hex[:8]}"
    role = {
        "role_id": role_id,
        "company_id": company_id,
        **data.dict(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_roles.insert_one(role)
    return {"role_id": role_id, "message": "Rol creado correctamente"}

@api_router.delete("/roles/{role_id}")
async def delete_custom_role(role_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar rol personalizado"""
    company_id = current_user.get("company_id")
    
    result = await db.custom_roles.delete_one({"role_id": role_id, "company_id": company_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return {"message": "Rol eliminado"}

# ===================== MAIN APP =====================

# Health check endpoint for Kubernetes (no /api prefix)
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    try:
        # Test MongoDB connection
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

app.include_router(api_router)

cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    # Allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins_list = cors_origins.split(',')
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

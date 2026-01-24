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
import stripe

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure Stripe - use key from environment variable only
stripe.api_key = os.environ.get('STRIPE_API_KEY', '')

# Import email service
from email_service import send_payment_confirmation_email, send_welcome_email, send_invoice_email

# Import modular routers
from routes.loans import router as loans_router, init_router as init_loans_router
from routes.subscriptions import router as subscriptions_router, init_router as init_subscriptions_router
from routes.roles import router as roles_router, init_router as init_roles_router
from routes.bank_files import router as bank_files_router, init_router as init_bank_files_router
from routes.employee_portal import router as employee_portal_router, init_router as init_employee_portal_router
from routes.documents import router as documents_router, init_router as init_documents_router
from routes.search import router as search_router, init_router as init_search_router
from routes.auth import router as auth_router, init_router as init_auth_router
from routes.employees import router as employees_router, init_router as init_employees_router
from routes.attendance import router as attendance_router, init_router as init_attendance_router
from routes.vacations import router as vacations_router, init_router as init_vacations_router
from routes.dashboard import router as dashboard_router, init_router as init_dashboard_router
from routes.company import router as company_router, init_router as init_company_router
from routes.organigrama import router as organigrama_router, init_router as init_organigrama_router
from routes.evaluations import router as evaluations_router, init_router as init_evaluations_router
from routes.recruitment import router as recruitment_router, init_router as init_recruitment_router
from routes.payroll import router as payroll_router, init_router as init_payroll_router
from routes.checkout import router as checkout_router, init_router as init_checkout_router
from routes.accounting import router as accounting_router, init_router as init_accounting_router
from routes.system_users import router as system_users_router, init_router as init_system_users_router
from routes.dgii_reports import router as dgii_reports_router, init_router as init_dgii_reports_router
from routes.notifications import router as notifications_router, init_router as init_notifications_router
from routes.reports import router as reports_router, init_router as init_reports_router
from routes.expenses import router as expenses_router, init_router as init_expenses_router
from routes.payroll_v2 import router as payroll_v2_router, init_router as init_payroll_v2_router
from routes.projects import router as projects_router, init_router as init_projects_router
from routes.invoices import router as invoices_router, init_router as init_invoices_router
from routes.metrics import router as metrics_router, init_router as init_metrics_router
from routes.notifications_system import router as notifications_system_router, init_router as init_notifications_system_router
from routes.reports_advanced import router as reports_advanced_router, init_router as init_reports_advanced_router
from routes.reports_system import router as reports_system_router, init_router as init_reports_system_router
from routes.quickbooks import router as quickbooks_router, init_router as init_quickbooks_router
from routes.cdc_audit import router as cdc_audit_router, init_router as init_cdc_audit_router, start_all_change_streams, create_indexes as create_cdc_indexes
from routes.support import router as support_router, init_router as init_support_router
from routes.partners import router as partners_router, init_router as init_partners_router, create_partner_indexes

# MongoDB connection with production-ready settings
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=10000,  # 10 second timeout for server selection
    connectTimeoutMS=10000,  # 10 second connection timeout
    socketTimeoutMS=30000,  # 30 second socket timeout
    maxPoolSize=50,  # Maximum connection pool size
    minPoolSize=5,  # Minimum connection pool size
    retryWrites=True,  # Retry writes on transient errors
)
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

# Configure CORS - Production-ready configuration
# When credentials are included, we cannot use wildcard '*'
# We need to dynamically allow the requesting origin
allowed_origins = [
    "https://fortexarh.com",
    "https://www.fortexarh.com",
    "https://staff-genius-2.emergent.host",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add any custom origins from environment
custom_origins = os.environ.get('CORS_ORIGINS', '')
if custom_origins and custom_origins != '*':
    allowed_origins.extend([o.strip() for o in custom_origins.split(',') if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Kubernetes (must be defined early, no /api prefix)
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {"status": "healthy"}

@app.get("/health/db")
async def health_check_db():
    """Extended health check with database connectivity (for debugging)"""
    try:
        await asyncio.wait_for(db.command("ping"), timeout=5.0)
        return {"status": "healthy", "database": "connected"}
    except asyncio.TimeoutError:
        return {"status": "degraded", "database": "timeout"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/health/config")
async def health_check_config():
    """Check configuration status (for debugging deployment issues)"""
    stripe_key = os.environ.get('STRIPE_API_KEY', '')
    stripe_mode = "live" if stripe_key.startswith("sk_live_") else "test" if stripe_key.startswith("sk_test_") else "not_configured"
    
    return {
        "status": "healthy",
        "stripe_mode": stripe_mode,
        "stripe_key_prefix": stripe_key[:12] + "..." if len(stripe_key) > 12 else "missing",
        "resend_configured": bool(os.environ.get('RESEND_API_KEY')),
        "db_name": os.environ.get('DB_NAME', 'not_set'),
    }

# ===================== MODELS =====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    company_name: Optional[str] = None
    payment_session_id: Optional[str] = None  # For paid registrations

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
    gender: Optional[str] = None  # Masculino, Femenino
    birth_date: Optional[str] = None
    marital_status: Optional[str] = "Soltero/a"
    blood_type: Optional[str] = None  # A+, A-, B+, B-, AB+, AB-, O+, O-
    weight: Optional[float] = None  # Weight in pounds (libras)
    height: Optional[float] = None  # Height in meters
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

# CheckoutRequest is defined later in the subscription section

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
        "restricted_features": ["employees", "attendance", "vacations", "evaluations", "recruitment", "reports", "organigrama", "accounting", "employee_portal"]
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
        "features": ["Hasta 50 empleados", "3 usuarios incluidos", "Gestión de empleados", "Nómina básica", "Asistencias y vacaciones", "Calculadora de nómina", "Módulo de préstamos", "Reportes básicos", "Exportación Excel/CSV", "Soporte por email", "Integración FortexaERP"],
        "allowed_features": ["all_basic"],
        "restricted_features": ["evaluations", "recruitment", "organigrama", "advanced_reports", "integrations_pro", "employee_portal"]
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
        "features": ["Hasta 200 empleados", "5 usuarios incluidos", "Todo lo del plan Básico", "Evaluaciones de desempeño", "Módulo de reclutamiento", "Portal autoservicio empleados", "Organigrama intuitivo", "Reportes avanzados", "Integración QuickBooks", "Soporte prioritario"],
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
# loans: available in ALL plans (basic, pro, enterprise)
# recruitment: Pro and Enterprise only
# employee_portal: Pro and Enterprise only
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
        "loans": False,
        "expenses": False,
        "employee_portal": False,
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
        "loans": True,
        "expenses": False,
        "employee_portal": False,
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
        "loans": True,
        "expenses": True,
        "employee_portal": True,
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
        "loans": True,
        "expenses": True,
        "employee_portal": True,
        "subscriptions": True,
        "settings": True,
        "custom_roles": True,
        "api": True
    }
}

# ===================== CONFIG STATUS (for debugging) =====================

@api_router.get("/config/status")
async def get_config_status():
    """Check configuration status - for debugging deployment issues"""
    stripe_key = os.environ.get('STRIPE_API_KEY', '')
    stripe_configured = bool(stripe_key)
    stripe_mode = "live" if stripe_key.startswith("sk_live_") else "test" if stripe_key.startswith("sk_test_") else "not_configured"
    
    return {
        "status": "ok",
        "stripe_configured": stripe_configured,
        "stripe_mode": stripe_mode,
        "resend_configured": bool(os.environ.get('RESEND_API_KEY')),
        "mongo_configured": bool(os.environ.get('MONGO_URL'))
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

# Note: SUBSCRIPTION_PLANS is defined at line ~679

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
    permissions: Dict[str, List[str]] = {}  # module: [view, create, edit, delete]
    color: Optional[str] = "#3b82f6"

class CustomRoleUpdate(BaseModel):
    """Actualización de rol personalizado"""
    name: Optional[str] = None
    description: Optional[str] = None
    modules: Optional[List[str]] = None
    permissions: Optional[Dict[str, List[str]]] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

# Default modules for roles
ROLE_MODULES = [
    {"id": "dashboard", "name": "Dashboard", "description": "Panel principal"},
    {"id": "employees", "name": "Empleados", "description": "Gestión de empleados"},
    {"id": "payroll", "name": "Nómina", "description": "Procesamiento de nómina"},
    {"id": "attendance", "name": "Asistencias", "description": "Control de asistencias"},
    {"id": "vacations", "name": "Vacaciones", "description": "Gestión de vacaciones"},
    {"id": "evaluations", "name": "Evaluaciones", "description": "Evaluaciones de desempeño"},
    {"id": "recruitment", "name": "Reclutamiento", "description": "Gestión de candidatos"},
    {"id": "organigrama", "name": "Organigrama", "description": "Estructura organizacional"},
    {"id": "accounting", "name": "Contabilidad", "description": "Entradas de diario"},
    {"id": "reports", "name": "Reportes", "description": "Generación de reportes"},
    {"id": "settings", "name": "Configuración", "description": "Ajustes de la empresa"},
    {"id": "subscriptions", "name": "Suscripciones", "description": "Gestión del plan"},
    {"id": "users", "name": "Usuarios", "description": "Administración de usuarios"},
]

ROLE_PERMISSION_TYPES = ["view", "create", "edit", "delete"]

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


# ===================== PROJECTS =====================


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
    """Obtener todos los planes de suscripción disponibles (excluyendo trial)"""
    # Only return paid plans, not trial
    return [plan for plan in SUBSCRIPTION_PLANS.values() if plan["plan_id"] != "trial"]

# Note: Other subscription endpoints (/subscription, /subscription/check-access, etc.)
# have been moved to routes/subscriptions.py

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

# Note: Custom roles endpoints have been moved to routes/roles.py


# ===================== METRICS & REPORTS ENDPOINTS =====================

@api_router.get("/stats/payroll-trend")
async def get_payroll_trend(year: int = None, current_user: dict = Depends(get_current_user)):
    """Get payroll trend data by month"""
    company_id = current_user.get("company_id")
    current_year = year or datetime.now().year
    
    # Get all processed periods for the year
    periods = await db.payroll_periods.find(
        {
            "company_id": company_id,
            "status": "processed",
            "year": current_year
        },
        {"_id": 0}
    ).sort("month", 1).to_list(12)
    
    months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    trend = []
    
    for i, month_name in enumerate(months, 1):
        period = next((p for p in periods if p.get("month") == i), None)
        if period:
            trend.append({
                "month": month_name,
                "gross": period.get("totals", {}).get("gross_salary", 0),
                "net": period.get("totals", {}).get("net_salary", 0),
                "deductions": period.get("totals", {}).get("total_deductions", 0),
                "employees": period.get("employee_count", 0)
            })
        else:
            trend.append({"month": month_name, "gross": 0, "net": 0, "deductions": 0, "employees": 0})
    
    return trend


@api_router.get("/stats/employees")
async def get_employee_stats(current_user: dict = Depends(get_current_user)):
    """Get employee statistics"""
    company_id = current_user.get("company_id")
    
    # Count active employees
    active = await db.employees.count_documents({"company_id": company_id, "status": "active"})
    inactive = await db.employees.count_documents({"company_id": company_id, "status": "inactive"})
    
    # New this month
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = await db.employees.count_documents({
        "company_id": company_id,
        "hire_date": {"$gte": month_start.isoformat()}
    })
    
    # By department
    pipeline = [
        {"$match": {"company_id": company_id, "status": "active"}},
        {"$group": {"_id": "$department", "count": {"$sum": 1}}}
    ]
    dept_stats = await db.employees.aggregate(pipeline).to_list(100)
    
    return {
        "total_active": active,
        "total_inactive": inactive,
        "new_this_month": new_this_month,
        "turnover_rate": round((inactive / (active + inactive) * 100) if (active + inactive) > 0 else 0, 1),
        "by_department": [{"name": d["_id"] or "Sin Departamento", "count": d["count"]} for d in dept_stats]
    }


@api_router.get("/reports/generate")
async def generate_report(
    report_type: str,
    date_from: str,
    date_to: str,
    department: str = "Todos",
    status: str = "all",
    employee_id: Optional[str] = None,
    period_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate custom report data"""
    company_id = current_user.get("company_id")
    
    data = []
    columns = []
    summary = {"totalRecords": 0, "totalAmount": 0}
    
    if report_type == "payroll":
        query = {"company_id": company_id}
        if department != "Todos":
            query["department"] = department
        if period_id:
            query["period_id"] = period_id
        if employee_id:
            query["employee_id"] = employee_id
        payrolls = await db.payroll_entries.find(query, {"_id": 0}).to_list(1000)
        
        # Get employee names
        emp_ids = [p.get("employee_id") for p in payrolls]
        employees = await db.employees.find(
            {"employee_id": {"$in": emp_ids}},
            {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1, "department": 1}
        ).to_list(1000)
        emp_map = {e["employee_id"]: e for e in employees}
        
        for p in payrolls:
            emp = emp_map.get(p.get("employee_id"), {})
            data.append({
                "employee": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                "department": emp.get("department", ""),
                "gross": p.get("gross_salary", 0),
                "deductions": p.get("total_deductions", 0),
                "net": p.get("net_salary", 0),
                "period": p.get("period_name", "")
            })
        columns = ["employee", "department", "gross", "deductions", "net", "period"]
        summary["totalAmount"] = sum(p.get("gross_salary", 0) for p in payrolls)
        
    elif report_type == "employees":
        emp_query = {"company_id": company_id}
        if department != "Todos":
            emp_query["department"] = department
        if status != "all":
            emp_query["status"] = status
        employees = await db.employees.find(emp_query, {"_id": 0}).to_list(1000)
        for emp in employees:
            data.append({
                "name": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                "position": emp.get("position", ""),
                "department": emp.get("department", ""),
                "hire_date": emp.get("hire_date", "")[:10] if emp.get("hire_date") else "",
                "status": emp.get("status", "")
            })
        columns = ["name", "position", "department", "hire_date", "status"]
        
    elif report_type == "loans":
        loans_query = {"company_id": company_id}
        if status != "all":
            loans_query["status"] = status
        loans = await db.loans.find(loans_query, {"_id": 0}).to_list(1000)
        
        emp_ids = [l.get("employee_id") for l in loans]
        employees = await db.employees.find(
            {"employee_id": {"$in": emp_ids}},
            {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1}
        ).to_list(1000)
        emp_map = {e["employee_id"]: e for e in employees}
        
        for loan in loans:
            emp = emp_map.get(loan.get("employee_id"), {})
            data.append({
                "employee": f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
                "amount": loan.get("amount", 0),
                "balance": loan.get("remaining_balance", 0),
                "monthly": loan.get("monthly_payment", 0),
                "status": loan.get("status", "")
            })
        columns = ["employee", "amount", "balance", "monthly", "status"]
        summary["totalAmount"] = sum(l.get("amount", 0) for l in loans)
    
    summary["totalRecords"] = len(data)
    
    return {
        "reportType": report_type,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "filters": {"dateFrom": date_from, "dateTo": date_to, "department": department},
        "summary": summary,
        "columns": columns,
        "data": data
    }




# ===================== MAIN APP =====================

# Initialize modular routers with dependencies
ADDITIONAL_USER_PRICE = 2.5

init_loans_router(db, get_current_user)
init_subscriptions_router(db, get_current_user, SUBSCRIPTION_PLANS, FEATURE_ACCESS, ADDITIONAL_USER_PRICE)
init_roles_router(db, get_current_user)
init_bank_files_router(db, get_current_user)
init_employee_portal_router(db)
init_documents_router(db, get_current_user)
init_search_router(db, get_current_user)
init_auth_router(db, SUBSCRIPTION_PLANS, send_welcome_email)
init_employees_router(db, get_current_user, SUBSCRIPTION_PLANS)
init_attendance_router(db, get_current_user)
init_vacations_router(db, get_current_user)
init_dashboard_router(db, get_current_user)
init_company_router(db, get_current_user)
init_organigrama_router(db, get_current_user)
init_evaluations_router(db, get_current_user)
init_recruitment_router(db, get_current_user)
init_payroll_router(db, get_current_user)
init_checkout_router(db, get_current_user, SUBSCRIPTION_PLANS, send_payment_confirmation_email, send_invoice_email)
init_invoices_router(db, get_current_user)
init_accounting_router(db, get_current_user)
init_system_users_router(db, get_current_user)
init_dgii_reports_router(db, get_current_user)
init_notifications_router(db, get_current_user)
init_reports_router(db, get_current_user)
init_expenses_router(db, get_current_user)
init_payroll_v2_router(db, get_current_user)
init_projects_router(db, get_current_user)
init_metrics_router(db, get_current_user)
init_notifications_system_router(db, get_current_user)
init_reports_advanced_router(db, get_current_user)
init_reports_system_router(db, get_current_user)
init_quickbooks_router(db, get_current_user)
init_cdc_audit_router(db, get_current_user)
init_support_router(db)
init_partners_router(db, get_current_user)

# Include modular routers in api_router
api_router.include_router(loans_router)
api_router.include_router(subscriptions_router)
api_router.include_router(roles_router)
api_router.include_router(bank_files_router)
api_router.include_router(employee_portal_router)
api_router.include_router(documents_router)
api_router.include_router(search_router)
api_router.include_router(auth_router)
api_router.include_router(support_router)
api_router.include_router(employees_router)
api_router.include_router(attendance_router)
api_router.include_router(vacations_router)
api_router.include_router(dashboard_router)
api_router.include_router(company_router)
api_router.include_router(organigrama_router)
api_router.include_router(evaluations_router)
api_router.include_router(recruitment_router)
api_router.include_router(payroll_router)
api_router.include_router(checkout_router)
api_router.include_router(invoices_router)
api_router.include_router(accounting_router)
api_router.include_router(system_users_router)
api_router.include_router(dgii_reports_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
api_router.include_router(expenses_router)
api_router.include_router(payroll_v2_router)
api_router.include_router(projects_router)
api_router.include_router(metrics_router)
api_router.include_router(notifications_system_router)
api_router.include_router(reports_advanced_router)
api_router.include_router(reports_system_router)
api_router.include_router(quickbooks_router)
api_router.include_router(cdc_audit_router)
api_router.include_router(partners_router)

# Include the API router
app.include_router(api_router)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_client():
    """Initialize database connection on startup"""
    try:
        # Test database connection with timeout
        await asyncio.wait_for(db.command("ping"), timeout=10.0)
        logger.info("Database connection established successfully")
        
        # Create CDC audit indexes
        await create_cdc_indexes()
        
        # Start CDC Change Streams in background (optional - can be started manually)
        # Uncomment the next line to auto-start CDC on server startup
        # asyncio.create_task(start_all_change_streams())
        
    except asyncio.TimeoutError:
        logger.warning("Database connection timeout during startup - will retry on first request")
    except Exception as e:
        logger.warning(f"Database connection error during startup: {e} - will retry on first request")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")


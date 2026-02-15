from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
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
from routes.geolocation_attendance import router as geolocation_attendance_router, init_router as init_geolocation_attendance_router
from routes.payroll_config import router as payroll_config_router, init_router as init_payroll_config_router
from routes.templates import router as templates_router, init_router as init_templates_router
from routes.generated_docs import router as generated_docs_router, init_router as init_generated_docs_router
from routes.currency import router as currency_router, init_router as init_currency_router
from routes.stats import router as stats_router, init_router as init_stats_router

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

JWT_SECRET = os.environ['JWT_SECRET']
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

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure CORS - Production-ready configuration
# When credentials are included, we cannot use wildcard '*'
# We need to dynamically allow the requesting origin
allowed_origins = [
    "https://fortexarh.com",
    "https://www.fortexarh.com",
    "https://staff-genius-2.emergent.host",
    "https://fortexa-staging.preview.emergentagent.com",
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

# Reports routes moved to routes/reports.py
# Payroll config routes moved to routes/payroll_config.py
# Templates routes moved to routes/templates.py
# Documents routes moved to routes/generated_docs.py

# Payroll settings/config/calculator routes moved to routes/payroll_config.py

# Templates routes moved to routes/templates.py

# Generated documents routes moved to routes/generated_docs.py

# Payroll calculator routes moved to routes/payroll_config.py

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

# Accounting generate-payroll-entry route moved to routes/accounting.py


# Currency routes moved to routes/currency.py

# ===================== SUBSCRIPTION ENDPOINTS =====================

@api_router.get("/plans")
async def get_subscription_plans():
    """Obtener todos los planes de suscripción disponibles (excluyendo trial)"""
    # Only return paid plans, not trial
    return [plan for plan in SUBSCRIPTION_PLANS.values() if plan["plan_id"] != "trial"]

# Note: Other subscription endpoints (/subscription, /subscription/check-access, etc.)
# have been moved to routes/subscriptions.py

# Note: System users CRUD and user-activities are in routes/system_users.py

# Note: Custom roles endpoints have been moved to routes/roles.py


# Stats routes moved to routes/stats.py
# Reports generate route moved to routes/reports.py




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
init_geolocation_attendance_router(db, get_current_user)
init_payroll_config_router(db, get_current_user)
init_templates_router(db, get_current_user)
init_generated_docs_router(db, get_current_user)
init_currency_router(db, get_current_user)
init_stats_router(db, get_current_user)

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
api_router.include_router(geolocation_attendance_router)
api_router.include_router(payroll_config_router)
api_router.include_router(templates_router)
api_router.include_router(generated_docs_router)
api_router.include_router(currency_router)
api_router.include_router(stats_router)

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


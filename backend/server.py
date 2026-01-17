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
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    position: str
    department: str
    hire_date: str
    salary: float
    status: str = "active"

class EmployeeResponse(BaseModel):
    employee_id: str
    company_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    position: str
    department: str
    hire_date: str
    salary: float
    status: str
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
    employee_id: Optional[str] = None
    title: str
    department: str
    parent_id: Optional[str] = None
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

# ISR (Impuesto Sobre la Renta) - DGII Tables 2026
# Monthly thresholds (based on DGII retention tables for salaried employees)
ISR_MONTHLY_EXEMPT = 34685.00  # Exento hasta este monto mensual
ISR_MONTHLY_BRACKET_1 = 52027.42  # 15% sobre excedente de 34,685.01 (624,329/12)
ISR_MONTHLY_BRACKET_2 = 72260.25  # 20% sobre excedente de 52,027.42 (867,123/12)
# Above 72,260.25 = 25% sobre excedente

# Fixed monthly tax amounts per DGII 2026
ISR_FIXED_MONTHLY_BRACKET_2 = 2601.33  # Monto fijo mensual para tramo 20% (31,216/12)
ISR_FIXED_MONTHLY_BRACKET_3 = 6648.00  # Monto fijo mensual para tramo 25% (79,776/12)

# Annual thresholds (for reference)
ISR_ANNUAL_EXEMPT = 416220.00  # Exento anual (34,685 * 12)
ISR_ANNUAL_BRACKET_1 = 624329.00
ISR_ANNUAL_BRACKET_2 = 867123.00
ISR_FIXED_BRACKET_2 = 31216.00  # Monto fijo anual para tramo 20%
ISR_FIXED_BRACKET_3 = 79776.00  # Monto fijo anual para tramo 25%

def calculate_isr_monthly(gross_monthly: float) -> dict:
    """
    Calculate ISR (Impuesto Sobre la Renta) based on DGII 2026 monthly retention tables.
    
    IMPORTANTE: La tabla de retención de ISR para asalariados calcula sobre el 
    SALARIO BRUTO MENSUAL directamente, no sobre la base después de restar TSS.
    
    Escala mensual para retenciones ISR 2026:
    - Hasta RD$34,685.00 mensual: Exento
    - De RD$34,685.01 a RD$52,027.42: 15% del excedente de RD$34,685.01
    - De RD$52,027.43 a RD$72,260.25: RD$2,601.33 + 20% del excedente de RD$52,027.42
    - De RD$72,260.26 en adelante: RD$6,648.00 + 25% del excedente de RD$72,260.25
    
    Returns dict with: taxable_base, annual_taxable, isr_annual, isr_monthly, tax_bracket
    """
    # ISR se calcula sobre el salario bruto mensual directamente
    monthly_gross = gross_monthly
    
    # Apply progressive tax brackets (DGII 2026 - Monthly calculation)
    isr_monthly = 0.0
    tax_bracket = "Exento"
    
    if monthly_gross <= ISR_MONTHLY_EXEMPT:
        # Exento: Hasta RD$34,685.00 mensual
        isr_monthly = 0.0
        tax_bracket = "Exento (0%)"
    elif monthly_gross <= ISR_MONTHLY_BRACKET_1:
        # 15%: De RD$34,685.01 a RD$52,027.42
        excess = monthly_gross - ISR_MONTHLY_EXEMPT
        isr_monthly = excess * 0.15
        tax_bracket = "15%"
    elif monthly_gross <= ISR_MONTHLY_BRACKET_2:
        # 20%: RD$2,601.33 + 20% del excedente de RD$52,027.42
        excess = monthly_gross - ISR_MONTHLY_BRACKET_1
        isr_monthly = ISR_FIXED_MONTHLY_BRACKET_2 + (excess * 0.20)
        tax_bracket = "20%"
    else:
        # 25%: RD$6,648.00 + 25% del excedente de RD$72,260.25
        excess = monthly_gross - ISR_MONTHLY_BRACKET_2
        isr_monthly = ISR_FIXED_MONTHLY_BRACKET_3 + (excess * 0.25)
        tax_bracket = "25%"
    
    isr_monthly = round(isr_monthly, 2)
    isr_annual = round(isr_monthly * 12, 2)
    annual_taxable = round(monthly_gross * 12, 2)
    
    return {
        "taxable_base_monthly": round(monthly_gross, 2),
        "annual_taxable": annual_taxable,
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
    "free": {
        "plan_id": "free",
        "name": "Prueba Gratuita",
        "base_price": 0.0,
        "price_per_employee": 0.0,
        "max_employees": 5,
        "features": ["Hasta 5 empleados", "Gestión básica de empleados", "Control de asistencias", "Soporte por email"]
    },
    "basic": {
        "plan_id": "basic",
        "name": "FortexaRH Básico",
        "base_price": 10.0,
        "price_per_employee": 1.5,
        "max_employees": 50,
        "features": ["Hasta 50 empleados", "Gestión de empleados", "Nómina básica", "Asistencias", "Vacaciones", "Soporte por email"]
    },
    "pro": {
        "plan_id": "pro",
        "name": "FortexaRH Pro",
        "base_price": 20.0,
        "price_per_employee": 1.5,
        "max_employees": 200,
        "features": ["Hasta 200 empleados", "Todas las funciones básicas", "Evaluaciones de desempeño", "Reclutamiento", "Reportes avanzados", "Soporte prioritario"]
    },
    "enterprise": {
        "plan_id": "enterprise",
        "name": "FortexaRH Enterprise",
        "base_price": 76.0,
        "price_per_employee": 1.5,
        "max_employees": 9999,
        "features": ["Empleados ilimitados", "Todas las funciones", "API personalizada", "Soporte 24/7", "Gerente de cuenta dedicado", "Capacitación incluida"]
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
    
    plan = SUBSCRIPTION_PLANS.get(company.get("subscription_plan", "free"))
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
        "employee_id": data.employee_id,
        "employee_name": employee_name,
        "title": data.title,
        "department": data.department,
        "parent_id": data.parent_id,
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

# ===================== MAIN APP =====================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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

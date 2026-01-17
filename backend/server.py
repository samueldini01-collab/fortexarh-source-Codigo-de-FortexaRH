from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx
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

app = FastAPI(title="HRflow SaaS API")
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

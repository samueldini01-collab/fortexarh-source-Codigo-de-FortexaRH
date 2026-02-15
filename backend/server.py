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
from routes.payroll import router as payroll_v2_router, legacy_router as payroll_router, init_router as init_payroll_router
from routes.checkout import router as checkout_router, init_router as init_checkout_router
from routes.accounting import router as accounting_router, init_router as init_accounting_router
from routes.system_users import router as system_users_router, init_router as init_system_users_router
from routes.dgii_reports import router as dgii_reports_router, init_router as init_dgii_reports_router
from routes.notifications import router as notifications_router, init_router as init_notifications_router
from routes.reports import router as reports_router, init_router as init_reports_router
from routes.expenses import router as expenses_router, init_router as init_expenses_router
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
    "https://fortexa-preview.preview.emergentagent.com",
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
        await asyncio.wait_for(db.command("ping"), timeout=10.0)
        logger.info("Database connection established successfully")

        # Create CDC audit indexes
        await create_cdc_indexes()

        # Create performance indexes for common queries
        await create_performance_indexes()

    except asyncio.TimeoutError:
        logger.warning("Database connection timeout during startup - will retry on first request")
    except Exception as e:
        logger.warning(f"Database connection error during startup: {e} - will retry on first request")


async def create_performance_indexes():
    """Create indexes for frequently queried collections"""
    try:
        # Employees - most queried collection
        await db.employees.create_index([("company_id", 1), ("status", 1)])
        await db.employees.create_index([("company_id", 1), ("department", 1)])
        await db.employees.create_index([("employee_id", 1)], unique=True)

        # Users
        await db.users.create_index([("email", 1)], unique=True)
        await db.users.create_index([("user_id", 1)], unique=True)
        await db.users.create_index([("company_id", 1)])

        # Payroll entries
        await db.payroll_entries.create_index([("company_id", 1), ("period_id", 1)])
        await db.payroll_entries.create_index([("company_id", 1), ("employee_id", 1)])

        # Payroll periods
        await db.payroll_periods.create_index([("company_id", 1), ("year", 1), ("month", 1)])
        await db.payroll_periods.create_index([("company_id", 1), ("status", 1)])

        # Attendances
        await db.attendances.create_index([("company_id", 1), ("date", 1)])
        await db.attendances.create_index([("company_id", 1), ("employee_id", 1)])

        # Vacations
        await db.vacations.create_index([("company_id", 1), ("status", 1)])
        await db.vacations.create_index([("company_id", 1), ("employee_id", 1)])

        # Journal entries
        await db.journal_entries.create_index([("company_id", 1), ("period", 1)])
        await db.journal_entries.create_index([("company_id", 1), ("status", 1)])

        # Accounts
        await db.accounts.create_index([("company_id", 1), ("code", 1)])

        # Loans
        await db.loans.create_index([("company_id", 1), ("employee_id", 1)])
        await db.loans.create_index([("company_id", 1), ("status", 1)])

        # Notifications
        await db.notifications.create_index([("company_id", 1), ("created_at", -1)])

        # Sessions
        await db.user_sessions.create_index([("session_token", 1)])
        await db.user_sessions.create_index([("expires_at", 1)], expireAfterSeconds=0)

        # Templates & Documents
        await db.templates.create_index([("company_id", 1)])
        await db.generated_documents.create_index([("company_id", 1)])

        # Evaluations
        await db.evaluations.create_index([("company_id", 1), ("employee_id", 1)])

        # Expenses
        await db.expenses.create_index([("company_id", 1), ("status", 1)])

        logger.info("Performance indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (non-fatal): {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")


from fastapi import FastAPI, APIRouter, Request
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
import asyncio

# Centralized config
from config import db, client, SUBSCRIPTION_PLANS

# Standardized error handling
from utils.errors import AppError, app_error_handler

# Import modular routers
from routes.loans import router as loans_router
from routes.subscriptions import router as subscriptions_router
from routes.roles import router as roles_router
from routes.bank_files import router as bank_files_router
from routes.employee_portal import router as employee_portal_router
from routes.documents import router as documents_router
from routes.search import router as search_router
from routes.auth import router as auth_router
from routes.employees import router as employees_router
from routes.attendance import router as attendance_router
from routes.vacations import router as vacations_router
from routes.dashboard import router as dashboard_router
from routes.company import router as company_router
from routes.organigrama import router as organigrama_router
from routes.evaluations import router as evaluations_router
from routes.recruitment import router as recruitment_router
from routes.payroll import router as payroll_router
from routes.payroll_exports import router as payroll_exports_router
from routes.checkout import router as checkout_router
from routes.accounting import router as accounting_router
from routes.system_users import router as system_users_router
from routes.dgii_reports import router as dgii_reports_router
from routes.notifications import router as notifications_router
from routes.reports import router as reports_router
from routes.expenses import router as expenses_router
from routes.projects import router as projects_router
from routes.invoices import router as invoices_router
from routes.metrics import router as metrics_router
from routes.notifications_system import router as notifications_system_router
from routes.reports_advanced import router as reports_advanced_router
from routes.reports_system import router as reports_system_router
from routes.quickbooks import router as quickbooks_router
from routes.cdc_audit import router as cdc_audit_router, start_all_change_streams, create_indexes as create_cdc_indexes
from routes.support import router as support_router
from routes.partners import router as partners_router, create_partner_indexes
from routes.partner_payments import router as partner_payments_router
from routes.geolocation_attendance import router as geolocation_attendance_router
from routes.payroll_config import router as payroll_config_router
from routes.templates import router as templates_router
from routes.generated_docs import router as generated_docs_router
from routes.currency import router as currency_router
from routes.stats import router as stats_router
from routes.two_factor import router as two_factor_router
from routes.notification_preferences import router as notification_preferences_router
from routes.super_admin import router as super_admin_router
from routes.fortexaerp import router as fortexaerp_router
from routes.workflows import router as workflows_router
from routes.contracts import router as contracts_router, seed_system_templates
from routes.hr_alerts import router as hr_alerts_router
from routes.liquidation import router as liquidation_router
from routes.salary_history import router as salary_history_router
from routes.admin_permissions import router as admin_permissions_router

# ===================== APP SETUP =====================

app = FastAPI(title="FortexaRH SaaS API")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)

api_router = APIRouter(prefix="/api")

# CORS - Production-ready configuration
allowed_origins = [
    "https://fortexarh.com",
    "https://www.fortexarh.com",
    "https://staff-genius-2.emergent.host",
    "https://company-config-debug.preview.emergentagent.com",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
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

# ===================== HEALTH CHECKS =====================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fortexarh-api"}


@api_router.get("/health")
async def api_health_check():
    return {"status": "healthy", "service": "fortexarh-api"}

@app.get("/health/db")
async def health_check_db():
    try:
        await asyncio.wait_for(db.command("ping"), timeout=5.0)
        return {"status": "healthy", "database": "connected"}
    except asyncio.TimeoutError:
        return {"status": "degraded", "database": "timeout"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/health/config")
async def health_check_config():
    stripe_key = os.environ.get('STRIPE_API_KEY', '')
    stripe_mode = "live" if stripe_key.startswith("sk_live_") else "test" if stripe_key.startswith("sk_test_") else "not_configured"
    return {
        "status": "healthy",
        "stripe_mode": stripe_mode,
        "stripe_key_prefix": stripe_key[:12] + "..." if len(stripe_key) > 12 else "missing",
        "resend_configured": bool(os.environ.get('RESEND_API_KEY')),
        "db_name": os.environ.get('DB_NAME', 'not_set'),
    }

# ===================== API ENDPOINTS =====================

@api_router.get("/config/status")
async def get_config_status():
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

@api_router.get("/plans")
async def get_subscription_plans():
    return [plan for plan in SUBSCRIPTION_PLANS.values() if plan["plan_id"] != "trial"]

# ===================== INCLUDE ROUTERS =====================

for r in [
    loans_router, subscriptions_router, roles_router, bank_files_router,
    employee_portal_router, documents_router, search_router, auth_router,
    support_router, employees_router, attendance_router, vacations_router,
    dashboard_router, company_router, organigrama_router, evaluations_router,
    recruitment_router, payroll_router, payroll_exports_router, checkout_router, invoices_router,
    accounting_router, system_users_router, dgii_reports_router,
    notifications_router, reports_router, expenses_router, projects_router,
    metrics_router, notifications_system_router, reports_advanced_router,
    reports_system_router, quickbooks_router, cdc_audit_router,
    partners_router, partner_payments_router, geolocation_attendance_router, payroll_config_router,
    templates_router, generated_docs_router, currency_router, stats_router,
    two_factor_router,
    notification_preferences_router,
    super_admin_router,
    fortexaerp_router,
    workflows_router,
    contracts_router,
    hr_alerts_router,
    liquidation_router,
    salary_history_router,
    admin_permissions_router,
]:
    api_router.include_router(r)

app.include_router(api_router)

# ===================== STARTUP / SHUTDOWN =====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db_client():
    try:
        await asyncio.wait_for(db.command("ping"), timeout=10.0)
        logger.info("Database connection established successfully")
        await create_cdc_indexes()
        await create_performance_indexes()
        await seed_system_templates()
    except asyncio.TimeoutError:
        logger.warning("Database connection timeout during startup - will retry on first request")
    except Exception as e:
        logger.warning(f"Database connection error during startup: {e} - will retry on first request")


async def create_performance_indexes():
    try:
        await db.employees.create_index([("company_id", 1), ("status", 1)])
        await db.employees.create_index([("company_id", 1), ("department", 1)])
        await db.employees.create_index([("employee_id", 1)], unique=True)
        await db.users.create_index([("email", 1)], unique=True)
        await db.users.create_index([("user_id", 1)], unique=True)
        await db.users.create_index([("company_id", 1)])
        await db.payroll_entries.create_index([("company_id", 1), ("period_id", 1)])
        await db.payroll_entries.create_index([("company_id", 1), ("employee_id", 1)])
        await db.payroll_periods.create_index([("company_id", 1), ("year", 1), ("month", 1)])
        await db.payroll_periods.create_index([("company_id", 1), ("status", 1)])
        await db.attendances.create_index([("company_id", 1), ("date", 1)])
        await db.attendances.create_index([("company_id", 1), ("employee_id", 1)])
        await db.vacations.create_index([("company_id", 1), ("status", 1)])
        await db.vacations.create_index([("company_id", 1), ("employee_id", 1)])
        await db.journal_entries.create_index([("company_id", 1), ("period", 1)])
        await db.journal_entries.create_index([("company_id", 1), ("status", 1)])
        await db.accounts.create_index([("company_id", 1), ("code", 1)])
        await db.loans.create_index([("company_id", 1), ("employee_id", 1)])
        await db.loans.create_index([("company_id", 1), ("status", 1)])
        await db.notifications.create_index([("company_id", 1), ("created_at", -1)])
        await db.user_sessions.create_index([("session_token", 1)])
        await db.user_sessions.create_index([("expires_at", 1)], expireAfterSeconds=0)
        await db.templates.create_index([("company_id", 1)])
        await db.generated_documents.create_index([("company_id", 1)])
        await db.contract_templates.create_index([("template_id", 1)], unique=True)
        await db.contract_templates.create_index([("company_id", 1)])
        await db.evaluations.create_index([("company_id", 1), ("employee_id", 1)])
        await db.expenses.create_index([("company_id", 1), ("status", 1)])
        await db.employee_notifications.create_index([("employee_id", 1), ("company_id", 1), ("created_at", -1)])
        await db.employee_notifications.create_index([("employee_id", 1), ("read", 1)])
        logger.info("Performance indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (non-fatal): {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("Database connection closed")

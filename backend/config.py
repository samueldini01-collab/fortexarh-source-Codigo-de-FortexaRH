"""
FortexaRH - Centralized Configuration
Single source of truth for all application configuration.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with production-ready settings
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=30000,
    maxPoolSize=50,
    minPoolSize=5,
    retryWrites=True,
)
db = client[os.environ['DB_NAME']]

# JWT configuration
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

# Stripe configuration
import stripe
stripe.api_key = os.environ.get('STRIPE_API_KEY', '')

# Resend configuration
import resend
resend.api_key = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# QuickBooks configuration
QB_CLIENT_ID = os.environ.get('QUICKBOOKS_CLIENT_ID', '')
QB_CLIENT_SECRET = os.environ.get('QUICKBOOKS_CLIENT_SECRET', '')
QB_REALM_ID = os.environ.get('QUICKBOOKS_REALM_ID', '')
_qb_redirect = os.environ.get('QUICKBOOKS_REDIRECT_URI', '')
_frontend_url = os.environ.get('FRONTEND_URL', '')
QB_REDIRECT_URI = _qb_redirect if _qb_redirect else (f"{_frontend_url}/api/quickbooks/callback" if _frontend_url else '')

# Subscription pricing
ADDITIONAL_USER_PRICE = 2.5

# Subscription plans
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
        "features": ["Hasta 200 empleados", "5 usuarios incluidos", "Todo lo del plan Básico", "Evaluaciones de desempeño", "Módulo de reclutamiento", "Portal autoservicio empleados", "Organigrama intuitivo", "Reportes avanzados", "Integración QuickBooks", "QuickBooks Desktop (IIF)", "Pagos ACH bancarios", "Soporte prioritario"],
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
        "features": ["Empleados ilimitados", "7 usuarios incluidos", "Todo lo del plan Pro", "Roles personalizados", "Múltiples administradores", "Contratos laborales", "Firma electrónica", "Workflows de aprobación", "API personalizada", "Integración SAP/Oracle/Dynamics", "Soporte 24/7", "Gerente de cuenta dedicado"],
        "allowed_features": ["all"],
        "restricted_features": []
    }
}

# Feature access mapping based on plan
FEATURE_ACCESS = {
    "trial": {
        "dashboard": True, "payroll_calculator": True, "employees": False,
        "attendance": False, "vacations": False, "evaluations": False,
        "recruitment": False, "reports": False, "organigrama": False,
        "accounting": False, "loans": False, "expenses": False,
        "employee_portal": False, "subscriptions": True, "settings": True,
        "global_compliance": False, "fiscal_comparison": False
    },
    "basic": {
        "dashboard": True, "payroll_calculator": True, "employees": True,
        "attendance": True, "vacations": True, "evaluations": False,
        "recruitment": False, "reports": True, "organigrama": False,
        "accounting": True, "loans": True, "expenses": False,
        "employee_portal": False, "subscriptions": True, "settings": True,
        "global_compliance": False, "fiscal_comparison": False
    },
    "pro": {
        "dashboard": True, "payroll_calculator": True, "employees": True,
        "attendance": True, "vacations": True, "evaluations": True,
        "recruitment": True, "reports": True, "organigrama": True,
        "accounting": True, "loans": True, "expenses": True,
        "employee_portal": True, "subscriptions": True, "settings": True,
        "global_compliance": False, "fiscal_comparison": True
    },
    "enterprise": {
        "dashboard": True, "payroll_calculator": True, "employees": True,
        "attendance": True, "vacations": True, "evaluations": True,
        "recruitment": True, "reports": True, "organigrama": True,
        "accounting": True, "loans": True, "expenses": True,
        "employee_portal": True, "subscriptions": True, "settings": True,
        "custom_roles": True, "api": True,
        "global_compliance": True, "fiscal_comparison": True
    }
}

# Default modules for roles
DEFAULT_MODULES = [
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

# Permission types
PERMISSION_TYPES = ["view", "create", "edit", "delete"]

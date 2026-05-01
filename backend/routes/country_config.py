"""
Country Configuration - Multi-country payroll engine
Stores tax rates, social security, ISR scales, currencies, document types per country.
Existing DR companies are auto-migrated.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/country-config", tags=["Country Config"])

# ===================== COUNTRY PROFILES =====================
# Each profile contains everything needed to calculate payroll for that country

COUNTRY_PROFILES = {
    "DO": {
        "code": "DO",
        "name": "República Dominicana",
        "currency": "DOP",
        "currency_symbol": "RD$",
        "currency_name": "Peso Dominicano",
        "locale": "es-DO",
        "document_types": ["Cédula", "Pasaporte", "RNC"],
        "working_days_month": 23.83,
        "weekly_hours": 44,
        "vacation_days_per_year": 14,
        "probation_days": 90,
        "christmas_bonus": True,
        "christmas_bonus_name": "Regalía Pascual (Salario 13)",
        "social_security": {
            "system_name": "TSS (Tesorería de la Seguridad Social)",
            "employee_deductions": [
                {"code": "SFS", "name": "Seguro Familiar de Salud", "rate": 0.0304, "cap_monthly": None},
                {"code": "AFP", "name": "Fondo de Pensiones", "rate": 0.0287, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "SFS_EMP", "name": "SFS Empleador", "rate": 0.0709, "cap_monthly": None},
                {"code": "AFP_EMP", "name": "AFP Empleador", "rate": 0.0710, "cap_monthly": None},
                {"code": "SRL", "name": "Seguro de Riesgos Laborales", "rate": 0.01, "cap_monthly": None},
                {"code": "INFOTEP", "name": "INFOTEP", "rate": 0.01, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISR (Impuesto Sobre la Renta)",
            "agency": "DGII",
            "exempt_monthly": 34685.00,
            "brackets": [
                {"min": 0, "max": 416220, "rate": 0, "fixed": 0},
                {"min": 416220.01, "max": 624329, "rate": 0.15, "fixed": 0},
                {"min": 624329.01, "max": 867123, "rate": 0.20, "fixed": 31216},
                {"min": 867123.01, "max": None, "rate": 0.25, "fixed": 79776}
            ]
        },
        "severance": {
            "preaviso_rules": [
                {"min_months": 0, "max_months": 3, "days": 0},
                {"min_months": 3, "max_months": 6, "days": 7},
                {"min_months": 6, "max_months": 12, "days": 14},
                {"min_months": 12, "max_months": None, "days": 28}
            ],
            "cesantia_formula": "DR_ART80"
        },
        "reports": ["DGII_IR3", "DGII_IR4", "DGII_IR17", "TSS_TXT"],
        "contract_types": ["indefinido", "temporal", "obra", "pasantia"],
        "permission_types": [
            {"code": "personal", "name": "Personal", "days": "1-3"},
            {"code": "medico", "name": "Médico", "days": "Según certificado"},
            {"code": "duelo", "name": "Duelo", "days": "3"},
            {"code": "matrimonio", "name": "Matrimonio", "days": "5"},
            {"code": "paternidad", "name": "Paternidad", "days": "2"},
            {"code": "maternidad", "name": "Maternidad", "days": "84"},
            {"code": "otro", "name": "Otro", "days": "Variable"}
        ]
    },
    "CO": {
        "code": "CO",
        "name": "Colombia",
        "currency": "COP",
        "currency_symbol": "$",
        "currency_name": "Peso Colombiano",
        "locale": "es-CO",
        "document_types": ["Cédula de Ciudadanía", "Cédula de Extranjería", "NIT", "Pasaporte"],
        "working_days_month": 30,
        "weekly_hours": 48,
        "vacation_days_per_year": 15,
        "probation_days": 60,
        "christmas_bonus": True,
        "christmas_bonus_name": "Prima de Servicios",
        "social_security": {
            "system_name": "Sistema General de Seguridad Social",
            "employee_deductions": [
                {"code": "SALUD", "name": "Salud (EPS)", "rate": 0.04, "cap_monthly": None},
                {"code": "PENSION", "name": "Pensión", "rate": 0.04, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "SALUD_EMP", "name": "Salud Empleador", "rate": 0.085, "cap_monthly": None},
                {"code": "PENSION_EMP", "name": "Pensión Empleador", "rate": 0.12, "cap_monthly": None},
                {"code": "ARL", "name": "Riesgos Laborales (ARL)", "rate": 0.00522, "cap_monthly": None},
                {"code": "CCF", "name": "Caja Compensación", "rate": 0.04, "cap_monthly": None},
                {"code": "ICBF", "name": "ICBF", "rate": 0.03, "cap_monthly": None},
                {"code": "SENA", "name": "SENA", "rate": 0.02, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Retención en la Fuente",
            "agency": "DIAN",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 52456800, "rate": 0, "fixed": 0},
                {"min": 52456800, "max": 83588400, "rate": 0.19, "fixed": 0},
                {"min": 83588400, "max": 194806800, "rate": 0.28, "fixed": 5914944},
                {"min": 194806800, "max": 388413600, "rate": 0.33, "fixed": 37056096},
                {"min": 388413600, "max": None, "rate": 0.35, "fixed": 100946340}
            ]
        },
        "severance": {
            "preaviso_rules": [
                {"min_months": 0, "max_months": None, "days": 15}
            ],
            "cesantia_formula": "CO_CST"
        },
        "reports": ["DIAN_210", "PILA", "PLANILLA_SOI"],
        "contract_types": ["indefinido", "fijo", "obra_labor", "prestacion_servicios"],
        "permission_types": [
            {"code": "personal", "name": "Personal", "days": "1-3"},
            {"code": "medico", "name": "Incapacidad Médica", "days": "Según EPS"},
            {"code": "duelo", "name": "Luto", "days": "5"},
            {"code": "matrimonio", "name": "Matrimonio", "days": "5"},
            {"code": "paternidad", "name": "Licencia Paternidad", "days": "14"},
            {"code": "maternidad", "name": "Licencia Maternidad", "days": "126"},
            {"code": "otro", "name": "Otro", "days": "Variable"}
        ]
    },
    "MX": {
        "code": "MX",
        "name": "México",
        "currency": "MXN",
        "currency_symbol": "$",
        "currency_name": "Peso Mexicano",
        "locale": "es-MX",
        "document_types": ["CURP", "RFC", "INE", "Pasaporte"],
        "working_days_month": 30,
        "weekly_hours": 48,
        "vacation_days_per_year": 12,
        "probation_days": 30,
        "christmas_bonus": True,
        "christmas_bonus_name": "Aguinaldo (15 días mínimo)",
        "social_security": {
            "system_name": "IMSS (Instituto Mexicano del Seguro Social)",
            "employee_deductions": [
                {"code": "IMSS_ENF", "name": "IMSS Enfermedad y Maternidad", "rate": 0.00375, "cap_monthly": None},
                {"code": "IMSS_INV", "name": "IMSS Invalidez y Vida", "rate": 0.00625, "cap_monthly": None},
                {"code": "IMSS_CES", "name": "IMSS Cesantía y Vejez", "rate": 0.01125, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "IMSS_EMP", "name": "IMSS Empleador", "rate": 0.13903, "cap_monthly": None},
                {"code": "SAR", "name": "SAR (Retiro)", "rate": 0.02, "cap_monthly": None},
                {"code": "INFONAVIT", "name": "INFONAVIT", "rate": 0.05, "cap_monthly": None},
                {"code": "ISN", "name": "Impuesto Sobre Nómina", "rate": 0.03, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISR (Impuesto Sobre la Renta)",
            "agency": "SAT",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 8952.49, "rate": 0.0192, "fixed": 0},
                {"min": 8952.50, "max": 75984.55, "rate": 0.064, "fixed": 171.88},
                {"min": 75984.56, "max": 133536.07, "rate": 0.1088, "fixed": 4461.94},
                {"min": 133536.08, "max": 155229.80, "rate": 0.16, "fixed": 10723.55},
                {"min": 155229.81, "max": 185852.57, "rate": 0.1792, "fixed": 14194.54},
                {"min": 185852.58, "max": 374837.88, "rate": 0.2136, "fixed": 19682.13},
                {"min": 374837.89, "max": None, "rate": 0.35, "fixed": 60049.40}
            ]
        },
        "severance": {
            "preaviso_rules": [
                {"min_months": 0, "max_months": None, "days": 0}
            ],
            "cesantia_formula": "MX_LFT"
        },
        "reports": ["SAT_CFDI", "IMSS_SUA", "INFONAVIT"],
        "contract_types": ["indefinido", "temporal", "capacitacion", "periodo_prueba"],
        "permission_types": [
            {"code": "personal", "name": "Personal", "days": "1-3"},
            {"code": "medico", "name": "Incapacidad", "days": "Según IMSS"},
            {"code": "duelo", "name": "Fallecimiento familiar", "days": "3"},
            {"code": "matrimonio", "name": "Matrimonio", "days": "5"},
            {"code": "paternidad", "name": "Paternidad", "days": "5"},
            {"code": "maternidad", "name": "Maternidad", "days": "84"},
            {"code": "otro", "name": "Otro", "days": "Variable"}
        ]
    },
    "PA": {
        "code": "PA",
        "name": "Panamá",
        "currency": "PAB",
        "currency_symbol": "B/.",
        "currency_name": "Balboa",
        "locale": "es-PA",
        "document_types": ["Cédula", "Pasaporte", "RUC"],
        "working_days_month": 26,
        "weekly_hours": 48,
        "vacation_days_per_year": 30,
        "probation_days": 90,
        "christmas_bonus": True,
        "christmas_bonus_name": "Décimo Tercer Mes",
        "social_security": {
            "system_name": "CSS (Caja de Seguro Social)",
            "employee_deductions": [
                {"code": "CSS", "name": "Seguro Social (CSS)", "rate": 0.0975, "cap_monthly": None},
                {"code": "SE", "name": "Seguro Educativo", "rate": 0.0125, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "CSS_EMP", "name": "CSS Empleador", "rate": 0.1275, "cap_monthly": None},
                {"code": "SE_EMP", "name": "Seguro Educativo Empleador", "rate": 0.015, "cap_monthly": None},
                {"code": "RP", "name": "Riesgos Profesionales", "rate": 0.0198, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISR (Impuesto Sobre la Renta)",
            "agency": "DGI",
            "exempt_monthly": 916.67,
            "brackets": [
                {"min": 0, "max": 11000, "rate": 0, "fixed": 0},
                {"min": 11000.01, "max": 50000, "rate": 0.15, "fixed": 0},
                {"min": 50000.01, "max": None, "rate": 0.25, "fixed": 5850}
            ]
        },
        "severance": {
            "preaviso_rules": [
                {"min_months": 0, "max_months": 24, "days": 30},
                {"min_months": 24, "max_months": None, "days": 90}
            ],
            "cesantia_formula": "PA_CT"
        },
        "reports": ["DGI_03", "CSS_PLANILLA"],
        "contract_types": ["indefinido", "definido", "obra"],
        "permission_types": [
            {"code": "personal", "name": "Personal", "days": "1-3"},
            {"code": "medico", "name": "Médico", "days": "Según CSS"},
            {"code": "duelo", "name": "Duelo", "days": "3"},
            {"code": "matrimonio", "name": "Matrimonio", "days": "5"},
            {"code": "paternidad", "name": "Paternidad", "days": "3"},
            {"code": "maternidad", "name": "Maternidad", "days": "98"},
            {"code": "otro", "name": "Otro", "days": "Variable"}
        ]
    }
}

SUPPORTED_COUNTRIES = list(COUNTRY_PROFILES.keys())


# ===================== ENDPOINTS =====================

@router.get("/countries")
async def get_supported_countries():
    """Get list of supported countries with basic info"""
    countries = []
    for code, profile in COUNTRY_PROFILES.items():
        countries.append({
            "code": code,
            "name": profile["name"],
            "currency": profile["currency"],
            "currency_symbol": profile["currency_symbol"],
            "currency_name": profile["currency_name"]
        })
    return {"countries": countries}


@router.get("/countries/{country_code}")
async def get_country_profile(country_code: str):
    """Get full country configuration profile"""
    profile = COUNTRY_PROFILES.get(country_code.upper())
    if not profile:
        raise HTTPException(status_code=404, detail=f"País no soportado: {country_code}")
    return profile


@router.get("/company")
async def get_company_country_config(current_user: dict = Depends(get_current_user)):
    """Get the country config for the current company"""
    company_id = current_user.get("company_id")

    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "country": 1, "currency": 1, "company_name": 1, "name": 1}
    )

    country_code = (company or {}).get("country", "DO")  # Default to DR
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["DO"])

    # Check for company-specific overrides
    overrides = await db.country_config_overrides.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )

    return {
        "country_code": country_code,
        "profile": profile,
        "overrides": overrides,
        "company_name": (company or {}).get("company_name", (company or {}).get("name", ""))
    }


@router.put("/company/country")
async def set_company_country(country_code: str, current_user: dict = Depends(get_current_user)):
    """Set the country for a company"""
    company_id = current_user.get("company_id")

    country_code = country_code.upper()
    if country_code not in COUNTRY_PROFILES:
        raise HTTPException(status_code=400, detail=f"País no soportado: {country_code}")

    profile = COUNTRY_PROFILES[country_code]

    await db.companies.update_one(
        {"company_id": company_id},
        {"$set": {
            "country": country_code,
            "currency": profile["currency"],
            "currency_symbol": profile["currency_symbol"],
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    return {"success": True, "message": f"País configurado: {profile['name']}"}


# ===================== PAYROLL RATES HELPER =====================

async def get_payroll_rates(company_id: str) -> dict:
    """
    Get the payroll calculation rates for a company based on its country.
    Returns a dict with employee deductions, employer contributions, and ISR config.
    This is the CORE function that makes payroll multi-country.
    """
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "country": 1}
    )

    country_code = (company or {}).get("country", "DO")
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["DO"])

    # Build rates dict
    employee_rates = {}
    for ded in profile["social_security"]["employee_deductions"]:
        employee_rates[ded["code"]] = {
            "name": ded["name"],
            "rate": ded["rate"],
            "cap": ded.get("cap_monthly")
        }

    employer_rates = {}
    for cont in profile["social_security"]["employer_contributions"]:
        employer_rates[cont["code"]] = {
            "name": cont["name"],
            "rate": cont["rate"],
            "cap": cont.get("cap_monthly")
        }

    return {
        "country_code": country_code,
        "country_name": profile["name"],
        "currency": profile["currency"],
        "currency_symbol": profile["currency_symbol"],
        "working_days_month": profile["working_days_month"],
        "employee_deductions": employee_rates,
        "employer_contributions": employer_rates,
        "income_tax": profile["income_tax"],
        "social_security_name": profile["social_security"]["system_name"]
    }


# ===================== MIGRATION =====================

async def migrate_existing_companies():
    """Migrate existing companies without proper country code to DO"""
    # Fix companies with full country names
    name_mappings = {
        "República Dominicana": "DO", "Dominican Republic": "DO",
        "Colombia": "CO", "México": "MX", "Mexico": "MX",
        "Panamá": "PA", "Panama": "PA"
    }
    for name, code in name_mappings.items():
        from routes.country_config import COUNTRY_PROFILES
        profile = COUNTRY_PROFILES.get(code, COUNTRY_PROFILES["DO"])
        await db.companies.update_many(
            {"country": name},
            {"$set": {"country": code, "currency": profile["currency"], "currency_symbol": profile["currency_symbol"]}}
        )

    # Migrate companies without country
    result = await db.companies.update_many(
        {"$or": [{"country": {"$exists": False}}, {"country": None}, {"country": ""}]},
        {"$set": {"country": "DO", "currency": "DOP", "currency_symbol": "RD$"}}
    )
    if result.modified_count > 0:
        print(f"[Country Migration] {result.modified_count} companies migrated to DO")
    return result.modified_count

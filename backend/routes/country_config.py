"""
Country Configuration - Multi-country payroll engine
Stores tax rates, social security, ISR scales, currencies, document types per country.
Organized by region. Existing DR companies are auto-migrated.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/country-config", tags=["Country Config"])

# ===================== REGIONS =====================
REGIONS = {
    "north_america": {"name": "América del Norte", "name_en": "North America"},
    "central_america": {"name": "América Central", "name_en": "Central America"},
    "caribbean": {"name": "Caribe", "name_en": "Caribbean"},
    "south_america": {"name": "América del Sur", "name_en": "South America"},
    "europe": {"name": "Europa", "name_en": "Europe"},
}

def _base_permissions():
    return [
        {"code": "personal", "name": "Personal", "days": "1-3"},
        {"code": "medico", "name": "Médico", "days": "Variable"},
        {"code": "duelo", "name": "Duelo", "days": "3"},
        {"code": "matrimonio", "name": "Matrimonio", "days": "5"},
        {"code": "paternidad", "name": "Paternidad", "days": "Variable"},
        {"code": "maternidad", "name": "Maternidad", "days": "Variable"},
        {"code": "otro", "name": "Otro", "days": "Variable"},
    ]

# ===================== COUNTRY PROFILES =====================
COUNTRY_PROFILES = {
    # ==================== CARIBE ====================
    "DO": {
        "code": "DO", "region": "caribbean",
        "name": "República Dominicana", "flag": "🇩🇴",
        "currency": "DOP", "currency_symbol": "RD$", "currency_name": "Peso Dominicano",
        "locale": "es-DO",
        "document_types": ["Cédula", "Pasaporte", "RNC"],
        "working_days_month": 23.83, "weekly_hours": 44,
        "vacation_days_per_year": 14, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Regalía Pascual (Salario 13)",
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
            "name": "ISR (Impuesto Sobre la Renta)", "agency": "DGII",
            "exempt_monthly": 34685.00,
            "brackets": [
                {"min": 0, "max": 416220, "rate": 0, "fixed": 0},
                {"min": 416220.01, "max": 624329, "rate": 0.15, "fixed": 0},
                {"min": 624329.01, "max": 867123, "rate": 0.20, "fixed": 31216},
                {"min": 867123.01, "max": None, "rate": 0.25, "fixed": 79776}
            ]
        },
        "severance": {"cesantia_formula": "DR_ART80"},
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
    "CU": {
        "code": "CU", "region": "caribbean",
        "name": "Cuba", "flag": "🇨🇺",
        "currency": "CUP", "currency_symbol": "$", "currency_name": "Peso Cubano",
        "locale": "es-CU",
        "document_types": ["Carné de Identidad", "Pasaporte"],
        "working_days_month": 24, "weekly_hours": 44,
        "vacation_days_per_year": 30, "probation_days": 90,
        "christmas_bonus": False, "christmas_bonus_name": "",
        "social_security": {
            "system_name": "Seguridad Social Estatal",
            "employee_deductions": [
                {"code": "CSS", "name": "Contribución Seguridad Social", "rate": 0.05, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "CSS_EMP", "name": "Seguridad Social Empleador", "rate": 0.125, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Impuesto sobre Ingresos Personales", "agency": "ONAT",
            "exempt_monthly": 0,
            "brackets": [{"min": 0, "max": None, "rate": 0, "fixed": 0}]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": [], "contract_types": ["indefinido", "temporal"],
        "permission_types": _base_permissions()
    },
    "HT": {
        "code": "HT", "region": "caribbean",
        "name": "Haití", "flag": "🇭🇹",
        "currency": "HTG", "currency_symbol": "G", "currency_name": "Gourde",
        "locale": "fr-HT",
        "document_types": ["CIN (Carte d'Identité)", "Passeport"],
        "working_days_month": 26, "weekly_hours": 48,
        "vacation_days_per_year": 15, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Boni de Fin d'Année",
        "social_security": {
            "system_name": "ONA / OFATMA",
            "employee_deductions": [
                {"code": "ONA", "name": "ONA (Assurance Vieillesse)", "rate": 0.06, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "ONA_EMP", "name": "ONA Empleador", "rate": 0.06, "cap_monthly": None},
                {"code": "OFATMA", "name": "OFATMA (Accidents)", "rate": 0.03, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "IRI (Impôt sur le Revenu)", "agency": "DGI",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 120000, "rate": 0, "fixed": 0},
                {"min": 120000.01, "max": 240000, "rate": 0.10, "fixed": 0},
                {"min": 240000.01, "max": 480000, "rate": 0.15, "fixed": 12000},
                {"min": 480000.01, "max": None, "rate": 0.30, "fixed": 48000}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": [], "contract_types": ["indefinido", "temporal", "obra"],
        "permission_types": _base_permissions()
    },

    # ==================== AMÉRICA CENTRAL ====================
    "CR": {
        "code": "CR", "region": "central_america",
        "name": "Costa Rica", "flag": "🇨🇷",
        "currency": "CRC", "currency_symbol": "₡", "currency_name": "Colón",
        "locale": "es-CR",
        "document_types": ["Cédula", "DIMEX", "Pasaporte"],
        "working_days_month": 26, "weekly_hours": 48,
        "vacation_days_per_year": 14, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo",
        "social_security": {
            "system_name": "CCSS (Caja Costarricense de Seguro Social)",
            "employee_deductions": [
                {"code": "SEM", "name": "Seguro Enfermedad y Maternidad", "rate": 0.055, "cap_monthly": None},
                {"code": "IVM", "name": "Invalidez, Vejez y Muerte", "rate": 0.0417, "cap_monthly": None},
                {"code": "BPC", "name": "Banco Popular", "rate": 0.01, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "SEM_EMP", "name": "SEM Empleador", "rate": 0.0934, "cap_monthly": None},
                {"code": "IVM_EMP", "name": "IVM Empleador", "rate": 0.0542, "cap_monthly": None},
                {"code": "FODESAF", "name": "FODESAF", "rate": 0.05, "cap_monthly": None},
                {"code": "IMAS", "name": "IMAS", "rate": 0.05, "cap_monthly": None},
                {"code": "INA", "name": "INA", "rate": 0.015, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Impuesto sobre la Renta", "agency": "DGT",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 11580000, "rate": 0, "fixed": 0},
                {"min": 11580000, "max": 17220000, "rate": 0.10, "fixed": 0},
                {"min": 17220000, "max": None, "rate": 0.15, "fixed": 564000}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": ["CCSS_PLANILLA"], "contract_types": ["indefinido", "temporal", "obra"],
        "permission_types": _base_permissions()
    },
    "SV": {
        "code": "SV", "region": "central_america",
        "name": "El Salvador", "flag": "🇸🇻",
        "currency": "USD", "currency_symbol": "$", "currency_name": "Dólar US",
        "locale": "es-SV",
        "document_types": ["DUI", "NIT", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 44,
        "vacation_days_per_year": 15, "probation_days": 30,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo",
        "social_security": {
            "system_name": "ISSS / AFP",
            "employee_deductions": [
                {"code": "ISSS", "name": "ISSS (Salud)", "rate": 0.03, "cap_monthly": 30},
                {"code": "AFP_SV", "name": "AFP (Pensión)", "rate": 0.0725, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "ISSS_EMP", "name": "ISSS Empleador", "rate": 0.075, "cap_monthly": 75},
                {"code": "AFP_SV_EMP", "name": "AFP Empleador", "rate": 0.0875, "cap_monthly": None},
                {"code": "INSAFORP", "name": "INSAFORP", "rate": 0.01, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISR", "agency": "DGII",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 4064, "rate": 0, "fixed": 0},
                {"min": 4064.01, "max": 9142.86, "rate": 0.10, "fixed": 0},
                {"min": 9142.87, "max": 22857.14, "rate": 0.20, "fixed": 507.89},
                {"min": 22857.15, "max": None, "rate": 0.30, "fixed": 3250.74}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": [], "contract_types": ["indefinido", "temporal"],
        "permission_types": _base_permissions()
    },
    "GT": {
        "code": "GT", "region": "central_america",
        "name": "Guatemala", "flag": "🇬🇹",
        "currency": "GTQ", "currency_symbol": "Q", "currency_name": "Quetzal",
        "locale": "es-GT",
        "document_types": ["DPI", "NIT", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 48,
        "vacation_days_per_year": 15, "probation_days": 60,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo + Bono 14",
        "social_security": {
            "system_name": "IGSS",
            "employee_deductions": [
                {"code": "IGSS", "name": "IGSS", "rate": 0.0483, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "IGSS_EMP", "name": "IGSS Empleador", "rate": 0.1267, "cap_monthly": None},
                {"code": "IRTRA", "name": "IRTRA", "rate": 0.01, "cap_monthly": None},
                {"code": "INTECAP", "name": "INTECAP", "rate": 0.01, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISR", "agency": "SAT",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 300000, "rate": 0.05, "fixed": 0},
                {"min": 300000.01, "max": None, "rate": 0.07, "fixed": 15000}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": ["SAT_ISR"], "contract_types": ["indefinido", "temporal", "obra"],
        "permission_types": _base_permissions()
    },
    "HN": {
        "code": "HN", "region": "central_america",
        "name": "Honduras", "flag": "🇭🇳",
        "currency": "HNL", "currency_symbol": "L", "currency_name": "Lempira",
        "locale": "es-HN",
        "document_types": ["Identidad", "RTN", "Pasaporte"],
        "working_days_month": 26, "weekly_hours": 44,
        "vacation_days_per_year": 10, "probation_days": 60,
        "christmas_bonus": True, "christmas_bonus_name": "Décimo Tercer Mes + Décimo Cuarto Mes",
        "social_security": {
            "system_name": "IHSS",
            "employee_deductions": [
                {"code": "IHSS_EM", "name": "IHSS Enfermedad/Maternidad", "rate": 0.025, "cap_monthly": None},
                {"code": "IHSS_IVM", "name": "IHSS Invalidez/Vejez", "rate": 0.025, "cap_monthly": None},
                {"code": "RAP", "name": "RAP (Vivienda)", "rate": 0.015, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "IHSS_EMP", "name": "IHSS Empleador", "rate": 0.05, "cap_monthly": None},
                {"code": "IHSS_IVM_EMP", "name": "IHSS IVM Empleador", "rate": 0.035, "cap_monthly": None},
                {"code": "RAP_EMP", "name": "RAP Empleador", "rate": 0.015, "cap_monthly": None},
                {"code": "INFOP", "name": "INFOP", "rate": 0.01, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISR", "agency": "SAR",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 172605.30, "rate": 0, "fixed": 0},
                {"min": 172605.31, "max": 263236.36, "rate": 0.15, "fixed": 0},
                {"min": 263236.37, "max": 611683.72, "rate": 0.20, "fixed": 13594.66},
                {"min": 611683.73, "max": None, "rate": 0.25, "fixed": 83284.13}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": [], "contract_types": ["indefinido", "temporal"],
        "permission_types": _base_permissions()
    },
    "NI": {
        "code": "NI", "region": "central_america",
        "name": "Nicaragua", "flag": "🇳🇮",
        "currency": "NIO", "currency_symbol": "C$", "currency_name": "Córdoba",
        "locale": "es-NI",
        "document_types": ["Cédula", "RUC", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 48,
        "vacation_days_per_year": 15, "probation_days": 30,
        "christmas_bonus": True, "christmas_bonus_name": "Décimo Tercer Mes",
        "social_security": {
            "system_name": "INSS",
            "employee_deductions": [
                {"code": "INSS", "name": "INSS", "rate": 0.07, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "INSS_EMP", "name": "INSS Empleador", "rate": 0.225, "cap_monthly": None},
                {"code": "INATEC", "name": "INATEC", "rate": 0.02, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "IR", "agency": "DGI",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 100000, "rate": 0, "fixed": 0},
                {"min": 100000.01, "max": 200000, "rate": 0.15, "fixed": 0},
                {"min": 200000.01, "max": 350000, "rate": 0.20, "fixed": 15000},
                {"min": 350000.01, "max": 500000, "rate": 0.25, "fixed": 45000},
                {"min": 500000.01, "max": None, "rate": 0.30, "fixed": 82500}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": [], "contract_types": ["indefinido", "temporal"],
        "permission_types": _base_permissions()
    },
    "PA": {
        "code": "PA", "region": "central_america",
        "name": "Panamá", "flag": "🇵🇦",
        "currency": "PAB", "currency_symbol": "B/.", "currency_name": "Balboa",
        "locale": "es-PA",
        "document_types": ["Cédula", "Pasaporte", "RUC"],
        "working_days_month": 26, "weekly_hours": 48,
        "vacation_days_per_year": 30, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Décimo Tercer Mes",
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
            "name": "ISR", "agency": "DGI",
            "exempt_monthly": 916.67,
            "brackets": [
                {"min": 0, "max": 11000, "rate": 0, "fixed": 0},
                {"min": 11000.01, "max": 50000, "rate": 0.15, "fixed": 0},
                {"min": 50000.01, "max": None, "rate": 0.25, "fixed": 5850}
            ]
        },
        "severance": {"cesantia_formula": "PA_CT"},
        "reports": ["DGI_03", "CSS_PLANILLA"], "contract_types": ["indefinido", "definido", "obra"],
        "permission_types": _base_permissions()
    },

    # ==================== AMÉRICA DEL NORTE ====================
    "MX": {
        "code": "MX", "region": "north_america",
        "name": "México", "flag": "🇲🇽",
        "currency": "MXN", "currency_symbol": "$", "currency_name": "Peso Mexicano",
        "locale": "es-MX",
        "document_types": ["CURP", "RFC", "INE", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 48,
        "vacation_days_per_year": 12, "probation_days": 30,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo (15 días mínimo)",
        "social_security": {
            "system_name": "IMSS",
            "employee_deductions": [
                {"code": "IMSS", "name": "IMSS Empleado", "rate": 0.02125, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "IMSS_EMP", "name": "IMSS Empleador", "rate": 0.13903, "cap_monthly": None},
                {"code": "SAR", "name": "SAR (Retiro)", "rate": 0.02, "cap_monthly": None},
                {"code": "INFONAVIT", "name": "INFONAVIT", "rate": 0.05, "cap_monthly": None},
                {"code": "ISN", "name": "Impuesto Sobre Nómina", "rate": 0.03, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISR", "agency": "SAT",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 8952.49, "rate": 0.0192, "fixed": 0},
                {"min": 8952.50, "max": 75984.55, "rate": 0.064, "fixed": 171.88},
                {"min": 75984.56, "max": 133536.07, "rate": 0.1088, "fixed": 4461.94},
                {"min": 133536.08, "max": 155229.80, "rate": 0.16, "fixed": 10723.55},
                {"min": 155229.81, "max": 185852.57, "rate": 0.1792, "fixed": 14194.54},
                {"min": 185852.58, "max": None, "rate": 0.35, "fixed": 60049.40}
            ]
        },
        "severance": {"cesantia_formula": "MX_LFT"},
        "reports": ["SAT_CFDI", "IMSS_SUA", "INFONAVIT"],
        "contract_types": ["indefinido", "temporal", "capacitacion", "periodo_prueba"],
        "permission_types": _base_permissions()
    },
    "US": {
        "code": "US", "region": "north_america",
        "name": "Estados Unidos", "flag": "🇺🇸",
        "currency": "USD", "currency_symbol": "$", "currency_name": "US Dollar",
        "locale": "en-US",
        "document_types": ["SSN", "EIN", "Passport", "Driver License"],
        "working_days_month": 22, "weekly_hours": 40,
        "vacation_days_per_year": 10, "probation_days": 90,
        "christmas_bonus": False, "christmas_bonus_name": "",
        "social_security": {
            "system_name": "FICA (Social Security + Medicare)",
            "employee_deductions": [
                {"code": "SS", "name": "Social Security", "rate": 0.062, "cap_monthly": 13350},
                {"code": "MEDICARE", "name": "Medicare", "rate": 0.0145, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "SS_EMP", "name": "Social Security Employer", "rate": 0.062, "cap_monthly": 13350},
                {"code": "MEDICARE_EMP", "name": "Medicare Employer", "rate": 0.0145, "cap_monthly": None},
                {"code": "FUTA", "name": "FUTA (Unemployment)", "rate": 0.006, "cap_monthly": 583.33}
            ]
        },
        "income_tax": {
            "name": "Federal Income Tax", "agency": "IRS",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 11600, "rate": 0.10, "fixed": 0},
                {"min": 11600.01, "max": 47150, "rate": 0.12, "fixed": 1160},
                {"min": 47150.01, "max": 100525, "rate": 0.22, "fixed": 5426},
                {"min": 100525.01, "max": 191950, "rate": 0.24, "fixed": 17168.50},
                {"min": 191950.01, "max": None, "rate": 0.32, "fixed": 39110.50}
            ]
        },
        "severance": {"cesantia_formula": "US_ATWILL"},
        "reports": ["W2", "941", "1099"],
        "contract_types": ["at_will", "fixed_term", "contractor"],
        "permission_types": _base_permissions()
    },
    "CA": {
        "code": "CA", "region": "north_america",
        "name": "Canadá", "flag": "🇨🇦",
        "currency": "CAD", "currency_symbol": "C$", "currency_name": "Canadian Dollar",
        "locale": "en-CA",
        "document_types": ["SIN", "Passport", "Driver License"],
        "working_days_month": 22, "weekly_hours": 40,
        "vacation_days_per_year": 10, "probation_days": 90,
        "christmas_bonus": False, "christmas_bonus_name": "",
        "social_security": {
            "system_name": "CPP / EI",
            "employee_deductions": [
                {"code": "CPP", "name": "Canada Pension Plan", "rate": 0.0595, "cap_monthly": None},
                {"code": "EI", "name": "Employment Insurance", "rate": 0.0166, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "CPP_EMP", "name": "CPP Employer", "rate": 0.0595, "cap_monthly": None},
                {"code": "EI_EMP", "name": "EI Employer (1.4x)", "rate": 0.02324, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Federal Income Tax", "agency": "CRA",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 55867, "rate": 0.15, "fixed": 0},
                {"min": 55867.01, "max": 111733, "rate": 0.205, "fixed": 8380.05},
                {"min": 111733.01, "max": 154906, "rate": 0.26, "fixed": 19832.58},
                {"min": 154906.01, "max": None, "rate": 0.29, "fixed": 31057.56}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": ["T4", "ROE"],
        "contract_types": ["indefinite", "fixed_term", "contractor"],
        "permission_types": _base_permissions()
    },
    "PR": {
        "code": "PR", "region": "north_america",
        "name": "Puerto Rico", "flag": "🇵🇷",
        "currency": "USD", "currency_symbol": "$", "currency_name": "US Dollar",
        "locale": "es-PR",
        "document_types": ["SSN", "Licencia", "Pasaporte"],
        "working_days_month": 22, "weekly_hours": 40,
        "vacation_days_per_year": 15, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Bono de Navidad",
        "social_security": {
            "system_name": "FICA + SINOT / CFSE",
            "employee_deductions": [
                {"code": "SS", "name": "Social Security", "rate": 0.062, "cap_monthly": None},
                {"code": "MEDICARE", "name": "Medicare", "rate": 0.0145, "cap_monthly": None},
                {"code": "SINOT", "name": "SINOT (Choferil)", "rate": 0.003, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "SS_EMP", "name": "Social Security Employer", "rate": 0.062, "cap_monthly": None},
                {"code": "MEDICARE_EMP", "name": "Medicare Employer", "rate": 0.0145, "cap_monthly": None},
                {"code": "FUTA_PR", "name": "FUTA", "rate": 0.006, "cap_monthly": None},
                {"code": "CFSE", "name": "CFSE (Workers Comp)", "rate": 0.03, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Contribución sobre Ingresos", "agency": "Hacienda PR",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 9000, "rate": 0, "fixed": 0},
                {"min": 9000.01, "max": 25000, "rate": 0.07, "fixed": 0},
                {"min": 25000.01, "max": 50000, "rate": 0.14, "fixed": 1120},
                {"min": 50000.01, "max": None, "rate": 0.25, "fixed": 4620}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": ["W2_PR", "499R"],
        "contract_types": ["indefinido", "temporal", "probatorio"],
        "permission_types": _base_permissions()
    },

    # ==================== AMÉRICA DEL SUR ====================
    "CO": {
        "code": "CO", "region": "south_america",
        "name": "Colombia", "flag": "🇨🇴",
        "currency": "COP", "currency_symbol": "$", "currency_name": "Peso Colombiano",
        "locale": "es-CO",
        "document_types": ["Cédula de Ciudadanía", "Cédula de Extranjería", "NIT", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 48,
        "vacation_days_per_year": 15, "probation_days": 60,
        "christmas_bonus": True, "christmas_bonus_name": "Prima de Servicios",
        "social_security": {
            "system_name": "Sistema General de Seguridad Social",
            "employee_deductions": [
                {"code": "SALUD", "name": "Salud (EPS)", "rate": 0.04, "cap_monthly": None},
                {"code": "PENSION", "name": "Pensión", "rate": 0.04, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "SALUD_EMP", "name": "Salud Empleador", "rate": 0.085, "cap_monthly": None},
                {"code": "PENSION_EMP", "name": "Pensión Empleador", "rate": 0.12, "cap_monthly": None},
                {"code": "ARL", "name": "Riesgos Laborales", "rate": 0.00522, "cap_monthly": None},
                {"code": "CCF", "name": "Caja Compensación", "rate": 0.04, "cap_monthly": None},
                {"code": "ICBF", "name": "ICBF", "rate": 0.03, "cap_monthly": None},
                {"code": "SENA", "name": "SENA", "rate": 0.02, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Retención en la Fuente", "agency": "DIAN",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 52456800, "rate": 0, "fixed": 0},
                {"min": 52456800, "max": 83588400, "rate": 0.19, "fixed": 0},
                {"min": 83588400, "max": None, "rate": 0.28, "fixed": 5914944}
            ]
        },
        "severance": {"cesantia_formula": "CO_CST"},
        "reports": ["DIAN_210", "PILA"], "contract_types": ["indefinido", "fijo", "obra_labor", "prestacion_servicios"],
        "permission_types": _base_permissions()
    },
    "AR": {
        "code": "AR", "region": "south_america",
        "name": "Argentina", "flag": "🇦🇷",
        "currency": "ARS", "currency_symbol": "$", "currency_name": "Peso Argentino",
        "locale": "es-AR",
        "document_types": ["DNI", "CUIL", "CUIT", "Pasaporte"],
        "working_days_month": 25, "weekly_hours": 48,
        "vacation_days_per_year": 14, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "SAC (Sueldo Anual Complementario)",
        "social_security": {
            "system_name": "SUSS (Sistema Único de Seguridad Social)",
            "employee_deductions": [
                {"code": "JUB", "name": "Jubilación", "rate": 0.11, "cap_monthly": None},
                {"code": "INSSJP", "name": "INSSJP (PAMI)", "rate": 0.03, "cap_monthly": None},
                {"code": "OS", "name": "Obra Social", "rate": 0.03, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "JUB_EMP", "name": "Jubilación Empleador", "rate": 0.108, "cap_monthly": None},
                {"code": "INSSJP_EMP", "name": "INSSJP Empleador", "rate": 0.02, "cap_monthly": None},
                {"code": "OS_EMP", "name": "Obra Social Empleador", "rate": 0.06, "cap_monthly": None},
                {"code": "AF", "name": "Asig. Familiares", "rate": 0.044, "cap_monthly": None},
                {"code": "FNE", "name": "Fondo Nac. Empleo", "rate": 0.0089, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Ganancias (4ta Categoría)", "agency": "AFIP",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 2040000, "rate": 0.05, "fixed": 0},
                {"min": 2040000, "max": 4080000, "rate": 0.09, "fixed": 102000},
                {"min": 4080000, "max": 6120000, "rate": 0.12, "fixed": 285600},
                {"min": 6120000, "max": None, "rate": 0.15, "fixed": 530400}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": ["F931", "LIBRO_SUELDOS"], "contract_types": ["indefinido", "plazo_fijo", "eventual"],
        "permission_types": _base_permissions()
    },
    "CL": {
        "code": "CL", "region": "south_america",
        "name": "Chile", "flag": "🇨🇱",
        "currency": "CLP", "currency_symbol": "$", "currency_name": "Peso Chileno",
        "locale": "es-CL",
        "document_types": ["RUT", "Cédula de Identidad", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 45,
        "vacation_days_per_year": 15, "probation_days": 0,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo (voluntario)",
        "social_security": {
            "system_name": "AFP + Fonasa/Isapre",
            "employee_deductions": [
                {"code": "AFP_CL", "name": "AFP (Pensión)", "rate": 0.1244, "cap_monthly": None},
                {"code": "SALUD_CL", "name": "Salud (Fonasa/Isapre)", "rate": 0.07, "cap_monthly": None},
                {"code": "CESANTIA_CL", "name": "Seguro Cesantía", "rate": 0.006, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "CESANTIA_CL_EMP", "name": "Seguro Cesantía Empleador", "rate": 0.024, "cap_monthly": None},
                {"code": "MUTUAL", "name": "Mutual de Seguridad", "rate": 0.0093, "cap_monthly": None},
                {"code": "SIS", "name": "Seguro Invalidez/Sobrevivencia", "rate": 0.0141, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Impuesto Único 2da Categoría", "agency": "SII",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 8412060, "rate": 0, "fixed": 0},
                {"min": 8412060, "max": 18693468, "rate": 0.04, "fixed": 0},
                {"min": 18693468, "max": 31155780, "rate": 0.08, "fixed": 0},
                {"min": 31155780, "max": None, "rate": 0.135, "fixed": 0}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": ["SII_DJ", "PREVIRED"], "contract_types": ["indefinido", "plazo_fijo", "obra"],
        "permission_types": _base_permissions()
    },
    "PE": {
        "code": "PE", "region": "south_america",
        "name": "Perú", "flag": "🇵🇪",
        "currency": "PEN", "currency_symbol": "S/", "currency_name": "Sol",
        "locale": "es-PE",
        "document_types": ["DNI", "RUC", "CE", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 48,
        "vacation_days_per_year": 30, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Gratificación (Jul + Dic)",
        "social_security": {
            "system_name": "EsSalud / AFP/ONP",
            "employee_deductions": [
                {"code": "ONP_AFP", "name": "ONP o AFP (Pensión)", "rate": 0.13, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "ESSALUD", "name": "EsSalud", "rate": 0.09, "cap_monthly": None},
                {"code": "SCTR", "name": "SCTR (Riesgos)", "rate": 0.01, "cap_monthly": None},
                {"code": "SENATI", "name": "SENATI", "rate": 0.0075, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Impuesto a la Renta 5ta Cat.", "agency": "SUNAT",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 25750, "rate": 0.08, "fixed": 0},
                {"min": 25750, "max": 103000, "rate": 0.14, "fixed": 2060},
                {"min": 103000, "max": 180250, "rate": 0.17, "fixed": 12874},
                {"min": 180250, "max": 231000, "rate": 0.20, "fixed": 26007.50},
                {"min": 231000, "max": None, "rate": 0.30, "fixed": 36157.50}
            ]
        },
        "severance": {"cesantia_formula": "PE_CTS"},
        "reports": ["PDT_PLAME", "T_REGISTRO"], "contract_types": ["indefinido", "plazo_fijo", "parcial"],
        "permission_types": _base_permissions()
    },
    "EC": {
        "code": "EC", "region": "south_america",
        "name": "Ecuador", "flag": "🇪🇨",
        "currency": "USD", "currency_symbol": "$", "currency_name": "Dólar US",
        "locale": "es-EC",
        "document_types": ["Cédula", "RUC", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 40,
        "vacation_days_per_year": 15, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Décimo Tercer Sueldo + Décimo Cuarto Sueldo",
        "social_security": {
            "system_name": "IESS",
            "employee_deductions": [
                {"code": "IESS", "name": "IESS Aporte Personal", "rate": 0.0945, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "IESS_EMP", "name": "IESS Patronal", "rate": 0.1115, "cap_monthly": None},
                {"code": "SECAP", "name": "SECAP", "rate": 0.005, "cap_monthly": None},
                {"code": "IECE", "name": "IECE", "rate": 0.005, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "Impuesto a la Renta", "agency": "SRI",
            "exempt_monthly": 0,
            "brackets": [
                {"min": 0, "max": 11722, "rate": 0, "fixed": 0},
                {"min": 11722, "max": 14930, "rate": 0.05, "fixed": 0},
                {"min": 14930, "max": 19385, "rate": 0.10, "fixed": 160},
                {"min": 19385, "max": 25638, "rate": 0.12, "fixed": 606},
                {"min": 25638, "max": None, "rate": 0.15, "fixed": 1356}
            ]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": ["SRI_RDEP"], "contract_types": ["indefinido", "fijo", "eventual", "obra"],
        "permission_types": _base_permissions()
    },
    "VE": {
        "code": "VE", "region": "south_america",
        "name": "Venezuela", "flag": "🇻🇪",
        "currency": "VES", "currency_symbol": "Bs.", "currency_name": "Bolívar",
        "locale": "es-VE",
        "document_types": ["Cédula V/E", "RIF", "Pasaporte"],
        "working_days_month": 30, "weekly_hours": 40,
        "vacation_days_per_year": 15, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Utilidades + Bono Vacacional",
        "social_security": {
            "system_name": "IVSS / FAOV / INCE",
            "employee_deductions": [
                {"code": "IVSS", "name": "IVSS (Seguro Social)", "rate": 0.04, "cap_monthly": None},
                {"code": "SPF", "name": "Paro Forzoso", "rate": 0.005, "cap_monthly": None},
                {"code": "FAOV", "name": "FAOV (Vivienda)", "rate": 0.01, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "IVSS_EMP", "name": "IVSS Empleador", "rate": 0.11, "cap_monthly": None},
                {"code": "SPF_EMP", "name": "Paro Forzoso Empleador", "rate": 0.02, "cap_monthly": None},
                {"code": "FAOV_EMP", "name": "FAOV Empleador", "rate": 0.02, "cap_monthly": None},
                {"code": "INCE", "name": "INCE", "rate": 0.02, "cap_monthly": None}
            ]
        },
        "income_tax": {
            "name": "ISLR", "agency": "SENIAT",
            "exempt_monthly": 0,
            "brackets": [{"min": 0, "max": None, "rate": 0, "fixed": 0}]
        },
        "severance": {"cesantia_formula": "GENERIC"},
        "reports": [], "contract_types": ["indefinido", "temporal", "obra"],
        "permission_types": _base_permissions()
    },
    "BO": {
        "code": "BO", "region": "south_america", "name": "Bolivia", "flag": "🇧🇴",
        "currency": "BOB", "currency_symbol": "Bs", "currency_name": "Boliviano", "locale": "es-BO",
        "document_types": ["CI", "NIT", "Pasaporte"],
        "working_days_month": 26, "weekly_hours": 48,
        "vacation_days_per_year": 15, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo + Segundo Aguinaldo",
        "social_security": {
            "system_name": "AFP / CNS",
            "employee_deductions": [
                {"code": "AFP_BO", "name": "AFP (Pensión)", "rate": 0.1271, "cap_monthly": None},
                {"code": "RC_IVA", "name": "RC-IVA", "rate": 0.13, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "CNS", "name": "CNS (Salud)", "rate": 0.10, "cap_monthly": None},
                {"code": "PRO_VIVIENDA", "name": "Pro-Vivienda", "rate": 0.02, "cap_monthly": None},
                {"code": "AFP_BO_EMP", "name": "AFP Riesgo Profesional", "rate": 0.017, "cap_monthly": None},
                {"code": "INFOCAL", "name": "INFOCAL", "rate": 0.01, "cap_monthly": None}
            ]
        },
        "income_tax": {"name": "RC-IVA", "agency": "SIN", "exempt_monthly": 0, "brackets": [{"min": 0, "max": None, "rate": 0.13, "fixed": 0}]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": [], "contract_types": ["indefinido", "temporal", "obra"],
        "permission_types": _base_permissions()
    },
    "PY": {
        "code": "PY", "region": "south_america", "name": "Paraguay", "flag": "🇵🇾",
        "currency": "PYG", "currency_symbol": "₲", "currency_name": "Guaraní", "locale": "es-PY",
        "document_types": ["CI", "RUC", "Pasaporte"],
        "working_days_month": 26, "weekly_hours": 48,
        "vacation_days_per_year": 12, "probation_days": 30,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo",
        "social_security": {
            "system_name": "IPS",
            "employee_deductions": [{"code": "IPS", "name": "IPS", "rate": 0.09, "cap_monthly": None}],
            "employer_contributions": [{"code": "IPS_EMP", "name": "IPS Empleador", "rate": 0.165, "cap_monthly": None}]
        },
        "income_tax": {"name": "IRP", "agency": "SET", "exempt_monthly": 0, "brackets": [{"min": 0, "max": None, "rate": 0.10, "fixed": 0}]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": [], "contract_types": ["indefinido", "temporal"],
        "permission_types": _base_permissions()
    },
    "UY": {
        "code": "UY", "region": "south_america", "name": "Uruguay", "flag": "🇺🇾",
        "currency": "UYU", "currency_symbol": "$U", "currency_name": "Peso Uruguayo", "locale": "es-UY",
        "document_types": ["CI", "RUT", "Pasaporte"],
        "working_days_month": 25, "weekly_hours": 44,
        "vacation_days_per_year": 20, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "Aguinaldo",
        "social_security": {
            "system_name": "BPS",
            "employee_deductions": [
                {"code": "JUBILACION_UY", "name": "Jubilación", "rate": 0.15, "cap_monthly": None},
                {"code": "FONASA", "name": "FONASA (Salud)", "rate": 0.045, "cap_monthly": None},
                {"code": "FRL", "name": "Fondo Reconversión Laboral", "rate": 0.001, "cap_monthly": None}
            ],
            "employer_contributions": [{"code": "BPS_EMP", "name": "BPS Empleador", "rate": 0.075, "cap_monthly": None}]
        },
        "income_tax": {"name": "IRPF", "agency": "DGI", "exempt_monthly": 0, "brackets": [
            {"min": 0, "max": 468420, "rate": 0, "fixed": 0},
            {"min": 468420, "max": 669180, "rate": 0.10, "fixed": 0},
            {"min": 669180, "max": None, "rate": 0.15, "fixed": 20076}
        ]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": [], "contract_types": ["indefinido", "temporal"],
        "permission_types": _base_permissions()
    },
    "GY": {
        "code": "GY", "region": "south_america", "name": "Guyana", "flag": "🇬🇾",
        "currency": "GYD", "currency_symbol": "$", "currency_name": "Guyana Dollar", "locale": "en-GY",
        "document_types": ["National ID", "Passport", "TIN"],
        "working_days_month": 26, "weekly_hours": 40, "vacation_days_per_year": 12, "probation_days": 90,
        "christmas_bonus": False, "christmas_bonus_name": "",
        "social_security": {"system_name": "NIS", "employee_deductions": [{"code": "NIS", "name": "NIS", "rate": 0.056, "cap_monthly": None}], "employer_contributions": [{"code": "NIS_EMP", "name": "NIS Employer", "rate": 0.084, "cap_monthly": None}]},
        "income_tax": {"name": "Income Tax", "agency": "GRA", "exempt_monthly": 0, "brackets": [{"min": 0, "max": 780000, "rate": 0.28, "fixed": 0}, {"min": 780000, "max": None, "rate": 0.40, "fixed": 218400}]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": [], "contract_types": ["indefinite", "fixed_term"],
        "permission_types": _base_permissions()
    },
    "SR": {
        "code": "SR", "region": "south_america", "name": "Surinam", "flag": "🇸🇷",
        "currency": "SRD", "currency_symbol": "$", "currency_name": "Surinamese Dollar", "locale": "nl-SR",
        "document_types": ["ID Card", "Passport"],
        "working_days_month": 26, "weekly_hours": 45, "vacation_days_per_year": 12, "probation_days": 60,
        "christmas_bonus": True, "christmas_bonus_name": "13th Month",
        "social_security": {"system_name": "SZF", "employee_deductions": [{"code": "AOV", "name": "AOV (Pension)", "rate": 0.04, "cap_monthly": None}], "employer_contributions": [{"code": "AOV_EMP", "name": "AOV Employer", "rate": 0.065, "cap_monthly": None}]},
        "income_tax": {"name": "Income Tax", "agency": "Belastingdienst", "exempt_monthly": 0, "brackets": [{"min": 0, "max": None, "rate": 0.38, "fixed": 0}]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": [], "contract_types": ["indefinite", "fixed_term"],
        "permission_types": _base_permissions()
    },
    "BR": {
        "code": "BR", "region": "south_america", "name": "Brasil", "flag": "🇧🇷",
        "currency": "BRL", "currency_symbol": "R$", "currency_name": "Real", "locale": "pt-BR",
        "document_types": ["CPF", "CNPJ", "RG", "Passaporte"],
        "working_days_month": 30, "weekly_hours": 44, "vacation_days_per_year": 30, "probation_days": 90,
        "christmas_bonus": True, "christmas_bonus_name": "13º Salário",
        "social_security": {
            "system_name": "INSS",
            "employee_deductions": [{"code": "INSS_BR", "name": "INSS", "rate": 0.09, "cap_monthly": None}],
            "employer_contributions": [
                {"code": "INSS_BR_EMP", "name": "INSS Patronal", "rate": 0.20, "cap_monthly": None},
                {"code": "FGTS", "name": "FGTS", "rate": 0.08, "cap_monthly": None},
                {"code": "SAT", "name": "SAT/RAT", "rate": 0.02, "cap_monthly": None},
                {"code": "SISTEMA_S", "name": "Sistema S", "rate": 0.058, "cap_monthly": None}
            ]
        },
        "income_tax": {"name": "IRRF", "agency": "Receita Federal", "exempt_monthly": 0, "brackets": [
            {"min": 0, "max": 24511.92, "rate": 0, "fixed": 0},
            {"min": 24511.93, "max": 33919.80, "rate": 0.075, "fixed": 0},
            {"min": 33919.81, "max": 45012.60, "rate": 0.15, "fixed": 0},
            {"min": 45012.61, "max": 55976.16, "rate": 0.225, "fixed": 0},
            {"min": 55976.17, "max": None, "rate": 0.275, "fixed": 0}
        ]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": ["ESOCIAL", "DIRF", "RAIS"],
        "contract_types": ["CLT", "PJ", "temporario", "intermitente"],
        "permission_types": _base_permissions()
    },

    # ==================== EUROPA ====================
    "ES": {
        "code": "ES", "region": "europe", "name": "España", "flag": "🇪🇸",
        "currency": "EUR", "currency_symbol": "€", "currency_name": "Euro", "locale": "es-ES",
        "document_types": ["DNI", "NIE", "NIF", "Pasaporte"],
        "working_days_month": 22, "weekly_hours": 40, "vacation_days_per_year": 22, "probation_days": 60,
        "christmas_bonus": True, "christmas_bonus_name": "Paga Extra (Jun + Dic)",
        "social_security": {
            "system_name": "Seguridad Social (TGSS)",
            "employee_deductions": [
                {"code": "CC", "name": "Contingencias Comunes", "rate": 0.047, "cap_monthly": None},
                {"code": "DESEMPLEO", "name": "Desempleo", "rate": 0.0155, "cap_monthly": None},
                {"code": "FP", "name": "Formación Profesional", "rate": 0.001, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "CC_EMP", "name": "Contingencias Comunes Emp.", "rate": 0.236, "cap_monthly": None},
                {"code": "DESEMPLEO_EMP", "name": "Desempleo Empleador", "rate": 0.055, "cap_monthly": None},
                {"code": "FOGASA", "name": "FOGASA", "rate": 0.002, "cap_monthly": None},
                {"code": "FP_EMP", "name": "Formación Profesional Emp.", "rate": 0.006, "cap_monthly": None}
            ]
        },
        "income_tax": {"name": "IRPF", "agency": "AEAT", "exempt_monthly": 0, "brackets": [
            {"min": 0, "max": 12450, "rate": 0.19, "fixed": 0},
            {"min": 12450, "max": 20200, "rate": 0.24, "fixed": 2365.50},
            {"min": 20200, "max": 35200, "rate": 0.30, "fixed": 4225.50},
            {"min": 35200, "max": 60000, "rate": 0.37, "fixed": 8725.50},
            {"min": 60000, "max": None, "rate": 0.45, "fixed": 17901.50}
        ]},
        "severance": {"cesantia_formula": "ES_ET"}, "reports": ["MODELO_111", "MODELO_190"],
        "contract_types": ["indefinido", "temporal", "formacion", "practicas"],
        "permission_types": _base_permissions()
    },
    "GB": {
        "code": "GB", "region": "europe", "name": "Reino Unido", "flag": "🇬🇧",
        "currency": "GBP", "currency_symbol": "£", "currency_name": "Pound Sterling", "locale": "en-GB",
        "document_types": ["NI Number", "Passport"],
        "working_days_month": 22, "weekly_hours": 37.5, "vacation_days_per_year": 28, "probation_days": 90,
        "christmas_bonus": False, "christmas_bonus_name": "",
        "social_security": {
            "system_name": "National Insurance (NI)",
            "employee_deductions": [{"code": "NI", "name": "National Insurance", "rate": 0.08, "cap_monthly": None}],
            "employer_contributions": [{"code": "NI_EMP", "name": "NI Employer", "rate": 0.138, "cap_monthly": None}]
        },
        "income_tax": {"name": "Income Tax", "agency": "HMRC", "exempt_monthly": 0, "brackets": [
            {"min": 0, "max": 12570, "rate": 0, "fixed": 0},
            {"min": 12570, "max": 50270, "rate": 0.20, "fixed": 0},
            {"min": 50270, "max": 125140, "rate": 0.40, "fixed": 7540},
            {"min": 125140, "max": None, "rate": 0.45, "fixed": 37488}
        ]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": ["P60", "P45", "RTI"],
        "contract_types": ["permanent", "fixed_term", "zero_hours"],
        "permission_types": _base_permissions()
    },
    "FR": {
        "code": "FR", "region": "europe", "name": "Francia", "flag": "🇫🇷",
        "currency": "EUR", "currency_symbol": "€", "currency_name": "Euro", "locale": "fr-FR",
        "document_types": ["CNI", "Passeport", "Titre de Séjour"],
        "working_days_month": 22, "weekly_hours": 35, "vacation_days_per_year": 25, "probation_days": 60,
        "christmas_bonus": False, "christmas_bonus_name": "",
        "social_security": {
            "system_name": "Sécurité Sociale / URSSAF",
            "employee_deductions": [
                {"code": "CSG", "name": "CSG", "rate": 0.098, "cap_monthly": None},
                {"code": "VIEILLESSE", "name": "Assurance Vieillesse", "rate": 0.069, "cap_monthly": None},
                {"code": "CHOMAGE", "name": "Assurance Chômage", "rate": 0, "cap_monthly": None}
            ],
            "employer_contributions": [
                {"code": "URSSAF_EMP", "name": "URSSAF (Maladie+Famille+AT)", "rate": 0.303, "cap_monthly": None},
                {"code": "VIEILLESSE_EMP", "name": "Vieillesse Employeur", "rate": 0.0855, "cap_monthly": None},
                {"code": "CHOMAGE_EMP", "name": "Chômage Employeur", "rate": 0.0405, "cap_monthly": None}
            ]
        },
        "income_tax": {"name": "Impôt sur le Revenu (PAS)", "agency": "DGFiP", "exempt_monthly": 0, "brackets": [
            {"min": 0, "max": 11294, "rate": 0, "fixed": 0},
            {"min": 11294, "max": 28797, "rate": 0.11, "fixed": 0},
            {"min": 28797, "max": 82341, "rate": 0.30, "fixed": 1925.33},
            {"min": 82341, "max": None, "rate": 0.41, "fixed": 17988.53}
        ]},
        "severance": {"cesantia_formula": "GENERIC"}, "reports": ["DSN"],
        "contract_types": ["CDI", "CDD", "interim"],
        "permission_types": _base_permissions()
    },
}

SUPPORTED_COUNTRIES = list(COUNTRY_PROFILES.keys())

# ===================== ENDPOINTS =====================

@router.get("/countries")
async def get_supported_countries():
    """Get list of supported countries organized by region"""
    result = {}
    for region_code, region_info in REGIONS.items():
        countries = []
        for code, profile in COUNTRY_PROFILES.items():
            if profile.get("region") == region_code:
                countries.append({
                    "code": code, "name": profile["name"], "flag": profile.get("flag", ""),
                    "currency": profile["currency"], "currency_symbol": profile["currency_symbol"],
                    "currency_name": profile["currency_name"]
                })
        if countries:
            countries.sort(key=lambda x: x["name"])
            result[region_code] = {"region": region_info, "countries": countries}
    return {"regions": result, "total": len(COUNTRY_PROFILES)}


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
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1, "currency": 1, "company_name": 1, "name": 1})
    country_code = (company or {}).get("country", "DO")
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["DO"])
    overrides = await db.country_config_overrides.find_one({"company_id": company_id}, {"_id": 0})
    return {"country_code": country_code, "profile": profile, "overrides": overrides, "company_name": (company or {}).get("company_name", (company or {}).get("name", ""))}


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
        {"$set": {"country": country_code, "currency": profile["currency"], "currency_symbol": profile["currency_symbol"], "updated_at": datetime.now(timezone.utc)}}
    )
    return {"success": True, "message": f"País configurado: {profile['name']}"}


# ===================== PAYROLL RATES HELPER =====================

async def get_payroll_rates(company_id: str) -> dict:
    """Get payroll calculation rates for a company based on its country."""
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    country_code = (company or {}).get("country", "DO")
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["DO"])
    employee_rates = {}
    for ded in profile["social_security"]["employee_deductions"]:
        employee_rates[ded["code"]] = {"name": ded["name"], "rate": ded["rate"], "cap": ded.get("cap_monthly")}
    employer_rates = {}
    for cont in profile["social_security"]["employer_contributions"]:
        employer_rates[cont["code"]] = {"name": cont["name"], "rate": cont["rate"], "cap": cont.get("cap_monthly")}
    return {
        "country_code": country_code, "country_name": profile["name"],
        "currency": profile["currency"], "currency_symbol": profile["currency_symbol"],
        "working_days_month": profile["working_days_month"],
        "employee_deductions": employee_rates, "employer_contributions": employer_rates,
        "income_tax": profile["income_tax"],
        "social_security_name": profile["social_security"]["system_name"]
    }


async def get_company_rates_flat(company_id: str) -> dict:
    """
    Get payroll rates in FLAT format (legacy-compatible with DR structure).
    Returns sfs/afp/srl/infotep slots mapped from country profile.
    - Slot 0-1 employee: first 2 employee deductions (DR: SFS, AFP)
    - Slot 0-3 employer: first 4 employer contributions (DR: SFS_EMP, AFP_EMP, SRL, INFOTEP)
    Countries with fewer slots get 0.0 for missing ones.
    """
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    country_code = (company or {}).get("country", "DO")
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES["DO"])
    emp_deds = profile["social_security"]["employee_deductions"]
    employer_conts = profile["social_security"]["employer_contributions"]

    def _rate(lst, idx):
        return lst[idx]["rate"] if idx < len(lst) else 0.0

    def _name(lst, idx, default=""):
        return lst[idx]["name"] if idx < len(lst) else default

    def _code(lst, idx, default=""):
        return lst[idx]["code"] if idx < len(lst) else default

    return {
        "country_code": country_code,
        "country_name": profile["name"],
        "currency": profile["currency"],
        "currency_symbol": profile["currency_symbol"],
        "working_days_month": profile["working_days_month"],
        # Employee deductions (legacy DR slots)
        "sfs_employee_rate": _rate(emp_deds, 0),
        "afp_employee_rate": _rate(emp_deds, 1),
        # Employer contributions (legacy DR slots)
        "sfs_employer_rate": _rate(employer_conts, 0),
        "afp_employer_rate": _rate(employer_conts, 1),
        "srl_employer_rate": _rate(employer_conts, 2),
        "infotep_employer_rate": _rate(employer_conts, 3),
        # Extra details for display / future expansion
        "employee_deductions_detail": emp_deds,
        "employer_contributions_detail": employer_conts,
        "income_tax": profile["income_tax"],
        # Labels for frontend (UI-agnostic to DR)
        "labels": {
            "sfs_employee": _name(emp_deds, 0, "Deducción 1"),
            "afp_employee": _name(emp_deds, 1, "Deducción 2"),
            "sfs_employer": _name(employer_conts, 0, "Contribución 1"),
            "afp_employer": _name(employer_conts, 1, "Contribución 2"),
            "srl_employer": _name(employer_conts, 2, "Contribución 3"),
            "infotep_employer": _name(employer_conts, 3, "Contribución 4"),
        },
        "codes": {
            "sfs_employee": _code(emp_deds, 0),
            "afp_employee": _code(emp_deds, 1),
            "sfs_employer": _code(employer_conts, 0),
            "afp_employer": _code(employer_conts, 1),
            "srl_employer": _code(employer_conts, 2),
            "infotep_employer": _code(employer_conts, 3),
        },
    }


def calculate_isr_dynamic(gross_monthly: float, income_tax_config: dict) -> dict:
    """
    Calculate monthly ISR (income tax) using bracket structure from any country.
    Returns dict compatible with DR's calculate_isr_monthly.
    """
    if not income_tax_config or not income_tax_config.get("brackets"):
        return {
            "taxable_base_monthly": round(gross_monthly, 2),
            "annual_taxable": round(gross_monthly * 12, 2),
            "isr_annual": 0.0,
            "isr_monthly": 0.0,
            "tax_bracket": "N/A",
        }
    exempt = float(income_tax_config.get("exempt_monthly", 0) or 0)
    annual_gross = gross_monthly * 12 if exempt > 0 and gross_monthly > 0 else gross_monthly * 12
    # Brackets can be annual (DO uses annual) or monthly. DO uses annual brackets.
    # Strategy: if country has exempt_monthly > 0 AND bracket max > 100000 → likely annual (DO, CR, MX).
    # If brackets are in currency thousands (e.g., UK: 12570) with no clear exemption -> monthly × 12.
    # Heuristic: if any bracket max > annual_gross * 2, treat as annual.
    brackets = income_tax_config["brackets"]
    max_bracket_val = max([b.get("max") or 0 for b in brackets])
    use_annual = max_bracket_val > gross_monthly * 3  # likely annual brackets
    taxable = annual_gross if use_annual else gross_monthly
    # Apply exemption
    if exempt > 0 and use_annual:
        pass  # brackets already include exempt threshold as first bracket
    isr_calc = 0.0
    bracket_label = "Exento"
    for b in brackets:
        b_min = float(b.get("min", 0) or 0)
        b_max = b.get("max")
        b_rate = float(b.get("rate", 0) or 0)
        b_fixed = float(b.get("fixed", 0) or 0)
        if b_max is None or taxable <= float(b_max):
            if taxable > b_min:
                isr_calc = b_fixed + (taxable - b_min) * b_rate
                bracket_label = f"{int(b_rate * 100)}%"
            break
    isr_monthly_val = isr_calc / 12 if use_annual else isr_calc
    isr_monthly_val = round(max(0.0, isr_monthly_val), 2)
    return {
        "taxable_base_monthly": round(gross_monthly, 2),
        "annual_taxable": round(gross_monthly * 12, 2),
        "isr_annual": round(isr_monthly_val * 12, 2),
        "isr_monthly": isr_monthly_val,
        "tax_bracket": bracket_label,
    }


# ===================== MIGRATION =====================

async def migrate_existing_companies():
    """Migrate existing companies without proper country code"""
    name_mappings = {"República Dominicana": "DO", "Dominican Republic": "DO", "Colombia": "CO", "México": "MX", "Mexico": "MX", "Panamá": "PA", "Panama": "PA"}
    for name, code in name_mappings.items():
        profile = COUNTRY_PROFILES.get(code, COUNTRY_PROFILES["DO"])
        await db.companies.update_many({"country": name}, {"$set": {"country": code, "currency": profile["currency"], "currency_symbol": profile["currency_symbol"]}})
    result = await db.companies.update_many(
        {"$or": [{"country": {"$exists": False}}, {"country": None}, {"country": ""}]},
        {"$set": {"country": "DO", "currency": "DOP", "currency_symbol": "RD$"}}
    )
    if result.modified_count > 0:
        print(f"[Country Migration] {result.modified_count} companies migrated to DO")

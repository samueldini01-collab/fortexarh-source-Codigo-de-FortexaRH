"""Catalog of native fiscal formats per country + filing deadlines.

This is the single source of truth for:
- which formats exist per country
- which are implemented vs. backlog (post-iter240: 33/33 implemented)
- the typical due-date heuristic used by the smart reminder engine

Exposed via ``GET /api/native-reports/catalog``.
"""
from __future__ import annotations

from fastapi import Depends

from routes.country_config import COUNTRY_PROFILES
from utils.auth import get_current_user

from . import router


# ===================== NATIVE FORMATS CATALOG =====================

NATIVE_FORMATS: dict[str, list[dict]] = {
    "DO": [
        {"code": "TSS_AUTODET", "name": "TSS Autodeterminación (Tipo A)", "agency": "TSS", "frequency": "monthly", "endpoint": "/api/dgii-reports/tss/autodeterminacion", "implemented": True},
        {"code": "TSS_NOVEDADES", "name": "TSS Novedades (Tipo N)", "agency": "TSS", "frequency": "monthly", "endpoint": "/api/dgii-reports/tss/novedades", "implemented": True},
        {"code": "IR3", "name": "IR-3 (Retenciones ISR)", "agency": "DGII", "frequency": "monthly", "endpoint": "/api/dgii-reports/ir3", "implemented": True},
        {"code": "IR17", "name": "IR-17 (Anual)", "agency": "DGII", "frequency": "annual", "endpoint": "/api/dgii-reports/ir17", "implemented": True},
    ],
    "CO": [
        {"code": "PILA", "name": "PILA UGPP (Planilla Integrada)", "agency": "UGPP", "frequency": "monthly", "endpoint": "/api/native-reports/co/pila", "implemented": True},
    ],
    "MX": [
        {"code": "IMSS_SUA", "name": "IMSS SUA Cuotas", "agency": "IMSS", "frequency": "monthly", "endpoint": "/api/native-reports/mx/imss-cuotas", "implemented": True},
        {"code": "INFONAVIT", "name": "INFONAVIT Bimestral", "agency": "INFONAVIT", "frequency": "bimonthly", "endpoint": "/api/native-reports/mx/infonavit", "implemented": True},
    ],
    "US": [{"code": "FORM_941", "name": "IRS Form 941 (PDF)", "agency": "IRS", "frequency": "quarterly", "endpoint": "/api/native-reports/us/form-941", "implemented": True}],
    "ES": [
        {"code": "MODELO_111", "name": "Modelo 111 (Retenciones IRPF)", "agency": "AEAT", "frequency": "quarterly", "endpoint": "/api/native-reports/es/modelo-111", "implemented": True},
        {"code": "TC1", "name": "TC1 FAN (Cotización SS)", "agency": "TGSS", "frequency": "monthly", "endpoint": "/api/native-reports/es/tc1", "implemented": True},
    ],
    "GB": [{"code": "RTI_FPS", "name": "HMRC RTI FPS (XML)", "agency": "HMRC", "frequency": "monthly", "endpoint": "/api/native-reports/gb/rti-fps", "implemented": True}],
    "FR": [{"code": "DSN", "name": "DSN (Déclaration Sociale Nominative)", "agency": "URSSAF", "frequency": "monthly", "endpoint": "/api/native-reports/fr/dsn", "implemented": True}],
    "CA": [{"code": "T4", "name": "T4 Statement of Remuneration", "agency": "CRA", "frequency": "annual", "endpoint": "/api/native-reports/ca/t4", "implemented": True}],
    "BR": [{"code": "ESOCIAL", "name": "eSocial S-1200", "agency": "Receita Federal", "frequency": "monthly", "endpoint": "/api/native-reports/br/esocial", "implemented": True}],
    "AR": [{"code": "F931", "name": "F.931 AFIP", "agency": "AFIP", "frequency": "monthly", "endpoint": "/api/native-reports/ar/f931", "implemented": True}],
    "CL": [{"code": "PREVIRED", "name": "PreviRed (cotizaciones previsionales)", "agency": "PreviRed", "frequency": "monthly", "endpoint": "/api/native-reports/cl/previred", "implemented": True}],
    "PE": [{"code": "PLAME", "name": "PLAME SUNAT (Planilla Electrónica)", "agency": "SUNAT", "frequency": "monthly", "endpoint": "/api/native-reports/pe/plame", "implemented": True}],
    "EC": [{"code": "IESS_PLANILLA", "name": "IESS Planilla mensual", "agency": "IESS", "frequency": "monthly", "endpoint": "/api/native-reports/ec/iess", "implemented": True}],
    "VE": [{"code": "IVSS_FORMA", "name": "IVSS Forma 14-02", "agency": "IVSS", "frequency": "monthly", "endpoint": "/api/native-reports/ve/ivss", "implemented": True}],
    "BO": [{"code": "F110", "name": "Formulario 110 (Aportes AFP/SIN)", "agency": "SIN/AFP", "frequency": "monthly", "endpoint": "/api/native-reports/bo/f110", "implemented": True}],
    "PY": [{"code": "F109", "name": "Formulario 109 IPS", "agency": "IPS", "frequency": "monthly", "endpoint": "/api/native-reports/py/f109", "implemented": True}],
    "UY": [{"code": "BPS_1146", "name": "BPS Formulario 1146", "agency": "BPS", "frequency": "monthly", "endpoint": "/api/native-reports/uy/bps-1146", "implemented": True}],
    "GY": [{"code": "NIS", "name": "NIS Returns", "agency": "NIS", "frequency": "monthly", "endpoint": "/api/native-reports/gy/nis", "implemented": True}],
    "SR": [{"code": "SZF", "name": "SZF Filing", "agency": "SZF", "frequency": "monthly", "endpoint": "/api/native-reports/sr/szf", "implemented": True}],
    "CR": [{"code": "CCSS_PLANILLA", "name": "CCSS Planilla", "agency": "CCSS", "frequency": "monthly", "endpoint": "/api/native-reports/cr/ccss", "implemented": True}],
    "SV": [{"code": "F1_ISSS", "name": "Formulario F-1 ISSS", "agency": "ISSS", "frequency": "monthly", "endpoint": "/api/native-reports/sv/f1-isss", "implemented": True}],
    "GT": [{"code": "IGSS_PLANILLA", "name": "IGSS Planilla", "agency": "IGSS", "frequency": "monthly", "endpoint": "/api/native-reports/gt/igss", "implemented": True}],
    "HN": [{"code": "IHSS_PLANILLA", "name": "IHSS Planilla", "agency": "IHSS", "frequency": "monthly", "endpoint": "/api/native-reports/hn/ihss", "implemented": True}],
    "NI": [{"code": "INSS_PLANILLA", "name": "INSS Planilla", "agency": "INSS", "frequency": "monthly", "endpoint": "/api/native-reports/ni/inss", "implemented": True}],
    "PA": [{"code": "CSS_PLANILLA", "name": "CSS Planilla", "agency": "CSS", "frequency": "monthly", "endpoint": "/api/native-reports/pa/css", "implemented": True}],
    "CU": [{"code": "ONAT_FORM", "name": "ONAT Form", "agency": "ONAT", "frequency": "monthly", "endpoint": "/api/native-reports/cu/onat", "implemented": True}],
    "HT": [{"code": "ONA_DECLAR", "name": "ONA Déclaration", "agency": "ONA", "frequency": "monthly", "endpoint": "/api/native-reports/ht/ona", "implemented": True}],
    "PR": [{"code": "FORM_499R", "name": "Form 499R-2/W-2PR", "agency": "Hacienda PR", "frequency": "annual", "endpoint": "/api/native-reports/pr/form-499r", "implemented": True}],
}


# ===================== FILING DEADLINES =====================

# (day_of_filing_month, offset_months_after_period). The smart reminder engine
# uses these to compute due dates and trigger 7/3/1/0/-1 day notifications.
FORMAT_DEADLINES: dict[str, dict] = {
    "TSS_AUTODET": {"day": 3, "offset_months": 1, "description": "Día 3 del mes siguiente"},
    "TSS_NOVEDADES": {"day": 3, "offset_months": 1, "description": "Día 3 del mes siguiente"},
    "IR3": {"day": 10, "offset_months": 1, "description": "Día 10 del mes siguiente"},
    "IR17": {"day": 15, "offset_months": 3, "description": "15 de marzo del año siguiente"},
    "PILA": {"day": 8, "offset_months": 1, "description": "Días 8-13 según último dígito NIT"},
    "IMSS_SUA": {"day": 17, "offset_months": 1, "description": "Día 17 del mes siguiente"},
    "INFONAVIT": {"day": 17, "offset_months": 2, "description": "Día 17 cada bimestre"},
    "FORM_941": {"day": 30, "offset_months": 1, "description": "Último día del mes siguiente al trimestre"},
    "MODELO_111": {"day": 20, "offset_months": 1, "description": "Día 20 del mes siguiente al trimestre"},
    "TC1": {"day": 30, "offset_months": 1, "description": "Último día del mes siguiente"},
    "RTI_FPS": {"day": 19, "offset_months": 1, "description": "Día 19 del mes siguiente al pago (HMRC)"},
    "DSN": {"day": 15, "offset_months": 1, "description": "Día 15 del mes siguiente (régimen général)"},
    "T4": {"day": 28, "offset_months": 2, "description": "Último día de febrero del año siguiente"},
    "ESOCIAL": {"day": 15, "offset_months": 1, "description": "Día 15 del mes siguiente"},
    "F931": {"day": 13, "offset_months": 1, "description": "Días 7-13 según último dígito CUIT"},
    "PREVIRED": {"day": 10, "offset_months": 1, "description": "Día 10 del mes siguiente (Chile)"},
    "PLAME": {"day": 12, "offset_months": 1, "description": "Días 7-22 según último dígito RUC (Perú)"},
    "IESS_PLANILLA": {"day": 15, "offset_months": 1, "description": "Día 15 del mes siguiente (IESS Ecuador)"},
    "IVSS_FORMA": {"day": 5, "offset_months": 1, "description": "Primeros 5 días del mes siguiente (IVSS)"},
    "F110": {"day": 13, "offset_months": 1, "description": "Día 13 del mes siguiente (SIN/AFP Bolivia)"},
    "F109": {"day": 20, "offset_months": 1, "description": "Día 20 del mes siguiente (IPS Paraguay)"},
    "BPS_1146": {"day": 25, "offset_months": 1, "description": "Día 25 del mes siguiente (BPS Uruguay)"},
    "NIS": {"day": 15, "offset_months": 1, "description": "Día 15 del mes siguiente (NIS Guyana)"},
    "SZF": {"day": 15, "offset_months": 1, "description": "Día 15 del mes siguiente (SZF Surinam)"},
    "CCSS_PLANILLA": {"day": 20, "offset_months": 1, "description": "Día 20 del mes siguiente (CCSS Costa Rica)"},
    "F1_ISSS": {"day": 7, "offset_months": 1, "description": "Primeros 7 días hábiles del mes siguiente (ISSS El Salvador)"},
    "IGSS_PLANILLA": {"day": 20, "offset_months": 1, "description": "Día 20 del mes siguiente (IGSS Guatemala)"},
    "IHSS_PLANILLA": {"day": 10, "offset_months": 1, "description": "Día 10 del mes siguiente (IHSS Honduras)"},
    "INSS_PLANILLA": {"day": 17, "offset_months": 1, "description": "Día 17 del mes siguiente (INSS Nicaragua)"},
    "CSS_PLANILLA": {"day": 30, "offset_months": 1, "description": "Último día del mes siguiente (CSS Panamá)"},
    "ONAT_FORM": {"day": 20, "offset_months": 1, "description": "Día 20 del mes siguiente (ONAT Cuba)"},
    "ONA_DECLAR": {"day": 10, "offset_months": 1, "description": "Día 10 del mes siguiente (ONA Haití)"},
    "FORM_499R": {"day": 31, "offset_months": 1, "description": "31 de enero del año siguiente (Hacienda PR)"},
}


# ===================== CATALOG ENDPOINT =====================

@router.get("/catalog")
async def get_native_formats_catalog(current_user: dict = Depends(get_current_user)):
    """Return the global catalog of native fiscal formats per country with implementation status."""
    summary = {
        "total_countries": len(NATIVE_FORMATS),
        "total_formats": sum(len(v) for v in NATIVE_FORMATS.values()),
        "implemented_formats": sum(1 for v in NATIVE_FORMATS.values() for f in v if f.get("implemented")),
        "countries": [],
    }
    for code, formats in NATIVE_FORMATS.items():
        profile = COUNTRY_PROFILES.get(code, {})
        impl_count = sum(1 for f in formats if f.get("implemented"))
        summary["countries"].append({
            "code": code,
            "name": profile.get("name", code),
            "flag": profile.get("flag", ""),
            "region": profile.get("region", ""),
            "currency": profile.get("currency", ""),
            "agency": (profile.get("income_tax") or {}).get("agency", ""),
            "social_security_system": (profile.get("social_security") or {}).get("system_name", ""),
            "formats": formats,
            "implemented_count": impl_count,
            "total_count": len(formats),
            "compliance_status": "complete" if impl_count == len(formats) else ("partial" if impl_count > 0 else "universal_only"),
        })
    return summary

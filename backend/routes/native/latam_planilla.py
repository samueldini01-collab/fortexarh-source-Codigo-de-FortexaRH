"""Generic LATAM monthly planilla CSV builder + auto-registered endpoints.

17 LATAM countries (CL, PE, EC, VE, BO, PY, UY, GY, SR, CR, SV, GT, HN, NI,
PA, CU, HT) require monthly contribution planillas with the same essential
shape: per-employee deductions + employer contributions on top of the gross.
Instead of duplicating 17 near-identical FastAPI handlers, we describe each
agency in ``PLANILLA_COLUMN_PROFILES`` and **iterate** to register routes.

CSV output: UTF-8 with BOM, semicolon-delimited (Excel-friendly across all
LATAM locales).
"""
from __future__ import annotations

import csv as _csv
import io
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Response

from config import db
from routes.country_config import COUNTRY_PROFILES
from routes.multi_country_reports import _collect_period_data
from utils.auth import get_current_user

from . import router
from ._helpers import require_country


# ===================== PLANILLA COLUMN PROFILES =====================
#
# Each profile describes ONE country's planilla layout. ``deductions`` are
# employee-side withholdings and ``employer`` are patronal contributions. Slot
# names map directly to ``payroll_entries`` fields produced by the calc engine.

PLANILLA_COLUMN_PROFILES: dict[str, dict] = {
    "PREVIRED": {  # 🇨🇱 Chile
        "expected_country": "CL",
        "endpoint_path": "/cl/previred",
        "agency": "PreviRed",
        "doc_field": "rut",
        "doc_label": "RUT Trabajador",
        "deductions": [
            ("AFP (10%)", "afp_employee"),
            ("Salud 7%", "sfs_employee"),
            ("AFC Trabajador 0.6%", "afc_employee"),
        ],
        "employer": [
            ("SIS Empleador", "srl_employer"),
            ("AFC Empleador 2.4%", "afc_employer"),
            ("Mutual ATEP", "mutual_employer"),
        ],
        "extra_company_field": ("RUT Empresa", "rnc"),
    },
    "PLAME": {  # 🇵🇪 Perú
        "expected_country": "PE",
        "endpoint_path": "/pe/plame",
        "agency": "SUNAT",
        "doc_field": "dni",
        "doc_label": "DNI / CE",
        "deductions": [
            ("AFP/ONP", "afp_employee"),
            ("EsSalud Trabajador", "sfs_employee"),
            ("Renta 5ta Cat.", "isr"),
        ],
        "employer": [
            ("EsSalud Empleador 9%", "sfs_employer"),
            ("SCTR", "srl_employer"),
        ],
        "extra_company_field": ("RUC", "rnc"),
    },
    "IESS_PLANILLA": {  # 🇪🇨 Ecuador
        "expected_country": "EC",
        "endpoint_path": "/ec/iess",
        "agency": "IESS",
        "doc_field": "cedula",
        "doc_label": "Cédula",
        "deductions": [
            ("Aporte IESS Personal 9.45%", "sfs_employee"),
            ("Impuesto a la Renta", "isr"),
        ],
        "employer": [
            ("Aporte Patronal 11.15%", "sfs_employer"),
            ("IECE-SECAP 1%", "infotep_employer"),
        ],
        "extra_company_field": ("RUC", "rnc"),
    },
    "IVSS_FORMA": {  # 🇻🇪 Venezuela
        "expected_country": "VE",
        "endpoint_path": "/ve/ivss",
        "agency": "IVSS",
        "doc_field": "cedula",
        "doc_label": "Cédula",
        "deductions": [
            ("IVSS 4%", "sfs_employee"),
            ("Paro Forzoso 0.5%", "afp_employee"),
            ("LPH 1%", "srl_employee"),
        ],
        "employer": [
            ("IVSS Patronal", "sfs_employer"),
            ("Paro Forzoso Patronal", "afp_employer"),
            ("LPH Patronal 2%", "srl_employer"),
            ("INCES 2%", "infotep_employer"),
        ],
        "extra_company_field": ("RIF", "rnc"),
    },
    "F110": {  # 🇧🇴 Bolivia
        "expected_country": "BO",
        "endpoint_path": "/bo/f110",
        "agency": "SIN/AFP",
        "doc_field": "ci",
        "doc_label": "CI",
        "deductions": [
            ("AFP Trabajador 12.71%", "afp_employee"),
            ("Aporte Solidario 0.5%", "sfs_employee"),
            ("RC-IVA", "isr"),
        ],
        "employer": [
            ("CNS Salud 10%", "sfs_employer"),
            ("PROVIVIENDA 2%", "srl_employer"),
            ("AFP Patronal 1.71%", "afp_employer"),
        ],
        "extra_company_field": ("NIT", "rnc"),
    },
    "F109": {  # 🇵🇾 Paraguay
        "expected_country": "PY",
        "endpoint_path": "/py/f109",
        "agency": "IPS",
        "doc_field": "ci",
        "doc_label": "CI",
        "deductions": [
            ("IPS Trabajador 9%", "sfs_employee"),
            ("IRP", "isr"),
        ],
        "employer": [
            ("IPS Patronal 16.5%", "sfs_employer"),
        ],
        "extra_company_field": ("RUC", "rnc"),
    },
    "BPS_1146": {  # 🇺🇾 Uruguay
        "expected_country": "UY",
        "endpoint_path": "/uy/bps-1146",
        "agency": "BPS",
        "doc_field": "ci",
        "doc_label": "CI",
        "deductions": [
            ("Aporte Jubilatorio 15%", "afp_employee"),
            ("FONASA 4.5%", "sfs_employee"),
            ("FRL 0.125%", "srl_employee"),
            ("IRPF", "isr"),
        ],
        "employer": [
            ("Aporte Patronal 7.5%", "afp_employer"),
            ("FONASA Patronal 5%", "sfs_employer"),
            ("FRL Patronal 0.025%", "srl_employer"),
        ],
        "extra_company_field": ("RUT BPS", "rnc"),
    },
    "NIS": {  # 🇬🇾 Guyana
        "expected_country": "GY",
        "endpoint_path": "/gy/nis",
        "agency": "NIS Guyana",
        "doc_field": "nis_number",
        "doc_label": "NIS Number",
        "deductions": [
            ("NIS Employee 5.6%", "sfs_employee"),
            ("PAYE", "isr"),
        ],
        "employer": [
            ("NIS Employer 8.4%", "sfs_employer"),
        ],
        "extra_company_field": ("Employer NIS Reg.", "rnc"),
    },
    "SZF": {  # 🇸🇷 Surinam
        "expected_country": "SR",
        "endpoint_path": "/sr/szf",
        "agency": "SZF",
        "doc_field": "id_number",
        "doc_label": "ID Nummer",
        "deductions": [
            ("AOV 4%", "afp_employee"),
            ("Loonbelasting", "isr"),
        ],
        "employer": [
            ("AOV Werkgever 4%", "afp_employer"),
            ("Ziektekosten", "sfs_employer"),
        ],
        "extra_company_field": ("KKF Nummer", "rnc"),
    },
    "CCSS_PLANILLA": {  # 🇨🇷 Costa Rica
        "expected_country": "CR",
        "endpoint_path": "/cr/ccss",
        "agency": "CCSS",
        "doc_field": "cedula",
        "doc_label": "Cédula",
        "deductions": [
            ("CCSS Trabajador 10.67%", "sfs_employee"),
            ("Renta", "isr"),
        ],
        "employer": [
            ("CCSS Patronal 26.67%", "sfs_employer"),
            ("INA/IMAS/Banco Pop.", "infotep_employer"),
            ("INS Riesgos Trabajo", "srl_employer"),
        ],
        "extra_company_field": ("Cédula Jurídica", "rnc"),
    },
    "F1_ISSS": {  # 🇸🇻 El Salvador
        "expected_country": "SV",
        "endpoint_path": "/sv/f1-isss",
        "agency": "ISSS / AFP",
        "doc_field": "dui",
        "doc_label": "DUI / NIT",
        "deductions": [
            ("ISSS 3%", "sfs_employee"),
            ("AFP 7.25%", "afp_employee"),
            ("Renta", "isr"),
        ],
        "employer": [
            ("ISSS Patronal 7.5%", "sfs_employer"),
            ("AFP Patronal 8.75%", "afp_employer"),
            ("INSAFORP 1%", "infotep_employer"),
        ],
        "extra_company_field": ("NIT Empresa", "rnc"),
    },
    "IGSS_PLANILLA": {  # 🇬🇹 Guatemala
        "expected_country": "GT",
        "endpoint_path": "/gt/igss",
        "agency": "IGSS",
        "doc_field": "dpi",
        "doc_label": "DPI",
        "deductions": [
            ("IGSS Trabajador 4.83%", "sfs_employee"),
            ("ISR", "isr"),
        ],
        "employer": [
            ("IGSS Patronal 10.67%", "sfs_employer"),
            ("IRTRA 1%", "infotep_employer"),
            ("INTECAP 1%", "srl_employer"),
        ],
        "extra_company_field": ("NIT Patronal", "rnc"),
    },
    "IHSS_PLANILLA": {  # 🇭🇳 Honduras
        "expected_country": "HN",
        "endpoint_path": "/hn/ihss",
        "agency": "IHSS",
        "doc_field": "id_number",
        "doc_label": "Identidad",
        "deductions": [
            ("IHSS EM 2.5%", "sfs_employee"),
            ("IHSS IVM 2.5%", "afp_employee"),
            ("RAP", "srl_employee"),
            ("ISR", "isr"),
        ],
        "employer": [
            ("IHSS EM Patronal 5%", "sfs_employer"),
            ("IHSS IVM Patronal 3.5%", "afp_employer"),
            ("RAP Patronal 1.5%", "srl_employer"),
            ("INFOP 1%", "infotep_employer"),
        ],
        "extra_company_field": ("RTN Empresa", "rnc"),
    },
    "INSS_PLANILLA": {  # 🇳🇮 Nicaragua
        "expected_country": "NI",
        "endpoint_path": "/ni/inss",
        "agency": "INSS",
        "doc_field": "cedula",
        "doc_label": "Cédula",
        "deductions": [
            ("INSS Laboral 7%", "sfs_employee"),
            ("IR", "isr"),
        ],
        "employer": [
            ("INSS Patronal 22.5%", "sfs_employer"),
            ("INATEC 2%", "infotep_employer"),
        ],
        "extra_company_field": ("RUC", "rnc"),
    },
    "CSS_PLANILLA": {  # 🇵🇦 Panamá
        "expected_country": "PA",
        "endpoint_path": "/pa/css",
        "agency": "CSS",
        "doc_field": "cedula",
        "doc_label": "Cédula",
        "deductions": [
            ("CSS Trabajador 9.75%", "sfs_employee"),
            ("Seguro Educativo 1.25%", "infotep_employee"),
            ("ISR", "isr"),
        ],
        "employer": [
            ("CSS Patronal 12.25%", "sfs_employer"),
            ("Seguro Educativo Pat. 1.5%", "infotep_employer"),
            ("Riesgos Profesionales", "srl_employer"),
        ],
        "extra_company_field": ("RUC", "rnc"),
    },
    "ONAT_FORM": {  # 🇨🇺 Cuba
        "expected_country": "CU",
        "endpoint_path": "/cu/onat",
        "agency": "ONAT",
        "doc_field": "ci",
        "doc_label": "CI",
        "deductions": [
            ("Contribución Especial Trabajador 5%", "sfs_employee"),
            ("Impuesto Ingresos Personales", "isr"),
        ],
        "employer": [
            ("Contribución Empleador 14%", "sfs_employer"),
            ("Fuerza de Trabajo 5%", "infotep_employer"),
        ],
        "extra_company_field": ("Reeup", "rnc"),
    },
    "ONA_DECLAR": {  # 🇭🇹 Haití
        "expected_country": "HT",
        "endpoint_path": "/ht/ona",
        "agency": "ONA / DGI",
        "doc_field": "nif",
        "doc_label": "NIF",
        "deductions": [
            ("ONA Travailleur 6%", "afp_employee"),
            ("OFATMA 3%", "sfs_employee"),
            ("Impôt sur Salaire", "isr"),
        ],
        "employer": [
            ("ONA Patronal 6%", "afp_employer"),
            ("OFATMA Patronal 3%", "sfs_employer"),
        ],
        "extra_company_field": ("NIF Entreprise", "rnc"),
    },
}


# ===================== GENERIC CSV BUILDER =====================

def _entry_value(entry: dict, slot: str) -> float:
    """Lookup a slot from a payroll entry, with safe fallbacks."""
    if slot is None:
        return 0.0
    return float(entry.get(slot, 0) or 0)


async def _generate_planilla_csv(
    company_id: str,
    period: str,
    expected_country: str,
    format_code: str,
):
    """Build an agency-tailored CSV from a ``PLANILLA_COLUMN_PROFILES`` entry."""
    profile_cfg = PLANILLA_COLUMN_PROFILES.get(format_code)
    if not profile_cfg:
        raise HTTPException(status_code=400, detail=f"Formato {format_code} no soportado")

    await require_country(company_id, expected_country, profile_cfg["agency"])

    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    entries, emps, _ = await _collect_period_data(company_id, period)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No hay datos de nómina para {period}")

    country_profile = COUNTRY_PROFILES.get(expected_country, {})
    company_name = company.get("company_name") or company.get("name") or "EMPRESA"
    period_str = period.replace("-", "")[:6]
    extra_label, extra_field = profile_cfg["extra_company_field"]
    extra_value = company.get(extra_field) or company.get("tax_id") or ""

    output = io.StringIO()
    output.write("\ufeff")  # UTF-8 BOM for Excel
    writer = _csv.writer(output, delimiter=";")

    writer.writerow([
        f"# {country_profile.get('flag', '')} {country_profile.get('name', expected_country)} — "
        f"{profile_cfg['agency']} Planilla {format_code}"
    ])
    writer.writerow([f"# Empresa: {company_name}", f"{extra_label}: {extra_value}", f"Período: {period}"])
    writer.writerow([
        f"# Generado por FortexaRH — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    ])
    writer.writerow([])

    headers = [
        "#",
        profile_cfg["doc_label"],
        "Apellidos",
        "Nombres",
        "Días",
        f"Sueldo Bruto ({country_profile.get('currency', '')})",
    ]
    headers += [d[0] for d in profile_cfg["deductions"]]
    headers += [e[0] for e in profile_cfg["employer"]]
    headers += [
        f"Total Aportes ({country_profile.get('currency', '')})",
        f"Sueldo Neto ({country_profile.get('currency', '')})",
    ]
    writer.writerow(headers)

    total_gross = 0.0
    total_net = 0.0
    total_aportes = 0.0
    for idx, entry in enumerate(entries, 1):
        emp = emps.get(entry.get("employee_id"), {})
        last_name = (emp.get("last_name") or "").upper()
        first_name = (emp.get("first_name") or "").upper()
        doc = (
            emp.get(profile_cfg["doc_field"])
            or emp.get("document_number")
            or emp.get("national_id")
            or ""
        )
        gross = float(entry.get("gross_salary", 0) or 0)
        net = float(entry.get("net_salary", 0) or gross)
        days = int(entry.get("days_worked", 30) or 30)

        row = [str(idx), str(doc), last_name, first_name, str(days), f"{gross:.2f}"]
        cot_total = 0.0
        for _label, slot in profile_cfg["deductions"]:
            v = _entry_value(entry, slot)
            row.append(f"{v:.2f}")
            cot_total += v
        for _label, slot in profile_cfg["employer"]:
            v = _entry_value(entry, slot)
            row.append(f"{v:.2f}")
            cot_total += v
        row.append(f"{cot_total:.2f}")
        row.append(f"{net:.2f}")
        writer.writerow(row)

        total_gross += gross
        total_net += net
        total_aportes += cot_total

    writer.writerow([])
    writer.writerow([
        "TOTALES", "", f"# trabajadores: {len(entries)}", "", "", f"{total_gross:.2f}",
    ] + [""] * (len(profile_cfg["deductions"]) + len(profile_cfg["employer"])) + [
        f"{total_aportes:.2f}",
        f"{total_net:.2f}",
    ])

    content = output.getvalue()
    output.close()

    safe_id = "".join(c for c in str(extra_value) if c.isalnum()) or "EMPRESA"
    filename = f"{format_code}_{safe_id}_{period_str}.csv"
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ===================== AUTO-REGISTER ENDPOINTS =====================
#
# Iterate ``PLANILLA_COLUMN_PROFILES`` and register one FastAPI route per
# country. Each route is a tiny closure that injects its ``format_code`` and
# ``expected_country`` into the shared ``_generate_planilla_csv`` helper.
#
# Default-arg trick (``_format_code=...``, ``_cc=...``) is intentional: it
# captures by VALUE so the closure does not late-bind to the loop variable.

def _make_handler(format_code: str, expected_country: str, agency: str):
    async def _handler(  # noqa: D401
        period: str,
        current_user: dict = Depends(get_current_user),
        _fc: str = format_code,
        _cc: str = expected_country,
    ):
        return await _generate_planilla_csv(
            current_user.get("company_id"), period, _cc, _fc,
        )

    _handler.__name__ = f"generate_{format_code.lower()}"
    _handler.__doc__ = (
        f"{agency} ({expected_country}) — auto-registered planilla CSV "
        f"(format_code={format_code})."
    )
    return _handler


for _format_code, _cfg in PLANILLA_COLUMN_PROFILES.items():
    router.get(
        _cfg["endpoint_path"],
        name=f"native_{_format_code.lower()}",
        summary=f"{_cfg['agency']} ({_cfg['expected_country']}) Planilla CSV",
    )(_make_handler(_format_code, _cfg["expected_country"], _cfg["agency"]))

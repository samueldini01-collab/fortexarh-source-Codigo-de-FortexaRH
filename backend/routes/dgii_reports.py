"""
DGII Reports Routes - FortexaRH
Handles Dominican Republic tax reporting (TSS, IR-3, IR-17, IR-4, IR-13).
Multi-country: /summary adapts to company country; DR-specific formats (TXT) gated.
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import io
import csv

from routes.country_config import get_company_rates_flat, COUNTRY_PROFILES

router = APIRouter(prefix="/dgii-reports", tags=["DGII Reports"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


# Dominican Republic Tax Rates (kept as fallback / for DR-specific files)
TSS_RATES = {
    "afp_employee": 0.0287,      # 2.87% AFP Empleado
    "afp_employer": 0.0710,      # 7.10% AFP Patronal
    "sfs_employee": 0.0304,      # 3.04% SFS Empleado
    "sfs_employer": 0.0709,      # 7.09% SFS Patronal
    "risk_employer": 0.0110,     # 1.10% Riesgo Laboral
    "infotep": 0.01,             # 1% INFOTEP
}

# ISR Tax Brackets 2024 (DR)
ISR_BRACKETS = [
    {"min": 0, "max": 416220.00, "rate": 0, "base": 0},
    {"min": 416220.01, "max": 624329.00, "rate": 0.15, "base": 0},
    {"min": 624329.01, "max": 867123.00, "rate": 0.20, "base": 31216.35},
    {"min": 867123.01, "max": float("inf"), "rate": 0.25, "base": 79775.15},
]


from models.system import DGIIReportRequest as ReportRequest


async def _require_dr(company_id: str, report_name: str = "Este reporte"):
    """Guard: raise 400 if company's country is not DR (DGII/TSS files are DR-specific)."""
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "country": 1})
    country_code = (company or {}).get("country", "DO")
    if country_code != "DO":
        profile = COUNTRY_PROFILES.get(country_code, {})
        raise HTTPException(
            status_code=400,
            detail=f"{report_name} es específico de República Dominicana (DGII/TSS). "
                   f"Su empresa está configurada como {profile.get('name', country_code)}. "
                   f"Use /api/dgii-reports/summary para ver totales de impuestos adaptables al motor fiscal de su país."
        )
    return country_code


def calculate_isr(annual_income: float) -> float:
    """Calculate ISR based on annual income"""
    for bracket in ISR_BRACKETS:
        if bracket["min"] <= annual_income <= bracket["max"]:
            if bracket["rate"] == 0:
                return 0
            excess = annual_income - bracket["min"]
            return bracket["base"] + (excess * bracket["rate"])
    return 0


@router.get("/summary")
async def get_dgii_summary(period: str, current_user: dict = Depends(get_current_user)):
    """Get summary of tax obligations for a period.
    Multi-country: uses country-specific SS rates from company profile.
    For DR: TSS (SFS/AFP/SRL/INFOTEP). For other countries: mapped labels."""
    company_id = current_user.get("company_id")
    rates = await get_company_rates_flat(company_id)

    # Get employees with payroll for the period
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(1000)

    total_salaries = sum(e.get("salary", 0) for e in employees)
    employee_count = len(employees)

    # Country-specific SS contributions
    sfs_employee = total_salaries * rates["sfs_employee_rate"]
    afp_employee = total_salaries * rates["afp_employee_rate"]
    sfs_employer = total_salaries * rates["sfs_employer_rate"]
    afp_employer = total_salaries * rates["afp_employer_rate"]
    risk_labor = total_salaries * rates["srl_employer_rate"]
    infotep = total_salaries * rates["infotep_employer_rate"]

    # Get payroll entries for ISR calculation
    payroll_entries = await db.payroll_entries.find(
        {"company_id": company_id, "period_id": {"$regex": period.replace("-", "")}},
        {"_id": 0}
    ).to_list(1000)

    total_isr = sum(e.get("isr", 0) for e in payroll_entries)

    # Country-specific report types available
    country_profile = COUNTRY_PROFILES.get(rates["country_code"], {})
    available_reports = country_profile.get("reports", [])

    return {
        "period": period,
        "employee_count": employee_count,
        "total_salaries": round(total_salaries, 2),
        "country_code": rates["country_code"],
        "country_name": rates["country_name"],
        "currency": rates["currency"],
        "currency_symbol": rates["currency_symbol"],
        "labels": rates["labels"],
        "codes": rates["codes"],
        "available_reports": available_reports,
        "tss": {
            "afp_employee": round(afp_employee, 2),
            "afp_employer": round(afp_employer, 2),
            "afp_total": round(afp_employee + afp_employer, 2),
            "sfs_employee": round(sfs_employee, 2),
            "sfs_employer": round(sfs_employer, 2),
            "sfs_total": round(sfs_employee + sfs_employer, 2),
            "risk_labor": round(risk_labor, 2),
            "infotep": round(infotep, 2),
            "total_tss": round(afp_employee + afp_employer + sfs_employee + sfs_employer + risk_labor + infotep, 2),
            # Full details from country profile (for future UI table)
            "employee_deductions_detail": [
                {"code": d["code"], "name": d["name"], "rate": d["rate"], "amount": round(total_salaries * d["rate"], 2)}
                for d in rates.get("employee_deductions_detail", [])
            ],
            "employer_contributions_detail": [
                {"code": c["code"], "name": c["name"], "rate": c["rate"], "amount": round(total_salaries * c["rate"], 2)}
                for c in rates.get("employer_contributions_detail", [])
            ],
        },
        "isr": {
            "total_retained": round(total_isr, 2),
            "agency": country_profile.get("income_tax", {}).get("agency", ""),
        }
    }


@router.get("/tss/autodeterminacion")
async def generate_tss_autodeterminacion(period: str, current_user: dict = Depends(get_current_user)):
    """Generate TSS Autodeterminación file (Type A) - Dominican Republic only"""
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "TSS Autodeterminación")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).to_list(1000)
    
    # Generate file content
    output = io.StringIO()
    writer = csv.writer(output, delimiter='|')
    
    # Header
    rnc = company.get("rnc", "000000000")
    period_formatted = period.replace("-", "")
    
    for emp in employees:
        cedula = emp.get("document_number", "").replace("-", "")
        salary = emp.get("salary", 0)
        
        # Skip employees with deductions disabled
        afp_salary = salary if emp.get("afp_discount", True) else 0
        sfs_salary = salary if emp.get("sfs_discount", True) else 0
        
        writer.writerow([
            rnc,
            cedula,
            emp.get("first_name", ""),
            emp.get("last_name", ""),
            "N",  # Sexo
            round(afp_salary, 2),  # Salario cotizable AFP
            round(sfs_salary, 2),  # Salario cotizable SFS
            round(salary, 2),      # Salario cotizable Riesgo Laboral
            "01",  # Tipo de ingreso
            period_formatted
        ])
    
    content = output.getvalue()
    
    filename = f"TSS_AUTODETERMINACION_{rnc}_{period_formatted}.txt"
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/tss/novedades")
async def generate_tss_novedades(period: str, current_user: dict = Depends(get_current_user)):
    """Generate TSS Novedades file (Type N) - Dominican Republic only"""
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "TSS Novedades")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    rnc = company.get("rnc", "000000000")
    period_formatted = period.replace("-", "")
    
    # Get employees with changes in the period
    # This would typically query for hiring, terminations, salary changes, etc.
    novedades = []
    
    # For now, return empty file structure
    output = io.StringIO()
    writer = csv.writer(output, delimiter='|')
    
    for novedad in novedades:
        writer.writerow([
            rnc,
            novedad.get("cedula"),
            novedad.get("tipo_novedad"),
            novedad.get("fecha"),
            period_formatted
        ])
    
    content = output.getvalue()
    filename = f"TSS_NOVEDADES_{rnc}_{period_formatted}.txt"
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/ir3")
async def generate_ir3(period: str, current_user: dict = Depends(get_current_user)):
    """Generate IR-3 (Monthly ISR Withholdings) report - Dominican Republic only"""
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "IR-3")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Get payroll entries for the period
    payroll_entries = await db.payroll_entries.find(
        {"company_id": company_id, "period_id": {"$regex": period.replace("-", "")}},
        {"_id": 0}
    ).to_list(1000)
    
    # Generate IR-3 data
    output = io.StringIO()
    writer = csv.writer(output, delimiter='|')
    
    rnc = company.get("rnc", "000000000")
    period_formatted = period.replace("-", "")
    
    # Header
    writer.writerow(["RNC", "PERIODO", "TIPO_RETENCION", "MONTO_PAGADO", "MONTO_RETENIDO"])
    
    total_salaries = sum(e.get("gross_pay", 0) for e in payroll_entries)
    total_isr = sum(e.get("isr", 0) for e in payroll_entries)
    
    writer.writerow([
        rnc,
        period_formatted,
        "01",  # Salarios
        round(total_salaries, 2),
        round(total_isr, 2)
    ])
    
    content = output.getvalue()
    filename = f"IR3_{rnc}_{period_formatted}.txt"
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/ir17")
async def generate_ir17(year: int, current_user: dict = Depends(get_current_user)):
    """Generate IR-17 (Annual Employee Compensation) report - Dominican Republic only"""
    company_id = current_user.get("company_id")
    await _require_dr(company_id, "IR-17")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    employees = await db.employees.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='|')
    
    rnc = company.get("rnc", "000000000")
    
    # Header
    writer.writerow([
        "RNC_CEDULA", "NOMBRE", "SALARIO_ANUAL", "OTROS_INGRESOS",
        "TOTAL_INGRESOS", "AFP_RETENIDO", "SFS_RETENIDO", "ISR_RETENIDO"
    ])
    
    for emp in employees:
        annual_salary = emp.get("salary", 0) * 12
        afp_annual = annual_salary * TSS_RATES["afp_employee"]
        sfs_annual = annual_salary * TSS_RATES["sfs_employee"]
        isr_annual = calculate_isr(annual_salary)
        
        writer.writerow([
            emp.get("document_number", ""),
            f"{emp.get('first_name', '')} {emp.get('last_name', '')}",
            round(annual_salary, 2),
            0,  # Otros ingresos
            round(annual_salary, 2),
            round(afp_annual, 2),
            round(sfs_annual, 2),
            round(isr_annual, 2)
        ])
    
    content = output.getvalue()
    filename = f"IR17_{rnc}_{year}.txt"
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/deadlines")
async def get_dgii_deadlines(current_user: dict = Depends(get_current_user)):
    """Get upcoming DGII reporting deadlines"""
    now = datetime.now(timezone.utc)
    current_month = now.month
    current_year = now.year
    
    deadlines = []
    
    # TSS - Due on the 3rd of each month
    tss_due = datetime(current_year, current_month + 1 if current_month < 12 else 1, 3)
    if current_month == 12:
        tss_due = datetime(current_year + 1, 1, 3)
    
    deadlines.append({
        "report": "TSS (Autodeterminación)",
        "period": f"{current_year}-{current_month:02d}",
        "due_date": tss_due.strftime("%Y-%m-%d"),
        "days_remaining": (tss_due - now.replace(tzinfo=None)).days
    })
    
    # IR-3 - Due on the 10th of each month
    ir3_due = datetime(current_year, current_month + 1 if current_month < 12 else 1, 10)
    if current_month == 12:
        ir3_due = datetime(current_year + 1, 1, 10)
    
    deadlines.append({
        "report": "IR-3 (Retenciones ISR)",
        "period": f"{current_year}-{current_month:02d}",
        "due_date": ir3_due.strftime("%Y-%m-%d"),
        "days_remaining": (ir3_due - now.replace(tzinfo=None)).days
    })
    
    # IR-17 - Due February 28th
    if current_month <= 2:
        ir17_due = datetime(current_year, 2, 28)
        deadlines.append({
            "report": "IR-17 (Compensaciones Anuales)",
            "period": str(current_year - 1),
            "due_date": ir17_due.strftime("%Y-%m-%d"),
            "days_remaining": (ir17_due - now.replace(tzinfo=None)).days
        })
    
    return sorted(deadlines, key=lambda x: x["days_remaining"])

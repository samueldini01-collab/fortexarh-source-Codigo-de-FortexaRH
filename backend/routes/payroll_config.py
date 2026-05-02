"""
Payroll Configuration Routes - FortexaRH
Handles payroll settings, payroll config CRUD, payroll calculator, and saved calculations.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

from utils.payroll_constants import (
    SFS_EMPLOYEE_RATE, AFP_EMPLOYEE_RATE,
    SFS_EMPLOYER_RATE, AFP_EMPLOYER_RATE, SRL_EMPLOYER_RATE, INFOTEP_EMPLOYER_RATE,
    calculate_isr_monthly,
)
from routes.country_config import (
    COUNTRY_PROFILES,
    calculate_isr_dynamic,
    get_company_rates_flat,
)

router = APIRouter(tags=["Payroll Config"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


# ===================== MODELS =====================
from models.payroll import (
    PayrollSettingsModel, PayrollConfigCreate,
    PayrollCalculatorInput, PayrollCalculatorResult
)


# ===================== PAYROLL SETTINGS =====================

@router.get("/payroll-settings")
async def get_payroll_settings(current_user: dict = Depends(get_current_user)):
    settings = await db.payroll_settings.find_one(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    return settings


@router.post("/payroll-settings")
async def save_payroll_settings(data: PayrollSettingsModel, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    settings = {
        "company_id": company_id,
        **data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.get("user_id")
    }
    await db.payroll_settings.update_one(
        {"company_id": company_id},
        {"$set": settings},
        upsert=True
    )
    return {"message": "Configuracion guardada correctamente"}


# ===================== PAYROLL CONFIG CRUD =====================

@router.get("/payroll-config")
async def get_payroll_configs(current_user: dict = Depends(get_current_user)):
    configs = await db.payroll_configs.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return configs


@router.post("/payroll-config")
async def create_payroll_config(data: PayrollConfigCreate, current_user: dict = Depends(get_current_user)):
    config_id = f"pconfig_{uuid.uuid4().hex[:12]}"
    config = {
        "config_id": config_id,
        "company_id": current_user.get("company_id"),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payroll_configs.insert_one(config)
    return {"config_id": config_id, "message": "Configuracion creada correctamente"}


@router.put("/payroll-config/{config_id}")
async def update_payroll_config(config_id: str, data: PayrollConfigCreate, current_user: dict = Depends(get_current_user)):
    result = await db.payroll_configs.update_one(
        {"config_id": config_id, "company_id": current_user.get("company_id")},
        {"$set": data.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Configuracion no encontrada")
    return {"message": "Configuracion actualizada correctamente"}


@router.delete("/payroll-config/{config_id}")
async def delete_payroll_config(config_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.payroll_configs.delete_one(
        {"config_id": config_id, "company_id": current_user.get("company_id")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuracion no encontrada")
    return {"message": "Configuracion eliminada correctamente"}


# ===================== PAYROLL CALCULATOR =====================

@router.post("/payroll-calculator")
async def calculate_payroll(data: PayrollCalculatorInput, current_user: dict = Depends(get_current_user)):
    # ===== iter246: DYNAMIC COUNTRY CONFIGURATION =====
    # Look up the company's country and use its rates/ISR/labels instead of
    # hardcoding DR values. Falls back to DR constants when country=='DO' or
    # when no country is configured (legacy behaviour preserved).
    company_id = current_user.get("company_id")
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0}) or {}
    country_code = (company.get("country") or "DO").upper()
    profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES.get("DO", {}))

    # Dynamic rates from country_config (overrides applied via settings). The
    # flat dict exposes sfs/afp/srl/infotep for every country with matching
    # semantics (health/pension/risk/training).
    rates = await get_company_rates_flat(company_id)
    sfs_emp_rate = rates.get("sfs_employee_rate", SFS_EMPLOYEE_RATE)
    afp_emp_rate = rates.get("afp_employee_rate", AFP_EMPLOYEE_RATE)
    sfs_er_rate = rates.get("sfs_employer_rate", SFS_EMPLOYER_RATE)
    afp_er_rate = rates.get("afp_employer_rate", AFP_EMPLOYER_RATE)
    srl_er_rate = rates.get("srl_employer_rate", SRL_EMPLOYER_RATE)
    infotep_er_rate = rates.get("infotep_employer_rate", INFOTEP_EMPLOYER_RATE)

    # Friendly labels for the frontend — each country's social-security system
    # has its own terminology (NIS in Guyana, AFORE in Mexico, etc.).
    ss = profile.get("social_security") or {}
    emp_deds = ss.get("employee_deductions") or []
    er_cons = ss.get("employer_contributions") or []

    # Canonical code buckets per slot. Profiles are searched first by known
    # code aliases; if nothing matches we fall back to positional index (safe
    # because all COUNTRY_PROFILES entries today follow the health-then-pension
    # ordering, but the code-lookup makes a future reorder a non-event).
    _HEALTH_CODES = {"SFS", "HEALTH", "SALUD", "IMSS", "CCSS", "IHSS",
                      "INSS", "IGSS", "ISSS", "IVSS", "IPS", "CNS", "EsSalud",
                      "FONASA", "NIS", "NHIF", "ZIEKTEKOSTEN", "OFATMA"}
    _PENSION_CODES = {"AFP", "PENSION", "PENSIÓN", "AFORE", "ONP", "AFC",
                       "IVM", "RAP", "JUBILATORIO", "AOV", "ONA"}
    _RISK_CODES = {"SRL", "ART", "SCTR", "ARL", "INS", "RIESGOS"}
    _TRAINING_CODES = {"INFOTEP", "INA", "INSAFORP", "INATEC", "IECE", "INTECAP",
                         "INFOP", "IRTRA", "SEGURO EDUCATIVO"}

    def _label_for(items, buckets, positional_idx, default):
        # First pass: lookup by code/label aliases.
        for it in items or []:
            code = (it.get("code") or "").upper()
            label = (it.get("label") or it.get("name") or "").upper()
            if any(b in code or b in label for b in buckets):
                return it.get("label") or it.get("name") or it.get("code") or default
        # Fallback to positional index.
        try:
            return items[positional_idx].get("label") or items[positional_idx].get("name") or items[positional_idx].get("code") or default
        except (IndexError, AttributeError):
            return default

    labels = {
        "sfs_employee": _label_for(emp_deds, _HEALTH_CODES, 0, "Seguro Salud"),
        "afp_employee": _label_for(emp_deds, _PENSION_CODES, 1, "Pensión"),
        "sfs_employer": _label_for(er_cons, _HEALTH_CODES, 0, "Seguro Salud (Patronal)"),
        "afp_employer": _label_for(er_cons, _PENSION_CODES, 1, "Pensión (Patronal)"),
        "srl_employer": _label_for(er_cons, _RISK_CODES, 2, "Riesgos Laborales"),
        "infotep_employer": _label_for(er_cons, _TRAINING_CODES, 3, "Capacitación / Otros"),
        "isr_agency": (profile.get("income_tax") or {}).get("agency", "DGII"),
    }

    # Observability: log a warning when the company's country is not recognized
    # so misconfigured tenants surface instead of silently getting DR rates.
    if country_code not in COUNTRY_PROFILES:
        import logging
        logging.getLogger(__name__).warning(
            "payroll-calculator: unknown company country %r — falling back to DR rates",
            country_code,
        )

    daily_rate = data.base_salary / 30
    proportional_salary = daily_rate * data.days_worked
    extra_hours_pay = data.hours_extra * data.hour_rate
    total_earnings = proportional_salary + extra_hours_pay + data.bonuses + data.commissions

    sfs_employee = round(total_earnings * sfs_emp_rate, 2)
    afp_employee = round(total_earnings * afp_emp_rate, 2)
    total_tss_employee = round(sfs_employee + afp_employee, 2)

    # DR uses the precise DGII interpolation table. Other countries use
    # the dynamic bracket calculator driven by country_config's income_tax.
    if country_code == "DO":
        isr_result = calculate_isr_monthly(total_earnings)
    else:
        isr_result = calculate_isr_dynamic(total_earnings, profile.get("income_tax") or {})
    isr_monthly = isr_result["isr_monthly"]

    total_employee_deductions = round(total_tss_employee + isr_monthly, 2)
    total_other_deductions = round(data.loan_deduction + data.other_deductions, 2)
    total_deductions = round(total_employee_deductions + total_other_deductions, 2)
    net_salary = round(total_earnings - total_deductions, 2)

    sfs_employer = round(total_earnings * sfs_er_rate, 2)
    afp_employer = round(total_earnings * afp_er_rate, 2)
    srl_employer = round(total_earnings * srl_er_rate, 2)
    infotep_employer = round(total_earnings * infotep_er_rate, 2)
    total_tss_employer = round(sfs_employer + afp_employer, 2)
    total_employer_contributions = round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2)
    total_cost_employer = round(total_earnings + total_employer_contributions, 2)

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
        total_tss_employer=total_tss_employer,
        total_cost_employer=total_cost_employer,
        total_employer_contributions=total_employer_contributions,
        breakdown={
            "country_code": country_code,
            "country_name": profile.get("name", country_code),
            "currency": profile.get("currency", "DOP"),
            "currency_symbol": profile.get("currency_symbol", "RD$"),
            "flag": profile.get("flag", ""),
            "labels": labels,
            "rates_applied": {
                "sfs_employee": sfs_emp_rate,
                "afp_employee": afp_emp_rate,
                "sfs_employer": sfs_er_rate,
                "afp_employer": afp_er_rate,
                "srl_employer": srl_er_rate,
                "infotep_employer": infotep_er_rate,
            },
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


@router.post("/payroll-calculator/save")
async def save_payroll_calculation(data: PayrollCalculatorInput, current_user: dict = Depends(get_current_user)):
    daily_rate = data.base_salary / 30
    proportional_salary = daily_rate * data.days_worked
    extra_hours_pay = data.hours_extra * data.hour_rate
    total_earnings = proportional_salary + extra_hours_pay + data.bonuses + data.commissions

    sfs_employee = round(total_earnings * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(total_earnings * AFP_EMPLOYEE_RATE, 2)
    total_tss_employee = sfs_employee + afp_employee

    isr_result = calculate_isr_monthly(total_earnings)
    isr_monthly = isr_result["isr_monthly"]

    total_employee_deductions = round(total_tss_employee + isr_monthly, 2)
    total_other_deductions = data.loan_deduction + data.other_deductions
    total_deductions = round(total_employee_deductions + total_other_deductions, 2)
    net_salary = round(total_earnings - total_deductions, 2)

    employee_name = data.employee_name or "Sin asignar"
    if data.employee_id:
        employee = await db.employees.find_one(
            {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
            {"_id": 0}
        )
        if employee:
            employee_name = f"{employee['first_name']} {employee['last_name']}"

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
    return {"calculation_id": calc_id, "message": "Calculo guardado correctamente", "net_salary": net_salary}


@router.get("/payroll-calculations")
async def get_payroll_calculations(current_user: dict = Depends(get_current_user)):
    calculations = await db.payroll_calculations.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return calculations

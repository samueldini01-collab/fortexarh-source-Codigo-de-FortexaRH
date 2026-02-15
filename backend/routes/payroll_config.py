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

router = APIRouter(tags=["Payroll Config"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


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
    daily_rate = data.base_salary / 30
    proportional_salary = daily_rate * data.days_worked
    extra_hours_pay = data.hours_extra * data.hour_rate
    total_earnings = proportional_salary + extra_hours_pay + data.bonuses + data.commissions

    sfs_employee = round(total_earnings * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(total_earnings * AFP_EMPLOYEE_RATE, 2)
    total_tss_employee = round(sfs_employee + afp_employee, 2)

    isr_result = calculate_isr_monthly(total_earnings)
    isr_monthly = isr_result["isr_monthly"]

    total_employee_deductions = round(total_tss_employee + isr_monthly, 2)
    total_other_deductions = round(data.loan_deduction + data.other_deductions, 2)
    total_deductions = round(total_employee_deductions + total_other_deductions, 2)
    net_salary = round(total_earnings - total_deductions, 2)

    sfs_employer = round(total_earnings * SFS_EMPLOYER_RATE, 2)
    afp_employer = round(total_earnings * AFP_EMPLOYER_RATE, 2)
    srl_employer = round(total_earnings * SRL_EMPLOYER_RATE, 2)
    infotep_employer = round(total_earnings * INFOTEP_EMPLOYER_RATE, 2)
    total_employer_contributions = round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2)

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
        total_employer_contributions=total_employer_contributions,
        breakdown={
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

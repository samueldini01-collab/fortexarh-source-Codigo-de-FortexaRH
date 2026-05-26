"""Auto-generated module from the iter243 split of routes/payroll/core.py.

Do not add new logic here without updating the integration test suite at
``/app/backend/tests/test_payroll_routes_integration.py``.
"""
from __future__ import annotations

import io
import csv
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from config import db
from models.payroll import ApprovalRequest, PaymentRequest, PayrollEntryCreate
from routes.country_config import calculate_isr_dynamic, get_company_rates_flat
from routes.fortexaerp import auto_sync_to_erp
from services.employee_notifications import create_employee_notification
from services.journal_entry_service import (
    delete_payroll_journal_entry,
    generate_payroll_journal_entry,
)
from services.push_service import send_push_to_user
from utils.auth import get_current_user
from utils.payroll_constants import (
    ISR_OBREROS_RATE,
    PAYROLL_NOVELTY_TYPES,
    PAYROLL_TYPES,
    PayrollNoveltyCreate,
    PayrollPaymentRequest,
    PayrollPeriodCreateV2,
    calculate_isr_monthly,
    generate_id,
    now_iso,
)

from . import router
from ._helpers import _compute_isr, period_scaling_factor, update_period_totals


@router.get("/entries/{entry_id}")
async def get_payroll_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific payroll entry"""
    company_id = current_user.get("company_id")
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    return entry


@router.put("/entries/{entry_id}")
async def update_payroll_entry(entry_id: str, data: PayrollEntryCreate, current_user: dict = Depends(get_current_user)):
    """Update a payroll entry"""
    company_id = current_user.get("company_id")
    
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    period = await db.payroll_periods.find_one(
        {"period_id": entry["period_id"], "company_id": company_id},
        {"_id": 0}
    )
    if period and period.get("status") == "paid":
        raise HTTPException(status_code=400, detail="No se puede modificar una nómina pagada")

    # Fetch country-specific rates
    rates = await get_company_rates_flat(company_id)
    working_days_month = rates.get("working_days_month") or 23.83
    hourly_rate = data.base_salary / working_days_month / 8
    
    overtime_day_amount = round(data.overtime_day_hours * hourly_rate * (1 + data.overtime_day_rate/100), 2)
    overtime_night_amount = round(data.overtime_night_hours * hourly_rate * (1 + data.overtime_night_rate/100), 2)
    overtime_weekend_amount = round(data.overtime_weekend_hours * hourly_rate * (1 + data.overtime_weekend_rate/100), 2)
    overtime_holiday_amount = round(data.overtime_holiday_hours * hourly_rate * (1 + data.overtime_holiday_rate/100), 2)
    
    # If overtime override provided, distribute to day_amount for simplicity
    if data.overtime_override is not None:
        overtime_day_amount = round(data.overtime_override, 2)
        overtime_night_amount = 0
        overtime_weekend_amount = 0
        overtime_holiday_amount = 0
    
    gross_salary = data.base_salary + overtime_day_amount + overtime_night_amount + overtime_weekend_amount + overtime_holiday_amount + data.bonuses + data.commissions + data.other_income
    
    # Get employee data for manual override settings
    emp = await db.employees.find_one(
        {"employee_id": entry["employee_id"], "company_id": company_id},
        {"_id": 0, "sfs_discount": 1, "afp_discount": 1, "isr_discount": 1,
         "sfs_manual_override": 1, "sfs_manual_amount": 1,
         "afp_manual_override": 1, "afp_manual_amount": 1,
         "isr_manual_override": 1, "isr_manual_amount": 1}
    ) or {}

    # Manual overrides on the employee profile are MONTHLY → scale to period
    scale = period_scaling_factor((period or {}).get("period_type"))

    # SFS: respect inline override first, then employee override, then calculation
    if data.sfs_override is not None:
        sfs_employee = round(data.sfs_override, 2)
    elif emp.get("sfs_discount", True):
        sfs_employee = round(float(emp.get("sfs_manual_amount", 0)) * scale, 2) if emp.get("sfs_manual_override") else round(gross_salary * rates["sfs_employee_rate"], 2)
    else:
        sfs_employee = 0

    # AFP: respect inline override first, then employee override, then calculation
    if data.afp_override is not None:
        afp_employee = round(data.afp_override, 2)
    elif emp.get("afp_discount", True):
        afp_employee = round(float(emp.get("afp_manual_amount", 0)) * scale, 2) if emp.get("afp_manual_override") else round(gross_salary * rates["afp_employee_rate"], 2)
    else:
        afp_employee = 0

    # ISR: respect inline override first, then employee override, then calculation
    isr_result = await _compute_isr(company_id, gross_salary, rates, period_type=(period or {}).get("period_type"))
    if data.isr_override is not None:
        isr = round(data.isr_override, 2)
    elif emp.get("isr_discount", True):
        isr = round(float(emp.get("isr_manual_amount", 0)) * scale, 2) if emp.get("isr_manual_override") else isr_result["isr_monthly"]
    else:
        isr = 0
    
    total_additional = sum(d.get("amount", 0) for d in (data.additional_deductions or []) if not d.get("is_percentage"))
    for d in (data.additional_deductions or []):
        if d.get("is_percentage"):
            total_additional += round(gross_salary * d.get("amount", 0) / 100, 2)
    
    loan_deduction = entry.get("loan_deduction", 0)
    total_deductions = round(sfs_employee + afp_employee + isr + total_additional + loan_deduction, 2)
    net_salary = round(gross_salary - total_deductions, 2)
    
    sfs_employer = round(gross_salary * rates["sfs_employer_rate"], 2)
    afp_employer = round(gross_salary * rates["afp_employer_rate"], 2)
    srl_employer = round(gross_salary * rates["srl_employer_rate"], 2)
    infotep_employer = round(gross_salary * rates["infotep_employer_rate"], 2)
    
    update_data = {
        "base_salary": data.base_salary,
        "overtime_day_hours": data.overtime_day_hours,
        "overtime_day_rate": data.overtime_day_rate,
        "overtime_day_amount": overtime_day_amount,
        "overtime_night_hours": data.overtime_night_hours,
        "overtime_night_rate": data.overtime_night_rate,
        "overtime_night_amount": overtime_night_amount,
        "overtime_weekend_hours": data.overtime_weekend_hours,
        "overtime_weekend_rate": data.overtime_weekend_rate,
        "overtime_weekend_amount": overtime_weekend_amount,
        "overtime_holiday_hours": data.overtime_holiday_hours,
        "overtime_holiday_rate": data.overtime_holiday_rate,
        "overtime_holiday_amount": overtime_holiday_amount,
        "bonuses": data.bonuses,
        "commissions": data.commissions,
        "other_income": data.other_income,
        "gross_salary": round(gross_salary, 2),
        "sfs_employee": sfs_employee,
        "afp_employee": afp_employee,
        "isr": isr,
        "isr_manual_override_entry": data.isr_override is not None,
        "sfs_manual_override_entry": data.sfs_override is not None,
        "afp_manual_override_entry": data.afp_override is not None,
        "overtime_manual_override_entry": data.overtime_override is not None,
        "additional_deductions": data.additional_deductions or [],
        "total_additional_deductions": round(total_additional, 2),
        "total_deductions": total_deductions,
        "net_salary": net_salary,
        "sfs_employer": sfs_employer,
        "afp_employer": afp_employer,
        "srl_employer": srl_employer,
        "infotep_employer": infotep_employer,
        "total_employer_contributions": round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2),
        "updated_at": now_iso()
    }
    
    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    await update_period_totals(entry["period_id"], company_id)
    
    return {"message": "Entrada actualizada", "net_salary": net_salary}


@router.delete("/entries/{entry_id}")
async def delete_payroll_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a payroll entry"""
    company_id = current_user.get("company_id")
    
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    period = await db.payroll_periods.find_one(
        {"period_id": entry["period_id"], "company_id": company_id},
        {"_id": 0}
    )
    if period and period.get("status") in ["approved", "paid"]:
        raise HTTPException(status_code=400, detail="No se puede eliminar entrada de nómina aprobada/pagada")
    
    await db.payroll_entries.delete_one({"entry_id": entry_id, "company_id": company_id})
    await update_period_totals(entry["period_id"], company_id)
    
    return {"message": "Entrada eliminada"}


@router.post("/entries/{entry_id}/reset-from-profile")
async def reset_entry_from_profile(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Re-sync a payroll entry's profile-driven novelties with the employee's
    CURRENT profile state.

    Useful when HR updates the employee's ``additional_deductions`` (or the
    SFS/AFP/ISR manual overrides) after a draft period is already populated,
    and wants to refresh the entry without deleting and re-adding the
    employee.

    Behavior:
      - Removes any deduction novelty with ``source == "employee_profile"``.
      - Re-emits new novelties from the employee's current
        ``additional_deductions`` (mapped to codes, scaled by period type).
      - Re-applies SFS/AFP/ISR from the profile (manual override or auto).
      - Recomputes ``total_deduction_novelties`` and the entry totals.
      - Does NOT touch user-created novelties (commissions, bonuses,
        manual deductions added during payroll editing).
      - Blocked for ``paid``/``approved`` periods.
    """
    from uuid import uuid4

    company_id = current_user.get("company_id")
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0},
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")

    period = await db.payroll_periods.find_one(
        {"period_id": entry["period_id"], "company_id": company_id},
        {"_id": 0},
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    if period.get("status") in {"paid", "approved"}:
        raise HTTPException(status_code=400, detail="No se puede resetear una nómina aprobada/pagada")

    emp = await db.employees.find_one(
        {"employee_id": entry.get("employee_id"), "company_id": company_id},
        {"_id": 0},
    )
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    rates = await get_company_rates_flat(company_id)
    period_type = period.get("period_type")
    scale = period_scaling_factor(period_type)
    base_salary = entry.get("base_salary", 0) or 0

    DED_TYPE_TO_CODE = {
        "Préstamo Empresa": "PREST", "Préstamo Cooperativa": "COOP", "Cooperativa": "COOP",
        "Seguro Adicional": "SEG", "Pensión Alimenticia": "PENS", "Anticipo": "ANTIC",
        "Embargo": "EMB", "Tardanzas": "TARD", "Ausencias": "AUS",
        "Otro": "OTROSD", "Otros": "OTROSD",
    }
    CODE_TO_FULL = {
        "ANTIC": "Anticipo", "COOP": "Cooperativa", "SEG": "Seguro Adicional",
        "PENS": "Pensión Alimenticia", "EMB": "Embargo", "TARD": "Tardanzas",
        "AUS": "Ausencias", "OTROSD": "Otros Descuentos", "PREST": "Préstamo Empresa",
    }

    # 1) Strip existing profile-sourced novelties; keep user-created ones
    kept = [
        n for n in (entry.get("novelties") or [])
        if n.get("source") != "employee_profile"
    ]

    # 2) Re-emit deduction novelties from current profile state
    now_str = now_iso()
    fresh_profile_novelties = []
    for d in emp.get("additional_deductions", []) or []:
        code = DED_TYPE_TO_CODE.get(d.get("type"), "OTROSD")
        raw_amt = float(d.get("amount", 0) or 0)
        if d.get("is_percentage"):
            scaled_amt = raw_amt
        else:
            scaled_amt = round(raw_amt * scale, 2)
        fresh_profile_novelties.append({
            "novelty_id": str(uuid4())[:12],
            "novelty_type": "deduction",
            "code": code,
            "name": CODE_TO_FULL.get(code, d.get("type") or code),
            "description": d.get("description", "") or d.get("type", ""),
            "amount": scaled_amt,
            "is_percentage": bool(d.get("is_percentage")),
            "created_at": now_str,
            "created_by": current_user.get("user_id"),
            "source": "employee_profile",
        })

    new_novelties = kept + fresh_profile_novelties

    # 3) Recompute totals for income/deduction novelties
    inc_total = 0.0
    ded_total = 0.0
    for n in new_novelties:
        amt = n.get("amount", 0) or 0
        value = round(base_salary * amt / 100, 2) if n.get("is_percentage") else amt
        if n.get("novelty_type") == "income":
            inc_total += value
        else:
            ded_total += value

    # 4) Refresh SFS / AFP / ISR honoring profile overrides + manual override flags on entry
    overtime_total = (
        (entry.get("overtime_day_amount", 0) or 0)
        + (entry.get("overtime_night_amount", 0) or 0)
        + (entry.get("overtime_weekend_amount", 0) or 0)
        + (entry.get("overtime_holiday_amount", 0) or 0)
    )
    gross_salary = round(
        base_salary + overtime_total
        + (entry.get("bonuses", 0) or 0)
        + (entry.get("commissions", 0) or 0)
        + (entry.get("other_income", 0) or 0)
        + inc_total,
        2,
    )

    if entry.get("sfs_manual_override_entry"):
        sfs_employee = round(entry.get("sfs_employee", 0) or 0, 2)
    elif emp.get("sfs_discount", True):
        sfs_employee = (
            round(float(emp.get("sfs_manual_amount", 0)) * scale, 2)
            if emp.get("sfs_manual_override")
            else round(gross_salary * rates["sfs_employee_rate"], 2)
        )
    else:
        sfs_employee = 0

    if entry.get("afp_manual_override_entry"):
        afp_employee = round(entry.get("afp_employee", 0) or 0, 2)
    elif emp.get("afp_discount", True):
        afp_employee = (
            round(float(emp.get("afp_manual_amount", 0)) * scale, 2)
            if emp.get("afp_manual_override")
            else round(gross_salary * rates["afp_employee_rate"], 2)
        )
    else:
        afp_employee = 0

    if entry.get("isr_manual_override_entry"):
        isr = round(entry.get("isr", 0) or 0, 2)
    elif emp.get("isr_discount", True):
        if emp.get("isr_manual_override"):
            isr = round(float(emp.get("isr_manual_amount", 0)) * scale, 2)
        else:
            isr_result = await _compute_isr(company_id, gross_salary, rates, period_type=period_type)
            isr = isr_result["isr_monthly"]
    else:
        isr = 0

    loan_deduction = entry.get("loan_deduction", 0) or 0
    total_additional = 0.0  # legacy field, always 0 after migration

    total_deductions = round(
        sfs_employee + afp_employee + isr + total_additional + ded_total + loan_deduction,
        2,
    )
    net_salary = round(gross_salary - total_deductions, 2)

    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "novelties": new_novelties,
            "total_income_novelties": round(inc_total, 2),
            "total_deduction_novelties": round(ded_total, 2),
            "additional_deductions": [],
            "total_additional_deductions": 0.0,
            "gross_salary": gross_salary,
            "sfs_employee": sfs_employee,
            "afp_employee": afp_employee,
            "isr": isr,
            "total_deductions": total_deductions,
            "net_salary": net_salary,
            "updated_at": now_iso(),
        }},
    )
    await update_period_totals(entry["period_id"], company_id)

    return {
        "message": "Entrada re-sincronizada con el perfil del empleado",
        "novelties_added": len(fresh_profile_novelties),
        "novelties_kept": len(kept),
    }





# ===================== NOVELTY ENDPOINTS =====================





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
from ._helpers import _compute_isr, update_period_totals


@router.post("/entries/{entry_id}/novelties")
async def add_novelty(entry_id: str, data: PayrollNoveltyCreate, current_user: dict = Depends(get_current_user)):
    """Add a novelty to a payroll entry"""
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
    
    novelty_id = generate_id("nov")
    novelty = {
        "novelty_id": novelty_id,
        "novelty_type": data.novelty_type,
        "code": data.code,
        "name": data.name,
        "description": data.description,
        "amount": data.amount,
        "is_percentage": data.is_percentage,
        "created_at": now_iso()
    }
    
    novelties = entry.get("novelties", [])
    novelties.append(novelty)
    
    # Recalculate
    base_salary = entry.get("base_salary", 0)
    bonuses = entry.get("bonuses", 0)
    commissions = entry.get("commissions", 0)
    other_income = entry.get("other_income", 0)
    
    total_income_novelties = 0
    total_deduction_novelties = 0
    
    for nov in novelties:
        if nov["novelty_type"] == "income":
            if nov.get("is_percentage"):
                total_income_novelties += round(base_salary * nov["amount"] / 100, 2)
            else:
                total_income_novelties += nov["amount"]
        else:
            if nov.get("is_percentage"):
                total_deduction_novelties += round(base_salary * nov["amount"] / 100, 2)
            else:
                total_deduction_novelties += nov["amount"]
    
    overtime_total = (
        entry.get("overtime_day_amount", 0) +
        entry.get("overtime_night_amount", 0) +
        entry.get("overtime_weekend_amount", 0) +
        entry.get("overtime_holiday_amount", 0)
    )
    
    gross_salary = base_salary + overtime_total + bonuses + commissions + other_income + total_income_novelties
    
    rates = await get_company_rates_flat(company_id)
    sfs_employee = round(gross_salary * rates["sfs_employee_rate"], 2)
    afp_employee = round(gross_salary * rates["afp_employee_rate"], 2)
    isr_result = await _compute_isr(company_id, gross_salary, rates)
    isr = isr_result["isr_monthly"]
    
    total_additional = entry.get("total_additional_deductions", 0)
    loan_deduction = entry.get("loan_deduction", 0)
    
    total_deductions = round(sfs_employee + afp_employee + isr + total_additional + loan_deduction + total_deduction_novelties, 2)
    net_salary = round(gross_salary - total_deductions, 2)
    
    sfs_employer = round(gross_salary * rates["sfs_employer_rate"], 2)
    afp_employer = round(gross_salary * rates["afp_employer_rate"], 2)
    srl_employer = round(gross_salary * rates["srl_employer_rate"], 2)
    infotep_employer = round(gross_salary * rates["infotep_employer_rate"], 2)
    
    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "novelties": novelties,
            "gross_salary": round(gross_salary, 2),
            "sfs_employee": sfs_employee,
            "afp_employee": afp_employee,
            "isr": isr,
            "total_deductions": total_deductions,
            "net_salary": net_salary,
            "sfs_employer": sfs_employer,
            "afp_employer": afp_employer,
            "srl_employer": srl_employer,
            "infotep_employer": infotep_employer,
            "total_employer_contributions": round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2),
            "updated_at": now_iso()
        }}
    )
    
    await update_period_totals(entry["period_id"], company_id)
    
    return {"message": "Novedad agregada", "novelty_id": novelty_id, "net_salary": net_salary}


@router.patch("/entries/{entry_id}/novelties/{novelty_id}")
async def update_novelty(
    entry_id: str,
    novelty_id: str,
    data: PayrollNoveltyCreate,
    current_user: dict = Depends(get_current_user),
):
    """Edit an existing novelty in a payroll entry and recompute totals."""
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
    if period and period.get("status") == "paid":
        raise HTTPException(status_code=400, detail="No se puede modificar una nómina pagada")

    novelties = entry.get("novelties", [])
    target_idx = next((i for i, n in enumerate(novelties) if n.get("novelty_id") == novelty_id), None)
    if target_idx is None:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")

    novelties[target_idx] = {
        **novelties[target_idx],
        "novelty_type": data.novelty_type,
        "code": data.code,
        "name": data.name,
        "description": data.description,
        "amount": data.amount,
        "is_percentage": data.is_percentage,
        "updated_at": now_iso(),
    }

    # Recalculate (same logic as add/delete)
    base_salary = entry.get("base_salary", 0)
    bonuses = entry.get("bonuses", 0)
    commissions = entry.get("commissions", 0)
    other_income = entry.get("other_income", 0)

    total_income_novelties = 0
    total_deduction_novelties = 0
    for nov in novelties:
        if nov["novelty_type"] == "income":
            if nov.get("is_percentage"):
                total_income_novelties += round(base_salary * nov["amount"] / 100, 2)
            else:
                total_income_novelties += nov["amount"]
        else:
            if nov.get("is_percentage"):
                total_deduction_novelties += round(base_salary * nov["amount"] / 100, 2)
            else:
                total_deduction_novelties += nov["amount"]

    overtime_total = (
        entry.get("overtime_day_amount", 0)
        + entry.get("overtime_night_amount", 0)
        + entry.get("overtime_weekend_amount", 0)
        + entry.get("overtime_holiday_amount", 0)
    )

    gross_salary = base_salary + overtime_total + bonuses + commissions + other_income + total_income_novelties

    rates = await get_company_rates_flat(company_id)
    sfs_employee = round(gross_salary * rates["sfs_employee_rate"], 2)
    afp_employee = round(gross_salary * rates["afp_employee_rate"], 2)
    isr_result = await _compute_isr(company_id, gross_salary, rates)
    isr = isr_result["isr_monthly"]

    total_additional = entry.get("total_additional_deductions", 0)
    loan_deduction = entry.get("loan_deduction", 0)

    total_deductions = round(
        sfs_employee + afp_employee + isr + total_additional + loan_deduction + total_deduction_novelties,
        2,
    )
    net_salary = round(gross_salary - total_deductions, 2)

    sfs_employer = round(gross_salary * rates["sfs_employer_rate"], 2)
    afp_employer = round(gross_salary * rates["afp_employer_rate"], 2)
    srl_employer = round(gross_salary * rates["srl_employer_rate"], 2)
    infotep_employer = round(gross_salary * rates["infotep_employer_rate"], 2)

    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "novelties": novelties,
            "gross_salary": round(gross_salary, 2),
            "sfs_employee": sfs_employee,
            "afp_employee": afp_employee,
            "isr": isr,
            "total_deductions": total_deductions,
            "net_salary": net_salary,
            "sfs_employer": sfs_employer,
            "afp_employer": afp_employer,
            "srl_employer": srl_employer,
            "infotep_employer": infotep_employer,
            "total_employer_contributions": round(
                sfs_employer + afp_employer + srl_employer + infotep_employer, 2
            ),
            "updated_at": now_iso(),
        }},
    )

    await update_period_totals(entry["period_id"], company_id)

    return {"message": "Novedad actualizada", "novelty_id": novelty_id, "net_salary": net_salary}


@router.delete("/entries/{entry_id}/novelties/{novelty_id}")
async def delete_novelty(entry_id: str, novelty_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a novelty from a payroll entry"""
    company_id = current_user.get("company_id")
    
    entry = await db.payroll_entries.find_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    novelties = entry.get("novelties", [])
    novelties = [n for n in novelties if n.get("novelty_id") != novelty_id]
    
    # Recalculate
    base_salary = entry.get("base_salary", 0)
    bonuses = entry.get("bonuses", 0)
    commissions = entry.get("commissions", 0)
    other_income = entry.get("other_income", 0)
    
    total_income_novelties = 0
    total_deduction_novelties = 0
    
    for nov in novelties:
        if nov["novelty_type"] == "income":
            if nov.get("is_percentage"):
                total_income_novelties += round(base_salary * nov["amount"] / 100, 2)
            else:
                total_income_novelties += nov["amount"]
        else:
            if nov.get("is_percentage"):
                total_deduction_novelties += round(base_salary * nov["amount"] / 100, 2)
            else:
                total_deduction_novelties += nov["amount"]
    
    overtime_total = (
        entry.get("overtime_day_amount", 0) +
        entry.get("overtime_night_amount", 0) +
        entry.get("overtime_weekend_amount", 0) +
        entry.get("overtime_holiday_amount", 0)
    )
    
    gross_salary = base_salary + overtime_total + bonuses + commissions + other_income + total_income_novelties
    
    rates = await get_company_rates_flat(company_id)
    sfs_employee = round(gross_salary * rates["sfs_employee_rate"], 2)
    afp_employee = round(gross_salary * rates["afp_employee_rate"], 2)
    isr_result = await _compute_isr(company_id, gross_salary, rates)
    isr = isr_result["isr_monthly"]
    
    total_additional = entry.get("total_additional_deductions", 0)
    loan_deduction = entry.get("loan_deduction", 0)
    
    total_deductions = round(sfs_employee + afp_employee + isr + total_additional + loan_deduction + total_deduction_novelties, 2)
    net_salary = round(gross_salary - total_deductions, 2)
    
    sfs_employer = round(gross_salary * rates["sfs_employer_rate"], 2)
    afp_employer = round(gross_salary * rates["afp_employer_rate"], 2)
    srl_employer = round(gross_salary * rates["srl_employer_rate"], 2)
    infotep_employer = round(gross_salary * rates["infotep_employer_rate"], 2)
    
    await db.payroll_entries.update_one(
        {"entry_id": entry_id, "company_id": company_id},
        {"$set": {
            "novelties": novelties,
            "gross_salary": round(gross_salary, 2),
            "sfs_employee": sfs_employee,
            "afp_employee": afp_employee,
            "isr": isr,
            "total_deductions": total_deductions,
            "net_salary": net_salary,
            "sfs_employer": sfs_employer,
            "afp_employer": afp_employer,
            "srl_employer": srl_employer,
            "infotep_employer": infotep_employer,
            "total_employer_contributions": round(sfs_employer + afp_employer + srl_employer + infotep_employer, 2),
            "updated_at": now_iso()
        }}
    )
    
    await update_period_totals(entry["period_id"], company_id)
    
    return {"message": "Novedad eliminada", "net_salary": net_salary}




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


@router.get("/periods")
async def get_payroll_periods(current_user: dict = Depends(get_current_user)):
    """Get all payroll periods"""
    company_id = current_user.get("company_id")
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("start_date", -1).to_list(100)
    return periods


@router.post("/periods")
async def create_payroll_period(data: PayrollPeriodCreateV2, current_user: dict = Depends(get_current_user)):
    """Create a new payroll period"""
    company_id = current_user.get("company_id")
    
    payroll_type = data.payroll_type or 'REG'
    department_filter = data.department_filter
    employee_ids = data.employee_ids
    currency = data.currency or "DOP"
    exchange_rate = data.exchange_rate
    project_id = data.project_id
    
    if data.template_id:
        template = await db.payroll_templates.find_one(
            {"template_id": data.template_id, "company_id": company_id},
            {"_id": 0}
        )
        if template:
            payroll_type = template.get("payroll_type", payroll_type)
            department_filter = template.get("department_filter", department_filter)
            employee_ids = template.get("employee_ids", employee_ids)
            currency = template.get("currency", currency)
            exchange_rate = template.get("default_exchange_rate", exchange_rate)
            project_id = template.get("project_id", project_id)
    
    period_id = generate_id("period")
    period = {
        "period_id": period_id,
        "company_id": company_id,
        "period_type": data.period_type,
        "payroll_type": payroll_type,
        "year": data.year,
        "month": data.month,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "description": data.description or f"Nómina {data.period_type} - {data.month}/{data.year}",
        "department_filter": department_filter,
        "employee_ids": employee_ids,
        "currency": currency,
        "exchange_rate": exchange_rate,
        "project_id": project_id,
        "template_id": data.template_id,
        "status": "draft",
        "total_gross": 0,
        "total_deductions": 0,
        "total_net": 0,
        "employee_count": 0,
        "journal_entry_id": None,
        "created_at": now_iso(),
        "created_by": current_user.get("user_id")
    }
    await db.payroll_periods.insert_one(period)
    
    return {"period_id": period_id, "message": "Período creado correctamente"}


@router.get("/periods/{period_id}")
async def get_payroll_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific payroll period with entries"""
    company_id = current_user.get("company_id")
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    period["entries"] = entries
    return period


@router.delete("/periods/{period_id}")
async def delete_payroll_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a payroll period and associated journal entry"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("journal_entry_id"):
        await db.journal_entries.delete_one({"entry_id": period["journal_entry_id"], "company_id": company_id})
    
    await db.payroll_entries.delete_many({"period_id": period_id, "company_id": company_id})
    await db.payroll_periods.delete_one({"period_id": period_id, "company_id": company_id})
    
    return {"message": "Período y asiento contable eliminados correctamente"}


@router.post("/periods/{period_id}/add-employees")
async def add_employees_to_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Add all active employees to payroll period"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    employee_query = {"company_id": company_id, "status": "active", "exclude_from_payroll": {"$ne": True}}
    
    if period.get("department_filter"):
        employee_query["department"] = period["department_filter"]
    
    if period.get("employee_ids") and len(period["employee_ids"]) > 0:
        employee_query["employee_id"] = {"$in": period["employee_ids"]}
    
    employees = await db.employees.find(employee_query, {"_id": 0}).to_list(1000)
    
    existing_entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    existing_employee_ids = {e["employee_id"] for e in existing_entries}
    
    added_count = 0
    payroll_type = period.get("payroll_type", "REG")

    # Fetch country-specific rates once for the whole period
    rates = await get_company_rates_flat(company_id)
    sfs_emp_rate = rates["sfs_employee_rate"]
    afp_emp_rate = rates["afp_employee_rate"]
    sfs_er_rate = rates["sfs_employer_rate"]
    afp_er_rate = rates["afp_employer_rate"]
    srl_er_rate = rates["srl_employer_rate"]
    infotep_er_rate = rates["infotep_employer_rate"]
    
    for emp in employees:
        if emp["employee_id"] in existing_employee_ids:
            continue
        
        salary = emp.get("salary", 0)
        
        if payroll_type == "REG":
            if period.get("period_type", "").startswith("quincenal"):
                salary = salary / 2
        elif payroll_type == "REG13":
            salary = emp.get("salary", 0)
        elif payroll_type == "BONO":
            salary = 0
        elif payroll_type == "VAC":
            salary = emp.get("salary", 0) / 23.83 * 14
        elif payroll_type == "OBREROS_NG":
            if period.get("period_type", "").startswith("quincenal"):
                salary = salary / 2

        # Manual overrides on the employee profile are stored as MONTHLY
        # amounts. Scale to the period (×0.5 for quincenal) so each period
        # withholds the correct fraction.
        scale = period_scaling_factor(period.get("period_type"))
        
        entry_id = generate_id("pe")
        
        # For OBREROS_NG payroll type, only apply ISR 2% - no TSS deductions
        if payroll_type == "OBREROS_NG":
            isr_obreros = round(salary * ISR_OBREROS_RATE, 2)
            entry = {
                "entry_id": entry_id,
                "period_id": period_id,
                "company_id": company_id,
                "employee_id": emp["employee_id"],
                "employee_name": f"{emp['first_name']} {emp['last_name']}",
                "employee_document": emp.get("document_number", ""),
                "department": emp.get("department", ""),
                "position": emp.get("position", ""),
                "payroll_type": payroll_type,
                "base_salary": salary,
                "overtime_day_hours": 0,
                "overtime_day_amount": 0,
                "overtime_night_hours": 0,
                "overtime_night_amount": 0,
                "overtime_weekend_hours": 0,
                "overtime_weekend_amount": 0,
                "overtime_holiday_hours": 0,
                "overtime_holiday_amount": 0,
                "bonuses": 0,
                "commissions": 0,
                "other_income": 0,
                "gross_salary": salary,
                "sfs_employee": 0,
                "afp_employee": 0,
                "isr": isr_obreros,
                "isr_obreros_rate": ISR_OBREROS_RATE,
                "additional_deductions": [],
                "total_additional_deductions": 0,
                "total_deductions": isr_obreros,
                "net_salary": round(salary - isr_obreros, 2),
                "sfs_employer": 0,
                "afp_employer": 0,
                "srl_employer": 0,
                "infotep_employer": 0,
                "total_employer_contributions": 0,
                "loan_deduction": 0,
                "status": "draft",
                "created_at": now_iso()
            }
        else:
            # Regular payroll with full TSS deductions
            # Convert the employee's recurring "additional_deductions" into
            # first-class novelties on the entry so they:
            #   - Populate the per-code columns (SEG / PENS / COOP / EMB / etc.)
            #   - Are editable inline in the Payroll Sheet
            #   - Are scaled correctly for quincenal periods
            from uuid import uuid4
            DED_TYPE_TO_CODE = {
                "Préstamo Empresa":      "PREST",
                "Préstamo Cooperativa":  "COOP",
                "Cooperativa":           "COOP",
                "Seguro Adicional":      "SEG",
                "Pensión Alimenticia":   "PENS",
                "Anticipo":              "ANTIC",
                "Embargo":               "EMB",
                "Tardanzas":             "TARD",
                "Ausencias":             "AUS",
                "Otro":                  "OTROSD",
                "Otros":                 "OTROSD",
            }
            CODE_TO_FULL = {
                "ANTIC": "Anticipo", "COOP": "Cooperativa", "SEG": "Seguro Adicional",
                "PENS": "Pensión Alimenticia", "EMB": "Embargo", "TARD": "Tardanzas",
                "AUS": "Ausencias", "OTROSD": "Otros Descuentos",
                "PREST": "Préstamo Empresa",
            }
            deduction_novelties = []
            total_ded_novelties_amount = 0.0
            now_str = now_iso()
            for d in emp.get("additional_deductions", []) or []:
                code = DED_TYPE_TO_CODE.get(d.get("type"), "OTROSD")
                raw_amt = float(d.get("amount", 0) or 0)
                # Manual monetary deductions are stored MONTHLY on the profile;
                # percentage deductions apply against base_salary directly.
                if d.get("is_percentage"):
                    scaled_amt = raw_amt
                    eff_value = round(salary * raw_amt / 100, 2)
                else:
                    scaled_amt = round(raw_amt * scale, 2)
                    eff_value = scaled_amt
                deduction_novelties.append({
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
                total_ded_novelties_amount += eff_value

            entry = {
                "entry_id": entry_id,
                "period_id": period_id,
                "company_id": company_id,
                "employee_id": emp["employee_id"],
                "employee_name": f"{emp['first_name']} {emp['last_name']}",
                "employee_document": emp.get("document_number", ""),
                "department": emp.get("department", ""),
                "position": emp.get("position", ""),
                "payroll_type": payroll_type,
                "base_salary": salary,
                "overtime_day_hours": 0,
                "overtime_day_amount": 0,
                "overtime_night_hours": 0,
                "overtime_night_amount": 0,
                "overtime_weekend_hours": 0,
                "overtime_weekend_amount": 0,
                "overtime_holiday_hours": 0,
                "overtime_holiday_amount": 0,
                "bonuses": 0,
                "commissions": 0,
                "other_income": 0,
                "gross_salary": salary,
                "sfs_employee": round(salary * sfs_emp_rate, 2) if emp.get("sfs_discount", True) and not emp.get("sfs_manual_override") else (round(float(emp.get("sfs_manual_amount", 0)) * scale, 2) if emp.get("sfs_manual_override") and emp.get("sfs_discount", True) else 0),
                "afp_employee": round(salary * afp_emp_rate, 2) if emp.get("afp_discount", True) and not emp.get("afp_manual_override") else (round(float(emp.get("afp_manual_amount", 0)) * scale, 2) if emp.get("afp_manual_override") and emp.get("afp_discount", True) else 0),
                "isr": 0,
                # Recurring deductions are now stored as novelties (see above).
                # Keep these fields zero/empty for new entries to avoid double-counting.
                "additional_deductions": [],
                "total_additional_deductions": 0.0,
                "novelties": deduction_novelties,
                "total_income_novelties": 0.0,
                "total_deduction_novelties": round(total_ded_novelties_amount, 2),
                "total_deductions": 0,
                "net_salary": 0,
                "sfs_employer": round(salary * sfs_er_rate, 2),
                "afp_employer": round(salary * afp_er_rate, 2),
                "srl_employer": round(salary * srl_er_rate, 2),
                "infotep_employer": round(salary * infotep_er_rate, 2),
                "total_employer_contributions": 0,
                "status": "draft",
                "created_at": now_iso()
            }
            
            isr_result = await _compute_isr(company_id, salary, rates, period_type=period.get("period_type"))
            if emp.get("isr_discount", True):
                if emp.get("isr_manual_override"):
                    entry["isr"] = round(float(emp.get("isr_manual_amount", 0)) * scale, 2)
                else:
                    entry["isr"] = isr_result["isr_monthly"]
            else:
                entry["isr"] = 0
            
            # Get loan deductions
            loan_deduction = 0
            active_loans = await db.loans.find({
                "employee_id": emp["employee_id"],
                "company_id": company_id,
                "status": "active",
                "deduct_from_payroll": True
            }, {"_id": 0}).to_list(10)
            
            for loan in active_loans:
                monthly_payment = loan.get("monthly_payment", 0)
                remaining = loan.get("remaining_balance", 0)
                deduction = min(monthly_payment, remaining)
                loan_deduction += deduction
            
            entry["loan_deduction"] = round(loan_deduction, 2)
            
            entry["total_deductions"] = round(
                entry["sfs_employee"] + entry["afp_employee"] + entry["isr"]
                + entry["total_additional_deductions"]
                + entry.get("total_deduction_novelties", 0)
                + entry["loan_deduction"],
                2
            )
            entry["net_salary"] = round(entry["gross_salary"] - entry["total_deductions"], 2)
            entry["total_employer_contributions"] = round(
                entry["sfs_employer"] + entry["afp_employer"] + entry["srl_employer"] + entry["infotep_employer"],
                2
            )
        
        await db.payroll_entries.insert_one(entry)
        added_count += 1
    
    await update_period_totals(period_id, company_id)
    
    return {"message": f"{added_count} empleados agregados al período", "added": added_count}





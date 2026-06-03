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


@router.post("/periods/{period_id}/calculate")
async def calculate_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Recalculate all entries in a period from scratch.

    Rebuilds ``gross_salary`` from the entry components (base + overtime +
    bonuses + commissions + other_income + income novelties), then applies
    SFS/AFP/ISR (period-aware) and updates the totals. Honors the employee's
    ``sfs_discount``/``afp_discount``/``isr_discount`` flags and any manual
    overrides stored on the entry (``sfs_manual_override_entry``, etc.).

    Returns ``{"message": str, "recalculated": int}``.
    """
    company_id = current_user.get("company_id")

    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    if period.get("status") == "paid":
        raise HTTPException(status_code=400, detail="No se puede recalcular una nómina ya pagada")

    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)

    rates = await get_company_rates_flat(company_id)
    period_type = period.get("period_type")

    for entry in entries:
        # Fetch employee for discount flags (some entries may pre-date the flags)
        emp = await db.employees.find_one(
            {"employee_id": entry.get("employee_id"), "company_id": company_id},
            {"_id": 0, "sfs_discount": 1, "afp_discount": 1, "isr_discount": 1}
        ) or {}

        base_salary = entry.get("base_salary", 0) or 0
        overtime_total = (
            (entry.get("overtime_day_amount", 0) or 0)
            + (entry.get("overtime_night_amount", 0) or 0)
            + (entry.get("overtime_weekend_amount", 0) or 0)
            + (entry.get("overtime_holiday_amount", 0) or 0)
        )
        bonuses = entry.get("bonuses", 0) or 0
        commissions = entry.get("commissions", 0) or 0
        other_income = entry.get("other_income", 0) or 0

        income_novelties = 0
        deduction_novelties = 0
        for nov in entry.get("novelties", []) or []:
            amt = nov.get("amount", 0) or 0
            value = round(base_salary * amt / 100, 2) if nov.get("is_percentage") else amt
            if nov.get("novelty_type") == "income":
                income_novelties += value
            else:
                deduction_novelties += value

        gross_salary = round(
            base_salary + overtime_total + bonuses + commissions + other_income + income_novelties,
            2,
        )

        # SFS / AFP — honor manual overrides on the entry
        if entry.get("sfs_manual_override_entry"):
            sfs_employee = round(entry.get("sfs_employee", 0) or 0, 2)
        elif emp.get("sfs_discount", True) is False:
            sfs_employee = 0
        else:
            sfs_employee = round(gross_salary * rates["sfs_employee_rate"], 2)

        if entry.get("afp_manual_override_entry"):
            afp_employee = round(entry.get("afp_employee", 0) or 0, 2)
        elif emp.get("afp_discount", True) is False:
            afp_employee = 0
        else:
            afp_employee = round(gross_salary * rates["afp_employee_rate"], 2)

        # ISR — period-aware via _compute_isr; honors override
        if entry.get("isr_manual_override_entry"):
            isr = round(entry.get("isr", 0) or 0, 2)
        elif emp.get("isr_discount", True) is False:
            isr = 0
        else:
            isr_result = await _compute_isr(
                company_id,
                gross_salary,
                rates,
                period_type=period_type,
                period=period,
                employee_id=entry.get("employee_id"),
            )
            isr = isr_result["isr_monthly"]

        total_additional = entry.get("total_additional_deductions", 0) or 0
        loan_deduction = entry.get("loan_deduction", 0) or 0
        total_deductions = round(
            sfs_employee + afp_employee + isr + total_additional + loan_deduction + deduction_novelties,
            2,
        )
        net_salary = round(gross_salary - total_deductions, 2)

        sfs_employer = round(gross_salary * rates["sfs_employer_rate"], 2)
        afp_employer = round(gross_salary * rates["afp_employer_rate"], 2)
        srl_employer = round(gross_salary * rates["srl_employer_rate"], 2)
        infotep_employer = round(gross_salary * rates["infotep_employer_rate"], 2)

        await db.payroll_entries.update_one(
            {"entry_id": entry["entry_id"], "company_id": company_id},
            {"$set": {
                "gross_salary": gross_salary,
                "total_income_novelties": round(income_novelties, 2),
                "total_deduction_novelties": round(deduction_novelties, 2),
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

    await update_period_totals(period_id, company_id)

    return {
        "message": f"{len(entries)} entradas recalculadas",
        "recalculated": len(entries),
    }



@router.post("/periods/{period_id}/pay")
async def pay_period(period_id: str, data: PaymentRequest = None, current_user: dict = Depends(get_current_user)):
    """Mark a payroll period as paid (Approved -> Paid)"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    user_permissions = current_user.get("permissions", [])
    user_role = current_user.get("role", "")
    can_pay = "payroll_pay" in user_permissions or user_role in ["admin", "hr_manager", "finance_manager"]
    
    if not can_pay:
        raise HTTPException(status_code=403, detail="No tiene permisos para pagar nóminas")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Solo se puede pagar nóminas en estado 'Aprobado'")
    
    workflow_entry = {
        "action": "pay",
        "from_status": period.get("status"),
        "to_status": "paid",
        "user_id": user_id,
        "user_name": current_user.get("email", current_user.get("name", "Usuario")),
        "timestamp": now_iso(),
        "payment_info": {
            "bank": data.payment_bank if data else "",
            "date": data.payment_date if data else now_iso()[:10],
            "reference": data.reference if data else ""
        }
    }
    
    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {
            "$set": {
                "status": "paid",
                "paid_at": now_iso(),
                "paid_by": user_id,
                "payment_bank": data.payment_bank if data else "",
                "payment_date": data.payment_date if data else now_iso()[:10],
                "payment_reference": data.reference if data else "",
                "updated_at": now_iso()
            },
            "$push": {
                "workflow_history": workflow_entry
            }
        }
    )
    
    await db.payroll_entries.update_many(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {"status": "paid"}}
    )
    
    # Register loan installments via the centralized helper (decrements
    # remaining_balance, marks payment_schedule installments as paid,
    # flips status to "paid" when fully settled, appends payments[]).
    from routes.loans import loan_deduction_for_period, register_loan_installment
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id, "loan_deduction": {"$gt": 0}},
        {"_id": 0, "employee_id": 1, "loan_deduction": 1}
    ).to_list(1000)

    payment_date = now_iso()[:10]
    for entry in entries:
        employee_id = entry.get("employee_id")
        deduction = float(entry.get("loan_deduction", 0) or 0)
        if deduction <= 0:
            continue
        active_loans = await db.loans.find(
            {"employee_id": employee_id, "company_id": company_id, "status": "active",
             "deduct_from_payroll": True, "remaining_balance": {"$gt": 0}},
            {"_id": 0}
        ).to_list(10)
        # Distribute the entry's loan deduction across loans in the same
        # proportion they were withheld (using each loan's expected
        # period-aware installment). This keeps multi-loan employees
        # working correctly.
        for loan in active_loans:
            if deduction <= 0:
                break
            expected = loan_deduction_for_period(loan, period.get("period_type"))
            if expected <= 0:
                continue
            payment = min(expected, deduction, float(loan.get("remaining_balance", 0) or 0))
            if payment <= 0:
                continue
            await register_loan_installment(
                loan_id=loan["loan_id"],
                company_id=company_id,
                amount=payment,
                period_id=period_id,
                payment_date=payment_date,
            )
            deduction -= payment
    
    # Notify employees that payroll is paid
    all_entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "employee_id": 1, "net_salary": 1}
    ).to_list(5000)
    period_name = period.get("name", period.get("period_name", period_id))
    for entry in all_entries:
        await create_employee_notification(
            db,
            employee_id=entry["employee_id"],
            company_id=company_id,
            title="Recibo de Nomina Disponible",
            message=f"Tu recibo de nomina del periodo {period_name} esta disponible. Revisa tu portal para ver los detalles.",
            notification_type="success",
            category="payroll",
            action_url="/payslips",
        )
        # Web push notification
        await send_push_to_user(
            user_id=entry['employee_id'],
            title="Nomina Procesada",
            body=f"Tu recibo de nomina del periodo {period_name} esta disponible.",
            url="/employee-portal",
        )

    # Auto-generate/update journal entry on payment
    settings = await db.company_settings.find_one({"company_id": company_id}, {"_id": 0})
    auto_je = (settings or {}).get("auto_journal_entry", True)
    je_id = None
    if auto_je:
        je_id = await generate_payroll_journal_entry(period_id, company_id, user_id, trigger="pay")
        # Auto-sync to FortexaERP if configured
        await auto_sync_to_erp(company_id, period_id, current_user.get("email", "system"))

    return {"message": "Nomina pagada correctamente", "status": "paid", "journal_entry_id": je_id}




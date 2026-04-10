"""
Payroll Routes - FortexaRH (Consolidated)
Advanced payroll management with TSS compliance for Dominican Republic
+ Basic/legacy payroll CRUD endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import io
import csv
from services.employee_notifications import create_employee_notification
from services.push_service import send_push_to_user

# Import shared constants
from utils.payroll_constants import (
    SFS_EMPLOYEE_RATE, AFP_EMPLOYEE_RATE,
    SFS_EMPLOYER_RATE, AFP_EMPLOYER_RATE, SRL_EMPLOYER_RATE, INFOTEP_EMPLOYER_RATE,
    PAYROLL_TYPES, PAYROLL_NOVELTY_TYPES, ISR_OBREROS_RATE,
    PayrollPeriodCreateV2, PayrollNoveltyCreate, PayrollPaymentRequest,
    calculate_isr_monthly, generate_id, now_iso
)

# Payroll router (consolidated)
router = APIRouter(prefix="/payroll", tags=["Payroll"])

from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)


# ===================== PYDANTIC MODELS =====================

from models.payroll import (
    PayrollEntryCreate, ApprovalRequest, PaymentRequest
)


# ===================== HELPER FUNCTIONS =====================

async def update_period_totals(period_id: str, company_id: str):
    """Update period totals based on entries"""
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    total_deductions = sum(e.get("total_deductions", 0) for e in entries)
    total_net = sum(e.get("net_salary", 0) for e in entries)
    
    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {
            "total_gross": round(total_gross, 2),
            "total_deductions": round(total_deductions, 2),
            "total_net": round(total_net, 2),
            "employee_count": len(entries),
            "updated_at": now_iso()
        }}
    )

    # Auto-update linked journal entry if exists
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "journal_entry_id": 1, "status": 1}
    )
    if period and period.get("journal_entry_id") and period.get("status") in ["approved", "paid"]:
        await generate_payroll_journal_entry(period_id, company_id, "system", trigger="update")


async def generate_payroll_journal_entry(period_id: str, company_id: str, user_id: str, trigger: str = "manual"):
    """Generate or update a journal entry for a payroll period.
    
    Args:
        trigger: 'approve', 'pay', 'manual', or 'update' (when entries change)
    Returns:
        entry_id or None
    """
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id}, {"_id": 0}
    )
    if not period:
        return None

    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id}, {"_id": 0}
    ).to_list(1000)
    if not entries:
        return None

    # Calculate totals
    total_gross = round(sum(e.get("gross_salary", 0) for e in entries), 2)
    total_sfs_emp = round(sum(e.get("sfs_employee", 0) for e in entries), 2)
    total_afp_emp = round(sum(e.get("afp_employee", 0) for e in entries), 2)
    total_isr = round(sum(e.get("isr", 0) for e in entries), 2)
    total_net = round(sum(e.get("net_salary", 0) for e in entries), 2)
    total_sfs_employer = round(sum(e.get("sfs_employer", 0) for e in entries), 2)
    total_afp_employer = round(sum(e.get("afp_employer", 0) for e in entries), 2)
    total_srl = round(sum(e.get("srl_employer", 0) for e in entries), 2)
    total_infotep = round(sum(e.get("infotep_employer", 0) for e in entries), 2)
    total_employer = round(total_sfs_employer + total_afp_employer + total_srl + total_infotep, 2)
    total_otros = round(sum(e.get("otros_descuentos", 0) for e in entries), 2)

    period_desc = period.get("description") or period.get("name") or f"Nómina {period.get('month','')}/{period.get('year','')}"
    entry_date = period.get("payment_date") or period.get("end_date") or now_iso()[:10]

    # Build journal lines
    lines = []
    # DEBITS
    if total_gross > 0:
        lines.append({"account_code": "6100", "account_name": "Gasto de Nómina (Sueldos y Salarios)", "debit": total_gross, "credit": 0, "description": period_desc})
    if total_employer > 0:
        lines.append({"account_code": "6200", "account_name": "Aportes Patronales TSS", "debit": total_employer, "credit": 0, "description": f"{period_desc} - TSS Patronal"})

    # CREDITS
    total_sfs = round(total_sfs_emp + total_sfs_employer, 2)
    if total_sfs > 0:
        lines.append({"account_code": "2110", "account_name": "SFS por Pagar", "debit": 0, "credit": total_sfs, "description": f"{period_desc} - SFS"})
    total_afp = round(total_afp_emp + total_afp_employer, 2)
    if total_afp > 0:
        lines.append({"account_code": "2120", "account_name": "AFP por Pagar", "debit": 0, "credit": total_afp, "description": f"{period_desc} - AFP"})
    if total_isr > 0:
        lines.append({"account_code": "2130", "account_name": "ISR por Pagar", "debit": 0, "credit": total_isr, "description": f"{period_desc} - ISR"})
    if total_srl > 0:
        lines.append({"account_code": "2140", "account_name": "SRL por Pagar", "debit": 0, "credit": total_srl, "description": f"{period_desc} - SRL"})
    if total_infotep > 0:
        lines.append({"account_code": "2150", "account_name": "INFOTEP por Pagar", "debit": 0, "credit": total_infotep, "description": f"{period_desc} - INFOTEP"})
    if total_otros > 0:
        lines.append({"account_code": "2160", "account_name": "Otros Descuentos por Pagar", "debit": 0, "credit": total_otros, "description": f"{period_desc} - Otros"})
    if total_net > 0:
        lines.append({"account_code": "1100", "account_name": "Banco / Nómina por Pagar", "debit": 0, "credit": total_net, "description": f"{period_desc} - Neto"})

    total_debits = round(sum(l["debit"] for l in lines), 2)
    total_credits = round(sum(l["credit"] for l in lines), 2)

    existing_je_id = period.get("journal_entry_id")

    if existing_je_id:
        # Update existing JE
        await db.journal_entries.update_one(
            {"entry_id": existing_je_id, "company_id": company_id},
            {"$set": {
                "entry_date": entry_date,
                "description": f"Asiento de Nómina - {period_desc}",
                "lines": lines,
                "total_debits": total_debits,
                "total_credits": total_credits,
                "notes": f"Actualizado automáticamente ({trigger}) - {len(entries)} empleados",
                "updated_at": now_iso()
            }}
        )
        return existing_je_id
    else:
        # Create new JE
        entry_id = f"je_{uuid.uuid4().hex[:12]}"
        je = {
            "entry_id": entry_id,
            "company_id": company_id,
            "entry_date": entry_date,
            "reference": f"NOM-{period.get('year','')}{str(period.get('month','')).zfill(2)}-{period_id[-6:]}",
            "description": f"Asiento de Nómina - {period_desc}",
            "period": f"{period.get('year','')}-{str(period.get('month','')).zfill(2)}",
            "entry_type": "payroll",
            "lines": lines,
            "payroll_id": period_id,
            "notes": f"Generado automáticamente ({trigger}) - {len(entries)} empleados",
            "total_debits": total_debits,
            "total_credits": total_credits,
            "status": "posted" if trigger == "pay" else "draft",
            "created_by": user_id,
            "created_at": now_iso(),
            "updated_at": now_iso()
        }
        await db.journal_entries.insert_one(je)

        # Link JE to period
        await db.payroll_periods.update_one(
            {"period_id": period_id, "company_id": company_id},
            {"$set": {"journal_entry_id": entry_id}}
        )
        return entry_id


async def delete_payroll_journal_entry(period_id: str, company_id: str):
    """Delete the journal entry linked to a payroll period."""
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "journal_entry_id": 1}
    )
    je_id = period.get("journal_entry_id") if period else None
    if je_id:
        await db.journal_entries.delete_one({"entry_id": je_id, "company_id": company_id})
        await db.payroll_periods.update_one(
            {"period_id": period_id, "company_id": company_id},
            {"$unset": {"journal_entry_id": ""}}
        )
    return je_id


# ===================== PERIOD ENDPOINTS =====================

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
                "sfs_employee": round(salary * SFS_EMPLOYEE_RATE, 2) if emp.get("sfs_discount", True) and not emp.get("sfs_manual_override") else (float(emp.get("sfs_manual_amount", 0)) if emp.get("sfs_manual_override") and emp.get("sfs_discount", True) else 0),
                "afp_employee": round(salary * AFP_EMPLOYEE_RATE, 2) if emp.get("afp_discount", True) and not emp.get("afp_manual_override") else (float(emp.get("afp_manual_amount", 0)) if emp.get("afp_manual_override") and emp.get("afp_discount", True) else 0),
                "isr": 0,
                "additional_deductions": emp.get("additional_deductions", []),
                "total_additional_deductions": sum(d.get("amount", 0) for d in emp.get("additional_deductions", []) if not d.get("is_percentage")),
                "total_deductions": 0,
                "net_salary": 0,
                "sfs_employer": round(salary * SFS_EMPLOYER_RATE, 2),
                "afp_employer": round(salary * AFP_EMPLOYER_RATE, 2),
                "srl_employer": round(salary * SRL_EMPLOYER_RATE, 2),
                "infotep_employer": round(salary * INFOTEP_EMPLOYER_RATE, 2),
                "total_employer_contributions": 0,
                "status": "draft",
                "created_at": now_iso()
            }
            
            isr_result = calculate_isr_monthly(salary)
            if emp.get("isr_discount", True):
                if emp.get("isr_manual_override"):
                    entry["isr"] = round(float(emp.get("isr_manual_amount", 0)), 2)
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
                entry["sfs_employee"] + entry["afp_employee"] + entry["isr"] + entry["total_additional_deductions"] + entry["loan_deduction"],
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


# ===================== ENTRY ENDPOINTS =====================

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
    
    hourly_rate = data.base_salary / 23.83 / 8
    
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

    # SFS: respect inline override first, then employee override, then calculation
    if data.sfs_override is not None:
        sfs_employee = round(data.sfs_override, 2)
    elif emp.get("sfs_discount", True):
        sfs_employee = round(float(emp.get("sfs_manual_amount", 0)), 2) if emp.get("sfs_manual_override") else round(gross_salary * SFS_EMPLOYEE_RATE, 2)
    else:
        sfs_employee = 0

    # AFP: respect inline override first, then employee override, then calculation
    if data.afp_override is not None:
        afp_employee = round(data.afp_override, 2)
    elif emp.get("afp_discount", True):
        afp_employee = round(float(emp.get("afp_manual_amount", 0)), 2) if emp.get("afp_manual_override") else round(gross_salary * AFP_EMPLOYEE_RATE, 2)
    else:
        afp_employee = 0

    # ISR: respect inline override first, then employee override, then calculation
    isr_result = calculate_isr_monthly(gross_salary)
    if data.isr_override is not None:
        isr = round(data.isr_override, 2)
    elif emp.get("isr_discount", True):
        isr = round(float(emp.get("isr_manual_amount", 0)), 2) if emp.get("isr_manual_override") else isr_result["isr_monthly"]
    else:
        isr = 0
    
    total_additional = sum(d.get("amount", 0) for d in (data.additional_deductions or []) if not d.get("is_percentage"))
    for d in (data.additional_deductions or []):
        if d.get("is_percentage"):
            total_additional += round(gross_salary * d.get("amount", 0) / 100, 2)
    
    loan_deduction = entry.get("loan_deduction", 0)
    total_deductions = round(sfs_employee + afp_employee + isr + total_additional + loan_deduction, 2)
    net_salary = round(gross_salary - total_deductions, 2)
    
    sfs_employer = round(gross_salary * SFS_EMPLOYER_RATE, 2)
    afp_employer = round(gross_salary * AFP_EMPLOYER_RATE, 2)
    srl_employer = round(gross_salary * SRL_EMPLOYER_RATE, 2)
    infotep_employer = round(gross_salary * INFOTEP_EMPLOYER_RATE, 2)
    
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


# ===================== NOVELTY ENDPOINTS =====================

@router.get("/novelty-types")
async def get_novelty_types(current_user: dict = Depends(get_current_user)):
    """Get available novelty types"""
    return PAYROLL_NOVELTY_TYPES


@router.get("/payroll-types")
async def get_payroll_types(current_user: dict = Depends(get_current_user)):
    """Get available payroll types"""
    return PAYROLL_TYPES


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
    
    sfs_employee = round(gross_salary * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(gross_salary * AFP_EMPLOYEE_RATE, 2)
    isr_result = calculate_isr_monthly(gross_salary)
    isr = isr_result["isr_monthly"]
    
    total_additional = entry.get("total_additional_deductions", 0)
    loan_deduction = entry.get("loan_deduction", 0)
    
    total_deductions = round(sfs_employee + afp_employee + isr + total_additional + loan_deduction + total_deduction_novelties, 2)
    net_salary = round(gross_salary - total_deductions, 2)
    
    sfs_employer = round(gross_salary * SFS_EMPLOYER_RATE, 2)
    afp_employer = round(gross_salary * AFP_EMPLOYER_RATE, 2)
    srl_employer = round(gross_salary * SRL_EMPLOYER_RATE, 2)
    infotep_employer = round(gross_salary * INFOTEP_EMPLOYER_RATE, 2)
    
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
    
    sfs_employee = round(gross_salary * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(gross_salary * AFP_EMPLOYEE_RATE, 2)
    isr_result = calculate_isr_monthly(gross_salary)
    isr = isr_result["isr_monthly"]
    
    total_additional = entry.get("total_additional_deductions", 0)
    loan_deduction = entry.get("loan_deduction", 0)
    
    total_deductions = round(sfs_employee + afp_employee + isr + total_additional + loan_deduction + total_deduction_novelties, 2)
    net_salary = round(gross_salary - total_deductions, 2)
    
    sfs_employer = round(gross_salary * SFS_EMPLOYER_RATE, 2)
    afp_employer = round(gross_salary * AFP_EMPLOYER_RATE, 2)
    srl_employer = round(gross_salary * SRL_EMPLOYER_RATE, 2)
    infotep_employer = round(gross_salary * INFOTEP_EMPLOYER_RATE, 2)
    
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


# ===================== UTILITY ENDPOINTS =====================

@router.get("/available-years")
async def get_available_years(current_user: dict = Depends(get_current_user)):
    """Get years with payroll data"""
    company_id = current_user.get("company_id")
    periods = await db.payroll_periods.find(
        {"company_id": company_id},
        {"_id": 0, "year": 1}
    ).to_list(1000)
    
    years = sorted(set(p.get("year") for p in periods if p.get("year")))
    if not years:
        years = [datetime.now().year]
    return years


@router.post("/periods/{period_id}/calculate")
async def calculate_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Recalculate all entries in a period"""
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
    
    for entry in entries:
        gross_salary = entry.get("gross_salary", 0)
        
        sfs_employee = round(gross_salary * SFS_EMPLOYEE_RATE, 2)
        afp_employee = round(gross_salary * AFP_EMPLOYEE_RATE, 2)
        isr_result = calculate_isr_monthly(gross_salary)
        isr = isr_result["isr_monthly"]
        
        total_additional = entry.get("total_additional_deductions", 0)
        loan_deduction = entry.get("loan_deduction", 0)
        
        total_deductions = round(sfs_employee + afp_employee + isr + total_additional + loan_deduction, 2)
        net_salary = round(gross_salary - total_deductions, 2)
        
        sfs_employer = round(gross_salary * SFS_EMPLOYER_RATE, 2)
        afp_employer = round(gross_salary * AFP_EMPLOYER_RATE, 2)
        srl_employer = round(gross_salary * SRL_EMPLOYER_RATE, 2)
        infotep_employer = round(gross_salary * INFOTEP_EMPLOYER_RATE, 2)
        
        await db.payroll_entries.update_one(
            {"entry_id": entry["entry_id"], "company_id": company_id},
            {"$set": {
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
    
    await update_period_totals(period_id, company_id)
    
    return {"message": f"{len(entries)} entradas recalculadas"}


# ===================== APPROVAL WORKFLOW =====================

@router.post("/periods/{period_id}/submit-for-approval")
async def submit_for_approval(period_id: str, data: ApprovalRequest = None, current_user: dict = Depends(get_current_user)):
    """Submit a payroll period for approval (Draft -> Pending Approval)"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    user_name = current_user.get("name", current_user.get("email", "Usuario"))
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("status") not in ["open", "draft"]:
        raise HTTPException(status_code=400, detail=f"Solo se puede enviar a aprobación desde estado borrador. Estado actual: {period.get('status')}")
    
    if period.get("employee_count", 0) == 0:
        raise HTTPException(status_code=400, detail="No hay empleados en esta nómina. Agregue empleados antes de enviar a aprobación.")
    
    workflow_entry = {
        "action": "submit_for_approval",
        "from_status": period.get("status"),
        "to_status": "pending_approval",
        "user_id": user_id,
        "user_name": current_user.get("email", current_user.get("name", "Usuario")),
        "comments": data.comments if data else None,
        "timestamp": now_iso()
    }
    
    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {
            "$set": {
                "status": "pending_approval",
                "submitted_at": now_iso(),
                "submitted_by": user_id,
                "updated_at": now_iso()
            },
            "$push": {
                "workflow_history": workflow_entry
            }
        }
    )
    
    await db.payroll_entries.update_many(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {"status": "pending_approval"}}
    )
    
    period_desc = period.get("description", f"Período {period_id}")
    notification = {
        "notification_id": f"notif_{generate_id('')[7:]}",
        "company_id": company_id,
        "title": "Nómina Pendiente de Aprobación",
        "message": f"{user_name} ha enviado la nómina '{period_desc}' para aprobación.",
        "type": "payroll_approval",
        "priority": "high",
        "link": f"/payroll?period={period_id}",
        "target_user_id": None,
        "target_role": "admin",
        "metadata": {"period_id": period_id, "period_description": period_desc},
        "read_by": [],
        "created_by": user_id,
        "created_at": now_iso()
    }
    await db.notifications.insert_one(notification)
    
    return {"message": "Nómina enviada para aprobación", "status": "pending_approval"}


@router.post("/periods/{period_id}/approve")
async def approve_period(period_id: str, data: ApprovalRequest = None, current_user: dict = Depends(get_current_user)):
    """Approve a payroll period (Pending Approval -> Approved)"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    user_permissions = current_user.get("permissions", [])
    user_role = current_user.get("role", "")
    can_approve = "payroll_approve" in user_permissions or user_role in ["admin", "hr_manager", "finance_manager"]
    
    if not can_approve:
        raise HTTPException(status_code=403, detail="No tiene permisos para aprobar nóminas")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Período ya pagado")
    
    if period.get("status") not in ["pending_approval", "calculated", "open"]:
        raise HTTPException(status_code=400, detail=f"No se puede aprobar desde estado: {period.get('status')}")
    
    workflow_entry = {
        "action": "approve",
        "from_status": period.get("status"),
        "to_status": "approved",
        "user_id": user_id,
        "user_name": current_user.get("email", current_user.get("name", "Usuario")),
        "comments": data.comments if data else None,
        "timestamp": now_iso()
    }
    
    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {
            "$set": {
                "status": "approved",
                "approved_at": now_iso(),
                "approved_by": user_id,
                "updated_at": now_iso()
            },
            "$push": {
                "workflow_history": workflow_entry
            }
        }
    )
    
    await db.payroll_entries.update_many(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {"status": "approved"}}
    )

    # Push notification to the user who created the period
    created_by = period.get("created_by")
    if created_by:
        period_name = period.get("name", period.get("period_name", period_id))
        await send_push_to_user(
            user_id=created_by,
            title="Nomina Aprobada",
            body=f"El periodo de nomina '{period_name}' ha sido aprobado y esta listo para pago.",
            url="/payroll",
        )

    # Auto-generate journal entry if company setting enabled
    settings = await db.company_settings.find_one({"company_id": company_id}, {"_id": 0})
    auto_je = (settings or {}).get("auto_journal_entry", True)
    je_id = None
    if auto_je:
        je_id = await generate_payroll_journal_entry(period_id, company_id, user_id, trigger="approve")

    return {"message": "Período aprobado correctamente", "status": "approved", "journal_entry_id": je_id}


@router.post("/periods/{period_id}/reject")
async def reject_period(period_id: str, data: ApprovalRequest, current_user: dict = Depends(get_current_user)):
    """Reject a payroll period (Pending Approval -> Draft)"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    user_permissions = current_user.get("permissions", [])
    user_role = current_user.get("role", "")
    can_approve = "payroll_approve" in user_permissions or user_role in ["admin", "hr_manager", "finance_manager"]
    
    if not can_approve:
        raise HTTPException(status_code=403, detail="No tiene permisos para rechazar nóminas")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("status") not in ["pending_approval"]:
        raise HTTPException(status_code=400, detail="Solo se puede rechazar nóminas en estado 'Pendiente Aprobación'")
    
    if not data.comments:
        raise HTTPException(status_code=400, detail="Debe proporcionar un motivo para el rechazo")
    
    workflow_entry = {
        "action": "reject",
        "from_status": period.get("status"),
        "to_status": "draft",
        "user_id": user_id,
        "user_name": current_user.get("email", current_user.get("name", "Usuario")),
        "comments": data.comments,
        "timestamp": now_iso()
    }
    
    await db.payroll_periods.update_one(
        {"period_id": period_id, "company_id": company_id},
        {
            "$set": {
                "status": "draft",
                "rejected_at": now_iso(),
                "rejected_by": user_id,
                "rejection_reason": data.comments,
                "updated_at": now_iso()
            },
            "$push": {
                "workflow_history": workflow_entry
            }
        }
    )
    
    await db.payroll_entries.update_many(
        {"period_id": period_id, "company_id": company_id},
        {"$set": {"status": "draft"}}
    )

    # Push notification to the user who created the period
    created_by = period.get("created_by")
    if created_by:
        period_name = period.get("name", period.get("period_name", period_id))
        await send_push_to_user(
            user_id=created_by,
            title="Nomina Rechazada",
            body=f"El periodo de nomina '{period_name}' fue rechazado. Motivo: {data.comments}",
            url="/payroll",
        )
    
    return {"message": "Nómina rechazada y devuelta a borrador", "status": "draft", "reason": data.comments}


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
    
    # Update loan balances
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id, "loan_deduction": {"$gt": 0}},
        {"_id": 0, "employee_id": 1, "loan_deduction": 1}
    ).to_list(1000)
    
    for entry in entries:
        employee_id = entry.get("employee_id")
        deduction = entry.get("loan_deduction", 0)
        
        if deduction > 0:
            active_loans = await db.loans.find(
                {"employee_id": employee_id, "company_id": company_id, "status": "active", "deduct_from_payroll": True},
                {"_id": 0, "loan_id": 1, "monthly_payment": 1, "remaining_balance": 1}
            ).to_list(10)
            
            remaining_deduction = deduction
            for loan in active_loans:
                if remaining_deduction <= 0:
                    break
                    
                loan_id = loan.get("loan_id")
                remaining = loan.get("remaining_balance", 0)
                payment = min(remaining_deduction, loan.get("monthly_payment", 0), remaining)
                
                new_remaining = max(0, remaining - payment)
                new_status = "paid_off" if new_remaining <= 0 else "active"
                
                await db.loans.update_one(
                    {"loan_id": loan_id},
                    {"$set": {
                        "remaining_balance": new_remaining,
                        "status": new_status,
                        "last_payment_date": now_iso(),
                        "updated_at": now_iso()
                    }}
                )
                
                remaining_deduction -= payment
    
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

    return {"message": "Nomina pagada correctamente", "status": "paid", "journal_entry_id": je_id}


@router.post("/periods/{period_id}/toggle-auto-je")
async def toggle_auto_journal_entry(period_id: str, current_user: dict = Depends(get_current_user)):
    """Toggle auto journal entry generation for company"""
    company_id = current_user.get("company_id")
    settings = await db.company_settings.find_one({"company_id": company_id}, {"_id": 0})
    current = (settings or {}).get("auto_journal_entry", True)
    new_val = not current
    await db.company_settings.update_one(
        {"company_id": company_id},
        {"$set": {"auto_journal_entry": new_val}},
        upsert=True
    )
    return {"auto_journal_entry": new_val, "message": f"Generación automática de asientos {'activada' if new_val else 'desactivada'}"}


@router.post("/periods/{period_id}/generate-je")
async def manual_generate_je(period_id: str, current_user: dict = Depends(get_current_user)):
    """Manually generate or update a journal entry for a payroll period."""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id}, {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    if period.get("status") not in ["approved", "paid"]:
        raise HTTPException(status_code=400, detail="Solo se pueden generar asientos para períodos aprobados o pagados")
    
    je_id = await generate_payroll_journal_entry(period_id, company_id, user_id, trigger="manual")
    return {"message": "Asiento de diario generado correctamente", "journal_entry_id": je_id}


@router.delete("/periods/{period_id}/journal-entry")
async def delete_period_je(period_id: str, current_user: dict = Depends(get_current_user)):
    """Delete the journal entry linked to a payroll period."""
    company_id = current_user.get("company_id")
    je_id = await delete_payroll_journal_entry(period_id, company_id)
    if not je_id:
        raise HTTPException(status_code=404, detail="No hay asiento vinculado a este período")
    return {"message": "Asiento de diario eliminado", "deleted_entry_id": je_id}


@router.get("/periods/{period_id}/workflow-history")
async def get_workflow_history(period_id: str, current_user: dict = Depends(get_current_user)):
    """Get the approval workflow history for a payroll period"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "workflow_history": 1, "status": 1, "created_at": 1, "created_by": 1}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    history = period.get("workflow_history", [])
    
    if not history:
        history = [{
            "action": "created",
            "from_status": None,
            "to_status": "draft",
            "user_id": period.get("created_by"),
            "timestamp": period.get("created_at")
        }]
    
    return {
        "period_id": period_id,
        "current_status": period.get("status"),
        "history": history
    }


# ===================== TEMPLATES =====================

@router.get("/templates")
async def get_payroll_templates(current_user: dict = Depends(get_current_user)):
    """Get payroll templates"""
    company_id = current_user.get("company_id")
    templates = await db.payroll_templates.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(100)
    return templates


@router.post("/templates")
async def create_payroll_template(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a payroll template"""
    company_id = current_user.get("company_id")
    template_id = generate_id("tpl")
    
    template = {
        "template_id": template_id,
        "company_id": company_id,
        "name": data.get("name", "Nueva Plantilla"),
        "payroll_type": data.get("payroll_type", "REG"),
        "period_type": data.get("period_type", "quincenal_1"),
        "department_filter": data.get("department_filter"),
        "employee_ids": data.get("employee_ids", []),
        "currency": data.get("currency", "DOP"),
        "default_exchange_rate": data.get("default_exchange_rate"),
        "project_id": data.get("project_id"),
        "created_at": now_iso()
    }
    
    await db.payroll_templates.insert_one(template)
    return {"template_id": template_id, "message": "Plantilla creada"}


@router.put("/templates/{template_id}")
async def update_payroll_template(template_id: str, data: dict, current_user: dict = Depends(get_current_user)):
    """Update a payroll template"""
    company_id = current_user.get("company_id")
    
    await db.payroll_templates.update_one(
        {"template_id": template_id, "company_id": company_id},
        {"$set": {**data, "updated_at": now_iso()}}
    )
    return {"message": "Plantilla actualizada"}


@router.delete("/templates/{template_id}")
async def delete_payroll_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a payroll template"""
    company_id = current_user.get("company_id")
    await db.payroll_templates.delete_one({"template_id": template_id, "company_id": company_id})
    return {"message": "Plantilla eliminada"}



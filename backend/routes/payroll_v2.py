"""
Payroll V2 Routes - FortexaRH
Advanced payroll management with TSS compliance for Dominican Republic
"""
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import io
import csv

# Import shared constants
from utils.payroll_constants import (
    SFS_EMPLOYEE_RATE, AFP_EMPLOYEE_RATE,
    SFS_EMPLOYER_RATE, AFP_EMPLOYER_RATE, SRL_EMPLOYER_RATE, INFOTEP_EMPLOYER_RATE,
    PAYROLL_TYPES, PAYROLL_NOVELTY_TYPES, ISR_OBREROS_RATE,
    PayrollPeriodCreateV2, PayrollNoveltyCreate, PayrollPaymentRequest,
    calculate_isr_monthly, generate_id, now_iso
)

router = APIRouter(prefix="/payroll-v2", tags=["Payroll V2"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


async def get_current_user(request: Request, credentials=Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


# ===================== PYDANTIC MODELS =====================

class PayrollEntryCreate(BaseModel):
    """Entrada de nómina individual por empleado"""
    period_id: str
    employee_id: str
    base_salary: float
    overtime_day_hours: float = 0
    overtime_day_rate: float = 35
    overtime_night_hours: float = 0
    overtime_night_rate: float = 15
    overtime_weekend_hours: float = 0
    overtime_weekend_rate: float = 100
    overtime_holiday_hours: float = 0
    overtime_holiday_rate: float = 100
    bonuses: float = 0
    commissions: float = 0
    other_income: float = 0
    additional_deductions: Optional[List[Dict[str, Any]]] = []


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
            # Obreros NG uses regular salary calculation
            if period.get("period_type", "").startswith("quincenal"):
                salary = salary / 2
        
        entry_id = generate_id("pe")
        
        # For OBREROS_NG payroll type, only apply ISR 2% - no TSS deductions
        if payroll_type == "OBREROS_NG":
            # Only ISR 2% retention for construction workers (Norma General 07-2027)
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
                # No TSS deductions for OBREROS_NG
                "sfs_employee": 0,
                "afp_employee": 0,
                "isr": isr_obreros,  # Only 2% ISR retention
                "isr_obreros_rate": ISR_OBREROS_RATE,
                "additional_deductions": [],
                "total_additional_deductions": 0,
                "total_deductions": isr_obreros,
                "net_salary": round(salary - isr_obreros, 2),
                # No employer TSS contributions for OBREROS_NG
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
                "sfs_employee": round(salary * SFS_EMPLOYEE_RATE, 2),
                "afp_employee": round(salary * AFP_EMPLOYEE_RATE, 2),
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
            entry["isr"] = isr_result["isr_monthly"]
            
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
    
    gross_salary = data.base_salary + overtime_day_amount + overtime_night_amount + overtime_weekend_amount + overtime_holiday_amount + data.bonuses + data.commissions + data.other_income
    
    sfs_employee = round(gross_salary * SFS_EMPLOYEE_RATE, 2)
    afp_employee = round(gross_salary * AFP_EMPLOYEE_RATE, 2)
    isr_result = calculate_isr_monthly(gross_salary)
    isr = isr_result["isr_monthly"]
    
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


# ===================== EXPORT ENDPOINTS =====================

@router.get("/periods/{period_id}/export/excel")
async def export_period_excel(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export payroll period to Excel format - Returns JSON for frontend processing"""
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
    ).sort("employee_name", 1).to_list(1000)
    
    # Get company name
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "name": 1}
    )
    company_name = company.get("name", "Sin Nombre") if company else "Sin Nombre"
    
    # Build structured response
    columns = [
        "No", "Cédula", "Nombre", "Cargo", "Departamento",
        "Salario Base", "Comisiones", "Bonos", "HE Diurnas", "HE Nocturnas",
        "HE Fin Semana", "HE Feriados", "Otros Ingresos", "Total Ingresos",
        "SFS", "AFP", "ISR", "Otros Descuentos", "Total Descuentos", "Neto"
    ]
    
    rows = []
    totals = {
        "salario_base": 0, "comisiones": 0, "bonos": 0,
        "he_diurnas": 0, "he_nocturnas": 0, "he_finsemana": 0, "he_feriados": 0,
        "otros_ingresos": 0, "total_ingresos": 0,
        "sfs": 0, "afp": 0, "isr": 0, "otros_descuentos": 0,
        "total_descuentos": 0, "neto": 0
    }
    
    for idx, entry in enumerate(entries, 1):
        he_diurnas = entry.get("overtime_day_amount", 0)
        he_nocturnas = entry.get("overtime_night_amount", 0)
        he_finsemana = entry.get("overtime_weekend_amount", 0)
        he_feriados = entry.get("overtime_holiday_amount", 0)
        otros_descuentos = entry.get("total_additional_deductions", 0)
        
        row = {
            "no": idx,
            "cedula": entry.get("employee_document", ""),
            "nombre": entry.get("employee_name", ""),
            "cargo": entry.get("position", ""),
            "departamento": entry.get("department", ""),
            "salario_base": round(entry.get("base_salary", 0), 2),
            "comisiones": round(entry.get("commissions", 0), 2),
            "bonos": round(entry.get("bonuses", 0), 2),
            "he_diurnas": round(he_diurnas, 2),
            "he_nocturnas": round(he_nocturnas, 2),
            "he_finsemana": round(he_finsemana, 2),
            "he_feriados": round(he_feriados, 2),
            "otros_ingresos": round(entry.get("other_income", 0), 2),
            "total_ingresos": round(entry.get("gross_salary", 0), 2),
            "sfs": round(entry.get("sfs_employee", 0), 2),
            "afp": round(entry.get("afp_employee", 0), 2),
            "isr": round(entry.get("isr", 0), 2),
            "otros_descuentos": round(otros_descuentos, 2),
            "total_descuentos": round(entry.get("total_deductions", 0), 2),
            "neto": round(entry.get("net_salary", 0), 2)
        }
        rows.append(row)
        
        # Accumulate totals
        totals["salario_base"] += row["salario_base"]
        totals["comisiones"] += row["comisiones"]
        totals["bonos"] += row["bonos"]
        totals["he_diurnas"] += row["he_diurnas"]
        totals["he_nocturnas"] += row["he_nocturnas"]
        totals["he_finsemana"] += row["he_finsemana"]
        totals["he_feriados"] += row["he_feriados"]
        totals["otros_ingresos"] += row["otros_ingresos"]
        totals["total_ingresos"] += row["total_ingresos"]
        totals["sfs"] += row["sfs"]
        totals["afp"] += row["afp"]
        totals["isr"] += row["isr"]
        totals["otros_descuentos"] += row["otros_descuentos"]
        totals["total_descuentos"] += row["total_descuentos"]
        totals["neto"] += row["neto"]
    
    # Round totals
    for key in totals:
        totals[key] = round(totals[key], 2)
    
    return {
        "company_name": company_name,
        "period": {
            "period_id": period.get("period_id"),
            "description": period.get("description", ""),
            "start_date": period.get("start_date", ""),
            "end_date": period.get("end_date", ""),
            "period_type": period.get("period_type", ""),
            "status": period.get("status", "")
        },
        "columns": columns,
        "rows": rows,
        "totals": totals,
        "employee_count": len(entries)
    }


@router.get("/periods/{period_id}/export/tss-autodeterminacion")
async def export_tss_autodeterminacion(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export TSS Autodetermination file"""
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
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    rnc = company.get("rnc", "") if company else ""
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow([
        "RNC_PATRONO", "CEDULA", "TIPO_CEDULA", "NSS",
        "NOMBRE", "APELLIDO1", "APELLIDO2",
        "SEXO", "FECHA_NACIMIENTO", "SALARIO_COTIZABLE",
        "APORTE_VOLUNTARIO", "SFS_EMPLEADOR", "SFS_EMPLEADO",
        "AFP_EMPLEADOR", "AFP_EMPLEADO", "SRL", "INFOTEP"
    ])
    
    for entry in entries:
        cedula = entry.get("employee_document", "").replace("-", "")
        name_parts = entry.get("employee_name", "").split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name1 = name_parts[-1] if len(name_parts) > 1 else ""
        last_name2 = name_parts[-2] if len(name_parts) > 2 else ""
        
        writer.writerow([
            rnc.replace("-", ""),
            cedula,
            "C",
            "",
            first_name,
            last_name1,
            last_name2,
            "M",
            "",
            entry.get("gross_salary", 0),
            0,
            entry.get("sfs_employer", 0),
            entry.get("sfs_employee", 0),
            entry.get("afp_employer", 0),
            entry.get("afp_employee", 0),
            entry.get("srl_employer", 0),
            entry.get("infotep_employer", 0)
        ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=TSS_Autodeterminacion_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/tss-novedades")
async def export_tss_novedades(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export TSS Novedades file"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    rnc = company.get("rnc", "") if company else ""
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow([
        "RNC_PATRONO", "CEDULA", "TIPO_NOVEDAD", "FECHA_NOVEDAD",
        "MOTIVO", "OBSERVACIONES"
    ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=TSS_Novedades_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/ir3")
async def export_ir3(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export IR-3 report"""
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
    
    total_isr = sum(e.get("isr", 0) for e in entries)
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow(["DECLARACIÓN IR-3 - RETENCIONES DE ASALARIADOS"])
    writer.writerow([])
    writer.writerow(["Empresa:", company.get("name", "") if company else ""])
    writer.writerow(["RNC:", company.get("rnc", "") if company else ""])
    writer.writerow(["Período:", f"{period.get('month', '')}/{period.get('year', '')}"])
    writer.writerow([])
    writer.writerow(["RESUMEN"])
    writer.writerow(["Total Empleados:", len(entries)])
    writer.writerow(["Total Salarios Brutos:", f"RD$ {total_gross:,.2f}"])
    writer.writerow(["Total ISR Retenido:", f"RD$ {total_isr:,.2f}"])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=IR3_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/ir4")
async def export_ir4(period_id: str, current_user: dict = Depends(get_current_user)):
    """Export IR-4 report (detail)"""
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
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow([
        "Cédula", "Nombre", "Salario Bruto", "ISR Retenido"
    ])
    
    for entry in entries:
        if entry.get("isr", 0) > 0:
            writer.writerow([
                entry.get("employee_document", ""),
                entry.get("employee_name", ""),
                entry.get("gross_salary", 0),
                entry.get("isr", 0)
            ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=IR4_{period_id}.xls"}
    )


@router.get("/periods/{period_id}/export/ir17")
async def export_ir17(period_id: str, current_user: dict = Depends(get_current_user)):
    """
    Export IR-17 report - Otras Retenciones y Retribuciones Complementarias
    Formato oficial DGII con todos los códigos de retención
    """
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_name = company.get("name", "") if company else ""
    company_rnc = company.get("rnc", "") if company else ""
    
    # Códigos oficiales DGII IR-17 con tasas
    ir17_codes = {
        1: {"name": "ALQUILERES", "rate": 10.00, "total": 0},
        2: {"name": "HONORARIOS POR SERVICIOS INDEPENDIENTES", "rate": 10.00, "total": 0},
        3: {"name": "PREMIOS (Ley 253-12)", "rate": 25.00, "total": 0},
        4: {"name": "TRANSFERENCIA DE TÍTULO Y PROPIEDADES", "rate": 2.00, "total": 0},
        5: {"name": "DIVIDENDOS (Ley 253-12)", "rate": 10.00, "total": 0},
        6: {"name": "INTERESES A PERSONAS JURÍDICAS NO RESIDENTES (Ley 253-12)", "rate": 10.00, "total": 0},
        7: {"name": "INTERESES A PERSONAS JURÍDICAS NO RESIDENTES (Ley 57-2007)", "rate": 5.00, "total": 0},
        8: {"name": "INTERESES A PERSONAS FÍSICAS NO RESIDENTES (Ley 253-12)", "rate": 10.00, "total": 0},
        9: {"name": "INTERESES A PERSONAS FÍSICAS NO RESIDENTES (Leyes 57-2007 y 253-12)", "rate": 5.00, "total": 0},
        10: {"name": "REMESAS AL EXTERIOR (Ley 253-12)", "rate": 27.00, "total": 0},
        11: {"name": "INTERESES PAGADOS POR ENTIDADES NO FINANCIERAS A PF RESIDENTES", "rate": 10.00, "total": 0},
        12: {"name": "PAGOS A PROVEEDORES DEL ESTADO (Ley 253-12)", "rate": 5.00, "total": 0},
        13: {"name": "JUEGOS TELEFÓNICOS (Norma 08-2011)", "rate": 5.00, "total": 0},
        14: {"name": "GANANCIA DE CAPITAL (Norma 07-2011)", "rate": 1.00, "total": 0},
        15: {"name": "JUEGOS VÍA INTERNET (Ley 139-11, Art. 7)", "rate": 10.00, "total": 0},
        16: {"name": "OTRAS RENTAS (Ley 11-92, Art. 309 Lit. f)", "rate": 10.00, "total": 0},
        17: {"name": "OTRAS RENTAS (Decreto 139-98, Art. 70 Lit. a y b)", "rate": 2.00, "total": 0},
        18: {"name": "OTRAS RETENCIONES - OBREROS CONSTRUCCIÓN (Norma 07-2007)", "rate": 2.00, "total": 0},
        19: {"name": "INTERESES POR ENTIDADES FINANCIERAS A PJ RESIDENTES (Norma 13-2011)", "rate": 1.00, "total": 0},
        20: {"name": "INTERESES POR ENTIDADES FINANCIERAS A PF RESIDENTES (Ley 253-12)", "rate": 10.00, "total": 0},
        21: {"name": "ADQUISICIÓN BIENES - GANADERÍA BOVINA (Norma 04-25)", "rate": 1.00, "total": 0},
    }
    
    # Get expenses/payments
    expenses = await db.expenses.find(
        {
            "company_id": company_id,
            "status": "approved",
            "expense_date": {
                "$gte": f"{period.get('year')}-{period.get('month'):02d}-01",
                "$lte": f"{period.get('year')}-{period.get('month'):02d}-31"
            }
        },
        {"_id": 0}
    ).to_list(500)
    
    # Get payroll entries for Obreros NG (code 18)
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id, "payroll_type": "OBREROS_NG"},
        {"_id": 0}
    ).to_list(1000)
    
    # Process Obreros NG - ISR 2% goes to code 18
    for entry in entries:
        isr = entry.get("isr", 0)
        if isr > 0:
            ir17_codes[18]["total"] += entry.get("gross_salary", 0)
    
    # Categorize expenses
    for expense in expenses:
        category = expense.get("category", "").lower()
        amount = expense.get("amount", 0)
        code = expense.get("ir17_code", 0)  # Allow explicit code assignment
        
        if code and code in ir17_codes:
            ir17_codes[code]["total"] += amount
        elif "alquiler" in category or "renta" in category:
            ir17_codes[1]["total"] += amount
        elif "honorario" in category or "servicio" in category:
            ir17_codes[2]["total"] += amount
        elif "premio" in category:
            ir17_codes[3]["total"] += amount
        elif "dividendo" in category:
            ir17_codes[5]["total"] += amount
        elif "interes" in category:
            ir17_codes[11]["total"] += amount
        else:
            ir17_codes[16]["total"] += amount  # Default: Otras Rentas
    
    # Generate Excel report
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    # Header
    writer.writerow(["FORMULARIO IR-17 - DECLARACIÓN JURADA DE OTRAS RETENCIONES"])
    writer.writerow([])
    writer.writerow(["RNC/Cédula del Agente de Retención:", company_rnc])
    writer.writerow(["Nombre/Razón Social:", company_name])
    writer.writerow(["Período Fiscal:", f"{period.get('month'):02d}/{period.get('year')}"])
    writer.writerow([])
    
    # Section: DETALLE DE LA RENTA NETA IMPONIBLE
    writer.writerow(["DETALLE DE LA RENTA NETA IMPONIBLE O PÉRDIDA FISCAL"])
    writer.writerow([])
    writer.writerow(["No.", "CONCEPTO", "TASA %", "MONTO IMPONIBLE (RD$)", "IMPUESTO RETENIDO (RD$)"])
    
    total_imponible = 0
    total_retenido = 0
    
    for code, data in ir17_codes.items():
        monto = data["total"]
        tasa = data["rate"]
        retencion = round(monto * tasa / 100, 2)
        
        writer.writerow([
            f"{code}.",
            data["name"],
            f"{tasa:.2f}%",
            f"{monto:,.2f}" if monto > 0 else "-",
            f"{retencion:,.2f}" if retencion > 0 else "-"
        ])
        
        total_imponible += monto
        total_retenido += retencion
    
    writer.writerow([])
    writer.writerow(["", "TOTAL MONTO IMPONIBLE", "", f"{total_imponible:,.2f}", ""])
    writer.writerow(["", "TOTAL IMPUESTO A PAGAR", "", "", f"{total_retenido:,.2f}"])
    
    content = "\ufeff" + output.getvalue()
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=IR17_{period.get('month'):02d}_{period.get('year')}.xls"}
    )


@router.get("/periods/{period_id}/export/ir6")
async def export_ir6(period_id: str, current_user: dict = Depends(get_current_user)):
    """
    Export IR-6 report - Anexo de Otras Retenciones del IR-17
    Formato oficial DGII con columnas requeridas
    """
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_name = company.get("name", "") if company else ""
    company_rnc = company.get("rnc", "") if company else ""
    
    # Códigos de concepto para IR-6
    concept_codes = {
        1: "ALQUILERES",
        2: "HONORARIOS",
        3: "PREMIOS",
        4: "TRANSFERENCIAS",
        5: "DIVIDENDOS",
        6: "INTERESES PJ NO RES",
        7: "INTERESES PJ NO RES 5%",
        8: "INTERESES PF NO RES",
        9: "INTERESES PF NO RES 5%",
        10: "REMESAS EXTERIOR",
        11: "INTERESES PF RES",
        12: "PROVEEDORES ESTADO",
        13: "JUEGOS TEL",
        14: "GANANCIA CAPITAL",
        15: "JUEGOS INTERNET",
        16: "OTRAS RENTAS",
        17: "OTRAS RENTAS 2%",
        18: "OBREROS CONST.",
        19: "INTERESES PJ FIN",
        20: "INTERESES PF FIN",
        21: "GANADERÍA",
    }
    
    # Get expenses
    expenses = await db.expenses.find(
        {
            "company_id": company_id,
            "status": "approved",
            "expense_date": {
                "$gte": f"{period.get('year')}-{period.get('month'):02d}-01",
                "$lte": f"{period.get('year')}-{period.get('month'):02d}-31"
            }
        },
        {"_id": 0}
    ).to_list(500)
    
    # Get Obreros NG entries
    obreros_entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id, "payroll_type": "OBREROS_NG"},
        {"_id": 0}
    ).to_list(1000)
    
    # Get suppliers lookup
    suppliers = await db.suppliers.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(500)
    supplier_lookup = {s.get("supplier_id"): s for s in suppliers}
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    # Header
    writer.writerow(["ANEXO IR-6 - DETALLE DE OTRAS RETENCIONES"])
    writer.writerow([])
    writer.writerow(["RNC/Cédula Agente Retención:", company_rnc])
    writer.writerow(["Nombre/Razón Social:", company_name])
    writer.writerow(["Período:", f"{period.get('month'):02d}/{period.get('year')}"])
    writer.writerow([])
    
    # Column headers matching DGII format
    writer.writerow([
        "FECHA",
        "MES",
        "DÍA", 
        "FORMA DE PAGO",
        "NOMBRE DEL BENEFICIADO",
        "RNC/CÉDULA O PASAPORTE",
        "DIRECCIÓN",
        "CÓDIGO CONCEPTO",
        "MONTO DEL PAGO (RD$)",
        "MONTO SUJETO A RETENCIÓN (RD$)",
        "TASA",
        "IMPUESTO RETENIDO (RD$)"
    ])
    
    total_pago = 0
    total_sujeto = 0
    total_retenido = 0
    row_count = 0
    
    # Process expenses
    for expense in expenses:
        amount = expense.get("amount", 0)
        if amount <= 0:
            continue
        
        # Determine code and rate
        category = expense.get("category", "").lower()
        code = expense.get("ir17_code", 16)  # Default: 16 - Otras Rentas
        
        if "alquiler" in category:
            code, rate = 1, 10.00
        elif "honorario" in category or "servicio" in category:
            code, rate = 2, 10.00
        elif "premio" in category:
            code, rate = 3, 25.00
        elif "dividendo" in category:
            code, rate = 5, 10.00
        elif "interes" in category:
            code, rate = 11, 10.00
        else:
            code, rate = 16, 10.00
        
        retencion = round(amount * rate / 100, 2)
        
        # Parse date
        expense_date = expense.get("expense_date", "")
        mes = expense_date[5:7] if len(expense_date) >= 7 else ""
        dia = expense_date[8:10] if len(expense_date) >= 10 else ""
        
        # Get supplier info
        supplier_id = expense.get("supplier_id")
        supplier = supplier_lookup.get(supplier_id, {})
        
        writer.writerow([
            expense_date,
            mes,
            dia,
            expense.get("payment_method", "TRANSFERENCIA"),
            expense.get("vendor_name", supplier.get("name", "")),
            expense.get("vendor_rnc", supplier.get("rnc", "")),
            supplier.get("address", ""),
            code,
            f"{amount:,.2f}",
            f"{amount:,.2f}",
            f"{rate:.2f}%",
            f"{retencion:,.2f}"
        ])
        
        total_pago += amount
        total_sujeto += amount
        total_retenido += retencion
        row_count += 1
    
    # Add Obreros NG entries (code 18)
    for entry in obreros_entries:
        gross = entry.get("gross_salary", 0)
        isr = entry.get("isr", 0)
        if isr <= 0:
            continue
        
        writer.writerow([
            "",
            f"{period.get('month'):02d}",
            "15",  # Mid-month for payroll
            "NÓMINA",
            entry.get("employee_name", ""),
            entry.get("employee_document", ""),
            "",
            18,  # Obreros Construcción
            f"{gross:,.2f}",
            f"{gross:,.2f}",
            "2.00%",
            f"{isr:,.2f}"
        ])
        
        total_pago += gross
        total_sujeto += gross
        total_retenido += isr
        row_count += 1
    
    # Totals row
    writer.writerow([])
    writer.writerow([
        "TOTALES",
        "",
        "",
        "",
        f"{row_count} registros",
        "",
        "",
        "",
        f"{total_pago:,.2f}",
        f"{total_sujeto:,.2f}",
        "",
        f"{total_retenido:,.2f}"
    ])
    
    content = "\ufeff" + output.getvalue()
    return Response(
        content=content.encode("utf-8"),
        media_type="application/vnd.ms-excel; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=IR6_Anexo_{period.get('month'):02d}_{period.get('year')}.xls"}
    )


@router.get("/periods/{period_id}/dgii-preview")
async def preview_dgii_reports(period_id: str, current_user: dict = Depends(get_current_user)):
    """
    Preview all DGII reports data for a period (IR-3, IR-17, IR-6)
    Returns JSON with summary data for preview before download
    """
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    
    # Get payroll entries for IR-3
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    # IR-3 data
    total_isr_asalariados = sum(e.get("isr", 0) for e in entries)
    total_gross = sum(e.get("gross_salary", 0) for e in entries)
    employees_with_isr = len([e for e in entries if e.get("isr", 0) > 0])
    
    # Get expenses for IR-17/IR-6
    expenses = await db.expenses.find(
        {
            "company_id": company_id,
            "status": "approved",
            "expense_date": {
                "$gte": f"{period.get('year')}-{period.get('month'):02d}-01",
                "$lte": f"{period.get('year')}-{period.get('month'):02d}-31"
            }
        },
        {"_id": 0}
    ).to_list(500)
    
    # Calculate IR-17 totals
    total_otras_retenciones = 0
    for expense in expenses:
        amount = expense.get("amount", 0)
        category = expense.get("category", "").lower()
        if "premio" in category:
            total_otras_retenciones += amount * 0.15
        else:
            total_otras_retenciones += amount * 0.10
    
    # Retribuciones complementarias
    total_retrib = sum(e.get("bonuses", 0) + e.get("other_income", 0) for e in entries)
    retrib_retencion = total_retrib * 0.27
    
    return {
        "period": {
            "period_id": period_id,
            "month": period.get("month"),
            "year": period.get("year"),
            "description": period.get("description", "")
        },
        "company": {
            "name": company.get("name", "") if company else "",
            "rnc": company.get("rnc", "") if company else ""
        },
        "ir3": {
            "name": "IR-3 - Retenciones de Asalariados",
            "total_employees": len(entries),
            "employees_with_isr": employees_with_isr,
            "total_gross": round(total_gross, 2),
            "total_isr": round(total_isr_asalariados, 2)
        },
        "ir17": {
            "name": "IR-17 - Otras Retenciones",
            "total_otras_retenciones": round(total_otras_retenciones, 2),
            "total_retrib_complementarias": round(retrib_retencion, 2),
            "total_ir17": round(total_otras_retenciones + retrib_retencion, 2),
            "expense_count": len(expenses)
        },
        "ir6": {
            "name": "IR-6 - Anexo Detalle Retenciones",
            "record_count": len(expenses),
            "total_retenido": round(total_otras_retenciones, 2)
        },
        "total_a_pagar_dgii": round(total_isr_asalariados + total_otras_retenciones + retrib_retencion, 2)
    }


@router.get("/annual-report/ir13/{year}")
async def export_ir13(year: int, current_user: dict = Depends(get_current_user)):
    """Export IR-13 annual report"""
    company_id = current_user.get("company_id")
    
    periods = await db.payroll_periods.find(
        {"company_id": company_id, "year": year},
        {"_id": 0}
    ).to_list(100)
    
    if not periods:
        raise HTTPException(status_code=404, detail="No hay períodos para este año")
    
    all_entries = []
    for period in periods:
        entries = await db.payroll_entries.find(
            {"period_id": period["period_id"], "company_id": company_id},
            {"_id": 0}
        ).to_list(1000)
        all_entries.extend(entries)
    
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    
    employee_totals = {}
    for entry in all_entries:
        emp_id = entry.get("employee_id")
        if emp_id not in employee_totals:
            employee_totals[emp_id] = {
                "document": entry.get("employee_document", ""),
                "name": entry.get("employee_name", ""),
                "total_gross": 0,
                "total_isr": 0
            }
        employee_totals[emp_id]["total_gross"] += entry.get("gross_salary", 0)
        employee_totals[emp_id]["total_isr"] += entry.get("isr", 0)
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    writer.writerow(["DECLARACIÓN IR-13 - RETENCIONES ANUALES"])
    writer.writerow([])
    writer.writerow(["Empresa:", company.get("name", "") if company else ""])
    writer.writerow(["RNC:", company.get("rnc", "") if company else ""])
    writer.writerow(["Año Fiscal:", year])
    writer.writerow([])
    writer.writerow(["Cédula", "Nombre", "Total Ingresos", "Total ISR Retenido"])
    
    for emp in employee_totals.values():
        writer.writerow([
            emp["document"],
            emp["name"],
            f"{emp['total_gross']:,.2f}",
            f"{emp['total_isr']:,.2f}"
        ])
    
    content = output.getvalue()
    return Response(
        content=content,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f"attachment; filename=IR13_{year}.xls"}
    )


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


class ApprovalRequest(BaseModel):
    """Solicitud de aprobación de nómina"""
    comments: Optional[str] = None


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
    
    # Create approval workflow entry
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
    
    # Create notification for approvers (admin, hr_manager, finance_manager)
    period_desc = period.get("description", f"Período {period_id}")
    notification = {
        "notification_id": f"notif_{generate_id('')[7:]}",
        "company_id": company_id,
        "title": "Nómina Pendiente de Aprobación",
        "message": f"{user_name} ha enviado la nómina '{period_desc}' para aprobación.",
        "type": "payroll_approval",
        "priority": "high",
        "link": f"/payroll-v2?period={period_id}",
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
    
    # Check user permission for payroll approval
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
    
    # Create approval workflow entry
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
    
    return {"message": "Período aprobado correctamente", "status": "approved"}


@router.post("/periods/{period_id}/reject")
async def reject_period(period_id: str, data: ApprovalRequest, current_user: dict = Depends(get_current_user)):
    """Reject a payroll period (Pending Approval -> Draft)"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Check user permission
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
    
    # Create rejection workflow entry
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
    
    return {"message": "Nómina rechazada y devuelta a borrador", "status": "draft", "reason": data.comments}


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
    
    # Add creation entry if not in history
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


# ===================== TSS REPORT GENERATION =====================

@router.get("/periods/{period_id}/tss-report")
async def generate_tss_report(period_id: str, current_user: dict = Depends(get_current_user)):
    """
    Generate TSS (Tesorería de Seguridad Social) report in TXT format
    for SUIR+ system submission (Dominican Republic).
    
    Format: Autodeterminación Mensual (AM) - Nativo TSS
    Structure: E (Header) + D (Detail per employee) + S (Summary)
    """
    company_id = current_user.get("company_id")
    
    # Get period
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    # Check if it's a regular payroll (TSS only applies to regular payrolls)
    payroll_type = period.get("payroll_type", "REG")
    if payroll_type == "OBREROS_NG":
        raise HTTPException(
            status_code=400, 
            detail="El reporte TSS no aplica para nóminas de Obreros NG 07/2007. Este tipo de nómina solo requiere ISR 2%."
        )
    
    # Get company info for RNC
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_rnc = company.get("rnc", "000000000") if company else "000000000"
    company_name = company.get("name", "EMPRESA") if company else "EMPRESA"
    
    # Get payroll entries for this period
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    if not entries:
        raise HTTPException(status_code=400, detail="No hay empleados en este período de nómina")
    
    # Build TSS file content
    year = period.get("year", datetime.now().year)
    month = period.get("month", datetime.now().month)
    period_str = f"{month:02d}{year}"
    
    lines = []
    
    # === HEADER (E) ===
    # Format: E|RNC|Period|CompanyName
    header = f"E|{company_rnc}|{period_str}|{company_name}"
    lines.append(header)
    
    # === DETAIL (D) - One per employee ===
    total_salario_cotizable = 0
    total_sfs_empleado = 0
    total_afp_empleado = 0
    total_sfs_patronal = 0
    total_afp_patronal = 0
    total_srl = 0
    total_infotep = 0
    employee_count = 0
    
    for entry in entries:
        # Get employee cedula
        employee_doc = entry.get("employee_document", "")
        employee_name = entry.get("employee_name", "")
        
        # Salario cotizable (gross salary for TSS purposes)
        salario_cotizable = entry.get("gross_salary", 0)
        
        # Employee contributions
        sfs_empleado = entry.get("sfs_employee", 0)
        afp_empleado = entry.get("afp_employee", 0)
        
        # Employer contributions
        sfs_patronal = entry.get("sfs_employer", 0)
        afp_patronal = entry.get("afp_employer", 0)
        srl = entry.get("srl_employer", 0)
        infotep = entry.get("infotep_employer", 0)
        
        # Format: D|Cedula|Name|SalarioCotizable|SFSEmpleado|AFPEmpleado|SFSPatronal|AFPPatronal|SRL|INFOTEP
        detail_line = (
            f"D|{employee_doc}|{employee_name}|"
            f"{salario_cotizable:.2f}|{sfs_empleado:.2f}|{afp_empleado:.2f}|"
            f"{sfs_patronal:.2f}|{afp_patronal:.2f}|{srl:.2f}|{infotep:.2f}"
        )
        lines.append(detail_line)
        
        # Accumulate totals
        total_salario_cotizable += salario_cotizable
        total_sfs_empleado += sfs_empleado
        total_afp_empleado += afp_empleado
        total_sfs_patronal += sfs_patronal
        total_afp_patronal += afp_patronal
        total_srl += srl
        total_infotep += infotep
        employee_count += 1
    
    # === SUMMARY (S) ===
    # Format: S|TotalRegistros|TotalSalario|TotalSFSEmp|TotalAFPEmp|TotalSFSPat|TotalAFPPat|TotalSRL|TotalINFOTEP
    summary = (
        f"S|{employee_count}|{total_salario_cotizable:.2f}|"
        f"{total_sfs_empleado:.2f}|{total_afp_empleado:.2f}|"
        f"{total_sfs_patronal:.2f}|{total_afp_patronal:.2f}|"
        f"{total_srl:.2f}|{total_infotep:.2f}"
    )
    lines.append(summary)
    
    # Join all lines
    content = "\r\n".join(lines)
    
    # Generate filename: AM_RNC_MMYYYY.txt
    filename = f"AM_{company_rnc}_{period_str}.txt"
    
    return Response(
        content=content.encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/periods/{period_id}/tss-preview")
async def preview_tss_report(period_id: str, current_user: dict = Depends(get_current_user)):
    """
    Preview TSS report data as JSON before downloading.
    Shows all employee contributions and totals.
    """
    company_id = current_user.get("company_id")
    
    # Get period
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    payroll_type = period.get("payroll_type", "REG")
    if payroll_type == "OBREROS_NG":
        return {
            "error": True,
            "message": "El reporte TSS no aplica para nóminas de Obreros NG 07/2007",
            "reason": "Este tipo de nómina solo requiere retención de ISR 2% sobre mano de obra, sin aportes a la TSS."
        }
    
    # Get company info
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    company_rnc = company.get("rnc", "000000000") if company else "000000000"
    company_name = company.get("name", "EMPRESA") if company else "EMPRESA"
    
    # Get payroll entries
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    year = period.get("year", datetime.now().year)
    month = period.get("month", datetime.now().month)
    
    # Build preview data
    employees = []
    totals = {
        "salario_cotizable": 0,
        "sfs_empleado": 0,
        "afp_empleado": 0,
        "total_empleado": 0,
        "sfs_patronal": 0,
        "afp_patronal": 0,
        "srl": 0,
        "infotep": 0,
        "total_patronal": 0
    }
    
    for entry in entries:
        emp_data = {
            "cedula": entry.get("employee_document", ""),
            "nombre": entry.get("employee_name", ""),
            "salario_cotizable": entry.get("gross_salary", 0),
            "sfs_empleado": entry.get("sfs_employee", 0),
            "afp_empleado": entry.get("afp_employee", 0),
            "sfs_patronal": entry.get("sfs_employer", 0),
            "afp_patronal": entry.get("afp_employer", 0),
            "srl": entry.get("srl_employer", 0),
            "infotep": entry.get("infotep_employer", 0)
        }
        emp_data["total_empleado"] = emp_data["sfs_empleado"] + emp_data["afp_empleado"]
        emp_data["total_patronal"] = emp_data["sfs_patronal"] + emp_data["afp_patronal"] + emp_data["srl"] + emp_data["infotep"]
        
        employees.append(emp_data)
        
        # Accumulate totals
        totals["salario_cotizable"] += emp_data["salario_cotizable"]
        totals["sfs_empleado"] += emp_data["sfs_empleado"]
        totals["afp_empleado"] += emp_data["afp_empleado"]
        totals["total_empleado"] += emp_data["total_empleado"]
        totals["sfs_patronal"] += emp_data["sfs_patronal"]
        totals["afp_patronal"] += emp_data["afp_patronal"]
        totals["srl"] += emp_data["srl"]
        totals["infotep"] += emp_data["infotep"]
        totals["total_patronal"] += emp_data["total_patronal"]
    
    # Round totals
    for key in totals:
        totals[key] = round(totals[key], 2)
    
    return {
        "company": {
            "rnc": company_rnc,
            "name": company_name
        },
        "period": {
            "year": year,
            "month": month,
            "description": period.get("description", ""),
            "payroll_type": payroll_type
        },
        "filename": f"AM_{company_rnc}_{month:02d}{year}.txt",
        "employee_count": len(employees),
        "employees": employees,
        "totals": totals,
        "rates": {
            "sfs_empleado": f"{SFS_EMPLOYEE_RATE * 100:.2f}%",
            "afp_empleado": f"{AFP_EMPLOYEE_RATE * 100:.2f}%",
            "sfs_patronal": f"{SFS_EMPLOYER_RATE * 100:.2f}%",
            "afp_patronal": f"{AFP_EMPLOYER_RATE * 100:.2f}%",
            "srl": f"{SRL_EMPLOYER_RATE * 100:.2f}%",
            "infotep": f"{INFOTEP_EMPLOYER_RATE * 100:.2f}%"
        }
    }

"""
Payroll (Basic) Routes - FortexaRH
Handles basic payroll operations
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/payroll", tags=["Payroll"])

db = None
get_current_user = None


def init_router(database, auth_func):
    global db, get_current_user
    db = database
    get_current_user = auth_func


class PayrollCreate(BaseModel):
    employee_id: str
    period_start: str
    period_end: str
    base_salary: float
    bonuses: float = 0
    deductions: float = 0


@router.get("")
async def get_payrolls(current_user: dict = Depends(lambda: get_current_user)):
    payrolls = await db.payrolls.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return payrolls


@router.post("")
async def create_payroll(data: PayrollCreate, current_user: dict = Depends(lambda: get_current_user)):
    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate net salary
    gross = data.base_salary + data.bonuses
    taxes = gross * 0.15  # 15% tax
    net_salary = gross - data.deductions - taxes
    
    payroll_id = f"pay_{uuid.uuid4().hex[:12]}"
    payroll = {
        "payroll_id": payroll_id,
        "company_id": current_user.get("company_id"),
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "period_start": data.period_start,
        "period_end": data.period_end,
        "base_salary": data.base_salary,
        "bonuses": data.bonuses,
        "deductions": data.deductions,
        "taxes": taxes,
        "net_salary": net_salary,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payrolls.insert_one(payroll)
    return {"payroll_id": payroll_id, "message": "Payroll created successfully"}


@router.put("/{payroll_id}/approve")
async def approve_payroll(payroll_id: str, current_user: dict = Depends(lambda: get_current_user)):
    result = await db.payrolls.update_one(
        {"payroll_id": payroll_id, "company_id": current_user.get("company_id")},
        {"$set": {"status": "approved"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payroll not found")
    return {"message": "Payroll approved successfully"}


@router.put("/{payroll_id}/pay")
async def pay_payroll(payroll_id: str, current_user: dict = Depends(lambda: get_current_user)):
    result = await db.payrolls.update_one(
        {"payroll_id": payroll_id, "company_id": current_user.get("company_id"), "status": "approved"},
        {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Payroll not found or not approved")
    return {"message": "Payroll paid successfully"}

"""
Salary History - Track salary changes per employee
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from config import db
from utils.auth import get_current_user
import uuid

router = APIRouter(prefix="/salary-history", tags=["Salary History"])


class SalaryChangeRequest(BaseModel):
    employee_id: str
    new_salary: float
    reason: str
    effective_date: Optional[str] = None
    new_position: Optional[str] = None


@router.get("/{employee_id}")
async def get_salary_history(employee_id: str, current_user: dict = Depends(get_current_user)):
    """Get salary change history for an employee"""
    company_id = current_user.get("company_id")

    employee = await db.employees.find_one(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0, "first_name": 1, "last_name": 1, "salary": 1, "position": 1, "hire_date": 1}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    history = await db.salary_history.find(
        {"employee_id": employee_id, "company_id": company_id},
        {"_id": 0}
    ).sort("effective_date", -1).to_list(100)

    return {
        "employee": employee,
        "current_salary": employee.get("salary", 0),
        "history": history
    }


@router.post("")
async def record_salary_change(data: SalaryChangeRequest, current_user: dict = Depends(get_current_user)):
    """Record a salary change for an employee"""
    company_id = current_user.get("company_id")

    employee = await db.employees.find_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    old_salary = employee.get("salary", 0)
    change_pct = ((data.new_salary - old_salary) / old_salary * 100) if old_salary > 0 else 0

    effective = data.effective_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    record = {
        "record_id": f"sh_{uuid.uuid4().hex[:12]}",
        "employee_id": data.employee_id,
        "company_id": company_id,
        "old_salary": old_salary,
        "new_salary": data.new_salary,
        "change_amount": round(data.new_salary - old_salary, 2),
        "change_percentage": round(change_pct, 2),
        "reason": data.reason,
        "old_position": employee.get("position", ""),
        "new_position": data.new_position or employee.get("position", ""),
        "effective_date": effective,
        "created_by": current_user.get("name", current_user.get("email", "")),
        "created_at": datetime.now(timezone.utc)
    }

    await db.salary_history.insert_one(record)

    # Update employee salary and position
    update_fields = {"salary": data.new_salary}
    if data.new_position:
        update_fields["position"] = data.new_position

    await db.employees.update_one(
        {"employee_id": data.employee_id, "company_id": company_id},
        {"$set": update_fields}
    )

    return {"message": "Cambio salarial registrado", "record_id": record["record_id"]}

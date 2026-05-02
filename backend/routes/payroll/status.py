"""Auto-generated module from the iter245 split of routes/payroll/workflow.py.

Do not add new logic here without extending the E2E test suite at
``/app/backend/tests/test_payroll_workflow_e2e.py``.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request

from config import db
from models.payroll import ApprovalRequest
from services.employee_notifications import create_employee_notification
from services.push_service import send_push_to_user
from utils.auth import get_current_user
from utils.payroll_constants import generate_id, now_iso

from . import router


@router.get("/periods/{period_id}/workflow-status")
async def get_period_workflow_status_endpoint(period_id: str, current_user: dict = Depends(get_current_user)):
    """Get the current workflow approval status for a period"""
    company_id = current_user.get("company_id")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    from routes.workflows import get_company_workflow, get_period_workflow_status, can_user_approve_step
    
    workflow = await get_company_workflow(company_id)
    if not workflow:
        return {"has_workflow": False}
    
    wf_status = await get_period_workflow_status(period, workflow)
    
    # Check if current user can approve the current step
    can_approve = False
    if wf_status["current_step_info"]:
        can_approve = await can_user_approve_step(current_user, wf_status["current_step_info"])
    
    return {
        "has_workflow": True,
        "workflow_name": workflow.get("name", ""),
        "current_step": wf_status["current_step"],
        "total_steps": wf_status["total_steps"],
        "fully_approved": wf_status["fully_approved"],
        "current_step_info": wf_status["current_step_info"],
        "can_current_user_approve": can_approve,
        "approvals": wf_status["approvals"],
        "all_steps": workflow.get("steps", [])
    }




@router.get("/periods/{period_id}/bank-check")
async def check_bank_info(period_id: str, current_user: dict = Depends(get_current_user)):
    """Check which employees are missing bank information for a payroll period"""
    company_id = current_user.get("company_id")
    
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "employee_id": 1, "employee_name": 1, "net_salary": 1}
    ).to_list(1000)
    
    if not entries:
        return {"total": 0, "with_bank": 0, "missing": []}
    
    employee_ids = [e.get("employee_id") for e in entries]
    employees = await db.employees.find(
        {"employee_id": {"$in": employee_ids}, "company_id": company_id},
        {"_id": 0, "employee_id": 1, "first_name": 1, "last_name": 1,
         "account_number": 1, "bank_name": 1, "account_type": 1}
    ).to_list(1000)
    
    emp_map = {e["employee_id"]: e for e in employees}
    
    missing = []
    with_bank = 0
    for entry in entries:
        emp = emp_map.get(entry.get("employee_id"), {})
        if emp.get("account_number"):
            with_bank += 1
        else:
            missing.append({
                "employee_id": entry.get("employee_id"),
                "name": entry.get("employee_name", f"{emp.get('first_name', '')} {emp.get('last_name', '')}"),
                "amount": round(entry.get("net_salary", 0), 2)
            })
    
    return {
        "total": len(entries),
        "with_bank": with_bank,
        "missing_count": len(missing),
        "missing": missing
    }




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





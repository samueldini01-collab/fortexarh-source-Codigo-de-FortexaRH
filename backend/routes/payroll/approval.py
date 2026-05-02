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
                "updated_at": now_iso(),
                "workflow_approvals": []
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
    """Approve a payroll period - supports multi-step workflow approval"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    user_permissions = current_user.get("permissions", [])
    user_role = current_user.get("role", "")
    
    period = await db.payroll_periods.find_one(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0}
    )
    if not period:
        raise HTTPException(status_code=404, detail="Período no encontrado")
    
    if period.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Período ya pagado")
    
    if period.get("status") == "approved":
        raise HTTPException(status_code=400, detail="Período ya aprobado completamente")
    
    allowed_statuses = ["pending_approval", "calculated", "open", "workflow_pending"]
    if period.get("status") not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"No se puede aprobar desde estado: {period.get('status')}")
    
    # Check for active workflow
    from routes.workflows import get_company_workflow, can_user_approve_step, get_period_workflow_status
    
    workflow = await get_company_workflow(company_id)
    
    is_final_approval = True
    step_info = None
    
    if workflow and workflow.get("steps"):
        # Multi-step workflow mode
        wf_status = await get_period_workflow_status(period, workflow)
        
        if wf_status["fully_approved"]:
            raise HTTPException(status_code=400, detail="Todos los pasos ya fueron aprobados")
        
        step_info = wf_status["current_step_info"]
        if not step_info:
            raise HTTPException(status_code=400, detail="No se encontró el paso actual del workflow")
        
        # Check if current user can approve this step
        can_approve = await can_user_approve_step(current_user, step_info)
        if not can_approve:
            approver_name = step_info.get("approver_name", "")
            step_name = step_info.get("name", f"Paso {step_info.get('step_number')}")
            raise HTTPException(
                status_code=403,
                detail=f"No autorizado. {step_name} requiere aprobación de: {approver_name}"
            )
        
        # Record this step approval
        step_approval = {
            "step_number": step_info.get("step_number"),
            "step_name": step_info.get("name"),
            "approved_by": user_id,
            "approved_by_name": current_user.get("name", current_user.get("email", "")),
            "approved_at": now_iso()
        }
        
        await db.payroll_periods.update_one(
            {"period_id": period_id, "company_id": company_id},
            {"$push": {"workflow_approvals": step_approval}}
        )
        
        # Check if this was the last step
        next_step = wf_status["current_step"] + 1
        is_final_approval = next_step > wf_status["total_steps"]
        
        if not is_final_approval:
            # Move to next step, stay in workflow_pending
            next_step_info = None
            for s in workflow.get("steps", []):
                if s.get("step_number") == next_step:
                    next_step_info = s
                    break
            
            await db.payroll_periods.update_one(
                {"period_id": period_id, "company_id": company_id},
                {
                    "$set": {
                        "status": "workflow_pending",
                        "updated_at": now_iso()
                    },
                    "$push": {
                        "workflow_history": {
                            "action": f"workflow_step_{step_info.get('step_number')}",
                            "from_status": period.get("status"),
                            "to_status": "workflow_pending",
                            "user_id": user_id,
                            "user_name": current_user.get("email", ""),
                            "comments": data.comments if data else None,
                            "timestamp": now_iso(),
                            "step_name": step_info.get("name")
                        }
                    }
                }
            )
            
            next_name = next_step_info.get("name", f"Paso {next_step}") if next_step_info else f"Paso {next_step}"
            return {
                "message": f"Paso {step_info.get('step_number')} aprobado. Pendiente: {next_name}",
                "status": "workflow_pending",
                "workflow_progress": {
                    "current_step": next_step,
                    "total_steps": wf_status["total_steps"],
                    "next_step_name": next_name
                }
            }
    else:
        # No workflow - use legacy permission check
        can_approve = "payroll_approve" in user_permissions or user_role in ["admin", "hr_manager", "finance_manager"]
        if not can_approve:
            raise HTTPException(status_code=403, detail="No tiene permisos para aprobar nóminas")
    
    # Final approval - set status to approved
    # Check for employees missing bank information
    entries = await db.payroll_entries.find(
        {"period_id": period_id, "company_id": company_id},
        {"_id": 0, "employee_id": 1}
    ).to_list(1000)
    
    employee_ids = [e.get("employee_id") for e in entries]
    employees_with_bank = await db.employees.find(
        {
            "employee_id": {"$in": employee_ids},
            "company_id": company_id,
            "account_number": {"$exists": True, "$nin": [None, ""]}
        },
        {"_id": 0, "employee_id": 1}
    ).to_list(1000)
    
    bank_ids = {e["employee_id"] for e in employees_with_bank}
    missing_bank_count = len(employee_ids) - len(bank_ids)
    missing_bank_names = []
    if missing_bank_count > 0:
        missing_emps = await db.employees.find(
            {"employee_id": {"$in": [eid for eid in employee_ids if eid not in bank_ids]}, "company_id": company_id},
            {"_id": 0, "first_name": 1, "last_name": 1}
        ).to_list(100)
        missing_bank_names = [f"{e.get('first_name', '')} {e.get('last_name', '')}" for e in missing_emps]
    
    wf_action = f"workflow_step_{step_info.get('step_number')}_final" if step_info else "approve"
    workflow_entry = {
        "action": wf_action,
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
        # Auto-sync to FortexaERP if configured
        await auto_sync_to_erp(company_id, period_id, current_user.get("email", "system"))

    response = {"message": "Período aprobado correctamente", "status": "approved", "journal_entry_id": je_id}
    
    if missing_bank_count > 0:
        response["bank_warning"] = {
            "missing_count": missing_bank_count,
            "total_employees": len(employee_ids),
            "missing_names": missing_bank_names[:10],
            "message": f"{missing_bank_count} de {len(employee_ids)} empleados no tienen datos bancarios configurados"
        }
    
    return response




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



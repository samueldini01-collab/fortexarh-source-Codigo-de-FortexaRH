"""
Payroll Approval Workflow Routes - FortexaRH
Configurable multi-step approval workflows for payroll periods.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/workflows", tags=["Workflows"])

from config import db
from utils.auth import get_current_user


class WorkflowStepCreate(BaseModel):
    step_number: int
    name: str
    approver_type: str  # "role" or "user"
    approver_role: Optional[str] = None
    approver_user_id: Optional[str] = None
    approver_name: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str
    steps: List[WorkflowStepCreate]


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    steps: Optional[List[WorkflowStepCreate]] = None
    is_active: Optional[bool] = None


# Default roles that can be used as approvers
APPROVER_ROLES = [
    {"id": "admin", "name": "Administrador"},
    {"id": "hr_manager", "name": "Gerente de RRHH"},
    {"id": "payroll_manager", "name": "Encargado de Nómina"},
    {"id": "finance_manager", "name": "Director Financiero"},
    {"id": "supervisor", "name": "Supervisor"},
]


@router.get("")
async def get_workflows(current_user: dict = Depends(get_current_user)):
    """Get all workflows for the company (Enterprise only)"""
    company_id = current_user.get("company_id")
    
    # Check if company has Enterprise plan
    company = await db.companies.find_one(
        {"company_id": company_id},
        {"_id": 0, "subscription_plan": 1}
    )
    plan = (company or {}).get("subscription_plan", "")
    is_enterprise = plan in ["enterprise", "Enterprise"]
    
    if not is_enterprise:
        return {"workflows": [], "is_enterprise": False}
    
    workflows = await db.workflows.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    return {"workflows": workflows, "is_enterprise": True}


@router.get("/announcement")
async def get_workflow_announcement(current_user: dict = Depends(get_current_user)):
    """Check if user should see the new Workflows module announcement"""
    company_id = current_user.get("company_id")
    user_id = current_user.get("user_id")
    
    # Only for Enterprise companies
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "subscription_plan": 1})
    plan = (company or {}).get("subscription_plan", "")
    if plan not in ["enterprise", "Enterprise"]:
        return {"show": False}
    
    # Check if user already dismissed it
    dismissed = await db.workflow_announcements.find_one(
        {"user_id": user_id, "dismissed": True},
        {"_id": 0}
    )
    if dismissed:
        return {"show": False}
    
    return {"show": True}


@router.post("/announcement/dismiss")
async def dismiss_workflow_announcement(current_user: dict = Depends(get_current_user)):
    """Dismiss the new Workflows module announcement"""
    user_id = current_user.get("user_id")
    
    await db.workflow_announcements.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "dismissed": True, "dismissed_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"success": True}


@router.get("/active")
async def get_active_workflow(current_user: dict = Depends(get_current_user)):
    """Get the active payroll approval workflow"""
    company_id = current_user.get("company_id")
    
    workflow = await db.workflows.find_one(
        {"company_id": company_id, "is_active": True, "type": "payroll"},
        {"_id": 0}
    )
    
    return {"workflow": workflow}


@router.get("/roles")
async def get_available_roles(current_user: dict = Depends(get_current_user)):
    """Get available roles for workflow step assignment"""
    return {"roles": APPROVER_ROLES}


@router.get("/users")
async def get_available_users(current_user: dict = Depends(get_current_user)):
    """Get company users that can be assigned as approvers"""
    company_id = current_user.get("company_id")
    
    users = await db.users.find(
        {"company_id": company_id, "is_active": {"$ne": False}},
        {"_id": 0, "user_id": 1, "email": 1, "name": 1, "role": 1}
    ).to_list(100)
    
    return {"users": [
        {
            "user_id": u.get("user_id"),
            "name": u.get("name", u.get("email", "")),
            "email": u.get("email", ""),
            "role": u.get("role", "user")
        }
        for u in users
    ]}


@router.post("")
async def create_workflow(data: WorkflowCreate, current_user: dict = Depends(get_current_user)):
    """Create a new payroll approval workflow (Enterprise only)"""
    company_id = current_user.get("company_id")
    user_role = current_user.get("role", "")
    
    if user_role not in ["admin", "hr_manager"]:
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear workflows")
    
    # Check Enterprise plan
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0, "subscription_plan": 1})
    plan = (company or {}).get("subscription_plan", "")
    if plan not in ["enterprise", "Enterprise"]:
        raise HTTPException(status_code=403, detail="Workflows de aprobación solo disponible en plan Enterprise")
    
    if not data.steps or len(data.steps) == 0:
        raise HTTPException(status_code=400, detail="El workflow debe tener al menos un paso de aprobación")
    
    if len(data.steps) > 5:
        raise HTTPException(status_code=400, detail="Máximo 5 niveles de aprobación")
    
    # Validate steps
    for step in data.steps:
        if step.approver_type == "role" and not step.approver_role:
            raise HTTPException(status_code=400, detail=f"Paso {step.step_number}: debe seleccionar un rol")
        if step.approver_type == "user" and not step.approver_user_id:
            raise HTTPException(status_code=400, detail=f"Paso {step.step_number}: debe seleccionar un usuario")
    
    # Deactivate any existing active workflow
    await db.workflows.update_many(
        {"company_id": company_id, "type": "payroll", "is_active": True},
        {"$set": {"is_active": False}}
    )
    
    workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    # Enrich steps with user names if needed
    enriched_steps = []
    for step in data.steps:
        step_dict = step.dict()
        if step.approver_type == "user" and step.approver_user_id and not step.approver_name:
            user = await db.users.find_one(
                {"user_id": step.approver_user_id},
                {"_id": 0, "name": 1, "email": 1}
            )
            if user:
                step_dict["approver_name"] = user.get("name", user.get("email", ""))
        if step.approver_type == "role" and step.approver_role:
            role_info = next((r for r in APPROVER_ROLES if r["id"] == step.approver_role), None)
            if role_info:
                step_dict["approver_name"] = role_info["name"]
        enriched_steps.append(step_dict)
    
    workflow = {
        "workflow_id": workflow_id,
        "company_id": company_id,
        "name": data.name,
        "type": "payroll",
        "is_active": True,
        "steps": enriched_steps,
        "total_steps": len(enriched_steps),
        "created_at": now,
        "updated_at": now,
        "created_by": current_user.get("user_id")
    }
    
    await db.workflows.insert_one(workflow)
    
    return {"success": True, "workflow_id": workflow_id, "message": f"Workflow creado con {len(enriched_steps)} niveles de aprobación"}


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, data: WorkflowUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing workflow"""
    company_id = current_user.get("company_id")
    
    existing = await db.workflows.find_one(
        {"workflow_id": workflow_id, "company_id": company_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.name is not None:
        update["name"] = data.name
    
    if data.is_active is not None:
        if data.is_active:
            # Deactivate others first
            await db.workflows.update_many(
                {"company_id": company_id, "type": "payroll", "is_active": True},
                {"$set": {"is_active": False}}
            )
        update["is_active"] = data.is_active
    
    if data.steps is not None:
        if len(data.steps) == 0:
            raise HTTPException(status_code=400, detail="Debe tener al menos un paso")
        if len(data.steps) > 5:
            raise HTTPException(status_code=400, detail="Máximo 5 niveles")
        
        enriched = []
        for step in data.steps:
            sd = step.dict()
            if step.approver_type == "user" and step.approver_user_id and not step.approver_name:
                user = await db.users.find_one({"user_id": step.approver_user_id}, {"_id": 0, "name": 1, "email": 1})
                if user:
                    sd["approver_name"] = user.get("name", user.get("email", ""))
            if step.approver_type == "role" and step.approver_role:
                role_info = next((r for r in APPROVER_ROLES if r["id"] == step.approver_role), None)
                if role_info:
                    sd["approver_name"] = role_info["name"]
            enriched.append(sd)
        update["steps"] = enriched
        update["total_steps"] = len(enriched)
    
    await db.workflows.update_one(
        {"workflow_id": workflow_id, "company_id": company_id},
        {"$set": update}
    )
    
    return {"success": True, "message": "Workflow actualizado"}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a workflow"""
    company_id = current_user.get("company_id")
    
    result = await db.workflows.delete_one(
        {"workflow_id": workflow_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workflow no encontrado")
    
    return {"success": True, "message": "Workflow eliminado"}


async def get_company_workflow(company_id: str):
    """Helper: Get active workflow for a company (used by payroll routes)"""
    if db is None:
        return None
    return await db.workflows.find_one(
        {"company_id": company_id, "type": "payroll", "is_active": True},
        {"_id": 0}
    )


async def can_user_approve_step(user: dict, step: dict) -> bool:
    """Check if a user can approve a specific workflow step"""
    approver_type = step.get("approver_type")
    
    if approver_type == "user":
        return user.get("user_id") == step.get("approver_user_id")
    elif approver_type == "role":
        return user.get("role") == step.get("approver_role")
    
    return False


async def get_period_workflow_status(period: dict, workflow: dict) -> dict:
    """Get the current workflow status for a period"""
    approvals = period.get("workflow_approvals", [])
    total_steps = workflow.get("total_steps", len(workflow.get("steps", [])))
    current_step = len(approvals) + 1
    
    fully_approved = current_step > total_steps
    
    current_step_info = None
    if not fully_approved and current_step <= total_steps:
        steps = workflow.get("steps", [])
        for s in steps:
            if s.get("step_number") == current_step:
                current_step_info = s
                break
    
    return {
        "current_step": current_step,
        "total_steps": total_steps,
        "fully_approved": fully_approved,
        "approvals": approvals,
        "current_step_info": current_step_info,
        "workflow_name": workflow.get("name", "")
    }

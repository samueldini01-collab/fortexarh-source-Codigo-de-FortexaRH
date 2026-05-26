"""
Admin endpoints for managing employee permissions/licenses
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("")
async def get_all_permissions(
    status: str = None,
    employee_id: str = None,
    current_user: dict = Depends(get_current_user),
):
    """Get all permission requests for the company.

    Optional filters: ``status`` (pending/approved/rejected/all) and
    ``employee_id`` to scope to a single employee.
    """
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    if status and status != "all":
        query["status"] = status
    if employee_id:
        query["employee_id"] = employee_id

    permissions = await db.employee_permissions.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(200)

    # Summary (always over all permissions in scope, not filtered by status)
    scope = {"company_id": company_id}
    if employee_id:
        scope["employee_id"] = employee_id
    all_perms = await db.employee_permissions.find(scope, {"_id": 0, "status": 1}).to_list(500)

    summary = {
        "total": len(all_perms),
        "pending": len([p for p in all_perms if p.get("status") == "pending"]),
        "approved": len([p for p in all_perms if p.get("status") == "approved"]),
        "rejected": len([p for p in all_perms if p.get("status") == "rejected"]),
    }

    return {"permissions": permissions, "summary": summary}


@router.post("")
async def create_permission_admin(data: dict, current_user: dict = Depends(get_current_user)):
    """Create a permission request from the admin side (auto-approved).

    Expected payload: ``{employee_id, permission_type, start_date, end_date,
    reason, notes?, status?}``. Defaults to ``approved`` when created by admin.
    """
    import uuid
    company_id = current_user.get("company_id")
    required = ("employee_id", "permission_type", "start_date", "end_date")
    if not all(data.get(k) for k in required):
        raise HTTPException(status_code=400, detail=f"Faltan campos: {required}")

    employee = await db.employees.find_one(
        {"employee_id": data["employee_id"], "company_id": company_id},
        {"_id": 0, "first_name": 1, "last_name": 1, "department": 1},
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    try:
        start = datetime.strptime(data["start_date"][:10], "%Y-%m-%d")
        end = datetime.strptime(data["end_date"][:10], "%Y-%m-%d")
        days = (end - start).days + 1
    except (ValueError, TypeError):
        days = 1

    perm = {
        "permission_id": f"perm_{uuid.uuid4().hex[:12]}",
        "employee_id": data["employee_id"],
        "company_id": company_id,
        "employee_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
        "department": employee.get("department", ""),
        "permission_type": data["permission_type"],
        "start_date": data["start_date"],
        "end_date": data["end_date"],
        "days": days,
        "reason": data.get("reason", ""),
        "notes": data.get("notes", ""),
        "status": data.get("status", "approved"),
        "created_by_admin": True,
        "approved_by": current_user.get("name", current_user.get("email", "")),
        "approved_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await db.employee_permissions.insert_one(perm)
    perm.pop("_id", None)
    return {"success": True, "permission": perm}


@router.put("/{permission_id}/approve")
async def approve_permission(permission_id: str, current_user: dict = Depends(get_current_user)):
    """Approve a permission request"""
    company_id = current_user.get("company_id")

    result = await db.employee_permissions.update_one(
        {"permission_id": permission_id, "company_id": company_id, "status": "pending"},
        {"$set": {
            "status": "approved",
            "approved_by": current_user.get("name", current_user.get("email", "")),
            "approved_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada o ya procesada")

    # Send push notification to employee
    try:
        from services.push_service import send_push_to_user
        perm = await db.employee_permissions.find_one({"permission_id": permission_id}, {"_id": 0})
        if perm:
            await send_push_to_user(
                perm["employee_id"],
                "Permiso Aprobado",
                f"Tu solicitud de {perm.get('permission_type', 'permiso')} ha sido aprobada.",
                "/portal"
            )
    except Exception:
        pass

    return {"success": True, "message": "Permiso aprobado"}


@router.put("/{permission_id}/reject")
async def reject_permission(permission_id: str, current_user: dict = Depends(get_current_user)):
    """Reject a permission request"""
    company_id = current_user.get("company_id")

    result = await db.employee_permissions.update_one(
        {"permission_id": permission_id, "company_id": company_id, "status": "pending"},
        {"$set": {
            "status": "rejected",
            "rejected_by": current_user.get("name", current_user.get("email", "")),
            "rejected_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada o ya procesada")

    return {"success": True, "message": "Permiso rechazado"}

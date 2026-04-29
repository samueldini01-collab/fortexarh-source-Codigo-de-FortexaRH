"""
Admin endpoints for managing employee permissions/licenses
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from config import db
from utils.auth import get_current_user

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("")
async def get_all_permissions(status: str = None, current_user: dict = Depends(get_current_user)):
    """Get all permission requests for the company"""
    company_id = current_user.get("company_id")
    query = {"company_id": company_id}
    if status and status != "all":
        query["status"] = status

    permissions = await db.employee_permissions.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(200)

    # Summary
    all_perms = await db.employee_permissions.find(
        {"company_id": company_id}, {"_id": 0, "status": 1}
    ).to_list(500)

    summary = {
        "total": len(all_perms),
        "pending": len([p for p in all_perms if p.get("status") == "pending"]),
        "approved": len([p for p in all_perms if p.get("status") == "approved"]),
        "rejected": len([p for p in all_perms if p.get("status") == "rejected"]),
    }

    return {"permissions": permissions, "summary": summary}


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

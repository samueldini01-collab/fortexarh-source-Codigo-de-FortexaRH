"""
System Users Routes - FortexaRH
Handles system user management, roles, and activities
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from utils.auth import hash_password

router = APIRouter(prefix="/system-users", tags=["System Users"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials = Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)



from models.auth import (
    SystemUserCreate, SystemUserUpdate, PasswordChange, AdminPasswordSet
)


@router.get("")
async def get_system_users(current_user: dict = Depends(get_current_user)):
    """Get all users for current company"""
    company_id = current_user.get("company_id")
    
    users = await db.users.find(
        {"company_id": company_id},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    
    return users


@router.post("")
async def create_system_user(data: SystemUserCreate, current_user: dict = Depends(get_current_user)):
    """Create a new system user"""
    company_id = current_user.get("company_id")
    
    # Check if current user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear usuarios")
    
    # Check if email exists
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    # Check user limits based on subscription
    company = await db.companies.find_one({"company_id": company_id}, {"_id": 0})
    subscription = await db.subscriptions.find_one({"company_id": company_id}, {"_id": 0})
    
    current_users = await db.users.count_documents({"company_id": company_id})
    max_users = 3  # Default
    
    if subscription:
        plan_id = subscription.get("plan_id", "trial")
        if plan_id == "basic":
            max_users = 3
        elif plan_id == "pro":
            max_users = 10
        elif plan_id == "enterprise":
            max_users = 9999
        
        # Add additional users
        max_users += subscription.get("additional_users", 0)
    
    if current_users >= max_users:
        raise HTTPException(
            status_code=403, 
            detail=f"Límite de usuarios alcanzado ({max_users}). Actualice su plan para agregar más usuarios."
        )
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    user = {
        "user_id": user_id,
        "company_id": company_id,
        "email": data.email,
        "name": data.name,
        "password_hash": hash_password(data.password),
        "role": data.role,
        "modules": data.modules or [],
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id")
    }
    
    await db.users.insert_one(user)
    
    # Log activity
    await db.user_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": user_id,
        "action": "user_created",
        "performed_by": current_user.get("user_id"),
        "performed_by_name": current_user.get("name"),
        "details": f"Usuario {data.name} creado",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"user_id": user_id, "message": "Usuario creado correctamente"}


@router.put("/{user_id}")
async def update_system_user(user_id: str, data: SystemUserUpdate, current_user: dict = Depends(get_current_user)):
    """Update a system user"""
    company_id = current_user.get("company_id")
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden editar usuarios")
    
    # Find user
    user = await db.users.find_one(
        {"user_id": user_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.role is not None:
        update_data["role"] = data.role
    if data.modules is not None:
        update_data["modules"] = data.modules
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one(
        {"user_id": user_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    # Log activity
    await db.user_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": user_id,
        "action": "user_updated",
        "performed_by": current_user.get("user_id"),
        "performed_by_name": current_user.get("name"),
        "details": f"Usuario actualizado",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Usuario actualizado correctamente"}


@router.delete("/{user_id}")
async def delete_system_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a system user"""
    company_id = current_user.get("company_id")
    
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar usuarios")
    
    if user_id == current_user.get("user_id"):
        raise HTTPException(status_code=400, detail="No puede eliminarse a sí mismo")
    
    user = await db.users.find_one(
        {"user_id": user_id, "company_id": company_id},
        {"_id": 0, "name": 1}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    await db.users.delete_one({"user_id": user_id, "company_id": company_id})
    
    # Log activity
    await db.user_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": user_id,
        "action": "user_deleted",
        "performed_by": current_user.get("user_id"),
        "performed_by_name": current_user.get("name"),
        "details": f"Usuario {user.get('name')} eliminado",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Usuario eliminado correctamente"}


@router.get("/{user_id}/activities")
async def get_user_activities(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get activity history for a user"""
    company_id = current_user.get("company_id")
    
    activities = await db.user_activities.find(
        {"company_id": company_id, "user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return activities


@router.get("/activities/all")
async def get_all_activities(limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Get all user activities for the company"""
    company_id = current_user.get("company_id")
    
    activities = await db.user_activities.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    return activities


@router.post("/change-password")
async def change_own_password(data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change own password (logged-in user)"""
    import bcrypt
    
    user = await db.users.find_one({"user_id": current_user["user_id"]}, {"_id": 0})
    
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=400, detail="No se puede cambiar la contraseña")
    
    # Verify current password
    if not bcrypt.checkpw(data.current_password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")
    
    # Update password
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {
            "password_hash": hash_password(data.new_password),
            "password_changed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/admin-set-password")
async def admin_set_user_password(data: AdminPasswordSet, current_user: dict = Depends(get_current_user)):
    """Admin sets password for another user"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden realizar esta acción")
    
    company_id = current_user.get("company_id")
    
    user = await db.users.find_one(
        {"user_id": data.user_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    await db.users.update_one(
        {"user_id": data.user_id},
        {"$set": {
            "password_hash": hash_password(data.new_password),
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
            "password_set_by_admin": True
        }}
    )
    
    # Log activity
    await db.user_activities.insert_one({
        "activity_id": f"act_{uuid.uuid4().hex[:12]}",
        "company_id": company_id,
        "user_id": data.user_id,
        "action": "password_reset_by_admin",
        "performed_by": current_user.get("user_id"),
        "performed_by_name": current_user.get("name"),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Contraseña del usuario actualizada correctamente"}

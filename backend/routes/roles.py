"""
Custom Roles Routes for FortexaRH
Enterprise-only feature for creating and managing custom roles
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid
import logging

router = APIRouter(prefix="/roles", tags=["Custom Roles"])

# These will be injected from server.py
db = None
get_current_user = None

# Default modules and permissions
DEFAULT_MODULES = [
    {"id": "dashboard", "name": "Dashboard", "description": "Panel principal"},
    {"id": "employees", "name": "Empleados", "description": "Gestión de empleados"},
    {"id": "payroll", "name": "Nómina", "description": "Procesamiento de nómina"},
    {"id": "attendance", "name": "Asistencias", "description": "Control de asistencias"},
    {"id": "vacations", "name": "Vacaciones", "description": "Gestión de vacaciones"},
    {"id": "evaluations", "name": "Evaluaciones", "description": "Evaluaciones de desempeño"},
    {"id": "recruitment", "name": "Reclutamiento", "description": "Gestión de candidatos"},
    {"id": "organigrama", "name": "Organigrama", "description": "Estructura organizacional"},
    {"id": "accounting", "name": "Contabilidad", "description": "Entradas de diario"},
    {"id": "reports", "name": "Reportes", "description": "Generación de reportes"},
    {"id": "settings", "name": "Configuración", "description": "Ajustes de la empresa"},
    {"id": "subscriptions", "name": "Suscripciones", "description": "Gestión del plan"},
    {"id": "users", "name": "Usuarios", "description": "Administración de usuarios"},
]

PERMISSION_TYPES = ["view", "create", "edit", "delete"]

# Pydantic models
class CustomRoleCreate(BaseModel):
    """Model for creating a custom role"""
    name: str
    description: Optional[str] = None
    modules: List[str] = []
    permissions: Dict[str, List[str]] = {}  # module_id: [view, create, edit, delete]
    color: Optional[str] = "#3b82f6"  # Default blue

class CustomRoleUpdate(BaseModel):
    """Model for updating a custom role"""
    name: Optional[str] = None
    description: Optional[str] = None
    modules: Optional[List[str]] = None
    permissions: Optional[Dict[str, List[str]]] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


def init_router(database, auth_dependency):
    """Initialize router with database and auth dependency"""
    global db, get_current_user
    db = database
    get_current_user = auth_dependency


async def check_enterprise_plan(company_id: str) -> bool:
    """Check if company has Enterprise plan"""
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0, "plan_id": 1}
    )
    return subscription and subscription.get("plan_id") == "enterprise"


@router.get("/modules")
async def get_available_modules(current_user: dict = Depends(lambda: get_current_user)):
    """Get list of available modules for role configuration"""
    return {
        "modules": DEFAULT_MODULES,
        "permission_types": PERMISSION_TYPES
    }


@router.get("")
async def get_custom_roles(current_user: dict = Depends(lambda: get_current_user)):
    """Get all custom roles for the company (Enterprise only)"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
    # Check if enterprise plan
    is_enterprise = await check_enterprise_plan(company_id)
    if not is_enterprise:
        return {
            "roles": [],
            "is_enterprise": False,
            "message": "Los roles personalizados solo están disponibles en el plan Enterprise"
        }
    
    roles = await db.custom_roles.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(50)
    
    # Add default roles info
    default_roles = [
        {
            "role_id": "admin",
            "name": "Administrador",
            "description": "Acceso completo a todas las funciones",
            "is_default": True,
            "modules": [m["id"] for m in DEFAULT_MODULES],
            "permissions": {m["id"]: PERMISSION_TYPES for m in DEFAULT_MODULES},
            "color": "#ef4444"
        },
        {
            "role_id": "manager",
            "name": "Gerente",
            "description": "Acceso a gestión de equipo",
            "is_default": True,
            "modules": ["dashboard", "employees", "payroll", "attendance", "vacations", "evaluations", "reports"],
            "permissions": {
                "dashboard": ["view"],
                "employees": ["view", "edit"],
                "payroll": ["view", "create"],
                "attendance": ["view", "create", "edit"],
                "vacations": ["view", "create", "edit"],
                "evaluations": ["view", "create", "edit"],
                "reports": ["view"]
            },
            "color": "#8b5cf6"
        },
        {
            "role_id": "user",
            "name": "Usuario",
            "description": "Acceso básico de solo lectura",
            "is_default": True,
            "modules": ["dashboard", "attendance", "vacations"],
            "permissions": {
                "dashboard": ["view"],
                "attendance": ["view"],
                "vacations": ["view", "create"]
            },
            "color": "#6b7280"
        }
    ]
    
    return {
        "roles": roles,
        "default_roles": default_roles,
        "is_enterprise": True,
        "modules": DEFAULT_MODULES,
        "permission_types": PERMISSION_TYPES
    }


@router.post("")
async def create_custom_role(data: CustomRoleCreate, current_user: dict = Depends(lambda: get_current_user)):
    """Create a new custom role (Enterprise only)"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
    # Check if enterprise plan
    is_enterprise = await check_enterprise_plan(company_id)
    if not is_enterprise:
        raise HTTPException(
            status_code=403, 
            detail="Los roles personalizados solo están disponibles en el plan Enterprise"
        )
    
    # Check for duplicate name
    existing = await db.custom_roles.find_one({
        "company_id": company_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un rol con este nombre")
    
    # Validate modules
    valid_module_ids = [m["id"] for m in DEFAULT_MODULES]
    invalid_modules = [m for m in data.modules if m not in valid_module_ids]
    if invalid_modules:
        raise HTTPException(
            status_code=400, 
            detail=f"Módulos inválidos: {', '.join(invalid_modules)}"
        )
    
    # Validate permissions
    for module_id, perms in data.permissions.items():
        if module_id not in valid_module_ids:
            raise HTTPException(
                status_code=400, 
                detail=f"Módulo inválido en permisos: {module_id}"
            )
        invalid_perms = [p for p in perms if p not in PERMISSION_TYPES]
        if invalid_perms:
            raise HTTPException(
                status_code=400, 
                detail=f"Permisos inválidos para {module_id}: {', '.join(invalid_perms)}"
            )
    
    role_id = f"role_{uuid.uuid4().hex[:8]}"
    role = {
        "role_id": role_id,
        "company_id": company_id,
        "name": data.name,
        "description": data.description,
        "modules": data.modules,
        "permissions": data.permissions,
        "color": data.color,
        "is_active": True,
        "is_default": False,
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_roles.insert_one(role)
    
    # Return without _id
    del role["_id"] if "_id" in role else None
    
    return {
        "role_id": role_id, 
        "message": "Rol creado correctamente",
        "role": role
    }


@router.get("/{role_id}")
async def get_custom_role(role_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Get a specific custom role"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
    role = await db.custom_roles.find_one(
        {"role_id": role_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return role


@router.put("/{role_id}")
async def update_custom_role(
    role_id: str, 
    data: CustomRoleUpdate, 
    current_user: dict = Depends(lambda: get_current_user)
):
    """Update a custom role"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
    # Check if role exists
    existing = await db.custom_roles.find_one({
        "role_id": role_id, 
        "company_id": company_id
    })
    
    if not existing:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Check for duplicate name if name is being changed
    if data.name and data.name != existing.get("name"):
        duplicate = await db.custom_roles.find_one({
            "company_id": company_id,
            "name": {"$regex": f"^{data.name}$", "$options": "i"},
            "role_id": {"$ne": role_id}
        })
        if duplicate:
            raise HTTPException(status_code=400, detail="Ya existe un rol con este nombre")
    
    # Build update
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.name is not None:
        updates["name"] = data.name
    if data.description is not None:
        updates["description"] = data.description
    if data.modules is not None:
        # Validate modules
        valid_module_ids = [m["id"] for m in DEFAULT_MODULES]
        invalid_modules = [m for m in data.modules if m not in valid_module_ids]
        if invalid_modules:
            raise HTTPException(
                status_code=400, 
                detail=f"Módulos inválidos: {', '.join(invalid_modules)}"
            )
        updates["modules"] = data.modules
    if data.permissions is not None:
        updates["permissions"] = data.permissions
    if data.color is not None:
        updates["color"] = data.color
    if data.is_active is not None:
        updates["is_active"] = data.is_active
    
    await db.custom_roles.update_one(
        {"role_id": role_id, "company_id": company_id},
        {"$set": updates}
    )
    
    # Get updated role
    updated_role = await db.custom_roles.find_one(
        {"role_id": role_id, "company_id": company_id},
        {"_id": 0}
    )
    
    return {
        "message": "Rol actualizado correctamente",
        "role": updated_role
    }


@router.delete("/{role_id}")
async def delete_custom_role(role_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Delete a custom role"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
    # Check if any users have this role
    users_with_role = await db.users.count_documents({
        "company_id": company_id,
        "custom_role_id": role_id
    })
    
    if users_with_role > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar el rol. Hay {users_with_role} usuario(s) asignados a este rol."
        )
    
    result = await db.custom_roles.delete_one({
        "role_id": role_id, 
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return {"message": "Rol eliminado correctamente"}


@router.post("/{role_id}/duplicate")
async def duplicate_custom_role(role_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Duplicate an existing role"""
    if get_current_user is None:
        raise HTTPException(status_code=500, detail="Router not initialized")
    
    user = current_user
    company_id = user.get("company_id")
    
    # Check if enterprise plan
    is_enterprise = await check_enterprise_plan(company_id)
    if not is_enterprise:
        raise HTTPException(
            status_code=403, 
            detail="Los roles personalizados solo están disponibles en el plan Enterprise"
        )
    
    # Get original role
    original = await db.custom_roles.find_one(
        {"role_id": role_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not original:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    # Create new role with copied data
    new_role_id = f"role_{uuid.uuid4().hex[:8]}"
    new_role = {
        "role_id": new_role_id,
        "company_id": company_id,
        "name": f"{original['name']} (Copia)",
        "description": original.get("description"),
        "modules": original.get("modules", []),
        "permissions": original.get("permissions", {}),
        "color": original.get("color", "#3b82f6"),
        "is_active": True,
        "is_default": False,
        "created_by": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_roles.insert_one(new_role)
    
    return {
        "role_id": new_role_id,
        "message": "Rol duplicado correctamente",
        "role": {k: v for k, v in new_role.items() if k != "_id"}
    }

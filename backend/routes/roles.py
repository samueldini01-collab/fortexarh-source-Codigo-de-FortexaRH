"""
Custom Roles Routes for FortexaRH
Enterprise-only feature for creating and managing custom roles
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timezone
import uuid
import logging

router = APIRouter(prefix="/roles", tags=["Custom Roles"])

from config import db
from utils.auth import get_current_user, get_user_from_request
logger = logging.getLogger(__name__)

# Default modules and permissions
DEFAULT_MODULES = [
    {
        "id": "dashboard", 
        "name": "Dashboard", 
        "description": "Panel principal y estadísticas",
        "permissions": ["view"]
    },
    {
        "id": "employees", 
        "name": "Empleados", 
        "description": "Gestión de empleados",
        "permissions": ["view", "create", "edit", "delete", "export", "import"]
    },
    {
        "id": "payroll", 
        "name": "Nómina", 
        "description": "Procesamiento de nómina",
        "permissions": ["view", "create", "edit", "delete", "calculate", "approve", "pay", "export", "reports"]
    },
    {
        "id": "attendance", 
        "name": "Asistencias", 
        "description": "Control de asistencias",
        "permissions": ["view", "create", "edit", "delete", "export", "reports"]
    },
    {
        "id": "vacations", 
        "name": "Vacaciones", 
        "description": "Gestión de vacaciones",
        "permissions": ["view", "create", "edit", "delete", "approve", "export"]
    },
    {
        "id": "leaves", 
        "name": "Licencias", 
        "description": "Gestión de licencias y permisos",
        "permissions": ["view", "create", "edit", "delete", "approve"]
    },
    {
        "id": "evaluations", 
        "name": "Evaluaciones", 
        "description": "Evaluaciones de desempeño",
        "permissions": ["view", "create", "edit", "delete", "assign", "reports"]
    },
    {
        "id": "recruitment", 
        "name": "Reclutamiento", 
        "description": "Gestión de candidatos",
        "permissions": ["view", "create", "edit", "delete", "schedule", "hire"]
    },
    {
        "id": "organigrama", 
        "name": "Organigrama", 
        "description": "Estructura organizacional",
        "permissions": ["view", "edit"]
    },
    {
        "id": "loans", 
        "name": "Préstamos", 
        "description": "Gestión de préstamos a empleados",
        "permissions": ["view", "create", "edit", "delete", "approve"]
    },
    {
        "id": "accounting", 
        "name": "Contabilidad", 
        "description": "Entradas de diario y cuentas",
        "permissions": ["view", "create", "edit", "delete", "export", "reports"]
    },
    {
        "id": "reports", 
        "name": "Reportes", 
        "description": "Generación de reportes",
        "permissions": ["view", "generate", "export", "schedule"]
    },
    {
        "id": "documents", 
        "name": "Documentos", 
        "description": "Gestión de documentos",
        "permissions": ["view", "create", "edit", "delete", "generate", "sign"]
    },
    {
        "id": "settings", 
        "name": "Configuración", 
        "description": "Ajustes de la empresa",
        "permissions": ["view", "edit"]
    },
    {
        "id": "subscriptions", 
        "name": "Suscripciones", 
        "description": "Gestión del plan",
        "permissions": ["view", "manage"]
    },
    {
        "id": "users", 
        "name": "Usuarios", 
        "description": "Administración de usuarios",
        "permissions": ["view", "create", "edit", "delete", "assign_roles"]
    },
    {
        "id": "roles", 
        "name": "Roles", 
        "description": "Gestión de roles personalizados",
        "permissions": ["view", "create", "edit", "delete"]
    },
    {
        "id": "audit", 
        "name": "Auditoría", 
        "description": "Registro de cambios y actividad",
        "permissions": ["view", "export"]
    },
    {
        "id": "support", 
        "name": "Soporte", 
        "description": "Tickets de soporte",
        "permissions": ["view", "create", "respond", "manage"]
    },
    {
        "id": "contracts", 
        "name": "Contratos", 
        "description": "Contratos laborales y firma electrónica",
        "permissions": ["view", "create", "edit", "delete", "sign", "send_for_signature"]
    },
    {
        "id": "workflows", 
        "name": "Automatización", 
        "description": "Workflows de aprobación de nómina",
        "permissions": ["view", "create", "edit", "delete"]
    },
]

# Permission type labels in Spanish
PERMISSION_LABELS = {
    "view": "Ver",
    "create": "Crear",
    "edit": "Editar",
    "delete": "Eliminar",
    "export": "Exportar",
    "import": "Importar",
    "reports": "Reportes",
    "calculate": "Calcular",
    "approve": "Aprobar",
    "pay": "Pagar",
    "assign": "Asignar",
    "schedule": "Programar",
    "hire": "Contratar",
    "generate": "Generar",
    "sign": "Firmar",
    "manage": "Gestionar",
    "assign_roles": "Asignar Roles",
    "respond": "Responder",
    "send_for_signature": "Enviar a Firma"
}

# All possible permission types
PERMISSION_TYPES = list(PERMISSION_LABELS.keys())


# Pydantic models
from models.system import CustomRoleCreate, CustomRoleUpdate


async def check_enterprise_plan(company_id: str) -> bool:
    """Check if company has Enterprise plan"""
    subscription = await db.subscriptions.find_one(
        {"company_id": company_id},
        {"_id": 0, "plan_id": 1}
    )
    return subscription and subscription.get("plan_id") == "enterprise"


@router.get("/modules")
async def get_available_modules(request: Request):
    """Get list of available modules for role configuration"""
    await get_user_from_request(request)  # Verify auth
    return {
        "modules": DEFAULT_MODULES,
        "permission_types": PERMISSION_TYPES,
        "permission_labels": PERMISSION_LABELS
    }


@router.get("")
async def get_custom_roles(request: Request):
    """Get all custom roles for the company (Enterprise only)"""
    current_user = await get_user_from_request(request)
    company_id = current_user.get("company_id")
    
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
            "permissions": {m["id"]: m["permissions"] for m in DEFAULT_MODULES},
            "color": "#ef4444"
        },
        {
            "role_id": "hr_manager",
            "name": "Gerente de RRHH",
            "description": "Gestión completa de recursos humanos",
            "is_default": True,
            "modules": ["dashboard", "employees", "payroll", "attendance", "vacations", "leaves", "evaluations", "recruitment", "loans", "documents", "reports"],
            "permissions": {
                "dashboard": ["view"],
                "employees": ["view", "create", "edit", "delete", "export"],
                "payroll": ["view", "create", "edit", "calculate", "approve", "export", "reports"],
                "attendance": ["view", "create", "edit", "export", "reports"],
                "vacations": ["view", "create", "edit", "approve", "export"],
                "leaves": ["view", "create", "edit", "approve"],
                "evaluations": ["view", "create", "edit", "assign", "reports"],
                "recruitment": ["view", "create", "edit", "schedule", "hire"],
                "loans": ["view", "create", "edit", "approve"],
                "documents": ["view", "create", "generate"],
                "reports": ["view", "generate", "export"]
            },
            "color": "#8b5cf6"
        },
        {
            "role_id": "payroll_manager",
            "name": "Encargado de Nómina",
            "description": "Procesamiento y gestión de nómina",
            "is_default": True,
            "modules": ["dashboard", "employees", "payroll", "attendance", "loans", "reports"],
            "permissions": {
                "dashboard": ["view"],
                "employees": ["view"],
                "payroll": ["view", "create", "edit", "calculate", "export", "reports"],
                "attendance": ["view", "export"],
                "loans": ["view", "create", "edit"],
                "reports": ["view", "generate", "export"]
            },
            "color": "#22c55e"
        },
        {
            "role_id": "supervisor",
            "name": "Supervisor",
            "description": "Supervisión de equipo y asistencias",
            "is_default": True,
            "modules": ["dashboard", "employees", "attendance", "vacations", "leaves", "evaluations"],
            "permissions": {
                "dashboard": ["view"],
                "employees": ["view"],
                "attendance": ["view", "create", "edit"],
                "vacations": ["view", "approve"],
                "leaves": ["view", "approve"],
                "evaluations": ["view", "create", "assign"]
            },
            "color": "#3b82f6"
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
        "permission_types": PERMISSION_TYPES,
        "permission_labels": PERMISSION_LABELS
    }


@router.post("")
async def create_custom_role(data: CustomRoleCreate, request: Request):
    """Create a new custom role (Enterprise only)"""
    current_user = await get_user_from_request(request)
    company_id = current_user.get("company_id")
    
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
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_roles.insert_one(role)
    
    # Return without _id
    if "_id" in role:
        del role["_id"]
    
    return {
        "role_id": role_id, 
        "message": "Rol creado correctamente",
        "role": role
    }


@router.get("/{role_id}")
async def get_custom_role(role_id: str, request: Request):
    """Get a specific custom role"""
    current_user = await get_user_from_request(request)
    company_id = current_user.get("company_id")
    
    role = await db.custom_roles.find_one(
        {"role_id": role_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    return role


@router.put("/{role_id}")
async def update_custom_role(role_id: str, data: CustomRoleUpdate, request: Request):
    """Update a custom role"""
    current_user = await get_user_from_request(request)
    company_id = current_user.get("company_id")
    
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
async def delete_custom_role(role_id: str, request: Request):
    """Delete a custom role"""
    current_user = await get_user_from_request(request)
    company_id = current_user.get("company_id")
    
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
async def duplicate_custom_role(role_id: str, request: Request):
    """Duplicate an existing role"""
    current_user = await get_user_from_request(request)
    company_id = current_user.get("company_id")
    
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
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.custom_roles.insert_one(new_role)
    
    return {
        "role_id": new_role_id,
        "message": "Rol duplicado correctamente",
        "role": {k: v for k, v in new_role.items() if k != "_id"}
    }

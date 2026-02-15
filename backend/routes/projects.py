"""
Projects Routes - FortexaRH
Handles project management for payroll assignment
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/projects", tags=["Projects"])
from config import db
from utils.auth import get_current_user
security = HTTPBearer(auto_error=False)

from models.system import ProjectCreate, ProjectUpdate


@router.get("")
async def get_projects(current_user: dict = Depends(get_current_user)):
    """Obtener todos los proyectos de la empresa"""
    company_id = current_user.get("company_id")
    projects = await db.projects.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(100)
    return projects


@router.post("")
async def create_project(data: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo proyecto"""
    company_id = current_user.get("company_id")
    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    
    project = {
        "project_id": project_id,
        "company_id": company_id,
        "name": data.name,
        "description": data.description,
        "status": data.status,
        "employee_ids": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("user_id")
    }
    
    await db.projects.insert_one(project)
    return {"project_id": project_id, "message": "Proyecto creado"}


@router.put("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, current_user: dict = Depends(get_current_user)):
    """Actualizar un proyecto"""
    company_id = current_user.get("company_id")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.projects.update_one(
        {"project_id": project_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {"message": "Proyecto actualizado"}


@router.post("/{project_id}/employees")
async def add_employees_to_project(project_id: str, employee_ids: List[str], current_user: dict = Depends(get_current_user)):
    """Agregar empleados a un proyecto"""
    company_id = current_user.get("company_id")
    
    project = await db.projects.find_one(
        {"project_id": project_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    current_employees = set(project.get("employee_ids", []))
    current_employees.update(employee_ids)
    
    await db.projects.update_one(
        {"project_id": project_id, "company_id": company_id},
        {"$set": {
            "employee_ids": list(current_employees),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": f"{len(employee_ids)} empleados agregados al proyecto"}


@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar un proyecto"""
    company_id = current_user.get("company_id")
    
    result = await db.projects.delete_one(
        {"project_id": project_id, "company_id": company_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {"message": "Proyecto eliminado"}

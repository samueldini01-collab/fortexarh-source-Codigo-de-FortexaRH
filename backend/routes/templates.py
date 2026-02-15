"""
Templates Routes - FortexaRH
Handles document template CRUD and document generation from templates.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/templates", tags=["Templates"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials=Depends(security)):
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)


from models.system import TemplateCreate


@router.get("")
async def get_templates(current_user: dict = Depends(get_current_user)):
    templates = await db.templates.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).to_list(1000)
    return templates


@router.post("")
async def create_template(data: TemplateCreate, current_user: dict = Depends(get_current_user)):
    template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
    template = {
        "template_id": template_id,
        "company_id": current_user.get("company_id"),
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    await db.templates.insert_one(template)
    return {"template_id": template_id, "message": "Plantilla creada correctamente"}


@router.get("/{template_id}")
async def get_template(template_id: str, current_user: dict = Depends(get_current_user)):
    template = await db.templates.find_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return template


@router.put("/{template_id}")
async def update_template(template_id: str, data: TemplateCreate, current_user: dict = Depends(get_current_user)):
    result = await db.templates.update_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")},
        {"$set": {
            **data.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return {"message": "Plantilla actualizada correctamente"}


@router.delete("/{template_id}")
async def delete_template(template_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.templates.delete_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return {"message": "Plantilla eliminada correctamente"}


@router.post("/{template_id}/generate")
async def generate_document(template_id: str, variables: Dict[str, str], current_user: dict = Depends(get_current_user)):
    template = await db.templates.find_one(
        {"template_id": template_id, "company_id": current_user.get("company_id")},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")

    content = template["content"]
    for var, value in variables.items():
        content = content.replace(f"{{{{{var}}}}}", value)

    return {"content": content, "template_name": template["name"]}

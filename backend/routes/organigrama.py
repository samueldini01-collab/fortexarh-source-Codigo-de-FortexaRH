"""
Organigrama Routes - FortexaRH
Handles organizational chart management
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/organigrama", tags=["Organigrama"])
security = HTTPBearer(auto_error=False)

db = None
_get_current_user_func = None


def init_router(database, auth_func):
    global db, _get_current_user_func
    db = database
    _get_current_user_func = auth_func


async def get_current_user(request: Request, credentials = Depends(security)):
    """Wrapper for the injected auth function"""
    if _get_current_user_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _get_current_user_func(request, credentials)



class OrgNodeCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    type: str = "department"
    manager_id: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None


class OrgNodeReorder(BaseModel):
    nodes: List[dict]


@router.get("")
async def get_organigrama(current_user: dict = Depends(get_current_user)):
    nodes = await db.organigrama.find(
        {"company_id": current_user.get("company_id")},
        {"_id": 0}
    ).sort("order", 1).to_list(1000)
    return nodes


@router.post("")
async def create_org_node(data: OrgNodeCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    manager_name = None
    if data.manager_id:
        manager = await db.employees.find_one(
            {"employee_id": data.manager_id, "company_id": company_id},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if manager:
            manager_name = f"{manager['first_name']} {manager['last_name']}"
    
    # Count employees in department
    employee_count = await db.employees.count_documents({
        "company_id": company_id,
        "department": data.name
    })
    
    # Get next order
    last_node = await db.organigrama.find_one(
        {"company_id": company_id},
        {"_id": 0, "order": 1},
        sort=[("order", -1)]
    )
    next_order = (last_node.get("order", 0) if last_node else 0) + 1
    
    node_id = f"org_{uuid.uuid4().hex[:12]}"
    node = {
        "node_id": node_id,
        "company_id": company_id,
        "name": data.name,
        "parent_id": data.parent_id,
        "type": data.type,
        "manager_id": data.manager_id,
        "manager_name": manager_name,
        "description": data.description,
        "budget": data.budget,
        "employee_count": employee_count,
        "order": next_order,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.organigrama.insert_one(node)
    
    return {"node_id": node_id, "message": "Organizational unit created successfully"}


@router.put("/{node_id}")
async def update_org_node(node_id: str, data: OrgNodeCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    manager_name = None
    if data.manager_id:
        manager = await db.employees.find_one(
            {"employee_id": data.manager_id, "company_id": company_id},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if manager:
            manager_name = f"{manager['first_name']} {manager['last_name']}"
    
    # Count employees in department
    employee_count = await db.employees.count_documents({
        "company_id": company_id,
        "department": data.name
    })
    
    update_data = {
        "name": data.name,
        "parent_id": data.parent_id,
        "type": data.type,
        "manager_id": data.manager_id,
        "manager_name": manager_name,
        "description": data.description,
        "budget": data.budget,
        "employee_count": employee_count,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.organigrama.update_one(
        {"node_id": node_id, "company_id": company_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Organizational unit not found")
    
    return {"message": "Organizational unit updated successfully"}


@router.delete("/{node_id}")
async def delete_org_node(node_id: str, current_user: dict = Depends(get_current_user)):
    company_id = current_user.get("company_id")
    
    # Check if node has children
    children = await db.organigrama.count_documents({
        "company_id": company_id,
        "parent_id": node_id
    })
    
    if children > 0:
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar una unidad que tiene sub-unidades. Elimine primero las sub-unidades."
        )
    
    # Check if node has employees
    node = await db.organigrama.find_one({"node_id": node_id, "company_id": company_id}, {"_id": 0})
    if node:
        employees = await db.employees.count_documents({
            "company_id": company_id,
            "department": node.get("name")
        })
        if employees > 0:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede eliminar. Hay {employees} empleados asignados a esta unidad."
            )
    
    result = await db.organigrama.delete_one({
        "node_id": node_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Organizational unit not found")
    
    return {"message": "Organizational unit deleted successfully"}


@router.put("/reorder")
async def reorder_org_nodes(data: OrgNodeReorder, current_user: dict = Depends(get_current_user)):
    """Reorder organizational nodes"""
    company_id = current_user.get("company_id")
    
    for node in data.nodes:
        await db.organigrama.update_one(
            {"node_id": node["node_id"], "company_id": company_id},
            {"$set": {
                "order": node.get("order", 0),
                "parent_id": node.get("parent_id")
            }}
        )
    
    return {"message": "Order updated successfully"}
